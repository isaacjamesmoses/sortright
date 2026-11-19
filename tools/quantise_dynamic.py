"""Fallback after static int8 collapsed accuracy: dynamic int8 of the Gemm (classifier) weights only; conv/SE blocks stay float."""
import sys, csv, json, time, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
ROOT = Path(__file__).resolve().parent.parent; OUT = ROOT/"web/model"
src, dst = OUT/"sortright_fp32.onnx", OUT/"sortright_dyn.onnx"
quantize_dynamic(str(src), str(dst), weight_type=QuantType.QInt8, op_types_to_quantize=["Gemm", "MatMul"])
from PIL import Image
CLS = ["plastic","paper","cardboard","glass","metal","organic","general_waste","other"]
MEAN=np.array([0.485,0.456,0.406],np.float32); STD=np.array([0.229,0.224,0.225],np.float32)
def prep(p):
    im=Image.open(p).convert("RGB"); w,h=im.size
    nw,nh=(256,int(256*h/w)) if w<=h else (int(256*w/h),256)
    im=im.resize((nw,nh),Image.BILINEAR); l,t=int(round((nw-224)/2.0)),int(round((nh-224)/2.0))
    return ((np.asarray(im.crop((l,t,l+224,t+224)),np.float32)/255-MEAN)/STD).transpose(2,0,1)[None].astype(np.float32)
rows=list(csv.DictReader(open(ROOT/"data/realworld_test_set/labels.csv",encoding="utf-8")))
X=np.concatenate([prep(ROOT/"data/realworld_test_set"/r["file"]) for r in rows]); y=np.array([CLS.index(r["label"]) for r in rows])
out={}
for n,p in (("fp32",src),("dynamic_int8_head",dst)):
    s=ort.InferenceSession(str(p),providers=["CPUExecutionProvider"]); t=time.time()
    P=np.concatenate([s.run(None,{"image":X[i:i+1]})[0] for i in range(len(X))]); out[n]=dict(acc=float((P.argmax(1)==y).mean()),size_mb=p.stat().st_size/1e6,ms=(time.time()-t)/len(X)*1000,pred=P.argmax(1))
    print(n,"acc %.3f size %.1f MB %.1f ms"%(out[n]["acc"],out[n]["size_mb"],out[n]["ms"]))
print("agreement",float((out["fp32"]["pred"]==out["dynamic_int8_head"]["pred"]).mean()))
