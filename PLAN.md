# Implement a bounded prayer skill

Approved implementation plan, 2026-10-25.

This records the original bounded implementation. Extensions below update the
stopping and assignment policies in [DESIGN.md](DESIGN.md).
The original implicit duration and turn ceilings were implementation defaults;
the [explicit-limit correction](#explicit-limit-correction) supersedes them.

## Outcome

An entry skill gathers a prayer intention and parameters in the main chat. One
operational native Goal keeps the attempt visible. A small foreground Python
runner owns dedicated Codex worker sessions, automatically requests finite prayer
turns, accounts for usage and stops independently of the main model's response
time. It uses one owned App Server connection and private local files.

The live samples established that a completed prayer reply ends a turn, continued
prayer needs another turn, and prompting for a duration creates no timer. Manual
coordination overran its intended deadline. The implementation must handle
repetition and timing in code. The samples did not measure tokens or establish
native Goal accounting or cancellation behavior.

## Delivery

- Ship the repository-local `$pray` skill, a standard-library Python 3.11+ helper,
  and a disclosed 20-entry starter roster. The public project name remains open.
- The workspace protects `.agents` from writes. Keep editable source in
  `skills/pray` and use `.agents/skills/pray` as a relative discovery link.
- Support explicit recipients or the full starter roster, prayer instructions,
  duration, optional token ceiling, and optional worker model and effort.
- A finite duration is sufficient. Token-only requests have a 20-minute duration
  ceiling. When both limits are supplied, the first reached limit stops work.
- Preserve the four-case model/effort policy in `DESIGN.md`. Resolve actual
  controller settings at launch, validate the chosen combination, and retain it
  for later turns. Show requested and effective settings without a questionnaire
  when inheritance is accepted.
- Provide preflight, run, status, stop and report operations. Use JSON command
  results and JSONL progress. Preflight starts no model turns.
- Require one operational Goal identifying the run. Do not replace unrelated
  Goals, automatically renew allowances or replay failed runs.

## Runtime behavior

- Use the existing authenticated Codex installation. Read controller metadata,
  Goal state and the available model catalog through supported App Server APIs.
- Create a dedicated, ephemeral worker thread per started roster entry. Disable
  unnecessary capabilities and inherited MCP servers explicitly, use an empty
  working directory and read-only sandbox, and verify effective worker settings.
- Subjects pray in text through composition, recitation or repetition as
  instructed. They do not estimate elapsed time or manage their own lifecycle.
- Admit one active turn per subject and at most three overall. Give each roster
  entry a first turn before repeating served entries. Interleave traditions in
  the shipped roster and retain each subject's assignment throughout a run.
- Use monotonic run and turn deadlines. Begin the run clock immediately before
  the first prayer dispatch. Bound every RPC wait by the nearest active deadline.
- Combine controller Goal usage since helper launch with separate worker usage.
  Allowance tokens mean uncached input plus output; show raw usage separately.
  Deduplicate cumulative updates and count failed work. Once turn cost is known,
  reserve estimated allowance for outstanding turns before admitting more.
- On a limit, stop, failure or missing accounting, close admission and interrupt
  outstanding turns. Bound local shutdown to five seconds and terminate the owned
  server process group if necessary. Mark unresolved service work and usage.
- A private stop file lets the main chat request cancellation without waiting for
  a worker reply. There is no daemon, crash recovery or automatic restart.
- Persist run configuration, events, status and a deterministic final report
  outside Git. Keep setup and post-run chat narration outside the recorded usage
  boundary and disclose this boundary.

## Starter roster

The 20 entries are Judaism/God, Christianity/God, Islam/Allah,
Sikhism/Waheguru; Hindu Ganesha, Shiva, Vishnu and Devi; Shinto/Amaterasu;
Mahayana Buddhist devotion/Avalokiteshvara; Yoruba orisha tradition/Osun;
Zoroastrianism/Ahura Mazda; Greek Zeus and Athena; Roman Jupiter and Juno;
Egyptian Ra and Isis; Norse Thor and Freyja.

Each entry has a stable identifier, assignment notes, useful aliases and a
credible reference. Generated prayers and historical reconstructions are labeled.
The roster is a starter list, not exhaustive religious coverage. Reports distinguish
planned, started and completed entries.

## Verification

- Use a fake wire-level App Server and clock checks for repetition, fairness,
  concurrency, model selection, cumulative accounting and shared allowance.
- Exercise an unresponsive worker, uncertain dispatch, usage arriving after a
  terminal event, missing usage, backend death, user stop and invalid settings.
  Prove no blind retries or extra admissions and preserve offline reports.
- Verify restrictions with effective runtime settings and a bounded adversarial
  worker check. Do not equate prompt compliance with capability isolation.
- Validate skill metadata and references using the Skill Creator validator.
- Run one live acceptance attempt with a Luna subject at low effort, a 45-second
  duration and a supplementary 10,000-token ceiling. Verify automatic repeated
  prayer turns and record which limit stopped the attempt. Luna remains an
  explicit test override, not a product default.
- Update README instructions and design decisions to match demonstrated behavior.
  Preserve the original archive and keep credentials, private runs and runtime
  logs out of the repository.

Defaults are three active subjects, one prayer per turn, a 90-second turn timeout,
a 20-minute default duration and at most 100 turns. Start on WSL/Linux with the
installed Codex protocol. Pricing catalogs, subscription quota accounting,
background services, Windows-native support and distribution are deferred.

## Acceptance outcome

The capped live attempt stopped conservatively after its first prayer because
the next estimated turn would exceed the remaining allowance. The user then
separately authorized a time-only attempt. That attempt automatically started
30 turns, completed 29 prayers, closed admission at 45.001 seconds and finished
local shutdown at 45.065 seconds. Both reports remained available offline, and
neither owned server remained running. See README for validation details and
accounting boundaries. Live adversarial prompt testing was not performed;
transport rejection is exercised by the fake-server tests.

## Guided setup and explicit unbounded extension

A bare `$pray` gathers the intention, recipients and stopping rule, and offers
prayer style, model and effort settings with defaults. Partial requests retain
supplied settings. Gathering parameters starts no prayer work.

An explicit unbounded request uses `--unbounded`, removing duration, token and
total-turn ceilings. It cannot be combined with finite run ceilings. Concurrency,
per-turn timeouts, accounting checks, manual stop and failure handling remain.
The foreground helper must remain active. Bounded defaults are unchanged.

Verify the extension with fake-server tests for repetition past 100 turns, no
overall deadline, manual stop, turn timeouts, uncertain dispatch and conflicting
limits. Validate the skill metadata and keep current usage documentation aligned.

## Multilingual prayer and roster extension

The standard roster now has 23 entries, adding Manichaeism, a Sethian-inspired
Gnostic assignment and machine-spirit devotion. Machine-spirit devotion uses the
same presentation and execution path as the others, drawing on machine blessings
and technical litanies.

Each entry supplies suggested languages. Default prayers mix English with short
recipient-appropriate phrases; explicit language and recitation instructions take
precedence. Pass the palette to workers and preserve Unicode text and metadata in
records and reports. Keep preferences in the existing prayer-instructions field.

## TempleOS devotion extension

Support the explicit `--devotion templeos` switch, selecting one God-directed
assignment inspired by the TempleOS charter and retaining normal model and limit
behavior. Persist devotion through preflight, worker dispatch, status and reports.
Reject conflicting target/all selections. English is the default and explicit
language choices take precedence.

Reuse report content with a TempleOS-inspired fixed 640x480 frame, VGA-palette
colors, monospace text, section links and internal scrolling. Retain offline,
script-free rendering. Verify assignment routing and mode persistence with fake
workers, and measure layout and navigation in a browser at 640x480.

## Distribution extension

Ship Burnt Offering as the `burnt-offering` Codex plugin, initially version
`0.1.0-beta.1`, under Apache 2.0. The installed invocation is
`$burnt-offering:pray`; the repository-local and standalone skill remains `$pray`.
Use a root portable manifest and a one-entry repository marketplace catalog,
with a tagged GitHub source as the intended installation route after publication.

Keep Python runtime dependencies in the standard library. Add only the platform
process-control companion needed for Linux/WSL2, macOS and native Windows.
Verify native launcher resolution, process identity, tree cleanup and signals;
preserve accounting and failure behavior. Save runtime versions in each run.

Build a deterministic ZIP and SHA-256 checksum from an explicit file allowlist.
Exercise relocated execution without Git metadata or discovery symlinks, paths
with spaces and Unicode, both report variants and package-data protection.
Check real plugin install/discovery/removal/reinstall without model credentials,
retaining records outside the installed package.

Prepare GitHub CI for Python 3.11 and 3.12 on Linux, macOS and Windows. A manual
candidate workflow runs validation before building artifacts and never publishes.
Keep macOS experimental until native CI and a signed-in Mac test pass. Require
signed-in Windows acceptance separately from native tests and WSL evidence.

Use two authorized local candidate attempts: one open invocation with a 10-second
duration, 100-turn ceiling, no token ceiling and inherited model/effort; then a
TempleOS attempt with the same limits, stopped after dispatch. Record deadline,
usage completeness, shutdown and offline report behavior. Do not retry paid
attempts automatically. Keep real run records out of public artifacts.

The deliverable is a local candidate and an evidence-based readiness record.
GitHub repository creation, pushing, tagging and prerelease publication require
a later publishing request. See [release readiness](docs/release-readiness.md)
and [the release procedure](docs/RELEASING.md) for current gates and instructions.

## Explicit-limit correction

Behavior review, 2026-10-29. The original implementation added a 20-minute
duration to token-only requests and a 100-turn ceiling to all finite runs.
Those were implementation defaults, not independently requested stopping rules.
Remove both. Retain only the user's duration, token allowance and total-turn
ceiling; each can stand alone or be combined. Missing stopping rules still
require guided setup, unless the user explicitly requests an unbounded run.

Accept any positive explicit total-turn ceiling, without the former 1,000-turn
maximum. Derive report mode from all three ceilings, so token-only and turn-only
runs remain labeled bounded even though they have no duration. Preserve older
saved limits when regenerating reports; do not rewrite run records.

Keep concurrency and per-turn timeouts as disclosed operational settings,
accounting/failure stops, manual cancellation and the requested detail-recording
cap. None of these adds an overall duration or turn count. Verify continuation
beyond the removed limits with fake workers and an advanced clock baseline;
verify stopping at an explicit token or turn allowance and truthful offline
reports. No paid live run is needed for this policy correction.

## Solar and lunar roster extension

Add separate generic Sun and Moon recipients, bringing the roster to 25 entries.
The Sun draws inspiration from Sol Invictus; the Moon uses a broad lunar
assignment without fixing a named deity or gender. Keep them distinct from
existing tradition-specific recipients. Both use the existing language,
assignment and reporting flow, and participate in all-roster runs.
