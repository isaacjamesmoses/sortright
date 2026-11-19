# SortRight results (real-world test set n=150; TrashNet test n=251)

| Arm | Train images | Real-world accuracy (95% CI) | Real-world macro-F1 | TrashNet accuracy | Seeds |
|---|---|---|---|---|---|
| Baseline: frozen backbone + linear probe (TrashNet) | 2024 | 0.500 (0.42-0.58) | 0.379 | 0.873 | 1 |
| CLIP zero-shot (comparison) | 0 | 0.580 (0.50-0.66) | 0.570 | 0.633 | 1 |
| A. Fine-tuned, TrashNet only | 2024 | 0.420 ±0.007 sd (0.34-0.50) | 0.329 | 0.928 | 2 |
| B. + strong classic augmentation | 2024 | 0.403 ±0.003 sd (0.33-0.48) | 0.291 | 0.934 | 2 |
| C. + synthetic composites | 3965 | 0.377 ±0.003 sd (0.31-0.46) | 0.280 | 0.924 | 2 |
| D. + composites + generated organic/other | 4205 | 0.440 ±0.020 sd (0.36-0.52) | 0.386 | 0.920 | 2 |
| E. + real TACO training crops | 2551 | 0.630 ±0.017 sd (0.55-0.70) | 0.552 | 0.926 | 2 |
| F. All data (real + composites + synthetic classes) | 4732 | 0.583 ±0.003 sd (0.50-0.66) | 0.551 | 0.926 | 2 |
| G. Real + more generated organic/other (no composites) | 3847 | 0.657 ±0.017 sd (0.58-0.73) | 0.633 | 0.916 | 2 |

## Per-class recall on the real-world test set (mean over seeds)

| Arm | plastic | paper | cardboard | glass | metal | organic | general_waste | other |
|---|---|---|---|---|---|---|---|---|
| Baseline: frozen backbone + linear probe (TrashNet) | 0.54 | 0.67 | 0.80 | 0.14 | 0.83 | 0.00 | 0.43 | 0.00 |
| CLIP zero-shot (comparison) | 0.46 | 0.27 | 0.70 | 0.29 | 0.58 | 0.92 | 0.82 | 0.38 |
| A. Fine-tuned, TrashNet only | 0.36 | 0.60 | 0.65 | 0.25 | 0.83 | 0.00 | 0.27 | 0.00 |
| B. + strong classic augmentation | 0.48 | 0.70 | 0.75 | 0.07 | 0.75 | 0.00 | 0.09 | 0.00 |
| C. + synthetic composites | 0.50 | 0.60 | 0.65 | 0.14 | 0.69 | 0.00 | 0.07 | 0.00 |
| D. + composites + generated organic/other | 0.61 | 0.63 | 0.68 | 0.14 | 0.67 | 0.38 | 0.09 | 0.06 |
| E. + real TACO training crops | 0.71 | 0.47 | 0.97 | 0.25 | 0.88 | 0.00 | 0.70 | 0.50 |
| F. All data (real + composites + synthetic classes) | 0.64 | 0.47 | 0.78 | 0.29 | 0.83 | 0.23 | 0.57 | 0.50 |
| G. Real + more generated organic/other (no composites) | 0.71 | 0.33 | 0.88 | 0.39 | 0.88 | 0.77 | 0.55 | 0.50 |

## 'Not sure' threshold on the real-world set, best arm by macro-F1 = G

| confidence threshold | share answered | accuracy on answered |
|---|---|---|
| 0.0 | 1.00 | 0.640 |
| 0.4 | 0.87 | 0.708 |
| 0.5 | 0.65 | 0.786 |
| 0.6 | 0.53 | 0.823 |
| 0.7 | 0.41 | 0.823 |
| 0.8 | 0.27 | 0.850 |
| 0.9 | 0.12 | 0.889 |
