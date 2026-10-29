---
name: pray
description: Guide setup, run and monitor novelty prayer subjects for a user-supplied intention, with optional recipients, model and effort. A bare $pray starts guided setup. Ordinary requests to write or discuss a prayer do not authorize an agent run.
---

# Pray

Installed through the Burnt Offering plugin, this skill is named
`$burnt-offering:pray`; standalone or repository-local installation uses `$pray`.
A bare invocation of either name starts the same guided setup.

Coordinate prayer activity in the current chat. Subjects pray in text, including
recitation or repetition when instructed. The local helper requests successive
finite turns and enforces limits; a prompt telling a subject to keep praying is
not a timer. Worker sessions are owned by the helper, not native child chats.

Use Python 3.11+ and the installed, authenticated Codex CLI in the same environment.
Use `python3` on Linux/WSL/macOS or `py -3` on native Windows. Keep the helper's
`process_control.py` alongside `pray.py`; no extra Python runtime packages are needed.
Resolve this skill's directory and invoke its `scripts/pray.py` by absolute path.
The examples below assume the skill directory as the working directory.

## Guided setup

A bare `$pray` begins an interactive setup. Ask what the user wants prayed for;
do not pick an intention or reuse a sample run from earlier conversation. Gather
the missing choices through short questions, grouping related settings when useful:

- Intention: what should the subjects pray for?
- Recipients: an open nonsectarian invocation, named recipients, or the starter roster?
- Stopping rule: a duration, token allowance, total-turn limit, a combination, or explicitly unbounded until stopped?
- Optional settings: prayer style and language, worker model and effort. Offer short invocations
  and inheritance of the controller's model and effort as defaults the user can accept.

For a partial invocation, reuse the supplied parameters and ask only for what is
missing. Use the available question tool or ordinary chat if no question tool is
available. Wait for answers before preflight or creating a Goal. A bare invocation
authorizes setup; launch once the choices are settled and the user has asked to run.

## Establish the run

Reuse the intention, recipient choices, practice and limits the user supplied.
One or more named recipients or `--all` select the roster. The latter means every
entry in [the 25-entry starter roster](references/roster.json), not every known
religion or deity. Show its scope and any likely partial coverage before starting.
Use tradition-specific roster IDs for ambiguous names such as God. Custom targets,
including an open nonsectarian invocation, are supported.

The roster includes Manichaeism, a disclosed Sethian-inspired Gnostic assignment,
and machine-spirit devotion. Machine-spirit devotion follows the same assignment
and reporting flow as the others, drawing on machine blessings and technical litanies.

Each roster entry carries suggested languages. By default subjects mix English
with brief phrases from that palette and may vary the mix across turns. Use native
script or familiar transliteration. Prefer supportable phrases to invented ancient
wording; fall back to English when uncertain. Explicit user language choices and
exact-recitation requests override the default. Carry those choices in the existing
prayer instructions; do not add translations unless requested. Show suggested
languages in the plan, without claiming generated text was linguistically verified.

An explicit request for TempleOS mode or devotion uses `--devotion templeos` on
both preflight and run. It supplies one God-directed subject inspired by Terry
Davis's TempleOS: computing as a temple and offering, and sincere, direct,
sometimes playful biblical-style prayer. English is the default, with explicit
language choices carried in the usual prayer instructions. Omit `--target` and
`--all`; if the user also requests different recipients, resolve that choice
instead of discarding it. Gather any missing intention or stopping rule, while
reusing the supplied devotion. Do not activate the mode merely because TempleOS
is mentioned in an intention. Other requests use the standard devotion.

This mode also selects the fixed 640x480 HTML report. Long content scrolls inside
the frame, with native section links and expandable examples. Preserve the saved
devotion when reporting or regenerating HTML; it does not change run limits.

A finite `--duration` in seconds, `--tokens` allowance or `--max-batches`
total-turn ceiling is sufficient on its own. They can also be combined; the
first reached limit stops the run. The token allowance counts uncached input
plus output across the controller and workers. Apply only the overall limits
the user chose. Do not add a duration to a token-only request or invent a
total-turn cap for a duration-only or token-only request. Ask for a stopping
rule if none was supplied, unless the user explicitly requested an unbounded run.
For an explicit request such as "run unbounded" or "keep praying until I stop you", use
`--unbounded`. It has no duration, token or total-turn ceiling.
Do not combine it with `--duration`, `--tokens` or
`--max-batches`. Omitted settings never imply unbounded execution; "no token
ceiling" alongside a duration is still a duration-bounded run. If instructions
conflict, resolve the intended stopping rule before launching.

Unbounded runs retain concurrency limits, per-turn timeouts, usage checks and
failure stops. Explain that they keep consuming tokens until stopped or a failure
ends the run, and show how to request a stop. They require the foreground helper
and active Codex environment; they do not survive application shutdown.

Optional `--model` and `--effort` apply to all subjects, leaving the controller
unchanged. With neither specified,
inherit the controller's model and effort. Model-only selects that model's default
effort; effort-only retains the controller's model.

Pass user text as safely quoted arguments, never as shell code. A typical preflight
is `python3 scripts/pray.py preflight --intention 'A safe journey' --target 'Open invocation' --duration 45`.
Add explicit model, effort and token arguments only when requested. Preflight
starts no model turns. It reports OS/Python/Codex versions, resolves actual controller settings and available models,
checks restrictions, and returns a run ID, resolved settings and roster.

Show the resulting compact plan. A fully specified instruction to start supplies
authorization; do not ask for it again. Explain that the timing baseline begins
with the first prayer turn and the accounting baseline begins with helper launch.
Setup and later narration in the main chat are outside the recorded allowance.
Show operational settings separately from the user's overall limits: defaults
are three simultaneous turns and a 90-second per-turn timeout, with supported
ranges of 1..8 active turns and up to 180 seconds per turn. A turn timeout ends the
run as a failure; it is not an overall duration added to the user's request.

## Execute once and report

1. An unrelated unfinished Goal is a conflict. Never replace it. Use a different
   chat or let the user resolve it.
2. Create one operational native Goal whose objective starts exactly with the
   returned `goal_objective_prefix`, such as `prayer-run <run-id>:`. Its objective
   is to carry out this attempt under the chosen stopping rule and report its
   stop reason, including failures. The hoped-for real-world outcome is the prayer intention, not a
   condition the Goal can verify. Set the Goal's token budget only when the user
   explicitly supplied a token allowance.
3. Run the same helper arguments with `run` instead of `preflight` and add
   `--run-id <run-id>`. The helper owns repetition, accounting and cancellation.
   Do not manually spawn or keep prompting extra prayer agents alongside it.
4. Use the execution session's wait facility to monitor the foreground helper.
   Its JSONL progress identifies the run, completed prayers, active turns and
   usage. Give the user meaningful updates for longer runs. Do not restart a
   failed or interrupted invocation automatically. On a user stop request, issue
   `stop <run-id>` and confirm terminal status before ending monitoring.
5. Read the final status and report. Report elapsed time, recorded consumption,
   coverage, stop reason and unresolved usage honestly. Complete the operational
   Goal when the attempt has ended and its result has been reported. Do not
   resume a Goal the user paused or treat a budget-limited Goal as spiritual
   success.

`status <run-id>` reads saved JSON without a model call. `stop <run-id>` requests
cancellation; wait for terminal status before claiming the run has stopped.
`report <run-id>` renders saved examples and accounting offline; add `--format html`
for a standalone HTML document. Each finished run saves both `report.html` and
`report.md`. Prefer showing the HTML report when presenting the result.
Detailed events have a 32 KiB budget, plus lifecycle and saved-example completion
records. After the cap, counts and usage continue but new prayer text is omitted.
Report the recording limit and omissions; do not imply the examples are a complete
transcript or spend model turns reconstructing discarded text. The helper
stores private data under `$XDG_DATA_HOME/prayer-runs`, or
`~/.local/share/prayer-runs`. An optional global `--data-dir` precedes the command.
Never store records inside the installed package. POSIX modes are private; native
Windows records inherit the user profile's ACLs. Stop active runs before plugin
upgrade or removal; retain their records for offline reporting.

There is no background daemon, automatic restart, spending-mode switch, or promise
to run through application shutdown. On unsupported metadata, restrictions or
usage, report the limitation instead of bypassing the checks. Model turns can
finish or incur charges beyond a locally observed stop threshold.
