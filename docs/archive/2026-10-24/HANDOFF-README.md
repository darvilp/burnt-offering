# Agentic Prayer — Implementation Handoff

Design artifacts only. No daemon, skill, or running prayer agents have been implemented.

- `agentic-prayer-technical-design.md`: architecture, models, Codex App Server APIs, state machine, SQLite DDL, reliability safeguards, implementation milestones, and tests.
- `campaign.schema.json`: Draft 2020-12 manifest schema. Cross-field validation for `roster.max_concurrency <= roster.count` and model/quota compatibility must also run in application code.
- `campaign.example.subscription.json`: illustrative subscription quota manifest (limit ID and window must be selected from live preflight; the example is **not** universally valid on every account).
- `campaign.example.api.json`: illustrative metered API manifest (replace placeholder model/pricing catalog version from live discovery before approval).

## Development guidance

Validate manifest schemas without a model call. Build the mock App Server first and confirm strict budget and stop invariants before using paid turns. Do not start a detached campaign without explicit user approval of the exact manifest digest.
