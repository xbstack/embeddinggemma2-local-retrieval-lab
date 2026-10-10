# EmbeddingGemma 2 本地 PDF/Word 知识检索实测｜XBSTACK 工程报告

> 日期：2026-10-10（本地实际推理） · 状态：**可复现实验完成，生产级 Benchmark / RecalAI / iPhone 13 验证未完成，不代表可发布新 URL**  
> 英文名称：*EmbeddingGemma 2 for local PDF/DOCX retrieval: a bounded, reproducible Mac LiteRT-LM pilot*

## 结论

Google EmbeddingGemma 2 的 **270M 文本量化 LiteRT-LM 模型**已在 Apple Silicon Mac **CPU 四线程**中成功执行：从已发布的真实中英文技术文章构造 8 份 PDF + 8 份 DOCX，经独立文件解析后生成 **278 个文本块**、完成 32 条中英文问题的文档级检索。并行评估 SQLite FTS5 两种分词索引、EmbeddingGemma 2 的 768/512/256/128 维归一化向量以及 RRF 混合排序。

**用户决策**：在这个人为挑选的小型主题库里，纯 Embedding 256/768 维的 Recall@5 和 MRR 达到同组最高，FTS5+RRF 没有提供额外提升；128 维仍保留 Hit@5，但 MRR 低于 256/768。**不能据此认定 EmbeddingGemma 2 在所有本地知识库、所有中文文档或 RecalAI 上超过现有方案。**

## 一、模型、运行时和资料来源

- 官方模型：Google [EmbeddingGemma 2 model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)；[开发者指南](https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/)（2026-10-06）。
- 本机运行模型：`litert-community/embeddinggemma-2-text-270m-litert-lm`、`embeddinggemma-2-text-270m.litertlm`，文件 SHA256 `2d079ee2f6f066b1f368e8d7c819f55214eaef1d0513b312321901f30ab286fb`。
- 实际运行：macOS/Darwin arm64、Python 3.12.13、LiteRT-LM 0.18.0 CPU（4 线程）。不是 740M 多模态推理、不是 PyTorch FP32/BF16、不是苹果手机芯片实测。
- 16 个原始来源：XBSTACK 已发布的 8 个技术主题，各含 1 篇中文、1 篇英文，涉及 MCP Tool Result 分页、n8n 失败处理、LangGraph 审批/检查点、Google ADK 会话删除、Agent 上下文管理、OpenAI Responses 流式中断、Agent 工具授权。原始 Markdown 的路径及 SHA256 均记录在 JSON 证据文件中。
- PDF/DOCX **不是第三方提供的原生资料**。实验将上述真实公开文章完整清洗后转换为文档文件，然后重新读取。此设计能验证文档**生成格式→解析→文本分块→向量编码→检索**链路，但**不能**证明扫描 PDF/OCR、表格、图片、复杂 Word 排版或自然资料检索能力。
- 已剔除 Markdown frontmatter、围栏代码块与图片 Markdown，故**不评估代码块精确检索**；文本保留完整正文，而不是上一轮实验的前 1800 字截断。

## 二、实验设计与可复现性

每份文件由 `pypdf` 或 `python-docx` 读取，提取后规范化空白，按 **850 字符 + 120 字符重叠** 分块，共 278 块；检索先对块排序，再去重得到文档级排名。问题包含 16 条原有基础问句，以及 16 条**在第二次推理前写定**的更复杂、较接近日常求助表达的改写，总计 32 条；中英各占一半。每题有两个相关文档（同主题中/英文章）；跨语言的另一版本也单独评分。

Baseline 包含：
- FTS5 `unicode61`：逐查询词 OR，BM25 排序；中文分词能力有限。
- FTS5 `trigram`：对连续中文字符切三元组后 OR，BM25 排序；是更强的简易中文检索参照，但并非专门训练的中文 BM25。
- Embedding：使用 LiteRT 要求的非对称查询前缀 `task: search query | text: ` 与文档前缀 `task: search result | text: `，得到 768d，随后对 512/256/128d **截取后再次 L2 归一化**，同一批原始嵌入只计算一次，不能把截断后检索的速度变化等同于模型推理节约。
- RRF：对文档级 FTS 与 Embedding 排名进行 `k=60` 的等权融合，无训练、没有针对本数据调参。

**指标解释**：Hit@5 指前五个文档中至少有一个同主题文档，Recall@5 指两种语言版本都计入相关集后的召回比例；MRR 指首个相关文档倒数排名。没有对被检索出的具体答案片段进行人工真值标注，故不是 Evidence Precision 或 RAG 端到端准确率。

## 三、第二轮 32 问实测结果（本机原始数据）

| 文档级检索策略 | Hit@1 | Hit@5 | Recall@5 | MRR |
| --- | ---: | ---: | ---: | ---: |
| SQLite FTS5 / unicode61 | 0.6250 | 0.8750 | 0.7812 | 0.7396 |
| SQLite FTS5 / trigram | 0.6562 | 1.0000 | 0.7812 | 0.7755 |
| EmbeddingGemma 2 / 768d | 0.9375 | 1.0000 | 1.0000 | 0.9688 |
| EmbeddingGemma 2 / 512d | 0.9375 | 1.0000 | 1.0000 | 0.9688 |
| EmbeddingGemma 2 / 256d | 0.9375 | 1.0000 | 1.0000 | 0.9688 |
| EmbeddingGemma 2 / 128d | 0.8750 | 1.0000 | 0.9844 | 0.9323 |
| RRF（unicode61 + 768d） | 0.9375 | 1.0000 | 0.9844 | 0.9688 |
| RRF（unicode61 + 256d） | 0.9062 | 1.0000 | 1.0000 | 0.9531 |
| RRF（trigram + 768d） | 0.8750 | 1.0000 | 0.9062 | 0.9375 |

**特别说明**：原有 16 条基础问题在同一数据集更容易，768/256 维 MRR 都为 1.0；纳入复杂问题后下降到 0.9688，属于同一小样本自身的难度变化，不能拿两轮比较描述模型版本改进。

### 跨语言限定检索

将**另一语言的对应文章**作为唯一正确答案（不允许本语言同主题答案占位）时：

| 策略 | 跨语言 Hit@5 | 跨语言 MRR |
| --- | ---: | ---: |
| FTS5 unicode61 | 0.6875 | 0.3087 |
| FTS5 trigram | 0.5625 | 0.2512 |
| Embedding 768d | 1.0000 | 0.5000 |
| Embedding 256d | 1.0000 | 0.5130 |
| Embedding 128d | 0.9688 | 0.5130 |

第一名通常是**同语言的同主题版本**，所以跨语言 Hit@1 不佳并不意味着语义跨语言完全失效；它反映了双语平行文档竞争名次的设置。不同模型或数据集的结果不能直接横比。

## 四、时间和存储成本

- 模型初始化：**286.37ms（仅这轮观测的一次加载）**。
- 278 块文本向量化：总共 **53.99 秒**；平均每块 **194.22ms**。
- 单条查询向量化：32 问平均 **79.08ms**；按本脚本采样计算的 p95 **82.47ms**。不含完整 UI/检索服务、FTS 查询、数据库 IO 和 Reranker 耗时，也不代表连续吞吐或不同设备上稳定的 SLA。
- 278 个向量，仅计算 float32 原始数据、不含索引/SQLite/文档/元数据：768d=854,016B（约 0.814MiB）；512d=569,344B；256d=284,672B（约 0.271MiB）；128d=142,336B（约 0.136MiB）。
- 256d 的向量体积理论上比 768d 减少 **66.7%**，是浮点数组大小的算术关系，**不是模型下载大小或实际 App 峰值内存节省**。
- LiteRT 文本模型文件大小约 **164.6MB**（实际缓存量化文件，详见 10/9 模型文件证据）；向量维度缩小不意味着模型权重或推理显著缩小。

## 五、对本地知识库产品的启示

原有产品流程仍推荐：`保存原件 → PDF/Word/图片 OCR/解析 → 文本规范化 → Chunk → FTS 立即可搜 → 后台 Embedding → Query 双路召回 → RRF/重排 → Evidence 片段引用 → 本地或云端生成`。

在产品真实用户数据上，**是否选择 EmbeddingGemma 2 270M + 256d** 应依赖以下验收，而不能直接依据本 Pilot 切换生产索引：

1. 用实际扫描 PDF、复杂 Word/PPT、图片与网页，逐类统计导入成功率、文本保真、OCR 噪声与去水印后召回；
2. 新增**同主题易混、非标题同义问句、无答案负样本**和真实用户匿名问题；人工标注篇章证据位置，记录 passage-level Recall@k、nDCG、MRR、无答案拒答；
3. 至少以当前线上 Embedding 模型（若存在）为基线，公平对比中文分词增强的 FTS、Embedding 和 Reranker，测量迁移/索引重建成本；本次没有任何“替换当前 RecalAI 模型必胜”的证据；
4. 在**真实 iPhone 13 / 更高配机型**测量模型冷/热启动、重复批处理、峰值内存、发热、电池、后台任务被系统杀掉、模型互斥调度及暂停恢复；
5. 验证 768/256 不同维度索引**不可混用**，每条索引保存模型文件哈希、量化版本、维度、归一化策略，并确保回滚时原索引仍可用；
6. 在真实 RAG 链路验证“找到正确 Chunk”和“最终回答引用正确”的差异，避免把文档级 Hit@5 当答案准确率；
7. 用完整事件统计引入不同 Embedding 后对 FTS 即时可搜的影响，确保低端机不因加载模型而阻断导入/搜索。

## 六、反面证据：模型表现依赖问题集

公开独立的 [strata→signal 2026-10-09 测试](https://research.strata2signal.com/embeddinggemma-2-on-release-day/index.html) 使用其自身更大的英文历史资料库和 68 条事实问题，报告 EmbeddingGemma 2 45/68、nomic-embed-text 44/68、关键词检索 58/68（原作者指标为 Recall@8）。这是**第三方结果**而非 XBSTACK 实测，语料和指标均不同，不宜合并为排行或推断相对性能。它提醒我们：本实验从少量技术主题和人工查询中得到的高分，不能外推至精确实体/时间/数字任务。

## 七、复现命令

```bash
# 在 /Users/beijingchaoyang/MyWeb/blog 下
uv pip install --python research/embeddinggemma2/.venv-litert/bin/python \
  -r research/embeddinggemma2/requirements-document-pilot.txt

# 需已在缓存中有对应 .litertlm 权重；默认不下载，且不上传私有文件
research/embeddinggemma2/.venv-litert/bin/python \
  research/embeddinggemma2/document_format_chunk_pilot.py

research/embeddinggemma2/.venv-litert/bin/python -m unittest \
  discover -s research/embeddinggemma2/tests -v
```

证据：`evidence/mac-litert-converted-pdf-docx-chunks-2026-10-10.json` 保存来源文件哈希、模型哈希、文档数量、每题完整文档级排名、32 问各项评价、跨语言指标、耗时与维度存储算式。临时生成的 PDF/DOCX 会自动清理，报告**不含用户私人资料**。

## English executive summary

On October 10, 2026, XBSTACK ran **real quantized EmbeddingGemma 2 text-only 270M inference** with LiteRT-LM on Apple Silicon macOS CPU (four threads). Sixteen published bilingual technical articles were converted to eight PDFs and eight DOCX files, parsed back into text and divided into 278 overlapping chunks. Two pre-authored question groups contained 32 English and Chinese queries in total.

The 768d and 256d embedding runs both achieved document-level **Hit@5=1.0000, Recall@5=1.0000, MRR=0.9688** on this restricted corpus. A unicode61 FTS5 baseline achieved **Hit@5=0.8750, Recall@5=0.7812, MRR=0.7396**; equal-weight RRF did not outperform embedding-only MRR. Indexing 278 chunks took approximately **54 seconds**, and query vector encoding averaged **79.08ms** on that Mac CPU run.

**Limitations are substantial**: these are converted published articles, not naturally sourced PDF/DOCX files; the queries and labels are author-created; metrics concern the correct parent document, not verified answer-bearing passages. No independent holdout, OCR, vision-PDF understanding, Reranker, RecalAI integration, physical iPhone 13, battery or sustained-latency measurement was conducted. The result is a reproducible **engineering pilot, not a production benchmark**. Future on-device rollout must be contingent on real-document ingestion quality, human-labelled evidence retrieval, current-system comparisons, and physical-device performance.

## 内容发布门禁

这份报告可作为**技术实测证据与文章初稿**，但不自动等于 `NEW_ARTICLE_ALLOWED`。正式新 URL 仍需独立验证中英文搜索需求、SERP 竞争缺口、站内库存重复风险和现行新文发布门禁，且正式文章的封面/文中配图按 XBSTACK 规则采用 GPT 生成。现阶段没有进行网站部署、URL 推送或站外正式发布。
