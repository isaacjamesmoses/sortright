"""Write results/everyday_summary.md from results/everyday_<arm>_s<seed>_<split>.json (made by eval_everyday.py)."""
import json, numpy as np
from pathlib import Path
R = Path(__file__).resolve().parent.parent / "results"
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
def load(arm, split):
    L = [json.load(open(f)) for f in sorted(R.glob(f"everyday_{arm}_s*_{split}.json"))]
    return L
def line(name, L):
    m = lambda k: np.mean([d[k] for d in L])
    mr = lambda k: np.mean([d["real"][k] if False else d[k] for d in L])
    return (f"| {name} | {L[0]['n']} | {m('acc'):.3f} | {m('macro_f1'):.3f} | {m('answered_at_0.6'):.2f} | "
            f"{np.mean([d['acc_answered_at_0.6'] for d in L]):.2f} | {np.mean([d['wrong_at_conf_ge_0.8'] for d in L]):.1f} |")
out = ["# Everyday-items stress test (second real-world set: product shots, packaging, items on tables and floors)", "",
       "Source: Wikimedia Commons (CC0 / public domain / CC BY / CC BY-SA), reviewed by eye. 191 images: 97 'train' half (used only by arm H, repeated x4), 94 'test' half (held out). Licences per image: data/everyday_set/labels.csv. Mean of 2 seeds.", "",
       "| Model | n | accuracy | macro-F1 | share answered at 0.6 | accuracy on answered | confident errors (conf >= 0.8) |", "|---|---|---|---|---|---|---|"]
for arm, nm in (("A", "A. TrashNet only"), ("E", "E. + real TACO crops"), ("G", "G. + generated organic/other (previously deployed)")):
    L = load(arm, "all")
    if L: out.append(line(nm + " (all 191, never saw this set)", L))
for arm, nm in (("G", "G (held-out half)"), ("H", "H (held-out half)")):
    L = load(arm, "test")
    if L: out.append(line(nm, L))
out += ["", "## Per-class recall, held-out half (mean of 2 seeds)", "", "| Model | " + " | ".join(CLS) + " |", "|---|" + "---|" * 8]
for arm in ("G", "H"):
    L = load(arm, "test")
    if L: out.append(f"| {arm} | " + " | ".join(f"{np.mean([d['recall'][c] for d in L]):.2f}" for c in CLS) + " |")
L = load("G", "all")
if L:
    out += ["", "## Per-class recall of G on all 191 images (mean of 2 seeds)", "", "| " + " | ".join(CLS) + " |", "|" + "---|" * 8,
            "| " + " | ".join(f"{np.mean([d['recall'][c] for d in L]):.2f}" for c in CLS) + " |"]
    cm = np.sum([np.array(d["confusion"]) for d in L], axis=0)
    out += ["", f"Printed/packaged cardboard called paper by G: {cm[2,1]} of {cm[2].sum()} cardboard images (both seeds pooled). General waste correct: {cm[6,6]} of {cm[6].sum()}."]
open(R / "everyday_summary.md", "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
