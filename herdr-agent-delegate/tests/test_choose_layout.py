import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "choose_layout.py"
SPEC = importlib.util.spec_from_file_location("choose_layout", MODULE_PATH)
choose_layout = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(choose_layout)


def layout(*panes):
    return {"result": {"layout": {"panes": [
        {"pane_id": pane_id, "rect": {"width": width, "height": height}}
        for pane_id, width, height in panes
    ]}}}


class ChooseLayoutTest(unittest.TestCase):
    def test_first_split_uses_wide_parent(self):
        result = choose_layout.choose(layout(("w1:p1", 120, 40)), "w1:p1", [], 0.5)
        self.assertEqual(result, {"target_pane_id": "w1:p1", "direction": "right", "ratio": 0.5})

    def test_second_split_prefers_equal_area_child_and_goes_down(self):
        value = layout(("w1:p1", 60, 40), ("w1:p2", 60, 40), ("w1:p9", 200, 50))
        result = choose_layout.choose(value, "w1:p1", ["w1:p2"], 0.5)
        self.assertEqual(result["target_pane_id"], "w1:p2")
        self.assertEqual(result["direction"], "down")

    def test_unrelated_larger_pane_is_ignored(self):
        value = layout(("w1:p1", 50, 30), ("w1:p2", 50, 30), ("w1:p9", 200, 80))
        result = choose_layout.choose(value, "w1:p1", ["w1:p2"], 0.5)
        self.assertNotEqual(result["target_pane_id"], "w1:p9")

    def test_missing_parent_fails(self):
        with self.assertRaises(ValueError):
            choose_layout.choose(layout(("w1:p2", 80, 30)), "w1:p1", [], 0.5)


if __name__ == "__main__":
    unittest.main()
