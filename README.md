# EmbeddingGemma 2 Local Retrieval Lab

**Real, reproducible Mac CPU LiteRT-LM inference**, with honest limits.

- Google LiteRT-LM 270M text quantized model; 10 tiny synthetic docs and 18 queries, 8 cross-language. EmbeddingGemma 2 Recall@5 and MRR were both 1.0 on **this simple toy data only**; SQLite FTS5 respectively 0.5556 and 0.5278.
- 740M multimodal quantized model; two synthetic images and two synthetic TTS audios successfully embedded. Synthetic two-frame MP4 -> FFmpeg frames -> vision encoder also ran.
- **Not an iPhone 13 test**, not an official production comparison, not a real-world image/audio/video quality benchmark. No raw weights or user content in this repository.
- Every run records exact model hash, device scope, per-query results and limitations in JSON.

Read the [reproduction guide](research/embeddinggemma2/README.md), [text evidence](research/embeddinggemma2/evidence/mac-litert-cross-language-2026-10-09.json), and [multimodal evidence](research/embeddinggemma2/evidence/mac-litert-multimodal-2026-10-09.json). No model weights are bundled; official LiteRT community repo provides downloads.

For broader architecture (not a model-specific independent benchmark), see [Personal AI Agent Architecture at XBSTACK](https://www.xbstack.com/en/ai/personal-ai-agent-architecture/?utm_source=github&utm_medium=referral&utm_campaign=embeddinggemma2_mac_litert_repro&utm_content=repo_readme&ref=github).

Sources: [Google developer guide](https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/) · [LiteRT embeddings](https://ai.google.dev/edge/litert-lm/embedding_models)
