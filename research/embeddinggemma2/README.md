# EmbeddingGemma 2 — 可复现端侧检索实验（2026-10-09）

**状态：Mac LiteRT-LM 实际推理已成功；公开新文章 / iPhone 13 性能结论仍未通过门禁。**

本仓库收集 Google EmbeddingGemma 2 的 **真实本地模型运行证据**，严格区分小样本合成测试、正式检索质量基准、生产 RAG 和 iPhone 真机实测。

## 已经实际验证的内容

**文本 270M（Google LiteRT-LM 量化权重，164,626,432 bytes，Apple Silicon Mac，CPU 4 threads）：**

- 源：`litert-community/embeddinggemma-2-text-270m-litert-lm`、`embeddinggemma-2-text-270m.litertlm`；
- 实际模型 SHA256：`2d079ee2f6f066b1f368e8d7c819f55214eaef1d0513b312321901f30ab286fb`；
- 10 个**自编合成文本**、10 条原始中英检索问题：SQLite FTS5 Recall@5 0.70 / MRR 0.70，模型 Recall@5 1.00 / MRR 1.00；
- 将 8 条跨语言人工问题加入后，共 18 条：FTS5 Recall@5 **0.5556** / MRR **0.5278**，模型 Recall@5 **1.00** / MRR **1.00**；跨语言子集仅 8 条，FTS5 Recall@5 **0.375** / MRR **0.3125**，模型均 1.0；
- 18 问实际单次 query embedding 平均耗时 **60.857 ms**，包括模型编码+Python 内积与排序；不是连续吞吐、冷启动可靠性或 iPhone 延迟指标；
- 768 维向量、CPU 模型初始化约 213ms（仅单次）、10 文档嵌入合计约 804ms；记录原始逐题排名、设备及模型哈希。

**完整 740M 多模态（Google LiteRT-LM 量化权重，484,622,336 bytes，Mac CPU）：**

- 源：`litert-community/embeddinggemma-2-740m-litert-lm`；SHA256：`e7a8a2204b91e0f96e92960e84a09a89212e1633dcb7575a9bf3378b4df77f4c`；
- 实际生成两张 320×320 几何图、两条本机合成语音 WAV；文本/图像/音频各 2 次编码都成功，全部输出 768 维向量；
- 图/文正确配对余弦 **0.805209 / 0.795280**，错配 **0.673467 / 0.672283**；音/文正确配对 **0.857802 / 0.868294**，错配 **0.630185 / 0.628279**；
- 图片单次编码约 976–1,363ms；音频约 158–187ms；不同尺寸与模态不可直接拿来比性能；
- FFmpeg 生成 2 秒合成短片，抽取每秒一帧，调用**视觉**编码器检索：两帧都匹配对应文字；这是视频**抽帧**检索，不是原生时序视频模型能力证明。

以上都是**合成、极小规模 smoke test（烟雾测试）**。10 文本、18 问和 2 对图音样本不足以推出生产召回、跨设备效果或任何实际视觉/语音准确率。原始详细结果：

- `evidence/mac-litert-text-2026-10-09.json`
- `evidence/mac-litert-cross-language-2026-10-09.json`
- `evidence/mac-litert-multimodal-2026-10-09.json`
- `evidence/mac-litert-video-frame-smoke-2026-10-09.json`

## 复现（只安装到本实验专用虚拟环境）

要求 macOS arm64、Python 3.12、`uv`、约 2GB 可用空间（如还需其它 PyTorch 环境则要更多），图片合成需要 Pillow，音频合成需要 macOS 的 `say` 和 FFmpeg。

```bash
uv venv research/embeddinggemma2/.venv-litert --python python3.12
uv pip install --python research/embeddinggemma2/.venv-litert/bin/python -r research/embeddinggemma2/requirements-litert.txt

# 下面显式授权首次下载，模型文件缓存于 ~/.cache/huggingface/hub，不进入 Git
research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/litert_benchmark.py --download
research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/litert_benchmark.py --fixture research/embeddinggemma2/fixtures/cross-language-v2.json

research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/create_multimodal_fixtures.py
research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/multimodal_benchmark.py --download
research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/video_frames_smoke.py
python3 -m unittest discover -s research/embeddinggemma2/tests -v
```

默认不开启自动下载；模型已经缓存时，不传 `--download`。首次下载不需要将权重复制到源码。生成的 WAV 与 MP4 被 gitignore，能够在支持环境下由脚本重建。

原来的 `benchmark.py`、`requirements-text-only.txt` 为 PyTorch + Sentence Transformers **非量化原始 checkpoint** 单独实验路径；其完整 `model.safetensors` 约 **1.49GB**，此前在下载期间超时，**没有原始 PyTorch checkpoint 的独立推理结果**。绝不能将 LiteRT 量化结果标成 PyTorch FP32/BF16 测试。

LiteRT 输入必须使用对应的非对称前缀 `task: search query | text:` 和 `task: search result | text:`；Sentence Transformers 使用模型卡定义的 prompts（并不保证与 LiteRT 前缀逐字相同）。跨模型/量化版本必须隔离 embedding 索引并重建、回滚验证。

## 2026-10-10：真实已发布文章的跨语言文本检索 Pilot

运行 `real_corpus_hybrid.py`，读取网站实际发表的 8 个主题、16 篇中英文 Markdown 文章，每篇仅取清理后的前 1,800 字作为索引文本；16 条查询均由作者编写，相关性标签指向另一语言的对应文章。

在 **Mac CPU / LiteRT-LM 270M 量化模型** 中，实际结果：

| 搜索策略 | Recall@5 | MRR |
| --- | ---: | ---: |
| FTS5 / unicode61 | 0.9375 | 0.4871 |
| EmbeddingGemma 2 | 1.0000 | 0.5938 |
| FTS5 + Embedding / RRF(k=60) | 1.0000 | 0.5365 |

原始逐题证据：`evidence/mac-litert-published-articles-hybrid-2026-10-10.json`；运行：

```bash
research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/real_corpus_hybrid.py
```

**重要限制**：这不是独立盲标数据，不是天然生成的 PDF/Word/图片语料，不是 OCR、分块、RecalAI 生产检索、Reranker 或 iPhone 13 性能实验。FTS5 未做中文词法增强，Embedding 只有一次查询集评估；RRF 未调权。在本小样本中，RRF 的 MRR 低于纯 Embedding，不能笼统宣传“混合检索更准”。

## 2026-10-10：PDF / DOCX 转换与 Chunk 检索实测（32 问）

**完整工程报告**：`document-pilot-report-2026-10-10.md`  
**逐题机器原始证据**：`evidence/mac-litert-converted-pdf-docx-chunks-2026-10-10.json`  
**真实模型执行脚本**：`document_format_chunk_pilot.py`  
**专项测试**：`tests/test_document_format_chunk_pilot.py`

实际使用的是站内已发表的 **16 篇中英文技术文章**完整正文，并**生成转换版** 8 份 PDF / 8 份 DOCX，经 pypdf / python-docx 实际解析，按 850 字符 / 120 字符 overlap 生成 **278 个 Chunk**。共 **32 条人工编写的中英文查询**（16 基础 + 16 更难改写），全部在 Mac arm64 LiteRT-LM 270M CPU 四线程执行、模型 SHA 已记录。

| 文档级策略 | Hit@5 | Recall@5 | MRR |
| --- | ---: | ---: | ---: |
| FTS5 unicode61 | 0.8750 | 0.7812 | 0.7396 |
| FTS5 trigram | 1.0000 | 0.7812 | 0.7755 |
| Embedding 768d | 1.0000 | 1.0000 | 0.9688 |
| Embedding 256d | 1.0000 | 1.0000 | 0.9688 |
| Embedding 128d | 1.0000 | 0.9844 | 0.9323 |
| RRF unicode61 + 768d | 1.0000 | 0.9844 | 0.9688 |

- `Hit@5` 代表找中一个相同主题的文档；`Recall@5` 是同时计算中英对应文档的实际相关文档召回；并非证据 Chunk 的准确率。
- 模型单次冷初始化约 **286ms**，278 Chunk 编码总时长约 **53.99s**，32 条 query embedding 平均约 **79.08ms**；仅限当次 Mac CPU 实验，不代表手机。
- 维度 768 → 256 对 278 个 float32 向量的理论纯存储从 854,016B 降至 284,672B；**不含索引元数据和模型权重，也不是推理时间节约数据**。
- 单独将“对应的另一语言文章”视为真值时，768d 跨语言 Hit@5=1.0000 / MRR=0.5000；中英平行文章竞争排序，并不是随机跨语言数据集。
- 这是对**真实文章衍生格式**执行文档解析和模型推理的 Pilot。转换得到的 PDF/DOCX 并非用户自然形成的扫描/复杂文件；没有 OCR、PPT、Rerank、答案与引用准确率、RecalAI 接入、独立盲标或 iPhone 13 真机证据。**不能当生产 Benchmark 或“256d 与 768d 总是等价”的证明。**

重现步骤：

```bash
uv pip install --python research/embeddinggemma2/.venv-litert/bin/python -r research/embeddinggemma2/requirements-document-pilot.txt
research/embeddinggemma2/.venv-litert/bin/python research/embeddinggemma2/document_format_chunk_pilot.py
research/embeddinggemma2/.venv-litert/bin/python -m unittest discover -s research/embeddinggemma2/tests -v
```

默认仅使用已经缓存的模型权重，不自动下载。PDF/DOCX 生成在临时目录并清理；不存在远程上传私人文档。

## 不能声称已完成的内容

1. **iPhone 13 实体真机**：本地仅有 iPhone 13 模拟器 connected；真机显示 unavailable。未测 iPhone 的峰值内存、速度、GPU、耗电、温控、挂起恢复。官方 iPhone 18 Pro 的数据不能转述成 iPhone 13。
2. **RecalAI 的生产级 OCR/PDF 导入 + FTS/Embedding/RRF/Rerank 对照**：本站研究合成数据不是 RecalAI 原始库，尚未接入 RecalAI 真正的 pipeline 或合法授权的真实文件。
3. **真实多模态准确率或长视频理解**：几何图、TTS 和抽帧小样本只验证输入输出可执行，没有多标签评估、人工标注自然图像/录音、原生视频时序语义的可靠证据。
4. **新文章发布门槛**：未对中英 SERP Top 10–20、Google/Bing autocomplete/PAA 和竞争缺口进行可核对的完整评分。未获得新 URL 批准，不应以“iPhone 多模态实测”名义上线；原有 Personal AI 文章还处于 14 天 SEO 观察期。

## 来源

- 官方模型发布：https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/
- 官方 LiteRT Embedding API：https://ai.google.dev/edge/litert-lm/embedding_models
- Google Sentence Transformers 指南：https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers
- LiteRT 270M：https://huggingface.co/litert-community/embeddinggemma-2-text-270m-litert-lm
- LiteRT 740M：https://huggingface.co/litert-community/embeddinggemma-2-740m-litert-lm

所有结果基于可追溯模型哈希与本地脚本；站内或 GitHub 引用必须链接确切版本及相应证据。
