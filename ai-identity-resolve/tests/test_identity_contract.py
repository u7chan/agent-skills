import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPO_ROOT = ROOT.parent
POSTING_SKILL_PATHS = {
    "review": REPO_ROOT / "github-pr-review" / "SKILL.md",
    "reply": REPO_ROOT / "github-pr-comment-reply" / "SKILL.md",
}
FEEDBACK_SKILL_PATH = REPO_ROOT / "github-pr-feedback-address" / "SKILL.md"
OPENAI_YAML_PATHS = {
    "ai-identity-resolve": ROOT / "agents" / "openai.yaml",
    "github-pr-review": REPO_ROOT / "github-pr-review" / "agents" / "openai.yaml",
    "github-pr-comment-reply": REPO_ROOT
    / "github-pr-comment-reply"
    / "agents"
    / "openai.yaml",
    "github-pr-feedback-address": REPO_ROOT
    / "github-pr-feedback-address"
    / "agents"
    / "openai.yaml",
}


class IdentityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.openai_yaml = (ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        cls.posting_skills = {
            name: path.read_text(encoding="utf-8")
            for name, path in POSTING_SKILL_PATHS.items()
        }
        cls.feedback_skill = FEEDBACK_SKILL_PATH.read_text(encoding="utf-8")
        cls.openai_yamls = {
            name: path.read_text(encoding="utf-8")
            for name, path in OPENAI_YAML_PATHS.items()
        }

    def test_runtime_model_precedes_codex_config_fallback(self):
        priority = re.search(
            r"## モデル取得優先順位\n(?P<body>.*?)\n## 取得タイミングと所有者",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(priority)
        body = priority.group("body")

        session_index = body.index("現在のAgentセッション")
        cagent_index = body.index("Herdr/cagent")
        config_index = body.index("~/.codex/config.toml")
        unknown_index = body.index("すべて取得不能なら不明")

        self.assertLess(session_index, cagent_index)
        self.assertLess(cagent_index, config_index)
        self.assertLess(config_index, unknown_index)
        self.assertIn("1と2の実行モデルを取得できないCodexに限り", body)
        self.assertIn("モデル名を推測しない", body)

    def test_herdr_explicit_runtime_model_wins_over_config(self):
        self.assertIn(
            "Configが `gpt-5.6-sol` でも、Herdr/cagentの明示実行モデルが "
            "`gpt-5.6-terra` なら `gpt-5.6-terra` を使う",
            self.skill,
        )

    def test_normal_codex_falls_back_to_config(self):
        self.assertIn(
            "通常Codexで実行モデルを取得できず、Configが `gpt-5.6-sol` なら "
            "`gpt-5.6-sol` へフォールバックする",
            self.skill,
        )

    def test_unknown_model_is_not_guessed(self):
        self.assertIn(
            "実行モデルとConfigモデルの両方を取得できなければ、"
            "モデル名を省略するか契約上の不明値 `—` とし、推測しない",
            self.skill,
        )

    def test_identity_owner_and_handoff_timing_are_explicit(self):
        timing = re.search(
            r"## 取得タイミングと所有者\n(?P<body>.*?)\n## 出力",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(timing)
        body = timing.group("body")

        self.assertIn("現在Agent自身が自身の識別値の所有者", body)
        self.assertIn("会話開始時や過去の取得値を再利用しない", body)
        self.assertIn("委譲では親が親自身の値の所有者", body)
        self.assertIn("子paneの起動とinput-ready確認", body)
        self.assertIn("worktree・HEAD・remote ref・Issue/PR一覧", body)
        self.assertIn("ハンドオフ時点のメタ情報として固定", body)
        self.assertIn("子は親の識別値を再解決、推測、上書きしない", body)
        self.assertIn(
            "最終取得完了から `send_request.py` による送信まで、"
            "外部I/Oや識別情報の再取得を挟まない",
            body,
        )

    def test_openai_metadata_still_matches_skill(self):
        self.assertIn('display_name: "AI Identity Resolve"', self.openai_yaml)
        self.assertIn("実行モデル優先", self.openai_yaml)
        self.assertIn("$ai-identity-resolve", self.openai_yaml)

    def test_standard_contract_is_portable_without_repository_agents(self):
        self.assertIn(
            "利用先リポジトリの `AGENTS.md` の有無を前提としない標準契約",
            self.skill,
        )

    def test_direct_posting_skills_resolve_identity_immediately_before_posting(self):
        for name, skill in self.posting_skills.items():
            with self.subTest(skill=name):
                self.assertIn("`ai-identity-resolve`", skill)
                self.assertIn("投稿直前", skill)
                self.assertIn("必ず", skill)
                self.assertIn("利用先リポジトリの `AGENTS.md` を前提にせず", skill)

    def test_feedback_handoff_leaves_identity_to_posting_skill(self):
        self.assertIn("`github-pr-comment-reply`", self.feedback_skill)
        self.assertIn("`ai-identity-resolve`", self.feedback_skill)
        self.assertIn("AI識別値は引き渡さない", self.feedback_skill)
        self.assertIn("投稿直前", self.feedback_skill)

    def test_posting_consumers_do_not_pin_codex_config_model(self):
        consumers = [*self.posting_skills.values(), self.feedback_skill]
        for skill in consumers:
            self.assertNotIn("/home/u7dev/.codex/config.toml", skill)
            self.assertNotIn("~/.codex/config.toml", skill)
            self.assertNotIn("Codex の設定モデルを明記", skill)
            self.assertNotRegex(skill, r'model\s*=\s*["\']')

    def test_updated_openai_metadata_matches_each_skill(self):
        for skill_name, openai_yaml in self.openai_yamls.items():
            with self.subTest(skill=skill_name):
                self.assertIn(f"${skill_name}", openai_yaml)
        self.assertIn("current AI identity", self.openai_yamls["github-pr-review"])
        self.assertIn(
            "current AI identity",
            self.openai_yamls["github-pr-comment-reply"],
        )
        self.assertIn(
            "hand replies to the posting skill",
            self.openai_yamls["github-pr-feedback-address"],
        )


if __name__ == "__main__":
    unittest.main()
