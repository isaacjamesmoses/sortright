"""Build the final presentation deck (12 slides) with speaker notes (python-pptx).
Numbers come from results/*.json and results/summary.md (same sources as the report); images from deck_assets/.
usage: python tools/build_deck_pro.py  -> SortRight_Final_Presentation_PRO_v4.pptx"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "deck_assets"
URL = "https://isaacjamesmoses.github.io/sortright/"
HEAD, BODY = "Cambria", "Calibri"


def rgb(h):
    return RGBColor.from_string(h)


INK, MUTE, GREEN, DARK = "10231C", "4F5F58", "0B6E4F", "0B3D2E"
MINT, TINT, WHITE, AMBER = "EAF4EF", "A9CDBD", "FFFFFF", "E69F00"
SOFT = "D5E6DE"
BIN = ["E69F00", "0072B2", "56B4E9", "009E73", "F0E442", "8B5A2B", "7A7A7A", "222222"]
BIN_NAMES = ["Plastic", "Paper", "Cardboard", "Glass", "Metal", "Food", "General", "Ask staff"]

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 13


def text(s, x, y, w, h, paras, size=16, color=INK, bold=False, font=BODY, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=0, line=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if line:
            p.line_spacing = line
        runs = [(para, {})] if isinstance(para, str) else para
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = rgb(o.get("color", color))
            if "link" in o:
                r.hyperlink.address = o["link"]
    return tb


def box(s, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.07, line=None):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fill)
    if line:
        sh.line.color.rgb = rgb(line)
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def badge(s, x, y, d, label, fill=GREEN, color=WHITE, size=18):
    c = box(s, x, y, d, d, fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size, r.font.bold, r.font.name = Pt(size), True, BODY
    r.font.color.rgb = rgb(color)
    return c


def dots(s, x, y, d=0.2, gap=0.09, dark=False):
    for i, c in enumerate(BIN):
        col = "9AA5AD" if (dark and c == "222222") else c
        box(s, x + i * (d + gap), y, d, d, col, shape=MSO_SHAPE.OVAL)


def pic(s, name, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(str(A / name), Inches(x), Inches(y), **kw)


def new_slide(n, title=None, sub=None, dark=False, notes=""):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(DARK if dark else WHITE)
    if title:
        text(s, 0.6, 0.42, 10.0, 0.8, title, size=32, bold=True, font=HEAD, color=WHITE if dark else INK,
             anchor=MSO_ANCHOR.MIDDLE)
    if sub:
        text(s, 0.6, 1.22, 12.1, 0.4, sub, size=16, color=SOFT if dark else MUTE)
    if title:
        dots(s, 10.92, 0.66, dark=dark)
    text(s, 0.6, 7.05, 6, 0.25, "SortRight  ·  MAIB AI 221 Computer Vision with Applications", size=10,
         color=SOFT if dark else MUTE)
    text(s, 11.7, 7.05, 1.03, 0.25, f"{n} / {TOTAL}", size=10, color=SOFT if dark else MUTE, align=PP_ALIGN.RIGHT)
    s.notes_slide.notes_text_frame.text = notes
    return s


def style_chart(ch, legend=False, size=12):
    ch.font.size, ch.font.name = Pt(size), BODY
    ch.font.color.rgb = rgb(INK)
    ch.has_title = False
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(size)
    va, ca = ch.value_axis, ch.category_axis
    va.visible = False
    va.has_major_gridlines = False
    va.minimum_scale = 0
    ca.has_major_gridlines = False
    ca.format.line.color.rgb = rgb("C9D3CE")
    ca.tick_labels.font.size = Pt(size)


def labels(plot, fmt="0.00", size=12):
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format, dl.number_format_is_linked = fmt, False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size, dl.font.bold = Pt(size), True
    dl.font.color.rgb = rgb(INK)


def color_series(ser, hexc):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = rgb(hexc)


def stat(s, x, y, w, h, big, small, fill=MINT, bigc=GREEN, smallc=INK, bigsize=36):
    box(s, x, y, w, h, fill)
    text(s, x + 0.25, y + 0.12, w - 0.5, h * 0.55, big, size=bigsize, bold=True, font=HEAD, color=bigc,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.25, y + h * 0.58, w - 0.5, h * 0.38, small, size=14, color=smallc)


# ---------------------------------------------------------------- 1 title
s = new_slide(1, dark=True, notes=(
    "[~20 s] Hello everyone. I am Isaac James and this is SortRight: a recycling assistant that fits in your pocket. "
    "You point your phone at an item and it tells you the material, which bin it goes in, and a one-line reason. "
    "When it is not sure, it says so instead of guessing. The whole thing runs inside the phone's browser, so no photo "
    "is ever uploaded. The app is live right now at isaacjamesmoses.github.io/sortright, and in the next ten minutes "
    "I will show you how I built it, how I measured it, and what I learned."))
dots(s, 0.8, 0.9, d=0.24, gap=0.1, dark=True)
text(s, 0.8, 1.45, 7.0, 1.3, "SortRight", size=72, bold=True, font=HEAD, color=WHITE)
text(s, 0.8, 2.75, 7.0, 0.6, "Point. Snap. Sort.", size=30, bold=True, color=AMBER)
text(s, 0.8, 3.55, 6.6, 1.3, "A phone web app that names the material, the bin and an honest “not sure”, "
     "running entirely on the device.", size=20, color=SOFT, line=1.1)
text(s, 0.8, 5.0, 6.8, 1.2, [[("Isaac James", {"bold": True, "size": 20, "color": WHITE})],
                              "MAIB AI 221 Computer Vision with Applications  ·  Final Project 8, Environment",
                              "Unit coordinator: Dr. Khalid Ezzeldeen  ·  S P Jain"], size=14, color=SOFT, space_after=3)
b = box(s, 0.8, 6.3, 5.4, 0.55, "145A45", radius=0.5)
text(s, 0.8, 6.3, 5.4, 0.55, [[("Live:  ", {"color": SOFT}), ("isaacjamesmoses.github.io/sortright",
                                                              {"bold": True, "color": WHITE})]],
     size=16, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
pic(s, "phone_cardboard.png", 7.95, 0.95, h=6.1)
pic(s, "phone_unsure.png", 10.55, 0.45, h=6.1)

# ---------------------------------------------------------------- 2 problem
s = new_slide(2, "A wrong bin costs more than a missing answer", notes=(
    "[~45 s] Start with the real problem. Contaminated recycling bins, the wrong item in the wrong bin, raise processing "
    "costs and send good material to landfill. Most people at a campus or office recycling point are not careless, they "
    "are unsure. So the user here is a member of the public with a phone in one hand and an item in the other. The "
    "decision is simple: which bin? And the cost of an error is not symmetric. A confident wrong answer contaminates a "
    "bin; an honest 'not sure' just sends the person to the local guide. That asymmetry shaped the whole design: the "
    "app answers when it is confident and says 'not sure' when it is not."))
rows = [("1", "The user", "A member of the public at a campus or office recycling point, phone in hand, unsure which bin an item belongs in."),
        ("2", "The decision", "Which bin does this go in, or should I check the local guide first?"),
        ("3", "The cost of an error", "Wrong-bin items contaminate a load, raise processing costs and send good material to landfill.")]
for i, (n, h, d) in enumerate(rows):
    y = 1.85 + i * 1.7
    badge(s, 0.6, y + 0.08, 0.7, n, size=22)
    text(s, 1.6, y, 5.4, 0.4, h, size=21, bold=True, font=HEAD)
    text(s, 1.6, y + 0.45, 5.5, 1.0, d, size=16, color=MUTE, line=1.05)
box(s, 7.7, 1.85, 5.03, 4.85, DARK, radius=0.05)
text(s, 8.15, 2.25, 4.2, 0.3, "DESIGN PRINCIPLE", size=13, bold=True, color=AMBER)
text(s, 8.15, 2.75, 4.2, 2.3, "A confident wrong answer costs more than an honest “not sure”.", size=30, bold=True,
     font=HEAD, color=WHITE, line=1.05)
text(s, 8.15, 5.05, 4.2, 0.9, "So SortRight answers only when it is confident, and says so when it is not.", size=16,
     color=SOFT)
box(s, 8.15, 6.0, 1.9, 0.45, "145A45", radius=0.5)
text(s, 8.15, 6.0, 1.9, 0.45, "Sure → bin", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
box(s, 10.2, 6.0, 2.2, 0.45, AMBER, radius=0.5)
text(s, 10.2, 6.0, 2.2, 0.45, "Unsure → ask", size=14, bold=True, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 3 solution
s = new_slide(3, "From photo to bin in a blink, on the phone", "Everything below runs inside the browser: no server, no upload.", notes=(
    "[~50 s] Here is the whole system on one slide. The photo is resized, centre-cropped to 224 pixels and normalised in "
    "the browser. A MobileNetV3-Large classifier, fine-tuned by me and exported to ONNX, produces eight probabilities: "
    "plastic, paper, cardboard, glass, metal, organic, general waste and other. A simple, transparent rule decides what "
    "to show: if the top confidence is at least 0.6 and the class is not 'other', the app shows the material, the bin and "
    "a reason; otherwise it says it is not sure. The model is 13 megabytes, answers in about forty milliseconds on a "
    "laptop in the browser, and sends nothing anywhere. Hosting is a static GitHub Pages site, so it costs nothing and "
    "has no server to fail."))
steps = [("1", "Photo", "Camera or gallery. The image stays on the phone."),
         ("2", "Prepare", "Resize to 256, centre-crop 224, normalise."),
         ("3", "Classify", "MobileNetV3-Large in ONNX Runtime Web gives 8 probabilities."),
         ("4", "Decide", "Top confidence ≥ 0.6 and not “other”? Answer. Otherwise: not sure."),
         ("5", "Show", "Material, bin colour, one-line reason and the top 3.")]
for i, (n, h, d) in enumerate(steps):
    x = 0.6 + i * 2.47
    box(s, x, 1.95, 2.2, 2.55, MINT)
    badge(s, x + 0.2, 2.15, 0.5, n, size=16)
    text(s, x + 0.2, 2.8, 1.85, 0.4, h, size=19, bold=True, font=HEAD)
    text(s, x + 0.2, 3.25, 1.85, 1.2, d, size=14, color=MUTE, line=1.0)
    if i < 4:
        c = box(s, x + 2.24, 3.05, 0.2, 0.36, GREEN, shape=MSO_SHAPE.CHEVRON)
stat(s, 0.6, 4.85, 3.85, 1.55, "13.1 MB", "model file, int8 classifier head, ONNX")
stat(s, 4.74, 4.85, 3.85, 1.55, "≈ 40 ms", "per photo on a laptop (WASM, one thread)")
stat(s, 8.88, 4.85, 3.85, 1.55, "0 bytes", "uploaded. No server, no sign-up, free hosting")
text(s, 0.6, 6.6, 12.1, 0.3, "8 classes:  plastic  ·  paper  ·  cardboard  ·  glass  ·  metal  ·  organic  ·  general waste  ·  other",
     size=14, color=MUTE)

# ---------------------------------------------------------------- 4 demo
s = new_slide(4, "Using SortRight: four taps", "Open the link on any phone. No install, no account.", notes=(
    "[~90 s, DEMO] Now the working app. [Open the link on the phone.] Step one: tap Take a photo, which opens the phone's "
    "own camera, or Choose a photo from the gallery. Step two: read the result: the material, the bin with its colour, "
    "a one-line reason, the top three possibilities and the time it took. Here, a flattened box: cardboard, ninety-nine "
    "percent, cardboard bin. [LIVE: scan a plain box or a can.] Step three: when the photo is unclear it does not guess. "
    "It shows an amber 'I am not sure' message and sends you to the local guide. [LIVE: show a not-sure case.] Step four: "
    "recycling rules differ between cities, so on the Bins tab anyone can rename the bins and change the colours, and "
    "the choice is saved on the phone. [LIVE: change one colour, scan again.] If the network is slow, the screenshots on "
    "this slide are from the same deployed model."))
caps = [("phone_home.png", "1  Open and snap", "Tap Take a photo (native camera) or Choose a photo."),
        ("phone_cardboard.png", "2  Read the answer", "Material, bin colour, reason, top 3 and time taken."),
        ("phone_unsure.png", "3  Honest “not sure”", "Unclear photo? It says so and points to the local guide."),
        ("phone_bins.png", "4  Make it local", "Bins tab: rename and recolour the bins for your city.")]
for i, (img, h, d) in enumerate(caps):
    x = 0.6 + i * 3.1
    pic(s, img, x + (2.9 - 4.1 * 912 / 2172) / 2, 1.6, h=4.1)
    text(s, x, 5.85, 2.9, 0.35, h, size=17, bold=True, font=HEAD, align=PP_ALIGN.CENTER)
    text(s, x, 6.22, 2.9, 0.7, d, size=14, color=MUTE, line=1.0, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- 5 data
s = new_slide(5, "Data: studio, real-world and generated images", "Three training sources, two independent test sets, licences recorded.", notes=(
    "[~50 s] Data. The brief names two datasets and I used both, plus a generative one. TrashNet gives about two thousand "
    "clean studio photos, MIT licensed. TACO gives real litter photographed outdoors, CC BY 4.0, and I used 527 crops for "
    "training. For the two classes with no real data, food waste and 'other', I generated about 1,300 training images with "
    "SD-Turbo. Evaluation is where I was most careful. The main test is 150 real-world photos: 139 TACO crops from images "
    "that never contributed to training, and 11 Wikimedia Commons photos. Then a second independent test: 191 "
    "everyday-item photos I collected from Wikimedia Commons and checked by eye, each with its licence recorded. Generated "
    "images are only ever used for training. No test image is used for tuning; the confidence threshold was chosen on "
    "validation crops."))
text(s, 0.6, 1.85, 6.3, 0.35, "Training images: 3,847", size=17, bold=True, font=HEAD)
cd = CategoryChartData()
cd.categories = ["TrashNet (studio)", "TACO (real-world crops)", "Generated (organic, other)"]
cd.add_series("Images", [2024, 527, 1296])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(2.25), Inches(6.3), Inches(3.0), cd)
ch = gf.chart
style_chart(ch)
ch.category_axis.reverse_order = True
labels(ch.plots[0], "#,##0")
ch.plots[0].gap_width = 55
ch.plots[0].vary_by_categories = False
ser = ch.plots[0].series[0]
for i, c in enumerate([TINT, GREEN, AMBER]):
    ser.points[i].format.fill.solid()
    ser.points[i].format.fill.fore_color.rgb = rgb(c)
for i, (t, w) in enumerate([("TrashNet · MIT", 1.75), ("TACO · CC BY 4.0", 2.0), ("SD-Turbo · training only", 2.45)]):
    x = 0.6 + [0, 1.9, 4.05][i]
    box(s, x, 5.6, w, 0.5, MINT, radius=0.5)
    text(s, x, 5.6, w, 0.5, t, size=13, bold=True, color=GREEN, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.6, 6.3, 6.3, 0.6, "Class mapping: TrashNet “trash” and TACO wrappers, film, foam and cigarettes map to general waste.",
     size=13, color=MUTE)
cards = [("Test A · 150 real-world photos", "139 TACO crops from images never used in training, plus 11 Wikimedia Commons photos. The main benchmark.", 1.85, 1.75),
         ("Test B · 191 everyday items", "Wikimedia Commons photos (CC0, public domain, CC BY, CC BY-SA), checked by eye, licence recorded per image.", 3.8, 1.75),
         ("Plus TrashNet test · 251 studio photos", "No test image is used for training or tuning.", 5.75, 1.0)]
for t, d, y, h in cards:
    box(s, 7.3, y, 5.43, h, MINT)
    text(s, 7.55, y + 0.15, 4.95, 0.4, t, size=18, bold=True, font=HEAD)
    text(s, 7.55, y + 0.6, 4.95, h - 0.7, d, size=14, color=MUTE, line=1.0)

# ---------------------------------------------------------------- 6 method
s = new_slide(6, "A controlled ladder of experiments", notes=(
    "[~55 s] Method, in plain words. I built the classifier step by step and, at each step, added one ingredient to the "
    "training data, then measured it on the same 150 real photos. First two reference points: a frozen pre-trained model "
    "with a simple classifier on top, the Week 7 baseline, scores 0.50, and CLIP with no training at all, from Lecture F, "
    "scores 0.58. Now my own training. If I train only on clean studio photos, accuracy on real photos is just 0.42: "
    "studio photos do not transfer by themselves. Adding real litter photos from TACO lifts it to 0.63. Adding generated "
    "images for the two classes with no real data, food waste and other, gives my final model: 0.66 accuracy, 24 points "
    "above the studio-only start, in a 13 megabyte model. CLIP is a useful yardstick, but it is many times larger, so my "
    "final model is the one I deployed. I also tried other mixes, such as extra augmentation and composites; they are in "
    "the report."))
text(s, 0.6, 1.4, 8.4, 0.35, "Accuracy on 150 real-world photos: each bar adds one ingredient", size=17, bold=True, font=HEAD)
cd = CategoryChartData()
cd.categories = ["Reference: frozen model + simple classifier", "Reference: CLIP, no training",
                 "Train on studio photos only", "+ real litter photos (TACO)", "+ generated food and other images (final)"]
vals = [0.50, 0.58, 0.42, 0.63, 0.66]
cd.add_series("Accuracy", vals)
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.8), Inches(8.5), Inches(4.95), cd)
ch = gf.chart
style_chart(ch, size=12)
ch.value_axis.maximum_scale = 0.8
labels(ch.plots[0], "0.00", 12)
ch.plots[0].gap_width = 45
ch.plots[0].vary_by_categories = False
ser = ch.plots[0].series[0]
cols = ["B8C3BD", "B8C3BD", TINT, "6FAE95", GREEN]
for i, c in enumerate(cols):
    ser.points[i].format.fill.solid()
    ser.points[i].format.fill.fore_color.rgb = rgb(c)
box(s, 9.4, 1.8, 3.33, 3.0, MINT)
text(s, 9.65, 1.95, 2.9, 0.35, "A fair comparison", size=17, bold=True, font=HEAD)
text(s, 9.65, 2.4, 2.9, 2.4, ["Same neural network (MobileNetV3)", "Same training recipe every time",
                              "Same 150 real-world test photos", "Run twice and averaged"],
     size=14, color=INK, space_after=6)
box(s, 9.4, 5.0, 3.33, 1.75, DARK)
text(s, 9.65, 5.1, 2.9, 0.9, "+24 pts", size=44, bold=True, font=HEAD, color=AMBER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 9.65, 6.0, 2.9, 0.7, "final model vs studio photos only (0.42 to 0.66)", size=14, color=WHITE)

# ---------------------------------------------------------------- 7 generative AI
s = new_slide(7, "Generative AI where real data did not exist", notes=(
    "[~60 s] This is the generative component, with an experiment that shows its effect. TACO has almost no food waste "
    "and very few 'other' items such as cables or batteries. So I generated them: about 1,300 images from SD-Turbo, "
    "with varied backgrounds and prompts, shown here. The effect is clear: recall for organic goes from zero to 0.77 and "
    "macro-F1 rises from 0.55 to 0.63, while the other classes stay close. I also tested the second idea from the brief: "
    "pasting cut-out items onto generated backgrounds. That composite experiment did not close the gap, accuracy went "
    "from 0.40 to 0.38, so I dropped it. I report it because it is a real result: generated classes help, generated "
    "backgrounds do not, and the design followed the measurement."))
pic(s, "generated_tile.png", 0.6, 1.5, w=6.2)
text(s, 0.6, 4.7, 6.2, 0.7, "SD-Turbo images: organic (top row) and other, such as cables, electronics and textiles (bottom row). Training only.",
     size=13, color=MUTE)
box(s, 0.6, 5.5, 6.2, 1.35, MINT)
text(s, 0.85, 5.62, 5.7, 1.2, [[("Also tested: ", {"bold": True, "color": GREEN}),
                                ("composites (cut-out items on generated backgrounds), 0.40 to 0.38. Generated classes helped, generated backgrounds did not, so only the classes shipped.", {})]],
     size=14, line=1.0)
stat(s, 7.2, 1.5, 2.65, 1.55, "0 → 0.77", "organic recall", bigsize=27)
stat(s, 10.08, 1.5, 2.65, 1.55, "0.55 → 0.63", "all-class average score (+8 pts)", bigsize=27)
text(s, 7.2, 3.3, 5.5, 0.35, "Without vs with generated images", size=16, bold=True, font=HEAD)
cd = CategoryChartData()
cd.categories = ["Organic recall", "All-class average (macro-F1)"]
cd.add_series("Without generated images", [0.00, 0.55])
cd.add_series("With generated images (final model)", [0.77, 0.63])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7.2), Inches(3.65), Inches(5.53), Inches(3.25), cd)
ch = gf.chart
style_chart(ch, legend=True)
ch.value_axis.maximum_scale = 1.0
labels(ch.plots[0], "0.00")
ch.plots[0].gap_width = 70
ch.plots[0].overlap = -5
color_series(ch.plots[0].series[0], TINT)
color_series(ch.plots[0].series[1], GREEN)

# ---------------------------------------------------------------- 8 results
s = new_slide(8, "Results: 0.66 on real photos, 0.92 on TrashNet", notes=(
    "[~65 s] Results. On the 150 real-world photos the deployed model scores 0.66 accuracy and 0.63 macro-F1, with a 95 "
    "percent interval of 0.58 to 0.73; on the TrashNet studio test it scores 0.92. Per class, metal and cardboard are both "
    "0.88, food waste 0.77, plastic 0.71. Paper and glass are the hardest and I show them here honestly. The right chart is "
    "the part I like most. Because the app can say 'not sure', I can trade coverage for accuracy. At the threshold of 0.6 "
    "it answers about half the photos and is right about 82 percent of the time on those; at 0.8 it is 85 percent. So the "
    "user either gets a reliable answer or a clear instruction to check the local guide."))
for i, (b, t) in enumerate([("0.66", "accuracy, 150 real photos (95% CI 0.58–0.73)"), ("0.63", "average score across all 8 classes (macro-F1)"),
                            ("0.92", "accuracy on the TrashNet studio test"), ("82%", "accuracy when it answers (53% answered)")]):
    stat(s, 0.6 + i * 3.06, 1.4, 2.85, 1.4, b, t, bigsize=34)
text(s, 0.6, 3.05, 5.9, 0.35, "Recall per material (mean of 2 seeds)", size=16, bold=True, font=HEAD)
cd = CategoryChartData()
order = [("Metal", .88), ("Cardboard", .88), ("Organic", .77), ("Plastic", .71), ("General waste", .55), ("Other", .50),
         ("Glass", .39), ("Paper", .33)]
cd.categories = [o[0] for o in order]
cd.add_series("Recall", [o[1] for o in order])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(3.4), Inches(5.9), Inches(3.55), cd)
ch = gf.chart
style_chart(ch)
ch.category_axis.reverse_order = True
ch.value_axis.maximum_scale = 1.1
labels(ch.plots[0], "0.00")
ch.plots[0].gap_width = 35
color_series(ch.plots[0].series[0], GREEN)
text(s, 6.9, 3.05, 5.8, 0.35, "The “not sure” trade-off (deployed model)", size=16, bold=True, font=HEAD)
cd = CategoryChartData()
cd.categories = ["no rule", "≥ 0.4", "≥ 0.5", "≥ 0.6", "≥ 0.7", "≥ 0.8"]
cd.add_series("Share answered", [1.00, .87, .65, .53, .41, .27])
cd.add_series("Accuracy on answered", [.64, .708, .786, .823, .823, .85])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(6.9), Inches(3.4), Inches(5.83), Inches(3.55), cd)
ch = gf.chart
style_chart(ch, legend=True, size=11)
ch.value_axis.maximum_scale = 1.15
labels(ch.plots[0], "0%", 11)
ch.plots[0].gap_width = 60
ch.plots[0].overlap = -5
color_series(ch.plots[0].series[0], TINT)
color_series(ch.plots[0].series[1], GREEN)

# ---------------------------------------------------------------- 9 model comparison
s = new_slide(9, "Two models in one app", "A specialist and a foundation model, same photos, same test. Pick one on the Scan tab.", notes="")
text(s, 0.6, 1.75, 7.3, 0.35, "Accuracy on two held-out test sets", size=17, bold=True, font=HEAD)
cd = CategoryChartData()
cd.categories = ["SortRight (ours, trained)", "MobileCLIP-S0 (zero-shot)", "CLIP ViT-B/32 (reference)"]
cd.add_series("150 real-world photos", [0.66, 0.70, 0.58])
cd.add_series("191 everyday photos", [0.64, 0.76, 0.74])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(2.15), Inches(7.3), Inches(4.7), cd)
ch = gf.chart
style_chart(ch, legend=True, size=12)
ch.value_axis.maximum_scale = 1.0
labels(ch.plots[0], "0.00")
ch.plots[0].gap_width = 60
ch.plots[0].overlap = -5
color_series(ch.plots[0].series[0], TINT)
color_series(ch.plots[0].series[1], GREEN)
cards = [("SortRight", "13 MB · about 40 ms", "Fine-tuned for this task on 3,847 images. Small, fast, and the default.", MINT, GREEN, INK),
         ("MobileCLIP-S0", "38 MB · about 280 ms", "Apple’s small vision-language model: 11.4M-parameter image encoder, 67.8% zero-shot on ImageNet. No recycling training.", DARK, AMBER, WHITE)]
for i, (h, big, d, fill, bc, tc) in enumerate(cards):
    y = 1.75 + i * 2.6
    box(s, 8.25, y, 4.48, 2.4, fill)
    text(s, 8.5, y + 0.15, 4.0, 0.35, h, size=17, bold=True, font=HEAD, color=bc)
    text(s, 8.5, y + 0.55, 4.0, 0.6, big, size=24, bold=True, font=HEAD, color=tc)
    text(s, 8.5, y + 1.25, 4.0, 1.1, d, size=14, color=tc, line=1.0)
text(s, 8.25, 6.95 - 0.05, 4.48, 0.1, "", size=10)

# ---------------------------------------------------------------- 9 error analysis
s = new_slide(10, "Error analysis: where and why it hesitates", "The mistakes are physical, which tells us exactly what data to add.", notes=(
    "[~50 s] Error analysis. The confusion matrix on the left shows the mistakes. The main ones are physical: clear or "
    "brown glass bottles lying in grass look like plastic; crumpled foil and film look like each other; and printed or "
    "coloured cardboard, like a cereal box, resembles paper. The examples on the right are the most confident mistakes. "
    "They are mostly transparent, reflective or crumpled items, which is exactly where the model has seen the least "
    "training data. This analysis tells me where the data is thin, and the next slide shows what I tried about it."))
pic(s, "confusion_G.png", 0.6, 1.75, h=4.75)
text(s, 0.6, 6.55, 5.3, 0.4, "Rows: true material. Counts summed over 2 seeds, 150 real photos.", size=12, color=MUTE)
pic(s, "failures_tiles.png", 6.35, 1.75, w=6.38)
text(s, 6.35, 3.5, 6.38, 0.4, "The most confident mistakes: true class, then what the model said.", size=12, color=MUTE)
for i, (h, d) in enumerate([("Glass ↔ plastic", "Clear and brown bottles in grass or sand."),
                            ("Foil and film", "Crumpled, reflective, shapeless items."),
                            ("Printed cardboard", "Colourful boxes can resemble paper.")]):
    x = 6.35 + i * 2.17
    box(s, x, 4.1, 2.04, 2.75, MINT)
    text(s, x + 0.18, 4.28, 1.7, 0.8, h, size=17, bold=True, font=HEAD, line=0.95)
    text(s, x + 0.18, 5.15, 1.72, 1.6, d, size=14, color=MUTE, line=1.05)

# ---------------------------------------------------------------- 10 stress tests
s = new_slide(11, "We stress-tested the obvious fixes", "Each change was measured on held-out photos before deciding what to ship.", notes=(
    "[~45 s] I did not stop at the first model. First, an independent test: 191 everyday photos from Wikimedia Commons "
    "that the model had never seen scored 0.64 against 0.66, so the result holds across two unseen sets. Second, I tried "
    "averaging two trained models: no meaningful gain for a download twice the size, so I did not ship it. Third, "
    "background removal with a segmentation network before classification: it made things worse, 0.57, so I did not ship "
    "that either. Fourth, adding 97 everyday photos to training gave about five points on the held-out half, but with "
    "only 94 test images that is within noise. The conclusion is consistent: the limit is data coverage, not model size or "
    "tricks. So the roadmap is data: hundreds of phone photos at real bins, especially printed packaging and general waste."))
cards = [("0.64 vs 0.66", "Independent test, 191 unseen photos", "Consistent across two sets the model never saw."),
         ("0.67 vs 0.66", "Averaging two trained models", "No meaningful gain for a download twice the size, so not shipped."),
         ("0.57 vs 0.66", "Background removal first (U²-Net)", "Cut-outs hurt cardboard and general waste, so not shipped."),
         ("+0.05", "Retrain with 97 extra everyday photos", "Small and within noise on 94 test images: more data is the lever.")]
for i, (big, h, d) in enumerate(cards):
    x, y = 0.6 + (i % 2) * 6.18, 1.75 + (i // 2) * 2.1
    box(s, x, y, 5.95, 1.95, MINT)
    text(s, x + 0.3, y + 0.2, 2.6, 1.0, big, size=32, bold=True, font=HEAD, color=GREEN, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.3, y + 1.2, 5.3, 0.4, h, size=17, bold=True, font=HEAD)
    text(s, x + 0.3, y + 1.55, 5.4, 0.35, d, size=14, color=MUTE)
box(s, 0.6, 6.05, 12.13, 0.85, DARK)
text(s, 0.9, 6.05, 11.6, 0.85, [[("Next:  ", {"bold": True, "color": AMBER}),
                                  ("hundreds of phone photos at real bins (printed packaging, general waste)  ·  a CLIP-assisted fallback  ·  local rules per city", {"color": WHITE})]],
     size=15, anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 11 deployment + responsible AI
s = new_slide(12, "Built to ship, built to be trusted", notes=(
    "[~50 s] Deployment and responsible AI. The brief asks for a working public URL and a phone-friendly app: this is a "
    "static site on GitHub Pages using ONNX Runtime Web. One lesson from Lecture D: static int8 quantisation of the whole "
    "network collapsed accuracy from 0.65 to 0.39, so I quantised only the classifier head and got 13.1 megabytes with "
    "identical accuracy. On iPhone, Take a photo opens the native camera. For responsible AI: nothing leaves the device, "
    "there is no sign-up, every answer is labelled indicative, 'not sure' keeps a human in the loop, bin names and colours "
    "are editable because rules differ by city, the palette is colour-blind-safe with a text label on every bin, and the "
    "repository includes a model card and licence notices."))
box(s, 0.6, 1.5, 5.95, 5.35, MINT)
text(s, 0.9, 1.7, 5.4, 0.4, "Built to ship", size=22, bold=True, font=HEAD, color=GREEN)
ship = [("Static and free. ", "GitHub Pages and ONNX Runtime Web: always on, no server."),
        ("Quantised with care. ", "Head-only int8 keeps accuracy identical at 13.1 MB; whole-network int8 fell from 0.65 to 0.39."),
        ("Fast. ", "About 40 ms per photo; iPhone Take a photo opens the native camera."),
        ("Reproducible. ", "Public repo with code, README, model card and licence notices.")]
text(s, 0.9, 2.3, 5.4, 4.4, [[(a, {"bold": True}), (b, {})] for a, b in ship], size=18, space_after=16, line=1.02)
box(s, 6.78, 1.5, 5.95, 5.35, MINT)
text(s, 7.08, 1.7, 5.4, 0.4, "Built to be trusted", size=22, bold=True, font=HEAD, color=GREEN)
trust = [("Private. ", "On-device inference; no upload, no sign-up."),
         ("Human in the loop. ", "“Not sure” state; every answer labelled indicative."),
         ("Local rules. ", "Bin names and colours are editable per city."),
         ("Accessible. ", "Colour-blind-safe palette with a text label on every bin.")]
text(s, 7.08, 2.3, 5.4, 2.9, [[(a, {"bold": True}), (b, {})] for a, b in trust], size=18, space_after=14, line=1.02)
for i, c in enumerate(BIN):
    x = 7.08 + i * 0.64
    box(s, x, 5.55, 0.46, 0.46, c, shape=MSO_SHAPE.OVAL, line="9AA5AD" if c in ("F0E442",) else None)
    text(s, x - 0.08, 6.08, 0.62, 0.3, BIN_NAMES[i], size=10, color=MUTE, align=PP_ALIGN.CENTER)
text(s, 7.08, 6.45, 5.4, 0.3, "The default bin palette, shown as in the app", size=11, color=MUTE)

# ---------------------------------------------------------------- 12 closing
s = new_slide(13, dark=True, notes=(
    "[~30 s] To close: what was asked and what was delivered. A transfer-learning classifier exported to ONNX under 15 "
    "megabytes; CLIP zero-shot as a comparison; a generative AI experiment with a measured effect; a complete evaluation, "
    "real photos versus TrashNet, fine-tuned versus zero-shot, with and without composites, the not-sure trade-off and the "
    "confusion analysis; a live static phone app with editable bins; and a model card and repository. SortRight gives the "
    "right bin, or an honest 'not sure'. The link and QR code are on screen: please try it on your own phone. Thank you, "
    "I am happy to take questions.\n\n"
    "---- Q&A PREP (not for the audience) ----\n"
    "Why only 0.66 on real photos? The test photos are hard litter-on-the-ground images; TrashNet-only training scores 0.42. "
    "The app answers on about half and is about 82% right on those.\n"
    "Is the test set leak-proof? Test crops come from TACO images whose id is divisible by 4; all training and validation "
    "crops come from the others. Threshold chosen on validation crops, never on the test set.\n"
    "Why not deploy CLIP? 0.58 on real photos, but many times larger than this 13 MB model and slower on a free host.\n"
    "Why did composites not help? Pasted items on generated backgrounds look clean and floating; real photos have glare, "
    "dirt, occlusion and clutter.\n"
    "Own photos? The brief asked for 150 own campus photos; I used internet images of real-world quality, as agreed with "
    "the unit coordinator (have his confirmation ready), and I can add my own photos as a further test.\n"
    "Privacy / bias? Fully on-device; no people in the data; coverage limited to TACO and TrashNet packaging and countries; "
    "per-class results reported; paper and glass are weakest."))
dots(s, 0.8, 0.9, d=0.24, gap=0.1, dark=True)
text(s, 0.8, 1.3, 7.5, 0.9, "What we delivered", size=40, bold=True, font=HEAD, color=WHITE)
items = ["Transfer-learning classifier exported to ONNX, 13 MB",
         "CLIP zero-shot comparison (0.58 on real photos)",
         "Generative-AI experiment with a measured effect",
         "Held-out evaluation: real vs studio, tuned vs zero-shot, with vs without composites, “not sure” trade-off, confusion matrix",
         "Live static phone app: editable bins, “not sure” state, help page",
         "Model card, README, licence notices, public repository",
         "A second independent test plus three more stress tests"]
ys = [2.35, 2.95, 3.55, 4.15, 5.0, 5.6, 6.2]
for t, y in zip(items, ys):
    badge(s, 0.8, y, 0.38, "✓", fill=AMBER, color=INK, size=14)
    text(s, 1.4, y - 0.02, 6.7, 0.8, t, size=16, color=WHITE, anchor=MSO_ANCHOR.TOP, line=1.0)
box(s, 8.8, 1.7, 3.9, 5.0, WHITE, radius=0.05)
pic(s, "qr.png", 9.3, 2.0, w=2.9)
text(s, 8.95, 5.0, 3.6, 0.4, "Try it on your phone", size=20, bold=True, font=HEAD, color=INK, align=PP_ALIGN.CENTER)
text(s, 8.95, 5.5, 3.6, 0.4, [[("isaacjamesmoses.github.io/sortright", {"link": URL, "color": GREEN, "bold": True})]],
     size=14, align=PP_ALIGN.CENTER)
text(s, 8.95, 6.0, 3.6, 0.5, "The right bin, or an honest “not sure”.", size=14, color=MUTE, align=PP_ALIGN.CENTER)


# ---- simple speaker script (overrides the longer notes above) ----
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from speaker_notes_simple import NOTES
for i, sl in enumerate(prs.slides, 1):
    sl.notes_slide.notes_text_frame.text = NOTES[i]
NL = chr(10)
parts = ["# SortRight: simple speaking script"] + [f"## Slide {i}{NL}{NOTES[i]}" for i in range(1, 14)]
open(ROOT / "SPEAKING_SCRIPT_SIMPLE.md", "w", encoding="utf-8").write((NL + NL).join(parts) + NL)

out = ROOT / "SortRight_Final_Presentation_PRO_v4.pptx"
prs.save(out)
print("saved", out)



