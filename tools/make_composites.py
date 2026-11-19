"""Synthetic composites: cut TrashNet items (plain white background -> simple mask) and paste them on generated backgrounds
with random scale/rotation/position, colour matching and a soft shadow. TrashNet train split only."""
import random, json, numpy as np, cv2
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
split = json.load(open(ROOT/"data/splits.json"))
bgs = sorted((ROOT/"data/synth/backgrounds").glob("*.jpg")); assert bgs
rng = random.Random(11); out = ROOT/"data/synth/composites"; n = 0
def mask_of(im):
    """Foreground mask of a TrashNet item (plain light background): GrabCut seeded with the image border as background."""
    h0, w0 = im.shape[:2]; k = 256/max(h0, w0); sm = cv2.resize(im, (int(w0*k), int(h0*k)))
    h, w = sm.shape[:2]; gm = np.full((h, w), cv2.GC_PR_FGD, np.uint8); b = 6
    gm[:b, :] = gm[-b:, :] = cv2.GC_BGD; gm[:, :b] = gm[:, -b:] = cv2.GC_BGD
    bg = np.median(np.concatenate([sm[:b].reshape(-1, 3), sm[-b:].reshape(-1, 3), sm[:, :b].reshape(-1, 3), sm[:, -b:].reshape(-1, 3)]), axis=0)
    far = np.abs(sm.astype(np.int16) - bg).max(axis=2) < 14; gm[far & (gm == cv2.GC_PR_FGD)] = cv2.GC_PR_BGD
    try:
        cv2.grabCut(sm, gm, None, np.zeros((1, 65)), np.zeros((1, 65)), 3, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        return None
    m = np.where((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return None
    m2 = np.zeros_like(m); cv2.drawContours(m2, [max(cnts, key=cv2.contourArea)], -1, 255, -1)
    return cv2.resize(m2, (w0, h0), interpolation=cv2.INTER_NEAREST) if 0.03 < m2.mean()/255 < 0.97 else None
for rel in split["trashnet_train"]:
    cls = rel.split("/")[0]; im = cv2.imread(str(ROOT/"data/trashnet/dataset-resized"/rel))
    if im is None: continue
    m = mask_of(im)
    if m is None: continue
    ys, xs = np.where(m > 0); im, m = im[ys.min():ys.max()+1, xs.min():xs.max()+1], m[ys.min():ys.max()+1, xs.min():xs.max()+1]
    bg = cv2.imread(str(rng.choice(bgs))); bg = cv2.resize(bg, (384, 384))
    s = rng.uniform(.35, .8)*384/max(im.shape[:2]); im2 = cv2.resize(im, None, fx=s, fy=s); m2 = cv2.resize(m, None, fx=s, fy=s)
    ang = rng.uniform(-35, 35); h, w = im2.shape[:2]; M = cv2.getRotationMatrix2D((w/2, h/2), ang, 1)
    im2 = cv2.warpAffine(im2, M, (w, h), borderValue=(255, 255, 255)); m2 = cv2.warpAffine(m2, M, (w, h))
    # colour/brightness match to background + random lighting
    k = rng.uniform(.65, 1.15); im2 = np.clip(im2.astype(np.float32)*k*(0.85+0.3*bg.mean()/255), 0, 255).astype(np.uint8)
    x, y = rng.randint(0, max(0, 384-w)), rng.randint(0, max(0, 384-h)); canvas = bg.copy()
    roi = canvas[y:y+h, x:x+w]; hh, ww = roi.shape[:2]; mm = m2[:hh, :ww]
    sh = cv2.GaussianBlur(mm, (0, 0), 7); sh = np.roll(sh, (6, 6), axis=(0, 1)).astype(np.float32)/255*0.45
    roi[:] = (roi*(1-sh[..., None])).astype(np.uint8)
    mm = cv2.erode(mm, np.ones((3, 3), np.uint8)); a = cv2.GaussianBlur(mm, (0, 0), 1.2).astype(np.float32)[..., None]/255; roi[:] = (im2[:hh, :ww]*a + roi*(1-a)).astype(np.uint8)
    if rng.random() < .4: canvas = cv2.GaussianBlur(canvas, (0, 0), rng.uniform(.5, 1.6))
    d = out/cls; d.mkdir(parents=True, exist_ok=True); cv2.imwrite(str(d/f"{Path(rel).stem}.jpg"), canvas, [cv2.IMWRITE_JPEG_QUALITY, 90]); n += 1
print("composites", n)
