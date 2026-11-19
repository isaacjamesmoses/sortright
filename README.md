# SortRight: which bin does this go in?

A phone web app that looks at one item and suggests the material and the recycling bin, or says "I am not sure". The model runs inside the browser (ONNX Runtime Web): no upload, no account, no payment. Coursework project for MAIB AI 221 Computer Vision with Applications (S P Jain School of Global Management), Final Group Project 8 (Environment).

**Live app:** `https://<your-github-username>.github.io/sortright/`  (see "Deploy" below)

## What it does
- Take a photo or choose one; get the material, the bin name and colour, and a one-line reason.
- Below 60% confidence, or for unusual items, it says "I am not sure, check your local guide".
- Bins tab: edit bin names and colours to match your city (colour-blind-safe defaults, always shown with text).
- Help tab: how it works, limits, model summary.

## Headline results (150 held-out real-world photos; details in `results/summary.md`)
| Model | Real-world accuracy | Real-world macro-F1 | TrashNet (studio) accuracy |
|---|---|---|---|
| Linear probe on frozen backbone (baseline) | 0.50 | 0.38 | 0.87 |
| CLIP zero-shot (comparison, not deployed) | 0.58 | 0.57 | 0.63 |
| Fine-tuned on TrashNet only (A, 2 seeds) | 0.42 | 0.33 | 0.93 |
| + real TACO crops (E, 2 seeds) | 0.63 | 0.55 | 0.93 |
| **+ real TACO + generated organic/other (G, deployed, 2 seeds)** | **0.66** | **0.63** | 0.92 |

Findings: studio-photo accuracy (about 91-94%) overstates real-world accuracy (about 40% for TrashNet-only training); real in-the-wild data is the biggest improvement; images generated with Stable Diffusion (SD-Turbo) fixed classes with no real data (organic recall 0.00 -> 0.77); pasting TrashNet items onto generated backgrounds did not help. Static int8 quantisation of the whole network collapsed accuracy (0.65 -> 0.39), so only the classifier head is int8 (13 MB, identical predictions).

## Repository layout
```
docs/                    the web app (index.html + model/sortright.onnx + model/config.json)  <- GitHub Pages serves this folder
tools/                   data building, training, evaluation, export, figures
results/                 summary.md, per-arm JSON, confusion matrix, failure gallery, figures
data/realworld_test_set/ labels.csv with source URL, licence, author for each of the 150 test images
MODEL_CARD.md            intended use, data, metrics, known failures
THIRD_PARTY_NOTICES.md   licences of data and models
```

## Run it locally
```bash
cd docs
python -m http.server 8000      # then open http://localhost:8000
```
Camera access needs https or localhost.

## Reproduce (needs a GPU for the diffusion step; everything else runs on a laptop)
```bash
pip install -r requirements.txt
python tools/build_taco_candidates.py   # held-out real-world crops from TACO (image_id % 4 == 0)
python tools/build_taco_train.py        # training crops (image_id % 4 != 0)
python tools/make_splits.py
python tools/gen_diffusion.py backgrounds ; python tools/gen_diffusion.py classes ; python tools/gen_diffusion.py classes_plus   # SD-Turbo
python tools/make_composites.py
python tools/train.py probe,A,B,C,D,E,F,G 0,1   # all arms, two seeds
python tools/eval_clip.py
python tools/analyse.py ; python tools/export_onnx.py G 0 ; python tools/quantise_dynamic.py
```
The 150-image test set is built by `tools/build_final_testset.py` after visual review of contact sheets (`tools/make_sheets.py`). The test images are not redistributed here; `labels.csv` lists their sources.

## Deploy (GitHub Pages, free)
1. Create a public repository named `sortright`, upload this folder.
2. Settings > Pages > Source: "Deploy from a branch", branch `main`, folder `/docs`.
3. Wait about a minute; the app is live at the URL above. Open it once on the phone and laptop before the demo (the first load downloads the 13 MB model; later loads are cached).

## Limits
Indicative only; rules differ by city; clear glass vs plastic, foil, film and mixed items are often wrong; test photos are litter on the ground, not bin-side phone photos; organic and 'other' were learned mostly from synthetic images. See `MODEL_CARD.md`.

## Licences
See `THIRD_PARTY_NOTICES.md`. Coursework use only.
