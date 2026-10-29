# One transition, not a global gate

The existing `check-transition` is read-only. It neither consumes results nor executes successors. Use the [composed step](delivery-step.md) when reducing mechanical assembly helps; existing callers remain compatible.

For `wait_for_qa`, `switch_assignment`, `dependent_action`, supply kind, exact binding (project/round/task/revision), candidate_refs and input_refs. Explicit empty input_refs is valid. Optional result_path must be the assignment's exact path. Supply witness_path for an unconsumed result. Switch/dependent requests additionally name action_path to an existing action request.

- `WAIT_FOR_CURRENT_QA`: supported original QA observation is inProgress. A partial report cannot complete it.
- `CONSUME_RESULT_REQUIRED`: matching completed observation and fixed report exist without valid first consumption. PM must read and dispose positive or negative findings, then consume. Do not describe the QA as still running.
- `RECONCILE_CURRENT_QA`: completed result missing, invalid or stale, or observation unavailable. Find/correct the exact evidence; do not automatically redispatch.
- `TRANSITION_READY`: retained first marker and unchanged result already match. No fresh terminal observation is needed. It proves only this transition; an old negative verdict remains negative.

Changed report or invalid/conflicting marker is refused. A new assignment/revision has its own obligation. A switch also checks the proposed action; settled old QA never permits expired work. A dependent action keeps the existing allowed-verdict policy. Consuming FAIL does not satisfy a PASS-only operation. Cancellation/deadline refusal takes precedence over waiting.

`independent_action` supplies action_path and delegates to next-action. It does not wait for unrelated QA or review ACK; renaming an operation cannot bypass declared dependencies.

`authorized_settlement` also supplies action_path. Only an explicitly granted `local_settle` with effect=local_metadata and local_only=true, or `submit_review` with effect=native_message and exact review recipient/key, qualifies. This may skip QA/decision dependencies after deadline; cancellation, unknown effects, scope, capabilities and cost remain binding. Generic cleanup labels provide no exemption. Read-only reconciliation remains available under existing authority.

All checks have global_stop=false. Exit0 dispositions include WAIT, READY, CONTINUE and INSPECT_ONLY; exit2 includes refusal/reconciliation/required consumption; malformed input exits3. Inspect the decision, not merely the numeric exit status. No observation file is platform authentication or a freshness guarantee. There is no role discovery, polling, cold wakeup, unadopted bypass protection or atomic lock on a later external action.
