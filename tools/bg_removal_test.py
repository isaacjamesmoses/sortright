"""Does removing the background first help? Offline test, no training.
usage: python tools/bg_removal_test.py <u2net.onnx path> <cache_dir> [G_s0,G_s1]
Foreground mask from U2-Net (salient object). Variants scored with the unchanged arm-G checkpoints:
  original   : photo as is
  white      : item kept, background replaced by white, same framing
  crop_white : item cropped to its mask bounding box (10% margin), pasted on white, square
Sets: 150 real-world photos, 191 everyday photos."""
import sys, json, numpy as np, torch
from pathlib import Path
from PIL import Image
import onnxruntime as ort
sys.path.insert(0, str(Path(__file__).resolve().parent))
import train as t

MEAN, STD = np.array([0.485, 0.456, 0.406], np.float32), np.array([0.229, 0.224, 0.225], np.float32)


def mask_of(sess, im):
    x = np.asarray(im.resize((320, 320), Image.LANCZOS), np.float32)
    x = x / max(x.max(), 1e-6)
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
    y = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    y = (y - y.min()) / max(y.max() - y.min(), 1e-6)
    return Image.fromarray((y * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR)


def variants(sess, p):
    im = Image.open(p).convert("RGB")
    m = mask_of(sess, im)
    a = np.asarray(m, np.float32)[..., None] / 255.0
    arr = np.asarray(im, np.float32)
    white = Image.fromarray((arr * a + 255 * (1 - a)).astype(np.uint8))
    ys, xs = np.where(a[..., 0] > 0.5)
    if len(xs) < 50:           # no object found: keep as is
        return white, white
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    mx, my = int(0.1 * (x1 - x0)), int(0.1 * (y1 - y0))
    box = (max(0, x0 - mx), max(0, y0 - my), min(im.width, x1 + mx), min(im.height, y1 + my))
    c = white.crop(box)
    s = max(c.size)
    sq = Image.new("RGB", (s, s), (255, 255, 255))
    sq.paste(c, ((s - c.width) // 2, (s - c.height) // 2))
    return white, sq


def report(P, y):
    r = t.metrics(P, y, sorted(set(y.tolist())))
    conf, pred = P.max(1), P.argmax(1)
    a = conf >= .6
    return dict(acc=r["acc"], f1=r["macro_f1"], cardboard=r["recall"].get("cardboard"), general_waste=r["recall"].get("general_waste"),
                paper=r["recall"].get("paper"), glass=r["recall"].get("glass"), answered=float(a.mean()),
                acc_answered=float((pred[a] == y[a]).mean()) if a.any() else None, n=len(y))


def main():
    mp, cache = sys.argv[1], Path(sys.argv[2])
    names = (sys.argv[3] if len(sys.argv) > 3 else "G_s0,G_s1").split(",")
    sess = ort.InferenceSession(mp, providers=["CPUExecutionProvider"])
    models = []
    for n in names:
        m = t.build()
        m.load_state_dict(torch.load(t.ROOT / f"models/{n}.pt", map_location="cuda"))
        models.append(m)
    sets = {"real150": t.realtest(), "everyday191": t.everyday("test") + t.everyday("train")}
    res = {}
    for sname, items in sets.items():
        y = np.array([c for _, c in items])
        d = {v: [] for v in ("white", "crop_white")}
        for i, (p, _) in enumerate(items):
            w, c = variants(sess, p)
            for v, img in (("white", w), ("crop_white", c)):
                f = cache / sname / v / f"{i:04d}.jpg"
                f.parent.mkdir(parents=True, exist_ok=True)
                img.save(f, quality=95)
                d[v].append((f, int(y[i])))
        print(sname, "n =", len(y), flush=True)
        res[sname] = {}
        for vname, its in (("original", items), ("white", d["white"]), ("crop_white", d["crop_white"])):
            Ps = [t.predict(m, its) for m in models]
            per = [report(P, y) for P in Ps]
            avg = {k: (float(np.mean([r[k] for r in per])) if per[0][k] is not None else None) for k in per[0] if k != "n"}
            res[sname][vname] = dict(mean_of_seeds=avg, per_seed=per)
            print(f"  {vname:10s} acc {avg['acc']:.3f} f1 {avg['f1']:.3f} cardboard {avg['cardboard']:.2f} gen.waste {avg['general_waste']:.2f} "
                  f"paper {avg['paper']:.2f} glass {avg['glass']:.2f} | answered {avg['answered']:.2f} acc_answered {avg['acc_answered']:.3f}", flush=True)
    json.dump(res, open(t.ROOT / "results/bg_removal_test.json", "w"), indent=1)


if __name__ == "__main__":
    main()
