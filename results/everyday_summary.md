# Everyday-items stress test (second real-world set: product shots, packaging, items on tables and floors)

Source: Wikimedia Commons (CC0 / public domain / CC BY / CC BY-SA), reviewed by eye. 191 images: 97 'train' half (used only by arm H, repeated x4), 94 'test' half (held out). Licences per image: data/everyday_set/labels.csv. Mean of 2 seeds.

| Model | n | accuracy | macro-F1 | share answered at 0.6 | accuracy on answered | confident errors (conf >= 0.8) |
|---|---|---|---|---|---|---|
| A. TrashNet only (all 191, never saw this set) | 191 | 0.518 | 0.406 | 0.38 | 0.74 | 4.0 |
| E. + real TACO crops (all 191, never saw this set) | 191 | 0.555 | 0.442 | 0.47 | 0.69 | 11.0 |
| G. + generated organic/other (previously deployed) (all 191, never saw this set) | 191 | 0.644 | 0.597 | 0.43 | 0.81 | 7.0 |
| G (held-out half) | 94 | 0.628 | 0.579 | 0.44 | 0.78 | 3.0 |
| H (held-out half) | 94 | 0.676 | 0.624 | 0.56 | 0.83 | 2.5 |

## Per-class recall, held-out half (mean of 2 seeds)

| Model | plastic | paper | cardboard | glass | metal | organic | general_waste | other |
|---|---|---|---|---|---|---|---|---|
| G | 0.67 | 0.94 | 0.46 | 0.81 | 0.56 | 0.75 | 0.17 | 0.32 |
| H | 0.71 | 1.00 | 0.50 | 0.81 | 0.62 | 0.88 | 0.17 | 0.41 |

## Per-class recall of G on all 191 images (mean of 2 seeds)

| plastic | paper | cardboard | glass | metal | organic | general_waste | other |
|---|---|---|---|---|---|---|---|
| 0.72 | 0.90 | 0.48 | 0.78 | 0.68 | 0.71 | 0.14 | 0.45 |

Printed/packaged cardboard called paper by G: 12 of 48 cardboard images (both seeds pooled). General waste correct: 5 of 36.
