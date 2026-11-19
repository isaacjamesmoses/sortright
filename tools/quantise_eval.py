"""Step 2 (python 3.12: onnx + onnxruntime, no torch needed): static int8 quantisation (QDQ) of web/model/sortright_fp32.onnx with a
representative calibration set (Lecture D, Lab D1 recipe), then compare fp32 vs int8 on the real-world test set (accuracy, agreement, latency, size)."""
import sys, json, csv, time, numpy as np
from pathlib import Path
from PIL import Image
import onnxruntime as ort
from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantFormat, QuantType

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "model"
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def prep(p):
    """Same as torchvision Resize(256) + CenterCrop(224) + Normalize (PIL bilinear)."""
    im = Image.open(p).convert("RGB")
    w, h = im.size
    if w <= h:
        nw, nh = 256, int(256 * h / w)
    else:
        nw, nh = int(256 * w / h), 256
    im = im.resize((nw, nh), Image.BILINEAR)
    l, t = int(round((nw - 224) / 2.0)), int(round((nh - 224) / 2.0))
    a = (np.asarray(im.crop((l, t, l + 224, t + 224)), np.float32) / 255 - MEAN) / STD
    return a.transpose(2, 0, 1)[None].astype(np.float32)


S = json.load(open(ROOT / "data/splits.json"))
rng = np.random.RandomState(0)
calib = [ROOT / "data/trashnet/dataset-resized" / r for r in rng.choice(S["trashnet_train"], 60, replace=False)]
calib += [ROOT / "data/train_taco" / r for r in rng.choice(S["taco_train"], 60, replace=False)]
comp = sorted((ROOT / "data/synth/composites").rglob("*.jpg"))
calib += [comp[i] for i in rng.choice(len(comp), 30, replace=False)]


class R(CalibrationDataReader):
    def __init__(s):
        s.it = iter(calib)

    def get_next(s):
        p = next(s.it, None)
        return None if p is None else {"image": prep(p)}


fp32, int8 = OUT / "sortright_fp32.onnx", OUT / "sortright.onnx"
quantize_static(str(fp32), str(int8), R(), quant_format=QuantFormat.QDQ, activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8, per_channel=True)
rows = list(csv.DictReader(open(ROOT / "data/realworld_test_set/labels.csv", encoding="utf-8")))
X = np.concatenate([prep(ROOT / "data/realworld_test_set" / r["file"]) for r in rows])
y = np.array([CLS.index(r["label"]) for r in rows])
res = {}
for name, path in (("fp32", fp32), ("int8", int8)):
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    se = ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])
    se.run(None, {"image": X[:1]})
    t = time.time()
    P = np.concatenate([se.run(None, {"image": X[i:i + 1]})[0] for i in range(len(X))])
    ms = (time.time() - t) / len(X) * 1000
    res[name] = dict(acc=float((P.argmax(1) == y).mean()), ms_per_image=ms, size_mb=path.stat().st_size / 1e6, pred=P.argmax(1).tolist())
    print(f"{name}: real-world acc {res[name]['acc']:.3f}, {ms:.1f} ms/img (1 CPU thread), {res[name]['size_mb']:.1f} MB", flush=True)
agree = float(np.mean(np.array(res["fp32"]["pred"]) == np.array(res["int8"]["pred"])))
print("fp32/int8 agreement", round(agree, 3))
json.dump(dict(fp32={k: v for k, v in res["fp32"].items() if k != "pred"}, int8={k: v for k, v in res["int8"].items() if k != "pred"}, agreement=agree),
          open(ROOT / "results/onnx_export.json", "w"), indent=1)
