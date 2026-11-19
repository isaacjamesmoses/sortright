import json, csv, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RS = ROOT/"data/review_sheets"; OUT = ROOT/"data/realworld_test_set"
if OUT.exists(): shutil.rmtree(OUT)
taco_meta = json.load(open(ROOT/"data/web_test_candidates_taco/meta.json"))
com_meta = json.load(open(ROOT/"data/web_test_candidates/candidates.json"))
SEL_T = {  # indices on the TACO review sheets (T_<class>_<n>.jpg)
 "plastic": [2,3,5,10,11,12,14,15,16,17,21,22,25,26,28,29,36,37,38,44,47,48,53,55,57,13,54,34],
 "paper": [0,1,2,3,4,5,6,7,8,9,10,13,19,21],
 "cardboard": [0,2,3,4,6,8,11,12,13,14,15,16,26,30,31,34,35,36,37,38],
 "glass": [0,1,2,5,8,9,10,11,12,14,15,16,17,18],
 "metal": [0,1,2,3,4,5,7,9,10,12,15,22,23,24,29,30,31,32,33,35,14,18,19,28],
 "organic": [0,2,3],
 "general_waste": [2,4,5,6,7,8,9,10,12,13,14,15,16,19,20,22,23,24,25,28,38,39,11,17,0,26,31,32],
 "other": [0,1,2,3,4,5,6,7],
}
SEL_C = {"organic": [6,9,13,14,22,23,24,28,32,35], "paper": [0]}  # Wikimedia Commons candidates (sheets <class>_<n>.jpg)
rows = []
def add(cls, src_path, source, info):
    d = OUT/cls; d.mkdir(parents=True, exist_ok=True)
    n = len(list(d.glob("*.jpg"))) + 1
    name = f"{cls}_{n:03d}.jpg"; shutil.copy(src_path, d/name)
    rows.append(dict(file=f"{cls}/{name}", label=cls, source=source, **info))
for cls, idxs in SEL_T.items():
    order = json.load(open(RS/f"T_{cls}_order.json"))
    for i in idxs:
        fn = order[i]; m = taco_meta.get(f"{cls}/{fn}", {})
        add(cls, ROOT/"data/web_test_candidates_taco"/cls/fn, "TACO", dict(original_name=fn, detail=m.get("taco_category", ""), url=m.get("original_url", ""), licence="TACO dataset (Proenca & Simoes 2020); annotations CC BY 4.0; Flickr photo licences per TACO", author=""))
for cls, idxs in SEL_C.items():
    order = json.load(open(RS/f"{cls}_order.json"))
    for i in idxs:
        fn = order[i]; key = f"data/web_test_candidates/{cls}/{fn}"; m = com_meta.get(key, {})
        add(cls, ROOT/key, "Wikimedia Commons", dict(original_name=fn, detail=m.get("query", ""), url=m.get("page", ""), licence=m.get("licence", ""), author=m.get("author", "")))
with open(OUT/"labels.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file","label","source","original_name","detail","url","licence","author"]); w.writeheader(); w.writerows(rows)
import collections; print(collections.Counter(r["label"] for r in rows), len(rows))
print(collections.Counter(r["source"] for r in rows))
