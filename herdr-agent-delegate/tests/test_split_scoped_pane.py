import importlib.util
import json
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "split_scoped_pane.py"
SPEC = importlib.util.spec_from_file_location("split_scoped_pane", MODULE_PATH)
split_scoped_pane = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(split_scoped_pane)


def pane_payload(pane_id, workspace_id="w1", tab_id="w1:t1"):
    return {
        "result": {
            "pane": {
                "pane_id": pane_id,
                "workspace_id": workspace_id,
                "tab_id": tab_id,
            }
        }
    }


def tab_payload(pane_id, workspace_id="w1", tab_id="w1:t2"):
    return {"result": {"root_pane": pane_payload(pane_id, workspace_id, tab_id)["result"]["pane"]}}


def layout_payload(pane_ids, width=160, height=80):
    return {
        "result": {
            "layout": {
                "panes": [
                    {
                        "pane_id": pane_id,
                        "rect": {"width": width, "height": height},
                    }
                    for pane_id in pane_ids
                ]
            }
        }
    }


class Result:
    def __init__(self, payload=None, returncode=0, stderr=""):
        self.returncode = returncode
        self.stdout = "" if payload is None else json.dumps(payload)
        self.stderr = stderr


class HerdrMock:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, arguments, timeout=None):
        self.calls.append(arguments)
        expected, result = self.responses.pop(0)
        if arguments != expected:
            raise AssertionError(f"expected {expected}, got {arguments}")
        return result


def args(children=None, new_tab=False):
    return Namespace(
        parent_pane_id="w1:p1",
        cwd="/work",
        child=children or [],
        new_tab=new_tab,
    )


class SplitScopedPaneTest(unittest.TestCase):
    def split_responses(self, children, direction, child_id="w1:new"):
        target = "w1:p1" if not children else children[-1]
        pane_ids = ["w1:p1", *children]
        return [
            (["pane", "current", "--current"], Result(pane_payload("w1:p1"))),
            (["pane", "layout", "--pane", "w1:p1"], Result(layout_payload(pane_ids))),
            (["pane", "get", target], Result(pane_payload(target))),
            (
                [
                    "pane",
                    "split",
                    target,
                    "--direction",
                    direction,
                    "--ratio",
                    "0.5",
                    "--cwd",
                    "/work",
                    "--no-focus",
                ],
                Result(pane_payload(child_id)),
            ),
            (["pane", "get", child_id], Result(pane_payload(child_id))),
        ]

    def test_fixed_incremental_split_sequence(self):
        directions = ["right", "down", "right", "down"]
        for count, direction in enumerate(directions):
            children = [f"w1:p{number}" for number in range(2, count + 2)]
            mock = HerdrMock(self.split_responses(children, direction))
            with self.subTest(child=count + 1), patch.object(
                split_scoped_pane, "run_herdr", mock
            ):
                result = split_scoped_pane.run(args(children))
                self.assertFalse(result["new_tab"])
                self.assertEqual(mock.responses, [])

    def test_fifth_child_starts_new_tab(self):
        children = ["w1:p2", "w1:p3", "w1:p4", "w1:p5"]
        mock = HerdrMock(
            [
                (["pane", "current", "--current"], Result(pane_payload("w1:p1"))),
                (
                    ["pane", "layout", "--pane", "w1:p1"],
                    Result(layout_payload(["w1:p1", *children])),
                ),
                (["tab", "create", "--workspace", "w1", "--cwd", "/work", "--no-focus"], Result(tab_payload("w1:p10"))),
                (["pane", "get", "w1:p10"], Result(pane_payload("w1:p10", tab_id="w1:t2"))),
                (
                    ["pane", "split", "w1:p10", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"],
                    Result(pane_payload("w1:p11", tab_id="w1:t2")),
                ),
                (["pane", "get", "w1:p11"], Result(pane_payload("w1:p11", tab_id="w1:t2"))),
            ]
        )
        with patch.object(split_scoped_pane, "run_herdr", mock):
            result = split_scoped_pane.run(args(children))
        self.assertTrue(result["new_tab"])
        self.assertEqual(result["anchor_pane_id"], "w1:p10")

    def test_unrelated_pane_uses_new_tab_without_touching_it(self):
        mock = HerdrMock(
            [
                (["pane", "current", "--current"], Result(pane_payload("w1:p1"))),
                (["pane", "layout", "--pane", "w1:p1"], Result(layout_payload(["w1:p1", "w1:p9"]))),
                (["tab", "create", "--workspace", "w1", "--cwd", "/work", "--no-focus"], Result(tab_payload("w1:p10"))),
                (["pane", "get", "w1:p10"], Result(pane_payload("w1:p10", tab_id="w1:t2"))),
                (["pane", "split", "w1:p10", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"], Result(pane_payload("w1:p11", tab_id="w1:t2"))),
                (["pane", "get", "w1:p11"], Result(pane_payload("w1:p11", tab_id="w1:t2"))),
            ]
        )
        with patch.object(split_scoped_pane, "run_herdr", mock):
            split_scoped_pane.run(args())
        self.assertFalse(any(call[:2] == ["pane", "close"] for call in mock.calls))

    def test_new_pane_scope_is_verified_and_only_new_child_is_closed(self):
        responses = self.split_responses([], "right")[:-1]
        responses.extend(
            [
                (["pane", "get", "w1:new"], Result(pane_payload("w1:new", tab_id="w1:t9"))),
                (["pane", "close", "w1:new"], Result()),
            ]
        )
        mock = HerdrMock(responses)
        with patch.object(split_scoped_pane, "run_herdr", mock):
            with self.assertRaisesRegex(ValueError, "tab_id mismatch"):
                split_scoped_pane.run(args())
        self.assertEqual(mock.calls[-1], ["pane", "close", "w1:new"])

    def test_minimum_size_falls_back_to_new_tab(self):
        mock = HerdrMock(
            [
                (["pane", "current", "--current"], Result(pane_payload("w1:p1"))),
                (["pane", "layout", "--pane", "w1:p1"], Result(layout_payload(["w1:p1"], width=60, height=20))),
                (["pane", "get", "w1:p1"], Result(pane_payload("w1:p1"))),
                (["tab", "create", "--workspace", "w1", "--cwd", "/work", "--no-focus"], Result(tab_payload("w1:p10"))),
                (["pane", "get", "w1:p10"], Result(pane_payload("w1:p10", tab_id="w1:t2"))),
                (["pane", "split", "w1:p10", "--direction", "right", "--ratio", "0.5", "--cwd", "/work", "--no-focus"], Result(pane_payload("w1:p11", tab_id="w1:t2"))),
                (["pane", "get", "w1:p11"], Result(pane_payload("w1:p11", tab_id="w1:t2"))),
            ]
        )
        with patch.object(split_scoped_pane, "run_herdr", mock):
            result = split_scoped_pane.run(args())
        self.assertTrue(result["new_tab"])

    def test_new_tab_anchor_can_be_used_as_next_group_parent(self):
        mock = HerdrMock(
            [
                (["pane", "current", "--current"], Result(pane_payload("w1:p1"))),
                (["pane", "get", "w1:p10"], Result(pane_payload("w1:p10", tab_id="w1:t2"))),
                (["pane", "layout", "--pane", "w1:p10"], Result(layout_payload(["w1:p10", "w1:p11"]))),
                (["pane", "get", "w1:p11"], Result(pane_payload("w1:p11", tab_id="w1:t2"))),
                (["pane", "split", "w1:p11", "--direction", "down", "--ratio", "0.5", "--cwd", "/work", "--no-focus"], Result(pane_payload("w1:p12", tab_id="w1:t2"))),
                (["pane", "get", "w1:p12"], Result(pane_payload("w1:p12", tab_id="w1:t2"))),
            ]
        )
        group_args = Namespace(
            parent_pane_id="w1:p10",
            cwd="/work",
            child=["w1:p11"],
            new_tab=False,
        )
        with patch.object(split_scoped_pane, "run_herdr", mock):
            result = split_scoped_pane.run(group_args)
        self.assertFalse(result["new_tab"])
        self.assertEqual(result["pane_id"], "w1:p12")
