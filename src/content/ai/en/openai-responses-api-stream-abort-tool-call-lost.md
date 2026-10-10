---
title: "OpenAI Responses API: Why Stream Abort Causes No tool call found for function call output"
description: "A function_call can be visible before it is durable in Conversation state. This guide explains the 400 No tool call found error, reconciliation, idempotency, and safe recovery."
seoTitle: "OpenAI No tool call found Error After Stream Abort"
seoDescription: "Fix OpenAI Responses API 400 No tool call found after a stream abort. Learn when call_id is durable, how to reconcile Conversation Items, and how to protect side effects."
geoSummary: "In the OpenAI Responses API, receiving response.output_item.added or response.function_call_arguments.done proves that the client observed a streamed function call; it does not prove that the call is already a durable Conversation item. If the client closes the stream before the response commits, a locally executed tool can become an orphaned side effect. Sending its function_call_output on the next turn can then fail with 400 No tool call found for function call output. The safe production rule is to reconcile Conversation Items before side-effecting execution, discard a call_id that is not present, regenerate the turn, and protect every external write with an application-owned idempotency key and result ledger."
category: ai
section: practice
contentType: error-guide
subcategory: openai-api
series: "OpenAI API Production Troubleshooting"
seriesOrder: 1
hideStructuredBlocks: true
draft: false
image: '../../../assets/covers/standardized/01-cover-en-9f3bcdf0-1200x630.webp'
imageAlt: "OpenAI Responses API streamed function_call breaks at Stream Abort before Conversation commit and returns 400 No tool call found"
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
keywords: OpenAI No tool call found for function call output, OpenAI Responses API stream abort, OpenAI function_call_output 400, OpenAI call_id not found, Responses API function call lost, OpenAI Conversation Items empty, response.output_item.added, response.function_call_arguments.done, OpenAI streaming tool call error, OpenAI Python SDK 3.19.2
primaryKeyword: "No tool call found for function call output"
targetHub: "AI Agent"
conversionTarget: "OpenAI Responses API Stream Abort Lab, AI Agent Tool Use Hub, XBSTACK AI Engineering Weekly"
evidenceStatus: partial
contentRole: main
tldr:
  - "A client receiving response.output_item.added or response.function_call_arguments.done does not prove that the function_call has been persisted to the Conversation."
  - "OpenAI Python SDK Issue #3561 reports that closing a stream after a function_call appears can leave Conversation Items empty, so the next function_call_output fails with 400 No tool call found."
  - "As of September 27, 2026, Issue #3561 remains open. openai-python 3.19.2 was released on September 23, but its public fixes do not mark #3561 as resolved. PR #3621 also remains open, and the September 8 discussion has shifted toward Responses-specific pending-tool-call reconciliation rather than treating generic Stream.close() behavior as a complete fix."
  - "For side-effecting tools, the safest gate is response completion plus an explicit Conversation Items check for the call_id before execution."
  - "After an abort or ambiguous disconnect, reconcile first. If the call_id is missing, discard it and start a new model turn instead of retrying the stale output."
  - "A committed call can still be delivered more than once, so payments, deployments, database writes, and notifications need a stable business idempotency key and result ledger."
queries:
  - How do I fix No tool call found for function call output?
  - Why is call_id missing after an OpenAI Responses API stream abort?
  - Can I execute a tool after response.output_item.added?
  - Does response.function_call_arguments.done mean the call is persisted?
  - Why are OpenAI Conversation Items empty after streaming?
  - How should I recover an aborted Responses API tool call?
faqs:
  - question: "What does No tool call found for function call output mean?"
    answer: "The function_call_output references a call_id that the server cannot find in the active conversation state. Common causes include using the wrong Conversation, mixing IDs between concurrent requests, or aborting a streamed response before the observed function_call became a durable Conversation item."
  - question: "Can I execute a tool as soon as response.output_item.added arrives?"
    answer: "Do not treat that event as a durable commit signal. For read-only tools, you may accept the risk. For payments, deployments, database writes, email, or permission changes, wait for completion and reconcile Conversation Items, or persist an application-owned execution intent first and enforce idempotency."
  - question: "Does response.function_call_arguments.done mean the function call was saved?"
    answer: "No. It means the argument stream is complete and can be parsed and validated. It does not promise that the function_call is already a durable item that a later function_call_output can reference."
  - question: "Should I retry the same function_call_output after an abort?"
    answer: "Read Conversation Items first. If the call_id exists, you can resume using the stored or idempotently produced result. If it does not exist, retrying the same output will keep failing. Discard the stale call_id and start a new model turn."
  - question: "Does upgrading to the latest openai Python SDK fix the issue?"
    answer: "Not based on current public evidence. As of September 27, 2026, Issue #3561 and PR #3621 are both still open, and the latest 3.19.2 release notes do not claim a fix. Test newer releases in an isolated regression matrix, but keep Conversation reconciliation, abort tests, and business idempotency safeguards."
  - question: "Does previous_response_id avoid this Conversation bug?"
    answer: "This article does not make that claim. The official report uses a Conversation, and no live API comparison was run here for previous_response_id. Regardless of the state mechanism, do not submit or execute side-effecting work until the server context has accepted the corresponding call."
note: "The OpenAI server behavior in this article is sourced from openai/openai-python Issue #3561 and official documentation. The local lab did not call the OpenAI API and did not independently reproduce the server bug. It uses a deterministic Python state model to test four application policies: complete then execute, execute then abort, reconcile before execute, and duplicate delivery with idempotency."
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
  intent: "Resolve the OpenAI Responses API failure where a streamed function_call is observed, the stream aborts, and the next function_call_output returns No tool call found."
  differentiation: "The existing OpenAI Agents SDK RunState article covers Tool Approval resume and Session persistence. This page focuses on the lower-level Responses API Conversation gap where a client has seen call_id but the function_call was not durably committed, and tests reconciliation, stale-ID discard, and business idempotency policies."
  inventoryCheckedAt: '2026-09-27'
  inventoryReferences:
    - '/en/ai/openai-agents-sdk-runstate-approval-resume/'
    - '/en/ai/langgraph-agent-error-recovery-retry-timeout/'
    - '/en/ai/ai-agent-tool-use/'
clusterHub: '/en/ai/'
audience:
  - "Python developers using OpenAI Responses API Conversations and function calling."
  - "Backend teams recovering tool calls after browser aborts, proxy timeouts, and ambiguous disconnects."
  - "Agent platform engineers responsible for side-effecting payments, deployments, database writes, and notifications."

createdAt: '2026-08-05'
lang: 'en'
route: '/en/ai/openai-responses-api-stream-abort-tool-call-lost/'
canonical: 'https://www.xbstack.com/en/ai/openai-responses-api-stream-abort-tool-call-lost/'
hub: 'agent'
translationKey: 'ai:openai-responses-api-stream-abort-tool-call-lost'
translations:
  zh-CN: '/ai/openai-responses-api-stream-abort-tool-call-lost/'
  en: '/en/ai/openai-responses-api-stream-abort-tool-call-lost/'
translationStatus: 'published'
translationSource: '/ai/openai-responses-api-stream-abort-tool-call-lost/'
translationSourceHash: 'd4c3920e0e3f0067bdcc1f286e34aad91db942b4628ead192be7c55790fee8ed'
indexing: 'index'
---
# OpenAI Responses API: Why Stream Abort Causes No tool call found for function call output

Here is the production conclusion first: **seeing a streamed `function_call` is not the same as having a durable call that the Conversation can reference later.** If a client closes the Responses API stream before the response commits, but the application already executes the tool, the next turn may reject the matching `function_call_output` with `400 No tool call found for function call output`. The error is bad; the orphaned side effect is worse. A payment, deployment, email, or database write may already exist even though the model conversation has no call record for it.

The fastest recovery is not to keep retrying the stale output. Read the Conversation Items first. If the matching `call_id` exists, reuse or produce the tool result idempotently and submit it. If the call is absent, treat the streamed call as uncommitted, discard that `call_id`, and generate a new turn. Separately, every external write needs an application-owned idempotency key, because durable model state does not provide business exactly-once execution.

The server-side behavior described here comes from OpenAI Python SDK Issue #3561. I did not use an unapproved production API key and do not present the local lab as an independent server reproduction. The lab makes the reported persistence boundary explicit and tests which recovery policies create or prevent orphaned side effects.

## 1. What the 400 Error Actually Means

The representative error is:

```text
400 No tool call found for function call output with call_id call_xxx.
```

This is not a missing Python function and not a JSON Schema validation failure. It is an association failure. A `function_call_output` says, in effect, “this value belongs to the tool call identified by `call_id`.” The server must be able to find that call in the current state before it can continue the model turn. If no matching call exists, accepting the output would attach data to an event that the conversation does not know happened.

Start by separating three failure classes. The first is wiring: the output was sent to the wrong Conversation, a stale ID was reused, or concurrent tabs crossed user state. The second is state-mechanism mismatch: one turn used a Conversation while another turn was built against a different context path. The third is the abort window covered here: the client observed a call in the stream, but the response never reached the state where that call was durably available in Conversation Items.

Issue #3561 documents that exact path. The reporter creates a Conversation, starts a streamed Responses request, receives a `function_call` in `response.output_item.added`, closes the stream, and then lists Conversation Items. The list is empty. The local tool is nevertheless executed. Submitting its output to the same Conversation on the next turn fails with the 400 error. The report uses Windows 10, Python 3.11.5, and `openai 2.45.0`.

## 2. Official Status as of September 27, 2026

Version numbers can be misleading here. As of September 27, 2026, the latest public OpenAI Python SDK release is `v3.19.2` from September 23. Its published bug-fix list does not identify #3561 as fixed; Issue #3561 remains open with the `bug` label, and the directly related PR #3621 is still open. The September 8 discussion on that PR also argues that generic stream closing is not a sufficient state repair: the more appropriate direction is Responses-specific retention and reconciliation of pending function calls.

The accurate statement therefore remains limited: there is a runnable report, an open candidate patch, and active design discussion, but there is still no merged-fix-plus-release evidence chain identifying a first fixed Python version. Test 3.19.2 or later in your own abort matrix, but do not remove the reconciliation gate merely because the package number is newer than 2.45.0.

If your failure is higher in the stack, compare this boundary with the [OpenAI Agents SDK RunState approval-resume lab](/en/ai/openai-agents-sdk-runstate-approval-resume/) and the [AI SDK 7 interruption and tool-recovery migration test](/en/ai/vercel-ai-sdk-7-migration-production/). Those pages cover framework-level resume and tool-loop state; this page stays focused on the lower-level Responses API Conversation commit gap.

Do not automatically downgrade either. The behavior crosses the client stream, the Responses service commit boundary, and Conversation persistence. A downgrade may not change server behavior and can reintroduce unrelated type, authentication, retry, or transport problems. A safer upgrade policy is to freeze the current production version, add a deterministic abort matrix, run the same matrix against a candidate release in an isolated OpenAI Project, and promote only when official status, live integration results, and side-effect counts agree.

The issue links to a related fix in the JavaScript Agents SDK, PR #1241, which reconciles streamed function calls when server-managed runs abort. That relationship makes the failure mode credible across adjacent stacks, but it is not proof that the Python Responses path is fixed. SDK runner behavior, API service behavior, and conversation storage must be verified independently.

## 3. Stream Visibility Is Not a Commit Token

Streaming exists to expose useful information before a full response completes. `response.output_item.added` tells the client that an output item has appeared in the current stream. `response.function_call_arguments.done` tells it that the function arguments are complete. Those events are useful for UI, validation, logging, and scheduling low-risk work. They are not, by themselves, a durable authorization token for an external side effect.

There are at least three distinct guarantees:

| Boundary | What you know | What you still do not know |
|---|---|---|
| Client observed an event | A call and `call_id` appeared in the stream | The Conversation durably contains the call |
| Response completed | The model turn reached a normal completion boundary | The tool will be delivered only once |
| Conversation reconciliation | The server lists the matching `function_call` | The business action is exactly once |

The unsafe implementation jumps from the first row directly to execution. That may be tolerable for a cacheable weather read. It is not acceptable for money movement, order creation, deployment, outbound email, access changes, or database mutation. If the stream aborts before commitment, the application has created an external fact without a model-state fact that can receive the result.

`call_id` is also not a sufficient business idempotency key. It is primarily the correlation ID between a model call and a tool output. A regenerated model turn can produce a new `call_id` for the same order or deployment. A stable key should come from the business intent, such as `tenant + operation + resource + desired_version`, with `call_id` stored as supporting evidence rather than the only uniqueness boundary.

```text
tenant-a:deploy:release-2026-08-05:call_xxx
```

## 4. The Local Lab and Its Evidence Boundary

The public lab is located at:

```text
experiments/openai-responses-stream-abort-tool-call-loss/
```

It uses only the Python standard library. `provisional_items` represents calls already exposed through stream events but not committed. `committed_items` represents calls that can be referenced by later outputs. Normal completion moves provisional calls into committed state. Abort discards them in the modeled failure path. Submitting an output for a missing call raises the same semantic error as the official report.

This is not a reverse-engineered copy of OpenAI internals. It does not prove how every production request is stored. Its purpose is narrower and honest: given the officially reported condition that the client can observe a call that the Conversation later lacks, which application policies are safe?

The lab fixes four scenarios:

1. complete the stream, confirm the call, then execute;
2. execute immediately after `output_item.added`, then abort;
3. abort, reconcile, and execute only if the call exists;
4. commit the call, deliver the tool job twice, and deduplicate with a business ledger.

It does not measure live API latency, token cost, browser behavior, HTTP/2 teardown, proxy buffering, model tool-selection quality, or the `previous_response_id` path. OpenAI behavior claims are sourced from official documentation and Issue #3561. Local results support the application control model only.

## 5. Four Scenarios, One Critical Invariant

The experiment writes the verified result to:

```text
experiments/openai-responses-stream-abort-tool-call-loss/results/verification.json
```

Four standard-library unit tests pass. The result matrix is:

| Scenario | Conversation items | Deliveries | External effects | Next turn |
|---|---|---:|---:|---|
| Complete, then execute | call + output | 1 | 1 | accepted |
| Execute on observed call, then abort | none | 1 | 1 | rejected with 400 |
| Abort, reconcile, then decide | none | 0 | 0 | stale call discarded |
| Committed call delivered twice with idempotency | call + output | 2 | 1 | accepted |

The second row is the failure that matters. The tool side effect count is already 1, while the Conversation contains no items. The output cannot be attached, so the next turn receives:

```text
No tool call found for function call output with call_id call_aborted.
```

For a read-only tool, generating another turn may be enough. For a charge or deployment, regeneration may produce a second valid call and a second side effect. Refusing every retry avoids duplication but can leave the user with a failed task after the action actually succeeded. That conflict cannot be solved with prompting; it requires an application truth store and idempotent execution.

The third scenario proves the conservative gate: after abort, reconcile first. If the call is missing, do not execute. The fourth scenario proves that reconciliation is not an exactly-once mechanism. A valid committed call can still be delivered repeatedly by a queue, manual retry, or worker recovery.

## 6. Fast Triage for Production Incidents

Do not begin by rewriting the prompt or randomly changing SDK versions. Follow the association chain.

### Step 1: Confirm the Conversation and call_id belong to the same turn

Capture complete correlation fields:

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

Verify that the output is being sent to the same Conversation that produced the call. Check concurrent tabs, retries, and tenant boundaries. Partial IDs are often insufficient when two live requests overlap.

### Step 2: Read Conversation Items

List Conversation Items and look for the exact `call_id`. If it is absent, stop submitting the output. Mark the application intent as `uncommitted` or `orphaned-intent` and route it to regeneration or manual reconciliation.

### Step 3: Identify how the stream ended

Distinguish normal completion, user stop, component unmount, `AbortController`, reverse-proxy timeout, mobile network loss, worker restart, and server crash. These paths can look identical to the UI while producing different backend states.

### Step 4: Check whether the tool already produced a side effect

Verify the external side effect independently. An empty Conversation does not mean the tool never ran. Check payment records, deployment IDs, message IDs, database constraints, or the application ledger.

### Step 5: Choose the recovery path

Use the reconciliation result and the external side-effect state together:

| Call in Conversation | Side effect | Recovery |
|---:|---:|---|
| yes | no | reserve idempotency key, execute, submit output |
| yes | yes | reuse stored result, submit output |
| no | no | discard stale call_id and generate a new turn |
| no | yes | do not execute again; compensate or reconcile manually, then rebuild model context |

The last row should not be hidden behind a generic retry loop. The business system has a fact that the model system lacks. Whether you send that fact back as a normal message, create an auditable recovery event, or require human review depends on the risk and regulatory context.

![Safe OpenAI Responses API recovery after a stream abort: reconcile Conversation Items, discard a missing call_id, or reserve a business idempotency key before execution](../../../assets/uploads/openai-responses-stream-abort-tool-call-lost-en/02-recovery-flow-en.svg)

## 7. A Production Tool-Call State Machine

A reliable orchestrator needs more than `pending/success/failed`:

```text
stream_observed
→ call_committed
→ execution_reserved
→ execution_succeeded
→ output_submitted
→ model_acknowledged
```

Failure branches need names as well:

```text
stream_aborted_before_commit
commit_unknown
execution_unknown
output_rejected
manual_reconciliation_required
```

`stream_observed` is safe for UI. It is not safe for a high-risk executor. `call_committed` means the Conversation reconciliation succeeded. `execution_reserved` means a unique business key has locked the action. `execution_succeeded` stores the immutable external result. `output_submitted` records delivery to the model, and `model_acknowledged` closes the complete workflow.

### What the state record should store

Persist this state in a transactional store, not only in traces. A minimal record should include the business key, tenant and user, Conversation and Response IDs, `call_id`, tool name, argument digest, every transition timestamp, abort reason, external result ID, result reference, retry count, and last error.

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

Use a unique constraint on the business idempotency key and another on `tenant + conversation_id + call_id`.

![Production tool-call state machine from stream_observed to model_acknowledged, with abort, unknown execution, and manual reconciliation branches](../../../assets/uploads/openai-responses-stream-abort-tool-call-lost-en/03-state-machine-en.svg)

The argument digest matters. Reusing one business key with different tool arguments should fail closed rather than silently return an old result. The external result ID should be a payment transaction, deployment ID, email Message ID, or other verifiable fact that a recovery worker can query after a crash.

Useful metrics include `stream_observed_without_commit_total`, `tool_execution_before_commit_total`, `function_call_output_not_found_total`, `reconciliation_latency_ms`, `duplicate_delivery_total`, `idempotency_reuse_total`, and `manual_reconciliation_total`. For high-risk tools, `tool_execution_before_commit_total` should remain zero. A falling 400 rate is not enough if errors are merely swallowed while side effects diverge.

## 8. A Safer Python Control Skeleton

The following is a control-flow example, not a complete OpenAI wrapper. The important separation is observed call, committed call, idempotency reservation, tool execution, and output submission:

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

    return client.responses.create(
        conversation=intent.conversation_id,
        input=[{
            "type": "function_call_output",
            "call_id": intent.call_id,
            "output": tool_result,
        }],
    )
```

Two crash windows remain. The process may fail after checking Conversation Items but before output submission. It may also fail after the external action succeeds but before the ledger is completed. The ledger therefore needs durable reservation, unique constraints, external result lookup, and result reuse. A recovery worker must query the ledger and external system before deciding to execute again.

High-risk tools should add authorization and human approval before `execution_reserved`. See [AI Agent tool authorization](/en/ai/ai-agent-tool-authorization-policy-gate/) for a per-call Policy Gate. If your application uses OpenAI Agents SDK approval interruptions, the separate [RunState resume and v0.19.3 persistence guide](/en/ai/openai-agents-sdk-runstate-approval-resume/) covers that layer.

## 9. Recovering Browser Disconnects and Proxy Timeouts

Production disconnects are rarely a clean `stream.close()`. A browser can background the tab, mobile connectivity can switch networks, a reverse proxy can close the downstream while the upstream is still working, and a server process can die after an event was received but before the log was flushed. The correct state is often “unknown,” not “failed.”

Persist one application record per streamed response:

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

After an ambiguous disconnect, a background reconciler should list Conversation Items and classify each observed call as `committed` or `missing`. Committed calls can enter the idempotent execution queue. Missing calls must be discarded and must not receive an output. If a frontend or another service already executed the tool, the business ledger must route the operation into compensation or manual reconciliation.

Do not give the browser direct ownership of high-risk execution. The browser should receive the stream and present approval. A backend orchestrator should persist the intent, reconcile Conversation state, execute the tool, and submit the output. Closing a page then becomes a presentation failure, not a payment or deployment consistency failure.

## 10. Regression Tests That Are Worth Keeping

A manual Ctrl-C test is not sufficient. The regression suite should actively abort at several boundaries and verify Conversation state, ledger state, and external effects together.

![OpenAI Responses API stream-abort regression matrix comparing abort points, Conversation persistence, side effects, stale output handling, and upgrade decisions](../../../assets/uploads/openai-responses-stream-abort-tool-call-lost-en/04-regression-matrix-en.svg)

Run commit-boundary tests after `response.output_item.added`, after `response.function_call_arguments.done`, after the final argument delta, immediately before completion, and after `response.completed`. Store the Response ID, call ID, final sequence number, and the Conversation Items result. Do not encode assumptions about which event commits; let the current API behavior populate the matrix.

Run side-effect-gate tests with a transactional fake payment, deployment table, or outbox. Before reconciliation, the count must be zero. After a committed call and first business-key reservation, it must be one. Deliver the same work two, five, or twenty times and assert that the external fact still appears once.

Inject process crashes in at least five windows:

```text
before ledger reservation
after reservation, before tool execution
after tool success, before ledger completion
after ledger completion, before function_call_output
after output submission, before final model response
```

Each window has a different recovery rule. Retry is safe before reservation. A stale reservation needs ownership and expiry logic. Success before ledger completion requires external lookup. A completed ledger result should be reused. A lost final model response should not execute the tool again.

Keep a version matrix in CI:

| SDK | Abort point | Call persisted | Side effects | Old output accepted | Decision |
|---|---|---:|---:|---:|---|
| production | after item added | measured | 0 | measured | safe/unsafe |
| production | after arguments done | measured | 0 | measured | safe/unsafe |
| production | after response completed | measured | 1 | measured | baseline |
| candidate | same three points | measured | invariant | measured | promote/block |

Unit tests should validate the application state machine on every commit. A live integration test should run when the SDK, streaming wrapper, proxy configuration, or cancellation logic changes. Use an isolated OpenAI Project, a low-cost model, a fake tool, and a strict spend limit. Save sanitized Conversation Items, package version, HTTP status, and timestamps as build artifacts.

The public XBSTACK lab deliberately stops before a live API call. A project adopting this pattern should add an environment-gated `live_integration_test.py` only after explicit credential authorization. That preserves the evidence boundary while making future official fixes comparable under the same test.

## 11. Common Mistakes and Final Decision

**Mistake: treating `function_call_arguments.done` as a commit.** It means argument streaming is complete, not that the Conversation can reference the call.

**Mistake: using `call_id` as the only exactly-once key.** A regenerated turn can produce a new call ID for the same order or deployment.

**Mistake: retrying the same output after every 400.** If the call is absent, retries do not create it.

**Mistake: assuming an empty Conversation means the tool did not execute.** External systems and the application ledger are the source of truth for side effects.

**Mistake: deleting safeguards because the current SDK is newer than the reported version.** As of August 26, 2026, Issue #3561 and candidate PR #3621 are still open, and no released Python version is identified as the fix.

The decision is simple:

> **A streamed tool call is observable data, not an execution credential. Confirm the server committed it, reserve a stable business idempotency key, execute through a backend orchestrator, and reconcile every ambiguous disconnect. If the call ID is missing, discard it.**

Read-only tools may accept a looser policy if duplicate cost is low. Payments, email, deployments, writes, and permission changes should not. They need the state machine, ledger, constraints, authorization, and recovery path described above. For broader timeout and retry design, see [AI Agent error recovery](/en/ai/langgraph-agent-error-recovery-retry-timeout/). For the full tool-call production boundary, continue with [AI Agent Tool Use](/en/ai/ai-agent-tool-use/).

## Frequently Asked Questions

### Why can the client have a call_id while Conversation Items are empty?

The stream event and durable state are different guarantees. The client can observe a provisional function call before the response reaches its persistence boundary. If the response is aborted first, the reported failure path leaves no Conversation item to reference later.

### Is waiting for response.completed enough?

It is safer than executing on the added event. For a high-risk tool, still reconcile Conversation Items before execution. Response completion addresses the model-turn boundary; an idempotency ledger addresses duplicate tool delivery.

### What if the tool executed but the call_id is missing?

Do not invent a tool call or continue submitting output to the missing ID. Record the real external result, prevent duplicate execution, and start a new auditable model turn or require human reconciliation. The appropriate recovery depends on whether the business allows the model to continue automatically.

### Is this the same as the OpenAI Agents SDK RunState persistence issue?

No. This page covers a Responses API Conversation that did not commit a streamed `function_call`. The RunState article covers approval resume and Session persistence in the Agents SDK. Both can create a mismatch between model state and external action, but the APIs and recovery boundaries differ.

### Does the local lab prove the OpenAI server implementation?

No. It tests application policies under the condition documented by the official issue. OpenAI server behavior, affected versions, and the first fixed release must come from official Issues, pull requests, and release notes. This page will update its version conclusion only when new official status and comparable verification are available.

---

**Experiment:** [OpenAI Responses API Stream Abort Tool Call Loss Lab](https://github.com/xbstack/my-blog-public/tree/main/experiments/openai-responses-stream-abort-tool-call-loss)

**Official sources:** [OpenAI Python SDK Issue #3561](https://github.com/openai/openai-python/issues/3561) · [Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling) · [Conversation State Guide](https://developers.openai.com/api/docs/guides/conversation-state)
