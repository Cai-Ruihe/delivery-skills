# Failure patterns and transferable checks

Maintenance only. These are generic examples for applying the runtime references, not a report about a particular project or measured performance.

| Possible failure | Useful check | Maintained source |
|---|---|---|
| Author tests pass while a consumer rejects an input shape | Exercise the actual consumer in the first complete slice | [verification](verification.md) |
| A partial external write changes unrelated data | Exercise relevant atomicity, idempotency and preservation faults | [verification](verification.md) |
| A deployed artifact lacks evidence of requested adoption | Check actual consumer and parent acceptance; preserve partial states | [verification](verification.md) |
| Repeated findings never change subsequent assignments | Verify the previous correction and assign an observable next action | [self-review](self-review.md) |
| Required source coverage is unavailable | Check capability and acceptance meaning before implementation | [verification](verification.md) |
| Repeated polling or scaffolding adds no new evidence | Use changed evidence and the last working route | [delegation](delegation.md), [recovery](recovery.md) |
| An operation times out with an uncertain result | Reconcile authoritative state before retrying | [recovery](recovery.md) |

These checks do not establish universal causality, savings or an optimal cadence. Evaluate authorized comparable tasks with consistent acceptance and budgets; include incomplete outcomes and review/recovery costs. Static validation cannot demonstrate actual efficiency gains.
