---
name: delivery-workflow
description: Select a delivery role when organizing a substantial project and the accountable PM, request preparation, technical challenge or bounded execution role is not yet chosen.
---
<!-- Runtime revision: 2026-10-02 -->
# Delivery Workflow

Choose only the role needed for the current outcome; this router does not run the project or require separate chats.

| Need | Direct entrypoint |
|---|---|
| Daily assignment, supervision, integration and project acceptance | [delivery-pm](../delivery-pm/SKILL.md) |
| Bounded diagnosis of a consequential technical dispute or recurring defect | [delivery-architect](../delivery-architect/SKILL.md) |
| Prepare a genuinely unresolved substantial request for an existing PM | [delivery-prepare](../delivery-prepare/SKILL.md) |
| Execute or verify an existing bounded project assignment | [delivery-work-chat](../delivery-work-chat/SKILL.md) |

An already selected role loads its entrypoint directly. A small or standalone task uses [multi-agent-dev](../multi-agent-dev/SKILL.md), with zero workers valid; no PM, Architect, router or project record hierarchy is required.

Each delivery role reads the short [project contract](references/contract.md) once. PM additionally reads its [daily cycle](references/pm-cycle.md). Execution uses the independently installable multi-agent-dev core and its conditional references. Reuse unchanged instructions; after compaction recover the active role, current controlling evidence and necessary rules, not the whole directory.

The five delivery folders are one installation unit requiring the separate multi-agent-dev core. Core never references delivery. Keep entrypoints and each runtime reference below 500 English words; split by actual activity, not arbitrary length. Maintenance research remains outside the daily reading path.

Role invocation does not create chats, launch agents, change model settings or authorize effects. Use existing authorized owners and supported tools. Root/Dot handles consequential exceptions and missing capabilities; PM remains the daily project owner.
