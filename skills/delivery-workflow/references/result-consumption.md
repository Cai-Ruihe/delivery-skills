# Result handling at an adopted task boundary

Use only for rounds adopting the local guard. It checks declared records and its callers; it does not authenticate native identities, discover dependencies, grant authority or accept products. Small standalone work needs no guard state.

At assignment/resume, check the current expected binding. At a selected QA wait/switch boundary, prefer the [composed step](delivery-step.md) to manually assembling repeated paths. Composed apply and relevant final-decision dispositions require the explicit PM appointment in [record rules](guard-records.md); legacy raw entry is not a way around an affected refusal. Its current view is generated from existing state, not a second ledger. Resolve stale/absent evidence before dependent work; independent work and authorized settlement retain their original routes.

The PM obtains supported original-role `read_thread`/`wait_threads` evidence. File existence, an active partial report, transport acceptance and a role label do not prove terminal processing. An ephemeral reviewer remains that reviewer; never fabricate a native witness to fit the schema.

Preparation presents the complete fixed report without consumption. PM reads the findings and limits and chooses a scoped disposition. Only an actual successful consumption return supports “consumed”; it is still not product acceptance. Negative findings are consumable. Exact duplicates do not create another obligation or authorize replay. Changed content cannot replace the retained first marker.

## Existing CLI remains supported

```sh
python3 -I -B GUARD --root ROUND --state STATE check-assignment --expected EXPECTED
python3 -I -B GUARD --root ROUND --state STATE consume-result --result RESULT --witness OBSERVATION
python3 -I -B GUARD --root ROUND --state STATE next-action --request ACTION
python3 -I -B GUARD --root ROUND --state STATE check-transition --request TRANSITION
python3 -I -B GUARD --root ROUND --state STATE reconcile
```

Use exact paths to one installed release. State is relative to root; other relative paths are relative to the state directory. Optional repeated `--read-root` permits fixed references only; writes remain in root. Static symlink/escaping-path checks refuse known aliases; concurrent directory replacement is outside this non-sandbox guarantee. Do not recursively interpret arbitrary report strings as asset paths.

Read only the applicable contract:

- Creating/changing structured assignment, action or decision records: [record schema](guard-records.md).
- Using raw wait/switch, independent or settlement checks: [transition rules](transition-checks.md).
- An appointed end-review obligation: [review channels](review-channels.md).
- A selected Python test: [bound local step](bound-local-step.md).

Exit 0 denotes a successful local disposition, including waiting/inspection; 2 denotes affected refusal or required reconciliation/consumption; 3 denotes malformed input. None proves a downstream action ran. Native waiting remains a foreground host call, not durable subscription. No routine ACK, second coordinator or retry loop is supplied.
