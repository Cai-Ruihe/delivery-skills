# Delivery Skills

Six independently callable Codex skills for delivering an observable result. **Version: delivery-skills-2026-10-04.** The execution core also works alone for small projects without PM, Architect or workers.

## Choose an entry

| Entry | Responsibility |
|---|---|
| [multi-agent-dev](skills/multi-agent-dev/SKILL.md) | Scoped execution, useful delegation and integrated acceptance |
| [delivery-workflow](skills/delivery-workflow/SKILL.md) | Select one delivery role when it is unclear |
| [delivery-pm](skills/delivery-pm/SKILL.md) | Autonomous sequencing, supervision, bounded research, integration and acceptance |
| [delivery-architect](skills/delivery-architect/SKILL.md) | Independent judgment of goals, assumptions, boundaries, simplicity and evolution |
| [delivery-prepare](skills/delivery-prepare/SKILL.md) | Prepare an unresolved substantial request without repeating settled discovery |
| [delivery-work-chat](skills/delivery-work-chat/SKILL.md) | Complete an existing bounded assignment with the execution core |

Read the selected entry, then only references whose actual triggers apply. Links are navigation, not a recursive reading queue. Background research, historical records, cases and evaluation answers are not bundled startup context. See [loading paths](docs/context-loading.md) and [changes](docs/changes.md).

## Install or update

Choose and inspect a reviewed revision. Clone this public repository:

```sh
git clone https://github.com/Cai-Ruihe/delivery-skills.git
cd delivery-skills
```

Install the five `delivery-*` folders together with `multi-agent-dev` so relative links resolve. The core can be installed alone. Use your host's skills directory; common Codex installations use the `skills` folder under `CODEX_HOME` or the user's `.codex` directory.

For a fresh installation, copy the chosen folders only after confirming their destinations are absent. For an update, back up the existing folders, review differences and replace each complete chosen folder; overlaying leaves retired rules behind. Check all local links, preserve unrelated skills and inspect partial failure before retrying. Use your host's documented discovery/reload behavior; no automatic scheduler or live-context refresh is promised.

Conditional preparation/design workflows may need separately installed `grill-with-research`, `prepare-work-spec` and `split-work-into-tickets`. They are not bundled or ordinary startup requirements. Report an unavailable required capability rather than claiming to use it.

## Use

These examples are synthetic:

```text
Use $multi-agent-dev to fix a rounding defect in this sample calculator and verify the relevant result. Zero workers is valid.
Use $delivery-pm to deliver the agreed sample importer capability, check its riskiest real boundary early, supervise bounded work and integrate acceptance.
Use $delivery-architect to independently assess the sample importer's repeated configuration failure; compare local repair, boundary consolidation and mechanism replacement.
Use $delivery-work-chat to complete this bounded sample parser assignment and return fixed artifacts and actual checks to its integration owner.
```

## Host and evidence limits

Defaults remain **GPT-6.1-Sol / medium** for the execution orchestrator and **GPT-6-Luna / max** for workers. User/project/host policy prevails; requested profiles are not proof of effective identity. Existing role UI settings are retained; roles grant no access or external effects. Invocation creates neither workers nor an unattended timer.

Three initial workers and review before a sixth failed substantive repair remain provisional backstops, subject to earlier constraints and material risks. Local checks, target application, consumer acceptance and parent acceptance are different claims. This version passed structural, link, content and byte checks; no model behavior benchmark establishes autonomy, quality, token savings or efficiency improvement.

The repository contains generic instructions and synthetic examples, without private project evidence, source mappings, backups, internal reports, research workspaces, credentials or evaluation oracles.

## License

[MIT](LICENSE). The inherited core keeps its [MIT notice](skills/multi-agent-dev/LICENSE). See [NOTICE](NOTICE.md) for attribution and third-party boundaries, and [SECURITY](SECURITY.md) for safe reporting.
