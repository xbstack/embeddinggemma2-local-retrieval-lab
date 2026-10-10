---
title: >-
  LangGraph Checkpointer in Practice: How to Choose Between MemorySaver, SQLite,
  and Redis
description: 'LangGraph Checkpointer in Practice: A practical guide to selecting a state persistence strategy for LangGraph Checkpointers.'
seoTitle: LangGraph Checkpointer in Practice
seoDescription: 'Choose LangGraph Checkpointer storage for production: compare InMemorySaver, SQLite, Redis and Postgres for persistence, concurrency, recovery, HITL, encryption and deployment.'
geoSummary: 'LangGraph Checkpointer in Practice: A practical guide to selecting a state persistence strategy for LangGraph Checkpointers. - What core data does the LangGraph Checkpointer actually save in the state machine? - Can MemorySaver (or InMemorySaver) truly be used in production environments?'
primaryKeyword: LangGraph Checkpointer
keywords: LangGraph Checkpointer, langgraph, checkpointer, sqlite, redis, state-persistence, ai-agent, How to Choose Between MemorySaver, and Redis, LangGraph Checkpointer in Practice, SqliteStore.batch, langgraph-checkpoint-sqlite, partial commit, transaction rollback
queries:
- How does LangGraph Checkpointer perform in real projects?
- What are the strengths and limitations of LangGraph Checkpointer?
- Is LangGraph Checkpointer worth using?
- Who should use LangGraph Checkpointer?
- What should I test before adopting LangGraph Checkpointer?
- Why can LangGraph SqliteStore.batch partially commit after an exception?
- Is langgraph-checkpoint-sqlite 3.1.1 batch atomic?
category: ai
subcategory: langgraph
tags:
  - langgraph
  - checkpointer
  - sqlite
  - redis
  - state-persistence
  - ai-agent
slug: langgraph-checkpointer-memory-sqlite-redis
series: Production-Grade Agent Orchestration with LangGraph
series_order: 6
image: >-
  ../../../assets/covers/standardized/langgraph-checkpointer-memory-sqlite-redis-4427180a-1200x630.webp
imageAlt: >-
  LangGraph Checkpointer in Practice: How to Choose Between MemorySaver, SQLite,
  and Redis
description_en: >-
  A practical guide to selecting a state persistence strategy for LangGraph
  Checkpointers. Covers use cases, pros and cons, thread_id design, state
  recovery, Human-in-the-loop workflows, failure recovery, and production
  deployment recommendations for MemorySaver/InMemorySaver, SQLite, Redis, and
  Postgres.
imageAlt_en: >-
  LangGraph Checkpointer in Practice: How to Choose Between MemorySaver, SQLite,
  and Redis
clusterHub: '/en/ai/langgraph/'

createdAt: '2026-06-15'
lang: 'en'
route: '/en/ai/langgraph-checkpointer-memory-sqlite-redis/'
canonical: 'https://www.xbstack.com/en/ai/langgraph-checkpointer-memory-sqlite-redis/'
hub: 'langgraph'
translationKey: 'ai:langgraph-checkpointer-memory-sqlite-redis'
translations:
  zh-CN: '/ai/langgraph-checkpointer-memory-sqlite-redis/'
  en: '/en/ai/langgraph-checkpointer-memory-sqlite-redis/'
translationStatus: 'published'
translationSource: '/ai/langgraph-checkpointer-memory-sqlite-redis/'
translationSourceHash: '06e7e2594c2e2c7d82def1ddbfd6b923fa72447d6207544b37345085bcd6a902'
indexing: 'index'
---
**2026-10-09 documentation review:** LangGraph's Python interrupt documentation covers `interrupt(response_schema=...)` on LangGraph 1.2.12 and later, and `Command(resume=...)` on the original `thread_id`. This is a documentation and API-contract check—not a fresh benchmark of all saver backends. The SQLite Store partial-commit case below remains pinned to the originally tested `langgraph-checkpoint-sqlite==3.1.1`; do not generalize it to a newly released build without rerunning the test. See [official interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) and [official persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

## LangGraph Checkpointer: durable state is not exactly-once tool execution

For local prototypes, `InMemorySaver` is convenient but dies with the process. SQLite can work on a single host with disciplined concurrency. Multi-worker production deployments need a shared durable saver plus a tested restart/recovery path. **Interrupt resumption restarts the interrupted node**, so a checkpoint does not make a payment, email, or database write exactly-once: the business executor must enforce idempotency. See the [official persistence guide](https://docs.langchain.com/oss/python/langgraph/persistence) and the [human approval walkthrough](/en/ai/langgraph-human-in-the-loop-approval/).

## What This Guide Covers

- What core data does the LangGraph Checkpointer actually save in the state machine?
- Can MemorySaver (or InMemorySaver) truly be used in production environments?
- For what kind of projects is the SQLite Checkpointer suitable, and what are its concurrency and read/write limitations?
- In which high-concurrency scenarios is the Redis Checkpointer appropriate, and what prerequisite Redis modules are required?
- What is the underlying physical addressing relationship between `thread_id` and the Checkpointer?
- Why is the Checkpointer indispensable for Human-in-the-loop workflows and failure recovery mechanisms?
- How should individual developers and professional teams approach Checkpointer architecture selection at different stages of their business?

---

## Who This Guide Is For

- Backend and full-stack engineers who have successfully run local LangGraph demos and are preparing to deploy Agent services into production.
- AI system architects designing multi-turn conversations, approval workflows, exception retries, or long-running asynchronous execution tasks.
- Developers struggling to choose between MemorySaver, SQLite, Redis, and Postgres due to uncertainty about their respective pros, cons, and applicable boundaries.
- Designers planning highly available storage architectures for AI Agents on platforms like Synology NAS, lightweight VPSs, or Kubernetes container clouds.

---

## 1. A Beginner's Hard-Nosed Practical Observation

In production environments with multiple instances or high concurrency, the state persistence strategy for an Agent is the critical dividing line that determines whether a system survives.

**Failure scenario (illustrative, not an incident reported by XBSTACK):** a container running financial audit workflows is terminated by an out-of-memory condition. After restart, an `InMemorySaver` instance starts empty, so previously interrupted approval threads cannot be reconstructed from the old process's memory. A restart policy does not turn volatile checkpoints into durable state.

In a production deployment, a persistent saver shared across the relevant workers, isolated `thread_id` values, recoverable checkpoint storage and a replay-safe tool execution policy all matter. Persistence alone cannot guarantee recovery of a partially completed external payment or database write; those need idempotency and reconciliation.

---

## 2. The Underlying Physical Mechanisms and State Anatomy of Checkpointers

## Where This Article Fits in the LangGraph Series

This article specifically addresses checkpointer selection and state persistence. If you have not designed your ID hierarchy, start with [thread_id, session_id, and user_id design](/en/ai/langgraph-thread-session-state-isolation/). For approval pauses and resumption, continue with [LangGraph human-in-the-loop approval workflows](/en/ai/langgraph-human-in-the-loop-approval/). For recovery after tool failures, see [tool errors, timeouts, and retry strategies](/en/ai/langgraph-agent-error-recovery-retry-timeout/). If users can see streamed content that disappears after cancellation or refresh, read [streaming, checkpoints, and cancellation recovery consistency](/en/ai/langgraph-cancel-run-streaming-checkpoint-state-loss/).

Do not choose a checkpointer by storage price alone. A cheaper state layer that increases failed recovery, duplicate execution, or manual compensation can raise the cost of each successful task. The [OpenAI outcome-based pricing and AI Agent ROI analysis](/en/ai/openai-outcome-based-pricing-ai-agent-roi/) puts persistence back into the full Agent cost model: checkpoint storage is part of Agent Cost, while the optimization target is task success and cost per verified outcome.

## Practical Review Checklist

Before pushing the Checkpointer to production, complete at least these 5 checks:

- After a container restart, can the same `thread_id` be restored to its last checkpoint, and can an interrupted node be safely **re-executed from the beginning** using `Command(resume=...)`?
- Will multiple concurrent tasks from the same user write to different `thread_id` instances?
- Have the backup and recovery commands for SQLite / Redis / Postgres actually been tested in practice?
- If a Human-in-the-loop suspension exceeds 24 hours, can the state still be recovered?
- Can error logs simultaneously pinpoint `thread_id`, the checkpoint ID, the current node, and the cause of failure?

The Checkpointer captures snapshots of the directed graph at the end of each node's execution, serializes them, and binds them to a unique thread_id. This provides the physical foundation for Agent task retries, time travel, and human approval.

We need to make one thing clear: the Checkpointer does not solve ordinary caching problems; it solves durable execution. When we pass a checkpointer during Graph compilation, LangGraph automatically intercepts and saves the current graph state snapshot after every step of the graph's execution (i.e., after each node finishes running).

These snapshots are organized by thread_id. A thread is like a branch in Git, recording all historical commits (checkpoints) for that thread. Each checkpoint contains not only the current state dictionary but also extremely rich physical metadata.

For orientation, the following is **an illustrative schema, not raw output captured from a specific LangGraph serializer or a verified production run**. The actual stored fields vary by saver implementation and version:

```json
{
  "thread_id": "usr_9982:billing_audit:task_20260615_001",
  "checkpoint_id": "1ef23b8f-89a1-6a20-b001-c91823abf100",
  "current_node": "agent_review_node",
  "state": {
    "messages": [
      {
        "type": "human",
        "content": "5 invoice"
      },
      {
        "type": "ai",
        "content": "",
        "tool_calls": [
          {
            "name": "fetch_invoices",
            "args": {
              "month": "2026-05"
            },
            "id": "call_tx_9982"
          }
        ]
      }
    ],
    "invoice_list": [],
    "audit_status": "pending_fetch"
  },
  "pending_action": null,
  "error_state": null,
  "metadata": {
    "source": "loop",
    "step": 2,
    "run_id": "run_0f8e91cd-89b2-44a1-b873-120aef2b001f"
  },
  "created_at": "2026-06-15T10:28:29Z"
}
```

As the structure above shows, the Checkpointer records:

- **The specific node in the current graph**: This tells the state machine which Node to start executing from when it is next awakened.
- **Complete State data**: Including conversation message history (the `messages` list) and custom business state fields (such as `invoice_list`).
- **Error states and pending actions**: If a node throws an exception during execution, or if an `interrupt_before` breakpoint is configured before a node, this records the pending tool calls or exception information.
- **Metadata**: Contains step counts, `run_id` for individual runs, etc., for observability path analysis.

With this foundation, when an Agent is interrupted by network failures, API timeouts, or container restarts, the same `thread_id` can retrieve a persisted checkpoint and resume from a framework-supported boundary. That can avoid re-running earlier graph nodes, but it does not automatically reconcile external side effects; the application still needs idempotency, result lookup, or compensation for tools that may already have completed.

---

## 3. MemorySaver / InMemorySaver: Suitable for Demos, Not for Production

The sole value of memory-based Checkpointers is zero-configuration out-of-the-box usability. Because they lack persistent storage, any process restart or multi-instance load balancing will cause the state to vanish instantly.

In the Python documentation, the official examples commonly use `InMemorySaver`; in the JavaScript/TypeScript version, the corresponding name is `MemorySaver`. Their physical essence is identical: they maintain a `dict` or `Map` in process memory to read and write checkpoint objects.

When used for local development, running unit tests, or quickly validating a state machine branch logic, their usage is extremely straightforward:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

memory_checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=memory_checkpointer)

config = {"configurable": {"thread_id": "local_demo_thread"}}
result = graph.invoke({"input": "task"}, config=config)
```

However, the in-memory checkpointer has three fatal physical flaws that make it absolutely unsuitable for production deployment:

1. Process-resident limitations: If your application is deployed on a Kubernetes cluster, managed by PM2, or hosted on a Serverless platform like Vercel, new processes start empty during container scaling, node drift, or automatic restarts after crashes. Once user requests are routed to a new instance by the load balancer, the preceding state is lost, resulting in errors.

2. Memory capacity exhaustion (OOM) risk: As conversation turns and concurrent users accumulate, the checkpoint list stored in process memory grows indefinitely. The message history within each checkpoint consumes significant memory, which can directly cause the application process to be forcibly killed by the system due to memory leaks or exhaustion.

3. Inability to persistently audit state: Once the service undergoes a hot update or a normal maintenance restart, all historical execution chains physically evaporate, making them unavailable for subsequent product data tracing and compliance auditing.

Therefore, unless you are writing single-machine scripts or running local pytest tests, you should physically remove `InMemorySaver` from your dependencies at the very beginning of the project's inception.

---

## 4. SQLite Checkpointer: A Low-Cost Choice for Personal Projects and Single-Machine Deployments

SQLite provides zero-deployment-cost disk-level persistence with support for both synchronous and asynchronous drivers, making it an ideal choice for single-machine applications and small-scale tool sites, though it requires handling database lock barriers under concurrent writes.

If your Agent service is currently a tool-type site developed by a single person, or if it is deployed on an independent cloud server or even a private NAS device, SQLite is an extremely cost-effective choice. It ensures that state remains intact after process restarts without requiring you to additionally manage complex database clusters.

LangGraph officially provides a standalone extension package `langgraph-checkpoint-sqlite` to support SQLite persistence. It includes the synchronous `SqliteSaver` and the asynchronous `AsyncSqliteSaver` implemented based on `aiosqlite`.

Let's look at a practical code example of standard initialization for `AsyncSqliteSaver` in an asynchronous application (such as FastAPI):

```python
import asyncio
import os
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph

DB_PATH = "data/agent_checkpoints.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

async def run_agent_workflow():
    async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        await checkpointer.asetup()

        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "sqlite_user_task_4451"}}

        async for event in graph.astream(
            {"messages": [("user", "Analyze the structure of this document")]},
            config=config,
            stream_mode="values"
        ):
            print(event)

asyncio.run(run_agent_workflow())
```

When using SQLite, you need to be aware of the following two common pitfalls:

- **SQLite write contention**: SQLite has a single-writer concurrency boundary. Use a busy timeout, short transactions and, when appropriate, WAL mode to improve concurrent readers and writer coordination; measure actual contention under your workload. **`check_same_thread=False` only changes Python's thread-affinity check—it does not cure database locks.**
- **Checkpoint retention and size**: Define retention and pruning rules for checkpoints and writes, back up before destructive maintenance, and monitor the database file and free space. `VACUUM` can reclaim file space after data is deleted but is **not** a replacement for retention management and should not be scheduled blindly during active writes.

### 2026-08-12 update: `SqliteStore.batch()` can still partially commit after it raises

A newly confirmed transaction-boundary issue belongs next to the SQLite persistence discussion. **This does not mean every `SqliteSaver` checkpoint write partially commits. The affected API in this reproduction is `langgraph.store.sqlite.SqliteStore.batch()`, a Store API shipped in the same `langgraph-checkpoint-sqlite` package.** If an application uses SQLite both for checkpointing and as a LangGraph Store, and relies on `batch()` as an all-or-nothing boundary, that assumption needs its own regression test.

LangGraph issue [#8590](https://github.com/langchain-ai/langgraph/issues/8590), opened on August 11, 2026, reports that an earlier mutation in a Store batch can remain persisted when a later operation raises. The observable case in the issue refreshes TTL through `GetOp(..., refresh_ttl=True)` and then triggers a serialization `TypeError` with an invalid `PutOp`. The batch fails, but the earlier TTL refresh is not rolled back.

On August 12, I reran the synchronous minimal reproduction with `langgraph-checkpoint-sqlite==3.1.1`. It uses an in-memory SQLite database and makes no model, API, or external database calls. The core batch is only:

```python
store.batch([
    GetOp(("test",), "key", refresh_ttl=True),
    PutOp(("test",), "invalid", {"value": object()}),
])
```

After pinning the original `expires_at`, the recorded output was:

```text
langgraph-checkpoint-sqlite 3.1.1
caught TypeError
original_expiration 2000-01-01 00:00:00
actual_expiration 2026-08-12 03:26:59
partial_commit_reproduced True
```

The exact refreshed timestamp is not the important part. **The batch raised `TypeError`, yet the earlier TTL mutation remained in the database.** On this version, `SqliteStore.batch()` therefore should not be treated as an atomic transaction boundary where any failure guarantees rollback of all earlier operations.

The upstream issue points to the synchronous and asynchronous SQLite Store `_cursor()` contexts committing unconditionally in `finally`. The proposed repair is to commit only on normal exit and roll back on any `BaseException` before re-raising it. When I rechecked the issue on August 12, it was still open and showed no linked pull request or released fix.

Until a fixed release passes the same regression test, the production boundary should stay conservative: do not place failure-sensitive writes behind an assumption that the current `batch()` is atomic; pre-validate fallible inputs where possible; and avoid mixing an earlier mutation with later operations that may raise when the business requirement is truly all-or-nothing. For this specific TTL reproduction, avoiding `refresh_on_read` inside a critical batch can avoid the demonstrated mutation path when the product semantics allow it, but that is a narrow workaround, not a general transaction fix.

XBSTACK has published the reproduction at [xbstack/langgraph-sqlite-partial-commit-repro](https://github.com/xbstack/langgraph-sqlite-partial-commit-repro), including the pinned package version, minimal script, recorded output, version matrix, and a fixed-version verification gate; the same fixture also remains in the site source under `experiments/langgraph-sqlite-partial-commit-repro/`. If upstream publishes a PR or release, the wording should only change from "reproduced/open" to "fixed/verified" after that same fixture passes against the candidate version.

---

## 5. Redis Checkpointer: A Tool for High Concurrency and Low-Latency State Management

Redis Checkpointer is the preferred choice for horizontally scaling multiple instances and managing low-latency, high-concurrency Agents. However, because it relies on memory, it requires an additional relational database mount for long-term auditing and compliance tracing.

If your Agent service has a large daily active user base and is deployed across multiple instances in a distributed Kubernetes cluster, where users have strict requirements for response latency, a Redis-based persistence solution is the best match.

Redis operates in memory, offering sub-millisecond read/write response speeds, which significantly reduces the overhead of saving snapshots during state machine transitions on each node. The official LangGraph integration package provides `langgraph-checkpoint-redis`, which includes `RedisSaver` and `ShallowRedisSaver` for memory optimization.

There is one mandatory prerequisite when using the Redis Saver: the connected Redis instance must support the "RedisJSON" and "RediSearch" official modules. This is because LangGraph relies on JSON format parsing and secondary index searching when retrieving states and backtracking historical snapshots for specific threads. If you are using an older version of Redis or a default Redis container image without these modules installed, calling the `setup` method will result in an immediate error and crash.

Let's look at the complete practical code for the Redis Saver:

```python
from langgraph.checkpoint.redis import RedisSaver
from langgraph.graph import StateGraph

REDIS_URI = "redis://:complex_password@192.168.1.100:6379/0"

redis_checkpointer = RedisSaver.from_conn_string(REDIS_URI)

redis_checkpointer.setup()

graph = builder.compile(checkpointer=redis_checkpointer)

config = {"configurable": {"thread_id": "redis_thread_9872"}}
graph.invoke({"messages": [("user", "Executesystemcheck")]}, config=config)
```

In Redis architecture selection, we must consider the following critical design factors:

- **Memory capacity protection (ShallowRedisSaver)**: The default ``RedisSaver`` saves the complete checkpoint history for every thread. If an Agent engages in hundreds of rounds of conversation with a user, the state is saved verbatim each time. This causes Redis memory to fill up rapidly. To mitigate this, use ``ShallowRedisSaver``, which employs an overwrite mechanism, retaining only the latest checkpoint node per `thread_id` in Redis. While this prevents "time travel" (loading historical versions), it ensures constant memory usage.

- **Memory eviction and persistence strategies**: In production environments, you must disable the ``allkeys-lru`` or ``volatile-lru`` memory eviction policies on your Redis instances. If Redis automatically evicts the latest checkpoint for active threads due to memory pressure, the user's Agent workflow will crash with errors in the next conversation turn. Additionally, you must enable AOF (Append Only File) persistence with `everysec` sync mode to prevent data loss from uncommitted states in the event of a Redis process crash or physical power outage.

---

## 6. Postgres: A Common Choice for Multi-Worker Production

LangGraph's PostgreSQL implementations are `PostgresSaver` and `AsyncPostgresSaver`. They are a stronger fit for multi-user, multi-process, or multi-worker production and can use PostgreSQL transactions, JSONB, backups, and HA tooling, but reliability still depends on the database deployment, permissions, backups, and idempotency of external side effects.

When the system becomes multi-tenant, long-running, multi-process or multi-worker and needs database-level backup, auditing and operations, PostgreSQL is often a strong default choice. The final decision should still reflect the infrastructure you already operate, throughput requirements, and the team's database expertise.

In fact, LangChain's official managed service, LangSmith Agent Server, uses Postgres as the underlying storage medium for checkpoint data by default. Through the ``langgraph-checkpoint-postgres`` package, we can easily build highly available enterprise-grade Agents.

Here, I must share a subtle pitfall that cost me an entire day: If you prefer not to use the default connection string factory and instead want to manually manage the connection pool (e.g., reusing an existing database connection pool in FastAPI), you **must** enable the following two configurations during initialization:

1. `1` and ``autocommit=True``: LangGraph's table creation and state update operations rely on non-blocking transaction commits. If these are not enabled, the ``.setup()`` method will either deadlock permanently or throw a transaction exception when creating the ``checkpoints`` table.
2. `2` and ``row_factory=dict_row``: LangGraph internally extracts database rows based on column name key-value pairs (e.g., ``row["checkpoint_id"]``). Using the default tuple row factory will cause parsing errors, resulting in an ``KeyError`` exception and a crash.

Below is the production-grade code for manually managing connections and initializing ``PostgresSaver``:

```python
import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://agent_admin:secure_db_pass@192.168.1.150:5432/agent_store"

conn = psycopg.connect(DB_URI, autocommit=True, row_factory=dict_row)

postgres_checkpointer = PostgresSaver(conn)

postgres_checkpointer.setup()

graph = builder.compile(checkpointer=postgres_checkpointer)

config = {
    "configurable": {
        "thread_id": "org_100:user_200:task_abc",
        "strict_msgpack": True
    }
}
```

To mitigate the physical risk of remote code execution (RCE) caused by third-party library deserialization vulnerabilities, you must set the ``LANGGRAPH_STRICT_MSGPACK=true`` environment variable in production. This ensures that when reading and restoring State from Postgres, only trusted built-in data types are deserialized.

---

## 7. Deep Dive: Benchmarking the Four Checkpointer Backends

When selecting an architecture, we need to compare each solution's latency, concurrency, disaster recovery capabilities, and operational complexity to determine the most suitable persistence backend for the current business stage.

To facilitate quick decision-making, I have organized these four typical Checkpointer options into a comparative table:

| Physical Dimension | MemorySaver | SQLite | Redis | Postgres |
| :--- | :--- | :--- | :--- | :--- |
| Ideal Use Case | Tutorial demos, local unit tests | Personal tools, single-node deployment, lightweight backends | High-concurrency short sessions, low-latency distributed services | Distributed multi-user, enterprise-grade long-task auditing |
| Operational Cost | Zero cost, no external dependencies | Extremely low, single-file management | Moderate, requires additional memory module configuration | High, requires a highly available relational database |
| Concurrency Capability | Limited to single-process concurrency | Weak; multi-threaded writes easily lock the database | Extremely strong, high-throughput concurrency | Strong, supports connection pools and high-concurrency transactions |
| Disaster Recovery & Persistence | Physically evaporates upon restart | Disk-level persistence; backups are required | Primarily memory-based, relies on AOF disk sync | Physically persisted, mature backup and recovery mechanisms |
| Time Travel Support | Supports full historical rollback | Supports full historical rollback | Configurable full or Shallow overwrite modes | Supports full history, facilitating JSONB query analysis |
| Physical Constraints | Limited by process-assigned RAM | Write locks limit suitability for high concurrency | Must be Redis Stack 8.0 or higher | Must configure autocommit and dict_row |

---

## 8. Thread ID and State Isolation: Preventing Cross-Thread Contamination

The `thread_id` serves as the physical primary key for the Checkpointer when reading state. Without strict tenant isolation and robust owner verification, the system will inevitably face unauthorized access and catastrophic context cross-contamination.

In my recent development summaries, I explored this issue in depth. If all user requests blindly share a single `thread_id`, or if `user_id` is used directly as the `thread_id`, then under high-concurrency scenarios, User A's operation snapshots will physically overwrite User B's preceding states in the Checkpointer tables, causing the state machine's context to instantly cross-contaminate.

When designing production interfaces, we must standardize ``thread_id`` as a composite key. For example, we define:
``thread_id = user_id + business_type + task_id``

Furthermore, the API gateway layer must not pass the client-supplied ``thread_id`` directly to the directed graph compilation layer. Instead, it must construct a physical barrier based on owner verification to prevent privilege escalation. Below is the pseudo-code for the strong validation logic I designed at the gateway interception layer:

```python
def process_incoming_request(user_context: dict, client_payload: dict):
    current_user_id = user_context["user_id"]
    requested_thread_id = client_payload["thread_id"]

    thread_parts = requested_thread_id.split(":")
    if len(thread_parts) < 3 or thread_parts[0] != current_user_id:
        raise PermissionError("security: Readcurrentuser Checkpoint state")

    config = {
        "configurable": {
            "thread_id": requested_thread_id,
            "user_id": current_user_id
        }
    }

    return graph.invoke({"input": client_payload["prompt"]}, config=config)
```

## 9. Common Pitfalls and Error Logs

Avoiding common compilation and runtime errors is a necessary prerequisite for ensuring that the Checkpointer reliably performs state recovery.

Based on my practical experience troubleshooting these issues, the following error messages appear most frequently. If you see similar logs in your console, you can directly apply my step-by-step troubleshooting guide to resolve them:

### 1. SQLite Lock Database Errors
```text
sqlite3.OperationalError: database is locked
```
- Cause: Under high-concurrency requests, multiple threads attempt to write to the SQLite ``checkpoint_writes`` table simultaneously.
- Solution: When configuring ``AsyncSqliteSaver.from_conn_string``, ensure that a connection timeout is set (`timeout=30`) and configure WAL mode at the SQLite database level.

### 2. Postgres Connection Hangs and Configuration Errors
```text
psycopg.errors.ActiveSqlTransaction: CREATE TABLE cannot run inside a transaction block
```
Or throw it when reading the data:
```text
KeyError: 'checkpoint_id'
```
- Root cause: The absence of an explicit ``autocommit=True`` configuration causes DDL statements to deadlock, or the lack of ``row_factory=dict_row`` prevents LangGraph from physically extracting data rows as dictionaries.
- Solution: When creating the `psycopg` connection object, explicitly specify ``autocommit=True, row_factory=dict_row``.

### 3. Redis Index Missing Error
```text
redis.exceptions.ResponseError: Cannot create index: ft.create require RediSearch module v2.0+
```
- Cause: The Redis image used is a standard Redis Server, which lacks the core RedisJSON or RediSearch modules.
- Solution: Replace the Redis image with `redis/redis-stack-server:latest`, or confirm with your Redis cloud hosting provider that these two module plugins are enabled.

### 4. Serialization Failure Error
```text
TypeError: Object of type CustomToolResult is not JSON serializable
```
- Root cause: Your Tool returned an object that is a custom Python class instance (for example, directly returning a database ORM object) instead of converting it to a basic `dict` or JSON string. The Checkpointer cannot serialize this complex object into a byte stream when saving the graph state to disk.
- Solution: Ensure that all data returned by your Tool function to the Node consists of standard primitive types (`str`, `int`, `dict`, `list`).
- If the value serializes successfully but its timezone semantics change after restore, continue with [LangGraph Checkpoint Loses ZoneInfo and fold](/en/ai/langgraph-checkpoint-zoneinfo-fold-dst/). That case is not a hard serialization failure: the `datetime` round-trip preserves the instant while losing the IANA timezone rule and `fold` semantics.

---

## 10. Production Readiness Checklist & FAQ

### Production Readiness Checklist

- Have you completely removed ``MemorySaver`` / ``InMemorySaver`` from your production dependencies?
- If using SQLite, have you enabled WAL mode and configured a script for automatic VACUUM?
- If using Redis, have you selected the ``redis-stack`` image and disabled the automatic memory eviction policy to prevent loss of active states?
- If using Postgres, did you force-enable ``autocommit=True`` and ``row_factory=dict_row`` during connection initialization?
- Have you configured ``LANGGRAPH_STRICT_MSGPACK=true`` in your environment variables to ensure secure deserialization?
- Does your API interface layer perform strict validation on the ``thread_id`` passed by clients to prevent cross-tenant state leakage due to unauthorized access?
- When a Tool execution throws an exception, can the Checkpointer correctly save ``error_state`` and suspend the state to support subsequent retries?

---

### FAQ

#### Since MemorySaver is not suitable for production, why is it still a staple in official examples?

Its sole purpose is to lower the barrier to entry. To help beginners quickly run Agent demos without needing to install and configure SQLite, Redis, or Postgres, the default configuration uses an in-memory Saver. However, in real-world commercial applications, process memory is an unsafe, temporary medium.

#### If my SQLite file gets corrupted, can the Agent recover?

If the database file is corrupted and there is no backup, all thread states stored within that file are permanently lost. The Agent will be forced to create a new thread and start from scratch. For projects using SQLite, it is recommended to schedule a daily late-night backup of the ``.db`` file to physical cold storage (such as a dedicated drive on a Synology NAS).

#### How do I choose between ShallowRedisSaver and the standard RedisSaver?

If the application does not need full checkpoint history and mainly cares about the latest state, evaluate `ShallowRedisSaver`. Retaining less checkpoint history can reduce Redis storage pressure, but **the memory reduction depends on state size, checkpoint count, TTL, and access pattern**; there is no universal “80% savings” result. Measure key count, bytes per key, total memory, recovery requirements, and historical-debugging needs before choosing it.

#### Will frequent read/write operations by the Postgres Checkpointer slow down the Agent's response time?

Under high-concurrency write loads, Postgres's I/O overhead is indeed higher than Redis's pure memory writes. If performance becomes a bottleneck, you can adopt a read-write separation architecture in your application design. Alternatively, use a Redis checkpointer to handle short-term conversation states, and asynchronously sync to Postgres for long-term persistent auditing only when the workflow is fully archived or at critical nodes such as triggering interrupts.

---

## Official persistence reference

LangGraph's current persistence documentation defines checkpoints as thread-scoped state snapshots saved at graph super-step boundaries, with pending writes used for fault-tolerant resume. It also distinguishes the checkpointer from the cross-thread Store interface. Use the official persistence reference when validating whether a behavior is framework semantics, backend-specific behavior, or an XBSTACK reproduction.

- [LangGraph persistence and checkpointer semantics](https://docs.langchain.com/oss/python/langgraph/persistence)

## Series Navigation

LangGraph Production-Grade Agent Orchestration in Practice Series:

- [Part 1: Supervisor / Worker](/en/ai/langgraph-supervisor-worker-handoff/)
- [Part 2: State Isolation](/en/ai/langgraph-thread-session-state-isolation/)
- [Part 3: Human-in-the-loop](/en/ai/langgraph-human-in-the-loop-approval/)
- [Part 4: Failure Recovery](/en/ai/langgraph-agent-error-recovery-retry-timeout/)
- [Part 5: Observability](/en/ai/langgraph-observability-agent-trace/)
- [Part 6: Checkpointer](/en/ai/langgraph-checkpointer-memory-sqlite-redis/)
- [ The 7th article in the Subgraph ](/en/ai/langgraph-subgraph-worker-state/) series

## More to Explore

- [LangGraph State Isolation in Practice: How to Design thread_id, session_id, and user_id?](/en/ai/langgraph-thread-session-state-isolation/)
- [LangGraph Human-in-the-loop in Practice: How to Implement Multi-Agent Approval Workflows?](/en/ai/langgraph-human-in-the-loop-approval/)
- [LangGraph Multi-Agent Failure Recovery: Tool Errors, Timeouts, and Retry Strategies](/en/ai/langgraph-agent-error-recovery-retry-timeout/)
- [LangGraph Observability in Practice: How to Track the Decision Path of Each Agent?](/en/ai/langgraph-observability-agent-trace/)
- [LangGraph Multi-Agent Collaboration in Practice: How to Design Supervisor, Worker, and State Handoff?](/en/ai/langgraph-supervisor-worker-handoff/)
- [LangGraph Memory and Checkpointing for Production AI Agents](/en/ai/langgraph-memory-checkpointing-production-agents/)
