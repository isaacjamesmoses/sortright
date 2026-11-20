"""Evaluate saved checkpoints (models/<arm>_s<seed>.pt) on the everyday-items set.
usage: python tools/eval_everyday.py G_s0,G_s1 [test|train|all]   -> prints per-class recall and writes results/everyday_<name>.json"""
import sys, json, numpy as np, torch
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import train as t

def main():
    names = sys.argv[1].split(",")
    split = sys.argv[2] if len(sys.argv) > 2 else "test"
    items = t.everyday("test") + t.everyday("train") if split == "all" else t.everyday(split)
    y = np.array([c for _, c in items])
    for n in names:
        m = t.build()
        m.load_state_dict(torch.load(t.ROOT / f"models/{n}.pt", map_location="cuda"))
        P = t.predict(m, items)
        res = t.metrics(P, y, sorted(set(y.tolist())))
        conf = P.max(1); pred = P.argmax(1)
        res["answered_at_0.6"] = float((conf >= .6).mean())
        res["acc_answered_at_0.6"] = float((pred[conf >= .6] == y[conf >= .6]).mean()) if (conf >= .6).any() else None
        res["wrong_at_conf_ge_0.8"] = int(((pred != y) & (conf >= .8)).sum())
        res["n"] = len(items)
        json.dump(res, open(t.ROOT / f"results/everyday_{n}_{split}.json", "w"), indent=1)
        np.savez(t.ROOT / f"results/everyday_probs_{n}_{split}.npz", P=P, y=y)
        print(n, split, f"n={len(items)} acc {res['acc']:.3f} macroF1 {res['macro_f1']:.3f} answered@.6 {res['answered_at_0.6']:.2f} acc_answered {res['acc_answered_at_0.6']} confident-wrong(>=.8) {res['wrong_at_conf_ge_0.8']}")
        print("  recall:", {k: round(v, 2) for k, v in res["recall"].items()})


if __name__ == "__main__":
    main()
