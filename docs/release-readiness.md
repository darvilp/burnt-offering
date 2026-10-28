# Release readiness: 0.1.0-beta.1

This records local validation and the initial hosted CI findings. The repository
is at [darvilp/burnt-offering](https://github.com/darvilp/burnt-offering).
Publication gates remain open. The 49-test Linux and native Windows suites
passed locally on 2026-10-28 after the timer-classification correction below.
Record hosted CI and fresh-install results against the exact pushed commit
before tagging a beta.

## Evidence

| Check | Evidence / status |
|---|---|
| Linux / WSL, Python 3.12.3 | 49 automated tests passed, including process-tree cleanup and relocated-package execution. |
| Native Windows, Python 3.12.10 | All 49 automated tests passed, including actual process-tree cleanup and relocated-package execution. |
| Codex manifest/catalog | Codex 0.164.0 parsed the portable plugin and discovered `burnt-offering:pray`. |
| Plugin lifecycle on Linux | Real install, discovery, removal and reinstall passed on Codex 0.164.0 without model credentials; private fixture records retained. |
| Plugin lifecycle on native Windows | The same no-credential lifecycle passed on Codex 0.146.0. This does not establish signed-in runtime support on that version. |
| Signed-in Linux / WSL acceptance | Standard deadline check passed on Python 3.12.3 / Codex 0.164.0; TempleOS deadline stop and report generation observed. Early cancellation remains pending. |
| Signed-in native Windows acceptance | Pending: the available native CLI is 0.146.0 and no native controller context is present in this session. |
| macOS | Experimental. Port implemented; hosted CI and signed-in end-to-end evidence pending. |
| GitHub CI | Initial Linux test jobs and Linux/Windows plugin-install jobs passed. Windows test failures identified an early-timer classification defect, now corrected locally; the full follow-up CI result remains pending. |
| Skill metadata and reports | Skill Creator validation passed. Both live HTML reports opened offline with JavaScript disabled and no network requests; standard examples expanded and TempleOS measured 640x480 with working section navigation. |
| Release package | Ten-file allowlist, deterministic rebuild and SHA-256 checks passed. Relocated execution and offline reports passed without checkout metadata or the development symlink. |

The CI matrix runs Python 3.11 and 3.12 on all three operating systems. Plugin
installation checks use Codex 0.164.0 without model credentials. Local WSL evidence
does not establish native Windows behavior, and prepared CI is not a passing run.

The [initial hosted run](https://github.com/darvilp/burnt-offering/actions/runs/40711941667)
showed Windows timers expiring up to one monotonic clock tick before a deadline.
The runner stopped without replaying work but reported `dispatch_uncertain`.
Timeout classification now accounts for the clock's reported resolution; normal
admission checks still use the exact deadline. A regression test covers early
timer classification, ordinary admission and user-stop precedence.

## Local runtime observations

Both attempts used an extracted candidate from outside the checkout, one subject,
a 10-second duration, 100-turn ceiling, no token ceiling and inherited model/effort.

| Attempt | Observation |
|---|---|
| Standard | Started two turns and completed one prayer. Closed admission at 10.000 seconds and reached terminal shutdown at 10.080 seconds. Complete recorded usage: 5,304 worker tokens plus 624 controller tokens. No unresolved batches. |
| TempleOS | Started one turn and completed no prayers. Closed admission at 10.001 seconds and reached terminal shutdown at 11.077 seconds. One unresolved batch, with worker usage unknown; 554 controller tokens recorded. The test watcher missed dispatch, so the later stop request does not establish early cancellation. |

Both owned runners and server processes were absent after shutdown. Both report
formats regenerated offline byte for byte from the saved records. Usage above
describes the helper's accounting window; setup and later chat narration are
outside it. Unknown usage is not evidence of zero consumption.

## Candidate contents

The artifact is `dist/burnt-offering-0.1.0-beta.1.zip`, with its adjacent
`.zip.sha256` file. It includes the portable manifest, entry skill, roster,
runner and process-control companion, README, two release documents, LICENSE
and NOTICE. The source repository also contains the marketplace catalog,
cross-platform CI and the manual candidate workflow.

The original design ZIP and its five extracted files remain unchanged. Private
run records, source archives, tests, caches and working previews are excluded
from the plugin ZIP. Build artifacts are ignored by Git.

## Release gates

- Complete and record the candidate's signed-in Linux/WSL acceptance attempts.
- Complete native Windows acceptance in a Windows Codex chat with a compatible
  CLI and authentication, keeping Python and the controller in that environment.
- Run the configured hosted CI before publication. Native macOS CI must pass;
  macOS stays experimental until a Mac tester confirms signed-in execution.
- Review the final ZIP/checksum and use the exact reviewed commit for a later tag.

The [fresh-install candidate check](RELEASING.md#fresh-install-candidate-check)
combines guided setup and the pending live cancellation check in a new chat.

Public artifacts contain synthetic fixtures and aggregate validation facts only.
Real intentions, prayer text, credentials, private paths and controller IDs stay
out of release notes and packages. The initial repository push and a tagged
prerelease are separate milestones; the latter still depends on the checks above.
