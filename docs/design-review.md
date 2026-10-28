# Design review

Historical review. [DESIGN.md](../DESIGN.md) is the current design draft. The supplied artifacts now live under [the original-design archive](archive/2026-10-24/agentic-prayer-technical-design.md).

Reviewed on 2026-10-25 against the user's description, the original technical design, and all four accompanying files in the archive. The loose technical design matches the archived copy byte for byte.

This is a review and a proposed refinement. It does not approve the original document's "fixed for v1" decisions or replace them with new fixed decisions.

## Assessment

The idea needs an entry skill, a few praying subjects, shared resource accounting, a stop mechanism and a readable activity report. The supplied design understands the spending problem, but commits to a service architecture before demonstrating the novelty. Its strongest parts are the controller's authority over spending, bounded work, tool restrictions and reporting that still works after usage is exhausted.

Keep those properties. Reduce the infrastructure around them. The joke benefits from interesting subjects and visible prayer output; a database command queue and recovery state machine do not make that experience better on their own.

## Requirements supported by the current request

- A user provides an intention or goal.
- An entry skill gathers any missing parameters and proposes a suitable roster and resource allowance.
- Each subject receives explicit instructions about what to pray for, whom to address and how to pray. The user can request a deity, selected targets or all gods.
- The allowance belongs to the whole run. Subjects do not receive independent copies of the full budget or authority to increase it.
- Subjects generate model output and continue until a resource limit, time limit, failure or user stop ends the run.
- Progress reports describe prayer activity, usage, errors and the stop reason. They do not claim evidence of divine efficacy.
- The public name should not imply allegiance to a particular faith or assert that the prayers work.

The request does not yet settle billing units, independence from the initiating chat, pause/resume, Windows support or a tradition catalog.

## Changes I recommend before implementation

| Concern | Evidence in the original | Recommended change |
|---|---|---|
| Prayer instructions are too rigid | Sections 1, 5 and 6 require mixed mode and a repeating creative/ritual cycle. The schema permits only `mixed`. | Make each subject's prayer instructions primary. Repetition can be requested without a mandatory ratio, weights or genre scheduler. |
| Goal-based budget proposal is undefined | Section 4 asks for a budget separately from the goal. No rule connects the goal or requested run size to the proposed allowance. | Let the entry skill suggest a bounded run size and allowance, then honor the user's ceiling. Do not invent a classifier that assigns monetary worth to goals. |
| The first deliverable is mostly infrastructure | Section 3 prescribes roughly two dozen Python modules. Sections 10 and 11 add a shared daemon, SQLite command queue, leases, migrations and recovery. Prayer behavior arrives in milestone 3. | Make the first complete slice one local run with several subjects, accounting, progress and stop. Start with one controller process. Add a detached process if independence from the chat is required; that alone does not require a multi-campaign service. |
| "All gods" changes meaning | Section 4 interprets `all` as a finite representative roster. | Explain the actual plan. A collective invocation to all gods and a finite roster addressing named targets are different behaviors. Preview the choice instead of claiming exhaustive coverage. A taxonomy of every deity is unnecessary. |
| Approval does not clearly freeze the actual execution plan | Sections 4 and 5 promise exact subjects and a frozen plan, but the sample model is `auto`; section 6 permits persona generation after approval. | Resolve the model, effort and subject instructions before launch, or explicitly describe any allowed generation. Record what the user authorized. Keep checksums internal if used. An instruction to start with fully specified limits can be authorization; avoid repeated confirmation rituals. |
| Two billing systems expand the first release | Section 8 requires both subscription quota monitoring and priced API accounting. | Implement the mode the user will actually use first. The budget ceiling must state its unit. Never silently switch credentials or billing modes. Add the second mode when needed. |
| Persistent history has machinery the product has not justified | Section 6 adds thread rotation, selected history and optional paid summarization after 20 rounds. | Keep subject identity and prayer instructions stable. Use bounded context appropriate to the requested behavior. Introduce history rotation only if long-lived threads prove useful. |

The controller is worth keeping even if subjects are described as autonomous. A prompt telling an agent to respect a spend limit cannot enforce a limit shared with other subjects. The skill can create the plan and request execution; deterministic code should admit work and stop it.

## Spending needs a precise promise

The original is right to call its spending estimates approximate. Keep that caveat in the product contract, not only in implementation notes.

- Subscription quota percentage points measure shared account activity. They do not establish a dollar amount or isolate this run from unrelated Codex use.
- API token accounting can estimate charges. A reserve based on recent average turns is not an upper bound on the next turn's charge.
- Timeouts and interrupts do not undo charges incurred before the stop arrives. Short turns and limited concurrency reduce exposure.
- Account for failed output, retries and any controller-created planning turns. Make the boundary around the initiating skill conversation explicit.
- Check the common budget before every dispatch. Stop admitting work on missing accounting, an unsupported billing mode, a reached limit, a deadline or a user stop. Report unresolved usage rather than treating it as zero.

If an absolute monetary ceiling is essential, establish whether the chosen provider and account offer an enforceable external spending control before promising it. A local estimate alone cannot supply that guarantee. This decision affects the first backend more than the choice of database does.

## Concrete gaps in the supplied contracts

The supplied JSON Schema is structurally valid and both supplied examples pass it. These observations do not establish that either example can run on the user's account.

1. Cross-field validation is incomplete. The handoff already acknowledges the concurrency check. I also verified that the schema accepts duplicate override ordinals, overrides outside the subject count, `non_theistic` scope with a deity target, and a subject override contradicting a single-target scope. Define precedence and validate the resolved plan. Keep the acknowledged concurrency check; do not describe schema acceptance as full validation.
2. The guide promises model discovery, but `execution.reasoning_effort` hardcodes a list of values. The installed Codex schema accepts a nonempty advertised effort string. Validate against the selected model's actual supported values instead of maintaining a competing static list.
3. Section 8.2 requires a service tier for price calculations, but the manifest has no service-tier field and the sample uses `model: auto`. Resolve and record the effective model and tier before approving an estimate. Either constrain execution to supported pricing or reject it.
4. Sections 8.1, 15 and 18 leave the optional included-usage signal ambiguous. State whether its absence makes subscription execution unsupported. In the installed schema, `ordinaryUsageAllowed` is an optional top-level response field, not a property of each quota bucket. Parse and test the actual shape.
5. Section 9 commits a reservation before remote dispatch. That does not make the database update and `turn/start` atomic. If a stop arrives before a reserved request is sent, cancel that reservation. If remote acceptance is uncertain, retain an unresolved record and avoid blindly resending paid work. Promise deduplicated local accounting, not exactly-once remote execution.
6. Tool isolation is a real requirement, not an optional hardening phase. An empty working directory and read-only filesystem do not prove the absence of readable private files, network tools or inherited connectors. Disable capabilities before execution and test the resulting worker environment. Interrupting after observing a tool event cannot reverse an action that already happened.
7. The repeated subscription/API definitions inside the schema add maintenance work. If this schema survives refinement, define each once. This is cleanup after deciding the actual contract, not a reason to build a schema framework.

These gaps are sufficient to treat the "implementation-ready" label as premature. They do not require implementing the full proposed architecture to resolve them.

## Smallest first version I would build

One entry skill calls one local controller. That controller runs a small roster of subjects through one supported model backend and writes records under a private per-run directory.

The skill gathers the goal, target selection, prayer instructions, subject count, resource ceiling and duration. It proposes explicit subject assignments and a budget when either is missing. It shows the effective model, billing unit and limits in ordinary language, then starts within the user's authorization.

The controller owns the shared budget and concurrency. It dispatches bounded prayer turns, records actual usage when available, and exposes a compact status containing completed prayers, active subjects, elapsed time, usage and errors. A local status command should read those records without a paid model call.

Keep a run description, an append-only activity record and a final summary. JSON and JSONL are enough for a single writer unless implementation reveals a transactional need. SQLite is also a reasonable small choice if already useful, but a database command bus, repository layer and migrations should not be prerequisites for the first prayer.

Launch, status and stop cover the first user flow. Stop must work during active turns. A simple foreground run can use cancellation; if a detached run is selected, provide a way to signal that process and distinguish a dead process from active work. Generate the final report from saved records without another model request.

Start with one billing mode and the current local platform. Defer pause/resume, crash reconciliation, cross-platform detachment, model-written summaries, catalog seeding, configurable creative/ritual weights and general plugin distribution until a concrete use requires them. Do not create empty modules for those future features.

The first implementation check should exercise one complete run against a fake model backend. Prove that concurrent subjects share the allowance, stop blocks new dispatch, failures still count usage, uncertain remote acceptance is not blindly retried, and a report survives backend failure. A later live check needs a separately authorized small allowance. Tool restrictions need direct verification before live prayer goals are accepted.

## Verification performed

- Read every Markdown and JSON file in the zip and the loose Markdown file.
- Checked zip integrity and confirmed the two technical-design copies match.
- Validated the manifest schema and both examples with `jsonschema.Draft202012Validator`.
- Checked the validation counterexamples above. They demonstrate missing application rules, not a failure of the JSON Schema implementation.
- Generated the nonexperimental App Server JSON Schema using the installed `codex-cli 0.164.0`. Both illustrative `thread/start` and `turn/start` parameter objects pass it. This proves their shape, not model access or runtime behavior.
- Read the [official Codex App Server documentation](https://learn.chatgpt.com/docs/app-server). It documents account and quota endpoints and recommends the Codex SDK for ordinary job automation. App Server is therefore a choice to justify through required quota/control capabilities, not an automatic requirement for every runner.

No worker turns were started. Account availability, actual charges, quota freshness, tool isolation and background process behavior remain unverified. This review does not approve spending.

## Name candidates

| Name | Why it fits |
|---|---|
| Perhaps | My favorite. It leaves the outcome and theology open while acknowledging the novelty. |
| May It Be | Reads like an intention without naming a deity or promising a result. |
| Wishful | Short, playful and easy to explain. |
| Many Voices | Emphasizes the praying subjects and permits different traditions. |
| Hope Loop | Describes repeated hopeful activity with a technical wink. |
| Open Petition | Suggests an appeal with no prescribed recipient. |

These are naming suggestions only. Package, domain and trademark availability have not been checked.
