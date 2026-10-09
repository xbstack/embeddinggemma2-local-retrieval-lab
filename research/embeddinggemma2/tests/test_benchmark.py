import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "benchmark.py"
spec = importlib.util.spec_from_file_location("retrieval_harness", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RetrievalHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(mod.FIXTURE.read_text(encoding="utf-8"))

    def test_unique_document_ids(self):
        ids = [x["id"] for x in self.data["documents"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_gold_ids_resolve(self):
        docs = {x["id"] for x in self.data["documents"]}
        self.assertTrue(all(set(x["relevant"]) <= docs for x in self.data["queries"]))

    def test_english_mcp_exact_match(self):
        ranked = mod.make_fts(self.data["documents"])("MCP tool timeout")
        self.assertIn("d03", ranked)

    def test_metrics_measure_missed_queries(self):
        cases = [{"id": "q", "query": "x", "relevant": ["d03"], "language": "zh"}]
        outcome = mod.evaluate(cases, lambda _: [], k=5)
        self.assertEqual(outcome["recall_at_k"], 0.0)
        self.assertEqual(outcome["mrr"], 0.0)

    def test_reciprocal_rank_not_equivalent_to_recall_at_1(self):
        cases = [{"id": "q", "query": "x", "relevant": ["d03"], "language": "en"}]
        outcome = mod.evaluate(cases, lambda _: ["d01", "d03"], k=1)
        self.assertEqual(outcome["recall_at_k"], 0.0)
        self.assertEqual(outcome["mrr"], 0.5)

    def test_bilingual_query_set(self):
        self.assertEqual({x["language"] for x in self.data["queries"]}, {"en", "zh"})


if __name__ == "__main__":
    unittest.main()
