"""Assemble data/everyday_set from the manually reviewed picks (data/review_sheets/final_<class>.json).
Fixed 50/50 split per class (seeded shuffle): 'train' images may be used for training arm H, 'test' images are held out."""
import json, csv, random, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
meta = json.load(open(ROOT / "data/everyday_candidates/candidates.json"))
OUT = ROOT / "data/everyday_set"; shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
picks = {}
for c in ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]:
    paths = json.load(open(ROOT / f"data/review_sheets/final_{c}.json"))[c]
    if c == "paper": paths += json.load(open(ROOT / "data/review_sheets/final_paper2.json"))["paper"]
    picks[c] = list(dict.fromkeys(paths))
rows = []
for c, paths in picks.items():
    random.Random(7).shuffle(paths)
    (OUT / c).mkdir()
    for i, p in enumerate(paths):
        m = meta[p]; dst = OUT / c / Path(p).name
        shutil.copy(ROOT / p, dst)
        rows.append(dict(file=f"{c}/{dst.name}", label=c, split="train" if i % 2 == 0 else "test", title=m["title"], licence=m["licence"],
                         author=m["author"], url=m["page"], query=m["query"]))
with open(OUT / "labels.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
import collections
print(collections.Counter((r["label"], r["split"]) for r in rows)); print(len(rows))
