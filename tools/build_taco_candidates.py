"""Build held-out real-world candidate crops from TACO (litter in the wild) for the SortRight test set.
Split is by IMAGE (id % 4 == 0 -> test-eligible), so no test image is ever used for training.
Each crop = one annotated item + 20% context margin, taken from the full-size photo."""
import json, random, requests, io, collections
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
D = json.load(open(ROOT/"data/taco/annotations.json"))
MAP = {
 "plastic": [4,5,7,21,27,43,44,45,47,49,55,24],
 "paper": [30,32,33,34],
 "cardboard": [13,14,15,17,18,19],
 "glass": [6,26,9,23],
 "metal": [0,8,10,11,12,50,52],
 "organic": [25],
 "general_waste": [22,31,36,39,42,46,57,59,58],
 "other": [1,51,53,48,54],
}
cat2cls = {c: k for k, v in MAP.items() for c in v}
imgs = {i["id"]: i for i in D["images"]}
test_ids = {i for i in imgs if i % 4 == 0}
json.dump(sorted(test_ids), open(ROOT/"data/taco/test_image_ids.json", "w"))
cands = collections.defaultdict(list)
for a in D["annotations"]:
    if a["image_id"] not in test_ids or a["category_id"] not in cat2cls: continue
    x, y, w, h = a["bbox"]
    cl = cat2cls[a["category_id"]]
    lo = (90, 140) if cl in ("paper", "glass") else (150, 220)
    if min(w, h) < lo[0] or max(w, h) < lo[1]: continue
    cands[cl].append(a)
rng = random.Random(7)
PER = {"plastic": 40, "paper": 35, "cardboard": 35, "glass": 30, "metal": 35, "organic": 8, "general_waste": 45, "other": 15}
cat_name = {c["id"]: c["name"] for c in D["categories"]}
sel = {}; meta = {}
for cls, lst in cands.items():
    rng.shuffle(lst); per_img = collections.Counter(); per_cat = collections.Counter(); out = []
    for a in lst:
        if per_img[a["image_id"]] >= (3 if cls in ("paper","glass") else 2) or per_cat[a["category_id"]] >= max(6, PER[cls] // 3): continue
        per_img[a["image_id"]] += 1; per_cat[a["category_id"]] += 1; out.append(a)
        if len(out) >= PER[cls]: break
    sel[cls] = out; print(cls, len(lst), "->", len(out))
need = sorted({a["image_id"] for v in sel.values() for a in v})
print("images to download:", len(need))
cache = ROOT/"data/taco/test_images"; cache.mkdir(parents=True, exist_ok=True)
for n, iid in enumerate(need):
    p = cache/f"{iid}.jpg"
    if p.exists(): continue
    for url in (imgs[iid]["flickr_url"], imgs[iid].get("flickr_640_url")):
        try:
            r = requests.get(url, timeout=(10, 40))
            if r.status_code == 200: p.write_bytes(r.content); break
        except Exception as e: print("retry/skip", iid, type(e).__name__, flush=True)
    if n % 25 == 0: print("dl", n, flush=True)
for cls, lst in sel.items():
    od = ROOT/"data/web_test_candidates_taco"/cls; od.mkdir(parents=True, exist_ok=True)
    for a in lst:
        p = cache/f"{a['image_id']}.jpg"
        if not p.exists(): continue
        im = Image.open(p).convert("RGB"); W, H = im.size
        sx = W / imgs[a["image_id"]]["width"]; sy = H / imgs[a["image_id"]]["height"]
        x, y, w, h = a["bbox"]; x, w, y, h = x*sx, w*sx, y*sy, h*sy
        m = 0.2; x0, y0, x1, y1 = max(0, x-m*w), max(0, y-m*h), min(W, x+w*(1+m)), min(H, y+h*(1+m))
        c = im.crop((int(x0), int(y0), int(x1), int(y1)))
        if max(c.size) > 800: c.thumbnail((800, 800))
        fn = f"taco_{a['image_id']}_{a['id']}.jpg"; c.save(od/fn, quality=90)
        meta[f"{cls}/{fn}"] = dict(source="TACO", image_id=a["image_id"], ann_id=a["id"], taco_category=cat_name[a["category_id"]], cls=cls,
                                    original_url=imgs[a["image_id"]]["flickr_url"], bbox=a["bbox"])
json.dump(meta, open(ROOT/"data/web_test_candidates_taco/meta.json", "w"), indent=1)
print("done", len(meta))
