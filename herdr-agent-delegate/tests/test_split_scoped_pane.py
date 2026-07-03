import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "split_scoped_pane.py"
SPEC = importlib.util.spec_from_file_location("split_scoped_pane", MODULE_PATH)
split_scoped_pane = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(split_scoped_pane)


def pane_payload(pane_id: str, workspace_id: str = "w1", tab_id: str = "w1:t1", **extra: object) -> dict:
    return {"result": {"pane": {"pane_id": pane_id, "workspace_id": workspace_id, "tab_id": tab_id, **extra}}}


def layout_payload(
    panes: list[dict], workspace_id: str = "w1", tab_id: str = "w1:t1"
) -> dict:
    return {"result": {"layout": {"workspace_id": workspace_id, "tab_id": tab_id, "panes": panes}}}


class MockResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class HerdrMock:
    def __init__(self) -> None:
        self.responses: list[tuple[list[str], MockResult | Exception]] = []
        self.calls: list[list[str]] = []

    def add(self, arguments: list[str], result: MockResult) -> None:
        self.responses.append((arguments, result))

    def add_exception(self, arguments: list[str], exception: Exception) -> None:
        self.responses.append((arguments, exception))

    def __call__(self, arguments: list[str], timeout: float | None = None) -> MockResult:
        self.calls.append(arguments)
        for index, (expected, result) in enumerate(self.responses):
            if arguments == expected:
                self.responses.pop(index)
                if isinstance(result, Exception):
                    raise result
                return result
        raise AssertionError(f"unexpected herdr call: {arguments}")


class SplitScopedPaneTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.task_dir = Path(self.temporary.name) / "task"
        self.task_dir.mkdir()
        self.layout_file = Path(self.temporary.name) / "layout.json"

    def tearDown(self):
        self.temporary.cleanup()

    def write_layout(self, payload: dict) -> None:
        self.layout_file.write_text(json.dumps(payload), encoding="utf-8")

    def args(self, **overrides) -> Namespace:
        defaults = {
            "parent_pane_id": "w1:p1",
            "task_dir": str(self.task_dir),
            "cwd": "/work",
            "layout_file": str(self.layout_file),
            "child": [],
            "cell_aspect": 0.5,
        }
        defaults.update(overrides)
        return Namespace(**defaults)

    def diagnostics(self) -> dict:
        path = self.task_dir / "split_scoped_pane.diagnostics.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_successful_split_returns_verified_pane(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            result = split_scoped_pane.run(self.args())

        self.assertEqual(result, {"pane_id": "w1:p2", "workspace_id": "w1", "tab_id": "w1:t1"})
        self.assertFalse((self.task_dir / "split_scoped_pane.diagnostics.json").exists())

    def test_parent_mismatch_fails_before_split(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p9"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("w1:p9", self.diagnostics()["failure_reason"])
        self.assertNotIn(["pane", "split", "w1:p1", "--direction", "right"], mock.calls)

    def test_missing_workspace_id_in_parent_fails(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(
            ["pane", "current", "--current"],
            MockResult(stdout=json.dumps({"result": {"pane": {"pane_id": "w1:p1", "tab_id": "w1:t1"}}})),
        )

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("workspace_id", self.diagnostics()["failure_reason"])
        self.assertNotIn(["pane", "split", "w1:p1"], [c[:3] for c in mock.calls])

    def test_layout_scope_mismatch_fails_before_split(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}], workspace_id="w2"))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("layout workspace_id mismatch", self.diagnostics()["failure_reason"])
        self.assertNotIn(["pane", "split", "w1:p1"], [c[:3] for c in mock.calls])

    def test_layout_missing_parent_fails_before_split(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p9", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("parent pane is not present", self.diagnostics()["failure_reason"])

    def test_target_scope_mismatch_fails_before_split(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1", workspace_id="w2"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("split_target_before", self.diagnostics()["failure_reason"])
        self.assertNotIn(["pane", "split", "w1:p1"], [c[:3] for c in mock.calls])

    def test_split_command_failure_does_not_close(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(returncode=1, stderr="split rejected"),
        )

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("split rejected", self.diagnostics()["failure_reason"])
        self.assertNotIn(["pane", "close", "w1:p2"], mock.calls)

    def test_parent_moved_after_split_triggers_safe_close(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1", workspace_id="w2"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))
        mock.add(["pane", "close", "w1:p2"], MockResult())

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertIn("parent_after", diagnostics["failure_reason"])
        self.assertTrue(diagnostics["close_attempted"])
        self.assertTrue(diagnostics["close_succeeded"])
        self.assertEqual(["pane", "close", "w1:p2"], mock.calls[-1])

    def test_new_pane_scope_mismatch_triggers_safe_close(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2", workspace_id="w2"))))
        mock.add(["pane", "close", "w1:p2"], MockResult())

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertIn("new_pane_after", diagnostics["failure_reason"])
        self.assertTrue(diagnostics["close_attempted"])
        self.assertTrue(diagnostics["close_succeeded"])

    def test_duplicate_new_pane_id_is_not_closed(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p1"))),
        )

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertIn("already present before the split", diagnostics["failure_reason"])
        self.assertFalse(diagnostics["close_attempted"])
        self.assertNotIn(["pane", "close", "w1:p1"], mock.calls)

    def test_close_failure_is_recorded_without_retry(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1", workspace_id="w2"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))
        mock.add(["pane", "close", "w1:p2"], MockResult(returncode=1, stderr="close rejected"))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertTrue(diagnostics["close_attempted"])
        self.assertFalse(diagnostics["close_succeeded"])
        self.assertEqual(diagnostics["close_stderr"], "close rejected")
        close_calls = [c for c in mock.calls if c[:2] == ["pane", "close"]]
        self.assertEqual(len(close_calls), 1)

    def test_child_candidate_is_preferred_and_verified(self):
        self.write_layout(
            layout_payload(
                [
                    {"pane_id": "w1:p1", "rect": {"width": 60, "height": 40}},
                    {"pane_id": "w1:p2", "rect": {"width": 120, "height": 40}},
                ]
            )
        )
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))
        mock.add(
            ["pane", "split", "w1:p2", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p3"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p3"], MockResult(stdout=json.dumps(pane_payload("w1:p3"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            result = split_scoped_pane.run(self.args(child=["w1:p2"]))

        self.assertEqual(result["pane_id"], "w1:p3")

    def test_layout_fetched_via_herdr_when_file_not_given(self):
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "layout", "--pane", "w1:p1"],
            MockResult(stdout=json.dumps(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))),
        )
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            result = split_scoped_pane.run(self.args(layout_file=None))

        self.assertEqual(result["pane_id"], "w1:p2")
        self.assertIn(["pane", "layout", "--pane", "w1:p1"], mock.calls)

    def test_empty_tab_id_in_layout_fails(self):
        self.write_layout(
            {"result": {"layout": {"workspace_id": "w1", "tab_id": "", "panes": [{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]}}}
        )
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("layout tab_id", self.diagnostics()["failure_reason"])

    def test_tab_id_mismatch_in_new_pane_triggers_close(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2", tab_id="w1:t2"))))
        mock.add(["pane", "close", "w1:p2"], MockResult())

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertIn("new_pane_after", diagnostics["failure_reason"])
        self.assertTrue(diagnostics["close_attempted"])

    def test_empty_new_pane_id_is_not_closed(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps({"result": {"pane": {"pane_id": "", "workspace_id": "w1", "tab_id": "w1:t1"}}})),
        )

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertIn("pane_id is not a non-empty string", diagnostics["failure_reason"])
        self.assertFalse(diagnostics["close_attempted"])
        self.assertNotIn(["pane", "close", ""], mock.calls)

    def test_post_validation_pane_get_failure_triggers_safe_close(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(returncode=1, stderr="pane vanished"))
        mock.add(["pane", "close", "w1:p2"], MockResult())

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertIn("pane get w1:p2 failed", diagnostics["failure_reason"])
        self.assertTrue(diagnostics["close_attempted"])
        self.assertTrue(diagnostics["close_succeeded"])

    def test_command_order_is_pre_validation_split_post_validation(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            split_scoped_pane.run(self.args())

        self.assertEqual(mock.calls[0], ["pane", "current", "--current"])
        self.assertEqual(mock.calls[1], ["pane", "get", "w1:p1"])
        self.assertEqual(mock.calls[2][:2], ["pane", "split"])
        self.assertEqual(mock.calls[3], ["pane", "current", "--current"])
        self.assertEqual(mock.calls[4], ["pane", "get", "w1:p2"])

    def test_non_string_identifier_is_rejected(self):
        cases = [
            ("pane_id", None),
            ("pane_id", 123),
            ("workspace_id", None),
            ("workspace_id", 123),
            ("tab_id", None),
            ("tab_id", 123),
        ]
        for field, bad_value in cases:
            with self.subTest(field=field, value=bad_value):
                self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
                pane = {"pane_id": "w1:p2", "workspace_id": "w1", "tab_id": "w1:t1"}
                pane[field] = bad_value
                mock = HerdrMock()
                mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
                mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
                mock.add(
                    ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
                    MockResult(stdout=json.dumps({"result": {"pane": pane}})),
                )

                with patch.object(split_scoped_pane, "run_herdr", mock):
                    with self.assertRaises(SystemExit):
                        split_scoped_pane.run(self.args())

                self.assertIn(f"{field} is not a non-empty string", self.diagnostics()["failure_reason"])

    def test_pane_get_returning_different_id_fails(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p99"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        self.assertIn("unexpected pane_id", self.diagnostics()["failure_reason"])

    def test_success_uses_post_validated_pane_values(self):
        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        # split response scope differs from post-validated scope to ensure output comes from post-validation
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2", workspace_id="w2", tab_id="w2:t1"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            result = split_scoped_pane.run(self.args())

        self.assertEqual(result["pane_id"], "w1:p2")
        self.assertEqual(result["workspace_id"], "w1")
        self.assertEqual(result["tab_id"], "w1:t1")

    def test_close_timeout_is_recorded(self):
        import subprocess as sp

        self.write_layout(layout_payload([{"pane_id": "w1:p1", "rect": {"width": 120, "height": 40}}]))
        mock = HerdrMock()
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(["pane", "get", "w1:p1"], MockResult(stdout=json.dumps(pane_payload("w1:p1"))))
        mock.add(
            ["pane", "split", "w1:p1", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
            MockResult(stdout=json.dumps(pane_payload("w1:p2"))),
        )
        mock.add(["pane", "current", "--current"], MockResult(stdout=json.dumps(pane_payload("w1:p1", workspace_id="w2"))))
        mock.add(["pane", "get", "w1:p2"], MockResult(stdout=json.dumps(pane_payload("w1:p2"))))
        mock.add_exception(["pane", "close", "w1:p2"], sp.TimeoutExpired(cmd=["herdr", "pane", "close", "w1:p2"], timeout=10))

        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaises(SystemExit):
                split_scoped_pane.run(self.args())

        diagnostics = self.diagnostics()
        self.assertTrue(diagnostics["close_attempted"])
        self.assertFalse(diagnostics["close_succeeded"])
        self.assertEqual(diagnostics["close_exit_code"], None)
        self.assertEqual(diagnostics["close_timeout_seconds"], 10)


if __name__ == "__main__":
    unittest.main()
