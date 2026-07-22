import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"

spec = importlib.util.spec_from_file_location("layout_planner", SCRIPTS_DIR / "layout_planner.py")
layout_planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout_planner)


def _tmp(content):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(content, f)
    f.close()
    return f.name


class LayoutPlannerTest(unittest.TestCase):
    def test_max_four_parent_included(self):
        self.assertEqual(layout_planner.MAX_PANES_PER_TAB, 4)

    def test_parent_only_child1_ok(self):
        panes = [{"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}}]
        r = layout_planner.plan(panes, "w1:p1", [])
        self.assertFalse(r["use_new_tab"])
        self.assertEqual(r["direction"], "right")
        self.assertEqual(r["split_target"], "w1:p1")

    def test_four_children_requires_new_tab(self):
        panes = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p2", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p3", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p4", "rect": {"width": 80, "height": 40}},
        ]
        r = layout_planner.plan(panes, "w1:p1", ["w1:p2", "w1:p3", "w1:p4"])
        self.assertTrue(r["use_new_tab"])

    def test_three_children_still_fits_on_tab(self):
        panes = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p2", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p3", "rect": {"width": 80, "height": 40}},
        ]
        r = layout_planner.plan(panes, "w1:p1", ["w1:p2", "w1:p3"])
        self.assertFalse(r["use_new_tab"])
        self.assertEqual(r["direction"], "right")

    def test_unrelated_pane_forces_new_tab(self):
        panes = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p9", "rect": {"width": 80, "height": 40}},
        ]
        r = layout_planner.plan(panes, "w1:p1", [])
        self.assertTrue(r["use_new_tab"])

    def test_min_width_fallback(self):
        panes = [{"pane_id": "w1:p1", "rect": {"width": 60, "height": 80}}]
        r = layout_planner.plan(panes, "w1:p1", [])
        self.assertTrue(r["use_new_tab"])

    def test_min_height_fallback(self):
        panes = [{"pane_id": "w1:p1", "rect": {"width": 160, "height": 8}}]
        r = layout_planner.plan(panes, "w1:p1", [])
        self.assertTrue(r["use_new_tab"])

    def test_split_directions_cycle(self):
        p1 = [{"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}}]
        r1 = layout_planner.plan(p1, "w1:p1", [])
        self.assertEqual(r1["direction"], "right")

        p2 = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p2", "rect": {"width": 80, "height": 40}},
        ]
        r2 = layout_planner.plan(p2, "w1:p1", ["w1:p2"])
        self.assertEqual(r2["direction"], "down")

        p3 = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p2", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p3", "rect": {"width": 80, "height": 40}},
        ]
        r3 = layout_planner.plan(p3, "w1:p1", ["w1:p2", "w1:p3"])
        self.assertEqual(r3["direction"], "right")

    def test_missing_pane_id_raises(self):
        panes = [{"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}}]
        with self.assertRaises(ValueError):
            layout_planner.plan(panes, "w1:p1", ["w1:missing"])

    def test_invalid_rect_raises(self):
        panes = [{"pane_id": "w1:p1", "rect": {"width": 0, "height": 0}}]
        with self.assertRaises(ValueError):
            layout_planner.plan(panes, "w1:p1", [])

    def test_new_tab_flag_overrides(self):
        panes = [{"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}}]
        r = layout_planner.plan(panes, "w1:p1", [], new_tab=True)
        self.assertTrue(r["use_new_tab"])

    # --- Herdr 0.7.5 envelope support ---

    def test_herdr_envelope_accepted(self):
        envelope = {"result": {"layout": {"panes": [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
        ]}}}
        panes = layout_planner.extract_panes(envelope)
        self.assertEqual(len(panes), 1)
        self.assertEqual(panes[0]["pane_id"], "w1:p1")

    def test_plain_array_also_accepted(self):
        panes = layout_planner.extract_panes([{"pane_id": "w1:p1", "rect": {}}])
        self.assertEqual(len(panes), 1)

    def test_invalid_envelope_raises(self):
        with self.assertRaises(ValueError):
            layout_planner.extract_panes({"bad": "envelope"})
        with self.assertRaises(ValueError):
            layout_planner.extract_panes(42)

    # --- State transition: full tab → tab create → new root → children ---

    def test_full_tab_creates_new_tab_then_root_accepts_children(self):
        # Full tab: root + 3 children = 4 panes
        full_tab_panes = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p2", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p3", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p4", "rect": {"width": 80, "height": 40}},
        ]
        r = layout_planner.plan(full_tab_panes, "w1:p1", ["w1:p2", "w1:p3", "w1:p4"])
        self.assertTrue(r["use_new_tab"])

        # Simulate tab create → new root = w2:p10, child_ids reset
        new_root = "w2:p10"
        new_child_ids = []
        new_tab_panes = [{"pane_id": new_root, "rect": {"width": 160, "height": 80}}]

        # Child 1 on new tab
        r1 = layout_planner.plan(new_tab_panes, new_root, new_child_ids)
        self.assertFalse(r1["use_new_tab"])
        self.assertEqual(r1["child_index"], 1)
        self.assertEqual(r1["direction"], "right")

        new_child_ids.append("w2:p11")
        new_tab_panes.append({"pane_id": "w2:p11", "rect": {"width": 80, "height": 80}})

        # Child 2
        r2 = layout_planner.plan(new_tab_panes, new_root, new_child_ids)
        self.assertFalse(r2["use_new_tab"])
        self.assertEqual(r2["child_index"], 2)
        self.assertEqual(r2["direction"], "down")

        new_child_ids.append("w2:p12")
        new_tab_panes.append({"pane_id": "w2:p12", "rect": {"width": 80, "height": 40}})

        # Child 3
        r3 = layout_planner.plan(new_tab_panes, new_root, new_child_ids)
        self.assertFalse(r3["use_new_tab"])
        self.assertEqual(r3["child_index"], 3)
        self.assertEqual(r3["direction"], "right")

        # Child 4 → new tab again
        new_child_ids.append("w2:p13")
        new_tab_panes.append({"pane_id": "w2:p13", "rect": {"width": 80, "height": 40}})
        r4 = layout_planner.plan(new_tab_panes, new_root, new_child_ids)
        self.assertTrue(r4["use_new_tab"])

    def test_child_count_boundary_exact_4(self):
        panes = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p2", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p3", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p4", "rect": {"width": 80, "height": 40}},
        ]
        # root + 3 children = 4 → next needs new tab
        r = layout_planner.plan(panes, "w1:p1", ["w1:p2", "w1:p3", "w1:p4"])
        self.assertTrue(r["use_new_tab"])

    def test_child_count_boundary_3(self):
        panes = [
            {"pane_id": "w1:p1", "rect": {"width": 160, "height": 80}},
            {"pane_id": "w1:p2", "rect": {"width": 80, "height": 40}},
            {"pane_id": "w1:p3", "rect": {"width": 80, "height": 40}},
        ]
        # root + 2 children = 3 → still ok (next child would be 4th)
        r = layout_planner.plan(panes, "w1:p1", ["w1:p2", "w1:p3"])
        self.assertFalse(r["use_new_tab"])


if __name__ == "__main__":
    unittest.main()
