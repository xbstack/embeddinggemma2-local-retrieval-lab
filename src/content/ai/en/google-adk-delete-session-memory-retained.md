---
title: "Google ADK delete_session() Does Not Delete Long-Term Memory: 2.8.0/2.9.0 Reproduction"
description: "Why does Google ADK delete_session() remove the Session while data copied with add_session_to_memory() remains searchable? This offline reproduction covers 2.8.0 and 2.9.0, the API boundary, and production deletion design."
seoTitle: "Google ADK delete_session does not delete Memory: 2.8/2.9 Test"
seoDescription: "Tested on Google ADK 2.8.0 and 2.9.0: delete_session() removes the Session but does not cascade-delete long-term Memory copied into MemoryService; BaseMemoryService exposes no generic delete method."
geoSummary: "XBSTACK reproduced the behavior offline on 2026-09-15 with google-adk 2.8.0 and 2.9.0. A user event containing a unique marker was written to InMemorySessionService, then copied into InMemoryMemoryService with add_session_to_memory(). After delete_session(), get_session() confirmed that the Session no longer existed, while search_memory() still returned the same marker. Runtime inspection also found no callable delete method on BaseMemoryService in either tested version. This result is limited to InMemorySessionService + InMemoryMemoryService and does not prove identical behavior for VertexAiMemoryBankService or every third-party backend."
category: ai
section: practice
contentType: troubleshooting
subcategory: google-adk
series: "Google ADK Production Troubleshooting"
seriesOrder: 2
hideStructuredBlocks: true
draft: false
image: "../../../assets/uploads/google-adk-memory-delete/01-cover.webp"
imageAlt: "Google ADK delete_session removing a Session while long-term Memory remains searchable in the 2.8.0 and 2.9.0 reproduction"
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
keywords: "Google ADK delete_session, Google ADK delete_session does not delete memory, Google ADK memory delete, Google ADK MemoryService delete, Google ADK long-term memory deletion, memory still exists after delete_session, delete_session memory retained, delete_session does not delete memory, add_session_to_memory, search_memory, InMemoryMemoryService, BaseMemoryService delete, Google ADK 2.8.0, Google ADK 2.9.0, agent memory data deletion, clear AI memory, account deletion memory cleanup, long-term memory cleanup, MemoryService cleanup"
primaryKeyword: "Google ADK delete_session does not delete memory"
targetHub: "AI Agent"
conversionTarget: "Google ADK minimal reproduction, Agent Memory data-deletion troubleshooting, AI Agent production governance"
evidenceStatus: complete
contentRole: support
tldr:
  - "On google-adk 2.8.0 and 2.9.0, InMemorySessionService.delete_session() removes the Session but does not cascade-delete long-term Memory previously copied into InMemoryMemoryService."
  - "The same unique marker is returned by search_memory() before and after delete_session(), while get_session() confirms that the Session itself is gone."
  - "BaseMemoryService exposes no callable delete method in either tested version, so applications must not treat delete_session() as a complete user-data deletion operation."
  - "This reproduction covers InMemorySessionService + InMemoryMemoryService only; VertexAiMemoryBankService and other managed backends were not exercised."
queries:
  - "Why does Google ADK delete_session not delete memory?"
  - "Why is Google ADK memory still searchable after deleting a session?"
  - "How do I delete long-term memory from Google ADK MemoryService?"
  - "How do I delete data after add_session_to_memory?"
  - "Why does BaseMemoryService have no delete method?"
  - "Google ADK 2.9 memory delete"
  - "Why does Google ADK long-term memory remain after deleting a session?"
  - "How should Google ADK MemoryService data be cleaned up during account deletion?"
faqs:
  - question: "Does Google ADK delete_session() delete long-term Memory?"
    answer: "Not in the InMemorySessionService + InMemoryMemoryService behavior reproduced here on google-adk 2.8.0 and 2.9.0. The Session is removed, but the marker previously copied with add_session_to_memory() remains searchable."
  - question: "Does this mean no Google ADK Memory backend can delete data?"
    answer: "No. This test covers the in-memory implementations and the BaseMemoryService public API surface. VertexAiMemoryBankService and third-party backends may expose backend-specific deletion capabilities that were not tested here."
  - question: "Why does delete_session() not clear Memory automatically?"
    answer: "Session and long-term Memory are separate persistence surfaces. After add_session_to_memory() copies session content into MemoryService, deleting the source Session does not automatically revoke the copied Memory unless a backend implements an explicit cascade."
  - question: "How should a production app implement user-data deletion?"
    answer: "Treat Session, Memory, Artifacts, vector stores, and application databases as separate deletion targets. Execute the supported deletion operation for each backend, then verify the post-delete state rather than assuming one Session API cascades everywhere."
  - question: "Does upgrading to google-adk 2.9.0 fix this?"
    answer: "No change was observed in this reproduction. The same behavior was reproduced on both 2.8.0 and 2.9.0, so upgrading to 2.9.0 alone does not provide cascade deletion for this path."
note: "This reproduction runs locally and offline with no Gemini, OpenAI, or Vertex AI model call. It covers google-adk 2.8.0 and 2.9.0 with InMemorySessionService and InMemoryMemoryService, using a unique marker to verify before/after search behavior. VertexAiMemoryBankService is not tested, so the conclusion must not be generalized to every managed Memory backend."
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
  intent: "Answer one production data-lifecycle question in Google ADK: why long-term Memory can remain after delete_session() removes a Session, and how applications should separate Session deletion from Memory deletion."
  differentiation: "This does not duplicate the existing Google ADK state_delta/A2A resume article and is not a generic Memory tutorial. It serves the independent Session-deletion-versus-long-term-Memory search intent."
  inventoryCheckedAt: '2026-09-15'
  inventoryReferences:
    - '/en/ai/google-adk-state-delta-resume/'
    - '/en/ai/ai-agent-framework-comparison/'
    - '/en/ai/agent-memory-system/'
demandEvidence:
  searchIntent: "Google ADK users deleting a Session or implementing account/user-data deletion still find long-term Memory previously copied with add_session_to_memory(), and need to know whether 2.8.0/2.9.0 are affected, why delete_session() does not cascade, and how to delete safely in production."
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
    - '/en/ai/google-adk-state-delta-resume/'
    - '/en/ai/ai-agent-framework-comparison/'
    - '/en/ai/agent-memory-system/'
  proof: reproduction
  cluster: other-validated
  score: 91
  distributionChannels:
    - devto
clusterHub: '/en/ai/'
audience:
  - "Python developers using Google ADK MemoryService for cross-session long-term memory."
  - "Agent product teams implementing account deletion, clear-memory controls, or user-data deletion."
  - "Platform engineers separating Session, Memory, Artifacts, and other persistence lifecycles."

createdAt: '2026-09-15'
lang: 'en'
route: '/en/ai/google-adk-delete-session-memory-retained/'
canonical: 'https://www.xbstack.com/en/ai/google-adk-delete-session-memory-retained/'
hub: 'agent'
translationKey: 'ai:google-adk-delete-session-memory-retained'
translations:
  zh-CN: '/ai/google-adk-delete-session-memory-retained/'
  en: '/en/ai/google-adk-delete-session-memory-retained/'
translationStatus: 'published'
translationSource: '/ai/google-adk-delete-session-memory-retained/'
translationSourceHash: 'befdaa0196e47c3f5414de4a04a621e1bc91601e5299bd92d932823b0585a3e2'
indexing: 'index'
---
If you are implementing user-data deletion in Google ADK, there is an easy boundary to miss: `delete_session()` deletes a Session. It does not necessarily delete long-term data that was already copied into a `MemoryService`.

I reproduced that behavior locally on both `google-adk==2.8.0` and `2.9.0`. After deleting the Session, `get_session()` confirmed that it was gone, but the same unique marker that had been copied with `add_session_to_memory()` was still returned by `search_memory()`.

This is not a stale model response or a remote cache. The reproduction makes no external model call. The retained content is the exact Session event that was explicitly copied into `InMemoryMemoryService` before the Session was deleted.

## The short answer

The test matrix is intentionally small:

- Python 3.11+
- `google-adk==2.8.0`
- `google-adk==2.9.0`
- `InMemorySessionService`
- `InMemoryMemoryService`
- unique marker: `blue-orchid-260915`
- fully offline, with no Gemini, OpenAI, or Vertex AI call

Both versions produced the same result:

| Version | Session after `delete_session()` | Memory found before delete | Memory found after delete | Callable `BaseMemoryService` delete method |
|---|---|---:|---:|---:|
| 2.8.0 | deleted | yes | **yes** | 0 |
| 2.9.0 | deleted | yes | **yes** | 0 |

That means this call cannot be treated as proof that all user data associated with the Session has been deleted:

```python
await session_service.delete_session(
    app_name=app_name,
    user_id=user_id,
    session_id=session_id,
)
```

It proves only that the Session layer completed its deletion. Long-term Memory, Artifacts, external vector stores, and application databases need their own deletion path and their own post-delete verification.

## How I reproduced it

The reproduction keeps the path minimal. First, it creates a Session and appends a user event containing one unique marker:

```text
Remember this marker: blue-orchid-260915
```

Next, it copies the Session into long-term Memory:

```python
await memory_service.add_session_to_memory(session)
```

A call to `search_memory()` confirms that the marker is present before deletion. The script then calls `delete_session()` and checks `get_session()` to verify that the Session itself no longer exists.

Finally, it searches Memory again.

The important fields from both runs are equivalent to:

```json
{
  "session_exists_after_delete": false,
  "memory_found_before_delete": true,
  "memory_found_after_delete": true,
  "base_memory_delete_methods": []
}
```

The complete minimal reproduction lives in the XBSTACK experiment asset with version-specific JSON logs. The evidence is not that one internal object happened to look unusual. Three assertions hold at the same time: **the Session is gone, Memory existed before deletion, and the copied Memory still exists afterward.**

## Why this happens: Session and Memory have separate lifecycles

The key operation is `add_session_to_memory()`.

Once an application gives Session content to a MemoryService, long-term Memory is no longer merely a view over the original Session. It has been copied into a separate persistence surface. Deleting the source Session therefore has no reason to erase the copy unless an explicit cascade has been implemented.

![Google ADK lifecycle showing a Session copied into MemoryService, the Session deleted, and long-term Memory still queryable through search_memory](../../../assets/uploads/google-adk-memory-delete/02-session-memory-lifecycle.webp)

The public service surface reinforces that separation. In both 2.8.0 and 2.9.0, SessionService has a `delete_session()` operation, while the runtime inspection in this test found no callable `delete*` method on `BaseMemoryService`.

This is the same product-level gap described by upstream issue #6949: applications may have deletion paths for Sessions and Artifacts while still lacking a backend-independent Memory deletion API.

For a broader architecture view of long-term Agent Memory, user isolation, and forgetting mechanisms, see [AI Agent Memory System](/en/ai/agent-memory-system/). The important distinction here is narrower: a Memory lifecycle cannot be inferred from a Session lifecycle.

## Why the issue resurfaced now

This boundary is not entirely new, but it became current again in September 2026.

Upstream issue #6949, opened on August 30, points out that `BaseMemoryService` has no deletion operation analogous to Session and Artifact deletion. On September 13, issue #7110 restated the problem as a concrete failure shape: copy a Session into Memory, delete the Session, and the long-term Memory remains.

Those issues are external problem evidence. The conclusion in this article does not rely only on their text: XBSTACK reran the behavior locally against both 2.8.0 and 2.9.0.

## Why this matters for account deletion and privacy controls

If Memory is only a disposable developer aid, the problem may stay invisible for a while. It becomes a production concern as soon as the product offers operations such as:

- delete one conversation;
- clear chat history;
- clear AI memory;
- close an account;
- export and delete user data;
- enforce enterprise retention rules;
- remove a departed user from a multi-tenant workspace.

The dangerous implementation is a UI that calls `delete_session()` and immediately tells the user that the data has been deleted. At least for the in-memory implementation reproduced here, that statement would be false for the Memory layer.

A safer design is an explicit deletion ledger:

| Persistence surface | Deletion operation | Post-delete verification |
|---|---|---|
| Session | `delete_session()` | `get_session()` returns no Session |
| Long-term Memory | backend-specific deletion | `search_memory()` no longer returns the user's marker or id |
| Artifacts | ArtifactService deletion | read returns not found |
| External vector store | delete by user/tenant/id | query returns zero matches |
| Application database | transaction / soft-delete / hard-delete policy | business query verifies final state |

![Production user-data deletion architecture that independently deletes and verifies Session, long-term Memory, Artifacts, Vector Store, and Application DB](../../../assets/uploads/google-adk-memory-delete/03-production-deletion-fanout.webp)

Deletion and verification belong together. Sending a delete request without a read-back or query verification is not enough to prove the final data state.

![Delete-and-verify loop showing storage identification, deletion, read-back verification, investigation when data remains, and final verification](../../../assets/uploads/google-adk-memory-delete/04-delete-verify-loop.webp)

## What can you do now?

The answer is not to call `delete_session()` twice. It depends on the Memory backend you actually use.

For a custom MemoryService, design a concrete deletion key in the backing store, such as `user_id + memory_id`, a tenant namespace, or another index that can reliably remove all long-term data for one user. The deletion should also be auditable.

For a managed Memory backend, check whether that backend exposes its own deletion API and use it directly. Do not wait for SessionService to cascade unless the backend contract explicitly guarantees that behavior.

If the chosen MemoryService has no deletion capability at all while your product promises user-data deletion, the safest engineering decision is simple: **do not ingest data that must later be deletable into that backend, or choose a backend with verifiable deletion.**

This is also the kind of production criterion that belongs in an Agent framework comparison. XBSTACK's [AI Agent framework comparison](/en/ai/ai-agent-framework-comparison/) already treats resume, state persistence, and idempotency as operational concerns; Memory deletion should be evaluated the same way rather than as a feature checkbox.

## Do not overgeneralize this into “Google ADK cannot delete data”

That would go beyond the evidence.

I did not test `VertexAiMemoryBankService`, and I did not provision managed infrastructure. Different MemoryService implementations may expose backend-specific deletion capabilities even though `BaseMemoryService` does not provide one common interface in the versions tested here.

The reproduction also does not prove that future versions will behave the same way. The 2.8.0/2.9.0 version matrix exists so that each future ADK upgrade can be retested. If a public delete API is added, or an explicit cascade contract appears, the current assertions should fail and this page should be updated.

## Do not mix this with Google ADK resume bugs

XBSTACK already has a separate [Google ADK state_delta and A2A resume reproduction](/en/ai/google-adk-state-delta-resume/). That page covers state updates during resumable `Runner.run_async()` calls and an A2A human-approval message-conversion boundary.

The search intent here is different:

- the state-delta page answers “why was my state not persisted when I resumed an Agent?”;
- this page answers “why is long-term Memory still present after I deleted the Session?”

They belong to the same Google ADK production cluster, but they require different reproductions and different production fixes.

## Production recommendation

If your application already uses Google ADK long-term Memory, make three changes.

First, remove `delete_session()` from any implementation that labels it as a complete user-data deletion operation. Treat it as Session deletion only.

Second, add an independent deletion path and post-delete verification for the actual MemoryService you deploy, especially for account closure, clear-memory controls, and multi-tenant retention requirements.

Third, keep this reproduction in your upgrade regression suite. For every `google-adk` upgrade, re-run the Session deletion assertion, Memory search assertion, and public delete-API inspection instead of inferring lifecycle behavior from release notes.

As of September 15, 2026, the result is the same on the two versions tested here: **deleting a Session is not the same operation as deleting long-term Memory.**

## References and reproduction sources

- [google/adk-python issue #6949: No way to delete memories from a MemoryService](https://github.com/google/adk-python/issues/6949)
- [google/adk-python issue #7110: Memory has no removal path](https://github.com/google/adk-python/issues/7110)
- [Google ADK Python repository](https://github.com/google/adk-python)
