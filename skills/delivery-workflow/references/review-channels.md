# Appointed end-review evidence

Read only for an existing authorized end review. See [management review](management-review.md) for responsibilities. Reconcile reports obligations, never sends or wakes anyone.

End-review state: required/key/owner/request_path/reply_path. A request alone is prepared. A submission.native_receipt_ref pins source=send_message_to_thread, key, recipient and raw tool_result. Optional native_observation_ref binds source/key/recipient/turn_id/status/request_message_ids. Accepted/started plus partial file never clears an obligation, even with consumed_ref.

Final consumption requires original native completion, or its started observation plus REVIEW_COMPLETED/reviewerThread/sourceCloseoutSHA256 matching this exact request. Explicit reviewer/hash contradictions are rejected in both routes; absent optional legacy fields remain legal. Store consumed_ref only after actual final consumption. No extra ACK ritual.

For an already-agreed **shared_file** route, both end-review state and fixed request declare channel=shared_file. The request names exact recipient, closeoutPath/closeoutSHA256. This mode cannot be downgraded by additional native-message fields.

Supply supported original-reviewer observation (`read_thread`/`wait_threads`, original thread_id/host_id, key/recipient/turn_id and raw status inProgress/completed). Its shared_file object pins request_ref/reply_ref and nonempty processed_item_ids from actual native execution items proving this exact request was processed and final artifact produced/read back. They are not fabricated message IDs.

PM must inspect those supported records: a running role, filesystem hash or CLI fixture alone is not processing/identity proof. Exact final ABI is mandatory even if the reviewer's whole turn ended. Wrong/partial/stale bindings retain the obligation. Changed content cannot replace first consumed_ref. Same-version rereads create no new obligation/effect.

A transport failure or Unknown submission is not permission to send again. Keep the same logical request, supported query route and actual pending owner in existing state. Safe stopping never waits for review/ACK. The file adapter does not watch files or start a reviewer/PM; continuation requires separate actual host evidence. An ephemeral independent check must be reported as such, never mislabeled as the original native reviewer.
