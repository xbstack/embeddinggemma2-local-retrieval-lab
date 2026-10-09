"""Static evidence checks; do not re-download model to run test suite."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("local_litert_benchmark", ROOT / "litert_benchmark.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LiteRTLabEvidenceTests(unittest.TestCase):
    def test_vector_normalization(self):
        self.assertEqual([round(x, 6) for x in module.normalize([3, 4])], [.6, .8])
        with self.assertRaises(ValueError):
            module.normalize([0, 0])

    def test_cosine_product(self):
        self.assertAlmostEqual(module.cosine([1, 0], [0, 1]), 0)
        self.assertAlmostEqual(module.cosine([1, 0], [1, 0]), 1)

    def test_cross_language_fixture_labels(self):
        data = json.loads((ROOT / "fixtures" / "cross-language-v2.json").read_text())
        ids = {r["id"] for r in data["documents"]}
        self.assertEqual(len(data["queries"]), 18)
        self.assertEqual(sum(bool(q.get("cross_language")) for q in data["queries"]), 8)
        self.assertTrue(all(set(q["relevant"]) <= ids for q in data["queries"]))

    def test_real_model_evidence_not_dummy(self):
        evidence = json.loads((ROOT / "evidence" / "mac-litert-cross-language-2026-10-09.json").read_text())
        b = evidence["embeddinggemma2_litert_cpu"]
        self.assertEqual(b["vector_dimensions"], 768)
        self.assertEqual(b["status"], "completed")
        self.assertEqual(len(b["per_query"]), 18)
        self.assertEqual(evidence["model_sha256"], "2d079ee2f6f066b1f368e8d7c819f55214eaef1d0513b312321901f30ab286fb")
        self.assertIn("synthetic", evidence["purpose"].lower())

    def test_multimodal_evidence_is_smoke_only(self):
        evidence = json.loads((ROOT / "evidence" / "mac-litert-multimodal-2026-10-09.json").read_text())
        self.assertEqual(len(evidence["items"]), 6)
        self.assertTrue(all(r["status"] == "completed" for r in evidence["items"]))
        self.assertIn("synthetic", evidence["status"])
        self.assertIn("No video-frame pipeline or iPhone 13 physical device", evidence["limitations"])

    def test_video_explicitly_frame_based(self):
        evidence = json.loads((ROOT / "evidence" / "mac-litert-video-frame-smoke-2026-10-09.json").read_text())
        self.assertTrue(evidence["not_native_video_encoder"])
        self.assertEqual(len(evidence["frames"]), 2)


if __name__ == "__main__":
    unittest.main()
