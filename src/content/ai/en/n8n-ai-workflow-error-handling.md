---
hideStructuredBlocks: true
title: 'n8n Error Handling: Error Workflows, Retry On Fail, Timeouts, and Failed Execution Retry'
description: 'Handle n8n rate limits, timeouts and node failures with Error Workflows, bounded Retry On Fail, execution history, idempotency and controlled data retention.'
seoTitle: 'n8n Error Handling: Error Workflows, Retries & Timeouts'
seoDescription: 'Design n8n error handling with Error Workflows, bounded Retry On Fail, failed-execution retry, execution-data retention, idempotency and AI cost tracking.'
geoSummary: 'n8n error handling separates bounded node Retry On Fail, final failure alerting via a configured Error Workflow, and controlled failed-execution replay. Diagnose 429, authentication and task-runner timeouts separately; preserve execution evidence and make external writes idempotent.'
primaryKeyword: n8n Error Handling
keywords: 'Productionizing n8n AI Workflows, n8n, workflow, monitoring, error-handling, Error Handling, Retries, Timeouts, and Cost Monitoring, n8n Error Handling, n8n AI workflow, n8n automation, webhook, queue mode'
category: ai
subcategory: Workflow
tags:
  - n8n
  - workflow
  - monitoring
  - error-handling
slug: n8n-ai-workflow-error-handling
image: ../../../assets/covers/standardized/cogview4-798f05e9-8792df7c-1200x630.webp
mood: high-energy
location: Guiyang
queries:
- How do I configure an Error Workflow in n8n?
- When should an n8n node use Retry On Fail rather than an Error Workflow?
- How should an AI workflow handle 429 rate limits, 401 failures and timeouts?
- Can I retry an n8n failed execution with the original workflow?
- How do I avoid duplicated external writes after a retry?
- How do I record LLM token usage, costs and failure alerts in n8n?
entities:
  - 'n8n Error Handling'
  - 'n8n'
  - 'workflow'
  - 'monitoring'
  - 'error-handling'
  - 'n8n AI workflow operations'
  - 'Error Handling'
  - 'Retries'
  - 'Timeouts'
  - 'AI cost monitoring'
faqs:
  - question: >-
      How can I prevent LLM billing overruns caused by infinite retry loops in
      n8n?
    answer: >-
      For transient failures, enable Retry On Fail and set a bounded retry count
      plus Wait Between Tries. Do not continuously retry authentication, invalid
      parameters, or other deterministic failures. If you need exponential
      backoff, model it explicitly with a Wait/Code/sub-workflow step and make
      every external write idempotent so a retry cannot duplicate side effects.
  - question: How should I resolve SQLite database lock errors?
    answer: >-
      SQLite can be appropriate for a small single-instance setup, while higher
      concurrency and queue-mode deployments should evaluate PostgreSQL. First
      inspect concurrency, execution-data retention, and the running n8n version;
      do not assume every lock issue has the same database root cause.
  - question: >-
      How do I handle AI tasks taking several minutes if the Webhook peer does
      not support long connections?
    answer: >-
      Avoid holding an external HTTP request open for a multi-minute AI task.
      Return an acknowledgement early and move the long-running work behind a
      Wait node, queue, sub-workflow, or callback pattern. Preserve an execution
      ID or business ID so the caller can correlate the asynchronous result.
  - question: >-
      How do I sanitize error logs containing sensitive information (e.g., API
      Keys or user passwords)?
    answer: >-
      After the Error Trigger node, use a Code node to write a JavaScript
      filtering function. Use regular expressions to identify patterns like sk-
      for LLM API keys, or key-value pairs containing password or token, and
      replace them with asterisks. This reduces the risk of secrets being written to logs or alert channels, but regex redaction is not complete. Combine it with field allowlists, secret scanning, least privilege, and restricted log access.
note: >-
  This article focuses on production n8n error handling, bounded retries, execution history, and cost-control boundaries.
imageAlt: >-
  Productionizing n8n AI Workflows: Error Handling, Retries, Timeouts, and Cost
  Monitoring
description_en: >-
  A detailed breakdown of exception handling, rate-limiting protection, token
  cost calculation, and failure replay mechanisms in self-hosted n8n AI
  workflows to build a highly available production-grade automation system.
imageAlt_en: >-
  Productionizing n8n AI Workflows: Error Handling, Retries, Timeouts, and Cost
  Monitoring
clusterHub: '/en/ai/workflow/'

createdAt: '2026-06-17'
lang: 'en'
route: '/en/ai/n8n-ai-workflow-error-handling/'
canonical: 'https://www.xbstack.com/en/ai/n8n-ai-workflow-error-handling/'
hub: 'workflow'
translationKey: 'ai:n8n-ai-workflow-error-handling'
translations:
  zh-CN: '/ai/n8n-ai-workflow-error-handling/'
  en: '/en/ai/n8n-ai-workflow-error-handling/'
translationStatus: 'published'
translationSource: '/ai/n8n-ai-workflow-error-handling/'
translationSourceHash: 'c78bb0b882dbe02b8df62dd4a267ca7a9ac7ae4e191520525e1ebd651b56f49b'
indexing: 'index'
---

**Direct answer: n8n error handling has three separate layers. Use node-level Retry On Fail only for bounded transient failures; route final workflow failures to an Error Workflow for logging and alerts; and retain failed executions so you can retry with the current or original workflow. Any database write, message send, ticket creation, or other side effect still needs its own idempotency key.**

One timeout class should not be sent straight into a retry loop: if the Code node reports **`Task request timed out` / `Your Code node task was not matched to a runner`**, the JavaScript task may not have reached a runner at all. Check Task Runner registration, broker connectivity, runner authentication, worker sidecars, and capacity before rerunning business logic. See [n8n Code Node Task request timed out: Task Runner troubleshooting](/en/ai/n8n-code-node-task-runner-timeout/) for the isolated reproduction and recovery path.

## Who This Guide Is For

- Developers who have deployed a self-hosted n8n instance on personal servers and are already implementing LLM-powered automation workflows in production business environments.
- Architects who need to productize complex AI Agent systems and have strong requirements for data flow stability, billing transparency, and fault self-healing.
- Self-hosted workflow builders who want less manual intervention while preserving explicit alerts, human review, and safe recovery boundaries.

## Production-Grade AI Workflow Pain Points and Self-Healing Design

The core challenge of production-grade AI workflows lies in their high degree of non-determinism. Unlike traditional automated pipelines assembled from deterministic APIs, AI workflows must contend not only with physical-layer jitter such as transient server network drops but also with semantic-level anomalies like model hallucinations, format corruption, large model API rate limits (Rate Limit 429), and context window overflow (Context Overflow).

The hard production question is not whether a node can fail; it is whether the workflow knows which failures are retryable, which must alert and stop, whether external writes can be repeated safely, and whether a failed execution can be reproduced later. In a [Gmail summarization workflow](/en/ai/n8n-ai-gmail-summarizer-openai-google-sheets/), transient network failures, rate limits, authentication errors, and business-validation errors should not all follow the same retry branch.

Moving from a demo to production means treating error capture, bounded retries, execution history, idempotency, data retention, and cost records as separate design concerns. The goal is not a zero-touch “self-healing” system; recover automatically when the failure is understood and safe to retry, and preserve evidence for human review when it is not.

## Exception Triggering and Retry Strategies Are the Foundation of System Resilience

In a self-hosted n8n topology, the first line of defense against failures is the combination of a global error trigger and node-level retry backoff.

n8n provides us with two dimensions of error self-healing mechanisms at the system level:

### 1. Global Error Trigger Node

As the [official n8n Error Workflow documentation](https://docs.n8n.io/build/flow-logic/handle-errors-gracefully/) explains, an Error Workflow must be configured for each monitored workflow, rather than automatically becoming a universal listener across the entire n8n instance. Create an alerting workflow beginning with Error Trigger, then configure it as the error workflow for each source workflow that should use it. When any node in your main workflow encounters an uncaught critical error (such as external service authentication failure or database downtime), the n8n engine will automatically interrupt the current execution and throw metadata context—including Workflow ID, Execution ID, Error Message, and the failing node name—directly to this catch flow. Using this mechanism, we can uniformly log exception metadata into a local PostgreSQL database, achieving system-level error visibility.

### 2. Bounded Node Retries: Retry On Fail + Wait Between Tries

For model APIs, HTTP Request nodes, and other third-party services, enable Retry On Fail for transient network failures or rate limits and set a bounded retry count plus Wait Between Tries. Current n8n node settings support bounded retries; do not describe exponential backoff as one universal toggle that every node exposes.

If the workflow needs a 5s → 10s → 20s schedule, calculate it explicitly with a Wait node, Code node, or sub-workflow. Classify failures first: temporary rate limits and 5xx responses may be retryable, while invalid parameters, missing permissions, and business-validation failures usually should go straight to the Error Workflow. Side-effecting operations must be idempotent so a successful retry does not create duplicate writes.

## Execution Context and State Preservation for Failed Tasks

In production environments, disk space on self-hosted instances is extremely precious. If you haven't configured logging properly during the **[Docker container self-hosted deployment](/en/ai/self-hosted-n8n-ai-workflows/)**, the node input/output caches generated by tens of thousands of successful executions daily will quickly fill up your NAS SSD.

To balance disk usage with enough evidence for debugging, we need to adjust the runtime parameters in **`docker-compose.yml`** to retain the full context only for failed tasks:

```yaml
environment:
  EXECUTIONS_DATA_PRUNE: "true"
  EXECUTIONS_DATA_MAX_AGE: "336"
  EXECUTIONS_DATA_SAVE_ON_ERROR: "all"
  EXECUTIONS_DATA_SAVE_ON_SUCCESS: "none"
```

After capturing the failed execution context, we need to structure the error logs and store them in our Postgres relational database to enable automatic breakpoint replay after system recovery. Below is the database table I designed, which includes token cost calculations, retry counts, and payloads:

```sql
CREATE TABLE IF NOT EXISTS ai_workflow_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    failed_node VARCHAR(255) NOT NULL,
    error_message TEXT,
    payload JSONB,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    cost_usd NUMERIC(10, 6) DEFAULT 0.000000,
    retry_count INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'failed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

An Error Workflow only receives the error context that n8n makes available for the failed execution; it does not automatically capture every upstream input or guarantee zero data loss. Store an explicit, redacted business payload and stable execution ID only when your workflow is authorized to retain them. SQL storage and replay require application-level implementation, access control and idempotency.

## Token Consumption and Cost Monitoring: Establishing a Billing Defense

Extracting and aggregating the `usage` field from large model responses is a critical measure for ensuring financial security.

In the actual operation of the [Notion Knowledge Base Agent](/en/ai/n8n-ai-notion-knowledge-base-agent/), if your knowledge base contains numerous PDFs or long text segments spanning tens of thousands of words, vector retrieval (RAG) can cause context consumption to skyrocket to hundreds of thousands of tokens in a single execution. This can happen if the Top-K limit fails or if a user initiates a malicious long-text injection. If we do not monitor the cost of every large model call, the project may be forced to shut down due to uncontrolled costs before you even see the large bill at the end of the month.

Do not assume every model node, provider, and version exposes identical `usage.prompt_tokens` and `usage.completion_tokens` fields. Adapt cost collection to the actual provider/node response. For long-lived accounting, persist provider, model, raw usage, and timestamp, then apply a versioned pricing table instead of hard-coding one model's rates into the workflow.

To automatically analyze costs in the background, we can place a Code node after the large model node and use JavaScript to convert token counts into actual dollar costs:

```javascript
const items = $input.all();
const results = items.map(item => {
  const data = item.json;
  const usage = data.usage || { prompt_tokens: 0, completion_tokens: 0 };

  const promptTokens = Number(usage.prompt_tokens ?? usage.input_tokens ?? 0);
  const completionTokens = Number(usage.completion_tokens ?? usage.output_tokens ?? 0);
  const totalTokens = promptTokens + completionTokens;

  // Keep volatile model pricing outside the workflow.
  const inputCostRate = data.pricing?.input_per_token || 0;
  const outputCostRate = data.pricing?.output_per_token || 0;
  const calculatedCost = (promptTokens * inputCostRate) + (completionTokens * outputCostRate);

  return {
    json: {
      raw_response: data,
      token_metrics: {
        prompt_tokens: promptTokens,
        completion_tokens: completionTokens,
        total_tokens: totalTokens,
        cost_usd: parseFloat(calculatedCost.toFixed(6))
      }
    }
  };
});
return results;
```

With this metric in place, any single processing cost that exceeds the set threshold will automatically trigger an alert in subsequent workflow steps and log the result to the `cost_usd` field of `ai_workflow_logs`, allowing you to trace and restrict high-cost tasks.

## Rate Limiting Protection and Webhook Timeout Control

Traffic shaping and asynchronous decoupling ensure that your local self-hosted environment won't suffer cascading failures when faced with surges in external concurrency.

### 1. Webhook Timeout Control (Immediate Response)

This is a critical design flaw that is often overlooked. If your webhook trigger is initiated by an external platform (such as GitHub or a third-party form), but your workflow needs to perform complex AI summarization in the backend (which might take 1 minutes), the default behavior is for the webhook node to remain suspended while waiting for the entire workflow to finish before returning a result. However, external callers typically enforce strict timeout limits at the network protocol level (e.g., 10 seconds or 30 seconds). Once this timeout is reached, the caller assumes the delivery failed and may initiate continuous retries. This causes n8n to repeatedly launch the same time-consuming workflows, instantly clogging your compute queue and wasting large amounts of LLM tokens.

If the caller has a short timeout while the backend task is much longer, set **Respond** to `Immediately` or use `Respond to Webhook` to control the response explicitly. Current n8n documentation says `Immediately` returns the configured status code and `Workflow got started`; do not assume it automatically returns an execution ID. If the caller needs asynchronous status tracking, create and persist your own `business_job_id`, return an acknowledgement, and update or callback from the background workflow.

### 2. LLM 429 Rate Limiting Protection (Limit & Wait)

LLM APIs have hard limits on RPM (requests per minute). When handling batch processing tasks, we must introduce traffic shaping mechanisms:

- A **Limit** node caps the number of items passing through an execution; it is **not** a shared RPM rate limiter across concurrent executions or workers.
- Use [Loop Over Items and Wait](https://docs.n8n.io/integrations/builtin/handle-rate-limits) to pace a local batch where appropriate, but a fixed 2-second pause does not guarantee compliance with the provider's RPM/TPM quota. For multiple workers, enforce limits in a shared queue or token bucket, honor `Retry-After` where supplied, and bound 429 retries.

The actual 429 error looks like this:

```text
NodeApiError: openai [openai_error]: 429 Too Many Requests
{
  "error": {
    "message": "Rate limit reached for gpt-4o on tokens per min. Limit: 30000, Used: 29847, Requested: 800.",
    "type": "tokens",
    "param": null,
    "code": "rate_limit_exceeded"
  }
}
at Object.execute (/usr/local/lib/node_modules/n8n/node_modules/n8n-nodes-base/dist/nodes/OpenAi/OpenAi.node.js:206:13)
```

When catching and handling this error in n8n's Code node, you can determine whether it is a rate-limiting issue rather than an authentication error by checking for the ``rate_limit_exceeded`` string within the ``$error.message`` string. This allows you to decide whether to trigger exponential backoff retries or raise an alert directly:

```javascript
const errorMsg = $error.message || '';
if (errorMsg.includes('rate_limit_exceeded')) {
  return [{ json: { action: 'retry', reason: 'rate_limit' } }];
} else if (errorMsg.includes('insufficient_quota')) {
  return [{ json: { action: 'alert', reason: 'quota_exhausted' } }];
} else {
  return [{ json: { action: 'alert', reason: 'unknown_error' } }];
}
```

## Failed execution replay: use the official Executions semantics first

The current n8n Executions UI supports two replay paths:

- **Retry with currently saved workflow**: replay failed data against the currently saved workflow;
- **Retry with original workflow**: replay with the workflow version that existed when the failure occurred.

That is a safer long-lived reference than hard-coding an unverified historical REST path as an “official retry API.” If you automate replay, verify the public API or node capability against the exact n8n version you deploy and put retries behind a controlled queue.

Before replaying, confirm whether side effects already happened, whether the upstream webhook may redeliver, whether a stable business idempotency key exists, whether the workflow schema changed, and what the maximum attempts, TTL, and dead-letter or human-review path should be.

Production “self-healing” should mean: **automatically replay only failures that are clearly transient, idempotent, bounded, and observable; route the rest to review or approval.**

## Prometheus + Grafana Monitoring: Making Workflow Status Visible

Self-hosted n8n can enable `/metrics` with `N8N_METRICS=true` and connect it to Prometheus/Grafana. n8n also exposes `/healthz` and `/healthz/readiness` for liveness and readiness checks. Metrics are disabled by default and should not be exposed directly to the public internet. Queue Mode can also expose queue-related metrics for the deployed version.

### Enabling the n8n Prometheus Metrics Endpoint

Add the following configuration to the n8n environment variables in `docker-compose.yml`:

```yaml
environment:
  N8N_METRICS: "true"
  N8N_METRICS_PREFIX: "n8n_"
  N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL: "true"
  N8N_METRICS_INCLUDE_NODE_TYPE_LABEL: "true"
  N8N_METRICS_INCLUDE_CREDENTIAL_TYPE_LABEL: "false"
```

After restarting the container, access `http://your-n8n-host:5678/metrics` to view Prometheus-formatted text metrics. The core fields include:

```text
# HELP n8n_workflow_success_total Total number of successful workflow executions
n8n_workflow_success_total{workflow_id="42"} 1583

# HELP n8n_workflow_failed_total Total number of failed workflow executions
n8n_workflow_failed_total{workflow_id="42"} 7

# HELP n8n_workflow_execution_duration_seconds Workflow execution duration in seconds
n8n_workflow_execution_duration_seconds_bucket{le="1",workflow_id="42"} 1100
n8n_workflow_execution_duration_seconds_bucket{le="5",workflow_id="42"} 1430
n8n_workflow_execution_duration_seconds_bucket{le="30",workflow_id="42"} 1580
```

### Prometheus scrape configuration

Add the n8n scrape job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "n8n"
    scrape_interval: 30s
    static_configs:
      - targets: ["n8n:5678"]
    metrics_path: /metrics
```

If n8n and Prometheus are on the same Docker Compose network, you can use the service name `n8n` directly; for cross-host deployments, replace it with the actual IP address.

### Grafana Panel JSON (Core Panel Snippet)

Import the following JSON into Grafana (Dashboard -> Import -> Paste JSON) to quickly create a workflow success rate panel:

```json
{
  "title": "n8n success",
  "type": "stat",
  "targets": [
    {
      "expr": "sum(rate(n8n_workflow_success_total[5m])) / (sum(rate(n8n_workflow_success_total[5m])) + sum(rate(n8n_workflow_failed_total[5m]))) * 100",
      "legendFormat": "success %",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "thresholds": {
        "steps": [
          { "color": "red", "value": 0 },
          { "color": "yellow", "value": 90 },
          { "color": "green", "value": 99 }
        ]
      }
    }
  },
  "options": {
    "reduceOptions": { "calcs": ["lastNotNull"] },
    "colorMode": "background"
  }
}
```

The PromQL query for the average workflow execution duration, which can be used directly in a Grafana Time Series panel, is as follows:

```text
histogram_quantile(0.95,
  sum by (workflow_id, le) (
    rate(n8n_workflow_execution_duration_seconds_bucket[5m])
  )
)
```

If the P95 latency persists above 30 seconds, it typically indicates that a workflow is waiting for an LLM timeout, and you should immediately investigate the node logs.

### Grafana Alerting Alert Rule Configuration

In Grafana's **Alerting** -> **Alert rules**, create a new alert rule to detect consecutive failures:

```yaml
apiVersion: 1
groups:
  - orgId: 1
    name: n8n_alerts
    folder: n8n
    interval: 1m
    rules:
      - uid: n8n_high_failure_rate
        title: "n8n failed"
        condition: C
        data:
          - refId: A
            queryType: ""
            relativeTimeRange:
              from: 300
              to: 0
            datasourceUid: prometheus
            model:
              expr: >
                sum(rate(n8n_workflow_failed_total[5m])) /
                (sum(rate(n8n_workflow_success_total[5m])) + sum(rate(n8n_workflow_failed_total[5m]))) * 100
          - refId: C
            queryType: ""
            relativeTimeRange:
              from: 300
              to: 0
            datasourceUid: "-100"
            model:
              conditions:
                - evaluator:
                    params: [10]
                    type: gt
                  operator:
                    type: and
                  query:
                    params: [A]
                  reducer:
                    type: last
              type: classic_conditions
        for: 2m
        annotations:
          summary: "n8n failed 10%"
        labels:
          severity: critical
```

The logic for this alert configuration is as follows: if the workflow failure rate exceeds 10% continuously over the past 5 minutes and remains above that threshold for 2 minutes, a critical-level alert is triggered. This alert is then pushed to DingTalk or Feishu bots via Grafana's Contact Points.

## Optimizing Failure Notifications and Alert Channels

A redundant alert path plus data masking can shorten detection and recovery time, but it does not guarantee incident recovery on its own.

When self-healing replay also fails, or when encountering P0-level disasters that require manual intervention—such as API authentication expiration—the system must immediately issue an alert. We can use the HTTP Request node to push structured error cards to DingTalk, Feishu, WeCom, or Slack bots. If your team relies on email on-call rotations, you can also add an SMTP / Gmail node to send the same masked fault summary to the operations email address.

Below is the standard Webhook request body format for pushing alerts to DingTalk bots, which can be configured directly in the Body of n8n's HTTP Request node:

```json
{
  "msgtype": "markdown",
  "markdown": {
    "title": "🚨 n8n",
    "text": "## 🚨 Workflow execution failed\n\nWorkflow: {{ $json.workflowName }}\n\nFailed node: {{ $json.failedNode }}\n\nError: {{ $json.errorMessage }}\n\nExecution ID: {{ $json.executionId }}\n\nOccurred at: {{ $now.format('YYYY-MM-DD HH:mm:ss') }}\n\n[View execution details](http://your-n8n-host:5678/workflow/{{ $json.workflowId }}/executions/{{ $json.executionId }})"
  }
}
```

When configuring this notification node, two defensive measures must be implemented:

- Alert data sanitization: Error messages returned by the LLM API often contain sensitive information such as LLM API keys (e.g., `sk-`), database passwords, or user privacy details within the context. Before forwarding to group bots, you must use a Code node with regular expressions to clean the error body, filtering out sensitive feature strings and replacing them with asterisks to prevent the leakage of sensitive assets over communication channels:

```javascript
const rawError = $json.error?.message || '';
const sanitized = rawError
  .replace(/sk-[a-zA-Z0-9]{20,}/g, 'sk-*REDACTED*')
  .replace(/(password|token|secret|key)\s*[:=]\s*\S+/gi, '$1=*REDACTED*');
return [{ json: { ...$json, sanitizedError: sanitized } }];
```

- **Alert Self-Healing & Isolation**: If your notification bot is temporarily unreachable, directly invoking the HTTP Request node could trigger a Timeout. This would cause a secondary crash in our error-handling flow, intercepting and preventing records that should be written to Postgres from being saved. Therefore, the timeout for the alert-sending node must be capped at `5` seconds, and its On Error setting must be configured to ``Continue On Fail``. We must strictly prevent notification channel failures from polluting our primary logging database.

- **Multi-Channel Degradation**: Instant messaging is ideal for second-level alerts, while email is better for capturing full context. It is recommended to first deliver notifications via IM channels such as Slack, Feishu (Lark), or WeCom, and then compose an email containing the ``execution_id``, failed nodes, sanitized errors, cost fields, and replay links to create a traceable on-call record.

## Continue Reading

- 👉 [n8n AI Workflow Production Portal](/en/ai/workflow/)
- 👉 [Self-hosted n8n AI Workflow in Practice: Docker, Postgres, VPS, and NAS Deployment Guide](/en/ai/self-hosted-n8n-ai-workflows/)
- 👉 [n8n AI Workflow in Practice: Automatically Writing Gmail Summaries to Google Sheets](/en/ai/n8n-ai-gmail-summarizer-openai-google-sheets/)
- 👉 [n8n AI Workflow in Practice: Building a Notion Knowledge Base Agent](/en/ai/n8n-ai-notion-knowledge-base-agent/)
- 👉 [n8n vs Make Comparison: Which is the Ultimate AI Automation Workflow Hub?](/en/ai/n8n-vs-make-ai-workflow-automation/)
- 👉 [n8n Queue Mode + Redis in Practice: High-Concurrency Queue Architecture Guide](/en/ai/n8n-queue-mode-redis-worker/)
