# Delivery Skills

Seven independently callable Codex skills for delivering the requested observable capability. **Version: delivery-skills-2026-10-18-r1.** The execution core works alone for small tasks without PM, Architect, QA or workers. The runtime files are identical to the reviewed frozen candidate; source-stage labels alone imply neither installation nor publication.

## Choose an entry

| Entry | Responsibility |
|---|---|
| [multi-agent-dev](skills/multi-agent-dev/SKILL.md) | Scoped execution, useful delegation and integrated evidence |
| [delivery-workflow](skills/delivery-workflow/SKILL.md) | Select a role only when genuinely unclear |
| [delivery-pm](skills/delivery-pm/SKILL.md) | Autonomous coordination, supervision, integration, obtaining required acceptance and direct reporting |
| [delivery-architect](skills/delivery-architect/SKILL.md) | Independent high-level judgment of goals, assumptions, simplicity and evolution |
| [delivery-prepare](skills/delivery-prepare/SKILL.md) | Prepare an unresolved substantial request while preserving settled decisions |
| [delivery-work-chat](skills/delivery-work-chat/SKILL.md) | Return one bounded assignment's fixed artifacts and actual evidence |
| [delivery-qa](skills/delivery-qa/SKILL.md) | Independently derive and judge product acceptance, coverage and delivery claims |

Roles are responsibilities, not seven mandatory resident agents. PM coordinates internally and reports directly to the user; an external human-user proxy is optional, never an internal monitor, required relay or recovery fallback. QA is not a second PM. Architect does not become a routine approval layer or the integrator.

Read the selected entry and only references whose triggers apply. Links are not a recursive reading queue. See [context loading](docs/context-loading.md) and [public release changes](docs/changes.md). Private development history is separate and is never required to run these skills.

## Install or update

Choose and inspect a reviewed revision of this repository:

```sh
git clone https://github.com/Cai-Ruihe/delivery-skills.git
cd delivery-skills
```

Install the six `delivery-*` folders with `multi-agent-dev` so relative links resolve. Core can be installed alone. Use your host's skills directory, such as `skills` under `CODEX_HOME` or the user's `.codex` directory.

For a fresh installation, confirm destinations are absent. For an update, back up the actual current folders, including whether the new QA folder already exists, and replace complete chosen folders. Overlaying can retain retired rules. Verify the exact file set and bytes, formats and links; preserve unrelated skills and inspect partial failures before retrying. Rollback must cover the added QA folder too. Follow host discovery/reload behavior; installation promises no live-context refresh, scheduler or recovery mechanism.

Conditional preparation/design workflows may use separately available `grill-with-research`, `prepare-work-spec` or `split-work-into-tickets`; they are not startup dependencies. Report an unavailable required capability rather than claiming it was used.

## Synthetic examples

```text
Use $multi-agent-dev to fix a defect in this sample calculator and verify the relevant local result. Zero workers is valid.
Use $delivery-pm to integrate this sample importer through its required entry and report the actual consumer result.
Use $delivery-architect to independently compare local repair, boundary consolidation and mechanism replacement for this sample configuration problem.
Use $delivery-qa to derive checks from the approved sample requirements before inspecting the fixed candidate and author verdict.
Use $delivery-work-chat to complete this bounded parser assignment and return fixed evidence to its integration owner.
```

## Evidence and authority

Defaults remain **GPT-6.1-Sol / medium** for the orchestrator and **GPT-6-Luna / max** for workers; owner/project/host policy prevails. Requested profiles are not effective-identity proof. Existing specialized role UI/policy settings are retained. No role grants access, deployment, retries, extensions or external effects.

One execution loop, one product-acceptance protocol and conditional host-continuity detail replace overlapping responsibilities. Product checks occur at plan, first real flow and final candidate when applicable; these opportunities can coincide. QA retains scoped findings and accepts fixes or counterevidence. Local checks, deployment and actual product acceptance remain different claims. Authorized verification deployment may precede a final consumer verdict; missing product evidence remains open.

User-required three-hour independent Architect checkpoints, including HOLD, remain binding; prompts create no wakeup guarantee. Existing safety, single-writer, uncertain-send, cumulative-budget and expiry controls remain. Ordinary already-authorized reads or dependency acquisition need no extra role approval. Unknown effects cannot be automatically replayed. Stopping development is not evidence that resource billing stopped.

Independent static review and four bounded fresh-context synthetic actor tasks support the checked local outcomes only. An initial QA exercise did not explicitly check one historical acceptance record; a later directed question checked its applicability. This is not an unprompted initial pass. These observations are not full scenario coverage, a model benchmark, rendered UI or production acceptance, host-control proof, or measured efficiency improvement. Private fixtures, answers and review evidence are not distributed.

## Maintenance and privacy

Before changing the suite, consult applicable owner-designated history under local access policy and record reasons, human direction, superseded approaches, lessons and actual validation limits. Missing private history is a stated maintenance gap, not a runtime prerequisite. Private histories, internal sources, reviews, backups, real cases and evaluation fixtures/oracles/runs stay out of this repository and public packages. Only generic instructions and synthetic examples belong here.

## License

[MIT](LICENSE). Preserve the inherited [core MIT notice](skills/multi-agent-dev/LICENSE). See [NOTICE](NOTICE.md) and [SECURITY](SECURITY.md).
