# Mocked / Placeholder Metrics

> **Purpose**: This file tracks every KPI or metric that is currently hardcoded
> (i.e., not fetched from the backend). Each entry lists the element's `id`,
> the current placeholder value, and the API endpoint that should replace it
> once the backend route is implemented.
>
> All mocked elements carry the HTML attribute `data-mock="true"` so they can
> be audited quickly with: `grep -r 'data-mock' templates/`

---

## agent_dashboard.html

| Element ID | Placeholder Value | Real Source | Notes |
|---|---|---|---|
| `agentThroughputCount` | `42 Cases` | `GET /api/agent/stats` → `throughput_today` | Count of cases processed by this agent today |
| `agentAvgTime` | `4.2 mins` | `GET /api/agent/stats` → `avg_inspection_time` | Rolling 24-hour average triage time |
| `agentAccuracy` | `99.4%` | `GET /api/agent/stats` → `accuracy_pct` | Percentage of AI verdicts confirmed by agent |
| `agentQueuePending` | `18 Pending` | `GET /api/complaints?status=pending` → `total` | Live queue depth |
| `agentCriticalCount` | `3` | `GET /api/complaints?priority=P0&status=open` → `total` | Count of unresolved P0 critical alerts |
| `agentVisionAccuracy` | `99.2%` | Gemini audit log aggregation | Requires a new `/api/gemini/vision-accuracy` endpoint; depends on logging infra |
| `agentActiveChatsCount` | `5 Online` | `GET /api/chat/active-count` → `active` | Number of currently open WhatsApp sessions |

---

## refunds.html — CLV Optimizer KPIs

> The three KPIs inside the CLV Optimizer card are loaded via
> `GET /api/escrow/clv-optimizer/{customerId}` when a customer is selected.
> They are **not** hardcoded globally — they default to `--` until a customer
> is chosen. **No action required here**, but listed for completeness.

| Element (visible label) | Default | Real Source |
|---|---|---|
| Retention Probability | `--` | `/api/escrow/clv-optimizer/{id}` → `retention_probability` |
| Churn Risk | `--` | `/api/escrow/clv-optimizer/{id}` → `churn_risk` |
| CLV Ceiling | `--` | `/api/escrow/clv-optimizer/{id}` → `clv_ceiling` |

---

## How to Wire Up a Mocked Metric

1. Implement the backend route listed in the table above.
2. In the relevant JS file, add a `fetch()` call after DOM load, e.g.:

```js
// Example: hydrate agentThroughputCount
fetch('/api/agent/stats')
  .then(r => r.json())
  .then(data => {
    const el = document.getElementById('agentThroughputCount');
    if (el && data.throughput_today !== undefined) {
      el.textContent = `${data.throughput_today} Cases`;
      el.removeAttribute('data-mock');   // mark as live once wired
    }
  })
  .catch(() => { /* keep placeholder on error */ });
```

3. Remove the `data-mock="true"` attribute from the element **and** delete the
   corresponding row from this table once the metric is live.

---

*Last updated: 2025 — maintained by the SupportNova engineering team.*
