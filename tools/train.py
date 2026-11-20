"""SortRight training / evaluation. Arms (same backbone, same schedule, same seeds):
 A trashnet            TrashNet only, basic augmentation
 B trashnet_aug        TrashNet only, strong classic augmentation
 C +composites         B + synthetic composites (TrashNet cut-outs on diffusion backgrounds)
 D +composites+synth   C + diffusion-generated images for organic / other
 E +taco               B + real in-the-wild TACO training crops (image_id % 4 != 0)
 F all                 E + composites + synthetic classes
 probe                 frozen backbone + logistic regression on TrashNet (Week 7 baseline)
Evaluation: real-world test set (data/realworld_test_set, 150 images) and TrashNet test.
Test sets are never used for training or tuning."""
import sys, json, csv, time, numpy as np, torch, torch.nn as nn
from pathlib import Path
from PIL import Image
import torchvision.transforms as T, torchvision
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix

ROOT = Path(__file__).resolve().parent.parent
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
CI = {c: i for i, c in enumerate(CLS)}
MAPTN = {"plastic": "plastic", "paper": "paper", "cardboard": "cardboard", "glass": "glass", "metal": "metal", "trash": "general_waste"}
S = json.load(open(ROOT / "data/splits.json"))


def tn(lst):
    return [(ROOT / "data/trashnet/dataset-resized" / r, CI[MAPTN[r.split("/")[0]]]) for r in lst]


def taco(lst):
    return [(ROOT / "data/train_taco" / r, CI[r.split("/")[0]]) for r in lst]


def folder(base):
    out = []
    for d in sorted(Path(base).iterdir()):
        if d.is_dir():
            out += [(f, CI[MAPTN.get(d.name, d.name)]) for f in sorted(d.glob("*.jpg"))]
    return out


def realtest():
    rows = list(csv.DictReader(open(ROOT / "data/realworld_test_set/labels.csv", encoding="utf-8")))
    return [(ROOT / "data/realworld_test_set" / r["file"], CI[r["label"]]) for r in rows]


norm = T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
basic = T.Compose([T.RandomResizedCrop(224, scale=(.6, 1)), T.RandomHorizontalFlip(), T.ToTensor(), norm])
strong = T.Compose([T.RandomResizedCrop(224, scale=(.3, 1)), T.RandomHorizontalFlip(), T.RandomRotation(25),
                    T.ColorJitter(.4, .4, .4, .05), T.RandomApply([T.GaussianBlur(5, (.1, 2))], p=.3),
                    T.RandomPerspective(.2, p=.3), T.ToTensor(), norm])
evalt = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(), norm])


class DS(torch.utils.data.Dataset):
    def __init__(s, items, tf):
        s.items, s.tf = items, tf

    def __len__(s):
        return len(s.items)

    def __getitem__(s, i):
        p, y = s.items[i]
        return s.tf(Image.open(p).convert("RGB")), y


def arm_items(arm):
    A = tn(S["trashnet_train"])
    comp = folder(ROOT / "data/synth/composites") if (ROOT / "data/synth/composites").exists() else []
    syn = folder(ROOT / "data/synth/classes") if (ROOT / "data/synth/classes").exists() else []
    tc = taco(S["taco_train"])
    plus = folder(ROOT / "data/synth/classes_plus") if (ROOT / "data/synth/classes_plus").exists() else []
    return {"G": A + tc + syn + plus, "H": A + tc + syn + plus + everyday("train") * 4, "A": A, "B": A, "C": A + comp, "D": A + comp + syn,
            "E": A + tc, "F": A + tc + comp + syn}[arm]


def everyday(split):
    """Second real-world set (tools/collect_everyday.py + manual review): split is 'train' or 'test' (held out)."""
    f = ROOT / "data/everyday_set/labels.csv"
    if not f.exists():
        return []
    return [(ROOT / "data/everyday_set" / r["file"], CI[r["label"]]) for r in csv.DictReader(open(f, encoding="utf-8")) if r["split"] == split]


def val_items(arm):
    return tn(S["trashnet_val"]) + (taco(S["taco_val"]) if arm in ("E", "F", "G", "H") else [])


dev = "cuda"


def build():
    m = torchvision.models.mobilenet_v3_large(weights=torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    m.classifier[3] = nn.Linear(m.classifier[3].in_features, len(CLS))
    return m.to(dev)


@torch.no_grad()
def predict(m, items):
    m.eval()
    dl = torch.utils.data.DataLoader(DS(items, evalt), batch_size=64, num_workers=4)
    P = []
    for x, _ in dl:
        with torch.autocast("cuda", dtype=torch.float16):
            P.append(torch.softmax(m(x.to(dev)).float(), 1).cpu())
    return torch.cat(P).numpy()


def metrics(P, y, present):
    pred = P.argmax(1)
    f1 = f1_score(y, pred, labels=present, average="macro", zero_division=0)
    rec = {CLS[c]: float(((pred == c) & (y == c)).sum() / max(1, (y == c).sum())) for c in present}
    return dict(acc=float(accuracy_score(y, pred)), macro_f1=float(f1), recall=rec,
                confusion=confusion_matrix(y, pred, labels=list(range(len(CLS)))).tolist())


def run(arm, seed, epochs1=3, epochs2=7):
    torch.manual_seed(seed)
    np.random.seed(seed)
    items = arm_items(arm)
    tf = basic if arm == "A" else strong
    dl = torch.utils.data.DataLoader(DS(items, tf), batch_size=64, shuffle=True, num_workers=6, drop_last=True,
                                     persistent_workers=True)
    m = build()
    crit = nn.CrossEntropyLoss(label_smoothing=.1)
    scaler = torch.amp.GradScaler()

    def phase(params, lr, ep):
        opt = torch.optim.AdamW(params, lr=lr, weight_decay=1e-2)
        sch = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=ep * len(dl), pct_start=.15)
        for e in range(ep):
            m.train()
            tot = 0
            for x, y in dl:
                x, y = x.to(dev), y.to(dev)
                with torch.autocast("cuda", dtype=torch.float16):
                    loss = crit(m(x), y)
                opt.zero_grad()
                scaler.scale(loss).backward()
                scaler.step(opt)
                scaler.update()
                sch.step()
                tot += loss.item()
            print(f"  {arm} s{seed} loss {tot / len(dl):.3f}", flush=True)

    for p in m.features.parameters():
        p.requires_grad = False
    phase(m.classifier.parameters(), 1e-3, epochs1)
    for p in m.features.parameters():
        p.requires_grad = True
    phase(m.parameters(), 2e-4, epochs2)
    real = realtest()
    yr = np.array([y for _, y in real])
    Pr = predict(m, real)
    tt = tn(S["trashnet_test"])
    yt = np.array([y for _, y in tt])
    Pt = predict(m, tt)
    vi = val_items(arm)
    yv = np.array([y for _, y in vi])
    Pv = predict(m, vi)
    res = dict(arm=arm, seed=seed, n_train=len(items), real=metrics(Pr, yr, list(range(8))),
               trashnet=metrics(Pt, yt, [0, 1, 2, 3, 4, 6]))
    ev = everyday("test")
    if ev:
        ye = np.array([y for _, y in ev])
        Pe = predict(m, ev)
        res["everyday"] = metrics(Pe, ye, sorted(set(ye.tolist())))
        np.savez(ROOT / f"results/probs_{arm}_s{seed}.npz", real=Pr, yr=yr, tn=Pt, yt=yt, val=Pv, yv=yv, ev=Pe, ye=ye)
    else:
        np.savez(ROOT / f"results/probs_{arm}_s{seed}.npz", real=Pr, yr=yr, tn=Pt, yt=yt, val=Pv, yv=yv)
    json.dump(res, open(ROOT / f"results/{arm}_s{seed}.json", "w"), indent=1)
    torch.save(m.state_dict(), ROOT / f"models/{arm}_s{seed}.pt")
    print(f"RESULT {arm} s{seed} n={len(items)} real acc {res['real']['acc']:.3f} f1 {res['real']['macro_f1']:.3f}"
          f" | trashnet acc {res['trashnet']['acc']:.3f}", flush=True)


def probe(seed=0):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    m = build()
    m.classifier[3] = nn.Identity()
    m.eval()

    @torch.no_grad()
    def feats(items):
        dl = torch.utils.data.DataLoader(DS(items, evalt), batch_size=64, num_workers=4)
        F = []
        for x, _ in dl:
            F.append(m(x.to(dev)).cpu())
        return torch.cat(F).numpy()

    tr = arm_items("A")
    Xtr = feats(tr)
    ytr = [y for _, y in tr]
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(C=0.1, max_iter=3000).fit(sc.transform(Xtr), ytr)

    def pr(items):
        P = np.zeros((len(items), len(CLS)))
        P[:, clf.classes_] = clf.predict_proba(sc.transform(feats(items)))
        return P

    real = realtest()
    yr = np.array([y for _, y in real])
    Pr = pr(real)
    tt = tn(S["trashnet_test"])
    yt = np.array([y for _, y in tt])
    Pt = pr(tt)
    res = dict(arm="probe", seed=seed, n_train=len(tr), real=metrics(Pr, yr, list(range(8))),
               trashnet=metrics(Pt, yt, [0, 1, 2, 3, 4, 6]))
    np.savez(ROOT / "results/probs_probe_s0.npz", real=Pr, yr=yr, tn=Pt, yt=yt)
    json.dump(res, open(ROOT / "results/probe_s0.json", "w"), indent=1)
    print(f"RESULT probe real acc {res['real']['acc']:.3f} f1 {res['real']['macro_f1']:.3f}"
          f" | trashnet acc {res['trashnet']['acc']:.3f}", flush=True)


if __name__ == "__main__":
    arms = sys.argv[1].split(",")
    seeds = [int(s) for s in sys.argv[2].split(",")]
    for a in arms:
        for s in seeds:
            t = time.time()
            probe(s) if a == "probe" else run(a, s)
            print(f"  time {time.time() - t:.0f}s", flush=True)
