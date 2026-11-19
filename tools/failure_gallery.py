"""Gallery of real-world test images the deployed model (arm G) got wrong, with true/predicted label and confidence."""
import sys, csv, numpy as np, cv2
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
arm = sys.argv[1] if len(sys.argv) > 1 else "G"
z = np.load(ROOT / f"results/probs_{arm}_s0.npz")
P = z["real"]; y = z["yr"]
rows = list(csv.DictReader(open(ROOT / "data/realworld_test_set/labels.csv", encoding="utf-8")))
wrong = [i for i in range(len(y)) if P[i].argmax() != y[i]]
wrong.sort(key=lambda i: -P[i].max())      # most confident mistakes first
sel = wrong[:20]
W, H = 256, 256
sheet = np.full((4 * (H + 34), 5 * W, 3), 255, np.uint8)
for k, i in enumerate(sel):
    im = cv2.imread(str(ROOT / "data/realworld_test_set" / rows[i]["file"])); h, w = im.shape[:2]; s = min(W / w, H / h)
    im = cv2.resize(im, (int(w * s), int(h * s))); r, c = divmod(k, 5); y0, x0 = r * (H + 34), c * W
    sheet[y0 + 34:y0 + 34 + im.shape[0], x0:x0 + im.shape[1]] = im
    cv2.putText(sheet, f"true: {CLS[y[i]]}", (x0 + 4, y0 + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    cv2.putText(sheet, f"pred: {CLS[P[i].argmax()]} {P[i].max():.0%}", (x0 + 4, y0 + 29), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 200), 1)
cv2.imwrite(str(ROOT / f"results/failures_{arm}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
print(len(wrong), "mistakes;", "shown", len(sel))
