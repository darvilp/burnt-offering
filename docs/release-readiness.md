# Beta validation: 0.1.0-beta.1

The beta targets Linux/WSL2. Native Windows and macOS remain experimental until
signed-in runtime acceptance is independently confirmed there. Passing automated
tests does not establish that signed-in prayer runs behave identically.

The GitHub release links the candidate workflow for its exact commit and hosted
CI results. This record also documents the local and signed-in checks that the
workflow cannot perform without a user account.

## Local checks

| Check | Evidence |
|---|---|
| Linux / WSL, Python 3.12.3 | All 54 automated tests passed locally on 2026-10-29. |
| Native Windows, Python 3.12.10 | All 54 tests passed locally on 2026-10-29, including actual process-tree cleanup. |
| Skill metadata | Skill Creator validation passed. |
| Package | Ten-file allowlist, reproducibility, relocated execution, package-data protection and SHA-256 checks passed. |
| Public source contents | Tracked source and the original design archive were checked for credentials and private machine paths. Private run records and working previews are excluded from Git and the plugin ZIP. |

A fresh user-perspective review found that a helper which died during cleanup
could leave a saved run permanently marked STOPPING. Runner identity is now
checked for RUNNING and STOPPING. Missing processes produce INTERRUPTED /
runner_missing and incomplete usage; live processes and completed runs retain
their state. The regression test failed before the fix and passes now.

Overall limits are independent and explicit. The implicit 20-minute deadline
and 100-turn cap are removed. Positive total-turn limits can stand alone and
have no arbitrary 1,000-turn maximum. A fake-worker token-only test completed
105 prayers with an hour added to its elapsed-time baseline, then stopped at
the token allowance. Both report formats label token-only and turn-only runs
as bounded. The shipped roster has 25 entries, with selection and aliases tested.

## Installed, signed-in acceptance

On 2026-10-29 the GitHub marketplace installation of candidate
[bee7afa](https://github.com/darvilp/burnt-offering/commit/bee7afad8f4528e4eb9a4d5de0461534071e8fac)
was tested from outside the checkout. Codex discovered the enabled skill as
`burnt-offering:pray`. The runtime used Python 3.12.3, Codex 0.164.0, and the
controller's inherited gpt-6.1-sol model at high effort. Each attempt used one
subject, a 10-second duration, an explicit 100-turn ceiling and no token ceiling.

| Attempt | Observed result |
|---|---|
| Standard | Completed one prayer and started two turns. Admission closed at 10.001 seconds; local shutdown finished at 10.092 seconds with duration_limit. Recorded 5,161 worker allowance tokens; usage was complete with no unresolved batches. |
| Early cancellation | An independent watcher observed dispatch and requested stop. Admission closed at 0.480 seconds; local shutdown finished at 1.539 seconds with user_stop. One turn started and no prayer completed. Usage was incomplete with one unresolved interrupted batch; zero recorded worker tokens does not establish zero consumption. |

Both owned runner and server processes were absent after shutdown. Both HTML
and Markdown reports regenerated offline byte for byte. Browser checks passed
with JavaScript disabled and no network requests: standard examples expanded,
and the TempleOS report measured 640x480 with working internal navigation.
Private intentions, prayer text, controller IDs and local paths are not copied
into release artifacts. Recorded usage excludes setup and later chat narration.

## Hosted CI and release assets

The candidate workflow runs the 54-test suite on Python 3.11 and 3.12 across
Linux, Windows and macOS. It also performs real plugin installation, discovery,
removal and reinstallation on each platform with Codex 0.164.0 and no model
credentials. All nine validation jobs must pass before the package job runs.

Release assets come from that passing workflow. Before upload, verify the ZIP
and checksum, compare every member with the intended tag commit, and confirm
that the runner, process-control module, roster and skill match the installed
acceptance candidate. The plugin manifest and catalog must agree on version
0.1.0-beta.1. Tag v0.1.0-beta.1 must identify that exact validated commit.

## Known limits

- Native Windows and macOS signed-in runtime acceptance is still pending; both
  remain experimental. WSL evidence applies to Linux, not native Windows.
- Guided setup is instruction-driven. Skill discovery and the setup instructions
  were checked; a fresh-chat user interaction was not automated end to end.
- Language routing is tested, but generated wording and translations are not
  independently verified. Model compliance can vary.
- Cancellation ends local admission and cleanup. Already dispatched service
  work may have unknown final usage, which reports must leave explicit.

See the [release procedure](RELEASING.md) for installation, upgrades and rollback.
Plugin removal retains saved records. The original design ZIP and its five
extracted files remain unchanged.
