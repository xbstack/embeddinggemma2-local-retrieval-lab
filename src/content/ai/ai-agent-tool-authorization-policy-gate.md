---
title: "AI Agent 工具授权怎么做？Policy Gate、HITL 与逐调用权限控制"
description: AI Agent 工具授权：AI Agent 已经通过 Guardrails，为什么仍可能越权调用工具？本文用逐调用 Policy Gate 实验实现身份、租户、Scope、参数、目标地址与金额授权，并返回 ALLOW、REQUIRE_CONFIRM、STEP_UP 或 BLOCK。
seoTitle: AI Agent 工具授权怎么做？Policy Gate、HITL 与逐调用权限控制
seoDescription: AI Agent 工具授权：AI Agent 已经通过 Guardrails，为什么仍可能越权调用工具？本文用逐调用 Policy Gate 实验实现身份、租户、Scope、参数、目标地址与金额授权，并返回 ALLOW、REQUIRE_CONFIRM、STEP_UP 或 BLOCK。
geoSummary: "AI Agent 的工具可见性不等于本次调用已获授权。生产系统应在模型生成 Tool Call 后、真实 Tool Executor 前插入 Policy Gate，按身份、租户、Scope、会话、目标地址、金额和参数做确定性判断，并输出 ALLOW、REQUIRE_CONFIRM、STEP_UP 或 BLOCK，同时生成去敏审计记录。本文用七组本地确定性实验验证该边界，并解释它与 Guardrails 和 Human-in-the-loop 的分工。"
geoQuestions:
  - question: "AI Agent 的 Policy Gate 应该放在哪里？"
    answer: "应放在模型生成 Tool Call 之后、真实 Tool Executor 之前，对主体、租户、Scope、参数、目标和风险做确定性授权。"
  - question: "Guardrails 和工具授权有什么区别？"
    answer: "Guardrails主要检查输入输出和内容约束；工具授权判断当前主体是否有权在当前上下文执行这次具体调用。"
  - question: "为什么授权结果不能只有允许和拒绝？"
    answer: "高风险调用常需要人工确认或提升认证，因此生产策略通常至少需要 ALLOW、REQUIRE_CONFIRM、STEP_UP 和 BLOCK。"
category: ai
section: practice
contentType: case-study
subcategory: agent
series: "AI Agent 生产安全工程"
hideStructuredBlocks: true
draft: false
image: "../../assets/uploads/ai-agent-tool-authorization-policy-gate/01-agent-tool-authorization-cover-zh.webp"
imageAlt: "AI Agent 工具调用进入 Policy Gate 后分流为允许、人工确认、提升验证或阻断"
tags:
  - AI Agent
  - Tool Authorization
  - Policy Gate
  - RBAC
  - ABAC
  - Human-in-the-loop
  - Guardrails
  - Multi-tenant
  - Audit Log
  - Zero Trust
keywords: AI Agent 工具授权，AI Agent 权限控制，AI Agent Policy Gate，agent tool authorization，per-tool authorization middleware，AI Agent access control，Tool Call authorization，AI Agent RBAC，AI Agent ABAC，Agent STEP_UP
primaryKeyword: "AI Agent 工具授权"
targetHub: "AI Agent"
conversionTarget: "Policy Gate Demo、AI Agent Tool Use、XBSTACK AI Engineering Weekly"
evidenceStatus: complete
contentRole: main
tldr:
  - "模型能看到工具，只代表能力被暴露，不代表它生成的每一次调用都经过授权。"
  - "Guardrails主要校验内容和输入输出，HITL负责暂停并收集人工决定，Authorization负责判断这个主体在当前上下文是否有权执行这次具体调用。"
  - "Policy Gate必须位于模型输出和真实Tool Executor之间，不能只在前端按钮或Prompt中做限制。"
  - "本地实验覆盖7个案例：同租户读取允许、跨租户阻断、外发客户数据要求确认、高金额退款要求二次认证、删除操作要求确认、缺少Scope阻断、未知工具默认拒绝。"
  - "二元 allow/deny 不够。生产系统至少需要 ALLOW、REQUIRE_CONFIRM、STEP_UP 和 BLOCK，并把策略版本、原因、参数摘要与审计ID写入日志。"
  - "审批通过仍不等于副作用只能发生一次；退款、发信、部署和删除还要有幂等键、唯一账本和恢复策略。"
queries:
- AI Agent 工具权限怎么做？
- AI Agent 如何防止越权调用工具？
- AI Agent HITL 能替代权限控制吗？
- 如何实现 per-tool authorization middleware？
- AI Agent Policy Gate 应该放在哪里？
- AI Agent 工具授权是什么？
faqs:
  - question: "Guardrails 已经能阻断工具调用，为什么还需要 Authorization？"
    answer: "Guardrails可以检查参数内容、格式或敏感信息，但通常不会自动证明当前用户、租户和Scope有权执行这次调用。Authorization使用可信身份和业务策略做确定性权限判断。"
  - question: "把高风险工具全部设为人工审批是否足够？"
    answer: "不够。人工审批解决确认流程，但审批请求本身也必须先通过主体、租户、Scope、金额、目标地址和策略版本校验，否则会把明显越权的请求推给人工。"
  - question: "RBAC 是否足够控制 Agent 工具？"
    answer: "RBAC适合粗粒度角色，但逐调用授权通常还需要ABAC或策略条件，例如目标租户、退款金额、收件人域名、资源所有者、时间和认证强度。"
  - question: "审批通过后还需要幂等吗？"
    answer: "需要。队列重投、Worker重启或人工重复点击都可能让同一已批准调用执行多次。授权决定和副作用Exactly-once是两个独立问题。"
note: "本文的本地实验使用确定性 Python Policy Gate，没有接入特定 Agent SDK、商业授权引擎或真实企业身份系统。它验证策略分层与决策结果，不代表某个组织已经满足法律、监管或零信任合规要求。"
entities:
  - Policy Enforcement Point
  - Policy Decision Point
  - Tool Authorization
  - Guardrails
  - Human-in-the-loop
  - RBAC
  - ABAC
  - STEP_UP
  - Tenant Isolation
  - Audit Record
citations:
  - https://github.com/openai/openai-agents-python/issues/2868
  - https://openai.github.io/openai-agents-python/guardrails/
  - https://openai.github.io/openai-agents-python/human_in_the_loop/
topicGovernance:
  status: case-study
  intent: "回答 AI Agent 在模型已经选择工具并生成参数后，如何在真实执行前按身份、租户、Scope、参数、目标和风险做逐调用授权。"
  differentiation: "现有 AI Agent Tool Use 文章覆盖工具注册、Schema、风险分级、重试和审计；本文单独聚焦执行前 Policy Gate、Guardrails/HITL/Authorization 分工、非二元授权决策和七组可复跑策略案例，不扩写通用工具调用流程。"
  inventoryCheckedAt: '2026-07-26'
  inventoryReferences:
    - '/ai/ai-agent-tool-use/'
    - '/ai/ai-agent-security/'
    - '/ai/langgraph-human-in-the-loop-approval/'
    - '/ai/openai-agents-sdk-runstate-approval-resume/'
    - '/ai/mcp-server-production-governance/'

clusterHub: '/ai/ai-developer-operations-agents/'
audience:
  - "正在为高风险 Tool Call 增加逐次授权、人工审批和审计记录的 Agent 开发者。"
  - "需要区分身份认证、业务授权、Policy Gate 与 Human-in-the-loop 责任边界的架构师。"
  - "准备把工具权限从 Prompt 约束升级为可测试、可撤销策略的安全工程团队。"

createdAt: '2026-07-27'
lang: 'zh-CN'
route: '/ai/ai-agent-tool-authorization-policy-gate/'
canonical: 'https://www.xbstack.com/ai/ai-agent-tool-authorization-policy-gate/'
hub: 'agent'
translationKey: 'ai:ai-agent-tool-authorization-policy-gate'
translations:
  zh-CN: '/ai/ai-agent-tool-authorization-policy-gate/'
  en: '/en/ai/ai-agent-tool-authorization-policy-gate/'
translationStatus: 'published'
indexing: 'index'
---
# AI Agent 工具授权怎么做？Policy Gate、HITL 与逐调用权限控制

一个Agent能看到`send_email`、`query_customer`和`issue_refund`，只说明这些能力被暴露给模型，不代表模型生成的每一次调用都已经获得授权。最危险的误区，是把“工具已注册”“参数通过Schema”“内容没有触发Guardrail”和“用户有权执行”混成同一件事。

例如，模型生成一条格式完全合法的调用：查询客户资料，然后把结果发到外部邮箱。输入没有明显恶意词，参数也符合JSON Schema，工具本身属于当前Agent，但这次组合仍可能构成数据外泄。真正缺失的是一个执行前授权层：它要读取可信身份、租户、Scope、目标资源和具体参数，在Tool Executor真正产生副作用前做确定性判断。

先给结论：**Policy Gate应放在模型输出和真实工具执行之间，而不是只写进Prompt、前端确认框或工具描述。** 它至少返回`ALLOW`、`REQUIRE_CONFIRM`、`STEP_UP`和`BLOCK`，并为每次决定生成结构化、去敏、可追踪的审计记录。

## Guardrails、HITL 和 Authorization 解决的不是同一个问题

OpenAI Agents SDK官方文档已经提供Tool Guardrails和Human-in-the-loop。Tool Guardrails可以在函数工具执行前后检查调用，并阻断、替换结果或触发Tripwire；HITL可以把敏感调用暂停为Interruption，等待人工批准或拒绝。[Guardrails](https://openai.github.io/openai-agents-python/guardrails/) [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/)

但授权仍是独立问题。官方仓库的[Issue #2868](https://github.com/openai/openai-agents-python/issues/2868)提出了per-tool authorization middleware：按身份、角色、Scope、Rate Limit和Session上下文，在每次工具执行前做授权，并支持非二元决策和审计。

| 层 | 回答的问题 | 典型输入 | 典型结果 |
|---|---|---|---|
| Authentication | 调用者是谁 | Token、证书、Session | 已认证主体 |
| Capability Exposure | Agent能看到哪些工具 | Tool Registry、Tool Filter | 候选工具集合 |
| Guardrails | 内容或参数是否安全、合规、格式正确 | Prompt、arguments、Tool Result | 通过、阻断、替换、Tripwire |
| Authorization | 这个主体是否有权执行这次具体调用 | 身份、租户、Scope、资源、参数、策略 | ALLOW、BLOCK、STEP_UP、DEFER |
| HITL | 是否需要人对这次调用做决定 | 待审批Tool Call、上下文摘要 | 批准、拒绝、修改、过期 |
| Idempotency | 同一副作用是否只会落地一次 | 幂等键、业务账本 | 执行一次或复用结果 |

HITL可以承接`REQUIRE_CONFIRM`，但不能替代授权。跨租户读取、缺少Scope和未知工具通常应该直接`BLOCK`，不应浪费人工审批资源。

## Policy Gate应该放在哪里

推荐拓扑：

```text
User Request
  -> Agent / Model
  -> Proposed Tool Call + Arguments
  -> Policy Enforcement Point
       -> Identity verification
       -> Tenant and ownership check
       -> Scope / role check
       -> Argument and destination policy
       -> Risk and assurance evaluation
       -> ALLOW / REQUIRE_CONFIRM / STEP_UP / BLOCK
  -> Approval Service（按需）
  -> Idempotency Ledger
  -> Tool Executor
  -> Audit / Trace
```

![用户请求经过 AI Agent、工具调用提案和 Policy Gate 后，再由策略引擎返回四类授权决定](../../assets/uploads/ai-agent-tool-authorization-policy-gate/02-policy-gate-flow-zh.webp)

Policy Enforcement Point负责拦截，Policy Decision Point负责计算策略。小系统可以在同一个进程实现；多服务系统可以把策略放在Gateway或独立Policy Service中。但无论放哪里，都必须满足两个条件：

1. Tool Executor不能绕过它；
2. 身份和租户上下文不能由模型自己填写。

模型可以提出`target_tenant_id=tenant-b`，但可信租户必须来自经过验证的Session、服务Token或网关上下文。把模型生成的tenant_id当作授权依据，相当于让请求自己给自己签通行证。

## 本地实验：七组逐调用授权决策

实验目录：

```text
experiments/agent-tool-authorization-policy-gate/
```

实验实现一个确定性Policy Gate，输入包含：

```python
Principal(
    user_id="user-17",
    tenant_id="tenant-a",
    scopes={"customer:read", "email:send", "refund:write"},
    assurance_level=1,
)

ToolCall(
    name="issue_refund",
    arguments={"amount": 8000, "currency": "CNY"},
    target_tenant_id="tenant-a",
    risk_level="write",
)
```

七组结果全部通过：

| 案例 | 期望决定 | 结果 |
|---|---|---|
| 同租户客户读取 | ALLOW | 允许 |
| 跨租户客户读取 | BLOCK | 直接阻断 |
| 把客户数据发到外部邮箱 | REQUIRE_CONFIRM | 进入人工确认 |
| 低认证强度执行8000元退款 | STEP_UP | 要求更强认证 |
| 删除记录 | REQUIRE_CONFIRM | 进入人工确认 |
| 用户缺少退款Scope | BLOCK | 直接阻断 |
| 未注册的任意Shell工具 | BLOCK | 默认拒绝 |

实验还验证了审计日志不会原样保存邮件正文等敏感字段：

```json
{
  "decision": "REQUIRE_CONFIRM",
  "reason": "customer_data_to_external_recipient",
  "policy_id": "email-dlp-v1",
  "audit_id": "c3d46b41f63c84c50927",
  "redacted_arguments": {
    "recipient": "partner@external.test",
    "body": "[REDACTED]",
    "contains_customer_data": true
  }
}
```

该实验有5项单元测试和一个包含7组案例的`verification.json`。它没有接入真实Agent SDK，因此验证的是策略语义，不是SDK集成完整性。

## 为什么授权不能只有allow和deny

二元决策会把大量业务场景压扁。

![ALLOW、REQUIRE_CONFIRM、STEP_UP 与 BLOCK 四种授权结果及对应的工具调用执行路径](../../assets/uploads/ai-agent-tool-authorization-policy-gate/03-four-authorization-outcomes-zh.webp)

### ALLOW

适合低风险、同租户、Scope完整、资源所有权明确的只读操作。例如用户读取自己的订单状态。

### REQUIRE_CONFIRM

适合有副作用、可被人工理解和确认的调用。例如向外部地址发送客户数据、删除记录或中等金额退款。Policy Gate先证明请求不是明显越权，再交给HITL。

### STEP_UP

适合权限基本成立，但当前认证强度不足的操作。例如高金额退款需要重新输入密码、MFA、硬件密钥或管理员签名。它与普通人工审批不同：重点是提高调用者身份可信度。

### BLOCK

适合跨租户、缺少Scope、资源不属于调用者、未知工具、策略过期或目标被禁用的请求。阻断应该Fail Closed，不能因为策略服务超时就默认放行。

生产系统还可能需要`MODIFY`或`DEFER`，例如把退款金额限制到授权上限，或把调用排到业务窗口。但修改模型生成参数必须留下原始参数摘要和策略理由，避免审计时无法还原。

## RBAC、ABAC与参数级授权怎么组合

RBAC解决“客服角色能否使用退款工具”这类粗粒度问题；ABAC解决“这个客服能否为当前租户、当前订单、当前金额执行退款”这类上下文问题。

一个可执行策略通常同时检查：

- 主体：user_id、service_id、role；
- 租户：tenant_id、组织边界；
- Scope：`customer:read`、`refund:write`；
- 资源：owner、region、classification；
- 参数：amount、recipient、environment；
- 会话：认证强度、设备、风险评分；
- 时间：策略版本、有效期、维护窗口；
- 速率：单位时间内调用次数与金额累计。

![策略引擎综合身份、权限范围、租户归属、风险等级和目标参数生成可解释授权决定](../../assets/uploads/ai-agent-tool-authorization-policy-gate/05-policy-engine-inputs-zh.webp)

例如：

```text
IF tool = issue_refund
AND principal.scope includes refund:write
AND order.tenant_id = principal.tenant_id
AND amount <= 500
THEN ALLOW

IF amount > 500 AND amount <= 5000
THEN REQUIRE_CONFIRM

IF amount > 5000 AND assurance_level < 2
THEN STEP_UP
```

模型不参与这个判断。它可以解释为什么需要退款，但不能决定自己是否满足Scope和金额上限。

## 如何与OpenAI Agents SDK、LangGraph和MCP连接

### OpenAI Agents SDK

`needs_approval`和Tool Guardrails可以作为集成点：Policy Gate先计算决定；`ALLOW`继续执行，`BLOCK`返回拒绝，`REQUIRE_CONFIRM`触发Interruption，`STEP_UP`把请求送到二次认证流程。不要只返回一个布尔值，至少保留策略ID、原因和审计ID。

### LangGraph

在Tool Node前增加独立Policy Node。Policy Node读取可信Context和拟执行Tool Call，把决定写入Graph State。`REQUIRE_CONFIRM`路由到`interrupt()`，`BLOCK`路由到安全终止，`ALLOW`才进入Tool Executor。现有[LangGraph Human-in-the-loop审批流](/ai/langgraph-human-in-the-loop-approval/)解决暂停恢复，Policy Gate解决是否有资格进入审批。

### MCP

MCP Server暴露工具时，可以先通过Tool Filter减少可见能力，但远程Server仍应在每次`tools/call`中校验主体、租户和参数。Client端审批不能替代Server端授权，因为恶意或错误Client可能绕过UI直接调用。对于MCP生产边界，可继续参考[MCP Server生产治理](/ai/mcp-server-production-governance/)和[MCP安全最佳实践](/ai/mcp-security-best-practices/)。

## 审计记录至少保存什么

每次决定建议保存：

```text
audit_id
request_id / trace_id
principal_id
trusted_tenant_id
tool_name
tool_version
argument_digest
redacted_argument_summary
policy_id
policy_version
decision
reason
approval_id（如有）
assurance_level
created_at
executor_result_id（执行后）
```

![工具调用请求、策略决定、执行或拒绝结果最终写入可追踪审计日志](../../assets/uploads/ai-agent-tool-authorization-policy-gate/04-authorization-audit-trail-zh.webp)

不要把完整客户数据、Token和邮件正文直接塞进审计日志。保存去敏摘要和不可逆Hash，在需要调查时通过受控权限读取权威数据。

还要记录策略版本。审批等待两天后，权限规则可能已经变化；恢复执行时应重新校验，不能只因为旧审批写着“approved”就跳过当前策略。

## 授权通过后为什么仍需要幂等

Policy Gate回答“可不可以执行”，不回答“是否已经执行过”。队列重投、网络超时、Worker重启和人工重复点击都可能让同一已授权调用再次进入Executor。

有副作用的工具必须使用稳定幂等键：

```text
idempotency_key = hash(
  tenant_id,
  business_action,
  business_object_id,
  approved_call_id
)
```

Executor先查账本：已成功则返回原结果，处理中则拒绝并发，失败可按策略重试。授权、审批、幂等和审计是四个不同层级，缺一不可。

## 上线前最小检查清单

- Tool Executor是否只能通过Policy Gate访问；
- 身份和租户是否来自可信上下文；
- 未注册工具是否默认拒绝；
- 跨租户是否直接阻断；
- 高风险操作是否有`REQUIRE_CONFIRM`或`STEP_UP`；
- 策略服务失败时是否Fail Closed；
- 审计参数是否去敏；
- 审批恢复时是否重新校验策略版本；
- 写操作是否有幂等键；
- 是否测试了绕过前端直接调用Tool API；
- 是否有撤销、过期和紧急停用机制。

## 最终判断

Agent工具安全不能只靠“模型听话”。Tool Registry决定它能看到什么，Schema决定参数长什么样，Guardrails检查内容和格式，HITL收集人工决定，而Authorization证明当前主体是否有权执行这次具体调用。

真正可靠的边界，是模型只能提出动作，Policy Gate决定能否继续，Tool Executor只接受已经授权且具备幂等保护的请求。这样即使模型被提示词注入、理解错误或生成了越权参数，业务系统仍有一层确定性的执行控制。

继续阅读：[AI Agent Tool Use：工具注册、参数校验与审计](/ai/ai-agent-tool-use/)、[AI Agent Security](/ai/ai-agent-security/) 和 [OpenAI Agents SDK RunState审批恢复](/ai/openai-agents-sdk-runstate-approval-resume/)。
