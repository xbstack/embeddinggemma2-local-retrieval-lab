---
title: "Google ADK delete_session 为什么删不掉长期 Memory？2.8.0/2.9.0 实测"
description: "Google ADK 调用 delete_session() 后，为什么 add_session_to_memory() 写入的长期记忆仍能被 search_memory() 搜到？本文用 2.8.0 与 2.9.0 做离线最小复现，并说明删除边界和生产处理方式。"
seoTitle: "Google ADK delete_session 删不掉 Memory？2.8/2.9 实测"
seoDescription: "实测 Google ADK 2.8.0/2.9.0：delete_session() 会删除 Session，但不会级联删除已复制到 MemoryService 的长期记忆；BaseMemoryService 也没有通用 delete API。"
geoSummary: "XBSTACK 在 2026-09-15 用 google-adk 2.8.0 与 2.9.0 做了离线最小复现：先向 InMemorySessionService 写入带唯一 marker 的用户事件，再通过 InMemoryMemoryService.add_session_to_memory() 复制到长期 Memory。调用 delete_session() 后，Session 已不存在，但 search_memory() 仍可检索到相同 marker；同时 BaseMemoryService 在两个版本中都没有可调用的 delete 方法。该结果只覆盖 InMemorySessionService + InMemoryMemoryService，不证明 VertexAiMemoryBankService 等所有后端行为完全一致。"
category: ai
section: practice
contentType: troubleshooting
subcategory: google-adk
series: "Google ADK 生产问题排查"
seriesOrder: 2
hideStructuredBlocks: true
draft: false
image: "../../assets/uploads/google-adk-memory-delete/01-cover.webp"
imageAlt: "Google ADK delete_session 删除会话后长期 Memory 仍可搜索的 2.8.0 与 2.9.0 实测流程图"
tags:
  - Google ADK
  - MemoryService
  - SessionService
  - delete_session
  - add_session_to_memory
  - InMemoryMemoryService
  - Agent Memory
  - Data Deletion
  - Python
keywords: "Google ADK delete_session，Google ADK memory delete，Google ADK MemoryService 删除，Google ADK 删除长期记忆，Google ADK 删除会话后 Memory 还在，delete_session memory retained，delete_session does not delete memory，add_session_to_memory，search_memory，InMemoryMemoryService，BaseMemoryService delete，Google ADK 2.8.0，Google ADK 2.9.0，Agent memory data deletion，AI Agent 清空记忆，账号注销数据删除，长期记忆删除，MemoryService cleanup"
primaryKeyword: "Google ADK delete_session 删不掉 Memory"
targetHub: "AI Agent"
conversionTarget: "Google ADK 最小复现、Agent Memory 数据删除排障、AI Agent 生产治理"
evidenceStatus: complete
contentRole: support
tldr:
  - "google-adk 2.8.0 与 2.9.0 中，InMemorySessionService.delete_session() 会删除 Session，但不会级联删除此前复制到 InMemoryMemoryService 的长期 Memory。"
  - "同一个唯一 marker 在 delete_session() 前后都能被 search_memory() 检索到，而 get_session() 在删除后已返回不存在。"
  - "两个版本的 BaseMemoryService 都没有可调用的 delete 方法，因此应用不能把 delete_session() 当成完整的数据删除操作。"
  - "本文结论只覆盖 InMemorySessionService + InMemoryMemoryService；VertexAiMemoryBankService 等托管后端没有在本次离线实验中验证。"
queries:
  - "Google ADK delete_session 为什么删不掉 memory？"
  - "Google ADK 删除 session 后 memory 为什么还在？"
  - "Google ADK MemoryService 怎么删除长期记忆？"
  - "add_session_to_memory 后如何删除用户数据？"
  - "BaseMemoryService 为什么没有 delete_memory？"
  - "Google ADK 2.9 memory delete"
  - "Google ADK 删除会话后长期记忆为什么还在？"
  - "Google ADK 账号注销时怎么清理 MemoryService 数据？"
faqs:
  - question: "Google ADK 的 delete_session() 会删除长期 Memory 吗？"
    answer: "在本文对 google-adk 2.8.0 与 2.9.0 的 InMemorySessionService + InMemoryMemoryService 实测中不会。Session 删除后，先前通过 add_session_to_memory() 复制进去的 marker 仍可被 search_memory() 检索到。"
  - question: "这是不是说明 Google ADK 所有 Memory 后端都删不掉数据？"
    answer: "不能这样推导。本次只验证了内存实现和 BaseMemoryService 的公共 API 表面，没有调用 VertexAiMemoryBankService 或其他第三方后端。"
  - question: "为什么 delete_session() 不会自动清理 Memory？"
    answer: "Session 与长期 Memory 是独立的持久化表面。add_session_to_memory() 把会话内容复制到 MemoryService 后，两者不再是同一份数据；删除 Session 不等于撤销已经写入 Memory 的副本。"
  - question: "生产环境应该怎么处理用户删除请求？"
    answer: "把 Session、Memory、Artifacts 和其他持久化存储分别列入删除清单，对每个后端执行独立删除并做删除后验证。若当前 MemoryService 没有删除能力，需要使用底层存储提供的删除接口，或避免把无法后续删除的数据写入该后端。"
  - question: "升级到 google-adk 2.9.0 能解决吗？"
    answer: "本文对 2.8.0 和 2.9.0 都复现了相同行为，因此至少不能依赖升级到 2.9.0 来获得级联删除。未来版本需要重新运行版本矩阵确认。"
note: "本次测试在本地离线运行，不调用 Gemini、OpenAI 或 Vertex AI API。测试覆盖 google-adk 2.8.0 与 2.9.0、InMemorySessionService、InMemoryMemoryService；使用唯一 marker 验证删除前后搜索结果。未测试 VertexAiMemoryBankService，因此不能把结论扩展到所有托管 Memory 后端。"
entities:
  - Google ADK
  - BaseMemoryService
  - InMemoryMemoryService
  - InMemorySessionService
  - delete_session
  - add_session_to_memory
  - search_memory
citations:
  - https://github.com/google/adk-python/issues/6949
  - https://github.com/google/adk-python/issues/7110
  - https://github.com/google/adk-python
topicGovernance:
  status: case-study
  intent: "解决 Google ADK 中一个独立的数据删除问题：为什么 delete_session() 删除会话后，已经通过 add_session_to_memory() 复制的长期 Memory 仍然存在，以及生产删除流程应该如何拆分。"
  differentiation: "不重复站内 Google ADK state_delta/A2A resume 页面，也不做泛 Memory 教程；本文只承接 Session 删除与长期 Memory 删除边界。"
  inventoryCheckedAt: '2026-09-15'
  inventoryReferences:
    - '/ai/google-adk-state-delta-resume/'
    - '/ai/ai-agent-framework-comparison/'
    - '/ai/agent-memory-system/'
demandEvidence:
  searchIntent: "Google ADK 用户在删除 Session 或处理账号注销/数据删除时，发现此前通过 add_session_to_memory() 写入的长期 Memory 仍可被搜索，需要确认 2.8.0/2.9.0 是否受影响、为什么 delete_session() 不级联，以及生产环境该如何真正删除。"
  signalType: regression
  observedAt: '2026-09-15'
  inventoryCheckedAt: '2026-09-15'
  primarySources:
    - https://github.com/google/adk-python/issues/7110
    - https://github.com/google/adk-python/issues/6949
    - https://github.com/google/adk-python
  independentSources:
    - https://github.com/google/adk-docs/blob/main/docs/context/index.md
  inventoryReferences:
    - '/ai/google-adk-state-delta-resume/'
    - '/ai/ai-agent-framework-comparison/'
    - '/ai/agent-memory-system/'
  proof: reproduction
  cluster: other-validated
  score: 91
  distributionChannels:
    - zhihu
    - juejin
    - csdn
    - devto
clusterHub: '/ai/'
audience:
  - "使用 Google ADK MemoryService 保存跨 Session 长期记忆的 Python 开发者。"
  - "需要实现账号注销、用户数据删除或长期记忆清理的 Agent 产品团队。"
  - "正在区分 Session、Memory、Artifacts 等持久化边界的 AI Agent 平台工程师。"

createdAt: '2026-09-15'
lang: 'zh-CN'
route: '/ai/google-adk-delete-session-memory-retained/'
canonical: 'https://www.xbstack.com/ai/google-adk-delete-session-memory-retained/'
hub: 'agent'
translationKey: 'ai:google-adk-delete-session-memory-retained'
translations:
  zh-CN: '/ai/google-adk-delete-session-memory-retained/'
  en: '/en/ai/google-adk-delete-session-memory-retained/'
translationStatus: 'published'
indexing: 'index'
---
如果你在 Google ADK 里做用户数据删除，有一个很容易被误判的边界：`delete_session()` 删除的是 Session，不等于删除此前已经复制进 `MemoryService` 的长期记忆。我在本地分别用 `google-adk==2.8.0` 和 `2.9.0` 做了同一组离线实验，两版结果一致：Session 删除后已经取不到，但同一个唯一 marker 仍然能被 `search_memory()` 搜出来。

这不是“缓存没刷新”，也不是模型又把内容生成了一遍。复现过程中没有调用任何外部模型 API，Memory 里的内容就是删除 Session 之前通过 `add_session_to_memory()` 明确复制进去的那一份。

## 先给结论

本次测试覆盖：

- Python 3.11+
- `google-adk==2.8.0`
- `google-adk==2.9.0`
- `InMemorySessionService`
- `InMemoryMemoryService`
- 一个唯一 marker：`blue-orchid-260915`
- 全程离线，不调用 Gemini、OpenAI 或 Vertex AI

两版结果相同：

| 版本 | `delete_session()` 后 Session | 删除前 Memory 可搜索 | 删除后 Memory 可搜索 | `BaseMemoryService` delete 方法 |
|---|---|---:|---:|---:|
| 2.8.0 | 已删除 | 是 | **是** | 0 |
| 2.9.0 | 已删除 | 是 | **是** | 0 |

这意味着生产系统不能把下面这句代码理解成“这个用户在 ADK 里的数据已经删干净”：

```python
await session_service.delete_session(
    app_name=app_name,
    user_id=user_id,
    session_id=session_id,
)
```

它只证明 Session 层完成了删除。Memory、Artifacts、外部向量库、数据库副本或其他持久化表面，都必须单独处理和验证。

## 我是怎么复现的

复现脚本刻意只保留最小路径。

第一步，创建一个 Session，并写入一条包含唯一 marker 的用户事件：

```text
Remember this marker: blue-orchid-260915
```

第二步，通过：

```python
await memory_service.add_session_to_memory(session)
```

把这条 Session 内容复制到 `InMemoryMemoryService`。

第三步，用 `search_memory()` 搜索 marker，确认删除前能命中。随后调用 `delete_session()`，再通过 `get_session()` 确认 Session 已经不存在。

最后，再次调用 `search_memory()`。

2.8.0 与 2.9.0 的关键结果都是：

```json
{
  "session_exists_after_delete": false,
  "memory_found_before_delete": true,
  "memory_found_after_delete": true,
  "base_memory_delete_methods": []
}
```

完整最小复现已经放在 XBSTACK 的实验目录，版本矩阵分别保留了两版 JSON 日志。这里最重要的不是某个内部对象长什么样，而是三个断言同时成立：**Session 真删了、Memory 删除前存在、Memory 删除后仍存在。**

## 为什么会这样：Session 和 Memory 是两套生命周期

问题的关键在 `add_session_to_memory()` 这个动作。

当应用把 Session 交给 MemoryService 后，长期 Memory 就不再只是“Session 的一个视图”。它已经被复制到了另一套持久化服务里。之后删除原 Session，只会影响 SessionService 管理的数据；除非框架明确实现级联删除，否则没有理由假设另一套服务会自动跟着清理。

![Google ADK 中 Session 被复制到 MemoryService 后，删除 Session 但长期 Memory 仍可被 search_memory 查询的生命周期示意图](../../assets/uploads/google-adk-memory-delete/02-session-memory-lifecycle.webp)

Google ADK 的公共接口也能看出这种分离。截至本文验证的 2.8.0 和 2.9.0，`BaseSessionService` 提供 `delete_session()`，但 `BaseMemoryService` 主要提供添加和搜索能力，我在运行时检查到的可调用 `delete*` 方法数量是 0。

如果要先理解“短期状态、跨 Session 长期 Memory、用户隔离和遗忘机制”这些基础层次，可以先看站内的 [AI Agent Memory System：记忆分层、隔离、遗忘与长期状态](/ai/agent-memory-system/)。本文只处理其中更窄的一条删除边界：**Session 生命周期不能替代 Memory 生命周期。**

这也是为什么上游 issue #6949 会把问题直接描述成“MemoryService 没有删除入口”：对于需要完成用户数据删除的应用来说，Session 和 Artifacts 有各自的删除路径，而长期 Memory 没有一个统一的、后端无关的删除接口。

## 上游最近为什么又重新出现这个问题

这个边界不是今天才第一次被提出。

2026 年 8 月 30 日，上游 issue #6949 已经指出：`BaseMemoryService` 没有与 `delete_session()`、`delete_artifact()` 对应的通用删除方法，并提出 `delete_memory()` / `delete_memories()` 这样的接口方向。

9 月 13 日，新的 issue #7110 又把问题缩小到一个更直接的失败场景：先把 Session 写入 Memory，再调用 `delete_session()`，长期 Memory 不会跟着消失。这正是本文最小复现验证的 failure shape。

我这里把这两个 Issue 当作“外部问题证据”，但最终结论不是从 Issue 文本抄出来的：2.8.0 与 2.9.0 的行为是本地脚本重新跑出来的。

## 这对“删除账号”和隐私功能有什么实际影响

如果你的产品只把 Memory 当成临时辅助信息，这个问题可能暂时不会显现。但一旦产品提供下面这些功能，删除边界就必须单独设计：

- 删除某一条对话；
- 清除聊天历史；
- 清空 AI 记忆；
- 注销账号；
- 用户数据导出与删除；
- 企业数据保留策略；
- 多租户用户离职或组织退出后的数据清理。

最危险的实现方式，是 UI 上只调用 `delete_session()`，随后就向用户展示“数据已删除”。因为从本文验证的内存实现来看，这句话至少对 Memory 层是不成立的。

更稳妥的做法是把数据删除写成一张明确的 deletion ledger：

| 数据表面 | 删除动作 | 删除后验证 |
|---|---|---|
| Session | `delete_session()` | `get_session()` 返回不存在 |
| Long-term Memory | 后端专用删除能力 | `search_memory()` 不再命中用户 marker / id |
| Artifacts | ArtifactService 删除 | 读取返回不存在 |
| 外部向量库 | 按 user/tenant/id 删除 | 查询结果为 0 |
| 业务数据库 | 事务/软删/硬删策略 | 业务查询复核 |

![生产环境用户数据删除请求需要分别清理 Session、长期 Memory、Artifacts、向量库和业务数据库，并逐项验证的架构图](../../assets/uploads/google-adk-memory-delete/03-production-deletion-fanout.webp)

删除动作和删除后验证必须成对出现。只发出 delete 请求但不做 read-back 验证，依然无法证明最终状态。

![数据删除必须经过定位存储、执行删除、回读验证、失败调查和最终确认的闭环流程图](../../assets/uploads/google-adk-memory-delete/04-delete-verify-loop.webp)

## 现在有什么可用的处理方式

当前最现实的方案不是“再调用一次 delete_session()”，而是根据你实际使用的 Memory 后端处理。

如果是自建 MemoryService，应该给底层存储设计明确的删除键，例如 `user_id + memory_id`、tenant namespace 或能够覆盖用户全部长期记忆的索引，并且让删除操作具备审计记录。

如果使用托管 Memory 后端，要检查该后端自身是否提供删除 API，并直接使用它完成删除，而不是等待 SessionService 级联。上游 #6949 也明确提到 Vertex 侧存在底层 memory 删除能力，但 ADK 的通用 `BaseMemoryService` 尚未把它抽象成统一接口。

如果你选择的 MemoryService 暂时完全没有删除能力，而产品又必须支持用户删除请求，最安全的工程判断是：**不要把必须可删除的数据写进去，或者更换具备可验证删除能力的后端。**

## 不要把这个结论扩大成“Google ADK 不支持数据删除”

本文验证的是一个具体边界，不是对整个框架下结论。

我没有测试 `VertexAiMemoryBankService`，也没有使用任何外部托管基础设施。不同 MemoryService 完全可能在底层提供额外的删除能力，只是当前 `BaseMemoryService` 没有统一暴露出来。

同样，我也没有证明未来版本一定继续保持这个行为。这个实验之所以保留 2.8.0 与 2.9.0 的版本矩阵，就是为了后续每次 ADK 升级都能重新跑一次。将来如果公共 API 增加删除方法，或者框架引入明确的 cascade 语义，当前断言就应该失败，文章也必须更新。

## 和 Google ADK 其他恢复问题不要混在一起

站内已有一篇 [Google ADK state_delta 恢复问题实测](/ai/google-adk-state-delta-resume/)，处理的是 `Runner.run_async()` 在 resumable invocation 中的状态写入，以及 A2A HITL 消息转换边界。

这篇新文章不应该合并进去，因为用户任务不同：

- `state_delta` 页面回答“恢复 Agent 时状态为什么没写进去”；
- 本文回答“删掉 Session 后，长期 Memory 为什么还在”。

二者都属于 ADK 生产问题，但搜索意图、复现脚本和生产处理方式都不同，分别保留 URL 更合理。

如果你正在做框架级选型，可以继续看 [AI Agent 框架怎么选：LangGraph、AI SDK 7、Google ADK 与 Microsoft Agent Framework](/ai/ai-agent-framework-comparison/)，把 Memory 生命周期、恢复语义和删除能力一起加入生产验收清单。

## 最终处理建议

如果你的应用正在使用 Google ADK 长期 Memory，我建议马上做三件事。

第一，把 `delete_session()` 从“完整用户删除”的实现里拆出来，明确它只负责 Session。

第二，为当前实际 MemoryService 增加独立删除路径和删除后验证，尤其是账号注销、清空记忆、多租户数据隔离这几类功能。

第三，把本文的最小复现加入升级回归测试。每次升级 `google-adk`，重新验证 Session 删除、Memory 搜索结果和公共 delete API；不要只看版本说明就假设数据生命周期已经变化。

截至 2026 年 9 月 15 日，我在 2.8.0 与 2.9.0 上的结论一致：**删除 Session 不等于删除长期 Memory。生产系统应该把两者当成两个独立的数据生命周期来管理。**

## 官方与复现资料

- [google/adk-python issue #6949：No way to delete memories from a MemoryService](https://github.com/google/adk-python/issues/6949)
- [google/adk-python issue #7110：Memory has no removal path](https://github.com/google/adk-python/issues/7110)
- [Google ADK Python repository](https://github.com/google/adk-python)
