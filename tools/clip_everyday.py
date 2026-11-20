"""CLIP ViT-B/32 (LAION-2B) zero-shot on the 191 everyday photos, same fixed prompts as tools/eval_clip.py, for the model comparison slide."""
import sys, json, numpy as np, torch, open_clip
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import train as t
from mobileclip_prompts import PROMPTS

model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
model.eval()
tok = open_clip.get_tokenizer("ViT-B-32")
with torch.no_grad():
    T_ = []
    for c in t.CLS:
        e = model.encode_text(tok(PROMPTS[c]))
        e = e / e.norm(dim=-1, keepdim=True)
        e = e.mean(0)
        T_.append(e / e.norm())
    T_ = torch.stack(T_)
items = t.everyday("test") + t.everyday("train")
y = np.array([c for _, c in items])
P = []
with torch.no_grad():
    for i in range(0, len(items), 32):
        x = torch.stack([pre(Image.open(p).convert("RGB")) for p, _ in items[i:i + 32]])
        f = model.encode_image(x)
        f = f / f.norm(dim=-1, keepdim=True)
        P.append(torch.softmax(100 * f @ T_.T, -1))
P = torch.cat(P).numpy()
m = t.metrics(P, y, sorted(set(y.tolist())))
m["n"] = len(y)
json.dump(m, open(t.ROOT / "results/clip_b32_everyday.json", "w"), indent=1)
print("CLIP ViT-B/32 on everyday191: acc %.3f macro-F1 %.3f" % (m["acc"], m["macro_f1"]))
