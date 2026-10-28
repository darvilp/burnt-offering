# Burnt Offering

A novelty Codex plugin that spends model turns praying for an intention. Subjects
compose, recite or repeat as instructed. A foreground Python runner requests
successive turns and handles timing, accounting, cancellation and private reports.

Initial candidate: **0.1.0-beta.1**, licensed under **Apache 2.0**.

## Install

Requirements: Python 3.11+, an authenticated Codex CLI in the same environment as
your Codex chat, and the native sandbox required by that installation. The first
tested Codex baseline is `0.164.0`. There are no extra Python runtime packages.

Once the beta release tag is published, install it with the following commands.
The tag is not published yet; use the
[fresh-install candidate check](docs/RELEASING.md#fresh-install-candidate-check)
to test an exact pushed commit before the release:

```bash
codex plugin marketplace add darvilp/burnt-offering --ref v0.1.0-beta.1
codex plugin add burnt-offering@burnt-offering
```

Start a new Codex chat and select Pray from Burnt Offering. The installed plugin's
qualified invocation is:

```text
$burnt-offering:pray
```

This starts guided setup for the intention, recipients, stopping rule and optional
style, language, model and effort. Nothing starts while choices are missing.
Fully specified requests can start without a second confirmation:

```text
$burnt-offering:pray Have an open, nonsectarian subject pray for a safe journey
for 45 seconds.
```

For early testing, Skill Installer can also install `skills/pray` directly from
the GitHub repository. A standalone or repository-local skill is invoked as
`$pray`; a plugin installation uses `$burnt-offering:pray`. The development
checkout's `.agents/skills/pray` symlink is not needed by installed plugins.

## Platform status and setup

| Environment | Candidate status | Setup |
|---|---|---|
| Linux / WSL2 | 49 local tests, plugin lifecycle and signed-in deadline check passed; live early cancellation pending | Run Linux Python and Codex in the same environment. WSL has its own configuration and sign-in. |
| Native Windows | 49 native tests and plugin lifecycle passed; signed-in runtime acceptance pending | Use Windows Python and Codex from PowerShell, with the Codex Windows sandbox set up. |
| macOS | Experimental; native CI and end-to-end acceptance pending | Use native Python and Codex. Automated checks do not establish a signed-in prayer run. |

See [release readiness](docs/release-readiness.md) for actual evidence and pending
checks. WSL results establish Linux behavior, not native Windows behavior.
The port targets current desktop OS releases; other architectures are unverified.

On Linux/WSL/macOS, use `python3` for manual helper commands. On Windows use
`py -3`. The native Windows launcher supports `codex.exe` and the official global
npm installation through its Node launcher. Codex, Python, authentication and
controller thread metadata must all belong to the same environment. Preflight
reports OS, Python and Codex versions and starts no model turns. Missing runtime
capabilities or restrictions are errors, not permission to weaken the sandbox.

## Prayer settings

Optional model and effort apply to subjects, leaving the controller unchanged:

| Supplied settings | Subject behavior |
|---|---|
| Neither | Inherit controller model and effort. |
| Model only | Requested model and its default effort. |
| Effort only | Controller model and requested effort. |
| Both | Requested pair. |

The runner validates and retains these choices. Subjects are helper-owned Codex
worker sessions, not child chats in the sidebar. The main chat creates one native
operational Goal and reports progress; the helper repeats prayer turns without
manual follow-ups.

A finite duration is sufficient. An optional token ceiling stops the run when
reached; token-only runs also have a 20-minute duration ceiling. Allowance tokens
mean uncached input plus output, combined across workers and controller usage
observed during helper execution. Known turn costs reserve allowance for work in
flight. Consumption is approximate near boundaries. Setup before the helper's
baseline and narration after shutdown are outside its recorded allowance.

Defaults are three active subjects, one prayer per turn, a 90-second turn timeout
and 100 turns total. To remove duration, token and total-turn ceilings, explicitly
ask for unbounded execution:

```text
$burnt-offering:pray Have one open, nonsectarian subject pray for peace.
Run unbounded until I stop you.
```

Unbounded runs retain concurrency, per-turn deadlines, accounting and failure
checks. They require the foreground helper and continue consuming tokens until
stopped or a failure occurs. Ask the chat to stop the run and confirm shutdown.
The helper's `--unbounded` option cannot be combined with `--duration`, `--tokens`
or `--max-batches`. Omitting limits does not imply unbounded execution.

## Recipients and languages

The [23-entry roster](skills/pray/references/roster.json) includes living and
historical traditions, Manichaeism, a Sethian-inspired Gnostic assignment and
machine-spirit devotion. “All” means every entry in this disclosed roster, each
with its own subject. First turns take priority over repetitions; reports show
entries that never started when a limit prevents full coverage.

Choose names or stable roster IDs such as `manichaeism`, `gnostic`,
`machine-spirit`, `judaism` or `christianity`. Use tradition-specific IDs for
ambiguous recipients such as God. Custom named recipients are supported.
Machine-spirit devotion draws on machine blessings, workshop benedictions and
technical litanies, with the same presentation and execution flow as other entries.

Subjects default to English mixed with brief recipient-appropriate phrases, such
as Hebrew, Arabic, Sanskrit, Japanese, Latin or Old Norse. Native script or familiar
transliteration is allowed. Explicit language and exact-recitation instructions
take precedence; translations are appended only when requested. Uncertain ancient
wording should fall back to English instead of invented language. Generated wording
and historical reconstructions are distinguished from authenticated liturgy.
Suggested languages in reports describe assignments, not verified language usage.

## TempleOS devotion

```text
$burnt-offering:pray Use TempleOS devotion to pray for a safe journey for 45 seconds.
```

The explicit `--devotion templeos` switch draws on the
[TempleOS charter](https://tinkeros.github.io/WbTempleOS/Doc/Charter.html): computing
as a temple, creative work as an offering and direct, sincere, sometimes playful
biblical-style prayer to God. English is the default; explicit language choices
still apply. The mode selects its own subject, so omit `--target` and `--all`.
It is separate from the standard roster and uses normal model and limit behavior.

Its offline HTML report has a fixed **640 × 480 CSS-pixel frame**, VGA-palette
colors, monospace text, section links and internal scrolling. The selected devotion
is saved, so offline regeneration retains the appearance.

## Reports and private records

Records live under `$XDG_DATA_HOME/prayer-runs`, normally
`~/.local/share/prayer-runs`, outside the checkout or installed package. An optional
global `--data-dir` precedes the helper operation. POSIX files use private modes;
Windows uses the user profile's inherited ACLs, not Unix `0600` guarantees. Use a
private folder if overriding the default. Reports include intentions and examples.

| File | Contents |
|---|---|
| `run.json` | Settings, assignments, model, effort, runtime versions and accounting baseline. |
| `status.json` | Latest aggregate counts, coverage, usage, limits and stop reason, replaced in place. |
| `events.jsonl` | Detailed events within a 32 KiB budget, plus lifecycle and saved-example completion records. |
| `report.html` | Standalone report with settings, coverage, accounting and expandable examples. |
| `report.md` | Terminal-readable report. |

After the next routine event would exceed 32 KiB of serialized UTF-8 data, new
prayer text and per-turn details are omitted. Aggregate counts and accounting
continue. Cap notices, failures, stop records and confirmation of saved examples
are retained, so the final event file can slightly exceed the detail budget.
Oversized examples are omitted whole. Memory uses the same recording policy.
Reports disclose saved-example and omitted-event counts. Terminal progress is
aggregate-only, limited to once per second except immediate state transitions.
Captured terminal output and Codex's own runtime storage are separate from this cap.

Reports work offline without scripts or external assets. Older logs are preserved;
offline report generation streams them and bounds displayed examples. Worker tools,
network access and inherited MCP servers are disabled. No background-survival or
automatic-restart guarantee is provided. A stop request closes admission and begins
bounded cleanup; service work already in flight may exceed an observed threshold.

## Helper commands

From a source checkout, or using the installed skill's absolute script path:

```bash
python3 skills/pray/scripts/pray.py preflight --intention 'A safe journey' --target 'Open invocation' --duration 45
python3 skills/pray/scripts/pray.py status RUN_ID
python3 skills/pray/scripts/pray.py stop RUN_ID
python3 skills/pray/scripts/pray.py report RUN_ID
python3 skills/pray/scripts/pray.py report RUN_ID --format html
```

Preflight returns the run ID, resolved settings and required Goal prefix. Execution
uses the same arguments with `run` and `--run-id`, after the controller creates the
matching active Goal. An unrelated unfinished Goal is never replaced. Controller
discovery uses `CODEX_THREAD_ID`; `--controller-thread` is available explicitly.
Status and report commands make no model request. A missing runner is interrupted.

## Updates, removal and development

Stop active runs before upgrading, rolling back or uninstalling. For this beta,
remove the plugin and catalog, re-add the catalog at the desired release tag, then
install again. Use `codex plugin remove burnt-offering@burnt-offering` and
`codex plugin marketplace remove burnt-offering`. Private records are retained;
delete a finished run's directory yourself when no longer needed.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package.py
```

Tests use fake workers without model requests. The packager produces an
allowlisted ZIP and SHA-256 file under `dist/`. The optional integration check
`python3 scripts/check_plugin_install.py` temporarily installs a uniquely named
catalog/plugin and removes its own entries. It writes Codex plugin state; CI runs
it on disposable accounts without model credentials. See
[release procedure](docs/RELEASING.md) for gates and publishing instructions.

The source repository's `DESIGN.md` is the current design and `PLAN.md` records
prior implementation decisions. The original zip and Markdown remain unchanged
under `docs/archive/2026-10-24/`. Historical designs do not define the current
runtime contract. Working previews and private run records are excluded from the
release archive. No remote service is needed for distribution.
