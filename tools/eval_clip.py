"""CLIP zero-shot comparison (Lecture F, Lab F1 recipe: descriptive prompt ensemble) on the real-world test set and TrashNet test.
Runs on CPU. Tuned on nothing: prompts are fixed in advance (not tuned on the test images)."""
import json, csv, numpy as np, torch, open_clip
from pathlib import Path
from PIL import Image
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix

ROOT = Path(__file__).resolve().parent.parent
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
CI = {c: i for i, c in enumerate(CLS)}
MAPTN = {"plastic": "plastic", "paper": "paper", "cardboard": "cardboard", "glass": "glass", "metal": "metal", "trash": "general_waste"}
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
S = json.load(open(ROOT / "data/splits.json"))
model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
model.eval()
tok = open_clip.get_tokenizer("ViT-B-32")
with torch.no_grad():
    T_ = []
    for c in CLS:
        e = model.encode_text(tok(PROMPTS[c]))
        e = e / e.norm(dim=-1, keepdim=True)
        e = e.mean(0)
        T_.append(e / e.norm())
    T_ = torch.stack(T_)


def probs(paths):
    out = []
    with torch.no_grad():
        for i in range(0, len(paths), 32):
            x = torch.stack([pre(Image.open(p).convert("RGB")) for p in paths[i:i + 32]])
            f = model.encode_image(x)
            f = f / f.norm(dim=-1, keepdim=True)
            out.append(torch.softmax(100 * f @ T_.T, -1))
    return torch.cat(out).numpy()


rows = list(csv.DictReader(open(ROOT / "data/realworld_test_set/labels.csv", encoding="utf-8")))
rp = [ROOT / "data/realworld_test_set" / r["file"] for r in rows]
yr = np.array([CI[r["label"]] for r in rows])
tt = S["trashnet_test"]
tp = [ROOT / "data/trashnet/dataset-resized" / r for r in tt]
yt = np.array([CI[MAPTN[r.split("/")[0]]] for r in tt])
Pr, Pt = probs(rp), probs(tp)


def m(P, y, present):
    pred = P.argmax(1)
    return dict(acc=float(accuracy_score(y, pred)), macro_f1=float(f1_score(y, pred, labels=present, average="macro", zero_division=0)),
                recall={CLS[c]: float(((pred == c) & (y == c)).sum() / max(1, (y == c).sum())) for c in present},
                confusion=confusion_matrix(y, pred, labels=list(range(8))).tolist())


res = dict(arm="clip_zeroshot", seed=0, n_train=0, real=m(Pr, yr, list(range(8))), trashnet=m(Pt, yt, [0, 1, 2, 3, 4, 6]))
np.savez(ROOT / "results/probs_clip_s0.npz", real=Pr, yr=yr, tn=Pt, yt=yt)
json.dump(res, open(ROOT / "results/clip_s0.json", "w"), indent=1)
print("CLIP zero-shot real acc %.3f f1 %.3f | trashnet acc %.3f" % (res["real"]["acc"], res["real"]["macro_f1"], res["trashnet"]["acc"]))
