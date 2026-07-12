import importlib.util
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


layout_planner = load_module("layout_planner")
choose_layout = load_module("choose_layout")


def layout(*panes):
    return {
        "result": {
            "layout": {
                "panes": [
                    {"pane_id": pane_id, "rect": rect} for pane_id, rect in panes
                ]
            }
        }
    }


class LayoutPlannerTest(unittest.TestCase):
    def test_max_panes_per_tab_is_four(self):
        self.assertEqual(layout_planner.MAX_PANES_PER_TAB, 4)

    def test_incremental_rule_repeats_on_fifth_child(self):
        slots = [layout_planner.incremental_slot(number) for number in range(1, 6)]
        self.assertEqual(
            [slot["direction"] for slot in slots],
            ["right", "down", "right", "down", "right"],
        )
        self.assertEqual([slot["tab_index"] for slot in slots], [0, 0, 0, 0, 1])
        self.assertTrue(slots[4]["starts_new_tab"])

    def test_known_batch_is_split_into_tabs_up_front(self):
        self.assertEqual(
            layout_planner.plan_tabs(9),
            [
                {
                    "tab_index": 0,
                    "first_child": 1,
                    "child_count": 4,
                    "directions": ["right", "down", "right", "down"],
                },
                {
                    "tab_index": 1,
                    "first_child": 5,
                    "child_count": 4,
                    "directions": ["right", "down", "right", "down"],
                },
                {
                    "tab_index": 2,
                    "first_child": 9,
                    "child_count": 1,
                    "directions": ["right"],
                },
            ],
        )

    def test_unrelated_pane_requires_dedicated_tab(self):
        value = layout(
            ("w1:p1", {"width": 80, "height": 40}),
            ("w1:p9", {"width": 80, "height": 40}),
        )
        info = layout_planner.detect_existing_panes(value, "w1:p1")
        self.assertTrue(layout_planner.should_use_dedicated_tabs(2, info))

    def test_five_known_children_require_dedicated_tabs(self):
        info = {"has_unrelated": False, "unrelated_count": 0}
        self.assertFalse(layout_planner.should_use_dedicated_tabs(4, info))
        self.assertTrue(layout_planner.should_use_dedicated_tabs(5, info))

    def test_tab_size_uses_rect_offsets(self):
        value = layout(
            ("w1:p1", {"x": 26, "y": 1, "width": 60, "height": 40}),
            ("w1:p2", {"x": 86, "y": 1, "width": 60, "height": 40}),
        )
        self.assertEqual(layout_planner.tab_size_from_layout(value), (120, 40))


class ChooseLayoutTest(unittest.TestCase):
    def test_wide_pane_splits_right(self):
        result = choose_layout.choose(
            layout(("w1:p1", {"width": 80, "height": 40})), "w1:p1"
        )
        self.assertEqual(result["direction"], "right")

    def test_square_or_tall_pane_splits_down(self):
        for width, height in ((40, 40), (30, 60)):
            with self.subTest(width=width, height=height):
                result = choose_layout.choose(
                    layout(("w1:p1", {"width": width, "height": height})),
                    "w1:p1",
                )
                self.assertEqual(result["direction"], "down")

    def test_missing_target_fails(self):
        with self.assertRaises(ValueError):
            choose_layout.choose(layout(), "w1:p1")
