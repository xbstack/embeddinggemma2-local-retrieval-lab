---
title: 'MCP Tool Call Result Truncated 怎么解决？分页、cursor 与结果大小排查'
description: MCP Tool Call Result Truncated 不代表 MCP 协议存在统一 64KB 上限。本文按客户端展示限制、SDK 缓冲区、模型上下文、序列化体积与超时逐层排查，并用分页、cursor/offset、摘要与索引避免静默截断。
seoTitle: MCP Tool Result Truncated：分页与 cursor 修复
seoDescription: MCP Tool Call Result Truncated 怎么解决？先区分客户端、SDK 缓冲区、上下文和超时限制，再用有界结果、total、cursor/offset 与按需分页避免信息丢失。
geoSummary: MCP Tool Call Result Truncated 不等于“stdio 只有 64KB”。MCP 规范没有统一工具结果 64KB 上限；真实限制可能来自客户端、SDK、上下文窗口、消息体积或超时。修复重点是返回有界结果并提供 total 与 cursor/offset，让调用方继续读取。
primaryKeyword: MCP Tool Call Result Truncated
keywords: 'MCP Tool Call Result Truncated, MCP result truncated, MCP tool result limit, MCP pagination, MCP cursor, stdio maxBufferSize, Cursor MCP, Claude MCP, MCP 故障排查, MCP, 故障排查, 缓冲区溢出, 语义压缩, Cursor'
queries:
- MCP Tool Call Result Truncated 怎么解决？
- MCP Tool Result 有统一 64KB 上限吗？
- MCP 工具返回结果太大怎么分页？
- MCP cursor 和 offset 应该怎么设计？
- TypeScript MCP SDK maxBufferSize 是什么？
hideStructuredBlocks: true
tldr:
- MCP 规范没有统一的 Tool Result 64KB 上限；截断可能来自客户端、SDK、模型上下文、代理层、消息体积或超时。
- TypeScript SDK v2 的 stdio `maxBufferSize` 是 SDK 实现边界，不等于 MCP 协议上限。
- 大结果不要静默 `text[:N]`；返回 `total`、`has_more`、`cursor` 或 `offset`，让调用方能够继续读取。
- 文件、日志和数据库大结果优先返回索引、摘要、范围和受控 URI，再按需取回原始内容。
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
note: '2026-08-15 再审：删除没有实验记录支撑的“生产日志压缩比例/准确率提升”等定量表述，保留可复现的分页、cursor、offset、摘要和 URI 设计。页面排名已进入 Top 10，因此保留 H1/URL 与主搜索意图，只增强证据边界。'
category: ai
section: ai
contentType: troubleshooting
image: "../../assets/covers/generated/ai/zh/mcp-tool-call-truncated-fix.webp"
tags:
  - MCP
  - 故障排查
  - 缓冲区溢出
  - 语义压缩
  - Cursor
  - Claude
imageAlt: "MCP Tool Call Result Truncated 怎么解决：深度拆解 Stdio 缓冲区与语义压缩实战：MCP 协议文章封面"

clusterHub: '/ai/mcp/'

createdAt: '2026-06-03'
lang: 'zh-CN'
route: '/ai/mcp-tool-call-truncated-fix/'
canonical: 'https://www.xbstack.com/ai/mcp-tool-call-truncated-fix/'
hub: 'mcp'
translationKey: 'ai:mcp-tool-call-truncated-fix'
translations:
  zh-CN: '/ai/mcp-tool-call-truncated-fix/'
  en: '/en/ai/mcp-tool-call-truncated-fix/'
translationStatus: 'published'
indexing: 'index'
---
**直接答案：`Tool call result truncated` 通常不代表 MCP 协议规定了统一的 64KB 上限，而是客户端展示限制、工具结果限制、模型上下文预算、序列化体积或传输消费速度中的某一层先触顶。正确修复不是静默截断，而是让 Tool 返回有界结果、总量信息和可继续读取的 cursor/offset；需要完整内容时，再按页读取或先生成摘要与索引。**

> **2026-09-03 版本说明：** MCP `2026-07-28` 规范和 TypeScript SDK v2 都已经进入稳定线。官方 SDK 仍把 stdio `maxBufferSize` 的默认值设为 10 MB；这是 SDK 读取缓冲区的实现边界，不是 MCP 协议对 Tool Result 的统一上限。v1.x 仍处于官方承诺的过渡维护期，因此排查截断时必须先确认客户端实际使用的是 v1 还是 v2，再区分协议规则、SDK 缓冲区和客户端展示限制。

## 本文解决的问题：信息丢失的物理重置

- 为什么我的 MCP Server 在读取一个 1MB 的日志文件时，Cursor 提示 `Tool call result truncated`？
- 如何在 Stdio 缓冲区溢出前，优雅地告诉 AI「还有更多内容未读」？
- 为什么简单的物理截断（如 `text[:5000]`）会导致 AI 产生幻觉？
- 在处理海量数据库查询结果时，如何设计具备「感知力」的流式反馈机制？

---

## 适合谁读

- AI 系统开发者：正在编写涉及大数据量交互的自定义 MCP Server。
- Agent 架构师：需要解决 Agent 在处理长文档、长日志时的「上下文贫血」问题。
- 全栈工程师：在调试本地私有云 Agent 时，频繁遇到协议层报错或响应超时的技术人。

---

## 一、病因拆解：先区分协议、客户端与上下文上限

排查大结果失败时，第一步不要先猜“MCP 只有 64KB”。MCP 的 stdio 传输要求客户端与 Server 通过 stdin/stdout 交换合法的 JSON-RPC 消息，规范本身没有声明一个统一的 64KB 工具结果上限。更可靠的做法是用可重复的本地 fixture 逐步放大结果体积，同时记录原始字节数、序列化字节数、客户端接收长度、耗时和错误层级。

真正需要逐层检查的是：客户端是否限制单次 Tool Result 的显示或注入长度、模型剩余上下文是否足够、JSON 序列化后的消息是否过大、宿主进程是否及时消费 stdout，以及工具是否在超时前完成读取。操作系统管道缓冲区可能影响写入是否阻塞，但它不是“超过某个固定字节数就必然截断”的 MCP 规则。

因此，排查时应先记录原始结果字节数、序列化后字节数、客户端实际收到的长度、耗时和截断标记，再决定使用分页、cursor、范围查询、摘要或对象存储链接。官方 MCP 分页适用于 `resources/list`、`tools/list` 等列表操作；自定义 Tool 的大结果需要在 Tool Schema 中自行设计 cursor/offset 和明确的 `has_more`。

---

## 二、 解决方案 A：物理分页与二级召唤

不要试图一次性喂饱 AI，要教它「翻页」。

### 1. 建立 Offset 机制
日志按行读取时，建议明确使用**行偏移量**，不要将 Python 文本文件的 `seek()` 位置与 `os.path.getsize()` 的字节长度混用。下面的示例按现行 MCP Python SDK v2 的 `MCPServer` / `@mcp.tool()` 接口编写，同时限制可访问的文件根目录：

```python
from pathlib import Path
from mcp.server import MCPServer

mcp = MCPServer("Bounded Logs")
ROOT = Path("/srv/agent-readable").resolve()  # 替换为允许访问的日志目录

@mcp.tool()
def read_large_file(filename: str, offset: int = 0, limit: int = 100) -> dict:
    """按行分页读取允许目录内的日志，不返回无界结果。"""
    if offset < 0 or not 1 <= limit <= 200:
        raise ValueError("offset >= 0 且 1 <= limit <= 200")
    target = (ROOT / filename).resolve()
    if not target.is_relative_to(ROOT) or not target.is_file():
        raise ValueError("文件不在授权目录中或不存在")
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

这是一个基于 [MCP Python SDK v2 官方 Tool 注册方式](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/servers/tools.md)的**有界输出**演示，不是常数时间的日志索引：为了统计总行数仍需扫描文件。超大日志应改用预先建立的行号/字节索引或数据库 Cursor；生产环境还需限制单行字节数、核验访问权限及最大返回体积。

### 2. 在 System Prompt 中注入「翻页逻辑」
必须明确告诉 AI：「如果检测到 metadata.status 为 partial_success，你必须主动调用下一页，严禁根据残缺信息进行臆测。」

---

## 三、 解决方案 B：语义压缩（The Semantic Shrink）

物理截断是粗暴的，它会切断逻辑链。真正硬核的做法是在 Server 端进行「感知压缩」。

### 核心结论：不要让 AI 读原始数据，要让它读「审计报告」。

对于大日志，可以先在 Server 端生成可追溯索引，再让 Agent 按需展开，而不是把所有原始文本一次塞进 Tool Result。例如：
1. 去重：按错误类型、堆栈指纹或业务错误码聚类，同时保留每类出现次数；
2. 范围采样：保留启动阶段、故障窗口和末尾状态，并记录原始行号/时间范围；
3. 关键词召回：为 `ERROR`、`FATAL`、`RETRY` 等信号建立索引，但允许调用方按时间或 cursor 继续读取原文；
4. 证据回链：每条摘要都带 `source_range`、校验值或可继续读取的 URI，避免摘要把关键上下文彻底丢掉。

这种方法的目标是减少一次 Tool Call 的上下文压力，同时保持“摘要可以回到原文”的证据链。实际压缩比例和诊断效果取决于日志结构、过滤规则、模型与任务，本文没有做统一 benchmark，因此不应写成固定的压缩倍数或准确率提升。

---

## 四、 对比块：物理截断 vs 逻辑压缩

- 物理截断 (str[:limit])：
    - 优点：实现简单，额外处理成本较低。
    - 缺点：可能切断 JSON 结构或核心逻辑，导致 AI 产生幻觉（Hallucination）。
- 逻辑分页 (Pagination)：
    - 优点：保证了数据的完整性，AI 具备自主决策权。
    - 缺点：增加了对话轮次（Multiple Turns），增加了 Token 消耗。
- 语义压缩 (Summarization)：
    - 优点：最高效，AI 一次性获得高质量上下文。
    - 缺点：Server 端需要额外的算力（如调用本地小模型或更复杂的逻辑）。

---

## 五、 常见坑与报错 (Error Logs)

### 1. Error: `JSON-RPC message exceeds max length`
- 原因：这是具体 Client、SDK、代理层或宿主应用给出的大小限制，不是 MCP 规范统一规定的 1MB 阈值。
- 对策：先查看报错来自哪一层，再记录序列化后的消息大小；避免把 Base64 图片或二进制流直接塞进 Tool Result，改为返回受控 URI、摘要和分段读取参数。

### 2. Error: `Tool Execution Timeout`
- 现象：Server 逻辑似乎已经完成，但 Client 仍报告超时。
- 排查：分别记录业务读取耗时、JSON 序列化耗时、写出耗时和 Client 超时配置。超时可能来自查询本身、消息过大、传输背压或宿主超时，不能只凭现象断定 stdout 被某个固定缓冲区截断。

---

## 2026-07-28 协议边界：无状态化不等于大结果自动安全

MCP 2026-07-28 已把协议核心推进到无状态请求/响应模型，并加入可缓存的 list 结果与新的路由、授权机制。但这并不会自动消除 Tool Result 过大、宿主上下文窗口不足、客户端展示截断或应用层超时。换句话说：**协议代际升级解决的是连接与请求语义，不替你解决 10MB 结果应该如何分页、摘要和恢复。**

因此本文的 Offset 分页、语义压缩和“让模型读取审计结果而不是原始海量数据”的策略仍然属于应用层控制。协议变化可对照 [MCP 官方 2026-07-28 规范发布说明](https://blog.modelcontextprotocol.io/posts/2026-07-28/)，远程 Endpoint 则可以先用 [XBSTACK MCP Inspector](/tools/mcp-inspector/) 做只读预检。

## 六、 常见问题解答

### Q: 既然 stdio 容易受到本地进程和宿主限制，为什么不全换成 Streamable HTTP？
A: 两者面向的部署边界不同。stdio 适合由 Client 启动的本地 Server，不需要单独监听端口；Streamable HTTP 更适合远程、多客户端和需要认证、会话与网络可观测性的服务。更换传输并不会自动消除 Tool Result 过大或模型上下文不足的问题。

### Q: 如果我必须提供一个 10MB 的 CSV 表格怎么办？
A: 不要把完整文件直接嵌入 Tool Result。把文件保存到经过权限控制、Client 可访问的位置，返回 URI、文件大小、校验值、字段摘要和允许的读取范围；随后由另一个读取 Tool 按行、分片或查询条件取回必要内容。

### Q: 如何判断我的 Server 是否发生了截断？
A: 同时记录原始字节数、序列化字节数、Client 实际收到的字节数、校验值、耗时与 `has_more`。任何固定的 100KB 或 1MB 数字都只能是某个具体 Client 的配置，不能当作 MCP 通用阈值。

---

## 推荐深度阅读

- [MCP 官方传输规范：stdio 与 Streamable HTTP](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [MCP 官方分页规范：cursor 与支持分页的列表操作](https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/pagination)
- [MCP 专题：协议、Server、部署与排错入口](/ai/mcp/)
- [MCP Resources、Tools、Prompts、Roots 有什么区别？](/ai/mcp-protocol-deep-dive/)
- [MCP Stdio 污染与 -32700 Parse Error 排查](/ai/mcp-json-rpc-parse-error/)
- [MCP Streamable HTTP 部署：远程传输、会话与安全边界](/ai/mcp-streamable-http-deployment/)
- [MCP 安全治理：Tool 权限、路径与高风险操作](/ai/mcp-security-best-practices/)
- [MCP Server 生产治理：超时、权限、可观测性与恢复边界](/ai/mcp-server-production-governance/)
