# Releasing Burnt Offering

This procedure prepares a GitHub plugin beta. Publication is a separate action;
the candidate workflow never creates a tag, pushes code or publishes a release.

## Candidate gates

1. Update the root plugin and catalog versions together. The first version is
   `0.1.0-beta.1`, with tag `v0.1.0-beta.1`, in `darvilp/burnt-offering`.
2. Run the full test suite and `python3 scripts/package.py`. Verify the SHA-256
   file against the ZIP and inspect its allowlisted members.
3. Require Linux, macOS and Windows CI to pass on Python 3.11 and 3.12, plus real
   plugin install/discovery/removal/reinstall checks using Codex `0.164.0`.
4. Complete signed-in runtime acceptance for Linux/WSL before publishing this
   beta. Native Windows and macOS remain experimental until their native signed-in
   runs are independently confirmed. Passing CI does not establish those runs,
   and WSL does not establish Windows behavior.
5. Record the evidence in `release-readiness.md`. Missing checks stay pending;
   a prepared workflow or successful fake-worker test is not end-to-end evidence.

The supported Codex baseline is the version actually checked. Later versions must
pass capability checks and acceptance before they are added to the tested list.
Do not downgrade restrictions or silently change billing mode to pass a gate.

## No-model checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package.py
python3 scripts/check_plugin_install.py
```

Use `py -3` in PowerShell. Integration checks modify only a uniquely named temporary
plugin/catalog entry and remove those entries afterward. They use the current
Codex account's plugin storage, so use a disposable environment for clean-install
proof. The check selects ephemeral credential storage, removes API-key environment
variables from its own process and asserts that no account is present. It never
starts model turns. CI uses no account/model secrets.

The release ZIP contains only the manifest, skill resources, README, release
instructions/readiness, Apache 2.0 license and NOTICE. The source repository keeps its design archive; that archive,
tests, working previews, caches and private runs are not release ZIP members.

Packaging and catalog installation follow the
[official OpenAI plugin packaging documentation](https://developers.openai.com/plugins/build/plugins).
The no-model integration check also verifies the installed skill's qualified name
against the actual CLI, rather than assuming a manifest alone establishes discovery.

## Signed-in acceptance

Run against an extracted or installed candidate from a different working folder.
Keep Python, Codex authentication and the controller chat in the same native
environment. Use inherited model/effort unless the user explicitly chooses others.

- Standard attempt: one open invocation, a synthetic non-private intention,
  10-second duration, 100-turn maximum and no token ceiling.
- Cancellation attempt: TempleOS devotion, the same finite limits, with a stop
  request after dispatch. Confirm terminal status rather than just stop-file creation.

These time-bounded checks consume model usage. They are run only within the user's
authorized testing scope and are not retried automatically. Check preflight and
state the resolved settings before launch. Keep operational Goals tied to the
attempt; finish them after reporting. Never replace an unrelated active Goal.

Record actual runtime versions, elapsed/prayer-window durations, counts, stop
reason, usage completeness and process shutdown. Verify both offline formats and
the TempleOS 640x480 frame. Keep real intentions, prayer text, account metadata,
private paths and controller IDs out of public release notes.

## Fresh-install candidate check

Before tagging a beta, use the pushed candidate's full commit SHA as
`CANDIDATE_SHA`. In the environment being tested, run these commands from an empty
folder outside the source checkout:

```bash
codex plugin marketplace add darvilp/burnt-offering --ref CANDIDATE_SHA
codex plugin add burnt-offering@burnt-offering
```

For a private repository, Git must already have read access in that environment.
If Burnt Offering is already installed, stop its active runs before removing the
plugin and catalog, then install the candidate. Record whether this is a first
installation or a reinstall. Do not overwrite unrelated marketplace entries.

Start a new Codex chat in the empty folder. First send only:

```text
$burnt-offering:pray
```

It should ask for missing parameters without creating a Goal or starting prayer
work. Then reply with this acceptance instruction:

```text
Use TempleOS devotion to pray for a safe journey. Run one subject for at most
10 seconds and 100 total turns, with no token ceiling. Inherit this chat's model
and effort. This authorizes one live cancellation test, including the matching
operational native Goal.

Use the installed Burnt Offering helper, not a source checkout. Show preflight's
resolved settings and runtime versions. Arrange cancellation before launch:
watch the private events.jsonl for the first record whose "kind" is "dispatch",
then issue the installed helper's stop command for that run ID. Keep the watcher
and runner active together so stop does not depend on another model response.
Do not wait for a completed prayer. Do not retry or start another run.

Wait for terminal status and report whether the stop reason is user_stop, how
many turns started and prayers completed, elapsed time, usage completeness and
unresolved batches. Confirm the owned runner and server processes exited. Show
the offline HTML and Markdown reports and check the HTML's 640x480 frame.
Treat unknown usage as unknown. A deadline stop does not pass the early-stop
check. Report any unsupported capability or failure without bypassing it.
```

This combines installed-skill setup and live cancellation. It establishes native
Windows behavior only when the controller, Python and Codex all run natively on
Windows. A fresh chat on an existing user profile is not a clean-machine test.

## GitHub publication, when requested

1. Commit reviewed source and metadata without private artifacts. Create the
   selected GitHub repository and push only when publication is authorized.
2. Let CI finish. Run **Build candidate** manually for the exact intended commit.
   Download its ZIP/checksum and compare with the reviewed candidate inputs.
3. Create tag `v0.1.0-beta.1` at that commit, then create a GitHub prerelease and
   attach the ZIP and checksum. Include the tested support matrix and known gaps.
4. Test the published installation from outside the source checkout:

   ```bash
   codex plugin marketplace add darvilp/burnt-offering --ref v0.1.0-beta.1
   codex plugin add burnt-offering@burnt-offering
   ```

5. Start a new Codex chat and invoke `$burnt-offering:pray`. Verify the guided
   setup without supplying an intention or starting a model turn.

Public-directory submission is a later milestone. GitHub publication alone does
not make this a browser-only ChatGPT workflow.

## Upgrades and rollback

Stop all active runs first. Remove the plugin and catalog, re-add the catalog at
the desired release tag, and install it again:

```bash
codex plugin remove burnt-offering@burnt-offering
codex plugin marketplace remove burnt-offering
codex plugin marketplace add darvilp/burnt-offering --ref VERSION_TAG
codex plugin add burnt-offering@burnt-offering
```

Use the previous tag for rollback. Never delete or migrate private run records as
part of these operations. Completed older records remain readable; active runs
are not automatically resumed across versions.
