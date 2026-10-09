#!/usr/bin/env python3
"""Run *real* quantized Google EmbeddingGemma 2 text retrieval on CPU.

Separate from Hugging Face torch checkpoint. Does not claim iOS performance.
Never substitutes dummy vectors for failed model inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from benchmark import FIXTURE, evaluate, make_fts

REPO = "litert-community/embeddinggemma-2-text-270m-litert-lm"
FILE = "embeddinggemma-2-text-270m.litertlm"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(vector):
    v = list(float(x) for x in vector)
    norm = math.sqrt(sum(x * x for x in v))
    if not v or norm <= 0:
        raise ValueError("Empty or zero embedding")
    return [x / norm for x in v]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "evidence" / "mac-litert-text-2026-10-09.json")
    parser.add_argument("--model-file", type=Path)
    parser.add_argument("--download", action="store_true",
                        help="Explicitly authorize downloading the model into local HF cache.")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    dataset = json.loads(args.fixture.read_text(encoding="utf-8"))
    ids = [row["id"] for row in dataset["documents"]]
    if len(ids) != len(set(ids)) or not all(set(q["relevant"]) <= set(ids) for q in dataset["queries"]):
        raise ValueError("Invalid or unresolvable gold labels")

    from huggingface_hub import hf_hub_download, __version__ as hf_version
    from litert_lm import Backend, EmbeddingEngine
    from importlib.metadata import version
    import numpy

    checkpoint = args.model_file
    if checkpoint is None:
        checkpoint = Path(hf_hub_download(
            repo_id=REPO, filename=FILE, local_files_only=not args.download,
        ))
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)

    run = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "synthetic engineering smoke test, NOT independent quality benchmark",
        "model_repo": REPO, "model_file": FILE, "model_bytes": checkpoint.stat().st_size,
        "model_sha256": sha256(checkpoint),
        "backend": f"LiteRT-LM CPU({args.threads} threads), quantized 270M text-only",
        "versions": {"litert_lm": version("litert-lm"), "numpy": numpy.__version__,
                     "huggingface_hub": hf_version},
        "machine": {"system": platform.system(), "machine": platform.machine(),
                    "processor": platform.processor(), "python": platform.python_version()},
        "data": {"dataset": dataset["dataset"], "provenance": dataset["provenance"],
                 "docs": len(ids), "queries": len(dataset["queries"]),
                 "languages": sorted({q["language"] for q in dataset["queries"]})},
        "limitations": [
            "Not physical iPhone 13, iOS simulator, RecalAI, or full RAG pipeline",
            "Does not evaluate image/audio/video or 740M multimodal models",
            "Corpus contains 10 authored synthetic short texts, not parsed PDFs or user files",
            "Not production hybrid FTS + embedding + RRF + reranker evaluation",
            "One cold launch and one pass; timing varies by load, device and OS",
        ],
    }

    fts = evaluate(dataset["queries"], make_fts(dataset["documents"]), k=args.k)
    run["baseline_sqlite_fts5"] = fts
    cold = time.perf_counter()
    with EmbeddingEngine(str(checkpoint), backend=Backend.CPU(thread_count=args.threads)) as engine:
        initialization_ms = round((time.perf_counter() - cold) * 1000, 3)
        index_start = time.perf_counter()
        doc_vec = [normalize(engine.compute_embedding(
            "task: search result | text: " + row["text"].strip()
        ).embedding) for row in dataset["documents"]]
        index_ms = round((time.perf_counter() - index_start) * 1000, 3)
        dims = {len(v) for v in doc_vec}
        if len(dims) != 1:
            raise RuntimeError(f"Inconsistent document vector dimensions: {dims}")

        def search(query):
            q = normalize(engine.compute_embedding(
                "task: search query | text: " + query.strip()
            ).embedding)
            if len(q) != next(iter(dims)):
                raise RuntimeError("Document/query embedding dimensions disagree")
            scores = [cosine(q, vec) for vec in doc_vec]
            ranked = sorted(range(len(ids)), key=lambda n: (-scores[n], ids[n]))
            return [ids[i] for i in ranked]

        actual = evaluate(dataset["queries"], search, k=args.k)
    run["embeddinggemma2_litert_cpu"] = {
        **actual,
        "vector_dimensions": next(iter(dims)),
        "model_init_ms": initialization_ms,
        "document_embedding_total_ms": index_ms,
        "process_peak_rss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "process_peak_rss_unit": "bytes on macOS; KB on Linux",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed", "model": REPO, "model_sha256": run["model_sha256"],
        "doc_count": len(ids), "query_count": len(dataset["queries"]), "vector_dimensions": next(iter(dims)),
        "fts_recall_at_5": fts["recall_at_k"], "fts_mrr": fts["mrr"],
        "model_recall_at_5": actual["recall_at_k"], "model_mrr": actual["mrr"],
        "model_init_ms": initialization_ms, "document_embedding_total_ms": index_ms,
        "model_query_latency_mean_ms": actual["mean_latency_ms"], "report": str(args.output),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
