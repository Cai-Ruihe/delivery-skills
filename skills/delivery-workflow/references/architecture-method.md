# Architecture judgment and simpler mechanisms

Read for consequential design, disputed boundaries or recurring structural failures. Scale depth to risk; this is not a mandatory bug-review gate.

**Frame:** recover user value and non-negotiable constraints. Select concrete quality scenarios: stimulus, operating context, expected response and acceptable cost/failure. Inspect actual boundaries and evidence independently. Identify which assumption would invalidate the route.

**Diagnose:** reproduce the failure and inspect a contrasting case. Trace incorrect assumptions, duplicated state, binding time, invariant owners and compensating obligations. Recurrence is a signal, not proof of architectural cause. Distinguish a local implementation defect from a model that forces callers to keep compensating.

**Compare:** keeping/local repair is appropriate for contained defects in a sound boundary. Boundary consolidation moves an invariant to its rightful owner and removes duplicate obligations. Mechanism replacement needs evidence that the current mechanism's premises cannot meet the outcome. Compare credible alternatives, not a compulsory three-option form for every fix. State changes in concepts/state/dependencies/coordination, actual behavior, necessary safeguards and migration cost. Extra adapters, flags or validators are suspect when they hide an invalid model; legitimate compatibility/security layers may remain. Shorter code or more abstraction is not proof.

**Choose:** return an executable minimal direction, counterevidence, discriminating check, affected owners and adoption/binding authority. For material decisions record reasons and consequences in the existing ledger. Explain which old code, state, procedure or assumption exits; new mechanisms must not accumulate indefinitely.

**Migrate and verify:** use a scoped reversible sequence, defined rollback and relevant compatibility checks. Reproduce the original failure, test adjacent success and boundary failures, inspect real consumer evidence at required scope. Keep old/new ownership unambiguous during transition. Preserve required invariants: externally mandated safeguards change only through their controlling authority; internal mechanisms can change under existing implementation/effect grants, without another approval ritual. New evidence may favor keeping the current design.

**Emergency:** a bounded patch can restore service sooner. Record coverage/remaining risk, owner and observable repayment trigger: recurrence, spreading temporary branches, restored prerequisite or next modification of that seam. On trigger, revisit the model and retire the patch when justified; a vague backlog promise is insufficient. No automatic rewrite, deadline extension or new effects.

Use applicable engineering/research evidence for foundational/system-wide changes; ordinary diagnosis needs the relevant evidence, not a literature ceremony. Philosophical consistency cannot substitute for measured behavior or final acceptance.
