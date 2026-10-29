import asyncio
import contextlib
from html.parser import HTMLParser
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/pray/scripts"))
SPEC = importlib.util.spec_from_file_location("pray", ROOT / "skills/pray/scripts/pray.py")
pray = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pray)
FAKE = Path(__file__).with_name("fake_app_server.py")
RUN_ID = "a" * 32
MODELS = [
    {"id": name, "model": name, "defaultReasoningEffort": default,
     "supportedReasoningEfforts": [{"reasoningEffort": effort} for effort in ("low", "medium", "high")]}
    for name, default in (("controller", "medium"), ("worker", "low"))
]


def make_spec(**overrides):
    args = pray.parser().parse_args([
        "run", "--run-id", RUN_ID, "--intention", "A safe journey",
        "--target", "Open invocation", "--duration", ".2", "--controller-thread", "controller"])
    for name, value in overrides.items(): setattr(args, name, value)
    return pray.build_spec(args)


class ConfigurationTests(unittest.TestCase):
    def test_missing_runner_reconciles_running_and_stopping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for state in ("RUNNING", "STOPPING", "STOPPED"):
                with self.subTest(state=state):
                    saved = {"state": state, "runner_pid": 123, "runner_start": "identity",
                             "stop_reason": "user_stop", "usage_complete": True}
                    (path / "status.json").write_text(json.dumps(saved), encoding="utf-8")
                    with mock.patch.object(pray, "process_start", return_value=None):
                        observed = pray.read_status(path)
                    if state == "STOPPED":
                        self.assertEqual(observed, saved)
                    else:
                        self.assertEqual(observed["state"], "INTERRUPTED")
                        self.assertEqual(observed["stop_reason"], "runner_missing")
                        self.assertFalse(observed["usage_complete"])
                    with mock.patch.object(pray, "process_start", return_value="identity"):
                        self.assertEqual(pray.read_status(path), saved)

    def test_four_model_selection_cases(self):
        controller = {"model": "controller", "reasoningEffort": "high"}
        cases = [(None, None, "controller", "high"), ("worker", None, "worker", "low"),
                 (None, "low", "controller", "low"), ("worker", "medium", "worker", "medium")]
        for model, effort, expected_model, expected_effort in cases:
            with self.subTest(model=model, effort=effort):
                self.assertEqual(pray.resolve_model(controller, MODELS, model, effort),
                                 {"model": expected_model, "effort": expected_effort})
        for model, effort in (("missing", None), ("worker", "unsupported")):
            with self.assertRaises(pray.PrayerError):
                pray.resolve_model(controller, MODELS, model, effort)

    def test_finite_limits_and_duration_only(self):
        self.assertIsNone(make_spec()["limits"]["tokens"])
        self.assertIsNone(make_spec()["limits"]["batches"])
        token_only = make_spec(duration=None, tokens=1000)["limits"]
        self.assertIsNone(token_only["duration_seconds"])
        self.assertIsNone(token_only["batches"])
        self.assertEqual(token_only["tokens"], 1000)
        for changes in ({"duration": None}, {"duration": float("inf")}, {"duration": float("nan")},
                        {"duration": -1}, {"tokens": -1}, {"concurrency": 0}, {"batch_timeout": float("inf")},
                        {"run_id": "../escape"}, {"max_batches": 0}, {"intention": ""}):
            with self.subTest(changes=changes), self.assertRaises(pray.PrayerError):
                make_spec(**changes)

    def test_explicit_turn_limit_is_sufficient_and_has_no_arbitrary_upper_cap(self):
        limits = make_spec(duration=None, max_batches=1001)["limits"]
        self.assertIsNone(limits["duration_seconds"])
        self.assertIsNone(limits["tokens"])
        self.assertEqual(limits["batches"], 1001)

    def test_explicit_unbounded_mode_removes_run_ceilings(self):
        args = pray.parser().parse_args([
            "preflight", "--intention", "A safe journey", "--target", "Open invocation", "--unbounded"])
        spec = pray.build_spec(args)
        self.assertEqual({key: spec["limits"][key] for key in ("duration_seconds", "tokens", "batches")},
                         {"duration_seconds": None, "tokens": None, "batches": None})
        self.assertEqual(spec["limits"]["concurrency"], 3)
        self.assertEqual(spec["limits"]["batch_seconds"], 90)
        json.dumps(spec, allow_nan=False)

    def test_templeos_devotion_selects_its_subject_and_retains_limits(self):
        args = pray.parser().parse_args([
            "preflight", "--intention", "A safe journey", "--duration", "45", "--devotion", "templeos"])
        spec = pray.build_spec(args)
        self.assertEqual(spec["devotion"], "templeos")
        self.assertEqual(len(spec["subjects"]), 1)
        self.assertEqual(spec["subjects"][0]["id"], "templeos")
        self.assertEqual(spec["subjects"][0]["target"], "God")
        self.assertEqual(spec["limits"]["duration_seconds"], 45)
        self.assertEqual(make_spec()["devotion"], "standard")
        for changes in ({"target": ["Zeus"]}, {"all": True}):
            with self.subTest(changes=changes), self.assertRaises(pray.PrayerError):
                make_spec(**{"devotion": "templeos", "target": None, **changes})

    def test_unbounded_mode_rejects_conflicting_ceilings(self):
        for changes in ({"duration": 45}, {"tokens": 1000}, {"max_batches": 100}):
            with self.subTest(changes=changes), self.assertRaises(pray.PrayerError):
                make_spec(**{"unbounded": True, "duration": None, **changes})

    def test_roster_and_ambiguity(self):
        roster = pray.load_subjects(use_all=True)
        self.assertEqual(len(roster), 25)
        self.assertEqual(len({entry["id"] for entry in roster}), 25)
        self.assertTrue(all(entry.get("reference", "").startswith("https://") for entry in roster))
        self.assertTrue(all(entry.get("languages") and all(isinstance(language, str) and language.strip()
                            for language in entry["languages"]) for entry in roster))
        self.assertEqual(pray.load_subjects(["Ganesh"])[0]["id"], "hindu-ganesha")
        self.assertEqual(pray.load_subjects(["christianity"])[0]["tradition"], "Christianity")
        for target, expected_id in (("Manichaeism", "manichaeism"), ("Gnosticism", "gnostic"),
                                    ("machine spirit", "machine-spirit"),
                                    ("The Sun", "sun"), ("Sun", "sun"), ("Sol", "sun"),
                                    ("Sol Invictus", "sun"), ("Unconquered Sun", "sun"),
                                    ("The Moon", "moon"), ("Moon", "moon")):
            with self.subTest(target=target):
                self.assertEqual(pray.load_subjects([target])[0]["id"], expected_id)
        self.assertEqual(pray.load_subjects(["machine-spirit"])[0]["tradition"], "Machine-spirit devotion")
        self.assertEqual([entry["id"] for entry in pray.load_subjects(["Sun", "Moon", "Ra"])],
                         ["sun", "moon", "egyptian-ra"])
        for targets in (["God"], ["Zeus", "greek-zeus"]):
            with self.assertRaises(pray.PrayerError): pray.load_subjects(targets)

    def test_deduplicate_cumulative_usage_and_exclude_cache(self):
        usage = pray.Usage()
        first = {"inputTokens": 100, "cachedInputTokens": 40, "outputTokens": 20, "totalTokens": 120}
        usage.observe("a", first)
        usage.observe("a", first)
        usage.observe("a", {"inputTokens": 50, "cachedInputTokens": 10, "outputTokens": 10, "totalTokens": 60})
        usage.observe("b", first)
        self.assertEqual(usage.totals()["goal_tokens"], 160)
        usage.observe("a", {"inputTokens": 200, "cachedInputTokens": 100, "outputTokens": 40, "totalTokens": 240})
        self.assertEqual(usage.totals()["goal_tokens"], 220)
        with self.assertRaises(pray.PrayerError): usage.observe("a", {})


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)
        self.server = None

    async def asyncTearDown(self):
        if self.server: await self.server.close()
        self.directory.cleanup()

    async def runner(self, scenario="normal", **changes):
        self.server = await pray.AppServer(self.path, [sys.executable, str(FAKE), scenario, RUN_ID]).start()
        info = {"goal": {"objective": f"prayer-run {RUN_ID}: test", "tokensUsed": 100, "status": "active"},
                "controller": {"model": "controller", "effort": "high"},
                "resolved": {"model": "worker", "effort": "low"}, "worker_config": dict(pray.WORKER_CONFIG)}
        spec = make_spec(**changes)
        return pray.Runner(self.server, info, spec, self.path)

    async def perform(self, runner):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = await runner.run()
        progress = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertTrue(all(entry["active_batches"] <= runner.spec["limits"]["concurrency"] for entry in progress))
        self.assertIsNotNone(self.server.process.returncode)
        self.assertTrue((self.path / "report.md").exists())
        self.assertTrue((self.path / "report.html").exists())
        return status

    async def test_default_launcher_reports_runtime_without_a_real_codex(self):
        def command(arguments):
            if arguments == ["--version"]:
                return [sys.executable, "-c", "print('codex-cli fixture')"]
            return [sys.executable, str(FAKE), "normal", RUN_ID]

        self.server = pray.AppServer(self.path)
        with mock.patch.object(pray, "codex_command", side_effect=command):
            await self.server.start()
        self.assertEqual(self.server.runtime["platform"], sys.platform)
        self.assertEqual(self.server.runtime["codex"], "codex-cli fixture")
        self.assertEqual(self.server.runtime["python"], sys.version.split()[0])

    async def test_logging_cap_keeps_counts_and_stops_recording_prayer_detail(self):
        runner = await self.runner(max_batches=20, duration=2)
        runner.detail_limit = 700
        status = await self.perform(runner)
        events = [json.loads(line) for line in (self.path / "events.jsonl").read_text().splitlines()]
        self.assertEqual(status["completed_prayers"], 20)
        self.assertEqual(status["usage"]["goal_tokens"], 2000)
        self.assertTrue(status["logging"]["detail_capped"])
        self.assertGreater(status["logging"]["omitted_events"], 0)
        self.assertLess(status["logging"]["saved_prayer_texts"], 20)
        self.assertLess((self.path / "events.jsonl").stat().st_size, 2000)
        self.assertEqual(events[-1]["kind"], "stopped")
        self.assertEqual(sum(event["kind"] == "logging_capped" for event in events), 1)
        self.assertEqual(len(runner.events), len(events))
        self.assertIn("omitted", (self.path / "report.md").read_text())

    async def test_cap_preserves_confirmation_of_previously_saved_text(self):
        runner = await self.runner(max_batches=1)
        runner.event("prayer_text", subject_id="custom-1", batch=1, text="A saved invocation")
        runner.detail_limit = runner.detail_bytes
        runner.event("dispatch", subject_id="custom-1", batch=2)
        runner.event("prayer", subject_id="custom-1", batch=1)
        report = pray.render_report(runner.status(), runner.events)
        self.assertIn("completed turn", report)
        self.assertNotIn("turn completion unconfirmed", report)
        self.assertIn("A saved invocation", report)

    async def test_log_cap_counts_utf8_bytes_and_does_not_save_oversized_text(self):
        runner = await self.runner()
        runner.detail_limit = 200
        runner.event("prayer_text", subject_id="custom-1", batch=1, text="雨" * 100)
        self.assertEqual(runner.saved_prayer_texts, 0)
        self.assertTrue(runner.detail_capped)
        for batch in range(1000):
            runner.event("prayer_text", subject_id="custom-1", batch=batch + 2, text="discarded")
        self.assertEqual(len(runner.events), 1)
        self.assertEqual(runner.omitted_events, 1001)
        self.assertLess((self.path / "events.jsonl").stat().st_size, 300)

    async def test_html_report_is_standalone_and_escapes_supplied_text(self):
        runner = await self.runner(max_batches=1, intention='<script>alert("intention")</script>')
        status = await self.perform(runner)
        malicious = '<img src="https://example.invalid/" onerror="alert(1)">'
        runner.events.append({"kind": "prayer_text", "subject_id": malicious, "batch": 2, "text": malicious})
        status["subjects"][0]["target"] = malicious
        report = pray.render_html_report(status, runner.events)

        class Elements(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []
                self.attributes = []

            def handle_starttag(self, tag, attrs):
                self.tags.append(tag)
                self.attributes.extend(attrs)

        elements = Elements()
        elements.feed(report)
        self.assertIn("html", elements.tags)
        self.assertIn("table", elements.tags)
        self.assertNotIn("script", elements.tags)
        self.assertNotIn("img", elements.tags)
        self.assertNotIn("link", elements.tags)
        self.assertFalse(any(key in ("src", "href", "onerror") for key, _ in elements.attributes))
        self.assertIn("&lt;script&gt;", report)
        self.assertIn("&lt;img", report)
        self.assertIn("May there be relief", report)
        if os.name != "nt":
            self.assertEqual((self.path / "report.html").stat().st_mode & 0o777, 0o600)

    async def test_legacy_events_stream_into_a_bounded_report(self):
        runner = await self.runner()
        status = runner.status()
        status.pop("logging", None)

        def events():
            for batch in range(1000):
                yield {"kind": "prayer_text", "subject_id": "custom-1", "batch": batch, "text": "x" * 500}
                yield {"kind": "prayer", "subject_id": "custom-1", "batch": batch}

        report = pray.render_report(status, events())
        self.assertLess(len(report.encode()), 40000)
        self.assertIn("older run", report)
        self.assertNotIn("turn completion unconfirmed", report)

    async def test_html_report_command_reads_saved_records_without_a_server(self):
        runner = await self.runner(max_batches=1)
        await self.perform(runner)
        saved = self.path / RUN_ID
        saved.mkdir()
        for filename in ("status.json", "events.jsonl"):
            (saved / filename).write_bytes((self.path / filename).read_bytes())
        args = pray.parser().parse_args([
            "--data-dir", str(self.path), "report", RUN_ID, "--format", "html"])
        with mock.patch.object(pray, "AppServer", side_effect=AssertionError("Report started a server")):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                await pray.execute(args)
        self.assertTrue(output.getvalue().startswith("<!doctype html>"))
        self.assertIn("May there be relief", output.getvalue())

    async def test_automatic_repetition_without_more_model_coordination(self):
        runner = await self.runner(max_batches=3)
        status = await self.perform(runner)
        self.assertEqual(status["completed_prayers"], 3)
        self.assertEqual(status["started_batches"], 3)
        self.assertEqual(status["stop_reason"], "batch_limit")
        self.assertEqual(status["usage"]["goal_tokens"], 300)

    async def test_language_palette_and_explicit_instructions_reach_worker(self):
        instructions = "Pray only in French. Preserve this intention: rétablissement."
        runner = await self.runner(target=["islam"], instructions=instructions)
        await runner.dispatch(0)
        turn = await self.server.rpc("test/lastTurn")
        assignment = json.loads(turn["input"][0]["text"].split("\n", 1)[1])
        self.assertEqual(assignment["languages"], ["Arabic"])
        self.assertEqual(assignment["instructions"], instructions)
        self.assertEqual(assignment["recipient"], "Allah")

    async def test_multilingual_text_and_language_palette_survive_reporting(self):
        runner = await self.runner("multilingual", target=["islam"], max_batches=1)
        status = await self.perform(runner)
        self.assertEqual(status["subjects"][0]["languages"], ["Arabic"])
        for filename in ("events.jsonl", "report.md", "report.html"):
            self.assertIn("سلام", (self.path / filename).read_text())
        for filename in ("report.md", "report.html"):
            self.assertIn("Arabic", (self.path / filename).read_text())

    async def test_templeos_devotion_reaches_worker_and_selects_report(self):
        runner = await self.runner(devotion="templeos", target=None, max_batches=1,
                                   intention='<script>alert("intention")</script>')
        status = await self.perform(runner)
        self.assertEqual(status["devotion"], "templeos")
        self.assertEqual(status["subjects"][0]["tradition"], "TempleOS devotion")
        report = (self.path / "report.html").read_text()
        self.assertIn('id="temple-screen"', report)
        for anchor in ("run-summary", "subject-coverage", "resource-accounting", "saved-prayers"):
            self.assertIn(f'href="#{anchor}"', report)
            self.assertIn(f'id="{anchor}"', report)
        self.assertIn("&lt;script&gt;", report)
        self.assertNotIn("<script", report.lower())
        self.assertIn("May there be relief", report)
        self.assertIn("Devotion: templeos", (self.path / "report.md").read_text())

    async def test_templeos_assignment_keeps_explicit_language_instructions(self):
        runner = await self.runner(devotion="templeos", target=None, instructions="Pray only in Hebrew.")
        await runner.dispatch(0)
        turn = await self.server.rpc("test/lastTurn")
        assignment = json.loads(turn["input"][0]["text"].split("\n", 1)[1])
        self.assertEqual(assignment["devotion"], "templeos")
        self.assertEqual(assignment["recipient"], "God")
        self.assertEqual(assignment["languages"], ["English"])
        self.assertEqual(assignment["instructions"], "Pray only in Hebrew.")

    async def test_unbounded_repeats_past_100_turns_until_user_stop(self):
        runner = await self.runner(unbounded=True, duration=None)

        async def stop_after_repetition():
            while sum(subject["completed"] for subject in runner.subjects) <= 100:
                await asyncio.sleep(.005)
            (self.path / "stop").touch()

        stopping = asyncio.create_task(stop_after_repetition())
        try:
            status = await asyncio.wait_for(self.perform(runner), 10)
        finally:
            stopping.cancel()
            await asyncio.gather(stopping, return_exceptions=True)
        self.assertGreater(status["completed_prayers"], 100)
        self.assertIsNone(runner.deadline)
        self.assertEqual(status["stop_reason"], "user_stop")
        self.assertIn("Run mode: unbounded", (self.path / "report.md").read_text())

    async def test_token_only_repeats_past_old_time_and_turn_caps_until_allowance(self):
        runner = await self.runner(duration=None, tokens=10500, concurrency=1)
        await runner.dispatch(0)
        runner.started -= 3600
        status = await self.perform(runner)
        self.assertEqual(status["stop_reason"], "token_limit")
        self.assertEqual(status["completed_prayers"], 105)
        self.assertEqual(status["usage"]["goal_tokens"], 10500)
        self.assertIsNone(runner.deadline)
        self.assertGreater(status["prayer_seconds"], 1200)
        markdown = (self.path / "report.md").read_text()
        html = (self.path / "report.html").read_text()
        self.assertIn("Run mode: bounded", markdown)
        self.assertIn("<td>bounded</td>", html)
        for report in (markdown, html):
            self.assertIn("No duration ceiling", report)
            self.assertIn("10,500 allowance tokens", report)
            self.assertIn("no turn ceiling", report)
            self.assertNotIn("None seconds", report)
            self.assertNotIn("None turns", report)

    async def test_duration_only_has_no_total_turn_ceiling(self):
        runner = await self.runner(duration=3600)
        runner.started = 0
        runner.deadline = 3600
        runner.clock = lambda: 1200
        runner.batch_count = 1001
        self.assertIsNone(runner.stop_reason())
        runner.clock = lambda: 3600
        self.assertEqual(runner.stop_reason(), "duration_limit")

    async def test_turn_only_limit_stops_and_reports_bounded(self):
        runner = await self.runner(duration=None, max_batches=3)
        status = await self.perform(runner)
        self.assertEqual(status["stop_reason"], "batch_limit")
        self.assertEqual(status["started_batches"], 3)
        self.assertEqual(status["completed_prayers"], 3)
        self.assertIsNone(runner.deadline)
        markdown = (self.path / "report.md").read_text()
        html = (self.path / "report.html").read_text()
        self.assertIn("Run mode: bounded", markdown)
        self.assertIn("<td>bounded</td>", html)
        for report in (markdown, html):
            self.assertIn("No duration ceiling; no token ceiling; 3 turns maximum", report)

    async def test_unbounded_has_no_elapsed_time_or_total_turn_ceiling(self):
        runner = await self.runner(unbounded=True, duration=None)
        runner.started = 100
        runner.clock = lambda: 1000000
        runner.batch_count = 1001
        self.assertIsNone(runner.stop_reason())

    async def test_unbounded_keeps_turn_timeout_and_stops_on_missing_usage(self):
        runner = await self.runner("missing_usage", unbounded=True, duration=None, batch_timeout=.06)
        status = await self.perform(runner)
        self.assertEqual(status["stop_reason"], "batch_timeout")
        self.assertEqual(status["started_batches"], 1)
        self.assertEqual(status["completed_prayers"], 1)
        self.assertFalse(status["usage_complete"])

    async def test_unbounded_uncertain_dispatch_times_out_without_replay(self):
        runner = await self.runner("missing_ack", unbounded=True, duration=None, batch_timeout=.06)
        status = await asyncio.wait_for(self.perform(runner), 3)
        self.assertEqual(status["stop_reason"], "batch_timeout")
        self.assertEqual(status["started_batches"], 1)
        self.assertEqual(status["unresolved_batches"], 1)

    async def test_every_subject_gets_first_turn_before_repetition(self):
        runner = await self.runner(target=["One", "Two", "Three", "Four"], max_batches=8, duration=2)
        status = await self.perform(runner)
        dispatched = [entry["subject_id"] for entry in runner.events if entry["kind"] == "dispatch"]
        self.assertEqual(len(set(dispatched[:4])), 4)
        self.assertEqual(status["completed_prayers"], 8)
        self.assertTrue(all(entry["completed"] == 2 for entry in status["subjects"]))

    async def test_deadline_interrupts_hanging_work_and_reports_unknown_usage(self):
        runner = await self.runner("hang", duration=.08)
        started = time.monotonic()
        status = await self.perform(runner)
        self.assertEqual(status["stop_reason"], "duration_limit")
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(status["started_batches"], 1)
        self.assertFalse(status["usage_complete"])
        self.assertEqual(status["unresolved_batches"], 1)

    async def test_token_ceiling_is_shared_not_per_subject(self):
        runner = await self.runner(target=["One", "Two", "Three"], tokens=150, duration=2)
        status = await self.perform(runner)
        self.assertEqual(status["stop_reason"], "token_limit")
        self.assertLessEqual(status["started_batches"], 3)
        self.assertGreaterEqual(status["usage"]["combined_goal_tokens"], 150)

    async def test_controller_consumption_can_stop_before_worker_dispatch(self):
        runner = await self.runner(tokens=50)
        runner.controller_tokens = 50
        status = await self.perform(runner)
        self.assertEqual(status["started_batches"], 0)
        self.assertEqual(status["stop_reason"], "token_limit")

    async def test_terminal_before_usage_is_not_lost(self):
        runner = await self.runner("terminal_first", max_batches=2)
        status = await self.perform(runner)
        self.assertEqual(status["completed_prayers"], 2)

    async def test_bad_effective_settings_start_no_paid_turn(self):
        runner = await self.runner("bad_settings")
        status = await self.perform(runner)
        self.assertEqual(status["started_batches"], 0)
        self.assertEqual(status["state"], "FAILED")

    async def test_forbidden_tool_stops_run(self):
        runner = await self.runner("tool")
        status = await self.perform(runner)
        self.assertEqual(status["state"], "FAILED")
        self.assertEqual(status["completed_prayers"], 0)
        self.assertEqual(status["started_batches"], 1)

    async def test_server_approval_requests_are_denied_on_the_wire(self):
        await self.runner()
        await self.server.rpc("test/requestApproval")
        self.assertEqual((await self.server.rpc("test/lastDecision"))["code"], -32601)
        methods = []
        while not self.server.events.empty(): methods.append(self.server.events.get_nowait()["method"])
        self.assertIn("prayer/forbiddenRequest", methods)

    async def test_missing_usage_stops_instead_of_rescheduling(self):
        runner = await self.runner("missing_usage", duration=2, batch_timeout=.06)
        status = await self.perform(runner)
        self.assertEqual(status["started_batches"], 1)
        self.assertEqual(status["stop_reason"], "batch_timeout")
        self.assertFalse(status["usage_complete"])
        self.assertEqual(status["completed_prayers"], 1)
        self.assertIn("May there be relief", (self.path / "report.md").read_text())

    async def test_controller_usage_is_reconciled_at_shutdown(self):
        runner = await self.runner("controller_final", max_batches=1)
        status = await self.perform(runner)
        self.assertEqual(status["usage"]["controller_goal_tokens"], 25)
        self.assertEqual(status["usage"]["combined_goal_tokens"], 125)
        self.assertTrue(status["usage_complete"])

    async def test_missing_final_controller_read_is_reported(self):
        runner = await self.runner("goal_final_fail", max_batches=1)
        status = await self.perform(runner)
        self.assertFalse(status["usage_complete"])
        self.assertIn("May there be relief", (self.path / "report.md").read_text())

    async def test_malformed_final_goal_still_produces_a_terminal_report(self):
        runner = await self.runner("goal_final_invalid", max_batches=1)
        status = await self.perform(runner)
        self.assertFalse(status["usage_complete"])
        self.assertNotEqual(status["state"], "STOPPING")
        self.assertIn("May there be relief", (self.path / "report.md").read_text())

    async def test_duplicate_terminal_and_text_events_are_idempotent(self):
        runner = await self.runner("duplicates", max_batches=2)
        status = await self.perform(runner)
        self.assertEqual(status["completed_prayers"], 2)
        report = (self.path / "report.md").read_text()
        self.assertEqual(report.count("May there be relief"), 2)

    async def test_backend_death_after_output_preserves_unconfirmed_text(self):
        runner = await self.runner("death_after_text")
        status = await self.perform(runner)
        report = (self.path / "report.md").read_text()
        self.assertIn("May there be relief", report)
        self.assertIn("turn completion unconfirmed", report)
        self.assertEqual(status["completed_prayers"], 0)

    async def test_backend_death_keeps_offline_report(self):
        runner = await self.runner("death", duration=2)
        status = await self.perform(runner)
        self.assertEqual(status["state"], "FAILED")
        self.assertFalse(status["usage_complete"])
        self.assertIn("Resource accounting", pray.render_report(status, runner.events))

    async def test_stop_control_closes_admission(self):
        runner = await self.runner("hang", duration=2)
        async def stop():
            await asyncio.sleep(.05)
            (self.path / "stop").touch()
        stopping = asyncio.create_task(stop())
        status = await self.perform(runner)
        await stopping
        self.assertEqual(status["stop_reason"], "user_stop")
        self.assertEqual(status["started_batches"], 1)

    async def test_uncertain_start_is_not_replayed(self):
        runner = await self.runner("missing_ack", duration=.06)
        started = time.monotonic()
        status = await self.perform(runner)
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(status["started_batches"], 1)
        self.assertEqual(status["stop_reason"], "duration_limit")
        self.assertEqual(status["unresolved_batches"], 1)

    async def test_known_next_turn_cost_can_stop_below_nominal_ceiling(self):
        runner = await self.runner(tokens=150, concurrency=1, duration=2)
        status = await self.perform(runner)
        self.assertEqual(status["started_batches"], 1)
        self.assertEqual(status["usage"]["goal_tokens"], 100)
        self.assertEqual(status["stop_reason"], "token_limit")

    async def test_early_timer_keeps_deadline_reason_without_early_admission_stop(self):
        runner = await self.runner()
        runner.clock = lambda: 9.99
        runner.deadline = 10
        with mock.patch.object(pray.time, "get_clock_info", return_value=mock.Mock(resolution=.015625)):
            self.assertIsNone(runner.stop_reason())
            self.assertEqual(runner.stop_reason(timer_expired=True), "duration_limit")
            runner.deadline = None
            runner.active = {"subject": {"deadline": 10}}
            self.assertIsNone(runner.stop_reason())
            self.assertEqual(runner.stop_reason(timer_expired=True), "batch_timeout")
            runner.clock = lambda: 9.9
            self.assertIsNone(runner.stop_reason(timer_expired=True))
            runner.stop_event.set()
            self.assertEqual(runner.stop_reason(timer_expired=True), "user_stop")

    async def test_clock_boundary_and_batch_timeout(self):
        runner = await self.runner()
        moment = [100.0]
        runner.clock = lambda: moment[0]
        runner.started, runner.deadline = 100, 145
        self.assertIsNone(runner.stop_reason())
        moment[0] = 145
        self.assertEqual(runner.stop_reason(), "duration_limit")

    async def test_changing_counts_do_not_emit_progress_for_every_prayer(self):
        runner = await self.runner()
        moment = [100.0]
        runner.clock = lambda: moment[0]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            for count in range(100):
                runner.batch_count = count
                runner.checkpoint()
            moment[0] += 1.01
            runner.checkpoint()
        self.assertEqual(len(output.getvalue().splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
