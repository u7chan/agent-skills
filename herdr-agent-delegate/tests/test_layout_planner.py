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
        # Simulate progressive splits for 4 children.
        panes = [("w1:p1", 120, 40)]
        children = []
        directions = []
        for _ in range(4):
            current = layout(*panes)
            result = choose_layout.choose(current, "w1:p1", children, 0.5, max_columns=2)
            directions.append(result["direction"])
            panes.append(("w1:px", 0, 0))
            children.append("w1:px")
        # The first child splits the parent right; subsequent splits should fill rows/cols.
        self.assertEqual(directions[0], "right")

    def test_max_columns_overrides_auto(self):
        value = layout(("w1:p1", 120, 40))
        result = choose_layout.choose(value, "w1:p1", [], 0.5, max_columns=1)
        self.assertEqual(result["plan"]["columns"], 1)


if __name__ == "__main__":
    unittest.main()
