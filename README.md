# EmbeddingGemma 2 Local Retrieval Lab

Real, reproducible Apple Silicon Mac CPU inference with quantized Google LiteRT-LM. **Not an iPhone 13 or production RAG benchmark.**

## Scope boundary: LiteRT-LM inference vs LiteRT Tensor API graph authoring (Oct 2026)

**Do not confuse this repository's quantized LiteRT-LM inference tests with the separate LiteRT Tensor API.** This lab measures a small set of EmbeddingGemma 2 retrieval tasks on Mac CPU via LiteRT-LM. The newer **LiteRT Tensor API** is a C++ computation-graph authoring interface with explicitly different supported execution routes: XNNPACK CPU, TFLite/CompiledModel, and the documented ML Drift GPU route. Neither this lab nor that API's existence demonstrates a particular phone's NPU execution, driver/operator coverage, memory use, or speedup. Those require a target-device trace and pinned model/backend.

- [Google official Tensor API introduction](https://developers.googleblog.com/en/native-model-authoring-for-edge-with-litert-tensor-api/) and [LiteRT tensor source README](https://github.com/google-ai-edge/LiteRT/blob/main/tensor/README.md).
- [Bilingual XBSTACK C++ Tensor API execution-path decision guide](https://www.xbstack.com/en/ai/litert-tensor-api-cpp-xnnpack-gpu-npu/?utm_source=github&utm_medium=referral&utm_campaign=litert_tensor_api_route&utm_content=related_repo_readme) — **documentation/engineering analysis only, not an independent Tensor API hardware benchmark**.

## Mac 270M PDF/DOCX conversion pilot — 2026-10-10

We converted 16 genuinely published XBSTACK bilingual technical articles into 8 real PDF and 8 DOCX files, re-parsed them, and indexed 278 overlapping chunks. The exact original public Markdown sources and their SHA256 fingerprints are included in this repo. 32 author-written queries compared SQLite FTS5 with 768/512/256/128d text embeddings and equal-weight RRF. These files are conversions, not native/scanned PDFs. No OCR or independent human passage annotations were evaluated.

| Document-level method | Hit@5 | Recall@5 | MRR |
| --- | ---: | ---: | ---: |
| FTS5 unicode61 | 0.8750 | 0.7812 | 0.7396 |
| FTS5 trigram | 1.0000 | 0.7812 | 0.7755 |
| Embedding 768d | 1.0000 | 1.0000 | 0.9688 |
| Embedding 256d | 1.0000 | 1.0000 | 0.9688 |
| Embedding 128d | 1.0000 | 0.9844 | 0.9323 |
| FTS5 unicode61 + 768d RRF | 1.0000 | 0.9844 | 0.9688 |

RRF did not improve pure-embedding MRR in this dataset. 256d matched 768d only for this small author-labelled parent-document retrieval test, and uses one-third as many raw float32 vector coordinate bytes. No phone latency, Reranker, OCR, generated answer correctness or natural user-document benchmark is claimed.

- [Complete lab report](research/embeddinggemma2/document-pilot-report-2026-10-10.md)
- [English XBSTACK engineering analysis](https://www.xbstack.com/en/ai/embeddinggemma-2-local-retrieval-test/?utm_source=github&utm_medium=referral&utm_campaign=embeddinggemma2_local_retrieval&utm_content=repository_readme) | [中文实测文章](https://www.xbstack.com/ai/embeddinggemma-2-local-retrieval-test/?utm_source=github&utm_medium=referral&utm_campaign=embeddinggemma2_local_retrieval&utm_content=repository_readme)
### Corpus articles referenced in the retrieval experiment

- [MCP tool result truncation: practical pagination and cursor fixes](https://www.xbstack.com/en/ai/mcp-tool-call-truncated-fix/?utm_source=github&utm_medium=referral&utm_campaign=embeddinggemma2_corpus&utm_content=mcp_source_article) — one real published-article source topic used in this corpus.
- [n8n AI Error Workflow: practical error handling](https://www.xbstack.com/en/ai/n8n-ai-workflow-error-handling/?utm_source=github&utm_medium=referral&utm_campaign=embeddinggemma2_corpus&utm_content=n8n_source_article) — another indexed published-article source topic.

The original Markdown snapshots and exact hashes retained in this repository, rather than the evolving live pages, define the reproducible benchmark inputs.
- [Reproduction code](research/embeddinggemma2/document_format_chunk_pilot.py)
- [Full per-query evidence and source hashes](research/embeddinggemma2/evidence/mac-litert-converted-pdf-docx-chunks-2026-10-10.json)
- [Dependency list](research/embeddinggemma2/requirements-document-pilot.txt)
- [Lab instructions, older smoke tests and limitations](research/embeddinggemma2/README.md)

Run from the repository root with macOS arm64, Python 3.12 and uv. The quantized model weight is **not** bundled. Download separately via the official model reference in the lab guide; normal benchmark runs use cached weights.

    uv venv research/embeddinggemma2/.venv-litert --python python3.12
    uv pip install --python research/embeddinggemma2/.venv-litert/bin/python -r research/embeddinggemma2/requirements-litert.txt
    uv pip install --python research/embeddinggemma2/.venv-litert/bin/python -r research/embeddinggemma2/requirements-document-pilot.txt
    research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/litert_benchmark.py --download
    research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/document_format_chunk_pilot.py
    research/embeddinggemma2/.venv-litert/bin/python -m unittest discover -s research/embeddinggemma2/tests -v

Official references: https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/ and https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2.

For adjacent architecture: https://www.xbstack.com/en/ai/personal-ai-agent-architecture/?utm_source=github&utm_medium=referral&utm_campaign=embeddinggemma2_mac_litert_repro&utm_content=repo_readme
