---
title: "OpenAI Responses API 中断流后，为什么报 No tool call found for function call output？"
description: "OpenAI Responses API 流式返回 function_call 后，如果客户端提前关闭 Stream，call_id 可能没有写入 Conversation，下一轮提交 function_call_output 就会报 400。本文结合官方 Issue 和本地状态机实验，给出判断、恢复、幂等与生产修复方案。"
seoTitle: "OpenAI No tool call found：流中断修复"
seoDescription: "OpenAI Responses API 中断流后报 No tool call found for function call output？本文分析 call_id 未提交原因，并给出 Conversation 对账、幂等和安全恢复方案。"
geoSummary: "当 OpenAI Responses API 在流式阶段已经发出 response.output_item.added 或 response.function_call_arguments.done，但客户端在 Response 完成前关闭连接时，收到的 function_call 仍可能只是客户端可见的临时事件，没有成为 Conversation 中可引用的持久化 Item。此时若本地先执行工具，再在下一轮提交对应 call_id 的 function_call_output，API 会返回 400 No tool call found for function call output。安全策略不是盲目重试旧 call_id，而是把工具执行放在持久化确认之后；遇到中断或连接状态不明时，先读取 Conversation Items 对账，找不到 call_id 就丢弃该调用并重新发起一轮，同时用稳定幂等键保护所有外部副作用。"
category: ai
section: practice
contentType: error-guide
subcategory: openai-api
series: "OpenAI API 生产排障"
seriesOrder: 1
hideStructuredBlocks: true
draft: false
image: '../../assets/covers/standardized/01-cover-zh-ca25a35d-1200x630.webp'
imageAlt: "OpenAI Responses API 流式 function_call 在 Stream Abort 后未提交到 Conversation，并触发 400 No tool call found 错误"
tags:
  - OpenAI Responses API
  - Function Calling
  - Streaming
  - Tool Calling
  - Python SDK
  - Conversation State
  - Idempotency
  - Error Handling
  - Production Engineering
keywords: OpenAI No tool call found for function call output，OpenAI Responses API stream abort，OpenAI function_call_output 400，OpenAI call_id not found，Responses API function call 丢失，OpenAI Conversation Items，response.output_item.added，response.function_call_arguments.done，OpenAI tool call streaming error，OpenAI Python SDK 3.19.2
primaryKeyword: "No tool call found for function call output"
targetHub: "AI Agent"
conversionTarget: "OpenAI Responses API Stream Abort Lab、AI Agent Tool Use 专题、XBSTACK AI Engineering Weekly"
evidenceStatus: partial
contentRole: main
tldr:
  - "收到 response.output_item.added 或 response.function_call_arguments.done，不等于 function_call 已经持久化到 Conversation；它们只证明客户端看到了流式事件。"
  - "OpenAI Python SDK 官方仓库 Issue #3561 显示：在 function_call 出现后关闭 Stream，Conversation Items 可能仍为空，下一轮提交对应 function_call_output 会返回 400 No tool call found。"
  - "截至 2026-09-27，Issue #3561 仍为 Open、标记为 bug；OpenAI Python SDK 最新 Release 已到 3.19.2（2026-09-23），但 3.19.2 及此前公开 Release 仍没有把 #3561 标记为已修复。PR #3621 也仍为 Open，9 月 8 日的讨论进一步转向 Responses 专用的 pending tool-call reconciliation，而不是把通用 Stream.close() 当成完整修复。"
  - "最安全的执行门槛是 Response 完成后再次读取 Conversation Items，确认 call_id 已存在，再执行具有外部副作用的 Tool。"
  - "如果流已中断或连接状态不明，先对账；Conversation 中没有 call_id 时，不要继续提交旧 Output，应丢弃该 call_id 并重新发起一轮。"
  - "即使 call_id 已持久化，工具投递仍可能重复；支付、部署、发信、写库等操作必须使用稳定幂等键和结果账本。"
queries:
  - OpenAI No tool call found for function call output 怎么解决？
  - OpenAI Responses API 流中断后 call_id 为什么找不到？
  - response.output_item.added 后可以立即执行工具吗？
  - function_call_arguments.done 是否代表工具调用已经保存？
  - OpenAI Conversation Items 为什么是空的？
  - OpenAI function_call_output 返回 400 怎么排查？
  - Responses API Stream 关闭后怎么恢复 Tool Call？
faqs:
  - question: "No tool call found for function call output 是什么意思？"
    answer: "它表示本次 function_call_output 引用的 call_id 不存在于服务端当前可见的会话状态中。常见原因包括把 Output 发到错误的 Conversation、call_id 复制错误，以及流式 Response 在提交前被中断，导致客户端看到了 Tool Call，但 Conversation 没有持久化该调用。"
  - question: "收到 response.output_item.added 后可以立即执行工具吗？"
    answer: "对于无副作用的读操作可以按业务风险自行决定，但不能把该事件当作服务端已提交凭证。支付、部署、写库、发信等操作应等待 Response 完成并读取 Conversation Items 确认 call_id，或先持久化应用自己的执行意图并使用幂等键。"
  - question: "response.function_call_arguments.done 是否等于 function_call 已保存？"
    answer: "不等于。它表示函数参数流已经结束，适合开始解析和校验参数；它没有承诺该 function_call 已经成为 Conversation 中可在下一轮引用的持久化 Item。"
  - question: "流中断后能否继续重试同一个 function_call_output？"
    answer: "先读取 Conversation Items。只有当对应 call_id 确实存在时，才应继续提交 Output；如果不存在，重复发送同一个 Output 只会继续报 400。应丢弃旧 call_id，重新发起一次模型轮次，并依靠幂等账本避免工具被重复执行。"
  - question: "升级到最新 openai Python SDK 能解决吗？"
    answer: "截至 2026-09-27，官方 Issue #3561 和 PR #3621 都仍为 Open；最新 Release 3.19.2 的公开修复项也没有声明解决该问题。因此升级可以用于隔离回归测试，但不能据此删除中断回归、Conversation 对账和业务幂等保护。"
  - question: "使用 previous_response_id 而不是 Conversation 能绕过吗？"
    answer: "不能直接推导。Issue #3561 的具体路径使用 Conversation，本文没有用真实 API 对 previous_response_id 做同条件测试。无论使用哪种状态方式，都不应在未确认服务端上下文已接受 Tool Call 时提交具有副作用的 Output。"
note: "官方服务端行为依据 openai/openai-python Issue #3561；本地实验未调用 OpenAI API，也未独立复现服务器 Bug。实验使用 Python 标准库建立确定性 Conversation 提交模型，验证正常完成、收到 Tool Call 后中断、先对账再执行、重复投递加幂等四条策略。正文中凡涉及 OpenAI 真实 API 行为均标注为官方 Issue 或官方文档事实；本地结果只用于验证应用层恢复策略。"
entities:
  - OpenAI Responses API
  - OpenAI Python SDK
  - Conversation API
  - function_call
  - function_call_output
  - call_id
  - response.output_item.added
  - response.function_call_arguments.done
  - response.completed
  - Idempotency Ledger
  - Stream Abort
citations:
  - https://github.com/openai/openai-python/issues/3561
  - https://github.com/openai/openai-python/releases/tag/v3.19.2
  - https://github.com/openai/openai-python/pull/3621
  - https://developers.openai.com/api/docs/guides/function-calling
  - https://developers.openai.com/api/docs/guides/conversation-state
  - https://platform.openai.com/docs/api-reference/responses-streaming/response/output_item/done
  - https://github.com/openai/openai-agents-js/pull/1241
topicGovernance:
  status: error
  intent: "解决 OpenAI Responses API 在流式 function_call 出现后中断，导致下一轮 function_call_output 报 No tool call found 的排查、恢复和生产幂等问题。"
  differentiation: "站内现有 OpenAI Agents SDK RunState 文章讨论 Tool Approval 恢复和 Session 持久化；本文聚焦底层 Responses API Conversation，在 Stream Abort 时客户端已见 call_id、服务端却未提交 function_call 的状态裂缝，并通过本地契约实验验证对账门槛、旧 call_id 丢弃和业务幂等策略。"
  inventoryCheckedAt: '2026-09-27'
  inventoryReferences:
    - '/ai/openai-agents-sdk-runstate-approval-resume/'
    - '/ai/langgraph-agent-error-recovery-retry-timeout/'
    - '/ai/ai-agent-tool-use/'
clusterHub: '/ai/'
audience:
  - "使用 OpenAI Responses API、Conversation 和 Function Calling 的 Python 开发者。"
  - "需要在浏览器断线、用户停止生成或代理超时后安全恢复 Tool Call 的后端团队。"
  - "负责支付、部署、写库和通知等有副作用工具的 Agent 平台工程师。"

createdAt: '2026-08-05'
lang: 'zh-CN'
route: '/ai/openai-responses-api-stream-abort-tool-call-lost/'
canonical: 'https://www.xbstack.com/ai/openai-responses-api-stream-abort-tool-call-lost/'
hub: 'agent'
translationKey: 'ai:openai-responses-api-stream-abort-tool-call-lost'
translations:
  zh-CN: '/ai/openai-responses-api-stream-abort-tool-call-lost/'
  en: '/en/ai/openai-responses-api-stream-abort-tool-call-lost/'
translationStatus: 'published'
indexing: 'index'
---
# OpenAI Responses API 中断流后，为什么报 No tool call found for function call output？

先给结论：**`response.output_item.added` 让客户端看见了 `function_call`，不代表这个调用已经成为 Conversation 中可引用的持久化 Item。**如果客户端在 Response 完成前关闭 Stream，本地又立即执行了工具，下一轮再提交同一个 `call_id` 的 `function_call_output`，就可能收到 `400 No tool call found for function call output`。这时最危险的不是 400 本身，而是工具可能已经完成支付、部署、发信或写库，服务端却没有保存它对应的调用记录。

最快的处理方式不是反复重试旧 Output，而是先读取当前 Conversation Items：能找到 `call_id`，再继续提交结果；找不到，就把该调用视为未提交，丢弃旧 `call_id`，重新发起模型轮次。生产系统还需要把所有外部写操作放在稳定幂等键之后，因为“调用已提交”和“工具只执行一次”是两件不同的事。

本文的 OpenAI 服务端事实来自官方 Python SDK Issue #3561。为了不把未授权的生产 API 调用伪装成本站实测，我没有连接真实 OpenAI API，而是建立一个确定性本地状态机，验证四种应用策略：正常完成后执行、看到 Tool Call 就执行再中断、中断后先对账、已提交调用重复投递加幂等。服务端 Bug 是否在某个后续版本修复，仍以官方 Issue、PR 和 Release 为准。

## 一、完整报错到底在说什么

典型错误是：

```text
400 No tool call found for function call output with call_id call_xxx.
```

这句话并不是在说工具函数不存在，也不是参数 Schema 校验失败。它表达的是一个更严格的关联约束：你提交的 `function_call_output` 带着某个 `call_id`，但服务端在当前会话上下文中找不到与之配对的 `function_call`。只有调用和输出组成合法的一对，模型才能在下一轮把工具结果继续纳入推理。

排查时先区分三类原因。第一类是业务接线错误，例如把 Output 发到了另一个 Conversation、错误复用了旧 `call_id`，或者在多并发请求中串错了用户。第二类是状态选择错误，例如一轮使用 Conversation，下一轮却切到另一套上下文管理方式。第三类就是本文讨论的中断窗口：客户端已经在流里收到了函数调用，但 Response 尚未完成，服务端最终没有把这个 Item 写入 Conversation。

OpenAI Python SDK 官方仓库的 Issue #3561 给出了完整路径：创建 Conversation；发起流式 Responses 请求；在 `response.output_item.added` 收到 `function_call` 后立即关闭流；随后查询 Conversation Items，结果为空；最后在同一个 Conversation 提交对应 Output，返回 400。原始报告使用 Windows 10、Python 3.11.5 和 `openai 2.45.0`，并明确说明本地工具已经执行，问题出在远端会话没有记录它所属的 Tool Call。

![OpenAI Responses API 从流式事件、Stream Abort、Conversation 未提交到 function_call_output 返回 400 的完整链路](../../assets/uploads/openai-responses-stream-abort-tool-call-lost/02-abort-chain-zh.svg)

## 二、截至 2026-09-27，官方状态是什么

这个时间点很重要，因为“原始复现版本是 2.45.0”不等于“升级到最新版就解决”。截至 2026-09-27，OpenAI Python SDK 最新公开 Release 已到 `v3.19.2`（2026-09-23），但其公开 Bug Fixes 并没有声明修复 #3561；Issue #3561 仍为 Open、标签仍是 `bug`。直接关联 #3561 的 PR #3621 也仍未合并。9 月 8 日的最新讨论甚至明确指出，简单在通用 `Stream.close()` 上做关闭处理并不足以解决 Conversation 状态裂缝，更合理的方向是让 Responses 层保留 pending function call，并提供专门的 reconciliation 过程。

因此，截至现在能写的准确结论仍然是：官方仓库有真实复现、候选 PR 和持续中的修复讨论，但**仍没有“已合并修复 + 已发布 Release”的完整证据链允许我们把 3.19.2 或其他版本标记为正式修复版本**。升级到最新版值得做回归验证，但不能仅凭版本号删除 Conversation 对账和业务幂等保护。

如果你的问题发生在更上层框架，可以对照 [OpenAI Agents SDK RunState 审批恢复实测](/ai/openai-agents-sdk-runstate-approval-resume/) 和 [AI SDK 7 中断、Tool Call 与恢复迁移实测](/ai/vercel-ai-sdk-7-migration-production/)。它们处理的是框架级 Resume 和 Tool Loop 状态；本文只聚焦 Responses API Conversation 的底层提交裂缝。

也不建议因为一条 Issue 就立即回退 SDK。这个错误跨越客户端流处理、Responses 服务端提交和 Conversation 状态三个边界，降级未必改变服务端行为，还可能重新引入其他类型、重试或鉴权问题。更合理的版本策略是：先锁定当前生产依赖，补上中断回归和对账门槛；候选版本在隔离 Project 中跑同一套故障矩阵；只有官方修复记录、真实 API 结果和业务副作用计数三者一致时，再决定升级或移除临时保护。

维护这篇文章时也不能只看 Issue 是 Open 还是 Closed。关闭原因可能是已修复、无法复现、转移到服务端团队或重复 Issue；真正需要更新的字段包括修复 PR、合并 Commit、首次包含修复的 Release、受影响版本范围，以及旧临时方案是否仍有必要。即使官方最终修复，Conversation 对账和业务幂等仍然有长期价值，因为浏览器断线、队列重投和外部系统超时不会随一个 SDK Bug 消失。

Issue 还提到，JavaScript Agents SDK 曾在 PR #1241 处理类似的“server-managed run 中断后协调已流式输出的 function call”问题。这个关联证明同类状态裂缝并非纯理论风险，但 JavaScript Agents SDK 的修复不能替代 Python Responses API 的正式结论。不同 SDK、Runner 和服务端状态管理路径必须分别验证。

## 三、为什么看见 function_call，仍然不等于可以执行

流式 API 的核心价值，是在完整 Response 结束前就把增量事件交给客户端。`response.output_item.added` 表示一个 Output Item 被加入当前流式输出，`response.function_call_arguments.done` 表示函数参数已经传输完成。它们适合驱动界面展示、参数解析、预校验和日志，但都不是一个天然的“外部副作用提交令牌”。

这里至少存在三层状态：

| 层级 | 你知道了什么 | 不能据此推导什么 |
|---|---|---|
| 客户端事件 | 流里出现了 `function_call` 和 `call_id` | Conversation 已经持久化该调用 |
| Response 完成 | 当前模型轮次正常完成 | 工具只能被投递一次 |
| Conversation 对账 | 服务端 Items 中确实存在该 `call_id` | 支付、部署或写库具备业务 Exactly-once |

许多实现把第二层和第三层混在一起，更常见的是直接从第一层跳到工具执行：一看到 `function_call` 就启动任务队列。对于读取天气、查询公开数据等无副作用工具，这个风险可能只是一次浪费；对于扣款、发券、创建订单、部署版本、发送邮件或修改权限，它会形成“外部动作已发生，但会话证据不存在”的孤儿副作用。

所以，`call_id` 既不能直接当幂等键，也不能直接当授权凭证。它首先是模型调用与工具输出之间的关联标识。你可以把它纳入应用幂等键，但仍需绑定租户、业务对象、操作类型和版本，例如：

```text
tenant-a:deploy:release-2026-08-05:call_xxx
```

如果同一个业务操作在模型重试后获得了新的 `call_id`，只依赖 `call_id` 会再次执行。真正稳定的幂等键应该优先来自业务意图，例如订单号、发布版本号、工单号或用户操作 UUID。

## 四、本地实验怎么设计，以及它没有证明什么

实验代码位于：

```text
experiments/openai-responses-stream-abort-tool-call-loss/
```

它使用 Python 标准库建立两个明确区域：`provisional_items` 表示已经通过流事件暴露、但尚未提交的调用；`committed_items` 表示已经进入 Conversation、可以被后续 Output 引用的调用。正常完成会把临时调用提交，中断会丢弃临时调用；提交 Output 时，如果找不到对应 `call_id`，就抛出与官方报告相同语义的错误。

这不是对 OpenAI 服务器内部实现的逆向模拟，也不是本站独立复现了官方 Bug。它只把 Issue 暴露出的应用契约显式化：**客户端可见不等于服务端已提交。**这样我们可以在不调用真实 API 的前提下，稳定验证不同执行策略会产生什么副作用。

实验固定了四条路径：

1. Stream 正常完成，确认调用已提交后再执行工具；
2. 收到 `output_item.added` 就执行工具，随后中断；
3. 中断后先检查服务端状态，再决定是否执行；
4. 调用已提交，但工具任务重复投递两次，使用幂等账本去重。

没有测试真实网络延迟、浏览器断线、HTTP/2 连接复用、代理超时、OpenAI 服务端提交时序、模型选择工具的准确率、真实 Token 成本，也没有验证 `previous_response_id` 在同样条件下的行为。因此，正文中关于 OpenAI API 的事实以官方文档和 Issue 为准，本地实验只支持应用恢复策略。

## 五、四组结果说明了什么

实验和四个标准库单元测试全部通过，结果写入：

```text
experiments/openai-responses-stream-abort-tool-call-loss/results/verification.json
```

结果对比如下：

| 场景 | Conversation 中的 Item | 工具投递 | 实际副作用 | 下一轮 |
|---|---|---:|---:|---|
| 正常完成后执行 | call + output | 1 | 1 | 接受 |
| 看到 call 就执行，再中断 | 空 | 1 | 1 | 400 拒绝 |
| 中断后先对账 | 空 | 0 | 0 | 丢弃旧调用 |
| 已提交调用重复投递，带幂等 | call + output | 2 | 1 | 接受 |

第二行是整个问题的核心。工具已经执行 1 次，Conversation 却没有任何 Item，下一轮只能得到：

```text
No tool call found for function call output with call_id call_aborted.
```

如果工具只是读天气，重新发起一轮即可；如果工具已经扣款，盲目重新发起会有二次扣款风险。如果为了避免重复而永久不重试，用户又可能看到任务失败。解决这个矛盾不能靠 Prompt，只能靠应用自己的业务状态和幂等账本。

第三行证明了最保守的门槛：中断后先对账，找不到 `call_id` 就不执行。这样不会制造孤儿副作用，但也意味着用户请求需要重新生成 Tool Call。第四行则说明，Conversation 对账并不能替代幂等；即使调用合法存在，队列至少一次投递、Worker 崩溃重启和人工重试仍可能让工具收到两次任务。

## 六、线上遇到 400，最快怎样排查

不要先改 Prompt，也不要先把 SDK 降级。按下面顺序查，通常能很快把问题缩小到“关联错误”还是“流中断未提交”。

### 第一步：确认 Conversation 和 call_id 属于同一轮

记录至少这些字段：

```text
request_id
conversation_id
response_id
call_id
user_id
tenant_id
stream_status
tool_name
business_idempotency_key
```

检查 Output 是否发到了生成该 Tool Call 的同一个 Conversation，是否在并发请求中把另一个用户或另一个 Tab 的 `call_id` 混了进来。不要只打印最后 6 位，因为并发问题需要完整关联。

### 第二步：读取 Conversation Items

在执行高风险工具前，或者任何中断之后，查询 Conversation Items，并按 `call_id` 查找对应 `function_call`。如果不存在，就停止提交 Output。这里的停止不是“无限等待”，而是把这次调用标记为 `uncommitted` 或 `orphaned-intent`，进入重新生成或人工核对流程。

### 第三步：检查 Stream 是怎样结束的

区分正常结束、用户主动停止、前端组件卸载、AbortController 取消、反向代理超时、移动网络断开和服务器进程重启。只有捕获这些结束原因，才能知道为什么本地拿到了调用，服务端却没有完成提交。

### 第四步：检查工具是否已经产生副作用

不要以 Conversation 为空就推导“工具没执行”。查支付流水、部署记录、邮件 Message ID、数据库唯一键和任务账本。Issue #3561 最危险的地方正是：远端没有调用记录，本地工具却已经执行。

### 第五步：决定恢复路径

| 对账结果 | 副作用状态 | 处理 |
|---|---|---|
| call 存在 | 未执行 | 使用幂等键执行并提交 Output |
| call 存在 | 已执行 | 复用账本结果，提交 Output |
| call 不存在 | 未执行 | 丢弃旧 call_id，重新发起模型轮次 |
| call 不存在 | 已执行 | 不要再次执行；进入业务补偿或人工核对，再重新建立会话事实 |

最后一行没有通用自动答案。外部动作已经发生，但模型上下文没有依据时，你需要决定是把结果作为普通用户消息重新告知模型，还是创建应用级审计事件后开启新一轮；不同业务对一致性和合规的要求不同。

## 七、生产系统应把 Tool Call 做成什么状态机

一个可靠的 Tool Orchestrator 至少需要下面这些状态，而不是只有 `pending/success/failed`：

```text
stream_observed
→ call_committed
→ execution_reserved
→ execution_succeeded
→ output_submitted
→ model_acknowledged
```

任何中断都要落到可诊断分支：

```text
stream_aborted_before_commit
commit_unknown
execution_unknown
output_rejected
manual_reconciliation_required
```

`stream_observed` 只能用于显示“模型正在准备调用工具”，不能触发高风险执行。`call_committed` 表示 Conversation 对账成功。`execution_reserved` 表示应用已经用业务幂等键占位，其他 Worker 不能重复执行。`execution_succeeded` 保存真实结果和外部系统凭据。`output_submitted` 表示已经把结果发给模型，`model_acknowledged` 才是整个轮次完成。

这套状态机的价值，是让浏览器断线不再等于任务状态丢失。前端可以断，SSE 可以断，Worker 可以重启，但应用数据库仍知道外部动作是否执行、结果在哪里、是否已提交给模型，并且能够给出可审计的恢复依据。Conversation 是模型上下文，不应该承担支付账本、部署审计或订单真相源的职责。

![OpenAI Responses API 高风险 Tool Call 从 stream_observed 到 model_acknowledged 的生产状态机，以及中断和人工对账分支](../../assets/uploads/openai-responses-stream-abort-tool-call-lost/03-state-machine-zh.svg)

### 状态表至少要保存哪些字段

不要只在日志里打印 `call_id`。日志会轮转，Trace 可能采样，真正用于恢复的字段应进入事务数据库。一个最小 Tool Intent 表可以包含：

```text
intent_id
business_idempotency_key
user_id
tenant_id
conversation_id
response_id
call_id
tool_name
arguments_hash
stream_observed_at
call_committed_at
execution_reserved_at
execution_succeeded_at
output_submitted_at
model_acknowledged_at
status
abort_reason
external_result_id
result_payload_ref
retry_count
last_error_code
created_at
updated_at
```

`arguments_hash` 用于判断同一个业务键是否被不同参数复用；一旦发现冲突，应拒绝自动复用旧结果。`external_result_id` 保存支付流水号、部署 ID、邮件 Message ID 等外部事实，恢复时优先向真实系统反查。`result_payload_ref` 可以指向加密对象存储，避免把大结果或敏感数据直接塞进主表。每一次状态变更都应带版本号或乐观锁，防止两个 Worker 同时把 `execution_reserved` 改成成功。

数据库层最好建立两类唯一约束：业务幂等键全局唯一；`conversation_id + call_id` 在租户内唯一。前者防止同一订单或发布版本被新 `call_id` 重复执行，后者防止同一 Tool Call 被并发 Worker 重复领取。对于允许重试但参数可能变化的操作，可以把业务键设计为 `operation_type + resource_id + desired_version`，而不是简单使用用户输入文本。

观测指标也应围绕状态裂缝设计。建议至少统计：`stream_observed_without_commit_total`、`tool_execution_before_commit_total`、`function_call_output_not_found_total`、`reconciliation_latency_ms`、`duplicate_delivery_total`、`idempotency_reuse_total` 和 `manual_reconciliation_total`。其中 `tool_execution_before_commit_total` 在高风险工具上应长期为 0；一旦出现，说明某条路径绕过了 Orchestrator。400 数量下降并不一定代表系统更安全，也可能只是错误被吞掉，因此必须同时看外部副作用和账本一致性。

保留审计事件时，不要记录完整 Secret、支付卡信息或未经处理的用户隐私。参数日志可以保存字段白名单、Hash 和敏感级别，真实结果通过受控引用访问。这样既能在故障后还原因果链，也不会为了排查一次 Tool Call 把整个生产数据暴露到日志平台。

## 八、一段更安全的 Python 执行骨架

下面的代码不是 OpenAI SDK 的完整封装，而是生产控制点示例。重点是把“看到调用”“确认提交”“占用幂等键”“执行工具”“提交 Output”拆开：

```python
from dataclasses import dataclass

@dataclass
class ToolIntent:
    conversation_id: str
    response_id: str
    call_id: str
    tool_name: str
    arguments: dict
    business_key: str


def handle_streamed_call(client, intent: ToolIntent, ledger, executor):
    # 1. 客户端看见 call，不代表服务端已经提交。
    items = client.conversations.items.list(
        conversation_id=intent.conversation_id,
    )

    committed = any(
        item.type == "function_call" and item.call_id == intent.call_id
        for item in items.data
    )
    if not committed:
        return {
            "status": "discarded_uncommitted_call",
            "call_id": intent.call_id,
        }

    # 2. 用业务键占位，不能只依赖 call_id。
    existing = ledger.get(intent.business_key)
    if existing:
        tool_result = existing.result
    else:
        reservation = ledger.reserve(intent.business_key, intent.call_id)
        if not reservation.acquired:
            return {"status": "execution_in_progress"}

        tool_result = executor.execute(
            intent.tool_name,
            intent.arguments,
        )
        ledger.complete(intent.business_key, tool_result)

    # 3. 只有 call 仍存在时才提交 Output。
    return client.responses.create(
        conversation=intent.conversation_id,
        input=[{
            "type": "function_call_output",
            "call_id": intent.call_id,
            "output": tool_result,
        }],
    )
```

这段代码仍需要处理两个竞争窗口。第一，查询 Items 后到提交 Output 前，服务端状态是否可能变化；第二，工具执行成功后进程崩溃，如何从账本恢复结果。生产实现应让 `ledger.reserve()` 和 `ledger.complete()` 具备数据库唯一约束，并保存外部系统返回的不可变 ID；重启后先查账本，不要重新执行。

对于真正高风险操作，还应在 `execution_reserved` 前加 Policy Gate 和 Human Approval。可以参考站内的 [AI Agent Tool 权限控制](/ai/ai-agent-tool-authorization-policy-gate/)；如果你使用 OpenAI Agents SDK 的审批中断，则继续阅读 [RunState 跨进程与流式 Resume 实测](/ai/openai-agents-sdk-runstate-approval-resume/)。

## 九、遇到浏览器断线和代理超时，怎么恢复

真实生产环境不会总是收到一个干净的 `stream.close()`。浏览器可能切后台，手机网络可能从 Wi-Fi 切到蜂窝，Cloudflare 或 Nginx 可能在上游仍运行时关闭下游连接，Node/Python 进程也可能在事件已经到达但日志尚未落盘时崩溃。此时最重要的是承认状态未知，而不是猜“应该成功了”。

建议为每次流式轮次保存一条应用记录：

```text
response_id
conversation_id
last_sequence_number
last_event_type
observed_call_ids
completed_at
abort_reason
reconciliation_status
```

连接异常后，由后台 Reconciler 读取 Conversation Items，并把每个观察到的 `call_id` 分类为 `committed` 或 `missing`。`committed` 的调用可以进入幂等执行队列；`missing` 的调用只能丢弃，不能继续提交 Output。若工具已被前端或另一个服务提前执行，则根据业务账本进入补偿流程。

不要让前端直接拥有高风险工具执行权。更稳妥的路径是：前端只接收流和展示审批；后端负责持久化 Tool Intent、对账 Conversation、执行工具和提交 Output。这样用户关闭页面不会直接打断业务一致性，也不会迫使浏览器保存 API Key、账本和敏感结果。

## 十、怎样把这个问题写进回归测试

只靠人工关闭一次终端，很难证明系统已经安全。真正有价值的回归测试，应当主动制造不同阶段的中断，并同时检查 Conversation、业务账本和外部副作用。测试目标不是“请求没有抛异常”，而是任何故障下都满足两条不变量：没有已提交调用时不执行高风险工具；无论任务被投递多少次，同一个业务意图最多产生一次外部副作用。

![OpenAI Responses API Stream Abort 回归测试矩阵：中断点、Conversation 持久化、工具副作用、旧 Output 和升级判断](../../assets/uploads/openai-responses-stream-abort-tool-call-lost/04-regression-matrix-zh.svg)

第一组是**提交边界测试**。分别在 `response.output_item.added`、`response.function_call_arguments.done`、最后一个参数 Delta、`response.completed` 前后关闭连接。每个时间点都保存 `response_id`、`call_id` 和最后事件序号，再读取 Conversation Items。不要预先假定哪个事件代表持久化，测试应以服务端实际可见状态为准。若 SDK 或服务端版本升级后提交时序变化，这组测试会第一时间暴露差异。

第二组是**副作用门槛测试**。把真实工具替换成计数器或事务性 Fake，例如模拟支付表、部署版本表和邮件发件箱。故障注入后断言：未对账成功时计数必须为 0；对账成功且首次获取业务锁时计数为 1；同一任务重复投递 2 次、5 次甚至 20 次时，外部记录仍只有 1 条。测试不能只断言函数返回值，因为 Worker 可能返回失败，但外部动作已经发生。

第三组是**进程崩溃窗口测试**。至少覆盖以下位置：

```text
账本占位前崩溃
账本占位后、工具执行前崩溃
工具成功后、账本 complete 前崩溃
账本 complete 后、function_call_output 提交前崩溃
Output 已提交、模型最终回复前崩溃
```

每个窗口的恢复策略都不同。账本占位前可以安全重试；占位后要判断锁是否过期；工具成功但账本未完成时必须从外部系统反查，不能直接重做；账本已有结果但 Output 未提交时，应复用旧结果；模型最终回复丢失时，只需恢复展示，不应再次执行工具。

第四组是**真实连接故障测试**。在测试环境中使用反向代理或故障注入中间件，模拟前端主动 Abort、客户端进程被杀、SSE 空闲超时、上游正常但下游断开、网络半开连接和服务重启。记录服务器是否继续生成 Response、SDK 是否抛出可识别异常、Conversation 最终有哪些 Items，以及 Reconciler 多久能把状态收敛。不同故障的表面都可能是“用户停止了生成”，但后端处理不能只依赖一个统一的 `cancelled` 字段。

建议把验收结果做成版本矩阵，而不是只保留一张成功截图：

| SDK 版本 | 中断点 | Conversation 有 call | 工具副作用 | 旧 Output 是否接受 | 结论 |
|---|---|---:|---:|---:|---|
| 当前生产版 | `output_item.added` 后 | 实测填写 | 0 | 实测填写 | 是否安全 |
| 当前生产版 | arguments done 后 | 实测填写 | 0 | 实测填写 | 是否安全 |
| 当前生产版 | response completed 后 | 实测填写 | 1 | 实测填写 | 基线 |
| 候选升级版 | 同样三点 | 实测填写 | 按不变量 | 实测填写 | 是否可升级 |

CI 不应该连接生产支付或部署系统，可以使用隔离 Project、低成本模型、Fake Tool 和临时 Conversation；但至少在每次 SDK 升级、流式封装改动、代理配置变化和前端取消逻辑变化时运行一次真实 API 集成测试。单元测试负责应用状态机，集成测试负责验证 OpenAI 当前行为，两者缺一不可。

本次公开 Lab 已提供最小的四场景不变量测试，但它没有替代真实 API 回归。项目接入后应新增一份受环境变量控制的 `live_integration_test.py`，只有在明确授权、测试 Project 和费用上限就绪时运行，并把 Conversation Items、HTTP 状态和版本信息脱敏保存为构建产物。这样以后官方关闭 Issue 或发布修复版本时，可以用同一套脚本得到可比证据，而不是凭感觉判断“好像不报错了”。

## 十一、常见误区与最终建议

**误区一：收到 `function_call_arguments.done` 就说明调用已经完成。**它只说明参数增量结束，适合做 JSON 解析和 Schema 校验，不代表 Conversation Commit。

**误区二：把 `call_id` 当成业务 Exactly-once 键。**同一业务意图在重新生成后可能出现新 `call_id`；业务幂等键必须绑定订单、发布版本、工单或用户操作。

**误区三：400 之后不断重试同一个 Output。**如果 Conversation 中没有该调用，重试不会凭空创建 Tool Call，只会重复失败。

**误区四：Conversation 为空就说明工具没执行。**工具可能已经在客户端或队列中完成，必须查外部系统和应用账本。

**误区五：最新版高于复现版本，所以可以删除保护。**截至 2026-09-27，OpenAI Python SDK 已到 3.19.2，但 Issue #3561 和候选 PR #3621 都仍为 Open，最新 Release 也没有给出已修复版本结论；升级只能配合回归测试，不能替代对账和幂等。

最终建议可以压缩成一句：

> **流式 Tool Call 的可见性不是执行凭证；先确认服务端已提交，再用应用幂等键执行，任何中断都先对账，找不到 call_id 就丢弃旧调用。**

如果你的工具只有只读查询，策略可以适当放宽，但仍应记录调用和错误；如果工具会支付、发信、部署、写库或改权限，就必须使用后端 Orchestrator、业务状态机、唯一约束和人工审批。关于超时、重试和 Tool Error 的通用恢复，可继续阅读 [AI Agent 失败恢复：Tool Error、Timeout 与重试策略](/ai/langgraph-agent-error-recovery-retry-timeout/)；关于 Tool Calling 的完整生产边界，可进入 [AI Agent Tool Use](/ai/ai-agent-tool-use/)。

## 常见问题

### 为什么 `response.output_item.added` 能拿到 call_id，Conversation Items 却为空？

因为流式事件和持久化状态不是同一个承诺。事件说明当前 Response 正在产生一个函数调用，客户端可以提前看到它；如果流在提交边界前被中断，服务端可能不会把这个临时 Item 写入 Conversation。

### 可以等到 `response.completed` 再执行工具吗？

这比收到 Added 事件立即执行安全，但对于高风险工具，仍建议在执行前读取 Conversation Items 确认 `call_id`。Response 完成解决模型轮次边界，幂等账本解决工具重复执行，两者不能互相替代。

### 如果工具已经执行，但 call_id 不存在，怎样告诉模型结果？

不要伪造或继续使用不存在的 Tool Call。先在业务系统记录真实结果和补偿状态，再开启新一轮，把已发生事实作为普通、可审计的上下文输入，或者转人工处理。具体选择取决于业务是否允许模型继续自动决策。

### 这个错误和 OpenAI Agents SDK RunState 的问题一样吗？

不一样。本文讨论 Responses API Conversation 在 Stream Abort 时没有提交 `function_call`；RunState 文章讨论 Agents SDK 的审批恢复、Session 持久化和已批准 Tool Output。两者都涉及“外部动作与模型状态不一致”，但发生层级和恢复接口不同。

### 本地实验能证明 OpenAI 服务器一定这样实现吗？

不能。本地实验只验证：一旦存在“客户端已看见、服务端未提交”这个官方报告的前提，哪些应用策略安全，哪些会制造孤儿副作用。服务器真实行为、影响版本和修复版本必须以 OpenAI 官方 Issue、PR 和 Release 为准；本文后续也只会在获得新的官方状态和同条件验证结果后更新版本结论。

---

**实验资产：** [OpenAI Responses API Stream Abort Tool Call Loss Lab](https://github.com/xbstack/my-blog-public/tree/main/experiments/openai-responses-stream-abort-tool-call-loss)

**官方来源：** [OpenAI Python SDK Issue #3561](https://github.com/openai/openai-python/issues/3561) · [Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling) · [Conversation State Guide](https://developers.openai.com/api/docs/guides/conversation-state)
