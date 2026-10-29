# Release readiness: 0.1.0-beta.1

The beta targets Linux/WSL2. Native Windows and macOS remain experimental until
signed-in runtime acceptance is independently confirmed there. Automated tests
and plugin installation checks cover all three systems, but do not establish
that signed-in prayer runs behave identically.

## Evidence

| Check | Evidence / status |
|---|---|
| Linux / WSL, Python 3.12.3 | All 54 automated tests passed locally on 2026-10-29. |
| Native Windows, Python 3.12.10 | All 54 automated tests passed locally on 2026-10-29, including actual process-tree cleanup. |
| Hosted CI | The prior pushed commit passed all nine jobs on Linux, Windows and macOS. The release commit must pass the same matrix and candidate workflow before tagging. |
| Plugin installation | Prior real install, discovery, removal and reinstall checks passed without model credentials on all three hosted platforms. Candidate-specific installation is checked again before publication. |
| Signed-in Linux / WSL | A previous 10-second standard attempt completed one prayer and started a second; admission closed at 10.000 seconds and local shutdown finished at 10.080 seconds, with complete usage. Current candidate cancellation acceptance remains pending. |
| Signed-in native Windows / macOS | Pending. Both remain experimental for this beta. WSL evidence does not establish Windows behavior. |
| Guided setup | Skill discovery and parameter-gathering instructions have been reviewed. A bare invocation is not an automated end-to-end chat acceptance test. |
| Reports | HTML and Markdown generation, escaping, Unicode, recording limits and offline regeneration are covered by tests. The TempleOS frame was measured at 640x480 in a browser with JavaScript disabled and no network requests. |
| Package | Deterministic ten-file allowlist, relocated execution, package-data protection and SHA-256 checks are covered by tests. The release assets must come from the passing candidate workflow. |

The CI matrix runs Python 3.11 and 3.12 on all three operating systems. Plugin
installation jobs use Codex 0.164.0 without model credentials. Runtime acceptance
uses the signed-in Codex environment; no credentials or real prayer text belong
in public artifacts.

## Correctness checks

A fresh user-perspective review found that a helper which died during cleanup
could leave a saved run permanently marked STOPPING. Runner identity is now
checked for both RUNNING and STOPPING. Missing processes produce INTERRUPTED /
runner_missing and incomplete usage; live processes and completed runs keep
their existing state. The regression test failed before the fix and passes now.

Overall run limits are independent and explicit. The former implicit 20-minute
deadline and 100-turn cap are removed. A positive total-turn limit can stand
alone and has no arbitrary 1,000-turn maximum. A fake-worker token-only test
completed 105 prayers with an hour added to its elapsed-time baseline, then
stopped at the token allowance. Token-only and turn-only runs are correctly
reported as bounded in both formats.

The shipped roster has 25 entries. Selection, aliases, distinct recipients,
all-roster coverage, language metadata and relocated installation are tested.
The original design ZIP and its five extracted files remain unchanged.

## Publication checks

- Pass hosted CI and the candidate workflow on the exact intended tag commit.
- Install the candidate outside the source checkout and verify skill discovery.
- Complete the bounded Linux/WSL cancellation attempt and verify terminal status,
  owned-process shutdown, offline reports and honest usage completeness.
- Verify the candidate ZIP, checksum and exact source contents before uploading.
- Publish tag v0.1.0-beta.1 and its GitHub prerelease with the tested support scope.
- Make the repository public only after these checks and release publication pass.

The [release procedure](RELEASING.md) covers installation, acceptance, upgrades
and rollback. Private records remain outside both the repository and plugin
package. Removing or updating the plugin does not remove those records.
