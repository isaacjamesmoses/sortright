"""TACO TRAINING crops (image_id % 4 != 0 only) using 640px thumbnails. Never touches the held-out test pool."""
import json, random, requests, collections
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
ROOT = Path(__file__).resolve().parent.parent
D = json.load(open(ROOT/"data/taco/annotations.json"))
exec(open(ROOT/"tools/build_taco_candidates.py").read().split("cat2cls")[0].split("MAP = ")[1].join(["MAP = ", ""]) if False else "")
MAP = {"plastic":[4,5,7,21,27,43,44,45,47,49,55,24],"paper":[30,32,33,34],"cardboard":[13,14,15,17,18,19],"glass":[6,26,9,23],
       "metal":[0,8,10,11,12,50,52],"organic":[25],"general_waste":[22,31,36,39,42,46,57,59,58],"other":[1,51,53,48,54]}
cat2cls = {c: k for k, v in MAP.items() for c in v}
imgs = {i["id"]: i for i in D["images"]}
PER = {"plastic":160,"paper":90,"cardboard":110,"glass":100,"metal":130,"organic":20,"general_waste":130,"other":30}
rng = random.Random(3); by = collections.defaultdict(list)
for a in D["annotations"]:
    if a["image_id"] % 4 == 0 or a["category_id"] not in cat2cls: continue
    w, h = a["bbox"][2:]; im = imgs[a["image_id"]]; s = 640/max(im["width"], im["height"])
    if min(w, h)*s < 50: continue
    by[cat2cls[a["category_id"]]].append(a)
sel = {}
for c, l in by.items():
    rng.shuffle(l); sel[c] = l[:PER[c]]; print(c, len(l), "->", len(sel[c]))
need = sorted({a["image_id"] for l in sel.values() for a in l}); print("images", len(need), flush=True)
cache = ROOT/"data/taco/train_thumbs"; cache.mkdir(parents=True, exist_ok=True)
def get(i):
    p = cache/f"{i}.jpg"
    if p.exists(): return
    for u in (imgs[i]["flickr_640_url"], imgs[i]["flickr_url"]):
        try:
            r = requests.get(u, timeout=(10, 40))
            if r.status_code == 200: p.write_bytes(r.content); return
        except Exception: pass
import os
if not os.environ.get('SKIP_DL'):
    with ThreadPoolExecutor(32) as ex: list(ex.map(get, need))
meta = {}
for c, l in sel.items():
    od = ROOT/"data/train_taco"/c; od.mkdir(parents=True, exist_ok=True)
    for a in l:
        p = cache/f"{a['image_id']}.jpg"
        if not p.exists(): continue
        im = Image.open(p).convert("RGB"); W, H = im.size; o = imgs[a["image_id"]]
        sx, sy = W/o["width"], H/o["height"]; x, y, w, h = a["bbox"]; x, w, y, h = x*sx, w*sx, y*sy, h*sy
        m = .2; box = (int(max(0, x-m*w)), int(max(0, y-m*h)), int(min(W, x+w*(1+m))), int(min(H, y+h*(1+m))))
        fn = f"{a['image_id']}_{a['id']}.jpg"; im.crop(box).save(od/fn, quality=92); meta[f"{c}/{fn}"] = dict(image_id=a["image_id"], cat=a["category_id"])
json.dump(meta, open(ROOT/"data/train_taco/meta.json", "w")); print("done", len(meta))
