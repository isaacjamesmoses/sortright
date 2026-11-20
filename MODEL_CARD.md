# Model card: SortRight material classifier

**Model.** MobileNetV3-Large (ImageNet-pretrained, torchvision) fine-tuned in two phases (3 epochs head, 7 epochs all layers, AdamW, one-cycle LR, label smoothing 0.1) to classify one item into 8 classes: plastic, paper, cardboard, glass, metal, organic, general waste, other. Exported to ONNX (opset 17); classifier-head weights int8 (dynamic quantisation); 13.1 MB. Input: 224x224 RGB after resize-256 and centre crop, ImageNet normalisation. Version: arm G, seed 0.

**Intended use.** An indicative assistant on a phone for a member of the public at a campus or office recycling point: suggests which material an item is and which bin to use. A human decides. Runs in the browser; no image is uploaded or stored.

**Out-of-scope use.** Not an official recycling rule; not for compliance, fines or auditing; not for sorting hazardous waste (batteries, chemicals, sharps); not for monitoring people; not for industrial sorting lines; not validated for other camera setups, other countries' packaging, or multiple items per photo.

**Training data.** TrashNet (2,024 training photos, studio, MIT); TACO training crops (527 crops from images with id not divisible by 4; annotations CC BY 4.0, photo licences per Flickr); about 1,000 images generated with SD-Turbo for organic and 'other' (synthetic). Class mapping: TrashNet 'trash' and TACO plastic film, wrappers, crisp packets, foam and cigarettes map to 'general waste'; TACO drink cartons are excluded.

**Evaluation data.** 150 held-out real-world images (139 TACO crops from images never used for training; 11 Wikimedia Commons photos), labelled by material: plastic 28, general waste 28, metal 24, cardboard 20, paper 15, glass 14, organic 13, other 8. Plus the TrashNet test split (251 studio photos, 6 classes).

**Results (mean of 2 seeds, arm G).** Real-world accuracy 0.66 (seeds: 0.64, 0.67; 95% interval for one run about 0.56-0.73 with n=150), macro-F1 0.63. TrashNet test accuracy 0.92. Per-class recall on real-world photos: metal 0.88, cardboard 0.88, organic 0.77, plastic 0.71, general waste 0.55, other 0.50, glass 0.39, paper 0.33. Comparison on the same photos: TrashNet-only fine-tune 0.41 accuracy, linear probe 0.50, CLIP zero-shot 0.58 (not deployable at this size). See `results/summary.md`.

**'Not sure' behaviour.** The app answers 'not sure' when top confidence is below 0.6, or when the top class is 'other'. Threshold chosen on real-photo validation images (TACO validation crops), not on the test set. On the 150 test photos at 0.6 about half are answered, at roughly 80% accuracy.

**Second test: everyday items.** A separate set of 191 openly licensed Wikimedia Commons photos of everyday items (product shots, packaging, items on tables and floors; reviewed by eye; per-image licences in `data/everyday_set/labels.csv`, not redistributed) was never used to train the deployed model. Arm G scored 0.64 accuracy / macro-F1 0.60 on it (two seeds). Printed or packaged cardboard was called paper in 12 of 48 cases (a printed pizza box was called 'paper' at 87% confidence), and general waste was right in only 5 of 36 cases. Retraining with half of this set (arm H, 97 images repeated 4x) reached 0.68 vs 0.63 for G on the held-out half (n=94, within sampling noise) and 0.66 vs 0.66 on the original 150 photos; H is not deployed. See `results/everyday_summary.md`.

**Subgroup / known failures.** Glass is often called plastic (clear or brown bottles in grass or sand); crumpled foil and film are confused with general waste or each other; plain paper is weak; organic and 'other' were learned mostly from synthetic images, so real food waste looks different from the training images; transparent, dirty, wet or mixed items are unreliable. No people appear in the data, so no demographic subgroup analysis applies; coverage is limited to the litter, packaging styles and countries represented in TACO and TrashNet.

**Ethical considerations.** Recycling rules differ between cities: bin names and colours are editable and every answer is labelled indicative. Colour-blind-safe palette, text label next to every colour. No data leaves the device. Synthetic images are used only for training and are labelled as synthetic. Licences: see `THIRD_PARTY_NOTICES.md` (SD-Turbo is non-commercial).

**Caveats.** The test set is small (n=150) and not bin-side phone photos; some TACO labels are ambiguous; results come from two training seeds. Do not read the 0.92 TrashNet number as real-world accuracy.
