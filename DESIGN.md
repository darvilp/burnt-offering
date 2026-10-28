# Prayer project design

Version 0.8, 2026-10-25. Project name: Burnt Offering. See [PLAN.md](PLAN.md) for the implementation plan.

This is the current design. The [original design bundle](docs/archive/2026-10-24/agentic-prayer-design-bundle.zip), its extracted files, and the [initial review](docs/design-review.md) are historical material. Their schemas, module layouts and milestones do not govern this version.

Accepted requirements come from the user's description and feedback. Numeric defaults and the detailed roster policy below are recommendations for the first implementation. Native Codex Goals are the preferred starting mechanism; use the simplest approach that preserves the required behavior and chosen stopping rule.

## 1. Product

The user supplies an intention, such as a wish for a successful event. An entry skill gathers any missing parameters, establishes a bounded or explicitly unbounded run, and creates subjects with instructions about what to pray for, whom to address and how to pray.

Subjects use model turns to pray according to their assigned intention, recipient and practice, including composition, recitation or repetition as instructed. The main thread coordinates them and reports activity until the allowance, deadline, batch limit or user stop ends the run. Consuming the full allowance is permitted, but not required when another limit or failure ends the run first.

There is no test for whether a prayer worked. The operational objective is to carry out and record the requested prayer activity within the run's limits. The name and presentation should leave theological beliefs open.

## 2. Main thread, Goal and subjects

The main thread is the chat where the user invokes the entry skill. It is the coordinator the user interacts with. It gathers parameters, resolves the roster, starts subjects, collects their output, and reports progress.

Use one native Codex Goal on that thread to retain the operational objective and support continuation. For example, "Coordinate the approved prayer roster for this intention until the allowance or deadline stops the run; record activity and report the reason for stopping." The user's hoped-for real-world outcome is data supplied to the subjects, not the Goal's completion test.

Each subject is a dedicated Codex worker session owned by the local helper. These sessions do not appear as native child chats. The helper requests finite prayer turns and reports their results to the main thread. Subjects do not recursively spawn agents, change recipients, increase allowances, research the intention or pursue it through external actions.

Do not put an independently continuing Goal on every subject. One root Goal and finite subject work keep lifecycle ownership in one place. If the main thread already has an unrelated active Goal, report that conflict rather than overwriting it or mixing the objectives.

The main thread is an LLM coordinator. The local helper owns one foreground App Server process and supplies scheduling, accounting, deadlines and cancellation. The sample runs demonstrated that prompting for a duration supplies no timer and manual supervision can overrun it. Native Goals remain useful for the operational objective, but the helper must enforce worker limits independently. There is no separate daemon.

## 3. What "all" means

"All" means every entry in a declared, finite roster. Every entry gets its own dedicated subject. It does not mean one generic subject addressing everyone, and it does not silently mean a random sample of traditions.

An unqualified request for "all" uses the project's shipped roster. Before starting, the skill names its scope, shows its size, and makes the entries inspectable. The resulting run records a snapshot of that list. New discoveries or later roster edits do not silently add subjects to an active run.

The roster covers living traditions, well-attested historical worship and additional prayer practices explicitly included by the user. There should be no arbitrary cutoff year. Include an ancient tradition when there is enough documented practice to give a subject a coherent assignment. Exclude an alleged prehistoric deity when the only available material would force us to invent the identity and practice. Recent traditions are not excluded merely because they are recent.

My preferred rules for roster granularity are:

| Case | Roster rule |
|---|---|
| A tradition centered on one God | Use a subject for that tradition and its prayer practice. Do not have the program decide whether different traditions ultimately address the same being. |
| A tradition with multiple named deities | Use a dedicated subject for each named deity included in the roster. Identify the tradition as well as the deity. |
| Aliases, titles and transliterations | Combine these within the same tradition unless they materially change the intended prayer assignment. |
| Related deities across traditions | Separate them when the ritual traditions make distinct assignments useful. Similarity does not require either merging them or asserting that they are different beings. |
| Denominations, schools and local practices | Use a stated representative practice initially. Add a separate subject when explicitly requested or when the roster deliberately includes a materially different practice. Avoid multiplying every organizational branch. |
| Traditions without a suitable deity-directed prayer | If included in the roster, describe the activity as a tradition-appropriate aspiration or well-wishing. Show that wording in the preview; do not invent a god or present the activity as universal to the tradition. |
| Additional prayer practices | Machine-spirit devotion belongs in the standard roster at the user's request, drawing on machine blessings and technical litanies. It uses the same assignment, language and execution fields as other entries. Other named recipients use the explicit-target flow. |

The key is a distinct prayer assignment, identified by tradition plus target where applicable. This lets subjects use different practices without turning the project into a theological identity resolver.

The shipped roster should be small enough to inspect, with broad coverage before deep lists from one pantheon. Maintain it as a plain file with names, aliases and short assignment notes. A bibliography is useful when introducing historical entries, especially reconstructed practices. A religion database, discovery crawler, ranking system and taxonomy engine are unnecessary.

The current 23 entries include Manichaeism addressing the Father of Greatness and a Sethian-inspired Gnostic invocation to the Invisible Spirit / Monad. The latter is a disclosed representative assignment, not a claim that all Gnostic traditions share one deity or practice. Machine-spirit devotion joins the same roster and follows the same execution and reporting rules.

All-roster scheduling gives every entry a first batch before giving any entry a second batch. Interleave traditions in the queue so a large pantheon does not consume the entire first wave. Keep each subject's assignment stable for the run.

Finite budget can end the run before every entry has prayed. Report planned, started and completed entries separately. If the batch ceiling is below the roster size, or the initial estimate plainly cannot fund a first pass, show the conflict before launch and propose a narrower roster or a larger allowance or batch ceiling. Do not silently substitute a smaller roster. Completion of a first pass is an estimate unless the user chooses a sufficiently small fixed task.

## 4. Entry skill and user flow

The skill needs the prayer intention, target selection, prayer instructions and a stopping rule: a finite duration or token allowance, or an explicit request for unbounded execution until stopped. Users can optionally specify `subagent_model` and `subagent_effort` for all subjects in the run. The helper exposes these as `--model` and `--effort`. Target selection can name one recipient, a list of recipients, a tradition, or the shipped all-roster. Simple requests should stay simple; most subject assignments can be proposed from the scope and shared style.

A bare `$pray` starts guided parameter gathering. Ask for the intention, recipients and stopping rule through short questions, and offer prayer style, model and effort choices with defaults. Reuse supplied settings in partial invocations. Gather the choices before preflight or Goal creation; do not infer an intention from previous sample runs. A bare invocation authorizes setup, with launch following once the choices are settled and the user has asked to run.

An explicit `--devotion templeos` request selects one God-directed subject whose practice draws on the TempleOS charter: the computer as a temple, programming and creative work as offerings, and personal conversation with God. Its language is sincere, plainspoken, biblical in register and sometimes playful. English is the default; explicit language instructions take precedence. It uses original wording and does not attribute invented quotations to Davis or scripture. This subject is separate from the standard 23-entry roster. The helper rejects simultaneous `--target` or `--all` selections; the skill resolves contradictory requests before launch. The standard devotion remains the default.

1. Read the request and reuse parameters already supplied. Ask only for missing choices that materially affect the run.
2. Propose explicit subject assignments. Each combines the common intention with its recipient, tradition and prayer instructions. A shared request such as "solemn and repetitive" applies unless an explicit subject instruction overrides it.
3. Establish a finite duration, token allowance or both, unless the user explicitly requests unbounded execution. A request such as "pray for 45 seconds" is sufficient. Missing limits trigger a question, never an inferred unbounded run. "Run unbounded" or "keep praying until I stop you" explicitly removes run-level ceilings. Never infer a monetary value from how serious the intention sounds.
4. Show a compact plan with roster size, concurrency, stopping rule, resolved subagent model and effort, and any known coverage limitation. For unbounded runs, state the absence of duration, token and total-turn ceilings and how to stop. If the user already instructed a fully specified run to start, that instruction supplies authorization. Do not require a second ritual confirmation or a checksum.
5. Create the native Goal identifying this run and launch the helper under the approved limits. The helper automatically repeats finite prayer turns and returns progress through the same chat and its saved records.

Resolve subagent settings from the user's optional choices and the controller's current settings at launch:

| User specifies | Subagent model | Subagent reasoning effort |
|---|---|---|
| Neither | Inherit the controller's current model | Inherit the controller's current effort |
| Model only | Use the requested model | Use that model's default effort |
| Effort only | Inherit the controller's current model | Use the requested effort |
| Model and effort | Use the requested model | Use the requested effort |

These choices apply to the praying subjects and do not change the controller. Resolve and record them once per run, and keep them for subsequent batches and any recreated subjects. A later change to the controller's settings does not silently change an active run.

Validate the resolved model's availability and supported effort values before starting subjects. Reject an unavailable model or unsupported explicit effort with a clear correction; do not silently substitute another model or effort. Verify the effective spawn settings rather than assuming omitted arguments will inherit correctly when runtime defaults or custom-agent settings can override them. Avoid a model-selection questionnaire when the user accepts inheritance.

Setup work in the chat consumes usage too. State where the run's budget baseline begins and avoid presenting that baseline as a cap on the entire conversation's prior usage.

## 5. Subject behavior

Each subject receives only the context it needs: the intention, its tradition and target, prayer instructions, the current batch request, and any small amount of previous output required by that request. Avoid copying the whole project conversation into every subject.

A batch directs a subject to carry out one or a small finite number of prayers in text during a model turn. The uttered text is the prayer activity itself and its record. Subjects return it with a completion result that identifies the batch. Start with one prayer per batch; a short length instruction controls verbosity. That instruction is not a token-enforcement mechanism.

New composition, repetition, chanting-like text, a formal invocation, or a playful style are all possible instructions. New wording is optional; reciting supplied wording or repeating an invocation is valid prayer activity. There is no required creative/ritual ratio, genre enum or personality generator. Preserve the requested meaning when adapting to a tradition, and flag a conflict rather than silently replacing the practice.

Each roster entry includes a short palette of suggested languages. Default prayer activity mixes English with brief recipient-appropriate phrases, with variation across turns when suitable. Explicit language or exact-recitation instructions override that default. Native scripts and familiar transliteration are acceptable; use supportable short phrases and fall back to English when ancient wording is uncertain. Do not invent pseudo-language, claim generated wording is authenticated liturgy or append translations without a request. Custom recipients may use inferred languages when their tradition is identifiable; otherwise follow the user's language. Preserve the palette in run metadata and show it as suggested languages in reports, not as measured language usage. The existing prayer-instructions field carries user preferences, without a separate language-routing subsystem.

Generated text must not masquerade as an authenticated traditional text. Use supplied sources for requests requiring exact canonical wording. Otherwise describe the output as generated or inspired by the stated practice. Historical reconstructions should be labeled accordingly.

Subjects have no reason to browse, edit project files, send messages to external people or services, buy anything, or create further agents. Give them the smallest supported capability set. Local subjects may inherit parent permissions, so verify actual restrictions instead of treating a prompt as isolation. The coordinator owns any necessary local record writing.

## 6. Budget and execution limits

Bounded runs accept duration-only limits and optional token ceilings. Token-only runs also have the default 20-minute duration ceiling. Explicit unbounded runs have no duration, token or total-batch ceiling. An exact dollar amount and subscription quota percentages are not required. Dollar pricing tables, quota-window accounting and multiple billing adapters stay out of this version.

When a token ceiling is supplied, one aggregate allowance covers the coordinator and every subject, including failed work after the baseline. Allowance tokens are uncached input plus output. The helper combines the controller Goal's usage since helper launch with cumulative usage from its separate worker sessions. Raw input, cached input and output are also reported. A budget of B must never become B for the parent plus B for each subject. Do not replenish it, create a replacement Goal or resume into a fresh allowance automatically.

The desired behavior is approximate near the allowance boundary. Stop admitting new batches when the observed total reaches the allowance or cannot reasonably accommodate another small batch. Some active work may finish beyond the nominal threshold. Exact exhaustion is not a success criterion.

Bounded means the run also has finite concurrency, a finite total batch count, a campaign deadline and a per-batch deadline. Unknown usage stops new admissions. No subject receives an instruction to loop indefinitely. Interrupt unfinished batches on a stop or deadline rather than letting a self-directed worker continue on its own.

The helper's explicit `--unbounded` flag removes all three run-level ceilings. It cannot be combined with `--duration`, `--tokens` or `--max-batches`; contradictory requests must be resolved rather than silently dropping limits. Concurrency, per-batch deadlines, capability restrictions, accounting and failure stops still apply. The helper continues requesting finite turns until the user stops it, the controller Goal ceases to be active or a failure occurs. Unbounded execution requires the foreground helper and active Codex environment and keeps consuming tokens while it runs.

Initial defaults are three active subjects, one prayer per batch, a 90-second batch deadline and, for bounded runs, a 20-minute run deadline when only tokens were supplied and at most 100 batches total. A token ceiling is optional and is never invented silently. The helper uses monotonic deadlines, closes admission before cancellation, and allows at most five seconds for local shutdown. Once observed turn costs are available, it reserves estimated allowance for active turns before admitting more work.

These limits bound the amount of outstanding work and its duration. They do not establish an exact numerical maximum for token overshoot unless the runtime supplies enforceable per-turn token controls. Keep that distinction in the report without turning approximate accounting into a billing project.

## 7. Runtime integration

The installed Codex App Server provides controller thread metadata, Goal state, model discovery, worker turns, token telemetry and interruption. The helper owns a separate stdio connection and its worker sessions. It reads the controller's existing Goal without taking over that chat or modifying its lifecycle.

Preflight resolves the actual controller model and effort, checks the selected model catalog entry, and verifies disabled process capabilities. Each worker is given explicit capability overrides, disabled inherited MCP servers, an empty working directory, a read-only sandbox and approval policy `never`. Verify the effective worker model, effort and sandbox before its first turn. Unexpected tool activity or model rerouting stops the run.

The helper uses finite turns because text-only replies terminate naturally. All RPC waits during prayer are bounded by the nearest deadline, including waits for a turn-start acknowledgement. An uncertain acknowledgement is never blindly replayed. Unknown usage prevents another turn and remains explicit in the final report.

Tests must cover these controls with a fake wire-level server, and live checks must establish the installed model and runtime behavior. Prompt compliance alone is not evidence that tools were disabled. The helper does not introduce pricing adapters, a shared daemon or a general scheduler framework.

## 8. Execution and stopping

Freeze the intention, assignments, resolved subagent model and effort, and resource limits for a run. Start the first eligible subjects up to the concurrency limit. Collect completed batches, record usage and outputs, then admit the next queued assignment while limits permit. Reuse a subject for later batches when supported; avoid unnecessary thread rotation or model-written context summaries.

One dedicated subject per roster entry does not mean every subject runs simultaneously. The helper keeps at most the configured number of turns active, retains worker sessions for reuse during that run, and closes its owned server at the end. Never repurpose an existing subject to pray to a different recipient.

The user can ask for progress or stop in the main chat. Progress requests should show the latest known state. They must not create extra prayer work merely to answer a status question.

On stop, budget threshold, deadline, unavailable usage or runtime failure, close admission first and cancel outstanding work using the available native control. Record unresolved work explicitly. Stop propagation must come from verified runtime behavior or the small support code described above, rather than depending on an extra model turn after the budget has expired.

Generate the final activity report from recorded data. The main thread may narrate it when it has allowance left, but the record must remain readable without spending more tokens. A run can finish under its intended limits, stop at the user's request, or stop because the runtime failed. Report the reason accurately. A budget-limited Goal does not become an achieved spiritual objective.

The initial design runs within the active Codex environment. A native Goal is not a promise that work continues through a closed application, sleep or shutdown. Independent background execution, recovery after a crash and automatic restart are deferred. A stopped run starts no new work without a fresh user instruction.

## 9. Records and reporting

Persist a small private run record with the intention, resolved roster, limits, controller model and effort at launch, requested and resolved subagent model and effort, baseline, subject/batch identifiers, usage, timestamps and stop reason. Retain bounded examples of prayer text. No live database or command queue is needed initially.

Detailed dispatch, prayer text and per-prayer completion records share a 32 KiB serialized UTF-8 budget. Stop detailed recording when the next routine event would exceed it. Keep aggregate counts, usage and per-subject coverage after the cap, plus a cap notice, lifecycle/failure records and completion markers for previously saved examples. These small additional records can exceed the detail budget; file size and memory use must not grow with every subsequent prayer. Oversized examples are omitted whole. Show omitted-event and saved-example counts in status and reports. This policy applies to new helper records, not Codex's own runtime storage or existing logs.

Any supplemental files belong in a per-run directory under the user's local application data, outside the source repository. A single coordinator owns record writes. JSON for the run description and JSONL for events are sufficient if native records cannot provide the needed status and report. Never persist credentials with a run.

Status and final output show the resolved subagent model and effort, allowance unit and observed usage, elapsed time, completed prayers, active and failed batches, roster coverage and the stop reason. For all-roster runs, list entries that never started as well as those that produced output. Keep quoted prayer excerpts separate from accounting facts.

Generate a standalone `report.html` and a terminal-readable `report.md` at shutdown. The HTML uses inline CSS, semantic tables, expandable examples and escaped text, with no scripts or external assets. Offline report generation streams event files and bounds saved examples even for older runs. Throttle aggregate terminal progress and status rewrites to once per second, except immediate state transitions. Captured terminal output remains separate from the helper's capped event file.

Persist the selected devotion in the run description, worker assignment and status. TempleOS devotion selects a fixed 640x480 CSS-pixel HTML frame with VGA-palette colors, monospace text, square edges and a title/status bar. Longer sections scroll inside that frame; native section links and details preserve access to the full report. The renderer retains the standard appearance for other and older runs. The theme changes no accounting, cancellation, model selection or recording policy and requires no scripts or external assets.

## 10. Smallest implementation

The implementation has an entry `SKILL.md`, a plain 23-entry roster reference, a standard-library Python runner with a companion process-control module, and fake-server tests. Editable source is under `skills/pray`, with a repository-local discovery link at `.agents/skills/pray`. The skill is named `pray`; the installed plugin qualifies it as `$burnt-offering:pray`.

The helper's small stdio App Server client exists to own worker execution and cancellation. Keep transport, accounting and stop logic together until the code warrants separation. There is no database, service, pricing adapter or general orchestration framework.

The runner keeps scheduling, accounting and reporting together. Platform-specific process identity and cleanup belong in the companion module so every launch path uses the same ownership rules.

## 11. Acceptance checks

The first implementation is ready for a small live demonstration when it can prove that:

1. Explicit recipients and prayer instructions reach the correct dedicated subjects without a forced prayer pattern.
2. An all-roster run plans every declared entry, gives unserved entries priority, and reports partial coverage honestly when a limit stops it.
3. Coordinator and subject consumption share the allowance, failed work counts, and parent/child telemetry is not double-counted.
4. Budget, deadline and user stop prevent further admissions and stop outstanding subjects within the verified runtime behavior.
5. Missing usage or uncertain dispatch stops further work without an unbounded retry loop or automatic allowance renewal.
6. A report is available after failure or allowance exhaustion without another paid request.
7. Subjects cannot use unnecessary tools, and cannot turn the prayer intention into an external action or recursively delegated task.
8. Model and effort selection follows the four-case table, invalid explicit choices fail before subject work starts, and later batches preserve the resolved settings.
9. A bare invocation gathers settings before launch; incomplete requests reuse supplied choices and ask only for missing ones.
10. Explicit unbounded runs omit duration, token and total-batch ceilings, repeat beyond bounded defaults, and retain manual stop, per-turn timeouts and failure checks. Missing limits without explicit unbounded intent still fail validation.
11. Detailed recording stops at its byte budget while counts and usage continue; retained examples keep accurate completion labels. Standalone HTML escapes supplied text, works without external assets and is available after failure.
12. Language palettes and explicit language instructions reach workers unchanged; Unicode text and suggested-language metadata survive recording and reporting. All-roster selection includes the three added assignments.
13. TempleOS devotion selects the intended subject, rejects conflicting roster selections, preserves explicit language choices and persists the mode. Its complete HTML report stays inside a measured 640x480 frame with working section navigation.

Test helper logic with fake usage and fake workers before spending tokens. Use live testing only for the native behaviors a fixture cannot establish. This design work itself starts no prayer Goal or subjects.

## 12. Distribution

Distribute Burnt Offering as a Codex plugin with ID `burnt-offering`, an Apache 2.0 license, a root portable `plugin.json` and a repository marketplace catalog. The initial candidate is `0.1.0-beta.1`. GitHub installation uses the catalog pinned to a release tag. A reproducible, allowlisted ZIP with a SHA-256 checksum provides a reviewable plugin artifact. It excludes private records, working previews, tests and the historical design bundle.

The runtime targets Linux/WSL2, native Windows and macOS with Python 3.11+ and an authenticated Codex CLI in the same environment as the controller. Resolve native executables without invoking a shell. Own POSIX process groups or a Windows Job Object, restore signal handlers, and retain stable process identities for offline status. Preflight reports OS, Python and Codex versions; run records preserve those versions. The helper rejects private-data directories inside either a checkout or an installed package, even without Git metadata.

Automated CI covers Python 3.11 and 3.12 on all three operating systems, plus real plugin installation, discovery, removal and reinstallation without model credentials. Signed-in runtime acceptance is a separate gate. WSL evidence does not establish native Windows execution. macOS remains experimental until native CI and a Mac user's signed-in test establish its behavior. The candidate workflow builds artifacts after validation; it does not publish anything.

Upgrades and rollback require stopping active runs and reinstalling the desired version. Removal retains private records. There are no package lifecycle scripts, extra runtime dependencies or automatic migration of active runs. [Release readiness](docs/release-readiness.md) records the actual evidence; [the release procedure](docs/RELEASING.md) defines later publication gates.

## 13. Decisions still open

The shipped roster is the 23-entry list in `skills/pray/references/roster.json`, extending the original list in `PLAN.md`; its scope rules do not claim a universally correct religious taxonomy.

The native Goal holds the operational objective; the helper supplies aggregate accounting and cancellation. Background independence and alternative budget units can wait until the initial experience demonstrates a reason to add them.

## Runtime references

The [official Goals guide](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) describes thread-scoped objectives, lifecycle and continuation. It also notes that a continuation with no tool call suppresses the next automatic continuation. That is why this design has the coordinator dispatch finite worker batches instead of assuming prayer-only subject Goals will keep running.

The [official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) describes native delegation and inherited permissions. The installed `codex-cli 0.164.0` generated schema exposes a thread Goal with `tokenBudget`, `tokensUsed` and `timeUsedSeconds`. A schema establishes those fields, not whether descendant usage and stop propagation have the semantics this run needs. Those remain implementation checks.
