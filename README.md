# EmbeddingGemma 2 Local Retrieval Lab

Real, reproducible Apple Silicon Mac CPU inference with quantized Google LiteRT-LM. **Not an iPhone 13 or production RAG benchmark.**

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
