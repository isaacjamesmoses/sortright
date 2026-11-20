"""Build the final-presentation deck (python-pptx) with numbers read live from results/*.json so slides never disagree with the report."""
import json, glob, numpy as np
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
CLS = ["plastic", "paper", "cardboard", "glass", "metal", "organic", "general_waste", "other"]
res = {}
for f in glob.glob(str(R / "*_s*.json")):
    if Path(f).name.startswith("everyday_"):
        continue
    d = json.load(open(f))
    res.setdefault(d["arm"].replace("clip_zeroshot", "clip"), []).append(d)


def m(a, key, sub="real"):
    return float(np.mean([d[sub][key] for d in res[a]]))


def rec(a, c):
    return float(np.mean([d["real"]["recall"][c] for d in res[a]]))


def ns(a):
    return len(res[a])


GREEN = RGBColor(0x0B, 0x6E, 0x4F)
INK = RGBColor(0x16, 0x20, 0x2A)
MUTE = RGBColor(0x55, 0x60, 0x6B)
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
blank = prs.slide_layouts[6]


def slide(title, sub=None):
    s = prs.slides.add_slide(blank)
    tb = s.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(1.0))
    p = tb.text_frame.paragraphs[0]
    p.text = title
    p.font.size, p.font.bold, p.font.color.rgb = Pt(34), True, INK
    if sub:
        t2 = s.shapes.add_textbox(Inches(0.6), Inches(1.15), Inches(12.1), Inches(0.5))
        q = t2.text_frame.paragraphs[0]
        q.text = sub
        q.font.size, q.font.color.rgb = Pt(18), MUTE
    bar = s.shapes.add_shape(1, Inches(0.6), Inches(0.3), Inches(0.9), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = GREEN
    bar.line.fill.background()
    return s


def bullets(s, items, x=0.6, y=1.8, w=12.1, h=5.2, size=22):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, t in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ("• " + t) if not t.startswith("  ") else ("– " + t.strip())
        p.font.size = Pt(size if not t.startswith("  ") else size - 4)
        p.font.color.rgb = INK
        p.space_after = Pt(8)
    return tb


def pic(s, path, x, y, w=None, h=None):
    if Path(path).exists():
        s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)


def table(s, rows, x, y, w, colw=None, size=14):
    nr, nc = len(rows), len(rows[0])
    t = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(0.4 * nr)).table
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.text = str(v)
            for p in c.text_frame.paragraphs:
                p.font.size = Pt(size)
                p.font.bold = (i == 0)
    if colw:
        for j, cw in enumerate(colw):
            t.columns[j].width = Inches(cw)


G = "G"
# 1 title
s = prs.slides.add_slide(blank)
tb = s.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(11.5), Inches(2.5))
tf = tb.text_frame
tf.text = "SortRight"
tf.paragraphs[0].font.size, tf.paragraphs[0].font.bold, tf.paragraphs[0].font.color.rgb = Pt(66), True, GREEN
p = tf.add_paragraph(); p.text = "Which bin does this go in? A phone recycling assistant that runs in your browser."; p.font.size = Pt(26); p.font.color.rgb = INK
p = tf.add_paragraph(); p.text = "MAIB AI 221 Computer Vision with Applications  |  Final project 8 (Environment)  |  Isaac James"; p.font.size = Pt(18); p.font.color.rgb = MUTE

# 2 problem
s = slide("The problem", "Contaminated recycling bins cost money and send material to landfill")
bullets(s, ["People are unsure which bin an item belongs in, so the wrong things end up in the wrong bin",
            "User: a student or office worker at a campus recycling point, using a phone",
            "Decision: which bin. A confident wrong answer contaminates a bin and teaches a bad habit, so it costs more than 'not sure'",
            "So the app must say 'I am not sure' instead of guessing, and the bin colours must be editable because rules differ by city",
            "Constraints from the brief: free to use, no sign-up, models open and running on the phone, public URL"])

# 3 data
s = slide("Data", "Studio photos are easy. Real photos are the test.")
table(s, [["Source", "What", "Used for", "Licence"],
          ["TrashNet", "2,527 studio photos, 6 classes", "training; studio test split", "MIT"],
          ["TACO", "litter photographed in the wild", "training crops + real-world test crops (held out by image id)", "annotations CC BY 4.0; photo licences per Flickr"],
          ["Wikimedia Commons", "11 photos", "real-world test set", "CC0 / CC BY / CC BY-SA"],
          ["SD-Turbo (generated)", "backgrounds, organic and 'other' items", "synthetic training data", "Stability AI community licence"]],
      0.6, 1.9, 12.1, [2.2, 3.2, 4.2, 2.5], 13)
bullets(s, ["Real-world test set: 150 images, 8 classes, never used for training or tuning (leak-proof split by TACO image id). The unit coordinator allowed internet images instead of self-collected photos",
            "Organic waste and 'other' barely exist in public datasets, which is where generative AI comes in"], y=5.3, h=2.0, size=16)

# 4 method
s = slide("Method", "Baselines first, then a fine-tuned network exported to ONNX")
bullets(s, ["Baseline 1 (Week 7): frozen ImageNet backbone + linear probe",
            "Baseline 2 (Lecture F): CLIP zero-shot with a prompt ensemble, no training",
            "Main model: MobileNetV3-Large, two-phase fine-tuning (head, then all layers), label smoothing, strong augmentation",
            "Export to ONNX, classifier-head weights int8: 13 MB, runs in the phone browser with ONNX Runtime Web (no upload)",
            "'Not sure' when the top confidence is below 0.6 or the item is 'other'; bin colours are editable and colour-blind-safe",
            "Everything evaluated on the same 150 real-world photos, same backbone, same schedule, same seeds"])

# 5 experiment
s = slide("Generative AI experiment", "Does generated data help on real photos? Eight arms, same model")
table(s, [["Arm", "Training data", "Images"],
          ["A", "TrashNet only", res["A"][0]["n_train"]], ["B", "A + strong classic augmentation", res["B"][0]["n_train"]],
          ["C", "B + composites: TrashNet cut-outs pasted on SD-Turbo backgrounds", res["C"][0]["n_train"]],
          ["D", "C + SD-Turbo organic/other images (240)", res["D"][0]["n_train"]],
          ["E", "B + real TACO crops (no synthetic)", res["E"][0]["n_train"]],
          ["F", "E + composites + 240 synthetic organic/other", res["F"][0]["n_train"]],
          ["G", "E + ~1,000 synthetic organic/other (no composites)", res["G"][0]["n_train"]]],
      0.6, 1.9, 12.1, [1.0, 9.0, 2.1], 16)
bullets(s, ["Metric: accuracy and macro-F1 on 150 real-world photos, per-class recall, 'not sure' rate"], y=5.6, h=1, size=18)

# 6 results
s = slide("Results: the gap is large", "Fine-tuned on studio photos: ~91-94% on TrashNet, about 40% on real photos")
pic(s, R / "arms.png", 0.5, 1.8, w=7.2)
rows = [["Arm", "Real acc", "Real macro-F1", "TrashNet acc"]]
for a, name in (("probe", "Probe"), ("clip", "CLIP zero-shot"), ("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E"), ("F", "F"), ("G", "G")):
    if a in res:
        rows.append([name + (f" ({ns(a)} seeds)" if ns(a) > 1 else ""), f"{m(a, 'acc'):.2f}", f"{m(a, 'macro_f1'):.2f}", f"{m(a, 'acc', 'trashnet'):.2f}"])
table(s, rows, 7.9, 1.8, 5.0, [2.0, 0.9, 1.1, 1.0], 13)

# 7 what helped
s = slide("What helped, and what did not")
bullets(s, [f"Real in-the-wild data is the biggest lever: A {m('A', 'acc'):.2f} -> E {m('E', 'acc'):.2f} accuracy",
            f"Generated organic/other images fixed classes that had no real data: organic recall E {rec('E', 'organic'):.2f} -> G {rec('G', 'organic'):.2f}, 'other' recall E {rec('E', 'other'):.2f} -> G {rec('G', 'other'):.2f}, macro-F1 E {m('E', 'macro_f1'):.2f} -> G {m('G', 'macro_f1'):.2f}",
            f"Pasting TrashNet items on generated backgrounds did not help (A {m('A', 'acc'):.2f}, C {m('C', 'acc'):.2f}): synthetic backgrounds do not carry real mess, glare and occlusion",
            f"Strong classic augmentation alone also did not close the gap (B {m('B', 'acc'):.2f})",
            f"CLIP zero-shot (no training) scores {m('clip', 'acc'):.2f} on real photos, {rec('clip', 'organic'):.2f} recall on organic, but only {m('clip', 'acc', 'trashnet'):.2f} on TrashNet; too big (hundreds of MB) for the free phone deployment",
            "Quantisation: static int8 of the whole network collapsed accuracy (0.65 -> 0.39); int8 on the classifier head only keeps it identical at 13 MB"], size=17)

# 8 errors
s = slide("Error analysis (deployed model)", "Transparent glass vs plastic, crumpled foil and film vs general waste")
pic(s, R / "failures_G.jpg", 0.5, 1.7, h=5.5)
pic(s, R / "confusion_best.png", 6.9, 1.7, w=4.3)
bullets(s, ["Litter photos: glass and paper weakest (clear bottles look like plastic)",
            "Second test, 191 everyday product photos: 1 in 4 cardboard items called paper (a printed pizza box: 'paper 87%'); general waste mostly wrong",
            "Retraining with 97 of those images (arm H) changed little: 0.63 -> 0.68 on the held-out half, within noise"], x=6.9, y=5.4, w=6.0, h=2.0, size=14)

# 9 deployment
s = slide("Deployment and 'not sure'", "Static site on GitHub Pages, model runs on the phone")
pic(s, R / "app_screenshot.jpg", 0.7, 1.7, h=5.4)
bullets(s, ["Model 13 MB, under 0.2 s per photo in the browser; nothing is uploaded",
            "Live: isaacjamesmoses.github.io/sortright",
            "Threshold 0.6 chosen on real-photo validation images (never on the test set)",
            "On the 150 real-world photos: about half are answered, at roughly 80% accuracy; the rest say 'not sure'",
            "Settings page maps materials to local bin names and colours; help page lists limits",
            "Monitoring plan: count 'not sure' rate per site, audit samples weekly, re-check after a camera or location change"], x=4.0, y=1.8, w=9.0, size=17)

# 10 responsible
s = slide("Responsible AI and limits")
bullets(s, ["Privacy: runs fully in the browser, no image leaves the phone, no sign-up, no storage",
            "Indicative only: rules differ by city; answers are labelled 'indicative'; 'not sure' always points to the local guide",
            "Accessibility: large text, colour-blind-safe palette, bin name always written next to the colour",
            "Bias and coverage: results per class reported; glass, clear plastic and mixed items are known weak spots; test set is 150 litter-on-ground photos, not bin-side phone photos; organic images are mostly synthetic",
            "Human in the loop: 'not sure' state and a link to the local guide; weekly audit plan",
            "Licences: TrashNet MIT, TACO CC BY 4.0 (photo licences per Flickr), SD-Turbo non-commercial; coursework use only"], size=18)

# 11 next
s = slide("Next steps")
bullets(s, ["Collect real phone photos at actual bins (the original brief's own-photo test set) and re-measure",
            "Add real organic and 'other' photos to replace synthetic ones",
            "Distil CLIP into the small model to get its organic and 'other' strength",
            "Per-city bin packs; multi-item detection for a tray"], size=24)
prs.save(str(ROOT / "SortRight_Final_Presentation.pptx"))
print("saved deck")
