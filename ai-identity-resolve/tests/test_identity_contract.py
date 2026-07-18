import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPO_ROOT = ROOT.parent
POSTING_SKILL_PATHS = {
    "review": REPO_ROOT / "github-pr-review" / "SKILL.md",
    "reply": REPO_ROOT / "github-pr-comment-reply" / "SKILL.md",
}
POSTING_RULE_PATHS = {
    "review": REPO_ROOT / "github-pr-review" / "references" / "posting-rules.md",
    "reply": REPO_ROOT
    / "github-pr-comment-reply"
    / "references"
    / "posting-rules.md",
}
API_PATHS = {
    "review": REPO_ROOT / "github-pr-review" / "references" / "posting-api.md",
    "reply": REPO_ROOT
    / "github-pr-comment-reply"
    / "references"
    / "posting-rules.md",
}
FEEDBACK_SKILL_PATH = REPO_ROOT / "github-pr-feedback-address" / "SKILL.md"
IMPLEMENTATION_PATH = (
    REPO_ROOT
    / "herdr-github-pr-orchestrate"
    / "references"
    / "implementation-delegation.md"
)
ISSUE_CREATION_PATH = REPO_ROOT / "herdr-github-create-issue" / "SKILL.md"


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
        cls.posting_rules = {
            name: path.read_text(encoding="utf-8")
            for name, path in POSTING_RULE_PATHS.items()
        }
        cls.apis = {
            name: path.read_text(encoding="utf-8")
            for name, path in API_PATHS.items()
        }
        cls.feedback_skill = FEEDBACK_SKILL_PATH.read_text(encoding="utf-8")
        cls.implementation = IMPLEMENTATION_PATH.read_text(encoding="utf-8")
        cls.issue_creation = ISSUE_CREATION_PATH.read_text(encoding="utf-8")

    def test_runtime_model_precedes_codex_config_fallback(self):
        priority = re.search(
            r"## モデル取得優先順位\n(?P<body>.*?)\n## Effort取得優先順位",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(priority)
        body = priority.group("body")

        self.assertLess(
            body.index("現在のAgentセッション"), body.index("Herdr/cagent")
        )
        self.assertLess(
            body.index("Herdr/cagent"), body.index("~/.codex/config.toml")
        )
        self.assertIn("1と2の実行モデルを取得できないCodexに限り", body)
        self.assertIn("モデル名を推測しない", body)

    def test_explicit_session_product_type_wins_over_hierarchical_path(self):
        agent_name = re.search(
            r"## Agent名\n(?P<body>.*?)\n## モデル取得優先順位",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(agent_name)
        body = agent_name.group("body")

        self.assertLess(
            body.index("現在セッションが明示する製品Agent種別"),
            body.index("pane.agent"),
        )
        self.assertIn("現在セッションがCodexで `/root` も見える場合は `Codex`", body)

    def test_agent_name_rejects_hierarchical_pane_and_role_identifiers(self):
        agent_name = re.search(
            r"## Agent名\n(?P<body>.*?)\n## モデル取得優先順位",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(agent_name)
        body = agent_name.group("body")

        for forbidden in (
            "`/root`",
            "`/root/...`",
            "pane ID",
            "pane label",
            "session ID",
            "役割名",
            "任意のcagent agent ID",
        ):
            self.assertIn(forbidden, body)

    def test_herdr_runtime_values_are_checked_before_config_fallback(self):
        runtime = re.search(
            r"## Herdrでの現在実行値\n(?P<body>.*?)\n## モデル取得優先順位",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(runtime)
        body = runtime.group("body")

        self.assertIn("`HERDR_ENV=1`と空でない`HERDR_PANE_ID`を確認", body)
        self.assertIn("`herdr pane current --current`", body)
        self.assertIn('`herdr pane process-info --pane "$HERDR_PANE_ID"`', body)
        self.assertIn("必ず実行", body)
        self.assertIn("コマンドを試さずにHerdr実行値を取得不能と判定しない", body)
        self.assertIn("Codex Configへフォールバックする前", body)
        self.assertIn("現在Agentプロセスの`--model`", body)
        self.assertIn("`-c model_reasoning_effort=...`", body)
        self.assertIn("別pane、親子の別Agent、shell、過去プロセスの値を混ぜない", body)
        self.assertIn("タスクlevel名やConfigの既定値だけから実行値を推測しない", body)

    def test_agent_name_uses_the_three_canonical_product_mappings(self):
        for source, display_name in (
            ("`codex`", "`Codex`"),
            ("`claude`", "`Claude Code`"),
            ("`opencode`", "`OpenCode`"),
        ):
            self.assertIn(f"{source} → {display_name}", self.skill)

    def test_unknown_agent_name_leaves_comment_identifier_empty(self):
        self.assertIn("すべて取得不能ならAgent名不明", self.skill)
        self.assertIn("信頼できる製品Agent種別を取得できなければ", self.skill)
        self.assertIn("Agent名も取得できなければ", self.skill)
        self.assertIn("識別子は空文字列", self.skill)

    def test_effort_has_the_same_runtime_first_codex_only_fallback(self):
        priority = re.search(
            r"## Effort取得優先順位\n(?P<body>.*?)\n## 取得タイミングと所有者",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(priority)
        body = priority.group("body")

        self.assertLess(body.index("現在セッション"), body.index("Herdr/cagent"))
        self.assertLess(
            body.index("Herdr/cagent"), body.index("model_reasoning_effort")
        )
        self.assertLess(
            body.index("model_reasoning_effort"), body.index("すべて取得不能")
        )
        self.assertIn("通常Codexに限り", body)
        self.assertIn("非Codex AgentへCodex Configを流用しない", body)
        self.assertIn("すべて取得不能なら `—`", body)

    def test_codex_config_and_non_codex_fallback_examples_are_explicit(self):
        self.assertIn("Configの`model_reasoning_effort`が`high`なら `high`", self.skill)
        self.assertIn("非Codex Agentで実行Effortを取得できなければ", self.skill)
        self.assertIn("Codex Configを読まず `—`", self.skill)

    def test_comment_identifier_always_has_three_cells_when_agent_exists(self):
        output = re.search(
            r"## 出力\n(?P<body>.*?)\n## 契約例", self.skill, flags=re.DOTALL
        )
        self.assertIsNotNone(output)
        body = output.group("body")

        self.assertIn("（<agent> / <model-or-—> / <effort-or-—>）", body)
        self.assertIn("ModelまたはEffortが不明なら、そのセルだけ `—`", body)
        self.assertIn("Agent名も取得できなければ", body)
        self.assertIn("識別子は空文字列", body)

    def test_pr_work_metadata_uses_the_shared_three_field_contract(self):
        metadata = re.search(
            r"## PR Work Metadata との整合\n(?P<body>.*?)\n## 出力",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(metadata)
        body = metadata.group("body")

        self.assertIn("Agent / Model / Effort", body)
        self.assertIn("ModelまたはEffortの優先順位を再定義しない", body)
        self.assertIn("ModelまたはEffortを補完しない", body)
        self.assertIn("依頼送信の直前に現在値を再取得して固定", body)

    def test_openai_metadata_describes_three_fields(self):
        self.assertIn('display_name: "AI Identity Resolve"', self.openai_yaml)
        self.assertIn("実行モデル・Effort優先", self.openai_yaml)
        self.assertIn("current Agent, Model, and Effort", self.openai_yaml)

    def test_posting_skills_resolve_identity_immediately_before_posting(self):
        for name, skill in self.posting_skills.items():
            with self.subTest(skill=name):
                self.assertIn("`ai-identity-resolve`", skill)
                self.assertIn("API へ渡す直前", skill)
                self.assertIn("必ず", skill)

    def test_posting_rules_and_api_examples_use_three_field_identifier(self):
        identifier = "（<agent> / <model-or-—> / <effort-or-—>）"
        for name, rules in self.posting_rules.items():
            with self.subTest(rules=name):
                self.assertIn(identifier, rules)
                self.assertIn("Agent名を取得できない場合は空文字列", rules)
        for name, api in self.apis.items():
            with self.subTest(api=name):
                self.assertIn("<effort-or-—>", api)

    def test_feedback_handoff_leaves_identity_to_posting_skill(self):
        self.assertIn("`github-pr-comment-reply`", self.feedback_skill)
        self.assertIn("`ai-identity-resolve`", self.feedback_skill)
        self.assertIn("AI識別値は引き渡さない", self.feedback_skill)
        self.assertIn("投稿直前", self.feedback_skill)

    def test_consumers_do_not_redefine_the_effort_contract(self):
        consumers = [
            *self.posting_skills.values(),
            self.feedback_skill,
            self.implementation,
            self.issue_creation,
        ]
        for consumer in consumers:
            self.assertNotIn("model_reasoning_effort", consumer)
            self.assertNotIn("~/.codex/config.toml", consumer)
        self.assertIn("Agent / Model / Effort は `ai-identity-resolve` の標準契約", self.implementation)
        self.assertIn("ModelまたはEffortの優先順位はこの文書に再定義しない", self.implementation)
        self.assertIn("Agent / Model / Effort標準契約", self.issue_creation)


if __name__ == "__main__":
    unittest.main()
