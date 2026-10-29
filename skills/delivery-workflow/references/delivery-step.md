# Compose a current-result decision

Use for an adopted guarded assignment at resume, waiting or result disposition. It reuses guard rules and the existing Python test entry; no scheduler, generic command executor, global hook or new authority is provided. Use the same release for all three scripts.

```sh
python3 -I -B STEP --root ROUND --state STATE --expected EXPECTED view
python3 -I -B STEP --root ROUND --state STATE --expected EXPECTED prepare --witness OBSERVATION
python3 -I -B STEP --root ROUND --state STATE --expected EXPECTED apply --witness OBSERVATION --disposition CHOICE
```

STEP is `../scripts/delivery_step.py`. EXPECTED is the fixed assignment already handed to the caller. Do not manufacture expected from live state to hide a mismatch. Paths/pointers follow [record rules](guard-records.md). Example: state `records/state.json` with adjacent assignment uses `--expected expected.json`, not `--expected records/expected.json`.

For first/changed callers use [caller contract](caller-contract.md); complete the generated disposition_draft instead of recopying fixed fields.

**View:** checks expected/current binding and authority source, projects existing records. The original requirement remains authoritative; inspect relevant records if this projection is insufficient.

**Prepare:** builds the existing wait transition without a temporary file. Returns WAIT, RECONCILE or READY_FOR_PM_DECISION with full report, result_ref and current view. No consumption/write occurs. Already-consumed results need no new witness. If output is truncated, read the exact result file fully before deciding. Non-reference report strings are not recursively opened.

**Decide:** PM reads findings and limits; stores an explicit disposition in its existing decision record:

```json
{
  "binding": {"project":"demo","round":"current","task":"slice","revision":"r1"},
  "pm": {"thread_id":"owner","host_id":"local"},
  "pm_authority_ref": {"path":"appointment.json","sha256":"actual digest"},
  "candidate_refs": [], "input_refs": [],
  "result_ref": {"path":"qa.json","sha256":"actual digest"},
  "disposition":"repair", "reason":"Explain the evidence-led next step",
  "accepted_scope": [], "remaining":["Required capability still unproved"]
}
```

Use the pinned PM appointment in [record rules](guard-records.md), independently of the product author. No appointment means no composed apply, even for an already consumed result; preserve facts and reconcile only the affected decision. Fill actual candidate refs; choices are accept_scope/repair/escalate/defer. Optional next_action_ref pins an existing action. Fields cannot prove PM understanding or authenticate identity.

**Apply:** rechecks current inputs, validates the disposition, invokes existing consume (including negatives), then checks an optional next action against refreshed state. Only the actual return supports consumed. A refusal after consumption preserves that fact. No successor runs by default.

Only when the assignment already selects a bounded Python test and next_action_ref matches its action, add `--run-selected`. This calls original bound_step in the same branch; STOP never starts that child. A first-attempt claim beside consumption markers binds the task and fixed action, independently of output names. Existing claims refuse replay, even if no final receipt exists; reconcile the original attempt. Claim creation precedes Popen; the claim alone does not establish whether a child started or finished. Output collisions also refuse reuse. Never delete claims/outputs to retry. New revisions retain actual authorization and repair limits; no exactly-once guarantee is supplied.

Other tools use their original authorized entry; ordinary independent actions/settlement retain [transition checks](transition-checks.md). Never chain an unconditional command after refusal. Native wait/read remains a supported active-call boundary; tool completion does not prove product acceptance or future wakeup.
