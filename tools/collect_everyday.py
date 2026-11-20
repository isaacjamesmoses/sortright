"""Collect a SECOND real-world set, 'everyday items': product shots, packaging, items on tables / floors / bins,
from Wikimedia Commons (CC0 / public domain / CC BY / CC BY-SA only). Complements the TACO litter test set, which is
mostly litter outdoors. Titles already used in the first candidate pool are skipped so the two sets never overlap.
Writes data/everyday_candidates/<class>/ and candidates.json."""
import requests, json, time, re, html, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "everyday_candidates"
UA = {"User-Agent": "SortRightStudentProject/1.0 (university coursework; open-licensed images only)"}
API = "https://commons.wikimedia.org/w/api.php"
QUERIES = {
 "plastic": ["plastic water bottle", "shampoo bottle", "plastic milk jug", "yogurt cup", "plastic takeaway container", "detergent bottle", "plastic bag shopping", "plastic cup drink"],
 "paper": ["magazine", "newspaper", "paper bag", "printed paper sheet", "envelope", "notebook paper", "paper cup coffee", "paper receipt", "brochure leaflet"],
 "cardboard": ["pizza box", "shipping cardboard box", "egg carton", "cardboard box printed", "packaging box product", "corrugated cardboard", "cardboard tube", "takeaway cardboard box"],
 "glass": ["glass bottle beer", "glass jar jam", "wine bottle", "glass bottle water", "empty glass jar", "glass bottle sauce", "juice bottle glass"],
 "metal": ["aluminium can soda", "tin can food", "beverage can", "aluminium foil", "spray can aerosol", "canned food", "metal can beer"],
 "organic": ["food waste", "vegetable peelings", "eggshells", "coffee grounds", "fruit scraps", "leftover food plate", "banana peel", "apple core"],
 "general_waste": ["crisp packet", "chocolate wrapper", "tissue paper used", "polystyrene food tray", "plastic wrapper snack", "cigarette butt", "disposable diaper", "chewing gum", "styrofoam cup"],
 "other": ["battery", "electrical cable", "light bulb", "mobile phone", "toothbrush", "shoe", "clothing t-shirt", "headphones", "toy"],
}
OKLIC = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+|CC BY(-SA)?( [0-9.]+)?)", re.I)
lic_ok = lambda s: bool(s) and ("NC" not in s) and ("ND" not in s) and bool(OKLIC.match(s.strip()))
strip = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
old = ROOT / "data" / "web_test_candidates" / "candidates.json"
seen = set(v["title"] for v in json.load(open(old)).values()) if old.exists() else set()
meta = json.load(open(OUT / "candidates.json")) if (OUT / "candidates.json").exists() else {}
seen |= set(v["title"] for v in meta.values())
PER_QUERY = int(sys.argv[1]) if len(sys.argv) > 1 else 9


def dl(job):
    path, url = job
    for _ in range(3):
        try:
            d = requests.get(url, headers=UA, timeout=60)
            if d.status_code == 200:
                path.write_bytes(d.content); return True
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return False


for cls, qs in QUERIES.items():
    (OUT / cls).mkdir(parents=True, exist_ok=True)
    jobs, new = [], {}
    for q in qs:
        off = 0
        nq = sum(1 for v in {**meta, **new}.values() if v["query"] == q)
        if nq >= PER_QUERY: continue
        for page in range(2):
            p = dict(action="query", format="json", generator="search", gsrnamespace=6, gsrsearch=q + " filetype:bitmap", gsrlimit=30, gsroffset=off,
                     prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=640)
            r = None
            for attempt in range(5):
                try:
                    r = requests.get(API, params=p, headers=UA, timeout=30).json(); break
                except Exception as e:
                    time.sleep(4 * (attempt + 1))
            if r is None: print("ERR", q); break
            for pg in (r.get("query", {}).get("pages", {})).values():
                ii = (pg.get("imageinfo") or [{}])[0]; t = pg["title"]
                if sum(1 for v in new.values() if v["query"] == q) + nq >= PER_QUERY: break
                if t in seen or ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 640 or ii.get("height", 0) < 480: continue
                em = ii.get("extmetadata", {}); lic = em.get("LicenseShortName", {}).get("value", "")
                if not lic_ok(lic): continue
                seen.add(t)
                fn = re.sub(r"[^A-Za-z0-9._-]+", "_", t[5:])[-80:]
                path = OUT / cls / fn
                jobs.append((path, ii["thumburl"]))
                new[str(path.relative_to(ROOT)).replace("\\", "/")] = dict(title=t, cls_query=cls, query=q, licence=lic,
                    author=strip(em.get("Artist", {}).get("value", ""))[:120], page=ii.get("descriptionurl"),
                    description=strip(em.get("ImageDescription", {}).get("value", ""))[:200])
            if "continue" in r: off = r["continue"]["gsroffset"]
            else: break
            time.sleep(1.5)
    with ThreadPoolExecutor(8) as ex:
        ok = list(ex.map(dl, jobs))
    for (path, _), good in zip(jobs, ok):
        k = str(path.relative_to(ROOT)).replace("\\", "/")
        if good: meta[k] = new[k]
    json.dump(meta, open(OUT / "candidates.json", "w"), indent=1)
    print(cls, sum(1 for v in meta.values() if v["cls_query"] == cls), flush=True)
