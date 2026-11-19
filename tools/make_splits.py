import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rng = random.Random(5); S = {"trashnet_train": [], "trashnet_val": [], "trashnet_test": [], "taco_train": [], "taco_val": []}
for c in sorted((ROOT/"data/trashnet/dataset-resized").iterdir()):
    fs = sorted(c.glob("*.jpg")); rng.shuffle(fs); n = len(fs)
    S["trashnet_test"] += [f"{c.name}/{f.name}" for f in fs[:int(.1*n)]]; S["trashnet_val"] += [f"{c.name}/{f.name}" for f in fs[int(.1*n):int(.2*n)]]
    S["trashnet_train"] += [f"{c.name}/{f.name}" for f in fs[int(.2*n):]]
t = ROOT/"data/train_taco"
if t.exists():
    meta = json.load(open(t/"meta.json")); items = sorted(meta); rng.shuffle(items)
    cut = int(.85*len(items)); S["taco_train"] = items[:cut]; S["taco_val"] = items[cut:]
    assert all(meta[i]["image_id"] % 4 != 0 for i in items)
json.dump(S, open(ROOT/"data/splits.json", "w")); print({k: len(v) for k, v in S.items()})
