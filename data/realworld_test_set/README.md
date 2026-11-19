# SortRight real-world test set (150 images)

Built 2026-11-19 from open internet images, because collecting 150 own photos on campus was not possible (no permission, items not available). The unit coordinator (Dr. Khalid Ezzeldeen) told the student to use internet images "of the quality requested" (real-world, not studio). Confirm this in writing before submission.

- **Labels:** by material (plastic, paper, cardboard, glass, metal, organic, general_waste, other). See `labels.csv` (file, label, source, original name, TACO category, source URL, licence, author).
- **Sources:** 139 crops from TACO (litter photographed in the wild; one annotated item per crop, 20% context margin) and 11 photos from Wikimedia Commons (CC0 / CC BY / CC BY-SA). Per-image author and licence for Commons images are in `labels.csv`; attribution must be reproduced in the report/README.
- **Leakage control:** TACO images with `image_id % 4 == 0` form the test pool (list in `../taco/test_image_ids.json`). **All TACO images used for training, validation, or synthetic-composite backgrounds/cut-outs must have image_id % 4 != 0.** Never train or tune on this folder; evaluate once at the end.
- **Counts:** plastic 28, general_waste 28, metal 24, cardboard 20, paper 15, glass 14, organic 13, other 8 (= 150).
- **Known limits:** labels follow TACO's categories mapped to the 7 SortRight materials (mapping in `../../tools/build_taco_candidates.py` and `build_final_testset.py`); some items are genuinely ambiguous (clear plastic film, drink cartons, painted metal). Organic is thin in TACO, so 10 of its 13 images come from Commons and are cleaner (often studio-like) than the rest. Photos are litter on the ground more than bin-side scenes. State these in the report.
- **Review:** images were selected by eye from contact sheets; none contain a recognisable person; labels were checked visually.
