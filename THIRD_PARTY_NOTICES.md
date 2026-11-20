# Third-party data, models and licences

SortRight is a student coursework project (MAIB AI 221, S P Jain School of Global Management). Not for commercial use.

| Asset | Use here | Licence / terms |
|---|---|---|
| TrashNet (Thung & Yang, 2016) | training and a studio-photo test split | MIT (repository garythung/trashnet) |
| TACO: Trash Annotations in Context (Proença & Simões, 2020) | training crops and the real-world test crops | Annotations CC BY 4.0; each photo carries its own open Flickr licence (see TACO documentation). Crops listed in `labels.csv` with source URLs |
| Wikimedia Commons photos (11 images in the test set) | test set | CC0 / CC BY / CC BY-SA; author and licence per image in `data/realworld_test_set/labels.csv` |
| MobileNetV3-Large ImageNet weights (torchvision) | backbone initialisation | BSD-3-Clause (torchvision); ImageNet terms for the weights |
| Stable Diffusion SD-Turbo (Stability AI) | generated backgrounds and organic/other images | Stability AI Community licence (non-commercial research use) |
| LAION-2B OpenCLIP ViT-B/32 | zero-shot comparison only (not deployed) | MIT code; LAION-2B weights under the open_clip licence |
| ONNX Runtime Web | in-browser inference | MIT |
| Ultralytics YOLO models | not used in the deployed model | (AGPL-3.0; course backbone only for the Week 7 exercises) |

Generated images are synthetic and are labelled as such in this repository (`data/synth/`). They contain no real people or personal data.

## MobileCLIP-S0 (optional second model in the app)
Apple MobileCLIP-S0 image encoder, ONNX int8 conversion by Xenova (https://huggingface.co/Xenova/mobileclip_s0), used as supplied under the Apple software licence in `docs/model/MOBILECLIP_LICENSE.txt` (copy retained as required). Source: https://github.com/apple/ml-mobileclip. Used here for education and research; no recycling-specific training of this model.
