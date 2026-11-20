"""Build the demo gallery assets: web/demo_images/*.jpg + credits.json (Wikimedia Commons photos that the deployed model
classifies correctly with confidence >= 0.70; all CC0 / public domain / CC BY / CC BY-SA, credited on the page),
then the offline package SortRight_Demo_Offline/ (works without internet; run START_DEMO.bat).
usage: python tools/build_demo.py"""
import csv, json, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/everyday_set"
OUT = ROOT / "web/demo_images"
# (class, filename fragment): ordered so that consecutive photos differ in material
PICK = [("cardboard", "Corrugated_Cardboard.JPG"), ("metal", "Bordonado_lata"), ("plastic", "A_bottle_of_Aveeno"),
        ("glass", "Angkor_beer_bottle_glass"), ("organic", "Ashtray_with_coffee"), ("paper", "Envelope_timbrado"),
        ("cardboard", "Cardboard_boxes_and_their_usage"), ("metal", "Drinking_can_ring-pull"), ("plastic", "Dasani_Water_Bottle"),
        ("glass", "Angkor_beer_bottle.jpg"), ("organic", "Broken_eggshell"), ("paper", "Kazbulbucijade"),
        ("cardboard", "Box_being_filled_with_wood_wool"), ("metal", "Aluminium-foil"), ("plastic", "Multi-use_water_bottle"),
        ("glass", "Tour_de_Vin"), ("organic", "BananaSkin")]
rows = list(csv.DictReader(open(SRC / "labels.csv", encoding="utf-8")))
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
credits = []
for k, (cls, frag) in enumerate(PICK, 1):
    r = next(x for x in rows if x["label"] == cls and frag in x["file"])
    im = Image.open(SRC / r["file"]).convert("RGB")
    im.thumbnail((720, 720))
    name = f"{k:02d}.jpg"
    im.save(OUT / name, quality=86)
    credits.append(dict(file=name, title=r["title"].replace("File:", "").rsplit(".", 1)[0], author=r["author"], licence=r["licence"], url=r["url"]))
json.dump(credits, open(OUT / "credits.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(credits), "photos ->", OUT)

# ---- offline package
PK = ROOT / "SortRight_Demo_Offline"
(PK / "model").mkdir(parents=True, exist_ok=True)
(PK / "ort").mkdir(exist_ok=True)
html = (ROOT / "web/demo.html").read_text(encoding="utf-8")
html = html.replace('<script src="https://cdn.jsdelivr.net/npm/onnxruntime-web@1.17.3/dist/ort.min.js"></script>', '<script src="ort/ort.min.js"></script>')
html = html.replace("const ORT_PATH=null;", 'const ORT_PATH="ort/";')
(PK / "demo.html").write_text(html, encoding="utf-8")
for f in ("sortright.onnx", "config.json", "mobileclip_s0_vision.onnx", "mobileclip_text.json", "MOBILECLIP_LICENSE.txt"):
    shutil.copy(ROOT / "web/model" / f, PK / "model" / f)
if (PK / "demo_images").exists():
    shutil.rmtree(PK / "demo_images")
shutil.copytree(OUT, PK / "demo_images")
(PK / "START_DEMO.bat").write_text(
    "@echo off\r\ncd /d \"%~dp0\"\r\necho Starting the SortRight demo at http://localhost:8000/demo.html  (close this window to stop)\r\n"
    "start \"\" http://localhost:8000/demo.html\r\n"
    "where py >nul 2>nul && (py -m http.server 8000) || (python -m http.server 8000)\r\n", encoding="utf-8")
(PK / "README.txt").write_text(
    "SortRight offline demo\r\n1. Double-click START_DEMO.bat (needs Python, already installed on this laptop).\r\n"
    "2. The browser opens http://localhost:8000/demo.html. Click a photo, or use the arrow keys.\r\n"
    "3. No internet is needed. Nothing is uploaded. Close the black window to stop.\r\n"
    "Photos: Wikimedia Commons, credited under each photo (CC0 / public domain / CC BY / CC BY-SA).\r\n", encoding="utf-8")
print("offline package ready:", PK)
