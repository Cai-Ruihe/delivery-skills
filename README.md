# Delivery Skills

Six Codex skills for turning an agreed request into a verified result: a standalone execution core, a role router, and four focused delivery roles.

**Version:** 2026-10-02 public snapshot. This repository contains the current skill content, with portable documentation and examples. It does not include private project records, implementation logs or earlier Git history.

## Skills and dependencies

| Skill | Purpose | Required local dependencies |
|---|---|---|
| [multi-agent-dev](skills/multi-agent-dev/SKILL.md) | Execute, debug, research or produce artifacts; delegate only useful bounded work | None of the delivery skills |
| [delivery-workflow](skills/delivery-workflow/SKILL.md) | Choose the delivery role needed for a substantial project | The four delivery roles and execution core |
| [delivery-pm](skills/delivery-pm/SKILL.md) | Assign, supervise, integrate and accept project outcomes | Shared delivery-workflow references and execution core |
| [delivery-architect](skills/delivery-architect/SKILL.md) | Diagnose consequential technical disputes and recurring defects | Shared delivery-workflow references and execution core |
| [delivery-prepare](skills/delivery-prepare/SKILL.md) | Prepare an unresolved request for an existing delivery owner | Shared delivery-workflow references and execution core |
| [delivery-work-chat](skills/delivery-work-chat/SKILL.md) | Execute or verify one bounded project assignment | Shared delivery-workflow references and execution core |

Install the five `delivery-*` folders together with `multi-agent-dev` so their relative links resolve. The core may also be installed alone; it has no file dependency on the delivery suite. A small task needs neither a PM nor additional workers.

Some conditional preparation/design workflows refer to `grill-with-research`, `prepare-work-spec` and `split-work-into-tickets`. These companion skills are not bundled. When such a workflow is needed, provide an authorized compatible installation or report the missing capability; do not claim to have applied an unavailable skill. Ordinary execution does not load them.

## Install

Inspect the files and choose a reviewed revision before installing. Clone this public repository, then run the following from its root in Bash or Zsh. The preflight refuses to replace any existing skill directory; for an update, review differences and back up your installation first.

```sh
git clone https://github.com/Cai-Ruihe/delivery-skills.git
cd delivery-skills
```

```sh
(
  skills_root="${CODEX_HOME:-$HOME/.codex}/skills"
  for skill in multi-agent-dev delivery-workflow delivery-pm delivery-architect delivery-prepare delivery-work-chat; do
    if [ -e "$skills_root/$skill" ] || [ -L "$skills_root/$skill" ]; then
      printf 'Existing skill requires an explicit update: %s\n' "$skill" >&2
      exit 1
    fi
  done
  mkdir -p "$skills_root" || exit 1
  for skill in multi-agent-dev delivery-workflow delivery-pm delivery-architect delivery-prepare delivery-work-chat; do
    cp -R "skills/$skill" "$skills_root/$skill" || exit 1
  done
)
```

If copying fails after some folders are installed, inspect that partial state before retrying. Reload or start a session according to your host's skill-discovery behavior. To install only the standalone core, copy `skills/multi-agent-dev` into your host's skills directory after checking that the destination is absent.

## Use

Invoke a known role directly. Use the router when the accountable role is undecided. These examples use fictional local projects:

```text
Use $multi-agent-dev to fix the rounding bug in this sample calculator and verify the result. Complete it directly if delegation adds no value.

Use $delivery-workflow to choose the role needed for this sample inventory application.

Use $delivery-pm to deliver the agreed sample inventory feature, supervise bounded assignments, and verify the actual consumer outcome.

Use $delivery-architect to diagnose why the sample importer rejects this fixed test file; return evidence and a discriminating check.

Use $delivery-prepare to prepare this unresolved sample feature request for the existing PM, preserving settled decisions.

Use $delivery-work-chat to complete this bounded sample parser assignment, verify its acceptance, and return the artifact and evidence to the integration owner.
```

## Operating limits

Skills are instructions, not an agent runtime or an automatic scheduler. Invocation does not create chats, launch workers, change model settings, grant access or authorize external effects. Your host must provide the relevant tools, permissions and supported lifecycle controls.

The snapshot preserves `gpt-5.6-sol / medium` as the execution-orchestrator preset and `gpt-5.6-luna / max` for default workers. Active user/project policy applies. Model availability varies; requested settings are not evidence of the effective profile. Disclose a required unavailable profile rather than silently substituting it.

Three starting workers and review after five failed substantive repairs are provisional defaults, subject to earlier stop conditions and host capacity. Worker success, local checks, target application and consumer acceptance are distinct. No benchmark here establishes efficiency, production compliance or an optimal cadence. See the [design limits](skills/delivery-workflow/references/design-basis.md) and [evaluation guidance](skills/multi-agent-dev/references/evidence-research.md).

Public preparation included content review and secret scanning. These checks cannot guarantee that every sensitive detail has been detected. Keep credentials, customer data and private task context outside public repositories and delegation envelopes.

## License

Repository materials are distributed under the [MIT License](LICENSE). The inherited execution core retains its [MIT notice](skills/multi-agent-dev/LICENSE); see [NOTICE](NOTICE.md) for attribution and the boundary around linked third-party sources. See [SECURITY.md](SECURITY.md) for safe reporting.
