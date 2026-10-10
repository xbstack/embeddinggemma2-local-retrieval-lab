from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from document_format_chunk_pilot import (
    chunk_text, docx_convert, extract_document, fts_ranker, make_converted_corpus,
    metrics, pdf_convert, queries_for_topics, unique_parent_order,
)


class DocumentFormatChunkPilotTests(unittest.TestCase):
    def test_pdf_and_docx_chinese_english_text_round_trip(self):
        sample = "中文知识库检索 EmbeddingGemma 2 PDF Word 正文和引用。MCP cursor pagination."
        with tempfile.TemporaryDirectory() as tmp:
            for suffix, convert in (("pdf", pdf_convert), ("docx", docx_convert)):
                path = Path(tmp) / f"test.{suffix}"
                convert(sample, path)
                extracted, count = extract_document(path)
                self.assertGreaterEqual(count, 1)
                self.assertIn("EmbeddingGemma", extracted)
                self.assertIn("中文知识库检索", extracted)
                self.assertIn("pagination", extracted)

    def test_chunk_overlap_and_no_empty_or_invented_chunks(self):
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("abcdefghijk", size=5, overlap=2),
                         ["abcde", "defgh", "ghijk", "jk"])
        with self.assertRaises(ValueError):
            chunk_text("hello", size=5, overlap=5)

    def test_parent_ranking_deduplicates_with_stable_order(self):
        parents = {"d1::0": "d1", "d1::1": "d1", "d2::0": "d2"}
        self.assertEqual(unique_parent_order(["d1::0", "d1::1", "d2::0"], parents),
                         ["d1", "d2"])

    def test_parent_metrics_do_not_confuse_gold_labels(self):
        queries = [{"id":"q", "query":"中文检索", "language":"zh",
                    "relevant":["topic-en","topic-zh"],
                    "other_language":["topic-en"]}]
        rankings = {"中文检索": ["topic-zh", "topic-en"]}
        result = metrics(queries, rankings)
        self.assertEqual(result["recall_at_k"], 1.0)
        self.assertEqual(result["mrr"], 1.0)
        other = metrics(queries, rankings, "other_language")
        self.assertEqual(other["mrr"], 0.5)

    def test_generated_formats_are_actual_parsed_published_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs, chunks, sources = make_converted_corpus(Path(tmp))
            self.assertEqual(len(docs), 16)
            self.assertEqual(sum(d["format"]=="pdf" for d in docs), 8)
            self.assertEqual(sum(d["format"]=="docx" for d in docs), 8)
            self.assertEqual({d["id"] for d in docs}, {m["doc_id"] for m in sources})
            self.assertTrue(all(m["source_characters"] > 250 for m in sources))
            self.assertTrue(all(m["extracted_characters"] >=
                                0.88 * m["source_characters"] for m in sources))
            self.assertGreater(len(chunks), 100)
            self.assertTrue(all(c["parent"] in {d["id"] for d in docs} for c in chunks))
            questions = queries_for_topics()
            self.assertEqual(len(questions), 32)
            self.assertTrue(all(set(q["relevant"]) <= {d["id"] for d in docs} for q in questions))
            for mode in ("unicode61","trigram"):
                rank = fts_ranker(chunks,mode)
                self.assertTrue(all(set(rank(q["query"])) <= {d["id"] for d in docs}
                                    for q in questions))


if __name__ == "__main__":
    unittest.main()
