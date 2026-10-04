# Security Policy

## Supported versions

Security fixes apply to the latest tagged release.

## Reporting a vulnerability

Use GitHub private vulnerability reporting from the repository's **Security** tab. Do not disclose credentials, private repository content, private prompts, personal information, or exploit details in a public issue.

If private vulnerability reporting is unavailable, open a public issue containing only a request for a private contact channel. Do not include the sensitive details themselves.

Useful reports identify the affected release, the relevant instruction or boundary, the smallest safe reproduction, the observed effect, and the expected behavior.

## Security boundaries

Particularly relevant issues include:

- prompt injection or untrusted repository content escaping a task envelope;
- credential, private-context, or personal-data disclosure;
- delegation that expands tools, permissions, data access, or external effects;
- multiple writers modifying the same mutable surface;
- unsafe retries after partial external effects;
- duplicate execution after ambiguous worker creation, delivery, termination, or outcome;
- spoofed worker identity or requested model/effort presented as observed execution evidence;
- model fallback that is reported as the required profile;
- a subagent claiming root completion or bypassing Sol verification.

The skill does not make an agent, tool, repository, or external service trustworthy. Active host controls, project instructions, sandboxing, permissions, and human approval boundaries remain authoritative.
