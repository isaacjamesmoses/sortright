"""Fixed zero-shot text prompts (identical to tools/eval_clip.py; not tuned on any test image)."""
PROMPTS = {
    "plastic": ["a photo of a plastic bottle or plastic cup", "a photo of a plastic container or plastic lid", "a photo of plastic waste"],
    "paper": ["a photo of crumpled paper", "a photo of a sheet of paper or newspaper", "a photo of paper waste"],
    "cardboard": ["a photo of a cardboard box", "a photo of flattened cardboard or a carton", "a photo of cardboard packaging"],
    "glass": ["a photo of a glass bottle", "a photo of a glass jar", "a photo of broken glass"],
    "metal": ["a photo of a metal drink can", "a photo of a tin can or aluminium foil", "a photo of scrap metal"],
    "organic": ["a photo of food waste", "a photo of a fruit peel or apple core", "a photo of organic waste"],
    "general_waste": ["a photo of a snack wrapper or plastic film", "a photo of a foam polystyrene piece or a cigarette", "a photo of dirty rubbish"],
    "other": ["a photo of a battery or an electrical cable", "a photo of clothing or a shoe", "a photo of electronic waste or rope"],
}
