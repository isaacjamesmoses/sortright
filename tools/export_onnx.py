"""Step 1 (python 3.14 + torch): export a trained arm to ONNX fp32. Step 2 is quantise_eval.py. Usage: python export_onnx.py F 0"""
import sys, json, csv, time, numpy as np, torch, torch.nn as nn, torchvision
from pathlib import Path
from PIL import Image
import torchvision.transforms as T

ROOT = Path(__file__).resolve().parent.parent
arm, seed = sys.argv[1], int(sys.argv[2])
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
OUT = ROOT / "web" / "model"
OUT.mkdir(parents=True, exist_ok=True)
m = torchvision.models.mobilenet_v3_large()
m.classifier[3] = nn.Linear(m.classifier[3].in_features, 8)
m.load_state_dict(torch.load(ROOT / f"models/{arm}_s{seed}.pt", map_location="cpu"))
m.eval()
x = torch.randn(1, 3, 224, 224)
fp32 = OUT / "sortright_fp32.onnx"
torch.onnx.export(m, x, str(fp32), input_names=["image"], output_names=["logits"], opset_version=17, dynamic_axes=None, dynamo=False)
print("exported fp32", round(fp32.stat().st_size / 1e6, 1), "MB", flush=True)
np.save(ROOT / "models/_ref_in.npy", x.numpy()); np.save(ROOT / "models/_ref_out.npy", m(x).detach().numpy())

