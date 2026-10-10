---
title: >-
  LangGraph Human-in-the-Loop in Practice: How to Build a Multi-Agent Approval
  Workflow
description: 'LangGraph Human-in-the-Loop in Practice: A hands-on guide to designing Human-in-the-Loop approval workflows in LangGraph multi-agent systems, covering interrupt-based execution.'
seoTitle: 'LangGraph Human-in-the-Loop: Interrupt & Resume'
seoDescription: 'LangGraph human-in-the-loop approval with interrupt(), Command(resume=...), typed inputs, checkpointers, and safe retries. Practical approval flow.'
geoSummary: 'LangGraph human-in-the-loop approval requires interrupt(), durable checkpoints and Command(resume=...) on the original thread; the paused node restarts on resume. Validate approval identity and tool parameters, prevent replayed side effects and handle edit/reject paths.'
primaryKeyword: LangGraph Human-in-the-Loop
keywords: LangGraph human in the loop, LangGraph interrupt approval, LangGraph Command resume, LangGraph response_schema, typed human input, TypedDict resume, Pydantic approval, checkpointer recovery, interrupt node replay, idempotent tool execution, agent approval workflow, Supervisor Worker authorization
queries:
- What is LangGraph Human-in-the-Loop?
- How does LangGraph Human-in-the-Loop work?
- How do I implement LangGraph Human-in-the-Loop?
- What are the common problems with LangGraph Human-in-the-Loop?
- When should I use LangGraph Human-in-the-Loop?
- How do I use LangGraph interrupt response_schema for structured human input?
category: ai
tags:
  - langgraph
  - human-in-the-loop
  - interrupt
  - checkpointer
  - ai-agent
  - multi-agent
  - approval-workflow
image: >-
  ../../../assets/covers/standardized/langgraph-human-in-the-loop-approval-bc4b4e1f-1200x630.webp
series: LangGraph Production-Grade Agent Orchestration in Practice
seriesOrder: 3
mood: focused
location: Guiyang
imageAlt: >-
  LangGraph Human-in-the-Loop in Practice: How to Build a Multi-Agent Approval
  Workflow
description_en: >-
  A hands-on guide to designing Human-in-the-Loop approval workflows in
  LangGraph multi-agent systems, covering interrupt-based execution pauses,
  manual approvals, rejection and rollback, state recovery, Checkpointer usage,
  and Supervisor/Worker collaboration. Helps developers build controllable,
  auditable, production-grade AI Agents.
imageAlt_en: >-
  LangGraph Human-in-the-Loop in Practice: How to Build a Multi-Agent Approval
  Workflow
citations:
  - https://github.com/langchain-ai/langgraph/releases/tag/1.2.12
  - https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py

clusterHub: '/en/ai/langgraph/'

createdAt: '2026-06-12'
lang: 'en'
route: '/en/ai/langgraph-human-in-the-loop-approval/'
canonical: 'https://www.xbstack.com/en/ai/langgraph-human-in-the-loop-approval/'
hub: 'langgraph'
translationKey: 'ai:langgraph-human-in-the-loop-approval'
translations:
  zh-CN: '/ai/langgraph-human-in-the-loop-approval/'
  en: '/en/ai/langgraph-human-in-the-loop-approval/'
translationStatus: 'published'
translationSource: '/ai/langgraph-human-in-the-loop-approval/'
translationSourceHash: '881ca6aa210bc3e945b4efb3d6db480911aa45e0da111897df6d4b5ce76a3502'
indexing: 'index'
---
## LangGraph human in the loop: approval and safe resume

LangGraph human-in-the-loop approval pauses a graph with `interrupt()`, persists the run with a checkpointer, and resumes on the **same thread** using `graph.invoke(Command(resume=decision), config)`. The **interrupted node restarts from its beginning**, so any writes or API calls before `interrupt()` may run again. Move irreversible operations to a separately authorized, idempotent executor node. This is a production design example, **not a claim of a new XBSTACK live integration test**.

## What This Guide Covers

- How to prevent AI agents from accidentally invoking high-risk, irreversible, or expensive tools when operating unattended in complex workflows.
- How to pause state, allow external modifications, and resume execution without breaking the Directed Acyclic Graph (DAG) state flow.
- How to define control boundaries between Supervisors, Workers, and human nodes in multi-agent collaboration systems.
- How the system should roll back state and safely terminate or replan when a human operator rejects an AI-proposed plan.
- How to design secure data routing in concurrent multi-user environments to prevent approval threads from cross-contamination or interleaving.

## Who This Guide Is For

- Backend developers who are already familiar with LangGraph basics and are attempting to apply agent systems to real-world business scenarios.
- System architects who need to integrate with internal OA, CRM, or ERP systems and have extremely high requirements for data security and operational auditability.
- Independent developers who have experienced model "hallucinations" leading to accidental invocations of send or delete tools, leaving them wary of automation.
- Developers looking to deeply understand the underlying mechanics of LangGraph state persistence, Checkpointers, and stateful graph orchestration.

## 1. Why Production-Grade Agents Cannot Be Fully Autonomous

## Where This Article Fits in the LangGraph Series

This article specifically addresses manual approval, pause/resume behavior, and isolation of high-risk tools. If you have not implemented state persistence, start with [LangGraph checkpointer selection](/en/ai/langgraph-checkpointer-memory-sqlite-redis/). If approval resumption mixes threads, revisit [thread_id, session_id, and user_id design](/en/ai/langgraph-thread-session-state-isolation/). If approval nodes need retry or degradation logic, review [LangGraph multi-agent failure recovery](/en/ai/langgraph-agent-error-recovery-retry-timeout/). To verify which code re-runs after `interrupt()` and why ordinary cancellation can lose streamed state, continue with [streaming, checkpoints, and cancellation recovery consistency](/en/ai/langgraph-cancel-run-streaming-checkpoint-state-loss/).

## Pre-Deployment Review Checklist

Before deploying the approval workflow, it is recommended to check off each item on the following list:

- Are high-risk tools disabled by default, requiring explicit Supervisor-triggered approval for execution?
- Is the payload returned to the frontend via `interrupt` properly sanitized and minimized?
- Are there clear branching logic for all four states: approved, rejected, modified, and timed out?
- Does the approval resume endpoint validate `user_id + thread_id + approval_id` rather than relying solely on a single token?
- Can approval records be replayed, including the original proposal, human modifications, final execution results, and the operator?

Consider a concrete **hypothetical** approval failure: an Analysis Worker misreads a vague request and proposes `write_database` to delete historical CRM records. If the worker also has database write credentials, a UI confirmation button cannot stop the tool call from happening first.

A production workflow therefore separates **proposal**, **human review**, **policy enforcement**, and **execution**. This example illustrates the risk; it is not a report of a production incident or a measured Mac Studio regression test.

High-risk actions in production environments are obvious:
- Sending commercial emails to key clients.
- Physical deletion or bulk write operations (SQL writes) on databases.
- Transfers, deductions, and invoice generation in financial systems.
- Execution of deployment scripts and service shutdowns in live production environments.
- Electronic signing of formal contracts or export of confidential information.

If these scenarios were left entirely to a large language model, a single probabilistic hallucination could result in catastrophic business losses for the enterprise. Therefore, a hard human-in-the-loop barrier must be established between reversible read-only analysis and irreversible write operations. This is the sole justification for Human-in-the-loop (HITL). It is not a concession to model limitations, but a mandatory practice in industrial-grade software engineering.

## 2. What Problem Does LangGraph Interrupt Solve?

In traditional workflow orchestration, implementing human approval typically requires breaking the integrity of the workflow. You often have to save the state to a temporary database, forcibly terminate the current process, and wait for manual confirmation on a backend interface. Once confirmed, you must use a new process and entry point to retrieve the data and reinitialize it. This approach is inelegant; it fragments workflow logic and makes tracking complex contexts exceptionally painful.

LangGraph’s native `interrupt` mechanism is designed to solve this problem elegantly. Its essence lies in allowing you to emit a suspension signal directly from any node during graph execution, halting the current Directed Acyclic Graph (DAG) run and returning a structured payload requiring human review to the caller.

At this point, the Graph pauses, but all its context, state variables, and call history do not disappear. Instead, they are safely persisted to a database via the underlying Checkpointer mechanism. When a human completes the approval or modifies relevant parameters externally, you simply send a resume signal carrying the same `thread_id`. Call `graph.invoke(Command(resume=decision), config)` with the same `thread_id` to continue. LangGraph **restarts the interrupted node from the start**; the call to `interrupt()` now returns the approved resume value. Any code before that call is re-executed, so place side effects after the pause or protect them with durable idempotency.

This is a durable pause in the graph workflow, **not** suspension at an arbitrary Python line. See the [official LangGraph interrupts guide](https://docs.langchain.com/oss/python/langgraph/interrupts) and the [interrupt source](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py).

### September 2026 update: use `interrupt(response_schema=...)` for typed resume input

LangGraph `1.2.12` added `response_schema` to `interrupt()`. This is more than a UI convenience: it puts the **interrupt contract emitted by the graph** and the **shape expected when a human resumes the graph** on the same API boundary.

For approvals involving refunds, publishing, deletion, or outbound messages, avoid accepting an unconstrained dictionary when the decision has a stable structure. A Pydantic model, `TypedDict`, or dataclass is converted to JSON Schema for the client and is also used to validate the resume value. A raw JSON Schema `dict` is surfaced to clients but is not itself used by LangGraph to validate the resume value.

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
            "message": "Review this refund",
            "proposed_action": state["proposed_action"],
        },
        response_schema=ApprovalResponse,
    )
    return {"approval_response": response}
```

A frontend or operations console can render a form from the same schema and reduce type drift across approve/edit/reason/amount fields. **Schema validation is still not authorization.** Eligibility to approve, amount limits, expiry, and whether the tool remains allowed after resume still belong to application policy and business state. See [AI Agent tool authorization and Policy Gate](/en/ai/ai-agent-tool-authorization-policy-gate/) for that layer.

## 3. How Do Supervisor and Worker Roles Divide Responsibilities in Approval Flows?

In Multi-Agent Systems, the biggest pitfall in designing approval flows is when Worker agents act independently. If a `MailWorker` responsible for sending emails triggers an interrupt within its own Tool, it becomes difficult to manage state and leads to high system coupling.

I believe a production-grade approval architecture should follow these division-of-labor principles:

The **Supervisor** agent acts as the central brain, managing global task risk assessment and routing logic. **Worker** agents serve as specialized execution tools, responsible only for generating structured proposals (`Proposed Action`). They should not possess direct access to any physical write tools.

For example, when a user requests "send last month's financial report to the client":

- The Supervisor receives the request and calls the `AnalyticsWorker` to organize data and draft the email.
- The `AnalyticsWorker` completes its work but does not directly call the `send_mail` tool. Instead, it returns standard structured data declaring the drafted content along with a flag indicating that human confirmation is required.
- Upon receiving the Worker's response, the Supervisor detects that `requires_approval` is `true` and triggers an interrupt suspension within the Supervisor's decision node.
- After external human approval, the Supervisor decides whether to dispatch the task to specific Executor tool nodes based on the outcome (approve/reject/modify) or return it to the Worker for replanning.

We can define a strict JSON contract for the Worker's proposal output:

```json
{
  "action_type": "send_email",
  "risk_level": "high",
  "target": "client@example.com",
  "summary": "Summary example",
  "proposed_payload": {
    "subject": "5AltStack",
    "body": "Body example"
  },
  "requires_approval": true
}
```

## 4. What Should an Approval Node Look Like?

An approval node is not merely a simple interactive popup at the underlying level; it is a data entity with a complete lifecycle, traceability, and auditability.

When defining an approval node in LangGraph, the node must expose the following structured data to external systems so that frontend pages or OA systems can correctly parse and render it:

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

On the backend, the evolution of approval status should follow a unidirectional, single-color track. Its initial state is inevitably pending; after human interaction, it branches into the following outcomes based on the action taken:

- approved: The review passes, and the data is directly dispatched to subsequent tool execution nodes.
- rejected: The review is denied, terminating the tool invocation. The rejection reason is written back to the graph state, allowing the Supervisor to decide whether to return it for rewriting or to report an error directly to the user.
- edited: The reviewer determines that the overall logic of the proposal is sound but contains minor flaws (e.g., typos in an email or an overly broad `limit` condition in SQL). They directly modify the data within the `proposed_payload` and then submit it for execution.
- expired/cancelled: The approval times out and becomes invalid, or it is manually revoked.

## 5. How to handle the three outcomes: approve, reject, and edit?

In LangGraph’s node logic, we need to leverage the graph’s state (State) to pass along human review feedback. Below are the core implementation mechanisms for handling these three decisions.

First, we define the global state structure for the graph. In `src/types/` or directly within the definition:

```python
from typing import TypedDict, Optional, Any

class AgentState(TypedDict):
    task: str
    proposed_action: Optional[dict]
    action_result: Optional[dict]
    approval_status: Optional[str] # approved | rejected | edited
    approval_response: Optional[Any]
```

When the graph execution reaches the critical approval node `prep_approval_node`, we trigger a graph suspension with `interrupt()`. The following fragments illustrate the API boundary; `authorization_service` and `idempotent_tool_executor` are **application-provided interfaces, not built-in LangGraph classes**. A real deployment must persist and implement them separately.

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
    # Do not call write/send tools before interrupt(): this node replays on resume.
    decision = interrupt(
        {"approval_id": action["approval_id"], "proposed_action": action},
        response_schema=ApprovalDecision,
    )
    # A separate backend handler must independently verify approver identity,
    # thread ownership, proposal hash, expiry and action scope.
    return {"approval_status": {
                "approve": "approved", "reject": "rejected", "edit": "edited"
            }[decision["decision"]],
            "approval_response": decision}
```

When the first invocation returns `__interrupt__`, the application shows the pending proposal. After the authenticated reviewer has been verified against the exact proposal, the application calls `graph.invoke(Command(resume=decision), config)` with the original thread config. The `interrupt()` call receives that decision on replay; `update_state` is **not** a substitute for the normal resume contract.

In the next node after resumption, ``execute_action_node``, we must implement defensive decision logic to handle branching:

```python
def execute_action_node(state: AgentState):
    status = state.get("approval_status")
    action = state.get("proposed_action") or {}
    decision = state.get("approval_response") or {}

    if status == "rejected":
        return {"action_result": {"status": "denied",
                "reason": decision.get("reason", "rejected")}}
    if status not in ("approved", "edited"):
        raise PermissionError("A verified human approval is required")
    if decision.get("approval_id") != action.get("approval_id"):
        raise PermissionError("Approval must match the exact proposal")

    payload = (decision.get("edited_payload") if status == "edited"
               else action.get("proposed_payload"))
    if not isinstance(payload, dict):
        raise ValueError("Approved tool arguments must be an object")
    # Application-defined durable policy/approval store: also verify identity,
    # ownership, original action hash, permissions, expiry and edited arguments.
    # The backend must atomically consume approval / enforce an idempotency key.
    authorization_service.verify_and_consume(action, decision, payload)
    result = idempotent_tool_executor.execute(
        action["tool_name"], payload, idempotency_key=action["approval_id"]
    )
    return {"action_result": result}
```

Through this logical design, the system achieves safe control over branch paths by updating `approval_status` without deconstructing the DAG structure.

## 6. What Role Does the Checkpointer Play in the Approval Workflow?

When discussing Human-in-the-loop (HITL) systems, many developers overlook the existence of the Checkpointer. In reality, without a reliable, persistent checkpointing system, any approval workflow would be rendered useless in a production environment.

Why is this the case? Because an `interrupt` only suspends the memory state of the current computation thread. If your Agent service runs in a container (such as Docker) or within a cloud Serverless architecture:
- By the time the approver opens the web interface for review, several hours may have passed.
- At that point, the original computation process may have already been physically destroyed due to timeouts or container restarts.
- Without a Checkpointer, all previous execution states, variables, and context would vanish along with the released memory.

The role of the Checkpointer is to automatically serialize the current graph state (State) and all checkpoint data generated after nodes complete their execution at the exact moment an interrupt is triggered, writing them to a physical database (such as Redis, SQLite, or PostgreSQL).

When external approval is completed and an update signal is sent, you simply specify the `thread_id`:
1. The system retrieves the historical snapshot from the moment of suspension from the database using the `thread_id`.
2. The deserialized graph state is reloaded into memory.
3. The externally written approval status is merged into the current state.
4. Execution **restarts from the start of the interrupted node**; the `interrupt()` call returns the supplied resume value, and subsequent nodes run according to the graph edges. Replay-sensitive work must be idempotent.

This means that the Checkpointer provides the ability to resurrect state across time, space, and physical processes. In production deployments, you should always use a stateful, persistent checkpointing mechanism.

## 7. How to Prevent Thread Contamination in Multi-User Approval Workflows?

If not designed carefully during development, multi-user high-concurrency scenarios are highly susceptible to severe security incidents known as "thread contamination" or "cross-wiring": User A approves an operation, but the application applies it to User B's `thread_id`, resulting in User B's funds being mistakenly transferred or their data being accidentally deleted.

To absolutely prevent such contamination incidents, the following variables must be strictly bound and cross-validated at the architectural design level:

```text
user_id + thread_id + run_id + approval_id
```

When persisting state and updating the graph, we must adhere to the following design ironclads:

- **Never** update global state using a generic `approval_id` without first validating the `thread_id`.
- Every `proposed_action` generated by an approval task must explicitly carry the current `thread_id` and `reviewer_id`.
- When writing approval results back via Webhook, the interface layer must first verify that the currently logged-in user has read/write permissions for the session associated with this `thread_id` through their active Session. Only after successful validation should the `state_update` write operation be executed.
- When saving logs, it is mandatory to write the operator's `reviewer_id` and the approval timestamp into the database snapshot as irrefutable evidence for subsequent compliance audits.

## 8. Which Tools Must Enter Approval?

To strike a delicate balance between security and work efficiency, we cannot apply a one-size-fits-all approval strategy to all tool calls. Doing so would overwhelm reviewers with countless minor approval pop-ups, eventually reducing the approval workflow to a mere formality (reviewers will blindly click "approve").

I believe the tool library should be divided into three risk tiers:

### 1. Low-Risk Tools Allowed for Automatic Execution (No Side Effects, Read-Only)
These tools typically do not alter any system state; they only perform retrieval and analysis. They can be fully open to the AI without requiring human confirmation.
- `read_file` (Read file)
- `search_knowledge_base` (Search knowledge base)
- `call_weather_api` (Weather query)
- `text_classification` (Classification)
- `format_data` (Formatting)

### 2. Medium-Risk Tools Requiring Approval (Minor Side Effects, Reversible)
These tools generate external behaviors or modify local business systems, but remain within the scope of being overridden or rolled back through subsequent actions.
- `update_crm_contact` (Update contact phone number)
- `create_draft_article` (Create article draft)
- `send_internal_slack_message` (Send internal notification)
- `calculate_compound_interest` (Complex financial value estimation and write)

### 3. High-Risk Tools Requiring Mandatory Approval (Irreversible, High Cost)
Once executed, these cause irreversible changes to the physical world, corporate assets, or core data. They must undergo strict verification and confirmation at the system level by a human.
- `delete_database_record` (Physical deletion of data)
- `execute_raw_sql` (Execute raw SQL statements)
- `send_client_email` (Directly send emails to external clients)
- `transfer_funds` (Financial transfers)
- `publish_to_production` (Deploy code or data to production)

## 9. Common Mistakes

When developing LangGraph human-in-the-loop approval workflows, these failure modes deserve explicit regression tests:

### Common Pitfall 1: Frontend Interception Only, Backend Tool APIs Left Exposed
This is the most common and dangerous security vulnerability. Developers merely add a frontend popup asking users to click "Confirm," but the backend implementation of the graph does not validate the `approval_status` when executing the tool. It executes immediately upon receiving the model's call instruction. If network fluctuations occur, the frontend refreshes, or someone bypasses the UI with direct API requests, the safety net instantly fails.
- **Solution:** At the actual Python/Node code execution layer of the Tool, a secondary assertion check must be enforced.

### Common Pitfall 2: Worker Agents Directly Possess Write Tool Permissions
In some designs, the Worker node directly includes `send_mail_tool` in its available tools. This allows the Worker to bypass the Supervisor's risk-control routing and self-complete the call during execution.
- **Solution:** Workers should only output structured Action proposals. These must be centrally handed over to a Supervisor with risk-control logic or a dedicated approval router for filtering and distribution.

### Common Pitfall 3: Throwing Non-Persistent Exceptions When Triggering Interrupts

If the underlying persistence library is not correctly configured, a resumed approval can fail to find its prior state after process restart or multi-pod handoff. The following is an **illustrative diagnostic message, not a recorded LangGraph stack trace or a guaranteed exception class**:

```text
Illustrative: no checkpoint found for thread_id=th_003, checkpoint_id=cp_9a2f1
```

- Solution: Ensure that when initializing the Graph in both development and production environments, you pass a persistent instance of ``SqliteSaver``, ``PostgresSaver``, or ``RedisSaver``, and that the `thread_id` generation rule is globally unique.

## 10. Pre-deployment Checklist

Before merging your multi-agent approval system code and deploying it to production, perform a final physical check against the following list:

- [ ] Have the tools been categorized into three tiers: read-only, reversible write, and high-risk write?
- [ ] [ Have all high-risk tools implemented a hardcoded assertion for `state.get("approval_status") == "approved"` in their backend execution code?
- [ ] [ Is the interrupt logic bound to persistent storage (Checkpointer) and capable of state recovery across Pods?
- [ ] [ Is the `thread_id` strictly validated against the user session `user_id` to prevent privilege escalation vulnerabilities?
- [ ] [ Does the approval state machine fully cover the three workflows: approved, rejected, and manually edited?
- [ ] [ After a manual rejection, can the graph safely fall back to the Supervisor planning node or output a safe failure result, rather than getting stuck?
- [ ] [ Has an audit log table been designed in the database to record `reviewer_id`, `approved_at`, and `request_payload`?
- [ ] [ During concurrency testing, does triggering approvals simultaneously for multiple users cause state pollution or thread cross-contamination?

## FAQ

### What is the fundamental difference between LangGraph's Human-in-the-loop and a standard frontend confirmation dialog?
A standard dialog only blocks at the interaction layer. If the user refreshes the page or the network disconnects, the state is lost, and the process can even be bypassed entirely. LangGraph's Human-in-the-loop pushes the pause and resume capabilities down to the underlying graph state engine and Checkpoint. Even if the service restarts due to a power outage, it can perfectly recover via the `thread_id`. This represents a protocol-level and engine-level block.

### Does a paused approval consume LLM tokens continuously?
An interrupted LangGraph run does not keep calling a model simply because it is waiting for an approver. However, **separate background jobs, polling, external tools and retries may still incur costs**. A durable checkpointer preserves the resumable state; the correct continuation is `graph.invoke(Command(resume=decision), config)` on the original thread. The interrupted node begins again from its start, so budget for re-execution and enforce idempotency before any external write.

### How should an edited approval payload reach the executor?
Return a typed `Command(resume={"decision": "edit", "approval_id": "...", "reason": "...", "edited_payload": {...}})` on the **original thread config**. The approval node returns this decision into graph state; the executor must revalidate the edited arguments against authorization rules, compare the approval with the original proposed action, and enforce a durable idempotency key. `update_state` is a separate state-management API, not the normal interrupt-resume call.

## Series Navigation

LangGraph Production-Grade Agent Orchestration in Practice Series:

- [Part 1: Supervisor / Worker](/en/ai/langgraph-supervisor-worker-handoff/)
- [Part 2: State Isolation](/en/ai/langgraph-thread-session-state-isolation/)
- [Part 3: Human-in-the-loop](/en/ai/langgraph-human-in-the-loop-approval/)
- [Part 4: Failure Recovery](/en/ai/langgraph-agent-error-recovery-retry-timeout/)
- [Part 5: Observability](/en/ai/langgraph-observability-agent-trace/)
- [Part 6: Checkpointer](/en/ai/langgraph-checkpointer-memory-sqlite-redis/)
- [Part 7: Subgraph](/en/ai/langgraph-subgraph-worker-state/)

## Continue Reading

- [LangGraph Multi-Agent Collaboration: Supervisor, Worker, and State Handoff](/en/ai/langgraph-supervisor-worker-handoff/)
- [LangGraph State Isolation: thread_id, session_id, and user_id](/en/ai/langgraph-thread-session-state-isolation/)
- [CrewAI vs LangGraph: 5 Key Considerations for AI Agent Orchestration](/en/ai/crewai-vs-langgraph-for-ai-workflows/)
- [MCP OAuth Authentication: Why Remote MCP Servers Need Authorization](/en/ai/mcp-oauth-authentication/)
- [AI Topic Hub: Agents, LangGraph, MCP, and Workflows](/en/ai/)
