---
title: "LangGraph Human-in-the-loop 实战：多智能体审批流怎么做？"
description: LangGraph Human-in-the-loop 实战：实战讲解 LangGraph 多智能体系统中的 Human-in-the-loop 审批流设计，包括 interrupt 暂停执行、人工审批、拒绝回滚、状态恢复、Checkpointer 和 Supervisor / Worker 协作，帮助开发者构建可控、可审计的生产级 AI Agent。
seoTitle: 'LangGraph Human-in-the-Loop：interrupt 审批与恢复'
seoDescription: 'LangGraph 人工审批实战：interrupt() 挂起、Command(resume=...) 恢复、response_schema 结构化审核、Checkpointer 持久化与防重复执行。'
geoSummary: 'LangGraph 人工审批通过 interrupt() 挂起运行、使用持久化 Checkpointer，并在原 thread_id 上以 Command(resume=...) 恢复；节点将从头重新执行。高风险工具必须核验审批身份与授权范围、避免重复执行，并正确处理拒绝与修改分支。'
primaryKeyword: LangGraph Human-in-the-Loop
keywords: LangGraph human in the loop，LangGraph interrupt 人工审批，LangGraph Command resume，LangGraph response_schema，结构化人工输入，TypedDict，Pydantic 审批，Checkpointer 恢复，节点重放与幂等执行，多智能体审批流，Supervisor Worker 授权
queries:
- LangGraph Human-in-the-loop是什么？
- LangGraph Human-in-the-loop怎么实现？
- LangGraph Human-in-the-loop有哪些常见问题？
- LangGraph Human-in-the-loop适合什么场景？
- LangGraph Human-in-the-loop如何排查和优化？
- LangGraph interrupt response_schema 怎么定义结构化人工输入？
category: "ai"
tags:
  - langgraph
  - human-in-the-loop
  - interrupt
  - checkpointer
  - ai-agent
  - multi-agent
  - approval-workflow
image: '../../assets/covers/standardized/langgraph-human-in-the-loop-approval-bc4b4e1f-1200x630.webp'
series: "LangGraph 生产级 Agent 编排实战"
seriesOrder: 3
mood: "focused"
location: "Guiyang"
imageAlt: "LangGraph Human-in-the-loop 实战：多智能体审批流怎么做？"

citations:
  - https://github.com/langchain-ai/langgraph/releases/tag/1.2.12
  - https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py

clusterHub: '/ai/langgraph/'

createdAt: '2026-06-12'
lang: 'zh-CN'
route: '/ai/langgraph-human-in-the-loop-approval/'
canonical: 'https://www.xbstack.com/ai/langgraph-human-in-the-loop-approval/'
hub: 'langgraph'
translationKey: 'ai:langgraph-human-in-the-loop-approval'
translations:
  zh-CN: '/ai/langgraph-human-in-the-loop-approval/'
  en: '/en/ai/langgraph-human-in-the-loop-approval/'
translationStatus: 'published'
indexing: 'index'
---
<!-- search-intent-lead -->

## LangGraph human in the loop：如何安全暂停和恢复审批流？

LangGraph 人工审批的关键链路是：在节点里调用 `interrupt()` 挂起，通过 Checkpointer 保存状态，再使用相同的 `thread_id` 调用 `graph.invoke(Command(resume=decision), config)` 恢复。**恢复时被中断节点会从头重新执行**，所以 `interrupt()` 之前的外部写入可能被重复触发。不可逆操作应放在审批后的独立执行节点，并加入权限校验及幂等键。这是可复核的架构示例，不是本站新增的生产实测结果。

## 本文解决的问题

- 在复杂的 AI 工作流中，如何防止智能体在无人值守时误调用高危、不可逆或高昂成本的工具。
- 如何在不打破有向无环图（DAG）状态流的前提下，实现状态的暂停、外界修改和继续运行。
- 在多智能体（Multi-Agent）协作系统中，如何划分 Supervisor、Worker 与人工节点之间的控制边界。
- 当人工干预拒绝了 AI 提出的方案后，系统应当如何回滚状态并安全终止或重新规划。
- 在并发多用户环境下，如何设计安全的数据路由，避免审批线程被交叉感染或串线。

## 适合谁读

- 已经熟悉 LangGraph 基础，正在尝试把智能体系统应用到实际业务场景的后台研发人员。
- 需要对接内部 OA、CRM、ERP 系统，且对数据安全性与操作可审计性有极高要求的系统架构师。
- 遭遇过模型“幻觉”误调用发送工具、删除工具而对自动化心存畏惧的独立开发者。
- 想要深入理解 LangGraph 状态持久化、检查点（Checkpointer）与有状态图编排底层机理的开发者。

## 一、 为什么生产级 Agent 不能完全自动执行？

## 本文在 LangGraph 专题中的位置

这篇文章专门解决「人工审批、暂停恢复和高风险工具隔离」。如果你还没处理状态持久化，先看 [LangGraph Checkpointer 实战](/ai/langgraph-checkpointer-memory-sqlite-redis/)；如果审批恢复后经常串线，先回到 [thread_id、session_id、user_id 设计](/ai/langgraph-thread-session-state-isolation/)；如果审批节点出错后需要重试和降级，再看 [LangGraph 多智能体失败恢复](/ai/langgraph-agent-error-recovery-retry-timeout/)；如果要确认 `interrupt()` 恢复时哪些代码会重跑，以及普通取消为什么会丢失流式状态，继续看 [Streaming、Checkpoint 与取消恢复一致性实战](/ai/langgraph-cancel-run-streaming-checkpoint-state-loss/)。

## 实战复核清单

审批流上线前，建议用下面的清单逐项打勾：

- 高风险工具是否默认不可直接执行，只能由 Supervisor 触发审批。
- `interrupt` 返回给前端的 payload 是否经过脱敏和最小化处理。
- 审批通过、拒绝、修改、超时四种状态是否都有明确分支。
- 审批恢复接口是否校验 `user_id + thread_id + approval_id`，而不是只校验一个 token。
- 审批记录是否能回放，包括原始提案、人工修改、最终执行结果和操作者。


设想一个**假设性的**生产故障：分析 Worker 误解模糊指令，直接建议调用 `write_database` 删除 CRM 历史数据。如果 Worker 本身就持有数据库写权限，前端再加一个“确认”弹窗也来不及阻止已经触发的工具调用。

因此，真正的审批流要把**提案、人工复核、权限策略和实际执行**隔离开。这是用于解释风险的示例，并非本站声称亲历过的生产事故或 Mac Studio 回归测试。

生产环境下的高风险动作显而易见：
- 发送给重要客户的商业邮件。
- 数据库的物理删除或批量写操作（SQL 写入）。
- 财务系统的转账、扣款和发票生成。
- 正式生产环境的部署脚本执行与服务关停。
- 外部合同的电子签发或机密信息的导出。

这些场景如果交给大语言模型完全自主执行，只要出现一次概率性的模型幻觉，给企业带来的可能就是底层别的商业损失。因此，在可逆的只读分析与不可逆的写入操作之间，必须建立一道硬性的人工隔离带。这就是 Human-in-the-loop（人机协同）存在的唯一理由。它不是对模型能力的妥协，而是工业级软件工程的必修课。

## 二、 LangGraph interrupt 解决什么问题？

在传统的流程编排中，要实现人工审批，我们通常需要破坏工作流的完整性。我们需要先将状态保存到临时数据库，强行终止当前进程，等待人工在后台页面点击确认后，再通过一个新的进程和入口把数据捞出来重新初始化。这种方式非常丑陋，不仅割裂了工作流逻辑，还让复杂的上下文跟踪变得异常痛苦。

LangGraph 原生提供的 interrupt 机制就是为了优雅地解决这一问题。它的本质是：在图执行（Graph Execution）的过程中，允许在任意节点直接发起挂起信号，中断当前的有向无环图运行，并向调用者返回一个需要人工审查的结构化载荷。

此时，Graph 会暂停，但它的所有上下文、状态变量和调用历史并不会消失，而是通过底层的检查点机制（Checkpointer）安全地封存在持久化数据库中。当人工在外部完成审批，或者修改了相关参数后，只需要携带相同的线程 ID（thread_id）发送恢复信号，需要使用同一个 `thread_id`，通过 `graph.invoke(Command(resume=decision), config)` 恢复。LangGraph 会**从中断节点的开头重新执行该节点**，再次执行到 `interrupt()` 时才返回人工提交的恢复值。中断前的外部写入、发送等副作用如果没有幂等保护，就有重复执行风险。

这是一种具有持久化能力的工作流暂停，并不是从 Python 某一行原地继续。细节见 [LangGraph 官方 Interrupt 文档](https://docs.langchain.com/oss/python/langgraph/interrupts) 和 [interrupt 源码](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py)。

### 2026-09 更新：用 `interrupt(response_schema=...)` 把人工恢复值变成可验证的结构化输入

LangGraph `1.2.12` 正式给 `interrupt()` 增加了 `response_schema`。这不只是让审批页更容易渲染，而是把 **Graph 发出的中断契约** 和 **人工恢复时应该返回的数据结构** 放到了同一个 API 边界里。

对于退款、发布、删除、发信这类审批，不建议只接收一个松散的 `dict`。可以使用 Pydantic、`TypedDict` 或 dataclass 作为 `response_schema`；LangGraph 会把它转换成 JSON Schema 给 Client 使用，并在 Resume 时验证返回值。若直接传 JSON Schema `dict`，Schema 会暴露给 Client，但 LangGraph 本身不会替你验证 Resume 值。

```python
from typing import Literal, TypedDict
from langgraph.types import interrupt

class ApprovalResponse(TypedDict):
    decision: Literal["approve", "reject", "edit"]
    reason: str
    approved_amount: float

def approval_node(state):
    response = interrupt(
        {
            "message": "请审核退款请求",
            "proposed_action": state["proposed_action"],
        },
        response_schema=ApprovalResponse,
    )
    return {"approval_response": response}
```

前端或 OA 可以根据同一份 Schema 生成结构化审批表单，减少 `approve`、`edit`、金额、原因等字段在恢复时发生类型漂移。**Schema 校验仍然不是 Authorization**：谁有资格批准、批准金额上限、审批是否过期、恢复后 Tool 是否仍允许执行，仍然要由应用层 Policy Gate 和业务状态机决定。关于逐调用授权边界，可继续看 [AI Agent 工具授权与 Policy Gate](/ai/ai-agent-tool-authorization-policy-gate/)。

## 三、 审批流里 Supervisor 和 Worker 怎么分工？

在多智能体系统（Multi-Agent System）中，审批流的设计最忌讳的是 Worker 智能体各自为政。如果负责发邮件的 MailWorker 自行在其 Tool 内部触发 interrupt，不仅会让状态难以管理，还会导致系统的耦合度极高。

我认为，合理的生产级审批架构应该遵循下述分工原则：

Supervisor 智能体作为中心大脑，掌握全局的任务风险评级和路由逻辑。Worker 智能体作为专项任务的执行工具，只负责生成结构化的提案（Proposed Action），本身不直接拥有任何物理写工具的权限。

举个例子，当用户提出“给客户发送上月财报”时：
- Supervisor 收到请求，调用 AnalyticsWorker 整理数据并起草邮件。
- AnalyticsWorker 完成工作，但它不直接调用 send_mail 工具。相反，它返回一个标准格式的结构化数据，声明自己起草的内容以及需要人工确认的标记。
- Supervisor 接收到 Worker 的返回，检测到 requires_approval 为 true，随后在 Supervisor 的决策节点中触发 interrupt 挂起。
- 外部人工完成审批后，Supervisor 根据审批结果（通过/拒绝/修改），决定是将任务分发给具体的 Executor 工具节点去执行，还是退回 Worker 重新规划。

我们可以为 Worker 的提案输出定义一个严密的 JSON 契约：

```json
{
  "action_type": "send_email",
  "risk_level": "high",
  "target": "client@example.com",
  "summary": "向客户发送 5 月份投资复利审计报告",
  "proposed_payload": {
    "subject": "5月度AltStack资产审计报告",
    "body": "您好，附件为您的 5 月度投资回报明细，请查收。"
  },
  "requires_approval": true
}
```

## 四、 审批节点应该长什么样？

审批节点（Approval Node）在底层不是一个简单的交互式弹窗，而是一个具备完整生命周期、可追溯、可审计的数据实体。

当我们在 LangGraph 中定义一个审批节点时，该节点至少要向外部展示以下结构化数据，以便被前端页面或 OA 系统正确解析渲染：

```json
{
  "approval_id": "appr_9x882a17f",
  "user_id": "usr_9921",
  "thread_id": "th_langgraph_hil_003",
  "run_id": "run_8b11c9f2",
  "proposed_action": {
    "tool_name": "send_email",
    "payload": "..."
  },
  "risk_level": "critical",
  "created_at": "2026-06-12T09:56:00Z",
  "approval_status": "pending"
}
```

在后端，审批状态的演转应该是一条单向的单色轨道。它的初始状态必然是 pending，经过人工交互后，根据操作行为分化为以下几种结果：
- approved：审核通过，直接将数据投递给后续工具执行节点。
- rejected：审核拒绝，终止该工具的调用，并将拒绝理由写回图状态，交由 Supervisor 决定是否退回重写或直接向用户报错。
- edited：审核人员认为提案的大体逻辑对，但局部细节有瑕疵（例如邮件有错别字，或者 SQL 的 limit 条件太宽），直接修改了 proposed_payload 中的数据，随后提交执行。
- expired/cancelled：审批超时失效或人工撤销。

## 五、 approve / reject / edit 三种结果怎么处理？

在 LangGraph 的节点逻辑中，我们需要利用图的状态（State）来传递人工的审核意见。以下是处理这三种决策的硬核实现机制。

首先，我们定义图的全局状态结构。在 `src/types/` 或直接在定义中：

```python
from typing import TypedDict, Optional, Any

class AgentState(TypedDict):
    task: str
    proposed_action: Optional[dict]
    action_result: Optional[dict]
    approval_status: Optional[str] # approved | rejected | edited
    approval_response: Optional[Any]
```

当图执行到关键审批节点 `prep_approval_node` 时，使用 `interrupt()` 挂起。下方片段用于说明 API 边界，其中 `authorization_service`、`idempotent_tool_executor` 是**业务需要自行实现的组件，并非 LangGraph 自带服务**，不能直接复制片段当成已可生产运行的完整应用。

```python
from typing import Literal, TypedDict
from typing_extensions import NotRequired
from langgraph.types import interrupt

class ApprovalDecision(TypedDict):
    decision: Literal["approve", "reject", "edit"]
    approval_id: str
    reason: str
    edited_payload: NotRequired[dict]

def prep_approval_node(state: AgentState):
    action = state.get("proposed_action")
    if not action or not action.get("requires_approval"):
        return {"approval_status": "rejected"}
    # 恢复时整个节点会重新运行，interrupt() 前不得执行真实写操作
    decision = interrupt(
        {"approval_id": action["approval_id"], "proposed_action": action},
        response_schema=ApprovalDecision,
    )
    # API 层必须单独验证审批人、thread 归属、提案哈希、期限和执行范围
    return {"approval_status": {
                "approve": "approved", "reject": "rejected", "edit": "edited"
            }[decision["decision"]],
            "approval_response": decision}
```

第一次调用会返回 `__interrupt__`，由外部控制台展示待审批提案。完成审批人身份与具体提案校验后，应携带原来的 `thread_id` 调用 `graph.invoke(Command(resume=decision), config)`；恢复值成为 `interrupt()` 在节点重跑时的返回值。普通审批恢复不应把 `update_state` 当成 `Command(resume=...)` 的替代品。

在恢复后的下一个节点 `execute_action_node` 中，我们必须编写防御性的决策逻辑来分流处理：

```python
def execute_action_node(state: AgentState):
    status = state.get("approval_status")
    action = state.get("proposed_action") or {}
    decision = state.get("approval_response") or {}

    if status == "rejected":
        return {"action_result": {"status": "denied",
                "reason": decision.get("reason", "人工拒绝")}}
    if status not in ("approved", "edited"):
        raise PermissionError("尚未获得有效的人工审批")
    if decision.get("approval_id") != action.get("approval_id"):
        raise PermissionError("审批 ID 与原提案不一致")

    payload = (decision.get("edited_payload") if status == "edited"
               else action.get("proposed_payload"))
    if not isinstance(payload, dict):
        raise ValueError("已批准的工具参数必须是对象")
    # 以下两个服务需要业务自行实现，非 LangGraph 内置：
    # 核对审批人、线程归属、提案哈希、过期时间与修改后权限。
    # 审批消费必须原子化，工具调用还需要持久化幂等键。
    authorization_service.verify_and_consume(action, decision, payload)
    result = idempotent_tool_executor.execute(
        action["tool_name"], payload, idempotency_key=action["approval_id"]
    )
    return {"action_result": result}
```

通过这样的逻辑设计，系统在不解构 DAG 结构的前提下，通过更新 approval_status 实现了对分支路径的安全控制。

## 六、 Checkpointer 在审批流里起什么作用？

在探讨 Human-in-the-loop 时，很多开发者容易忽略检查点（Checkpointer）的存在。实际上，要是没有一个可靠的持久化检查点系统，任何审批流在生产环境中都会变得形同虚设。

为什么这么说？因为 interrupt 挂起只是当前计算线程的内存行为。如果你的 Agent 服务是跑在容器（如 Docker）中，或者是在云端 Serverless 架构下：
- 当审批人打开网页进行审查时，可能已经是几个小时之后了。
- 此时，原来的计算进程由于超时或者容器重启，可能早就被物理销毁了。
- 如果没有 Checkpointer，那么之前的所有执行状态、变量和上下文就会随着内存释放而烟消云散。

Checkpointer 的作用，就是在触发 interrupt 的那一瞬间，自动把当前的图状态（State）、所有节点跑完后的 Checkpoint 数据，全部序列化并写入到物理数据库中（比如 Redis, SQLite 或 PostgreSQL）。

当外部审批完成，发送更新信号时，你只需要指定 thread_id：
1. 系统根据 thread_id 从数据库里捞出当时挂起那一刻的历史快照。
2. 将图的反序列化状态重新装载进内存。
3. 将外部写入的审批状态合并进当前状态。
4. **从被中断节点的开头重新执行**；调用 `interrupt()` 时取得恢复值，随后再按图的边继续执行。重复运行前置代码时必须避免重复外部副作用。

这也就意味着，Checkpointer 提供了状态跨越时空和物理进程进行复活的能力。在生产部署中，应始终使用有状态的持久化检查点机制。

## 七、 多用户审批流如何避免串线？

如果在开发中设计不周，在多用户高并发场景下，极易发生“审批串线”的严重安全事故：用户 A 批准了某项操作，结果却被应用到了用户 B 的 thread_id 线程中，导致用户 B 的资金被误转走，或者是其数据被误删。

为了绝对避免这种串线事故，必须在架构设计层面将下述变量进行多重的强行绑定校验：

```text
user_id + thread_id + run_id + approval_id
```

在状态持久化和图更新时，我们必须坚持以下的设计铁律：
- 绝对不鼓励在没有校验 thread_id 的情况下，全局通过一个通用的 approval_id 去更新状态。
- 每一个审批任务生成的 proposed_action 中，必须显式携带当前的 thread_id 和 reviewer_id。
- 当审批结果通过 Webhook 写回时，接口层必须先通过当前登录的用户 Session 校验该用户是否拥有此 thread_id 对应会话的读写权限，验证通过后方可执行 state_update 写入操作。
- 在保存日志时，强制将操作人 reviewer_id 与审批时间戳 timestamp 写入数据库快照，作为后续合规性审计的铁证。

## 八、 哪些工具必须进入审批？

为了在安全性和工作效率之间取得精巧的平衡，我们不能对所有的工具调用都采取一刀切的审批策略。这样做会让审核人员被海量的微小待审批弹窗淹没，最终导致审批流流于形式（审核人会闭着眼疯狂点 approve）。

我认为应当将工具库划分为三级风险边界：

### 1. 允许自动执行的低风险工具（无副作用，只读）
这类工具通常不改变任何系统状态，只进行检索和分析。可以完全对 AI 开放，无需人工确认。
- read_file（读取文件）
- search_knowledge_base（检索知识库）
- call_weather_api（天气查询）
- text_classification（分类）
- format_data（格式化）

### 2. 建议审批的中风险工具（有轻微副作用，可逆）
这类工具会产生外部行为或修改局部业务系统，但仍属于可以通过后续手段进行覆盖或回退的范围。
- update_crm_contact（更新联系人电话）
- create_draft_article（创建文章草稿）
- send_internal_slack_message（发送内部通知）
- calculate_compound_interest（复杂理财数值预估写入）

### 3. 强制审批的高风险工具（不可逆，高成本）
一旦执行，会对物理世界、企业资产或核心数据产生无法恢复的改变，必须由人工在系统层面进行强行校验和确认。
- delete_database_record（物理删除数据）
- execute_raw_sql（执行原始 SQL 语句）
- send_client_email（直接向外部客户发送邮件）
- transfer_funds（财务转账）
- publish_to_production（向生产环境发布代码或数据）

## 九、 常见错误

开发 LangGraph 人工审批流时，下面这些失败模式需要在实际项目中增加回归测试：

### 常见坑 1：只在前端做拦截保护，后端 Tool 接口裸奔
这是最常见也最危险的安全漏洞。开发者仅仅在前端写了弹窗让用户点“确定”，但在图的后端实现中，执行工具的接口根本不校验 approval_status 状态值，只要接收到模型调用指令就直接执行。这种做法只要遇到网络波动、前端刷新或直接用 API 请求绕过，安全网就会瞬间漏风。
- 解决办法：在 Tool 执行的 Python/Node 真实代码层，必须强制进行二次断言校验。

### 常见坑 2：Worker 智能体直接拥有写工具权限
有些设计中，Worker 节点直接把 send_mail_tool 作为其可用工具。这会导致 Worker 在执行中绕过了 Supervisor 的风控路由，自我完成调用。
- 解决办法：Worker 只输出结构化的 Action 提案，统一交给有风控逻辑的 Supervisor 或专门的审批路由来进行过滤分发。

### 常见坑 3：在触发 interrupt 时抛出非持久化异常
如果未正确配置持久化库，在进程重启或多 Pod 切换后可能找不到审批前的状态。下面只是**示意性诊断消息，不是本站采集的真实日志，也不能保证对应 LangGraph 的具体异常类名**：

```text
示例：未找到 thread_id=th_003、checkpoint_id=cp_9a2f1 对应的检查点。
```

- 解决办法：确保在开发和生产环境中，为 Graph 初始化时传入了持久化的 `SqliteSaver`、`PostgresSaver` 或 `RedisSaver` 实例，并且 thread_id 的生成规则全局唯一。

## 十、 最小上线检查清单

在你的多智能体审批系统合并代码并部署上线前，请对照下述清单进行最后的物理核对：

- [ ] 工具库是否完成了只读、可逆写入、高危写入的三级分级？
- [ ] 高危工具执行时是否重新校验用户身份、授权范围、审批提案 ID/哈希与有效期，并使用幂等键避免重复执行？
- [ ] 挂起（interrupt）逻辑是否与持久化存储（Checkpointer）绑定，并支持跨 Pod 状态恢复？
- [ ] thread_id 是否与用户会话 user_id 进行了强行校验，是否存在权限越权漏洞？
- [ ] 审批状态机是否完整覆盖了批准（approved）、拒绝（rejected）与人工修改（edited）三种流程？
- [ ] 当人工拒绝（rejected）后，图是否能安全地退回到 Supervisor 规划节点或输出安全失败结果，而不是卡死在原地？
- [ ] 数据库中是否设计了用于记录 reviewer_id、approved_at、request_payload 的审计日志表？
- [ ] 在并发测试中，多用户同时触发审批，是否会产生状态污染或 thread 交叉？

## FAQ

### LangGraph Human-in-the-loop 和普通的前端确认弹窗有什么本质区别？
普通弹窗只是在交互层进行阻断，如果用户刷新网页或者网络中断，状态就丢失了，甚至可以被直接绕过。LangGraph 的 Human-in-the-loop 是将暂停和恢复能力下沉到了底层的图状态引擎和检查点（Checkpoint）中，即使服务断电重启，也能通过 thread_id 完美恢复，是协议级和引擎级的阻断。

### 审批挂起后还会持续消耗 Token 吗？
单纯等待人工审批时，被挂起的 LangGraph 运行不会不断调用模型；但**独立的后台任务、轮询、外部工具和重试仍可能产生费用**。Checkpointer 保存可恢复状态后，应使用同一 `thread_id` 和 `graph.invoke(Command(resume=decision), config)` 继续。被中断节点会从头执行，因此要考虑重跑成本和外部写操作的幂等性。

### 在多智能体系统中，人工修改（edit）后的载荷怎么传给 Agent？
应该在原线程配置上调用 `Command(resume={"decision": "edit", "approval_id": "...", "reason": "...", "edited_payload": {...}})`。审批节点获得结构化恢复值并写回图状态；执行节点必须重新验证被修改的参数是否仍在授权范围内、是否匹配原始提案，并用持久化幂等键避免重复写入。`update_state` 是独立状态操作，不是通常的 interrupt 恢复接口。

## 系列导航

LangGraph 生产级 Agent 编排实战系列：

- [第 1 篇：Supervisor / Worker](/ai/langgraph-supervisor-worker-handoff/)
- [第 2 篇：状态隔离](/ai/langgraph-thread-session-state-isolation/)
- [第 3 篇：Human-in-the-loop](/ai/langgraph-human-in-the-loop-approval/)
- [第 4 篇：失败恢复](/ai/langgraph-agent-error-recovery-retry-timeout/)
- [第 5 篇：Observability](/ai/langgraph-observability-agent-trace/)
- [第 6 篇：Checkpointer](/ai/langgraph-checkpointer-memory-sqlite-redis/)
- [第 7 篇：Subgraph](/ai/langgraph-subgraph-worker-state/)

## 继续阅读

- [LangGraph 多智能体协作实战：Supervisor、Worker 与状态交接怎么设计？](/ai/langgraph-supervisor-worker-handoff/)
- [LangGraph 状态隔离实战：thread_id、session_id、user_id 怎么设计？](/ai/langgraph-thread-session-state-isolation/)
- [CrewAI vs LangGraph：AI Agent 编排选型的 5 个核心考量](/ai/crewai-vs-langgraph-for-ai-workflows/)
- [MCP OAuth 认证实战：远程 MCP Server 为什么不能裸奔？](/ai/mcp-oauth-authentication/)
- [AI 专题入口：Agent、LangGraph、MCP 与 Workflow](/ai/)
