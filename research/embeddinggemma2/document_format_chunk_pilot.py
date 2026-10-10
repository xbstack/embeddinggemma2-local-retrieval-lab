#!/usr/bin/env python3
"""Local LiteRT-LM 270M document-format + chunk retrieval pilot.

REAL source text is taken from already published XBSTACK bilingual Markdown.
PDF/DOCX are *generated conversions of those articles*, NOT independent user
documents. This evaluates extraction and retrieval wiring, not native OCR,
RecalAI integration, physical mobile runtime, or production RAG quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import resource
import sqlite3
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from benchmark import evaluate
from litert_benchmark import FILE, REPO, sha256
from real_corpus_hybrid import PAIRS, ROOT, read_published, reciprocal_rank_fusion


def digest(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def pdf_convert(text: str, path: Path) -> None:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen.canvas import Canvas

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    canvas = Canvas(str(path), pagesize=(595, 842))
    canvas.setTitle("XBSTACK conversion-based document retrieval fixture")
    canvas.setFont("STSong-Light", 10)
    y = 804
    line = ""
    for ch in text:
        if ch == "\n" or pdfmetrics.stringWidth(line + ch, "STSong-Light", 10) > 510:
            if line:
                canvas.drawString(42, y, line)
                y -= 15
            line = ""
            if y < 42:
                canvas.showPage()
                canvas.setFont("STSong-Light", 10)
                y = 804
            if ch == "\n":
                continue
        line += ch
    if line:
        canvas.drawString(42, y, line)
    canvas.save()


def docx_convert(text: str, path: Path) -> None:
    from docx import Document
    doc = Document()
    for offset in range(0, len(text), 600):
        doc.add_paragraph(text[offset:offset + 600])
    doc.save(path)


def extract_document(path: Path) -> tuple[str, int]:
    if path.suffix == ".pdf":
        from pypdf import PdfReader
        pdf = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in pdf.pages]
        return re.sub(r"\s+", " ", " ".join(pages)).strip(), len(pdf.pages)
    if path.suffix == ".docx":
        from docx import Document
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        return re.sub(r"\s+", " ", " ".join(paragraphs)).strip(), len(paragraphs)
    raise ValueError(f"Unsupported format: {path.suffix}")


def chunk_text(text: str, size: int = 850, overlap: int = 120) -> list[str]:
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed non-negative overlap")
    if not text:
        return []
    stride = size - overlap
    return [text[at:at + size] for at in range(0, len(text), stride)
            if text[at:at + size].strip()]


def make_converted_corpus(output_dir: Path, chunk_size: int = 850,
                          overlap: int = 120) -> tuple[list[dict], list[dict], list[dict]]:
    docs, chunks, metadata = [], [], []
    for group_index, (tag, slug, en_query, zh_query) in enumerate(PAIRS):
        for lang in ("zh", "en"):
            relative = (f"src/content/ai/en/{slug}.md" if lang == "en"
                        else f"src/content/ai/{slug}.md")
            path = ROOT / relative
            source_text = read_published(path)  # short-text baseline for an integrity check
            # Extract full-length normalized published article, not its 1800-char pilot.
            raw = path.read_text(encoding="utf-8")
            raw = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", raw, flags=re.S)
            raw = re.sub(r"`{3}.*?`{3}", " ", raw, flags=re.S)
            raw = re.sub(r"<[^>]+>", " ", raw)
            raw = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", raw)
            raw = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", raw)
            text = re.sub(r"\s+", " ", raw).strip()
            if len(text) < len(source_text) or len(text) < 250:
                raise ValueError(f"Unexpectedly short source: {relative}")
            doc_id = f"{tag}-{lang}"
            # Rotate formats per topic, each language has four PDF + four Word.
            fmt = "pdf" if (group_index + (lang == "en")) % 2 == 0 else "docx"
            converted = output_dir / f"{doc_id}.{fmt}"
            (pdf_convert if fmt == "pdf" else docx_convert)(text, converted)
            extracted, pages = extract_document(converted)
            if len(extracted) < 0.88 * len(text):
                raise ValueError(f"Severe extraction loss ({fmt}): {relative}")
            doc_chunks = chunk_text(extracted, chunk_size, overlap)
            docs.append({"id": doc_id, "lang": lang, "format": fmt, "text": extracted})
            chunks.extend({"id": f"{doc_id}::{index:03d}", "parent": doc_id,
                           "text": item} for index, item in enumerate(doc_chunks))
            metadata.append({"doc_id": doc_id, "original_path": relative,
                             "original_sha256": sha256(path), "source_characters": len(text),
                             "extracted_characters": len(extracted),
                             "extraction_retention_ratio": round(len(extracted) / len(text), 4),
                             "converted_format": fmt, "document_pages_or_paragraphs": pages,
                             "chunks": len(doc_chunks),
                             "extracted_sha256": digest(extracted)})
    if len(docs) != 16 or len({d["id"] for d in docs}) != 16:
        raise RuntimeError("Unexpected corpus cardinality")
    return docs, chunks, metadata


# Harder queries are authored BEFORE the measured run, not selected from its results.
# Some concepts overlap across articles by design. The label is the primary
# source article, not proof that no other article has a partial answer.
HARD_QUESTIONS = {
    "mcp-pagination": (
        "An MCP tool response silently clips huge logs. How do I retrieve the remainder without assuming a protocol-wide byte limit?",
        "工具日志被截掉后怎样继续读取剩余部分？不能把 SDK 缓冲限制当成协议限制吧？"),
    "n8n-errors": (
        "Where should a workflow-wide failure alert hook go in n8n, and how should retries and errors be coordinated?",
        "节点失败后怎样让另一个工作流收到告警，同时处理重试和失败？"),
    "langgraph-approval": (
        "Why can a side effect happen twice after a suspended graph resumes, and where should the irreversible action go?",
        "人工审核恢复后为什么中断前的动作可能执行两次，怎样确保不重复？"),
    "checkpoint": (
        "Can multiple agent workers safely share a SQLite checkpoint store for persistent conversation state?",
        "多个并行 Worker 同时存会话状态，SQLite Checkpointer 会遇到什么限制？"),
    "adk-delete": (
        "Does deleting an agent session also erase stored long term memories or do the two have separate lifecycles?",
        "删掉会话为什么持久记忆可能还存在，是否需要单独清理？"),
    "context": (
        "Which parts of an agent's long-running state should stay in a prompt and which belong in searchable external memory?",
        "上下文很长而且越来越贵，应该把哪些状态放到外部检索记忆？"),
    "responses-stream": (
        "How should an app handle a disconnected streamed tool call whose JSON arguments arrived only in fragments?",
        "SSE 断线导致工具调用参数还没拼完整，如何判断该不该恢复重试？"),
    "tool-authorization": (
        "How can an autonomous assistant reject dangerous tool arguments before the privileged operation executes?",
        "如何在 Agent 执行高权限工具前拦截危险参数，防止越权？"),
}


def queries_for_topics() -> list[dict]:
    questions = []
    for tag, _, en, zh in PAIRS:
        for variant, pairs in (("basic", (en, zh)), ("hard", HARD_QUESTIONS[tag])):
            for lang, question in (("en", pairs[0]), ("zh", pairs[1])):
                questions.append({"id": f"{tag}-{lang}-{variant}", "query": question,
                                  "language": lang, "difficulty": variant,
                                  "relevant": [f"{tag}-en", f"{tag}-zh"],
                                  "other_language": [f"{tag}-zh" if lang == "en" else f"{tag}-en"]})
    return questions


def unique_parent_order(chunk_ids: list[str], parents: dict[str, str]) -> list[str]:
    seen, ranked = set(), []
    for cid in chunk_ids:
        parent = parents[cid]
        if parent not in seen:
            seen.add(parent)
            ranked.append(parent)
    return ranked


def fts_ranker(chunks: list[dict], mode: str):
    db = sqlite3.connect(":memory:")
    tokenizer = "trigram" if mode == "trigram" else "unicode61"
    db.execute(f"CREATE VIRTUAL TABLE chunks USING fts5(cid UNINDEXED, body, tokenize='{tokenizer}')")
    db.executemany("INSERT INTO chunks(cid, body) VALUES(?,?)",
                   ((c["id"], c["text"]) for c in chunks))
    parents = {c["id"]: c["parent"] for c in chunks}

    def rank(question: str):
        if mode == "trigram":
            cjk = re.findall(r"[\u3400-\u9fff]+", question)
            terms = [block[i:i+3] for block in cjk for i in range(len(block)-2)]
            # Unicode trigram tokenizer supports arbitrary scripts; these individual
            # trigrams are safe OR tokens and avoid requiring Chinese word segmentation.
            terms += re.findall(r"[A-Za-z0-9_]{3,}", question)
        else:
            terms = [t.strip("?!？。，,") for t in question.split()]
        terms = list(dict.fromkeys(t for t in terms if len(t) >= 3))[:48]
        if not terms:
            return []
        expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
        ids = [x[0] for x in db.execute(
            "SELECT cid FROM chunks WHERE chunks MATCH ? ORDER BY bm25(chunks) ASC, cid ASC",
            (expr,)).fetchall()]
        return unique_parent_order(ids, parents)
    return rank


def metrics(rows: list[dict], ranks: dict[str, list[str]], gold_key: str = "relevant",
            k: int = 5) -> dict:
    evaluation = evaluate([{**row, "relevant": row[gold_key]} for row in rows],
                          lambda q: ranks[q], k=k)
    evaluation["hit_at_1"] = round(sum(bool(set(row[gold_key]) &
                                 set(ranks[row["query"]][:1])) for row in rows) / len(rows), 4)
    evaluation["hit_at_5"] = round(sum(bool(set(row[gold_key]) &
                                 set(ranks[row["query"]][:5])) for row in rows) / len(rows), 4)
    return evaluation


def vector_rank(queries: list[dict], corpus: list[dict], checkpoint: Path):
    import numpy as np
    from litert_lm import Backend, EmbeddingEngine

    indexes = [c["id"] for c in corpus]
    inferred, index_timing, query_timing = {}, [], []
    cold = time.perf_counter()
    with EmbeddingEngine(str(checkpoint), backend=Backend.CPU(thread_count=4)) as engine:
        init_ms = round(1000*(time.perf_counter()-cold), 3)
        vectors = []
        for c in corpus:
            start = time.perf_counter()
            vec = np.asarray(engine.compute_embedding(
                "task: search result | text: " + c["text"]).embedding, dtype=np.float32)
            vectors.append(vec)
            index_timing.append((time.perf_counter()-start)*1000)
        queries_v = {}
        for q in queries:
            start = time.perf_counter()
            v = np.asarray(engine.compute_embedding(
                "task: search query | text: " + q["query"]).embedding, dtype=np.float32)
            queries_v[q["query"]] = v
            query_timing.append((time.perf_counter()-start)*1000)

    original = np.stack(vectors)
    parents = {c["id"]: c["parent"] for c in corpus}
    for dim in (768, 512, 256, 128):
        # MRL requires re-normalization after slicing, for BOTH query and corpus.
        v = original[:, :dim]
        v = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)
        ranks = {}
        for query, qvec in queries_v.items():
            q = qvec[:dim]
            q = q / max(float(np.linalg.norm(q)), 1e-12)
            scores = v @ q
            chunk_order = [indexes[i] for i in np.argsort(-scores, kind="stable")]
            ranks[query] = unique_parent_order(chunk_order, parents)
        inferred[str(dim)] = ranks
    return inferred, {"model_init_ms": init_ms,
                      "document_embedding_total_ms": round(sum(index_timing), 2),
                      "document_embedding_mean_ms": round(statistics.mean(index_timing), 2),
                      "query_embedding_mean_ms": round(statistics.mean(query_timing), 2),
                      "query_embedding_p95_ms": round(sorted(query_timing)[int(.95*(len(query_timing)-1))], 2),
                      "vector_count": len(vectors), "native_dimensions": len(vectors[0])}


def run(args) -> dict:
    from huggingface_hub import hf_hub_download
    checkpoint = args.model_file or Path(hf_hub_download(
        repo_id=REPO, filename=FILE, local_files_only=True))
    with tempfile.TemporaryDirectory(prefix="xbstack-eg2-doc-") as directory:
        docs, chunks, metadata = make_converted_corpus(Path(directory),
                                                       args.chunk_size, args.overlap)
        questions = queries_for_topics()
        lexical = {}
        for mode in ("unicode61", "trigram"):
            lookup = fts_ranker(chunks, mode)
            lexical[mode] = {q["query"]: lookup(q["query"]) for q in questions}
        embeddings, timing = vector_rank(questions, chunks, checkpoint)
    evaluations = {}
    for label, ranks in {**{f"fts5_{mode}": rows for mode, rows in lexical.items()},
                         **{f"embedding_{d}": rows for d, rows in embeddings.items()}}.items():
        evaluations[label] = metrics(questions, ranks)
    for mode in ("unicode61", "trigram"):
        for dimension in (768, 256):
            merged = {q["query"]: reciprocal_rank_fusion(
                lexical[mode][q["query"]], embeddings[str(dimension)][q["query"]])
                for q in questions}
            evaluations[f"rrf_{mode}_{dimension}"] = metrics(questions, merged)
    # Explicit cross-language-only success is secondary; not the primary metric.
    cross_language = {key: metrics(questions, rows, "other_language")
                      for key, rows in {**{f"fts5_{m}": v for m,v in lexical.items()},
                                       **{f"embedding_{d}": v for d,v in embeddings.items()}}.items()}
    # Keep full per-query ranks, not only aggregate scores.
    result = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "published articles converted to real PDF and DOCX, extraction -> overlapping chunks -> FTS / quantized embeddings / RRF",
        "model": {"repo": REPO, "file": FILE, "sha256": sha256(checkpoint),
                  "runtime": "LiteRT-LM CPU 4 threads, quantized 270M text"},
        "hardware": {"os": platform.system(), "arch": platform.machine(),
                     "python": platform.python_version()},
        "corpus": {"documents": len(docs), "pdf_documents": sum(d["format"]=="pdf" for d in docs),
                   "docx_documents": sum(d["format"]=="docx" for d in docs),
                   "chunks": len(chunks), "questions": len(questions),
                   "chunk_char_size": args.chunk_size, "overlap_chars": args.overlap},
        "provenance": metadata, "timing": timing,
        "metrics": evaluations, "cross_language_only_metrics": cross_language,
        "vector_storage_estimates_bytes": {str(dim): len(chunks)*dim*4
                                           for dim in (768, 512, 256, 128)},
        "per_query_parent_rankings": {**{f"fts5_{m}":r for m,r in lexical.items()},
                                     **{f"embedding_{d}":r for d,r in embeddings.items()}},
        "peak_rss_bytes_mac": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "limitations": [
            "PDF/DOCX are generated conversions of real published Markdown, not independently sourced natural documents",
            "Neither scanned PDFs, OCR, tables, images, handwritten text, native multimodal PDF embedding, nor genuine user documents evaluated",
            "Only 8 topics, 16 documents, 16 author-written queries and labels; no blinded external relevance judges",
            "Retrieval ranking is aggregated at parent-document level from chunk rankings, not evidence passage accuracy",
            "FTS5 unicode61 and naive trigram lexical baselines are not language-specific production BM25",
            "No RecalAI application integration, reranker, answer generation, citation accuracy, iPhone 13, GPU or battery tests",
            "MRL storage estimate is float32 vectors only, no metadata/index overhead; all dimensions reuse ONE 768d inference pass",
            "Generated PDF/DOCX files are temporary and removed after parsing; no private materials in output",
        ],
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-file", type=Path)
    parser.add_argument("--chunk-size", type=int, default=850)
    parser.add_argument("--overlap", type=int, default=120)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent /
                        "evidence/mac-litert-converted-pdf-docx-chunks-2026-10-10.json")
    args = parser.parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": "completed", "corpus": result["corpus"],
                      "metrics": {key: {"hit_at_5": value["hit_at_5"], "mrr": value["mrr"]}
                                  for key,value in result["metrics"].items()},
                      "timing": result["timing"], "evidence": str(args.output)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
