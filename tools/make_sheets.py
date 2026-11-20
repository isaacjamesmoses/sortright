import cv2, json, random, sys, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
C = ROOT/"data"/(sys.argv[3] if len(sys.argv)>3 else "web_test_candidates"); OUT = ROOT/"data"/"review_sheets"; OUT.mkdir(exist_ok=True, parents=True)
cls, n = sys.argv[1], int(sys.argv[2]); pref = (sys.argv[4] if len(sys.argv)>4 else "T_") if len(sys.argv)>3 else ""
face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") if hasattr(cv2, "CascadeClassifier") else None
files = sorted((C/cls).glob("*.jpg"))
if len(sys.argv) <= 3: random.Random(1).shuffle(files)
keep = []
for f in files:
    im = cv2.imread(str(f))
    if im is None: continue
    g = cv2.cvtColor(cv2.resize(im, (400, int(400*im.shape[0]/im.shape[1]))), cv2.COLOR_BGR2GRAY)
    if face is not None and len(face.detectMultiScale(g, 1.1, 6, minSize=(30, 30))) > 0: continue
    keep.append(f)
    if len(keep) >= n: break
json.dump([f.name for f in keep], open(OUT/f"{pref}{cls}_order.json", "w"))
W, H, cols = 320, 240, 5
for s in range(0, len(keep), 20):
    chunk = keep[s:s+20]; rows = (len(chunk)+cols-1)//cols
    sheet = np.full((rows*H, cols*W, 3), 255, np.uint8)
    for i, f in enumerate(chunk):
        im = cv2.imread(str(f)); h, w = im.shape[:2]; k = min(W/w, (H-4)/h)
        im = cv2.resize(im, (int(w*k), int(h*k))); y, x = (i//cols)*H, (i % cols)*W
        sheet[y:y+im.shape[0], x:x+im.shape[1]] = im
        cv2.rectangle(sheet, (x, y), (x+44, y+26), (0, 0, 0), -1); cv2.putText(sheet, str(s+i), (x+4, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.imwrite(str(OUT/f"{pref}{cls}_{s//20}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
print(cls, len(keep), "kept from", len(files))
