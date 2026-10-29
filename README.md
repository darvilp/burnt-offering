# Burnt Offering

A novelty Codex plugin that spends tokens on prayer. Give it an intention,
choose whom to address, and set a stopping rule. Agents pray in successive
turns while the chat reports progress. When the run ends, you get an offline
report with saved prayer excerpts, usage and the reason it stopped.

```text
$burnt-offering:pray Have an open, nonsectarian subject pray for a safe journey for 45 seconds.
```

This consumes your Codex usage. A short duration is the easiest way to try it.
Ask the chat to stop whenever you want, and keep the Codex environment active
while a run is in progress.

## Install the preview

The current preview is `0.1.0-beta.1`. The repository is private and there is no
tagged release yet, so Git needs authenticated read access to install it.

You need Python 3.11+ and an authenticated Codex CLI in the same environment as
your Codex chat. The tested CLI baseline is `0.164.0`; there are no extra Python
runtime packages.

```bash
codex plugin marketplace add darvilp/burnt-offering --ref main
codex plugin add burnt-offering@burnt-offering
```

Start a new Codex chat and invoke:

```text
$burnt-offering:pray
```

It will ask for the intention, recipients and stopping rule, with optional style,
language, model and effort choices. Gathering settings starts no prayer work.
You can also supply the settings in your invocation, as in the example above.

Linux/WSL has signed-in runtime testing. Native Windows still needs signed-in
acceptance, and macOS is experimental. See [platform evidence and remaining
checks](docs/release-readiness.md) before choosing a test environment. For a
repeatable installation test pinned to a commit, use the
[fresh-install procedure](docs/RELEASING.md#fresh-install-candidate-check).

## Choose the run

- **Recipients.** Use an open invocation, name recipients, or request the
  [23-entry starter roster](skills/pray/references/roster.json). Each selected
  entry gets its own agent. "All" selects that roster; it is not a claim to
  cover every religion or deity. Short runs may stop before every agent prays.
- **Practice and language.** Ask for original prayer, recitation or repetition.
  By default, agents mix English with brief phrases from their assigned
  tradition's suggested languages. Your explicit language instructions take
  precedence. The output is model-generated and is not independently verified
  liturgy or translation.
- **Limits.** Choose a duration, an optional token allowance, or both. Bounded
  runs also default to 100 total turns. Token-only runs also have a 20-minute
  duration ceiling. Explicitly asking to run unbounded until stopped removes
  run-level ceilings and keeps consuming usage until you stop it or a failure
  ends it. Missing settings never imply an unbounded run.
- **Model and effort.** Agents inherit the current chat's model and effort unless
  you override them. Choosing only a model uses that model's default effort.

An optional TempleOS devotion selects a God-directed assignment and a retro
report theme. The [skill reference](skills/pray/SKILL.md) covers this mode,
advanced settings and manual helper commands. Repository-local or standalone
skill installations use `$pray` instead of the plugin's qualified invocation.

## Usage and stopping

A token allowance counts uncached input plus output across the agents and
controller activity observed during the run. Setup and later chat narration are
outside that accounting window. Limits are approximate near boundaries; work
already in flight can incur usage after a stop threshold is observed.

The runner handles repetition without further prompts from you. Ask the chat to
stop and wait for confirmation that the run has ended. Runs need the foreground
helper and active Codex environment; they do not survive application shutdown or
restart automatically.

## Reports and saved prayers

Each finished run saves `report.html` and `report.md`. The HTML report opens
offline without scripts or external assets and includes:

- Saved prayer excerpts you can expand and read.
- Which recipients received prayer activity, including any that never started.
- Elapsed time, recorded token usage, stop reason and unresolved work or usage.

Prayer details have a 32 KiB recording budget. After that, new excerpts are
omitted while counts and usage continue. The report shows omissions, so its
examples should be read as a sample of the run.

Codex processes the intention and generates the prayers. The helper stores run
records locally, outside the checkout or installed plugin, under
`$XDG_DATA_HOME/prayer-runs` or normally `~/.local/share/prayer-runs`. Reports
contain your intention and retained prayer text.

## Remove or update

Stop active runs before removing or updating the plugin. To uninstall:

```bash
codex plugin remove burnt-offering@burnt-offering
codex plugin marketplace remove burnt-offering
```

Removal keeps saved run records. Delete finished run directories yourself when
you no longer want them. See the [release procedure](docs/RELEASING.md) for
updates and rollback.

For development, `python3 -m unittest discover -s tests -v` runs the tests without
model requests, and `python3 scripts/package.py` builds the plugin ZIP and
checksum. Use `py -3` on native Windows.

Licensed under [Apache 2.0](LICENSE).
