import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class AiWorkMetadataContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.delegation = (
            ROOT / "references" / "implementation-delegation.md"
        ).read_text(encoding="utf-8")
        template = re.search(
            r"```markdown\n(.*?)\n```", cls.skill, flags=re.DOTALL
        )
        assert template is not None
        cls.pr_body_template = template.group(1)

    def test_pr_body_ends_with_required_metadata_section(self):
        sections = re.split(r"^## ", self.pr_body_template, flags=re.MULTILINE)
        self.assertTrue(sections[-1].startswith("AI Work Metadata\n"))

        metadata_section = sections[-1]
        self.assertIn("| Role | Agent | Model | Effort |", metadata_section)
        self.assertIn(
            "| オーケストレーター | `<agent>` | `<model>` | `<effort>` |",
            metadata_section,
        )
        self.assertIn(
            "| 実装 | `<agent>` | `<model>` | `<effort>` |", metadata_section
        )

    def test_optional_roles_and_unknown_values_are_not_inferred(self):
        for text in (self.skill, self.delegation):
            self.assertIn("レビュー", text)
            self.assertIn("レビューFB", text)
            self.assertIn("推測", text)
            self.assertIn("—", text)

        self.assertIn("担当 Agent が会話または解決結果で確定", self.skill)
        self.assertIn("Agent 担当自体が未確定なら行を作らない", self.delegation)

    def test_model_uses_ai_identity_resolve_without_a_duplicate_priority(self):
        self.assertIn("`ai-identity-resolve` の標準契約を適用", self.delegation)
        self.assertIn("Model の優先順位はこの文書に再定義しない", self.delegation)
        self.assertIn("子役割の実行値が得られない場合に、親自身や別 Agent の Codex Config から Model を補完しない", self.delegation)
        self.assertNotIn("Model は各役割の現在の値について、次の順で解決する", self.delegation)

    def test_effort_priority_and_codex_only_config_fallback_are_explicit(self):
        effort = re.search(
            r"Effort は各役割の現在の値について、次の順で解決する。\n\n(?P<body>.*?)\n\nHerdr/cagent",
            self.delegation,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(effort)
        body = effort.group("body")

        session_index = body.index("現在セッション")
        cagent_index = body.index("Herdr/cagent")
        config_index = body.index("model_reasoning_effort")
        unknown_index = body.index("すべて取得不能なら `—`")
        self.assertLess(session_index, cagent_index)
        self.assertLess(cagent_index, config_index)
        self.assertLess(config_index, unknown_index)
        self.assertIn("通常 Codex に限り", body)
        self.assertIn("Herdr/cagent の明示または解決値は Config より優先する", self.delegation)
        self.assertIn("実行値を取得できない非Codex Agent へ Config fallback は行わない", self.delegation)

    def test_snapshot_contract_uses_the_same_terms_for_all_roles(self):
        self.assertIn("PR Work Metadata スナップショット", self.delegation)
        self.assertIn("各値の所有者は対象役割の現在 Agent", self.delegation)
        self.assertIn("現在 Agent 以外、別 pane、過去セッションの値を混ぜない", self.delegation)
        for role in ("オーケストレーター", "実装", "レビュー", "レビューFB"):
            with self.subTest(role=role):
                self.assertIn(f"| {role} |", self.delegation)

        review_loop = (ROOT / "references" / "review-loop.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("PR Work Metadata スナップショット", review_loop)
        self.assertIn("同じ用語・所有者・取得時点の契約", review_loop)
        self.assertIn("過去の PR 本文へ追加・更新しない", review_loop)

    def test_orchestrator_snapshot_is_resolved_immediately_before_send(self):
        self.assertIn("実装 pane の input-ready 確認を終え、実装依頼を送る直前", self.delegation)
        self.assertIn("取得不能なセルだけ `—`", self.delegation)

    def test_existing_comment_metadata_is_out_of_scope(self):
        self.assertIn("既存のレビューコメント・FB 対応コメントの AI 識別メタ情報は変更しない", self.skill)
        self.assertIn("既存のレビューコメント・FB 対応コメントの記録方法も変更しない", self.delegation)


if __name__ == "__main__":
    unittest.main()
