#!/usr/bin/env python3
"""Quantized EmbeddingGemma 2 full-model modality I/O smoke test.

No claims about video support, iPhone runtime, production quality or accuracy.
"""
from __future__ import annotations
import argparse
import json
import platform
import resource
import time
from datetime import datetime, timezone
from pathlib import Path
from importlib.metadata import version
from huggingface_hub import hf_hub_download
from litert_lm import Backend, Content, EmbeddingEngine
from litert_benchmark import normalize, cosine, sha256

HERE = Path(__file__).resolve().parent
REPO = "litert-community/embeddinggemma-2-740m-litert-lm"
FILE = "embeddinggemma-2-740m.litertlm"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-file", type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--output", type=Path, default=HERE / "evidence" / "mac-litert-multimodal-2026-10-09.json")
    args = parser.parse_args()
    root = HERE / "fixtures" / "multimodal-synthetic"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    model = args.model_file or Path(hf_hub_download(
        repo_id=REPO, filename=FILE, local_files_only=not args.download
    ))
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "synthetic_modality_io_only",
        "model_repo": REPO, "model_file": FILE,
        "model_bytes": model.stat().st_size, "model_sha256": sha256(model),
        "runtime": {"litert_lm": version("litert-lm"), "hardware": platform.machine(),
                    "os": platform.system(), "backend": "CPU four threads all encoders"},
        "dataset": manifest,
        "limitations": ["No real-world retrieval accuracy evaluation",
                        "No independent image/audio annotation of natural samples",
                        "No video-frame pipeline or iPhone 13 physical device",
                        "No full production RAG/hybrid/rerank comparison"],
        "items": [],
    }
    with EmbeddingEngine(str(model), backend=Backend.CPU(thread_count=4),
                         vision_backend=Backend.CPU(thread_count=4),
                         audio_backend=Backend.CPU(thread_count=4)) as engine:
        embeddings = {"text":{}, "image":{}, "audio":{}}
        for case in manifest["labels"]:
            key = case["id"]
            payloads = [
                ("text", "task: search query | text: " + case["text"]),
                ("image", Content.ImageFile(str(root / case["image"]))),
            ]
            if case["speech"]:
                payloads.append(("audio", Content.AudioFile(str(root / case["speech"]))))
            for modality, payload in payloads:
                start = time.perf_counter()
                try:
                    output = engine.compute_embedding(payload)
                    emb = normalize(output.embedding)
                    embeddings[modality][key] = emb
                    report["items"].append({
                        "id":key, "modality":modality, "status":"completed",
                        "dimensions":len(emb),
                        "elapsed_ms":round((time.perf_counter()-start)*1000,3)
                    })
                except Exception as exc:
                    report["items"].append({
                        "id":key, "modality":modality, "status":"blocked",
                        "error":f"{type(exc).__name__}: {exc}",
                    })
        report["pairwise_cosine"] = []
        for mod in ["image", "audio"]:
            for key, vector in embeddings[mod].items():
                for text_key, text_emb in embeddings["text"].items():
                    report["pairwise_cosine"].append({
                        "source_modality":mod, "source_id":key,
                        "query_modality":"text", "query_id":text_key,
                        "cosine":round(cosine(vector,text_emb),6),
                        "same_synthetic_label":key==text_key,
                    })
    report["peak_rss_raw"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["peak_rss_units"] = "bytes on macOS, KB on Linux; includes process and Python"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":report["status"],"checks":[
            (r["id"],r["modality"],r["status"],r.get("elapsed_ms"),r.get("error"))
            for r in report["items"]
        ],"pairwise_cosine":report["pairwise_cosine"],
        "report":str(args.output)},ensure_ascii=False))
    return 0 if all(x["status"]=="completed" for x in report["items"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
