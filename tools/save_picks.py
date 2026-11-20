import json, sys
cls = sys.argv[1]; idx = [int(i) for i in sys.argv[2].split(",")]
o = json.load(open(f"data/review_sheets/E2_{cls}_order.json"))
json.dump({cls: [o[i] for i in idx]}, open(f"data/review_sheets/final_{cls}.json", "w")); print(cls, len(idx))
