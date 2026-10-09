#!/usr/bin/env python3
"""XBSTACK retrieval smoke test. No Google model measurement is fabricated."""
from __future__ import annotations

import argparse
import json
import platform
import resource
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixtures" / "text-retrieval-smoke.json"
OUTPUT = ROOT / "results" / "latest.json"


def evaluate(queries, rank, k=5):
    details = []
    for row in queries:
        start = time.perf_counter()
        ids = rank(row["query"])
        duration = round((time.perf_counter() - start) * 1000, 3)
        gold = set(row["relevant"])
        recall = sum(d in gold for d in ids[:k]) / len(gold)
        rr = next((1.0 / i for i, d in enumerate(ids, 1) if d in gold), 0.0)
        details.append({"id": row["id"], "lang": row["language"],
                        "retrieved": ids[:k], "gold": row["relevant"],
                        "recall_at_k": recall, "rr": rr, "latency_ms": duration})
    return {"status": "completed", "count": len(details), "k": k,
            "recall_at_k": round(sum(r["recall_at_k"] for r in details) / len(details), 4),
            "mrr": round(sum(r["rr"] for r in details) / len(details), 4),
            "mean_latency_ms": round(sum(r["latency_ms"] for r in details) / len(details), 3),
            "per_query": details}


def make_fts(documents):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE VIRTUAL TABLE docs USING fts5(doc_id UNINDEXED, body, tokenize='unicode61')")
    db.executemany("INSERT INTO docs(doc_id,body) VALUES(?,?)",
                   [(r["id"], r["text"]) for r in documents])
    def search(query):
        terms = [t.strip("?!？。，,") for t in query.split() if t.strip("?!？。，,")]
        expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
        if not expr:
            return []
        return [x[0] for x in db.execute(
            "SELECT doc_id FROM docs WHERE docs MATCH ? ORDER BY bm25(docs) ASC", (expr,)
        ).fetchall()]
    return search


def make_model(documents, model_id):
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("missing dependency: " + str(exc)) from exc
    start = time.perf_counter()
    model = SentenceTransformer(model_id, config_kwargs={
        "vision_config": None, "audio_config": None
    })
    load_s = round(time.perf_counter() - start, 3)
    vectors = model.encode([r["text"] for r in documents], prompt_name="Document",
                           normalize_embeddings=True, convert_to_numpy=True)
    ids = [r["id"] for r in documents]
    def search(query):
        q = model.encode([query], prompt_name="SearchQuery",
                         normalize_embeddings=True, convert_to_numpy=True)[0]
        scores = np.asarray(vectors) @ np.asarray(q)
        return [ids[int(i)] for i in np.argsort(-scores)]
    return search, load_s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("fts5", "embeddinggemma2", "both"), default="both")
    parser.add_argument("--model", default="google/embeddinggemma-2")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ids = {d["id"] for d in dataset["documents"]}
    assert all(set(x["relevant"]) <= ids for x in dataset["queries"])
    report = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset["dataset"], "provenance": dataset["provenance"],
        "machine": {"os": platform.system(), "arch": platform.machine(),
                    "python": platform.python_version()},
        "model_id": args.model, "model_scope": "text-only, not full multimodal",
        "not_measured": ["iPhone 13 performance", "battery", "device thermal",
                         "image/audio/video retrieval", "production RecalAI RAG"],
        "backends": {},
    }
    if args.backend in ("fts5", "both"):
        try:
            report["backends"]["sqlite_fts5"] = evaluate(dataset["queries"],
                                                         make_fts(dataset["documents"]), args.k)
        except Exception as exc:
            report["backends"]["sqlite_fts5"] = {"status": "failed", "error": repr(exc)}
    if args.backend in ("embeddinggemma2", "both"):
        try:
            rank, seconds = make_model(dataset["documents"], args.model)
            outcome = evaluate(dataset["queries"], rank, args.k)
            outcome["model_load_seconds"] = seconds
            outcome["peak_rss_raw"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            outcome["rss_units"] = "bytes on macOS; kB on Linux"
            report["backends"]["embeddinggemma2_text_only"] = outcome
        except Exception as exc:
            report["backends"]["embeddinggemma2_text_only"] = {
                "status": "blocked", "error": type(exc).__name__ + ": " + str(exc)
            }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    summary = {"report": str(args.output),
               "backends": {k: {"status": v["status"], "recall_at_k": v.get("recall_at_k"),
                               "mrr": v.get("mrr"), "error": v.get("error")}
                            for k, v in report["backends"].items()}}
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if all(x["status"] == "completed" for x in report["backends"].values()) else 2


if __name__ == "__main__":
    sys.exit(main())
