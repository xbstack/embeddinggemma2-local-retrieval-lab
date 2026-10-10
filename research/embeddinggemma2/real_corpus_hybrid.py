#!/usr/bin/env python3
"""Evaluate quantized EmbeddingGemma 2 against real *published XBSTACK Markdown*.

This is a targeted, author-labelled bilingual production-like text retrieval
pilot, NOT independent PDF/Word/OCR, user-data, or iPhone validation.
The two-language source articles are published; queries and gold labels were
manually authored for this small pilot. No private source files are exported.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import resource
import time
from datetime import datetime, timezone
from pathlib import Path

from benchmark import evaluate, make_fts
from litert_benchmark import REPO, FILE, normalize, sha256

ROOT = Path(__file__).resolve().parents[2]
PAIRS = [
    ("mcp-pagination", "mcp-tool-call-truncated-fix",
     "How can I paginate oversized MCP tool results?", "MCP 工具调用结果太长时怎么分页？"),
    ("n8n-errors", "n8n-ai-workflow-error-handling",
     "How to configure n8n Error Workflow and retries?", "n8n 错误工作流和失败重试怎么配置？"),
    ("langgraph-approval", "langgraph-human-in-the-loop-approval",
     "How can LangGraph interrupt and resume human approval?", "LangGraph 人工审批如何中断并恢复？"),
    ("checkpoint", "langgraph-checkpointer-memory-sqlite-redis",
     "How to choose a LangGraph SQLite checkpoint store?", "LangGraph Checkpointer 用 SQLite 有什么限制？"),
    ("adk-delete", "google-adk-delete-session-memory-retained",
     "Why does Google ADK delete_session leave long term memory?", "Google ADK 删除会话后为何仍保留长期记忆？"),
    ("context", "context-engineering-agent-cost-memory-tools",
     "How do retrieval and memory affect agent context cost?", "AI Agent 怎么用检索和记忆降低上下文成本？"),
    ("responses-stream", "openai-responses-api-stream-abort-tool-call-lost",
     "How can an aborted Responses API stream lose tool call arguments?", "Responses API 流式中断为什么丢失工具调用？"),
    ("tool-authorization", "ai-agent-tool-authorization-policy-gate",
     "How to implement an agent tool authorization policy gate?", "Agent 工具授权策略门禁应该怎样做？"),
]


def read_published(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", raw, flags=re.S)
    raw = re.sub(r"\x60{3}.*?\x60{3}", " ", raw, flags=re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", raw)
    raw = re.sub(r"\[[^]]+\]\([^)]*\)", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    # Small deterministic budget, not full document or RAG chunk evaluation.
    return raw[:1800]


def make_dataset() -> tuple[dict, list[dict]]:
    docs, queries, sources = [], [], []
    for tag, slug, en_question, zh_question in PAIRS:
        for lang in ("zh", "en"):
            relative = (f"src/content/ai/en/{slug}.md"
                        if lang == "en" else f"src/content/ai/{slug}.md")
            path = ROOT / relative
            content = read_published(path)
            if len(content) < 120:
                raise ValueError(f"Source too short: {relative}")
            docs.append({"id": f"{tag}-{lang}", "lang": lang, "text": content})
            sources.append({"id": f"{tag}-{lang}", "path": relative,
                            "sha256": sha256(path), "chars_used": len(content)})
        # Cross-language: the gold document is explicitly in the other language.
        queries.extend([
            {"id": f"{tag}-q-en", "query": en_question,
             "relevant": [f"{tag}-zh"], "language": "en", "cross_language": True},
            {"id": f"{tag}-q-zh", "query": zh_question,
             "relevant": [f"{tag}-en"], "language": "zh", "cross_language": True},
        ])
    return {"documents": docs, "queries": queries}, sources


def reciprocal_rank_fusion(a: list[str], b: list[str], weight_a: float = 1.0,
                           weight_b: float = 1.0, constant: int = 60) -> list[str]:
    scores = {}
    for ranking, weight in ((a, weight_a), (b, weight_b)):
        for index, document in enumerate(ranking):
            scores[document] = scores.get(document, 0.0) + weight / (constant + index + 1)
    return sorted(scores, key=lambda identifier: (-scores[identifier], identifier))


def run(args) -> dict:
    import numpy as np
    from huggingface_hub import hf_hub_download
    from litert_lm import Backend, EmbeddingEngine

    dataset, sources = make_dataset()
    docs, queries = dataset["documents"], dataset["queries"]
    ids = [item["id"] for item in docs]
    model_path = args.model_file or Path(hf_hub_download(repo_id=REPO, filename=FILE,
                                                         local_files_only=True))
    fts_rank = make_fts(docs)
    fts = evaluate(queries, fts_rank, k=args.k)
    with EmbeddingEngine(str(model_path), backend=Backend.CPU(thread_count=4)) as engine:
        index_start = time.perf_counter()
        vectors = [np.asarray(normalize(engine.compute_embedding(
            "task: search result | text: " + item["text"]).embedding))
            for item in docs]
        index_ms = round(1000 * (time.perf_counter() - index_start), 2)

        def embedding_rank(query: str) -> list[str]:
            qvec = np.asarray(normalize(engine.compute_embedding(
                "task: search query | text: " + query).embedding))
            similarities = [float(qvec @ vector) for vector in vectors]
            return [ids[i] for i in sorted(range(len(ids)), key=lambda i: (-similarities[i], ids[i]))]

        # Cache query embeddings across embedding-only and fused evaluations.
        query_ranks = {item["query"]: embedding_rank(item["query"]) for item in queries}
        model = evaluate(queries, lambda q: query_ranks[q], k=args.k)
        hybrid = evaluate(queries, lambda q: reciprocal_rank_fusion(
            fts_rank(q), query_ranks[q]), k=args.k)

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "real published article text; author-labelled cross-language query pilot",
        "model": {"repo": REPO, "sha256": sha256(model_path),
                  "quantization": "LiteRT-LM 270M text-only"},
        "hardware": {"os": platform.system(), "arch": platform.machine(),
                     "python": platform.python_version()},
        "documents": len(ids), "queries": len(queries),
        "provenance": sources,
        "fts": fts, "embedding": model, "hybrid_rrf_60": hybrid,
        "index_ms": index_ms,
        "peak_rss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "limitations": [
            "Real published Markdown texts, not raw PDF/DOCX/OCR or private user documents",
            "Only the first 1800 normalized characters of each article are indexed",
            "Author-written queries/gold labels; not independent blinded annotation",
            "Only 8 topics, 16 localized articles, 16 cross-language queries",
            "No separate reranker, OCR, RAG generation, native iPhone measurement",
            "Embedding query times in these cached-rank evaluations exclude model inference",
            "FTS baseline is unicode61 without Chinese segmentation",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-file", type=Path)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent /
                        "evidence/mac-litert-published-articles-hybrid-2026-10-10.json")
    args = parser.parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "docs": result["documents"], "queries": result["queries"],
                      "fts": [result["fts"]["recall_at_k"], result["fts"]["mrr"]],
                      "embedding": [result["embedding"]["recall_at_k"], result["embedding"]["mrr"]],
                      "rrf": [result["hybrid_rrf_60"]["recall_at_k"], result["hybrid_rrf_60"]["mrr"]],
                      "report": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
