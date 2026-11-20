"""Does averaging two seeds of the same arm help? usage: python tools/ensemble_test.py G_s0,G_s1
Reports single models and the probability average on the 150-photo real-world set and on the 191 everyday photos.
(Arm G never saw either set, so both are fair for G.)"""
import sys, json, numpy as np, torch
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import train as t


def report(name, P, y):
    r = t.metrics(P, y, sorted(set(y.tolist())))
    conf, pred = P.max(1), P.argmax(1)
    a = conf >= .6
    out = dict(acc=r["acc"], f1=r["macro_f1"], cardboard=r["recall"].get("cardboard"), general_waste=r["recall"].get("general_waste"),
               paper=r["recall"].get("paper"), answered=float(a.mean()), acc_answered=float((pred[a] == y[a]).mean()) if a.any() else None,
               confident_wrong=int(((pred != y) & (conf >= .8)).sum()), n=len(y))
    print(f"  {name:10s} acc {out['acc']:.3f} f1 {out['f1']:.3f} cardboard {out['cardboard']:.2f} gen.waste {out['general_waste']:.2f} "
          f"| answered {out['answered']:.2f} acc_on_answered {out['acc_answered']:.3f} | conf-wrong {out['confident_wrong']}")
    return out


def main():
    names = sys.argv[1].split(",")
    models = []
    for n in names:
        m = t.build()
        m.load_state_dict(torch.load(t.ROOT / f"models/{n}.pt", map_location="cuda"))
        models.append(m)
    sets = {"real150": t.realtest(), "everyday191": t.everyday("test") + t.everyday("train"), "everyday_test94": t.everyday("test")}
    res = {}
    for sname, items in sets.items():
        y = np.array([c for _, c in items])
        Ps = [t.predict(m, items) for m in models]
        print(sname, "n =", len(y))
        res[sname] = {n: report(n, P, y) for n, P in zip(names, Ps)}
        res[sname]["average"] = report("average", np.mean(Ps, 0), y)
    json.dump(res, open(t.ROOT / "results/ensemble_test.json", "w"), indent=1)


if __name__ == "__main__":
    main()
