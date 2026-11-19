"""Generate synthetic images with SD-Turbo (pretrained text-to-image diffusion, openly available weights).
 mode backgrounds: empty real-looking surfaces to composite TrashNet cut-outs on.
 mode classes: images of items for classes with almost no public data (organic, other)."""
import sys, torch, random
from pathlib import Path
from diffusers import AutoPipelineForText2Image
ROOT = Path(__file__).resolve().parent.parent
mode = sys.argv[1]
pipe = AutoPipelineForText2Image.from_pretrained(str(ROOT / "models" / "sd-turbo"), torch_dtype=torch.float16, variant="fp16", local_files_only=True).to("cuda")
pipe.set_progress_bar_config(disable=True)
STYLE = ", realistic smartphone photo, natural lighting, slightly imperfect, not studio"
if mode == "backgrounds":
    P = ["a wooden desk surface, top-down view", "grey concrete pavement ground, top-down close-up", "short green grass lawn, top-down close-up",
         "the inside of a dirty black rubbish bin with a plastic liner, looking down", "a tiled kitchen floor, top-down", "sandy ground with a few dry leaves, top-down",
         "a university cafeteria table with a tray, top-down, no food", "brown soil and dirt ground, top-down", "an outdoor asphalt road surface, top-down", "a white office table top, top-down"]
    N, out = 14, ROOT/"data/synth/backgrounds"
else:
    CL = {"organic": ["a banana peel on the ground", "an apple core on a table", "an orange peel on pavement", "leftover vegetable peels and food scraps in a bin",
                      "eggshells on a kitchen counter", "a half eaten piece of bread on a table", "a pile of fruit peels on grass", "a rotten tomato on the ground",
                      "used tea bags in a bin", "chicken bones and food leftovers on a plate", "fallen leaves and twigs on the ground", "a bitten apple on a desk"],
          "other": ["a used AA battery lying on the ground", "a tangled electrical cable on a table", "a single old sock on the floor", "a broken phone charger on a desk",
                    "a used lightbulb on the ground", "an old broken headphone set on a table", "a cracked toy on the floor", "a discarded t-shirt on the ground",
                    "a used marker pen on a desk", "an old computer mouse on a table", "a pair of broken spectacles on the floor", "a worn rubber shoe on the pavement"]}
    P, N, out = None, 10, ROOT/"data/synth/classes"
    if mode == "classes_plus":
        CL["organic"] += ["a rotten banana on the ground", "chewed corn cob on pavement", "a watermelon rind on grass", "potato peels in a kitchen sink", "a mango stone on the ground",
                          "grape stems and leftover fruit on a plate", "used coffee grounds and a paper filter in a bin", "a half eaten sandwich on a bench", "pizza crust on a tray", "dry bread pieces on pavement"]
        CL["other"] += ["a used alkaline battery near a drain", "a tangled phone charging cable on pavement", "a pair of old jeans on the floor", "a discarded sneaker on grass",
                        "an old computer keyboard on a desk", "a broken remote control on the floor", "a light bulb in a bin", "a toy car on pavement", "a hairbrush on the floor", "a wooden spoon and rope on the ground"]
        N, out = 24, ROOT/"data/synth/classes_plus"
g = torch.Generator("cuda")
jobs = [("", p) for p in P] if P else [(k, p) for k, v in CL.items() for p in v]
for ci, (sub, p) in enumerate(jobs):
    d = out/sub if sub else out; d.mkdir(parents=True, exist_ok=True)
    for k in range(N):
        fn = d/f"{ci:02d}_{k:02d}.jpg"
        if fn.exists(): continue
        g.manual_seed(1000*ci + k + (500 if mode == "classes_plus" else 0))
        im = pipe(p + STYLE, num_inference_steps=2, guidance_scale=0.0, generator=g, height=512, width=512).images[0]
        im.save(fn, quality=92)
    print(sub, p, flush=True)
print("done")
