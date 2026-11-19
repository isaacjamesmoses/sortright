"""Collect openly licensed candidate photos from Wikimedia Commons for the SortRight real-world test set.
Writes images to data/web_test_candidates/<class>/ and metadata (title, author, licence, source URL) to candidates.json.
Only CC0 / public domain / CC BY / CC BY-SA files are kept."""
import requests, json, time, re, os, sys, html
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "web_test_candidates"
UA = {"User-Agent": "SortRightStudentProject/1.0 (university coursework; open-licensed images only)"}
API = "https://commons.wikimedia.org/w/api.php"
QUERIES = {
 "plastic": ["plastic bottle", "plastic cup", "plastic food container", "plastic bag", "plastic bottle litter", "plastic bottle table"],
 "paper": ["crumpled paper", "newspaper waste", "paper sheet crumpled", "paper litter", "used paper"],
 "cardboard": ["cardboard box", "pizza box", "cardboard carton", "flattened cardboard", "cardboard packaging"],
 "glass": ["glass bottle", "glass jar", "empty glass bottle", "glass bottle litter", "wine bottle empty"],
 "metal": ["aluminium can", "beverage can", "tin can", "crushed can", "soda can litter"],
 "organic": ["banana peel", "apple core", "orange peel", "food waste scraps", "fruit peel"],
 "general_waste": ["chip packet", "crisp packet litter", "candy wrapper", "used tissue", "snack wrapper litter", "polystyrene food container"],
 "other": ["used battery", "electrical cable", "single sock", "compact fluorescent bulb", "earphones"],
}
OKLIC = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+|CC BY(-SA)?( [0-9.]+)?)", re.I)
def lic_ok(s): return bool(s) and ("NC" not in s) and ("ND" not in s) and bool(OKLIC.match(s.strip()))
def strip(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
meta = json.load(open(OUT/"candidates.json")) if (OUT/"candidates.json").exists() else {}
seen = set(v["title"] for v in meta.values())
for cls, qs in QUERIES.items():
    (OUT/cls).mkdir(parents=True, exist_ok=True)
    for q in qs:
        off = 0
        for page in range(2):
            p = dict(action="query", format="json", generator="search", gsrnamespace=6, gsrsearch=q+" filetype:bitmap", gsrlimit=40, gsroffset=off,
                     prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=800)
            try: r = requests.get(API, params=p, headers=UA, timeout=30).json()
            except Exception as e: print("ERR", q, e); break
            for pg in (r.get("query", {}).get("pages", {})).values():
                ii = (pg.get("imageinfo") or [{}])[0]; t = pg["title"]
                if t in seen or ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 800 or ii.get("height", 0) < 600: continue
                em = ii.get("extmetadata", {}); lic = em.get("LicenseShortName", {}).get("value", "")
                if not lic_ok(lic): continue
                seen.add(t)
                fn = re.sub(r"[^A-Za-z0-9._-]+", "_", t[5:])[-90:]
                path = OUT/cls/fn
                try:
                    d = requests.get(ii["thumburl"], headers=UA, timeout=60)
                    if d.status_code != 200: continue
                    path.write_bytes(d.content)
                except Exception as e: print("dl err", t, e); continue
                meta[str(path.relative_to(ROOT)).replace("\\", "/")] = dict(title=t, cls_query=cls, query=q, licence=lic,
                    author=strip(em.get("Artist", {}).get("value", "")), page=ii.get("descriptionurl"), description=strip(em.get("ImageDescription", {}).get("value", ""))[:200])
                time.sleep(0.3)
            if "continue" in r: off = r["continue"]["gsroffset"]
            else: break
            time.sleep(0.5)
    json.dump(meta, open(OUT/"candidates.json", "w"), indent=1)
    print(cls, sum(1 for v in meta.values() if v["cls_query"] == cls), flush=True)
