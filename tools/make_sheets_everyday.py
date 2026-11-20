"""Contact sheets for reviewing everyday_candidates, grouped by search query (cap per query).
usage: python tools/make_sheets_everyday.py <class> <cap_per_query> [excluded,queries]  -> data/review_sheets/E2_<class>_<k>.jpg + E2_<class>_order.json"""
import cv2, json, sys, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
meta = json.load(open(ROOT / "data/everyday_candidates/candidates.json"))
cls, cap = sys.argv[1], int(sys.argv[2])
excl = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else set()
OUT = ROOT / "data/review_sheets"
byq = {}
for k, v in sorted(meta.items()):
    if v["cls_query"] == cls and v["query"] not in excl and (ROOT / k).exists():
        byq.setdefault(v["query"], []).append(k)
keep = [k for q in byq for k in byq[q][:cap]]
json.dump(keep, open(OUT / f"E2_{cls}_order.json", "w"))
W, H, cols = 320, 240, 5
for s in range(0, len(keep), 20):
    chunk = keep[s:s + 20]; rows = (len(chunk) + cols - 1) // cols
    sheet = np.full((rows * H, cols * W, 3), 255, np.uint8)
    for i, k in enumerate(chunk):
        im = cv2.imread(str(ROOT / k))
        if im is None: continue
        h, w = im.shape[:2]; f = min(W / w, (H - 4) / h)
        im = cv2.resize(im, (int(w * f), int(h * f))); y, x = (i // cols) * H, (i % cols) * W
        sheet[y:y + im.shape[0], x:x + im.shape[1]] = im
        cv2.rectangle(sheet, (x, y), (x + 44, y + 26), (0, 0, 0), -1); cv2.putText(sheet, str(s + i), (x + 4, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.imwrite(str(OUT / f"E2_{cls}_{s // 20}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
print(cls, len(keep), {q: min(len(v), cap) for q, v in byq.items()})
