import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class IssueCreationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        template = re.search(
            r"```markdown\n(.*?)\n```", cls.skill, flags=re.DOTALL
        )
        assert template is not None
        cls.issue_body_template = template.group(1)

    def test_issue_body_ends_with_english_metadata_heading(self):
        sections = re.split(r"^## ", self.issue_body_template, flags=re.MULTILINE)
        self.assertTrue(sections[-1].startswith("AI Work Metadata\n"))
        self.assertIn("| Role | Agent | Model | Effort |", sections[-1])
        self.assertNotIn("AI作業メタ情報", self.skill)

    def test_parent_compares_pre_and_post_delegation_snapshots(self):
        for command in (
            "git status --short",
            "git rev-parse HEAD",
            "git ls-remote --heads",
            "gh issue list --author @me --state all",
            "gh pr list --author @me --state all",
            "--limit 1000 --json number,url",
        ):
            self.assertIn(command, self.skill)

        self.assertIn("送信前スナップショットと完全一致", self.skill)
        self.assertIn("今回のIssue 1件だけ", self.skill)
        self.assertIn("PR作成を検出していない", self.skill)

    def test_handoff_resolves_and_freezes_parent_runtime_identity_before_send(self):
        dispatch_step = re.search(
            r"4\. 入力可能確認後、`send_request\.py`で依頼を送信する直前に、"
            r"親が次の順で送信前処理を完了する。(?P<steps>.*?)\n\n## 3\.",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(dispatch_step)
        steps = dispatch_step.group("steps")

        pane_start_index = self.skill.index("`herdr pane run`")
        input_ready_index = self.skill.index("input-ready確認")
        worktree_snapshot_index = steps.index("送信前スナップショットとして保持")
        final_identity_index = steps.index("識別情報を所有者である親が再取得")
        for command in (
            "git status --short",
            "git rev-parse HEAD",
            "git ls-remote --heads",
            "gh issue list --author @me --state all --limit 1000 --json number,url",
            "gh pr list --author @me --state all --limit 1000 --json number,url",
        ):
            command_index = steps.index(command)
            self.assertLess(command_index, final_identity_index, command)
        metadata_snapshot_index = steps.index(
            "ハンドオフ時点のメタ情報スナップショットとして固定"
        )
        send_index = steps.index("`send_request.py`でEnter込みで一度だけ送信")

        self.assertLess(pane_start_index, input_ready_index)
        self.assertLess(
            input_ready_index,
            self.skill.index("送信前スナップショットとして保持"),
        )
        self.assertLess(worktree_snapshot_index, final_identity_index)
        self.assertLess(final_identity_index, metadata_snapshot_index)
        self.assertLess(metadata_snapshot_index, send_index)
        self.assertIn("会話開始時または過去の取得値を使わない", steps)
        self.assertIn(
            "現在のAgentセッション、親paneを起動したHerdr/cagentの"
            "明示または解決済み実行モデルの順で取得",
            steps,
        )
        config_index = steps.index("`~/.codex/config.toml`を直接再読込")
        self.assertLess(final_identity_index, config_index)
        self.assertIn("どちらも取得できないCodexの場合だけ", steps)
        self.assertIn("それも取得できない場合だけModelを`—`とする", steps)
        self.assertIn("モデル名は推測せず", steps)
        self.assertIn("子は親の値を再解決、推測、上書きせず", steps)
        self.assertIn(
            "親自身の識別情報の最終取得完了から送信まで、"
            "外部I/Oや識別情報の再取得を挟まない",
            steps,
        )
        self.assertIn("送信後に壁打ち担当の識別情報を再取得または変更しない", steps)

    def test_forbidden_operations_fail_closed_and_keep_pane(self):
        self.assertIn("herdr pane read --source recent-unwrapped", self.skill)
        self.assertIn("出力が欠ける、判定できない", self.skill)
        self.assertIn("禁止操作の検出、スナップショット不一致、確認不能", self.skill)
        self.assertIn("paneを診断用に保持して停止", self.skill)
        for operation in (
            "HTML生成",
            "再委譲",
            "commit",
            "push",
            "PR作成",
        ):
            self.assertIn(operation, self.skill)


if __name__ == "__main__":
    unittest.main()
