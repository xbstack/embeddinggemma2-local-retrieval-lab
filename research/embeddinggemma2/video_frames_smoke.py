"""Test video -> sampled frame -> EmbeddingGemma 2 vision retrieval.

This is *not* a native temporal/video encoder benchmark.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import time
from pathlib import Path
from huggingface_hub import hf_hub_download
from litert_lm import Backend, Content, EmbeddingEngine
from litert_benchmark import normalize, cosine

HERE=Path(__file__).resolve().parent
ROOT=HERE/"fixtures"/"multimodal-synthetic"
VIDEO=ROOT/"two-frames.mp4"
EXTRACT=HERE/"results"/"video-frames"
EXTRACT.mkdir(parents=True,exist_ok=True)
for idx,key in enumerate(("red-square","blue-circle")):
    shutil.copyfile(ROOT/f"{key}.png", EXTRACT/f"frame_{idx:02d}.png")
subprocess.run(["ffmpeg","-y","-v","error","-framerate","1","-i",
                str(EXTRACT/"frame_%02d.png"),"-c:v","libx264","-pix_fmt",
                "yuv420p","-t","2",str(VIDEO)],check=True,timeout=20)
for f in EXTRACT.glob("frame_*.png"):f.unlink()
subprocess.run(["ffmpeg","-y","-v","error","-i",str(VIDEO),"-vf","fps=1",
                str(EXTRACT/"frame_%02d.png")],check=True,timeout=20)
frames=sorted(EXTRACT.glob("frame_*.png"))
if len(frames)!=2:raise RuntimeError(f"Expected 2 extracted frames, got {len(frames)}")
model=hf_hub_download(repo_id="litert-community/embeddinggemma-2-740m-litert-lm",
                      filename="embeddinggemma-2-740m.litertlm",local_files_only=True)
metrics=[]
with EmbeddingEngine(str(model),backend=Backend.CPU(thread_count=4),
                     vision_backend=Backend.CPU(thread_count=4)) as eng:
    red=normalize(eng.compute_embedding("task: search query | text: a red square").embedding)
    blue=normalize(eng.compute_embedding("task: search query | text: a blue circle").embedding)
    for i,path in enumerate(frames):
        t=time.perf_counter()
        vec=normalize(eng.compute_embedding(Content.ImageFile(str(path))).embedding)
        scores={"red_square":round(cosine(vec,red),6),
                "blue_circle":round(cosine(vec,blue),6)}
        metrics.append({"frame_second":i,"elapsed_ms":round((time.perf_counter()-t)*1000,3),
                        "vector_dimensions":len(vec),"similarity":scores,
                        "correct_first":max(scores,key=scores.get)==("red_square" if i==0 else "blue_circle")})
out=HERE/"evidence"/"mac-litert-video-frame-smoke-2026-10-09.json"
out.write_text(json.dumps({"status":"completed","video_pipeline":"ffmpeg 1fps frame extraction, EmbeddingGemma2 vision encoder per frame","not_native_video_encoder":True,"synthetic":True,"frames":metrics},indent=2)+"\n")
print(json.dumps({"status":"completed","frames":metrics,"report":str(out)}))
