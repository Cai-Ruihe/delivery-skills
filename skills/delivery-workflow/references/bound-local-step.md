# Selected local Python step

Use only at an explicitly adopted caller for one reviewed, harmless local Python
test. This is not an OS sandbox, native-tool hook, identity authentication or
global enforcement. Flags cannot isolate arbitrary side effects. Never relabel a
denied network, browser, SQL or credential operation as local.

```sh
python3 -I -B BOUND_STEP --root ROUND --state STATE --expected EXPECTED
```

`BOUND_STEP` is `delivery-workflow/scripts/bound_step.py`, importing the adjacent
fixed `delivery_guard.py`. Pin both in the adopted package. State paths, repeated
`--read-root` and assignment/grant/review pointers follow the
[result consumer](result-consumption.md). Writes stay within `ROUND`.

## Request

Both current assignment and `EXPECTED` include:

```json
{
  "bounded_step": {
    "adapter": "python-test-file",
    "entry_ref": {"path":"selected_test.py", "sha256":"ACTUAL_SHA256"},
    "action_ref": {"path":"action.json", "sha256":"ACTUAL_SHA256"},
    "timeout_seconds": 2,
    "outputs": {
      "stdout":"step-output/stdout.bin",
      "stderr":"step-output/stderr.bin",
      "receipt":"step-output/receipt.json"
    }
  }
}
```

Both refs must match current `candidate_refs` or `input_refs`. The action declares
`operation:local_test`, `local_only:true`, `additional_external_usd:0`, and the
actual granted scope/capabilities. Declarations grant no authority. Declare
QA-dependent operations in existing `dependent_actions`; consume the matching
fixed report through a real supported original-QA observation first. Synthetic
witness fixtures never authenticate a real role.

The adapter compares expected task/round/revision/roles and refs, verifies actual
files, calls the existing action policy, validates duration/output declarations,
and launches only that Python entry using isolated mode, no bytecode and no
stdin. There is no shell/command interface. Observation timestamps alone do not
change identity. Duration must be finite, positive and at most ten seconds, with
duration plus five seconds remaining. Three output paths must be distinct and
unused. Run through this entry, not a detached precheck followed by another tool.

## Result and limits

Consume the CLI decision, exit code, raw streams and receipt together.
`RUN_COMPLETED`/exit0 proves the selected direct child returned zero with local
evidence; it is not product acceptance. Pre-launch refusal stops only this
proposed action; independent legal work remains available. Deadline/cancellation
checks are invocation observations, not continuous monitoring.

Late failures can occur after execution. Preserve `child_started`, `primary` and
`known_child`; never translate them into nonexecution or blindly replay.
`STEP_UNCERTAIN/RECEIPT_ALREADY_EXISTS` retains the first receipt and reports known
child/failure state. Preserve already-retained streams too. Retention failure
does not permit another execution.

The same Popen handle communicates/waits; timeout handling targets only that
known direct child and closes its streams. Retaining 65,536 bytes per stream is
not a capture-memory bound. No grandchild/global closure, malicious-entry
isolation, unadopted-caller protection or atomic validation-to-launch guarantee
is supplied. Unknown execution requires supported reconciliation. Safe stopping
never waits for ACK. Installation, actual caller adoption and independent
acceptance require separate evidence; author fixture comparisons supply none of
those by themselves.

For a first or changed caller, append `--check-only` to the same argv for read-only execution-contract validation. It opens no outputs and starts no child; the execution entry rechecks. An adopted task_context_ref also limits selected input/output paths; see [caller contract](caller-contract.md).
