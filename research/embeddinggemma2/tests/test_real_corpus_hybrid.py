from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from real_corpus_hybrid import make_dataset, reciprocal_rank_fusion


class PublishedArticleRetrievalPilotTests(unittest.TestCase):
    def test_published_bilingual_source_and_cross_language_labels(self) -> None:
        dataset, sources = make_dataset()
        ids = {item["id"] for item in dataset["documents"]}
        self.assertEqual(len(dataset["documents"]), 16)
        self.assertEqual(len(sources), 16)
        self.assertEqual(len(dataset["queries"]), 16)
        self.assertEqual(len(ids), 16)
        self.assertTrue(all(query["cross_language"] for query in dataset["queries"]))
        for query in dataset["queries"]:
            self.assertTrue(set(query["relevant"]) <= ids)
            self.assertTrue(all(doc_id.endswith("-zh" if query["language"] == "en" else "-en")
                                for doc_id in query["relevant"]))

    def test_reciprocal_rank_fusion_is_stable_and_deduplicated(self) -> None:
        result = reciprocal_rank_fusion(["a", "b", "c"], ["b", "c", "d"])
        self.assertEqual(result[0], "b")
        self.assertEqual(set(result), {"a", "b", "c", "d"})
        self.assertEqual(len(result), 4)

    def test_empty_rankings_do_not_invent_documents(self) -> None:
        self.assertEqual(reciprocal_rank_fusion([], []), [])


if __name__ == "__main__":
    unittest.main()
