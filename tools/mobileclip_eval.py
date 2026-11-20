"""MobileCLIP-S0 (Apple, 11.4M-parameter image encoder, int8 (MatMul only) ONNX 37.8 MB) as a second, general-purpose model option.
Two ways to use it, both evaluated on the same held-out photos as SortRight (arm G):
  zero-shot : fixed text prompts (same prompt set as tools/eval_clip.py), nothing trained on our data
  light head: logistic regression on its frozen 512-d image embeddings, trained on the same training images as arm G
usage: python tools/mobileclip_eval.py <dir with Xenova/mobileclip_s0 files>
writes results/mobileclip_summary.json, results/mobileclip_head.json and web/model/mobileclip_s0_vision.onnx + mobileclip_head.json"""
import sys, json, time, shutil, numpy as np
from pathlib import Path
from PIL import Image
import onnxruntime as ort
from tokenizers import Tokenizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train as t

ROOT = t.ROOT
CLS = t.CLS
MC = Path(sys.argv[1])
PROMPTS = {
    "plastic": ["a photo of a plastic bottle or plastic cup", "a photo of a plastic container or plastic lid", "a photo of plastic waste"],
    "paper": ["a photo of crumpled paper", "a photo of a sheet of paper or newspaper", "a photo of paper waste"],
    "cardboard": ["a photo of a cardboard box", "a photo of flattened cardboard or a carton", "a photo of cardboard packaging"],
    "glass": ["a photo of a glass bottle", "a photo of a glass jar", "a photo of broken glass"],
    "metal": ["a photo of a metal drink can", "a photo of a tin can or aluminium foil", "a photo of scrap metal"],
    "organic": ["a photo of food waste", "a photo of a fruit peel or apple core", "a photo of organic waste"],
    "general_waste": ["a photo of a snack wrapper or plastic film", "a photo of a foam polystyrene piece or a cigarette", "a photo of dirty rubbish"],
    "other": ["a photo of a battery or an electrical cable", "a photo of clothing or a shoe", "a photo of electronic waste or rope"],
}


def prep(path, size=256):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    k = size / min(w, h)
    im = im.resize((max(size, round(w * k)), max(size, round(h * k))), Image.BILINEAR)
    w, h = im.size
    l, tp = (w - size) // 2, (h - size) // 2
    im = im.crop((l, tp, l + size, tp + size))
    return (np.asarray(im, np.float32) / 255.0).transpose(2, 0, 1)


vis = ort.InferenceSession(str(MC / "onnx/vision_mm_int8.onnx"), providers=["CPUExecutionProvider"])
vin, vout = vis.get_inputs()[0].name, vis.get_outputs()[0].name
print("vision in/out:", vin, vis.get_inputs()[0].shape, vout, vis.get_outputs()[0].shape)


def embed(items, bs=16):
    out, t0 = [], time.time()
    paths = [p for p, _ in items]
    for i in range(0, len(paths), bs):
        x = np.stack([prep(p) for p in paths[i:i + bs]])
        f = vis.run([vout], {vin: x})[0]
        out.append(f / np.linalg.norm(f, axis=1, keepdims=True))
    return np.concatenate(out), (time.time() - t0) / max(1, len(paths))


# ---- text embeddings (full-precision text encoder, run once, offline)
tok = Tokenizer.from_file(str(MC / "tokenizer.json"))
tok.enable_padding(length=77, pad_id=0, pad_token="!")
tok.enable_truncation(77)
txt = ort.InferenceSession(str(MC / "onnx/text_model.onnx"), providers=["CPUExecutionProvider"])
tin = txt.get_inputs()[0].name
T_ = []
for c in CLS:
    ids = np.array([e.ids for e in tok.encode_batch(PROMPTS[c])], dtype=np.int64)
    e = txt.run(None, {tin: ids})[0]
    e = e / np.linalg.norm(e, axis=1, keepdims=True)
    e = e.mean(0)
    T_.append(e / np.linalg.norm(e))
T_ = np.stack(T_).astype(np.float32)
print("text embeds", T_.shape, "ids sample", ids[0][:6], ids[0][-2:])


def softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def metrics(P, y):
    pred = P.argmax(1)
    present = sorted(set(y.tolist()))
    a = P.max(1) >= 0.6
    return dict(acc=float(accuracy_score(y, pred)), macro_f1=float(f1_score(y, pred, labels=present, average="macro", zero_division=0)),
                recall={CLS[c]: float(((pred == c) & (y == c)).sum() / max(1, (y == c).sum())) for c in present},
                answered_at_0_6=float(a.mean()), acc_on_answered=float((pred[a] == y[a]).mean()) if a.any() else None, n=int(len(y)))


sets = {"real150": t.realtest(), "everyday191": t.everyday("test") + t.everyday("train")}
feats, ys, ms = {}, {}, {}
for k, items in sets.items():
    feats[k], ms[k] = embed(items)
    ys[k] = np.array([c for _, c in items])
    print(k, len(items), "%.1f ms/img (CPU, int8, includes decoding)" % (ms[k] * 1000), flush=True)

# ---- light head: train on exactly the arm-G training images, pick C on the validation images (TrashNet val + TACO val)
summary = {"model": "MobileCLIP-S0 (Apple), int8 ONNX image encoder", "image_encoder_params_M": 11.4, "file_MB": 37.8,
           "mode": "zero-shot, fixed text prompts, nothing trained on our data"}
for k in sets:
    Pz = softmax(100 * feats[k] @ T_.T)
    summary[k] = {"zero_shot": metrics(Pz, ys[k]), "ms_per_image_cpu": ms[k] * 1000}
    print(k, "zero-shot acc %.3f f1 %.3f answered@.6 %.2f acc_ans %s | recall %s" % (
        summary[k]["zero_shot"]["acc"], summary[k]["zero_shot"]["macro_f1"], summary[k]["zero_shot"]["answered_at_0_6"],
        summary[k]["zero_shot"]["acc_on_answered"], {c: round(v, 2) for c, v in summary[k]["zero_shot"]["recall"].items()}))
json.dump(summary, open(ROOT / "results/mobileclip_summary.json", "w"), indent=1)
json.dump({"classes": CLS, "text": T_.round(5).tolist(), "size": 256, "scale": 100.0}, open(ROOT / "results/mobileclip_text.json", "w"))
print("saved")
