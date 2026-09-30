# Dashboard Measurement Gaps

> Historical inventory, updated for the current implementation. Dashboard values are either live, explicitly unavailable, or still require integration. Earlier entries below included fabricated sample metrics and must not be reused as current evidence.
>
> No `data-mock` audit attribute is currently used.

---

## agent_dashboard.html

| Element ID | Placeholder Value | Real Source | Notes |
|---|---|---|---|
| `agentThroughputCount` | Live resolved-case count | `GET /api/agent/stats` → `resolved_cases` | Total resolved records, not a per-agent daily throughput metric |
| `agentAvgTime` | `Not recorded` until timestamp pairs exist | `GET /api/agent/stats` → `avg_inspection_time` | Uses recorded start/end timestamps only |
| `agentAccuracy` | `Not measured` until comparisons exist | `GET /api/agent/stats` → `accuracy_pct` | Currently averages stored comparison consistency, not a validated agent-accuracy study |
| `agentQueuePending` | Live review count | `GET /api/agent/stats` → `pending_reviews` | Counts Analyzed, Manual Review Required, and Escalated statuses |
| `agentCriticalCount` | Live open P0 count | `GET /api/agent/stats` → `critical_alerts` | P0 records excluding resolved states |
| `agentVisionAccuracy` | `Not measured` | None | Vision analysis provider is not integrated; photo upload is disabled in the portal |
| `agentActiveChatsCount` | `Open desk` | None | No live WhatsApp connector or validated active-session count is configured |

---

## refunds.html — CLV Optimizer KPIs

> Retention/churn estimates are unavailable. The API returns an explicit unavailable reason until verified customer history and an approved model are connected.

| Element (visible label) | Default | Real Source |
|---|---|---|
| Retention Probability | `Not available` | No validated model |
| Churn Risk | `Not available` | No validated model |
| CLV Ceiling | `Not available` | No verified transaction history |

---

## Next integration work

1. Connect a persistent chat provider before reporting active chat counts.
2. Add a validated multimodal provider and human-reviewed evaluation set before reporting vision accuracy.
3. Add payment-service integration, verified transaction records, idempotency, and audit controls before claiming payments are processed.
4. Add timestamp and outcome data collection before reporting SLA or agent-performance rates.

---

*Last updated: 2025 — maintained by the SupportNova engineering team.*
