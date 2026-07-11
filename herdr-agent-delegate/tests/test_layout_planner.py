import importlib.util
import unittest
from pathlib import Path
from unittest import mock


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
    return {"result": {"layout": {"panes": [
        {"pane_id": pane_id, "rect": {"width": width, "height": height}}
        for pane_id, width, height in panes
    ]}}}


class LayoutPlannerTest(unittest.TestCase):
    def test_compute_columns_for_4_children_landscape(self):
        plan = layout_planner.plan_grid(4, 120, 40, cell_aspect=0.5, max_columns=3, min_width=60)
        self.assertEqual(plan["columns"], 2)
        self.assertEqual(plan["rows"], 2)
        self.assertEqual(plan["slots"], [
            {"row": 0, "col": 0},
            {"row": 0, "col": 1},
            {"row": 1, "col": 0},
            {"row": 1, "col": 1},
        ])

    def test_compute_columns_for_5_children_landscape(self):
        plan = layout_planner.plan_grid(5, 120, 40, cell_aspect=0.5, max_columns=3, min_width=60)
        self.assertIn(plan["columns"], [2, 3])
        self.assertGreaterEqual(plan["rows"], 2)
        self.assertEqual(len(plan["slots"]), 5)

    def test_min_width_limits_columns(self):
        plan = layout_planner.plan_grid(4, 120, 40, max_columns=4, min_width=80)
        # Each cell must be at least 80 wide; 120 // 3 = 40 < 80, so max usable columns is 1.
        self.assertLessEqual(plan["columns"], 1)

    def test_min_height_limits_rows(self):
        plan = layout_planner.plan_grid(4, 120, 40, max_columns=2, min_height=25)
        # 2 columns and 2 rows -> 40 // 2 = 20 < 25, so capacity is reduced.
        self.assertLessEqual(plan["capacity"], 2)

    def test_plan_capacity_respects_max_panes_per_tab(self):
        plan = layout_planner.plan_grid(10, 1000, 1000, max_columns=10)
        self.assertLessEqual(plan["capacity"], layout_planner.DEFAULT_MAX_PANES_PER_TAB)

    def test_tab_size_from_layout(self):
        value = layout(("w1:p1", 120, 40), ("w1:p2", 60, 40))
        self.assertEqual(layout_planner.tab_size_from_layout(value), (120, 40))


class ChooseLayoutTest(unittest.TestCase):
    def test_first_split_uses_wide_parent(self):
        result = choose_layout.choose(layout(("w1:p1", 120, 40)), "w1:p1", [], 0.5)
        self.assertEqual(result["target_pane_id"], "w1:p1")
        self.assertEqual(result["direction"], "right")
        self.assertEqual(result["ratio"], 0.5)
        self.assertIn("plan", result)
        self.assertEqual(result["plan"]["columns"], 1)

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

    def test_grid_direction_for_four_children(self):
        # Simulate progressive splits for 4 children on a large enough tab.
        panes = [("w1:p1", 240, 80)]
        children = []
        directions = []
        for _ in range(4):
            current = layout(*panes)
            result = choose_layout.choose(current, "w1:p1", children, 0.5, max_columns=2, min_width=1, min_height=1)
            directions.append(result["direction"])
            panes.append(("w1:px", 0, 0))
            children.append("w1:px")
        # The first child splits the parent right; subsequent splits should fill rows/cols.
        self.assertEqual(directions[0], "right")

    def test_max_columns_overrides_auto(self):
        value = layout(("w1:p1", 120, 40))
        result = choose_layout.choose(value, "w1:p1", [], 0.5, max_columns=1)
        self.assertEqual(result["plan"]["columns"], 1)

    def test_max_columns_zero_means_auto(self):
        # 120x40, 0.5 aspect -> estimated columns for 4 children should be 2, not 1.
        plan = layout_planner.plan_grid(4, 120, 40, cell_aspect=0.5, max_columns=0, min_width=1)
        self.assertGreater(plan["columns"], 1)

    def test_capacity_exceeded_raises(self):
        # A tiny tab fits at most 1 child; requesting 2 should fail.
        value = layout(("w1:p1", 40, 20))
        with self.assertRaises(ValueError):
            choose_layout.choose(value, "w1:p1", [], 0.5, min_width=30, min_height=15, total_children=2)

    def test_total_children_affects_plan(self):
        # Pre-plan for 4 total children while only one child exists so far.
        value = layout(("w1:p1", 240, 80))
        result = choose_layout.choose(value, "w1:p1", ["w1:p2"], 0.5, max_columns=2, total_children=4, min_width=1, min_height=1)
        self.assertEqual(result["plan"]["columns"], 2)
        self.assertEqual(result["plan"]["rows"], 2)


class DetectExistingPanesTest(unittest.TestCase):
    def test_detect_existing_panes_unrelated(self):
        value = layout(
            ("w1:p1", 60, 40),
            ("w1:p2", 60, 40),
            ("w1:p9", 120, 40),
        )
        info = layout_planner.detect_existing_panes(value, parent_id="w1:p1", children=["w1:p2"])
        self.assertTrue(info["has_unrelated"])
        self.assertEqual(info["unrelated_count"], 1)

    def test_detect_existing_panes_no_unrelated(self):
        value = layout(
            ("w1:p1", 60, 40),
            ("w1:p2", 60, 40),
        )
        info = layout_planner.detect_existing_panes(value, parent_id="w1:p1", children=["w1:p2"])
        self.assertFalse(info["has_unrelated"])
        self.assertEqual(info["unrelated_count"], 0)

    def test_detect_existing_panes_empty(self):
        value = layout()
        info = layout_planner.detect_existing_panes(value, parent_id="w1:p1")
        self.assertFalse(info["has_unrelated"])
        self.assertEqual(info["unrelated_count"], 0)


class ShouldUseDedicatedTabTest(unittest.TestCase):
    def test_should_use_dedicated_tab_with_unrelated(self):
        info = {"has_unrelated": True, "unrelated_count": 1}
        result = layout_planner.should_use_dedicated_tab(2, 120, 40, info)
        self.assertTrue(result)

    def test_should_use_dedicated_tab_capacity_shortage(self):
        info = {"has_unrelated": False, "unrelated_count": 0}
        result = layout_planner.should_use_dedicated_tab(4, 40, 20, info, min_width=30, min_height=15)
        self.assertTrue(result)

    def test_should_use_dedicated_tab_high_count(self):
        info = {"has_unrelated": False, "unrelated_count": 0}
        result = layout_planner.should_use_dedicated_tab(
            6, 1000, 1000, info, max_panes_per_tab=6
        )
        self.assertTrue(result)

    def test_should_not_use_dedicated_tab_normal(self):
        info = {"has_unrelated": False, "unrelated_count": 0}
        result = layout_planner.should_use_dedicated_tab(3, 240, 80, info)
        self.assertFalse(result)

    def test_should_not_use_dedicated_tab_when_auto_disabled(self):
        info = {"has_unrelated": True, "unrelated_count": 5}
        with mock.patch.object(layout_planner, "AUTO_DEDICATED_TAB", False):
            result = layout_planner.should_use_dedicated_tab(2, 120, 40, info)
            self.assertFalse(result)


class PlanDedicatedTabTest(unittest.TestCase):
    def test_plan_dedicated_tab(self):
        plan = layout_planner.plan_dedicated_tab(4, 240, 80, cell_aspect=0.5, max_columns=2, min_width=1)
        self.assertEqual(plan["columns"], 2)
        self.assertEqual(plan["rows"], 2)
        self.assertEqual(len(plan["slots"]), 4)

    def test_plan_dedicated_tab_single(self):
        plan = layout_planner.plan_dedicated_tab(1, 120, 40)
        self.assertEqual(plan["columns"], 1)
        self.assertEqual(plan["rows"], 1)


class LayoutForAgentCountTest(unittest.TestCase):
    def test_layout_for_1_agent(self):
        plan = layout_planner.plan_grid(1, 120, 40, cell_aspect=0.5, max_columns=0, min_width=1, min_height=1)
        self.assertEqual(plan["columns"], 1)
        self.assertEqual(plan["rows"], 1)
        self.assertEqual(plan["slots"], [{"row": 0, "col": 0}])

    def test_layout_for_2_agents(self):
        plan = layout_planner.plan_grid(2, 240, 80, cell_aspect=0.5, max_columns=2, min_width=1, min_height=1)
        self.assertGreaterEqual(plan["capacity"], 2)
        self.assertIn(plan["columns"], [1, 2])

    def test_layout_for_3_plus_agents(self):
        plan = layout_planner.plan_grid(4, 240, 80, cell_aspect=0.5, max_columns=2, min_width=1, min_height=1)
        self.assertEqual(plan["columns"], 2)
        self.assertEqual(plan["rows"], 2)
        self.assertEqual(len(plan["slots"]), 4)
