"""Aggregate results into results/summary.md and figures. Reads results/*.json and results/probs_*.npz."""
import json, glob, numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
NAMES = {"probe": "Baseline: frozen backbone + linear probe (TrashNet)", "clip": "CLIP zero-shot (comparison)",
         "A": "A. Fine-tuned, TrashNet only", "B": "B. + strong classic augmentation",
         "C": "C. + synthetic composites", "D": "D. + composites + generated organic/other",
         "E": "E. + real TACO training crops", "F": "F. All data (real + composites + synthetic classes)", "G": "G. Real + more generated organic/other (no composites)"}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def load():
    out = {}
    for f in sorted(glob.glob(str(R / "*_s*.json"))):
        d = json.load(open(f))
        a = d["arm"].replace("clip_zeroshot", "clip")
        out.setdefault(a, []).append(d)
    return out


def threshold_table(arm, seed):
    f = R / f"probs_{arm}_s{seed}.npz"
    if not f.exists():
        return None
    z = np.load(f)
    P, y = z["real"], z["yr"]
    conf = P.max(1)
    pred = P.argmax(1)
    rows = []
    for t in (0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        acc_mask = conf >= t
        cov = acc_mask.mean()
        accu = (pred[acc_mask] == y[acc_mask]).mean() if acc_mask.any() else float("nan")
        rows.append((t, cov, accu))
    return rows


res = load()
lines = ["# SortRight results (real-world test set n=150; TrashNet test n=251)", "",
         "| Arm | Train images | Real-world accuracy (95% CI) | Real-world macro-F1 | TrashNet accuracy | Seeds |", "|---|---|---|---|---|---|"]
order = ["probe", "clip", "A", "B", "C", "D", "E", "F", "G"]
for a in order:
    if a not in res:
        continue
    L = res[a]
    acc = np.mean([d["real"]["acc"] for d in L])
    f1 = np.mean([d["real"]["macro_f1"] for d in L])
    ta = np.mean([d["trashnet"]["acc"] for d in L])
    lo, hi = wilson(round(acc * 150), 150)
    sd = (" ±%.3f sd" % np.std([d["real"]["acc"] for d in L])) if len(L) > 1 else ""
    lines.append(f"| {NAMES[a]} | {L[0]['n_train']} | {acc:.3f}{sd} ({lo:.2f}-{hi:.2f}) | {f1:.3f} | {ta:.3f} | {len(L)} |")
lines += ["", "## Per-class recall on the real-world test set (mean over seeds)", "",
          "| Arm | " + " | ".join(CLS) + " |", "|---|" + "---|" * len(CLS)]
for a in order:
    if a not in res:
        continue
    rec = [np.mean([d["real"]["recall"][c] for d in res[a]]) for c in CLS]
    lines.append(f"| {NAMES[a]} | " + " | ".join(f"{r:.2f}" for r in rec) + " |")
best = max((a for a in ("A", "B", "C", "D", "E", "F", "G") if a in res), key=lambda a: np.mean([d["real"]["macro_f1"] for d in res[a]]), default=None)
if best:
    lines += ["", f"## 'Not sure' threshold on the real-world set, best arm by macro-F1 = {best}", "",
              "| confidence threshold | share answered | accuracy on answered |", "|---|---|---|"]
    tt = threshold_table(best, res[best][0]["seed"])
    for t, cov, accu in tt:
        lines.append(f"| {t:.1f} | {cov:.2f} | {accu:.3f} |")
    # confusion matrix figure
    cm = np.sum([np.array(d["real"]["confusion"]) for d in res[best]], axis=0)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    cmn = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(8)); ax.set_yticks(range(8)); ax.set_xticklabels(CLS, rotation=45, ha="right"); ax.set_yticklabels(CLS)
    for i in range(8):
        for j in range(8):
            if cm[i, j]:
                ax.text(j, i, int(cm[i, j]), ha="center", va="center", color="white" if cmn[i, j] > .5 else "black", fontsize=8)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(f"Real-world test set: arm {best}")
    fig.tight_layout(); fig.savefig(R / "confusion_best.png", dpi=150)
    # arms bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    arms = [a for a in order if a in res]
    ax.bar(range(len(arms)), [np.mean([d["real"]["acc"] for d in res[a]]) for a in arms], color="#0b6e4f", label="real-world")
    ax.bar([i + .35 for i in range(len(arms))], [np.mean([d["trashnet"]["acc"] for d in res[a]]) for a in arms], width=.35, color="#bbbbbb", label="TrashNet test")
    ax.set_xticks([i + .17 for i in range(len(arms))]); ax.set_xticklabels([a.upper() if len(a) == 1 else a for a in arms]); ax.set_ylim(0, 1); ax.legend(); ax.set_ylabel("accuracy")
    fig.tight_layout(); fig.savefig(R / "arms.png", dpi=150)
open(R / "summary.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
