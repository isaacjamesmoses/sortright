"""Parallel range download of the SD-Turbo fp16 weights (stabilityai/sd-turbo) into models/sd-turbo (resumable, 16 connections)."""
import os, sys, requests, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parent.parent
DST = ROOT / "models" / "sd-turbo"
REPO = "stabilityai/sd-turbo"
SMALL = ["model_index.json", "scheduler/scheduler_config.json", "tokenizer/merges.txt", "tokenizer/special_tokens_map.json",
         "tokenizer/tokenizer_config.json", "tokenizer/vocab.json", "text_encoder/config.json", "unet/config.json", "vae/config.json"]
BIG = ["unet/diffusion_pytorch_model.fp16.safetensors", "text_encoder/model.fp16.safetensors", "vae/diffusion_pytorch_model.fp16.safetensors"]
for f in SMALL:
    hf_hub_download(REPO, f, local_dir=str(DST))
print("small files ok", flush=True)
CH = 8 * 1024 * 1024
for f in BIG:
    out = DST / f
    out.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/{REPO}/resolve/main/{f}"
    r = requests.head(url, allow_redirects=True, timeout=30)
    size = int(r.headers["Content-Length"])
    final = r.url
    done_f = Path(str(out) + ".done")
    if out.exists() and out.stat().st_size == size and done_f.exists():
        print("have", f, flush=True)
        continue
    with open(out, "wb") as fh:
        fh.truncate(size)
    parts = [(s, min(s + CH, size) - 1) for s in range(0, size, CH)]
    lock = threading.Lock()
    got = [0]

    def grab(p):
        s, e = p
        for attempt in range(6):
            try:
                rr = requests.get(final, headers={"Range": f"bytes={s}-{e}"}, timeout=(15, 60))
                if rr.status_code in (200, 206) and len(rr.content) == e - s + 1:
                    with lock:
                        with open(out, "r+b") as fh:
                            fh.seek(s)
                            fh.write(rr.content)
                        got[0] += len(rr.content)
                    return
            except Exception:
                time.sleep(1)
        raise RuntimeError(f"failed part {s}")

    t0 = time.time()
    with ThreadPoolExecutor(16) as ex:
        futs = [ex.submit(grab, p) for p in parts]
        while not all(x.done() for x in futs):
            time.sleep(10)
            print(f"{f}: {got[0] / 1e6:.0f}/{size / 1e6:.0f} MB, {got[0] / 1e6 / (time.time() - t0):.2f} MB/s", flush=True)
        for x in futs:
            x.result()
    done_f.write_text("ok")
    print("done", f, flush=True)
print("ALL DONE", flush=True)
