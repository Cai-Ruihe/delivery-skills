# Check the actual caller and current task

Use only when a new guarded assignment adopts `task_context_ref`, or when a real caller's fields/paths are uncertain. No global tool interception, extra approval or recurring ACK is supplied. Never retrofit in-flight assignments or reset consumption/attempt identity.

## Read-only first use

With the real caller's root, state, fixed expected and explicit read roots:

```sh
python3 -I -B STEP --root ROUND --state STATE --expected EXPECTED contract
python3 -I -B BOUND --root ROUND --state STATE --expected EXPECTED --check-only
```

STEP/BOUND are the same release's delivery_step.py/bound_step.py. The second command uses exactly the execution validator but starts no child and creates no outputs. It may refuse because a real dependency remains open; do not bypass it. Remove `--check-only` only at the actual authorized execution boundary. Checks reserve neither permission nor runtime state.

`contract` returns canonical paths, the original scope JSON type, review recipient shape and an incomplete result draft. Optional `--selected` inspects an already selected local test. Relative state uses root; expected and nested references use the state directory. Use `host_id`, not `host` or `operatorHost`. Do not coerce scope lists to strings or vice versa. A review recipient is the configured owner object, not just a thread string. No action generator is supplied.

## One short task reference

Assignment and fixed expected pin `task_context_ref` to one JSON record:

- binding: project/round/task/revision; original `goal_ref`;
- author/qa/pm identities and `pm_authority_ref` under [role rules](guard-records.md);
- deadline_utc matching the current grant;
- surfaces: read/write arrays of explicit paths (relative to state directory);
- release: version and scripts mapping delivery_guard.py, delivery_step.py and bound_step.py to exact path/hash refs from the selected release. Add that release as an explicit read root.

Check at resume and execution; reason from current goals/evidence. The controlled Python entry checks current binding, input and output surfaces before opening outputs. It is not an OS sandbox: arbitrary child/native-tool accesses are not intercepted. Correct exact observed drift; do not repeatedly awaken idle roles without new evidence.

## Handback, not another report

Complete the generated result draft with the real QA turn, verdict and `verification`: executed means a check was actually performed (static or runtime), with fixed evidence_refs; it does not imply runtime coverage. not_run requires no evidence and cannot claim PASS/ACCEPTED/SUCCESS. A not_run verdict listed in a nonempty dependent allow-list is contradictory and refused before consumption. Otherwise it may be consumed for repair/defer, never accept_scope; empty lists still permit any finding. Preserve the same task_context_ref and deadline. Hash checks cannot detect a self-consistent lie: QA/PM must cross-check actual tool activity, candidate and findings. An old date or no-work final contradicting current activity is not acceptance.

`prepare` supplies structural disposition fields once; PM supplies the decision, reason and scope. Drafts with null judgment cannot apply. Native witness requirements stay unchanged. Label ephemeral reviewers honestly; use a witness only when supported read_thread/wait_threads actually observes that exact reviewer and turn. Without that route, consumption remains NOT_RUN; hand off the genuine report without fabricating a source.
