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
