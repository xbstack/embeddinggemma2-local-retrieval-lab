---
title: 'Context Engineering 是什么？AI Agent 如何用 Retrieval、Tool Search、Memory 降低上下文成本'
description: 'Context Engineering 不只是 Prompt Engineering。本文结合 Microsoft、Anthropic、Google 官方资料与 XBSTACK 本地实测，解释 Retrieval、Tool Search、MCP、Memory、Compaction 如何减少无效上下文与 AI Agent Token 成本。'
seoTitle: 'Context Engineering：AI Agent 上下文与 Token 成本'
seoDescription: 'Context Engineering 是什么？解析 Prompt Engineering 区别、RAG/Retrieval、Tool Search、MCP、Skills、Memory、Compaction、上下文成本与 Agent 优化。'
primaryKeyword: 'Context Engineering'
queries:
  - 'Context Engineering 是什么？'
  - 'Context Engineering 和 Prompt Engineering 有什么区别？'
  - 'AI Agent 上下文怎么优化？'
  - '怎么降低 AI Agent Token 成本？'
  - 'Context Engineering 和 RAG 有什么区别？'
  - 'Tool Search 为什么能降低 Agent 上下文成本？'
  - 'Memory、Skills、MCP 在 Context Engineering 里是什么关系？'
category: ai
section: agent
contentType: technical-guide
subcategory: context-engineering
series: ai-agent-production
image: '../../assets/covers/standardized/01-context-engineering-cover-8f89d46c-1200x630.webp'
imageAlt: '上下文工程：系统指令、用户任务、检索、记忆、工具、状态与压缩历史汇入 AI 智能体，并输出准确回答、完成任务和更低上下文成本'
tags:
  - Context Engineering
  - Prompt Engineering
  - AI Agent
  - RAG
  - Retrieval
  - Tool Search
  - MCP
  - Agent Memory
  - Agent Skills
  - Context Window
  - Token Cost
  - Compaction
  - Sub-agent
  - AIGC
keywords: 'Context Engineering, context engineering AI agent, Prompt Engineering, prompt engineering vs context engineering, AI Agent context, Agent context optimization, context window, LLM context, token cost, AI Agent cost, context caching, RAG, Retrieval Augmented Generation, retrieval, semantic reranking, Tool Search, dynamic tool loading, MCP, Model Context Protocol, Agent Memory, session memory, user memory, procedural memory, Agent Skills, instructions, message history, compaction, structured note taking, sub-agent, just in time retrieval, context rot, attention budget, context pipeline, generative AI, AIGC, AI Agent 工程, 上下文工程, Token 成本优化'
geoSummary: 'Context Engineering 指在每次模型推理前动态决定哪些高价值信息进入有限上下文，而不仅是优化 Prompt 文字。Anthropic 将其定义为对 system instructions、tools/MCP、external data、message history 等完整上下文状态的持续策划；Google 将其描述为结构化的数据与环境管线；Microsoft 2026-09-02 将 Knowledge Retrieval、Tool Search、Skills 和 Memory 放在企业 Agent 成本优化框架中。Microsoft 的文中数字仍属于其官方内部/产品评估，不是 XBSTACK 实测。XBSTACK 于 2026-09-05 额外完成本地 context-assembly audit：在 3 个真实项目任务中，聚焦上下文比 20,397-token 全量包减少 91.93%–94.29%，预设关键证据保持 3/3；该结果只证明上下文装配规模与指定证据保留，不代表模型准确率或真实账单同比下降。'
tldr:
  - 'Prompt Engineering 主要优化“怎么写指令”；Context Engineering 管理“模型这一轮到底看到什么”，包括 Instructions、Tools、MCP、Retrieval、Memory、History 和任务状态。'
  - '更大的 Context Window 不会自动解决 Agent 问题。Anthropic 强调 context 是有限 attention budget，信息越多并不等于结果越好。'
  - '生产 Agent 的高成本往往来自每一轮重复携带历史、全量工具定义和低价值检索结果；优化目标应该是完成一个结果的总成本，而不是只比较百万 Token 单价。'
  - 'Tool Search、just-in-time retrieval、Memory、Skills、Compaction 与 Sub-agent 是不同手段：核心目标都是让当前模型只看到足够且高信号的信息。'
  - 'XBSTACK 已完成本地 context-assembly audit：3 个真实项目任务的聚焦上下文从 20,397 tokens 降到 1,165–1,647 tokens，预设关键证据保持 3/3；这不是模型成功率或真实账单测试，后续仍需补模型层重试、Tool Call、延迟与任务成本。'
entities:
  - Context Engineering
  - Microsoft Foundry
  - Anthropic
  - Google Cloud
  - Model Context Protocol
  - RAG
  - Agent Memory
citations:
  - https://azure.microsoft.com/en-us/blog/the-economics-of-agent-optimization-context-engineering-for-enterprise-ai-agents/
  - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - https://cloud.google.com/discover/ai-context-engineering
demandEvidence:
  searchIntent: 'AI Agent 从短 Prompt 进入长任务后，开发者开始搜索 context engineering、prompt engineering 区别、RAG、Tool Search、MCP、Memory、context window 与 Token 成本优化。'
  signalType: validated-market-demand
  observedAt: '2026-09-05'
  inventoryCheckedAt: '2026-09-05'
  primarySources:
    - https://azure.microsoft.com/en-us/blog/the-economics-of-agent-optimization-context-engineering-for-enterprise-ai-agents/
    - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
    - https://cloud.google.com/discover/ai-context-engineering
  independentSources:
    - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
    - https://cloud.google.com/discover/ai-context-engineering
  inventoryReferences:
    - '/ai/ai-agent-rag-integration/'
    - '/ai/agent-memory-system/'
    - '/ai/mcp-protocol-guide/'
    - '/ai/ai-agent-production-governance/'
  proof: real-project-test
  cluster: other-validated
  score: 90
  distributionChannels:
    - zhihu
    - juejin
    - devto
    - hashnode
topicGovernance:
  status: case-study
  intent: '回答 Context Engineering 与 Prompt Engineering、RAG、MCP、Memory 的区别，以及生产 AI Agent 如何通过上下文筛选、Tool Search、Compaction 与检索控制无效 Token 和上下文成本。'
  differentiation: '站内已有 RAG、MCP、Agent Memory 与生产治理文章，但没有页面系统回答“模型这一轮应该看到什么”这一独立搜索意图。本文结合 Microsoft、Anthropic、Google 一手资料与 XBSTACK 2026-09-05 本地 context-assembly audit，提供 20,397-token 全量包与 1,165–1,647-token 聚焦包的可复现实验边界，不重复现有组件教程。'
  inventoryCheckedAt: '2026-09-05'
  inventoryReferences:
    - '/ai/ai-agent-rag-integration/'
    - '/ai/agent-memory-system/'
    - '/ai/mcp-protocol-guide/'
    - '/ai/ai-agent-production-governance/'

draft: false
hideStructuredBlocks: true
evidenceStatus: complete
note: '草稿创建于 2026-09-04，2026-09-05 已重新核对 Microsoft、Anthropic、Google 一手资料，完成 XBSTACK 本地 context-assembly audit，并补齐专用 GPT 封面/正文配图且通过 article:prepublish-gate。本文当前声明的证据边界已完成：本地实验只验证真实项目上下文从全量包收敛到聚焦包后的 token 规模与预设证据保留，不调用外部模型、不代表模型准确率或真实账单同比下降。模型层成功率、重试、Tool Call、延迟和任务成本属于后续增量实测，不影响本文当前结论。'
clusterHub: '/ai/'
schemaJsonLd:
  "@context": "https://schema.org"
  "@graph":
    - "@type": "TechArticle"
      "@id": "https://www.xbstack.com/ai/context-engineering-agent-cost-memory-tools/#article"
      headline: "Context Engineering 是什么？AI Agent 如何用 Retrieval、Tool Search、Memory 降低上下文成本"
      description: "解释 Context Engineering 与 Prompt Engineering 的区别，以及 Retrieval、Tool Search、MCP、Skills、Memory、History 与 Compaction 如何管理 Agent 上下文。"
      mainEntityOfPage:
        "@type": "WebPage"
        "@id": "https://www.xbstack.com/ai/context-engineering-agent-cost-memory-tools/"
      author:
        "@type": "Person"
        name: "小白"
        url: "https://www.xbstack.com/about"
      publisher:
        "@type": "Organization"
        name: "XBSTACK"
        url: "https://www.xbstack.com"
      dateCreated: "2026-09-04"
      inLanguage: "zh-CN"
      articleSection: "AI Agent Engineering"
      isAccessibleForFree: true
      keywords:
        - "Context Engineering"
        - "Prompt Engineering"
        - "RAG"
        - "Tool Search"
        - "MCP"
        - "Agent Memory"
        - "Token Cost"
      citation:
        - "https://azure.microsoft.com/en-us/blog/the-economics-of-agent-optimization-context-engineering-for-enterprise-ai-agents/"
        - "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents"
        - "https://cloud.google.com/discover/ai-context-engineering"
    - "@type": "FAQPage"
      "@id": "https://www.xbstack.com/ai/context-engineering-agent-cost-memory-tools/#faq"
      mainEntity:
        - "@type": "Question"
          name: "Context Engineering 是什么？"
          acceptedAnswer:
            "@type": "Answer"
            text: "Context Engineering 是持续设计和筛选每一轮 LLM 推理可见的信息，包括系统指令、工具、MCP、检索数据、Memory、历史和任务状态，以有限高信号上下文支持正确行为。"
        - "@type": "Question"
          name: "Context Engineering 和 Prompt Engineering 有什么区别？"
          acceptedAnswer:
            "@type": "Answer"
            text: "Prompt Engineering 主要优化指令文本的写法和结构；Context Engineering 管理完整推理环境，Prompt 只是其中一部分，此外还包含 Tools、Retrieval、Memory、History 等动态信息。"
        - "@type": "Question"
          name: "Context Engineering 能降低 Agent 成本吗？"
          acceptedAnswer:
            "@type": "Answer"
            text: "可以通过减少重复历史、全量工具定义和低价值检索内容降低输入规模，但实际节省取决于工作流。厂商内部 benchmark 不能直接当作你的成本结果，应按完成任务的总请求、Token、工具调用和重试实测。"
    - "@type": "BreadcrumbList"
      "@id": "https://www.xbstack.com/ai/context-engineering-agent-cost-memory-tools/#breadcrumb"
      itemListElement:
        - "@type": "ListItem"
          position: 1
          name: "XBSTACK"
          item: "https://www.xbstack.com/"
        - "@type": "ListItem"
          position: 2
          name: "AI"
          item: "https://www.xbstack.com/ai/"
        - "@type": "ListItem"
          position: 3
          name: "AI Agent"
          item: "https://www.xbstack.com/ai/agent/"
        - "@type": "ListItem"
          position: 4
          name: "Context Engineering"
          item: "https://www.xbstack.com/ai/context-engineering-agent-cost-memory-tools/"

createdAt: '2026-09-04'
lang: 'zh-CN'
route: '/ai/context-engineering-agent-cost-memory-tools/'
canonical: 'https://www.xbstack.com/ai/context-engineering-agent-cost-memory-tools/'
hub: 'agent'
translationKey: 'ai:context-engineering-agent-cost-memory-tools'
translations:
  zh-CN: '/ai/context-engineering-agent-cost-memory-tools/'
  en: '/en/ai/context-engineering-agent-cost-memory-tools/'
translationStatus: 'published'
indexing: 'index'
---

**直接答案：Context Engineering 不是把 Prompt Engineering 换一个更时髦的名字。Prompt Engineering 解决“指令怎么写”，Context Engineering 解决“模型这一轮到底应该看到什么”。对一个 AI Agent 来说，真正进入上下文的通常同时有 system instructions、工具定义、MCP 描述、检索文档、Memory、消息历史、任务状态和工具返回；这些内容每轮都可能变化，也都会消耗 Token 和模型的注意力。**

这个方向现在值得单独写，是因为几家大厂已经从不同角度收敛到同一个问题。Anthropic 把 context 看成有限的 attention budget；Google 把 context engineering 描述为围绕 Agent 建立结构化数据和环境管线；Microsoft 2026 年 9 月 2 日则直接把 Knowledge Retrieval、Tool Search、Skills 和 Memory 放进生产 Agent 的成本优化体系。

本文仍不是“模型成本实测”。Microsoft 的百分比继续按厂商内部/产品评估引用；XBSTACK 新增的是本地 context-assembly audit，只验证真实项目上下文从全量包收敛到聚焦包后的 token 规模与预设证据保留。它已经能回答“是否存在大量可避免的上下文装配开销”，但还不能回答“模型成功率是否提高”或“最终账单到底下降多少”。

## Context Engineering 和 Prompt Engineering 到底差在哪？

Anthropic 给出的区分非常实用：Prompt Engineering 主要研究如何编写、组织模型指令；Context Engineering 则是在每一次模型推理前，策划和维护最合适的一组 Token，包括 Prompt 之外所有可能进入模型视野的信息。

一个 Agent 的真实上下文可能是：

```text
System instructions
+ User task
+ Few-shot examples
+ Tool schemas
+ MCP server/tool descriptions
+ Retrieved documents
+ User/session memory
+ Project notes
+ Prior messages
+ Previous tool results
+ Current checkpoint/state
```

如果只优化第一行和第二行，后面的 80% 信息仍然可能又长、又旧、又互相冲突。

Anthropic 因此把 Context Engineering 称为 Prompt Engineering 的自然延伸。随着 Agent 进入多轮工具循环和长时间任务，“把一句 Prompt 写漂亮”不再足以控制模型。官方原文：<https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

![提示词工程主要优化指令本身，而上下文工程决定系统指令、用户任务、检索、记忆、工具、状态和历史中哪些内容进入模型](../../assets/uploads/context-engineering-agent-cost-memory-tools-zh/02-prompt-vs-context-engineering.webp)

## 为什么 Context Window 越大，Context Engineering 反而越重要？

直觉上，模型从 128K 走到 1M、2M 上下文后，好像可以直接把所有资料塞进去。但这会混淆“容量”和“有效注意力”。

Anthropic 提到 context rot：随着上下文变长，模型对其中信息的精确提取和长距离关系理解可能下降。它把 context 描述为有限 attention budget，建议寻找“能最大化目标行为概率的最小高信号 Token 集”。

Google Cloud 的官方解释也强调 Context Engineering 是一个数据/环境系统，而不是把大 Context Window 当作仓库。即使模型可以读取很长输入，生产系统仍然要决定稳定 instructions、半持久 Memory 和动态外部数据如何组合。

这一点和今天的 [GPT-6 Astra 105 万上下文](/ai/gpt-6-astra-api-guide/) 很契合：窗口更大确实扩大了任务空间，但它不会自动判断哪些日志、工具和历史已经失效，也不会自动替你控制每轮重复输入的成本。

## 为什么 Agent 的成本不能只看模型单价？

Agent 是模型调用循环，不是一次 completion。它计划、调用 Tool、读取结果、再推理；完成一个结果可能包含很多请求。

因此真正的成本近似可以写成：

```text
Outcome cost
= Σ(每轮 input + cached input/write + output + tool fee)
+ retry cost
+ failed-run cost
+ human correction cost
```

上下文膨胀的问题是：历史越长、工具越多、检索结果越杂，**每一轮**都可能重复支付这些输入。

Microsoft 在 9 月 2 日的官方文章里直接提出，很多生产 Agent 在原型阶段就固定了“模型每轮看什么”，以后很少重新优化，而这往往既影响成本也影响回答质量。因此 Context Engineering 的目标不是“尽量少 Token”，而是**保留完成任务需要的高价值 Token，删除当前轮不需要的低价值 Token。**

Microsoft 官方：<https://azure.microsoft.com/en-us/blog/the-economics-of-agent-optimization-context-engineering-for-enterprise-ai-agents/>

## 第一层：Instructions 应该足够明确，但不要写成程序

Anthropic 对 system prompt 的建议很克制：不要把所有业务逻辑硬编码成几百条 if/else，也不要只写“你是一个有帮助的 Agent”这种空指令。

更好的状态是“正确高度”：

- 明确角色与目标；
- 明确边界和不可做事项；
- 明确工具使用原则；
- 给少量代表性例子；
- 结果格式需要时明确；
- 把动态事实留给 Retrieval/Tools，而不是复制进长期 Prompt。

指令越稳定，越适合放长期层；事实越动态，越应该运行时获取。

## 第二层：Retrieval 不是“搜到越多文档越好”

RAG 解决的是从大量外部知识里拿到当前任务需要的证据。Context Engineering 关心的是下一步：**拿哪些、多少、以什么顺序、带什么 metadata 放进 context。**

一个生产检索链通常至少要考虑：

```text
Query rewrite / decomposition
        ↓
Candidate retrieval
        ↓
Filter / ACL
        ↓
Semantic / hybrid rerank
        ↓
Deduplicate
        ↓
Token budget
        ↓
Context packing + citations
```

Microsoft 在其 Foundry 文章里公布了 BrowseComp-Plus 上的内部结果：通过更好的 evidence retrieval/reranking，报告最高 **54% evidence recall 提升和 34% retrieval token cost 降低**。这组数字只能写成 Microsoft 的官方内部评估，不能改写成“Context Engineering 能给你省 34%”。真实知识库、文档质量和查询分布都会改变结果。

站内 [AI Agent + RAG 集成](/ai/ai-agent-rag-integration/) 可以作为 Retrieval 实现的下一步阅读。

## 第三层：Tool Search 为什么可能比“把所有工具都告诉模型”更合理？

当 Agent 只有 5 个 Tool 时，全量 tool schema 很简单；当它连接 MCP、SaaS、数据库、浏览器和内部 API 后，可能有几十甚至几百个 Tool。

如果每轮都把全部定义放进 context，会同时产生两种成本：

1. **Token 成本**：工具描述本身可以非常长；
2. **决策噪声**：功能相近的 Tool 越多，模型越难选。

一种 Context Engineering 方案是 Tool Search：模型先看到一个小型工具索引/发现能力，需要时再加载相关工具详细 schema。Microsoft 报告其大工具库内部 benchmark 中平均 **input-token reduction 约 97%**。仍然要强调，这是微软特定工作负载和产品能力的内部结果，而不是一般规律。

MCP 同样需要这个思路。MCP 让 Tool/Data 接入更标准，但“接上 100 个 MCP Tools”不等于“每轮应该把 100 个工具都暴露给模型”。协议层与 context selection 是两个不同问题。可参考 [MCP 协议指南](/ai/mcp-protocol-guide/)。

## 第四层：Memory 不应该等于“把聊天历史全部带回来”

长期 Agent 需要 Memory，但 Memory 的价值是把**跨会话仍然有用的信息**带入当前轮，而不是无限累加消息。

Microsoft 在文章里把 Memory 分成 session、user、procedural 等类型；Anthropic 更强调 structured note-taking 与动态检索。无论具体实现如何，一个好 Memory 层都需要回答：

- 这条信息为什么值得长期保存？
- 来源是什么？
- 什么时候写入？
- 是否过期？
- 当前任务真的需要吗？
- 和新的事实冲突怎么办？

Microsoft 文中还给出 Memory 相关内部评估约 **5% benchmark improvement**，同样不能直接推广到任意 Agent。

如果你在做具体记忆系统，可以继续看 [AI Agent Memory System](/ai/agent-memory-system/)；如果关心 Coding Agent 原始 trace 检索，Funes Agent Memory 是另一个值得继续验证的方向，但本站相关实测仍处于草稿阶段，暂不提供公开链接。

## 第五层：Skills 把稳定“方法”从每次 Prompt 里抽出来

Skills 和 Memory 容易混淆。

Memory 主要回答“过去发生了什么、用户/项目有什么长期状态”；Skill 更接近“遇到某类任务应该如何做”。例如一套 PDF 财报校验流程、一套部署验收步骤、一套代码 review 方法，都属于可复用 procedure。

把稳定 procedure 做成 Skill 的好处，是不需要每次在 user prompt 里重复粘贴完整 SOP；Agent 可以在任务需要时加载。但 Skills 同样需要版本和适用范围，否则旧流程会像旧 Memory 一样污染新任务。

## 第六层：长任务里的 History 怎么处理？

无限保留全部 message history 最简单，也最容易膨胀。Anthropic 对长时间 Agent 给出的几个常见策略是：

### Compaction

把旧消息压成高价值摘要，在活动 context 里保留当前计划、关键状态、失败信息和后续步骤。

### Structured note-taking

让 Agent 主动把长期重要状态写到 context 之外，例如文件、Memory 或 durable notes，需要时再取回。

### Just-in-time retrieval

上下文只保留轻量引用，例如路径、URL、query ID；真正需要时再通过工具加载数据，而不是一开始预加载所有东西。

### Sub-agent

把子问题隔离到独立 context，主 Agent 最后只接收压缩后的必要结果，避免所有调查过程污染主上下文。

这四种手段解决的都是同一件事：**不要让每一轮模型请求都背着过去所有工作。**

## Context Engineering 和 RAG、MCP、Memory 到底是什么关系？

可以把它们看成层级关系：

```text
Context Engineering
├── Instructions / Examples
├── Retrieval / RAG
├── Tool selection / Tool Search
│   └── MCP can be one tool/data connection layer
├── Skills / procedures
├── Memory
├── History / Compaction / Notes
├── Runtime state
└── Context caching / packing / budget
```

RAG、MCP、Memory 都不是 Context Engineering 的同义词。它们是供 Context Engineering 调用的数据与能力组件。

因此一个系统“用了 RAG”仍然可能 context 很差：检索出 30 个重复 chunk 全部塞进去；“用了 MCP”也可能很差：每轮暴露 80 个重叠工具；“用了 Memory”也可能很差：把过期信息一直注入新任务。

![上下文组装流程：从任务开始，经过检索、过滤、排序、工具加载和历史压缩，只把相关信息交给模型并进入行动反馈循环](../../assets/uploads/context-engineering-agent-cost-memory-tools-zh/03-context-assembly-selective-retrieval.webp)

## XBSTACK 本地 Context Audit：先测“进入上下文的东西”，再谈模型成本

2026 年 9 月 5 日，我先做了一轮**不调用外部模型的本地 Context Assembly Audit**。目的不是证明 Context Engineering 一定能让模型更准，而是先回答一个更基础的问题：同一个真实工程任务，如果把整包项目上下文全部塞进去，和只检索当前任务所需的规则、脚本与证据相比，进入模型窗口的内容规模到底差多少？

这次使用的都是真实 XBSTACK 项目资料：`AGENTS.md`、搜索问题运营规则、`package.json` 发布/增长脚本、当天 `daily-operation-evidence`，以及刚完成的 LangGraph 首个 checkpoint 崩溃实验结果。Token 只用 `tiktoken o200k_base` 做本地统一估算，不代表任何厂商实际账单。

| 任务 | 全量上下文 | 聚焦上下文 | 减少比例 | 预设关键证据 |
| --- | ---: | ---: | ---: | ---: |
| 每日运营门禁 | 20,397 | 1,647 | 91.93% | 3/3 |
| 文章发布门禁 | 20,397 | 1,541 | 92.44% | 3/3 |
| LangGraph 首个 checkpoint 恢复 | 20,397 | 1,165 | 94.29% | 3/3 |

![XBSTACK 本地 Context Audit：日常运营、发布门禁和 LangGraph 恢复任务的上下文从 20,397 tokens 收敛到 1,165–1,647 tokens，预设关键证据均保留 3/3](../../assets/uploads/context-engineering-agent-cost-memory-tools-zh/04-token-budget-context-audit.webp)

这里的“关键证据 3/3”是一个很克制的检查：例如每日运营任务必须仍然保留 `growth:daily-operation-gate`、`DAILY_OPERATION_PASS` 和候选数量门槛；LangGraph 恢复任务必须仍然拿到 `EmptyInputError`、`accepted` 与最终 `completed` 的证据。它只能证明**这组确定性检索没有把我事先定义的关键证据丢掉**，不能证明模型准确率提高 90%，更不能把 91.93%–94.29% 直接写成真实账单节省。

实验文件在 `experiments/context-engineering-context-audit/`，同一套规则可以重复运行。下一步真正需要继续测的是模型层：聚焦上下文后任务成功率、重试次数、Tool Call 数、延迟和最终任务成本是否仍然不差于全量上下文。

所以给现有 Agent 做 Context Audit 时，我仍然建议记录下面这些指标，而不是只看输入 Token：

| 指标 | 为什么看 |
| --- | --- |
| System / instruction tokens | 长期 Prompt 是否膨胀 |
| Tool-schema tokens | 是否每轮带全量 Tools |
| Retrieved tokens | RAG 是否过量 |
| Memory tokens | 长期状态是否真正相关 |
| History tokens | 多轮重复成本 |
| Cached tokens | 重复内容是否利用缓存 |
| Output tokens | 推理/回答规模 |
| Tool calls | 上下文变短是否导致更多探索 |
| Retry / failure | 不能为了省 Token 降低成功率 |
| Total outcome cost | 最终业务指标 |

最终比较仍然应该是两套方案：

**A：全量上下文** —— 现有 Prompt、所有历史、所有 Tool schemas、固定 top-k retrieval。  
**B：Context Engineering** —— 动态 Tool Search/过滤、just-in-time retrieval、Memory 筛选、compaction/notes、明确 token budget。

成功标准不是 B 的 input token 更少，而是**在任务质量不下降的前提下，完成结果的总成本、重试和时间更低**。

## 一个可落地的 Context Engineering 检查表

在模型调用之前，逐项问：

1. 这条 instruction 是否稳定且仍然需要？
2. 当前任务真正需要哪些 Tools？
3. Tool 描述有没有重叠？
4. 哪些事实必须实时 Retrieval，而不是写死在 Prompt？
5. 检索结果是否去重、rerank、受 ACL 约束？
6. 哪些 Memory 真的和当前任务相关？
7. Memory 是否有来源、版本和时效？
8. 旧 history 能否 compaction？
9. 哪些大数据可以只保留引用，需要时再读取？
10. 子任务是否值得用 Sub-agent 隔离 context？
11. 可重复上下文是否能 cache？
12. 失败时应该增加信息，还是换工具/策略？

这个清单比“把 context 控制在某个固定 Token 数”更实用，因为不同任务需要的信息密度完全不同。

## 安全：减少 Context 也不能破坏权限

Context Engineering 不只是成本工程。检索、Tool Search、Memory 都涉及数据可见性。

一个常见错误是为了方便 Agent 检索，把用户本来无权看到的文档放进统一向量库；另一个错误是 Tool Search 只按语义找工具，却忘了当前用户/Agent 是否有权限调用它。

因此 context pipeline 应该遵守：

- retrieval ACL 在召回前/后都可验证；
- Tool discovery 先做 permission filter；
- Memory 按用户、项目、租户隔离；
- 凭据不直接进入模型上下文；
- audit 能追踪每条外部信息为何被注入；
- high-impact write 仍走 approval。

Context 越动态，数据边界越应该显式。

## 最终判断：为什么这会成为 Agent 工程的基础能力？

Prompt Engineering 不会消失。好的 Instructions 仍然重要。但生产 Agent 一旦进入多轮、Tools、Memory、RAG、Computer Use 和长期任务，影响每轮结果的变量已经远超一段 Prompt。

Context Engineering 真正提供的是一个工程视角：把模型视为有有限注意力与按 Token 计费的执行核心，每一轮都应该给它**足够但不过量、当前且有权限、高信号且可追溯**的信息。

Microsoft 的最新成本文章、Anthropic 的 Agent 工程方法和 Google 的 Context Engineering 页面都指向这条主线，但具体产品和 benchmark 各自不同。不能因为三个厂商都谈 Context Engineering 就把它包装成一个统一标准。

**对 XBSTACK 来说，这篇未来发布最需要证明的不是“Context Engineering 很重要”，而是：同一个真实 Agent，在不降低成功率的前提下，通过更少重复历史、更少无关 Tool schema、更精准 Retrieval 和更合适 Memory，能不能用更少总输入完成同一个结果。**

## FAQ

### Context Engineering 是什么？

Context Engineering 是设计和动态筛选每一轮模型可见信息的工程实践，范围包括 Instructions、Tools/MCP、Retrieval、Memory、History、Runtime state 与缓存，不只是 Prompt 文本。

### Context Engineering 会取代 Prompt Engineering 吗？

不会。Prompt Engineering 是 Context Engineering 的一部分。明确 system instructions、示例和输出要求仍然重要，只是生产 Agent 还必须管理动态工具、数据、Memory 和历史。

### Context Engineering 和 RAG 有什么区别？

RAG 主要负责从外部知识检索证据；Context Engineering 还决定检索多少、怎样 rerank/去重、与哪些 Instructions、Tools、Memory、History 一起放进模型，以及总 token budget。

### Context Engineering 和 MCP 有什么关系？

MCP 是连接 Tools/Data 的协议层；Context Engineering 决定当前轮应该发现、加载和暴露哪些 MCP 能力。接入很多 MCP Server 不代表所有 Tool schemas 都应该每轮进入上下文。

### Context Engineering 一定能省 Token 吗？

通常有机会减少重复和无关输入，但不能预设固定节省比例。真实结果需要在同任务、同成功标准下比较总 input/output、工具调用、重试、耗时和成功率。Microsoft 的 34%、97% 等数字是其特定内部评估，不是通用保证。

## 官方资料

- [Microsoft Azure：The Economics of Agent Optimization — Context engineering](https://azure.microsoft.com/en-us/blog/the-economics-of-agent-optimization-context-engineering-for-enterprise-ai-agents/)
- [Anthropic：Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Google Cloud：What is AI context engineering?](https://cloud.google.com/discover/ai-context-engineering)

## 继续阅读

- [AI Agent + RAG：检索怎么接入生产工作流](/ai/ai-agent-rag-integration/)
- [AI Agent Memory System](/ai/agent-memory-system/)
- [MCP Protocol Guide](/ai/mcp-protocol-guide/)
- [AI Agent 生产化治理](/ai/ai-agent-production-governance/)
