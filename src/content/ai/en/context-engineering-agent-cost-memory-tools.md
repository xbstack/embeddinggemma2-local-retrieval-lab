---
title: 'What Is Context Engineering? Reducing AI Agent Cost with Retrieval, Tool Search and Memory'
description: 'Context engineering goes beyond prompt engineering. This guide combines Microsoft, Anthropic and Google sources with XBSTACK tests on retrieval, tools, memory and token cost.'
seoTitle: 'Context Engineering for AI Agents: Retrieval, Tools, Memory and Cost'
seoDescription: 'What is context engineering? Prompt engineering vs context engineering, RAG, Tool Search, MCP, skills, memory, compaction, context windows and agent token cost.'
primaryKeyword: 'Context Engineering'
queries:
  - 'What is context engineering?'
  - 'Context engineering vs prompt engineering: what is the difference?'
  - 'How do I optimize AI agent context?'
  - 'How do I reduce AI agent token cost?'
  - 'Context engineering vs RAG: what is the difference?'
  - 'How does Tool Search reduce agent context cost?'
  - 'How do memory, skills and MCP fit into context engineering?'
category: ai
section: agent
contentType: technical-guide
subcategory: context-engineering
series: ai-agent-production
image: '../../../assets/covers/standardized/01-context-engineering-cover-379ef384-1200x630.webp'
imageAlt: 'Context engineering routes system instructions, user tasks, retrieval, memory, tools, state and compacted history into an AI agent to produce grounded answers, completed tasks and lower context cost'
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
keywords: 'Context Engineering, context engineering AI agent, Prompt Engineering, prompt engineering vs context engineering, AI Agent context, agent context optimization, context window, LLM context, token cost, AI agent cost, context caching, RAG, Retrieval Augmented Generation, retrieval, semantic reranking, Tool Search, dynamic tool loading, MCP, Model Context Protocol, Agent Memory, session memory, user memory, procedural memory, Agent Skills, instructions, message history, compaction, structured note taking, sub-agent, just in time retrieval, context rot, attention budget, context pipeline, generative AI'
geoSummary: 'Context engineering decides which high-value information enters a model’s finite context on each inference turn rather than optimizing prompt wording alone. Anthropic frames it as curating the full context state—system instructions, tools/MCP, external data and message history; Google describes a structured data/environment pipeline; Microsoft’s September 2, 2026 enterprise-agent article organizes Knowledge Retrieval, Tool Search, Skills and Memory as context-optimization levers. Microsoft benchmark figures remain vendor evaluations, not XBSTACK results. On September 5, XBSTACK added a local context-assembly audit over three real repository tasks: focused context reduced a 20,397-token full pack to 1,165–1,647 tokens, a 91.93%–94.29% reduction, while retaining 3/3 predefined evidence markers. This measures context assembly only, not model accuracy or billed-cost reduction.'
tldr:
  - 'Prompt engineering optimizes how instructions are written. Context engineering manages what the model sees on a turn: instructions, tools, MCP, retrieval, memory, history and runtime state.'
  - 'A larger context window does not remove the problem. Anthropic describes context as a finite attention budget; more tokens can add noise and context rot.'
  - 'Agent cost often comes from repeatedly carrying long history, full tool definitions and low-value retrieval on every model call. The useful metric is cost per successful outcome, not only price per million tokens.'
  - 'Tool Search, just-in-time retrieval, memory, skills, compaction and sub-agents are different mechanisms with the same goal: expose enough high-signal context for the current step without dragging every possible token into the request.'
  - 'XBSTACK now has a local context-assembly audit: three real repository tasks reduced a 20,397-token full pack to 1,165–1,647 tokens while retaining 3/3 predefined evidence markers. This is not a model-success or billing benchmark; model-layer retries, tool calls, latency and completed-task cost remain future measurements.'
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
  searchIntent: 'As AI agents move from short prompts to long-running tool loops, developers need guidance on context engineering, its difference from prompt engineering, RAG, Tool Search, MCP, memory, context windows and token-cost optimization.'
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
    - '/en/ai/ai-agent-rag-integration/'
    - '/en/ai/agent-memory-system/'
    - '/en/ai/mcp-protocol-guide/'
    - '/en/ai/ai-agent-production-governance/'
  proof: real-project-test
  cluster: other-validated
  score: 90
  distributionChannels:
    - devto
    - hashnode
draft: false
hideStructuredBlocks: true
evidenceStatus: complete
note: 'Draft created September 4, 2026. On September 5, Microsoft, Anthropic and Google primary sources were re-checked, XBSTACK completed a local context-assembly audit over real repository tasks, dedicated GPT-generated cover/body images were added, and article:prepublish-gate passed. The evidence boundary for the article’s current claims is complete: the local audit measures context size and predefined evidence retention only and does not claim model-accuracy gains or equal billed-cost savings. Model-layer success rate, retries, tool calls, latency and completed-task cost remain follow-up measurements rather than prerequisites for the current scoped conclusion.'
clusterHub: '/en/ai/'
schemaJsonLd:
  "@context": "https://schema.org"
  "@graph":
    - "@type": "TechArticle"
      "@id": "https://www.xbstack.com/en/ai/context-engineering-agent-cost-memory-tools/#article"
      headline: "What Is Context Engineering? Reducing AI Agent Cost with Retrieval, Tool Search and Memory"
      description: "Context engineering versus prompt engineering, and how retrieval, Tool Search, MCP, skills, memory, history and compaction manage an agent’s context."
      mainEntityOfPage:
        "@type": "WebPage"
        "@id": "https://www.xbstack.com/en/ai/context-engineering-agent-cost-memory-tools/"
      author:
        "@type": "Person"
        name: "Xiaobai"
        url: "https://www.xbstack.com/en/about/"
      publisher:
        "@type": "Organization"
        name: "XBSTACK"
        url: "https://www.xbstack.com"
      dateCreated: "2026-09-04"
      inLanguage: "en"
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
      "@id": "https://www.xbstack.com/en/ai/context-engineering-agent-cost-memory-tools/#faq"
      mainEntity:
        - "@type": "Question"
          name: "What is context engineering?"
          acceptedAnswer:
            "@type": "Answer"
            text: "Context engineering is the continuous design and selection of information visible to an LLM on each inference turn, including system instructions, tools, MCP, retrieved data, memory, message history and runtime state."
        - "@type": "Question"
          name: "How is context engineering different from prompt engineering?"
          acceptedAnswer:
            "@type": "Answer"
            text: "Prompt engineering focuses on instruction wording and structure. Context engineering manages the whole inference environment, of which the prompt is only one part alongside tools, retrieval, memory and history."
        - "@type": "Question"
          name: "Can context engineering reduce agent cost?"
          acceptedAnswer:
            "@type": "Answer"
            text: "It can reduce repeated history, full tool schemas and low-value retrieval, but the actual savings depend on the workflow. Vendor internal benchmarks should not be treated as your cost result; measure total requests, tokens, tool calls, retries and task success."
    - "@type": "BreadcrumbList"
      "@id": "https://www.xbstack.com/en/ai/context-engineering-agent-cost-memory-tools/#breadcrumb"
      itemListElement:
        - "@type": "ListItem"
          position: 1
          name: "XBSTACK"
          item: "https://www.xbstack.com/en/"
        - "@type": "ListItem"
          position: 2
          name: "AI"
          item: "https://www.xbstack.com/en/ai/"
        - "@type": "ListItem"
          position: 3
          name: "AI Agent"
          item: "https://www.xbstack.com/en/ai/agent/"
        - "@type": "ListItem"
          position: 4
          name: "Context Engineering"
          item: "https://www.xbstack.com/en/ai/context-engineering-agent-cost-memory-tools/"

createdAt: '2026-09-04'
lang: 'en'
route: '/en/ai/context-engineering-agent-cost-memory-tools/'
canonical: 'https://www.xbstack.com/en/ai/context-engineering-agent-cost-memory-tools/'
hub: 'agent'
translationKey: 'ai:context-engineering-agent-cost-memory-tools'
translations:
  zh-CN: '/ai/context-engineering-agent-cost-memory-tools/'
  en: '/en/ai/context-engineering-agent-cost-memory-tools/'
translationStatus: 'published'
translationSource: '/ai/context-engineering-agent-cost-memory-tools/'
translationSourceHash: '25883d392e9b3d4853366b70c02b4288b44c9cb815a40a5bbb0e1b5df0402c47'
indexing: 'index'
---

**Short answer: context engineering is not prompt engineering with a new label. Prompt engineering asks how the instruction should be written. Context engineering asks what the model should see on this turn. A real AI agent context can include system instructions, tool schemas, MCP descriptions, retrieved documents, memory, message history, task state and tool results. Those inputs change from turn to turn, consume tokens and compete for model attention.**

This topic deserves its own search page because multiple vendors are converging on the same engineering problem from different directions. Anthropic describes context as a finite attention budget. Google describes context engineering as structured data/environment infrastructure around an agent. Microsoft’s September 2, 2026 Foundry article puts Knowledge Retrieval, Tool Search, Skills and Memory directly inside its enterprise-agent cost optimization framework.

This is still not an XBSTACK model-cost benchmark. Microsoft’s percentage figures below remain vendor internal/product evaluations. XBSTACK now adds a local context-assembly audit over real repository tasks, which shows that a focused evidence pack can be much smaller while retaining predefined evidence markers. That answers the narrower context-packaging question, but it still does not prove higher model success or an equal reduction in production billing.

## Context engineering vs prompt engineering

Anthropic’s distinction is useful: prompt engineering is about writing and structuring model instructions; context engineering is the repeated process of curating the best set of tokens for every inference turn, including everything outside the prompt that can enter the model’s working state.

A real agent request can look like:

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

Optimizing only the first two lines leaves the rest of the system free to become long, stale or contradictory.

Anthropic therefore describes context engineering as a natural progression from prompt engineering as agents operate over more model turns and longer time horizons. Official source: <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

![Prompt engineering improves the instruction itself, while context engineering decides which instructions, user task, retrieval, memory, tools, state and history enter the model](../../../assets/uploads/context-engineering-agent-cost-memory-tools-en/02-prompt-vs-context-engineering.webp)

## Why larger context windows make this more important, not less

A 1M- or 2M-token window can tempt a system designer to load everything. That confuses capacity with useful attention.

Anthropic discusses “context rot”: as contexts become very large, precise retrieval and long-range reasoning can degrade. It treats context as a finite attention budget and recommends finding the smallest high-signal token set that is sufficient for the desired behavior.

Google Cloud likewise frames context engineering as a data/environment pipeline rather than a giant text buffer. Even when a model can technically ingest an enormous input, the system still has to combine persistent instructions, semi-persistent memory and dynamic external truth deliberately.

This is directly relevant to [GPT-6 Astra’s 1.05M context window](/en/ai/gpt-6-astra-api-guide/): capacity expands the space of possible tasks, but it does not tell you which logs, tools and old messages are stale or whether repeating them is economical.

## Why agent cost is more than model token price

An agent is a loop around a model. It plans, calls a tool, reads the result and reasons again. A successful outcome can require many model requests.

A useful cost model is approximately:

```text
Outcome cost
= Σ(input + cached input/write + output + tool fees for each turn)
+ retries
+ failed runs
+ human correction
```

Long history, large tool catalogs and noisy retrieval can be paid for **on every turn**.

Microsoft argues in its September 2 article that many production systems effectively freeze “what the model sees” during prototyping and never revisit it, even though context can dominate operating cost and answer quality. The objective is not minimum tokens at any price; it is **the smallest high-value context that still completes the task reliably.**

Microsoft source: <https://azure.microsoft.com/en-us/blog/the-economics-of-agent-optimization-context-engineering-for-enterprise-ai-agents/>

## Layer 1: instructions should be clear without becoming a program

Anthropic recommends avoiding both extremes: huge brittle prompts that encode every branch as pseudo-code, and vague role prompts that assume missing context.

A better stable instruction layer defines:

- role and goal;
- boundaries and prohibited actions;
- tool-use guidance;
- a small set of canonical examples;
- output requirements when needed;
- stable policy, while leaving dynamic facts to retrieval/tools.

The more dynamic a fact is, the less attractive it is to hard-code into a long-lived system prompt.

## Layer 2: retrieval is not “more documents equals better context”

RAG retrieves evidence from a large external corpus. Context engineering asks what happens after that: which candidates, how many, in what order, with which metadata and within what token budget should enter the current request?

A production retrieval chain often needs:

```text
query rewrite / decomposition
        ↓
candidate retrieval
        ↓
filter / ACL
        ↓
semantic / hybrid rerank
        ↓
deduplicate
        ↓
token budget
        ↓
context packing + citations
```

Microsoft reports internal BrowseComp-Plus results of up to **54% higher evidence recall and 34% lower retrieval token cost** with its retrieval/reranking approach. Those are Microsoft internal/product evaluation numbers, not a general promise and not an XBSTACK result. Different corpora, permissions, chunking and query distributions can produce very different outcomes.

For the retrieval implementation layer, see [AI Agent + RAG integration](/en/ai/ai-agent-rag-integration/).

## Layer 3: why Tool Search can beat exposing every tool every turn

Five tools are easy. A production agent connected to MCP servers, SaaS products, databases, browsers and internal APIs may have dozens or hundreds.

Sending every schema on every turn creates two problems:

1. **token overhead** from tool descriptions;
2. **decision noise** when several tools overlap.

Tool Search changes the pattern: give the model a smaller discovery surface, then load detailed schemas for the tools relevant to the current task. Microsoft reports roughly **97% average input-token reduction** in an internal large-tool-library benchmark. Again, that figure is specific to its evaluated workload and product—not a universal result.

MCP fits the same distinction. MCP standardizes how tools/data are connected, but connecting 100 MCP tools does not imply that all 100 schemas should enter every model request. Protocol integration and context selection are separate layers. See the [MCP protocol guide](/en/ai/mcp-protocol-guide/).

## Layer 4: memory is not “put the whole conversation back in”

Long-running agents need durable state, but useful memory means bringing **relevant cross-session information** into the current turn, not replaying the entire transcript forever.

Microsoft discusses session, user and procedural memory. Anthropic emphasizes structured note-taking and dynamic retrieval. Whichever taxonomy you use, a memory layer should answer:

- why is this worth keeping?
- where did it come from?
- when was it written?
- is it stale?
- is it relevant to this task?
- what supersedes it?

Microsoft also cites an internal memory-related benchmark improvement of about **5%**. That should remain vendor-attributed and should not be generalized to arbitrary agents.

For concrete architecture, see [AI Agent Memory System](/en/ai/agent-memory-system/). Trace-based coding-agent memory such as Funes is another direction worth validating, but XBSTACK's corresponding hands-on test is still a draft, so no public link is exposed yet.

## Layer 5: skills separate reusable procedure from memory

Memory and skills solve different problems.

Memory asks what happened before and which user/project state should persist. A skill is closer to a reusable method: a financial-report validation procedure, a release checklist or a code-review workflow.

Loading a stable procedure as a skill can avoid pasting the full SOP into every user prompt, but skills also need versioning and scope. An outdated skill can pollute a new task just as an outdated memory can.

## Layer 6: how should long-running history be managed?

Keeping every previous message is easy and expensive. Anthropic describes several strategies for long-horizon agents.

### Compaction

Compress older history while preserving the active plan, key state, errors and next actions.

### Structured note-taking

Write durable important state outside the active context—files, memory or notes—and retrieve it later.

### Just-in-time retrieval

Keep lightweight identifiers such as paths, URLs or query IDs and load the actual data only when needed instead of front-loading everything.

### Sub-agents

Isolate a subproblem in its own context and return only the useful result to the main agent so that every investigative token does not pollute the primary context.

All four techniques pursue the same goal: **do not make every model call carry every token from all previous work.**

## How context engineering relates to RAG, MCP and memory

A useful hierarchy is:

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

RAG, MCP and memory are not synonyms for context engineering. They are components that produce or control information the context-engineering layer may decide to expose.

A system can “have RAG” and still have poor context if it dumps 30 duplicate chunks into every request. It can “have MCP” and still have poor context if it exposes 80 overlapping tool schemas on every turn. It can “have memory” and still inject expired facts into new tasks.

![Context assembly pipeline: task, retrieve, filter, rank, load tools and compress history before only relevant context reaches the model and action loop](../../../assets/uploads/context-engineering-agent-cost-memory-tools-en/03-context-assembly-selective-retrieval.webp)

## XBSTACK local context audit: measure what enters context before claiming cost savings

On September 5, 2026, XBSTACK ran a **local context-assembly audit with no external model call**. The goal was deliberately narrower than a model benchmark: measure how much material enters the context window when a real engineering task receives an entire project context bundle versus a focused pack containing only the rules, scripts and evidence needed for that task.

The audit uses real XBSTACK repository material: `AGENTS.md`, the search-problem operating rules, release/growth scripts from `package.json`, the current daily-operation evidence file, and the LangGraph first-checkpoint crash experiment completed the same day. Token counts use `tiktoken o200k_base` only as a consistent local estimator; they are not provider billing numbers.

| Task | Full context | Focused context | Reduction | Required evidence retained |
| --- | ---: | ---: | ---: | ---: |
| Daily-operation gate | 20,397 | 1,647 | 91.93% | 3/3 |
| Article release gate | 20,397 | 1,541 | 92.44% | 3/3 |
| LangGraph first-checkpoint recovery | 20,397 | 1,165 | 94.29% | 3/3 |

![XBSTACK local context audit: daily operations, publishing gate and LangGraph recovery shrink a 20,397-token full context pack to 1,165–1,647 tokens while retaining all 3/3 predefined evidence markers](../../../assets/uploads/context-engineering-agent-cost-memory-tools-en/04-token-budget-context-audit.webp)

The 3/3 evidence check is intentionally conservative. For the daily-operation task, the focused pack still had to retain the project gate command, the `DAILY_OPERATION_PASS` terminal state, and the candidate-count rule. For the LangGraph recovery task, it still had to retain the `EmptyInputError`, the durable `accepted` record, and the final `completed` state. This proves only that the deterministic retrieval fixture kept the evidence we explicitly required while shrinking the input pack. It does **not** prove a 90% accuracy gain, and the 91.93%–94.29% reduction must not be presented as an equal reduction in a production bill.

The reproducible fixture lives in `experiments/context-engineering-context-audit/`. The next layer to test is model/runtime behavior: task success, retry count, tool calls, latency and completed-task cost after context filtering.

For a production agent, keep measuring the full set of metrics rather than input size alone:

| Metric | Why it matters |
| --- | --- |
| System/instruction tokens | Is the stable prompt bloated? |
| Tool-schema tokens | Are all tools sent every turn? |
| Retrieved tokens | Is RAG over-retrieving? |
| Memory tokens | Is persistent state relevant? |
| History tokens | What repeats across turns? |
| Cached tokens | Is repeated context cached? |
| Output tokens | Reasoning/response size |
| Tool calls | Does shorter context cause extra exploration? |
| Retry/failure | Savings must not destroy reliability |
| Total outcome cost | The business metric |

The useful comparison is still:

**A: full context** — current prompt, all history, all tool schemas, fixed top-k retrieval.  
**B: engineered context** — dynamic tool filtering/search, just-in-time retrieval, memory filtering, compaction/notes and an explicit token budget.

Success is not simply “B has fewer input tokens.” It is **lower context overhead without reducing task quality, followed by lower total time/cost per completed result when the model layer is tested.**

## A practical context-engineering checklist

Before a model call, ask:

1. Is every instruction still needed and current?
2. Which tools are actually relevant to this task?
3. Do any tool descriptions overlap?
4. Which facts should be retrieved live rather than hard-coded?
5. Are retrieved candidates deduplicated, reranked and ACL-filtered?
6. Which memory entries are relevant now?
7. Do memory entries have source/version/time metadata?
8. Can old history be compacted?
9. Can large data stay as references until needed?
10. Should a sub-task use an isolated sub-agent context?
11. Can repeated context use caching?
12. On failure, does the model need more information—or a different tool/strategy?

This is more useful than a universal fixed-token target because different tasks need different information density.

## Security: less context cannot mean weaker authorization

Context engineering is also a data-boundary problem. Retrieval, tool discovery and memory determine what the model can see.

A common failure is indexing documents into one shared retrieval corpus without preserving the user’s document ACL. Another is selecting tools by semantic relevance without checking whether the current user/agent has permission to call them.

A context pipeline should therefore keep:

- retrieval ACL enforcement;
- permission filtering before tool exposure;
- user/project/tenant memory isolation;
- credentials out of model context;
- auditability for why external information was injected;
- approval for high-impact writes.

The more dynamic the context becomes, the more explicit its authorization path should be.

## Current decision: why context engineering is becoming core agent infrastructure

Prompt engineering is not disappearing. Clear instructions still matter. But once a production agent has multiple turns, tools, memory, RAG, computer use and long-running work, the variables controlling each model call extend far beyond one prompt.

Context engineering supplies an engineering model: the LLM has finite attention and token-priced input, so each turn should receive information that is **sufficient but not excessive, current, authorized, high-signal and traceable.**

Microsoft’s new cost article, Anthropic’s agent engineering guidance and Google’s context-engineering material converge on that broad problem, while their concrete products and benchmarks remain different. There is no reason to pretend that vendor convergence makes context engineering a single standard.

**For XBSTACK, the future publication should prove something narrower: on the same real agent task, can less repeated history, fewer irrelevant tool schemas, better retrieval and better memory reduce total input while preserving or improving successful completion?**

## FAQ

### What is context engineering?

Context engineering is the design and dynamic selection of information visible to an LLM on each inference turn, including instructions, tools/MCP, retrieval, memory, history, runtime state and caching—not only prompt wording.

### Does context engineering replace prompt engineering?

No. Prompt engineering remains one part of context engineering. Good system instructions, examples and output constraints still matter, while production agents also need dynamic tool, data, memory and history management.

### What is the difference between context engineering and RAG?

RAG retrieves external evidence. Context engineering additionally decides how much to retrieve, how to rerank/deduplicate it, how it combines with instructions/tools/memory/history and what token budget applies.

### How is MCP related to context engineering?

MCP is a protocol layer for connecting tools/data. Context engineering decides which MCP capabilities should be discovered, loaded and exposed on the current turn. Connecting many MCP servers does not mean every tool schema belongs in every request.

### Does context engineering always save tokens?

It can remove repeated and irrelevant input, but there is no universal savings percentage. Compare total input/output, tool calls, retries, latency and successful completion on the same task. Microsoft’s 34%/97% figures are vendor-specific internal evaluations, not guarantees.

## Official sources

- [Microsoft Azure: The Economics of Agent Optimization — Context engineering](https://azure.microsoft.com/en-us/blog/the-economics-of-agent-optimization-context-engineering-for-enterprise-ai-agents/)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Google Cloud: What is AI context engineering?](https://cloud.google.com/discover/ai-context-engineering)

## Continue reading

- [AI Agent + RAG integration](/en/ai/ai-agent-rag-integration/)
- [AI Agent Memory System](/en/ai/agent-memory-system/)
- [MCP Protocol Guide](/en/ai/mcp-protocol-guide/)
- [Production AI agent governance](/en/ai/ai-agent-production-governance/)
