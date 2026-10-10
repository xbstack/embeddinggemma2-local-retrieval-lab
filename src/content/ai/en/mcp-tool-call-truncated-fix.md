---
title: 'MCP Tool Call Result Truncated: Causes, Pagination, Cursors, and Size Limits'
description: 'MCP Tool Call Result Truncated is not a universal 64KB limit. Diagnose client, SDK, context and timeout limits, then return bounded results with totals, cursors and pagination.'
seoTitle: 'MCP Tool Call Result Truncated: Pagination & Cursor Fixes'
seoDescription: 'How do you fix MCP Tool Call Result Truncated? Separate protocol rules from client and SDK limits, then use bounded results, totals, cursor/offset pagination and targeted follow-up reads.'
geoSummary: 'MCP does not define one universal 64KB Tool Result cap. Truncation can come from a client, SDK buffer, model context, serialized message size or timeout. The robust fix is a bounded result contract with total counts and cursor/offset pagination.'
primaryKeyword: MCP Tool Call Result Truncated
keywords: 'MCP Tool Call Result Truncated, MCP result truncated, MCP tool result limit, MCP pagination, MCP cursor, stdio maxBufferSize, Cursor MCP, Claude MCP, MCP troubleshooting, MCP, Troubleshooting, Buffer Overflow, Semantic Compression, Cursor'
queries:
- How do I fix MCP Tool Call Result Truncated?
- Does MCP have a universal 64KB tool result limit?
- How should an MCP tool paginate large results?
- How should MCP cursor or offset pagination work?
- What does TypeScript MCP SDK maxBufferSize limit?
hideStructuredBlocks: true
tldr:
- MCP does not define one universal 64KB Tool Result ceiling; truncation may come from a client, SDK, model context, proxy, serialized message size, or timeout.
- TypeScript SDK v2 stdio `maxBufferSize` is an SDK implementation boundary, not an MCP protocol limit.
- Do not silently use `text[:N]` for large results; return `total`, `has_more`, `cursor`, or `offset` so the caller can continue reading.
- For large files, logs, and query results, return an index, summary, ranges, or a controlled URI first and fetch raw evidence on demand.
entities:
- Model Context Protocol
- MCP Tool Result
- MCP Pagination
- cursor
- offset
- TypeScript MCP SDK v2
- maxBufferSize
- stdio
- Streamable HTTP
citations:
- https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/pagination
- https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/migration/upgrade-to-v2.md
- https://blog.modelcontextprotocol.io/posts/2026-07-28/
evidenceStatus: partial
note: 'Re-reviewed on 2026-08-15. Unsupported production-log compression ratios and accuracy-improvement claims were removed. The page keeps its ranked H1/URL and search intent while strengthening pagination, cursor, offset, summary, URI, and evidence boundaries.'
category: ai
section: ai
contentType: troubleshooting
image: ../../../assets/covers/generated/ai/en/mcp-tool-call-truncated-fix.webp
tags:
  - MCP
  - Troubleshooting
  - Buffer Overflow
  - Semantic Compression
  - Cursor
  - Claude
imageAlt: >-
  How to Fix Truncated MCP Tool Call Results: A Deep Dive into Stdio Buffers and
  Semantic Compression: MODEL CONTEXT PROTOCOL article cover
description_en: >-
  Diagnose MCP tool-result truncation without assuming a protocol-level 64KB cap.
  Separate client, SDK buffer, model-context, serialized-size and timeout limits,
  then use bounded results, total counts, cursors, offsets and targeted follow-up reads.
imageAlt_en: >-
  How to Fix Truncated MCP Tool Call Results: A Deep Dive into Stdio Buffers and
  Semantic Compression
clusterHub: '/en/ai/mcp/'

createdAt: '2026-06-03'
lang: 'en'
route: '/en/ai/mcp-tool-call-truncated-fix/'
canonical: 'https://www.xbstack.com/en/ai/mcp-tool-call-truncated-fix/'
hub: 'mcp'
translationKey: 'ai:mcp-tool-call-truncated-fix'
translations:
  zh-CN: '/ai/mcp-tool-call-truncated-fix/'
  en: '/en/ai/mcp-tool-call-truncated-fix/'
translationStatus: 'published'
translationSource: '/ai/mcp-tool-call-truncated-fix/'
translationSourceHash: 'b4ae0534b659bd8c5837632fea49f2fc509c7e0cdf920ad58ab4cd4650aba1a3'
indexing: 'index'
---
**Direct answer: `Tool call result truncated` usually does not mean that MCP defines one universal 64KB result limit. A client display cap, tool-result cap, model context budget, serialized message size, transport backpressure, or timeout may be the first layer to fail. Return bounded results with total counts and a cursor or offset instead of silently cutting text, then let the model request the next page or a targeted range.**

> **Version note — 2026-08-10:** MCP `2026-07-28` is now published, and the protocol still does not define one universal 64KB Tool Result ceiling. The TypeScript SDK v2 migration guide adds a configurable stdio `maxBufferSize` with a 10 MB default. That is an SDK read-buffer boundary, not a protocol-wide tool-result limit, so production debugging must keep protocol rules separate from client and SDK implementation limits.

## What This Guide Covers: The Physical Limits of Information Loss

- Why did Cursor prompt ``Tool call result truncated`` when my MCP Server was reading a log file containing `1MB`?
- How can I gracefully inform the AI that "there is more content to read" before the Stdio buffer overflows?
- Why does simple physical truncation (e.g., ``text[:5000]``) cause the AI to hallucinate?
- How do you design a "perceptive" streaming feedback mechanism when processing massive database query results?

---

## Who This Guide Is For

- **AI System Developers**: Those writing custom MCP Servers involving large-scale data interactions.
- **Agent Architects**: Those needing to solve the "context anemia" problem Agents face when handling long documents or logs.
- **Full-Stack Engineers**: Developers frequently encountering protocol-level errors or response timeouts while debugging local private cloud Agents.

---

## 1. Diagnose the Correct Layer: Protocol, Client, Context, or Transport

When a large result fails, do not begin with the assumption that “MCP only supports 64KB.” The MCP stdio transport requires the client and server to exchange valid newline-delimited JSON-RPC messages over stdin and stdout; the specification does not define one universal 64KB tool-result ceiling. A reproducible test should instead increase fixture size gradually and record raw bytes, serialized bytes, bytes received by the client, elapsed time, and the layer that emitted the failure.

The investigation must separate client display or injection limits, the remaining model context budget, serialized JSON size, whether the host process consumes stdout promptly, and whether the tool finishes before its timeout. An operating-system pipe buffer can create backpressure, but it is not an MCP rule that automatically truncates every message above one fixed byte count.

Record the raw result size, serialized message size, received size, elapsed time, and any client truncation marker before choosing pagination, cursor-based continuation, range queries, summaries, or an object-storage link. MCP's standard cursor pagination applies to list operations such as `resources/list` and `tools/list`; a custom Tool that returns large data should define its own cursor or offset, bounded page size, and explicit `has_more` field in the Tool schema.

---

## 2. Solution A: Physical Pagination and Secondary Invocation

Don't try to feed the AI everything at once; teach it how to "turn the page."

### 1. Implementing an Offset Mechanism
Use a **line offset**, not a UTF-8 byte offset, for line-oriented log files. This avoids mixing Python text `seek()` cookies with `os.path.getsize()` byte counts. The following MCP Python SDK v2 example uses `MCPServer` and a root-allowlisted directory; change `ROOT` to your authorized log directory.

```python
from pathlib import Path
from mcp.server import MCPServer

mcp = MCPServer("Bounded Logs")
ROOT = Path("/srv/agent-readable").resolve()  # Configure this directory.

@mcp.tool()
def read_large_file(filename: str, offset: int = 0, limit: int = 100) -> dict:
    """Read a bounded number of log lines from the authorized directory."""
    if offset < 0 or not 1 <= limit <= 200:
        raise ValueError("offset >= 0 and 1 <= limit <= 200 required")
    target = (ROOT / filename).resolve()
    if not target.is_relative_to(ROOT) or not target.is_file():
        raise ValueError("File is outside the authorized directory or missing")
    lines = []
    total_lines = 0
    with target.open("r", encoding="utf-8", errors="replace") as stream:
        for index, line in enumerate(stream):
            if offset <= index < offset + limit:
                lines.append(line.rstrip("\n"))
            total_lines += 1
    has_more = offset + len(lines) < total_lines
    return {
        "lines": lines,
        "total_lines": total_lines,
        "has_more": has_more,
        "next_offset": offset + len(lines) if has_more else None,
    }
```

This is an illustrative **bounded result** implementation (using the [official MCP Python SDK v2 tool-registration API](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/servers/tools.md)), not a constant-time random-access file index: counting lines scans the input. For huge files, prebuild line/byte indexes or use database-backed cursor pagination. Enforce permission checks and bound line/byte sizes as well as the page count before production use.

### 2. Injecting "Pagination Logic" into the System Prompt
You must explicitly instruct the AI: "If you detect that `metadata.status` is `partial_success`, you must proactively call for the next page. Do not speculate based on incomplete information."

---

## 3. Solution B: Semantic Compression (The Semantic Shrink)

Physical truncation is blunt; it severs the logical chain. The truly robust approach is to perform "perceptive compression" on the server side.

### Key Point: Don't let the AI read raw data; make it read an "audit report."

For large logs, generate a traceable index before asking the model to inspect raw text. A practical pattern is:
1. Deduplicate by error type, stack fingerprint, or business error code while preserving occurrence counts.
2. Sample startup, failure-window, and tail ranges while retaining original line numbers or timestamps.
3. Index signals such as `ERROR`, `FATAL`, and `RETRY`, but let the caller fetch additional ranges by cursor or time window.
4. Attach `source_range`, a checksum, or a controlled URI to every summary so the model or reviewer can return to the original evidence.

The purpose is to reduce context pressure without breaking the evidence chain. Compression ratio and diagnostic quality depend on the log structure, filters, model, and task. This article does not contain a controlled benchmark, so it should not claim one fixed compression factor or accuracy improvement.

---

## 4. Comparison Block: Physical Truncation vs. Logical Compression

- Physical truncation (str[:limit]):
    - Pros: Easy to implement and imposes little additional processing overhead.
    - Cons: May break JSON structure or core logic, leading to AI hallucinations.
- Logical pagination:
    - Pros: Ensures data integrity and gives the AI autonomous decision-making power.
    - Cons: Increases conversation turns and token consumption.
- Semantic summarization:
    - Pros: Most efficient; the AI receives high-quality context in a single pass.
    - Cons: Requires additional server-side compute resources (e.g., invoking a local small model or more complex logic).

---

## 5. Common Pitfalls and Error Logs

### 1. Error: `JSON-RPC message exceeds max length`
- Cause: This is a size limit imposed by a particular client, SDK, proxy, or host application—not a universal 1MB threshold in the MCP specification.
- Solution: Identify the layer that emitted the error and record the serialized message size. Do not embed Base64 images or binary payloads in a Tool Result; return a controlled URI, summary, and bounded read parameters instead.

### 2. Error: `Tool Execution Timeout`
- Symptom: The server logic appears to complete, but the client still reports a timeout.
- Investigation: Measure business-query time, JSON serialization time, write time, and the client timeout separately. The cause may be the query itself, oversized messages, transport backpressure, or a host timeout; the symptom alone does not prove that stdout crossed one fixed buffer limit.

---

## MCP 2026-07-28 boundary: stateless transport does not make oversized results automatically safe

MCP 2026-07-28 moves the protocol core toward stateless request/response handling and adds newer routing, authorization, and cacheable list semantics. That does not automatically remove oversized Tool Results, host context-window limits, client display truncation, or application-level timeouts. In other words: **a protocol-generation change fixes connection and request semantics; it does not decide how your application should page, summarize, or recover a 10MB result.**

The offset pagination, semantic compression, and “let the model read an audit result instead of raw bulk data” controls in this guide therefore remain application-layer concerns. Compare protocol changes against the [official MCP 2026-07-28 release notes](https://blog.modelcontextprotocol.io/posts/2026-07-28/), and use the [XBSTACK MCP Inspector](/en/tools/mcp-inspector/) for a read-only preflight check of a public remote endpoint.

## 6. Frequently Asked Questions

### Q: If stdio is affected by local-process and host limits, why not use Streamable HTTP everywhere?
A: The transports serve different deployment boundaries. stdio is appropriate for a local Server launched by the Client and requires no separately exposed port. Streamable HTTP is better for remote or multi-client services that need authentication, sessions, and network observability. Changing transport does not automatically solve oversized Tool Results or insufficient model context.

### Q: What if I must provide a 10MB CSV file?
A: Do not embed the complete file in the Tool Result. Save it in an access-controlled location the Client can reach, then return a URI, file size, checksum, schema summary, and allowed read ranges. A separate reader Tool can retrieve only the required rows, chunks, or query results.

### Q: How do I know whether the Server or Client truncated a result?
A: Record raw bytes, serialized bytes, bytes received by the Client, a checksum, elapsed time, and an explicit `has_more` value. Any fixed 100KB or 1MB number is a client-specific configuration until verified; it is not an MCP-wide threshold.

---

## Recommended Deep Reading

- [Official MCP transport specification: stdio and Streamable HTTP](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [Official MCP pagination specification: cursors and paginated list operations](https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/pagination)
- [MCP hub: protocol, servers, deployment, and troubleshooting](/en/ai/mcp/)
- [MCP Resources vs Tools vs Prompts vs Roots](/en/ai/mcp-protocol-deep-dive/)
- [MCP stdio pollution and -32700 Parse Error troubleshooting](/en/ai/mcp-json-rpc-parse-error/)
- [MCP Streamable HTTP deployment: remote transport and security boundaries](/en/ai/mcp-streamable-http-deployment/)
- [MCP security: tool permissions, paths, and high-risk actions](/en/ai/mcp-security-best-practices/)
- [MCP Server production governance: timeouts, permissions, observability, and recovery](/en/ai/mcp-server-production-governance/)
