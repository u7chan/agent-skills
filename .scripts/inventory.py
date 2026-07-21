#!/usr/bin/env python3
"""Phase 1: 全スキルの棚卸し — 配布対象 + .claude/skills/ 保守専用スキルを走査し、
責務・参照関係・外部依存・本文量・重複候補を YAML として inventory/ に出力する。"""

import os
import re
import sys
import yaml
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "inventory"

# ── スコープ定義 ──────────────────────────────────────────
EXCLUDE_DIRS = {".git", ".archive", ".codex", ".system", ".github", ".agents",
                "node_modules", "inventory", "__pycache__"}
MAINTENANCE_PREFIX = ".claude/skills"

# ── 外部依存の種別・分類 ──────────────────────────────────
DEP_TYPES = ("required", "conditional", "optional", "fallback")

# 既知の外部依存キーワード（README の External Dependencies 列から推測用）
KNOWN_EXTERNAL = {
    "gh": "required",
    "jq": "conditional",
    "git": "required",
    "bun": "required",
    "npm": "required",
    "node": "required",
    "npx": "fallback",
    "uv": "required",
    "python": "required",
    "rg": "required",
    "playwright": "required",
    "herdr": "required",
    "cagent": "required",
    "librsvg": "optional",
    "inkscape": "optional",
    "browser": "required",
    "tailwind": "required",
    "coreutils": "required",
    "posix": "required",
    "github": "required",
    "github api": "required",
    "web access": "conditional",
    "agent cli": "required",
    "selected agent cli": "required",
}


def find_skill_files() -> list[Path]:
    """スコープ内の全 SKILL.md を返す。"""
    skills = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if "SKILL.md" in files:
            rel = Path(root).relative_to(REPO_ROOT)
            if str(rel) != ".":
                skills.append(rel / "SKILL.md")
    return sorted(skills)


def classify_skill(rel_path: Path) -> str:
    """distributable か maintenance かを返す。"""
    s = str(rel_path)
    if s.startswith(MAINTENANCE_PREFIX):
        return "maintenance"
    return "distributable"


def parse_frontmatter(content: str) -> dict:
    """YAML frontmatter を抜き出す。"""
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return {}
    try:
        return yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def extract_responsibility(skill_name: str, frontmatter: dict) -> str:
    """責務を1文で返す。description の先頭文を優先。"""
    desc = frontmatter.get("description", "")
    if desc:
        # 最初の文または改行まで
        desc = desc.strip()
        # YAML の > で折りたたまれている場合、改行は空白になる
        first_sentence = re.split(r"[.。]", desc.replace("\n", " "))[0].strip()
        if first_sentence:
            return first_sentence
    return f"unknown: {skill_name}"


def count_lines(filepath: Path) -> int:
    """ファイル行数。"""
    with open(filepath) as f:
        return sum(1 for _ in f)


def check_subdirs(skill_dir: Path) -> dict:
    """references/ scripts/ の有無を返す。"""
    result = {}
    for sub in ("references", "scripts", "tests", "evaluation-samples"):
        p = skill_dir / sub
        if p.is_dir():
            result[sub] = True
    return result


def extract_skill_references(content: str, all_skill_names: set[str]) -> list[str]:
    """本文中の他スキル参照を抽出する。
    - バッククォート内のスキル名
    - ../skill-name/ 形式の相対パス参照
    - 自然言語での `skill-name` 言及（agents/openai.yaml など）
    """
    refs = set()

    # バッククォートで囲まれたスキル名
    backtick_refs = re.findall(r"`([a-z]+-[a-z]+-[a-z]+(?:-[a-z]+)*)`", content)
    for ref in backtick_refs:
        if ref in all_skill_names:
            refs.add(ref)

    # 相対パス: ../skill-name/SKILL.md または ../skill-name/
    path_refs = re.findall(r"\.\./?(?:[a-z]+-(?:[a-z]+-)*[a-z]+)", content)
    for ref in path_refs:
        clean = ref.lstrip("./")
        # ファイル名やディレクトリを取り出す
        parts = clean.split("/")
        for part in parts:
            if part in all_skill_names:
                refs.add(part)
            # サブパス: references/agent-cli.md → スキル名に変換
            if part in ("SKILL.md", "references", "scripts"):
                continue

    # プレーンなスキル名言及（バッククォート外、より幅広なパターン）
    # 命名パターン: service-target-action
    # 注意: 長い名前を先にチェックし、部分文字列一致を避ける（word boundary 必須）
    for name in sorted(all_skill_names, key=len, reverse=True):
        # 単語境界でマッチ（バッククォート内、空白・改行・句読点で区切られた出現）
        pattern = r'(?<![a-z-])' + re.escape(name) + r'(?![a-z-])'
        if re.search(pattern, content):
            refs.add(name)

    # 自分自身を除く
    return sorted(refs)


def extract_path_references(content: str) -> list[str]:
    """物理パス参照 (../) を抽出する。"""
    refs = set()
    # ../ で始まるパターン
    matches = re.findall(r"\.\./[^\s`)]+", content)
    for m in matches:
        # クリーンアップ
        clean = m.rstrip(".,;:")
        refs.add(clean)
    return sorted(refs)


def extract_external_deps(skill_name: str, content: str, readme_deps: dict) -> list[dict]:
    """外部依存を抽出。README の External Dependencies 列を優先し、SKILL.md から補完。"""
    deps = []
    seen = set()

    # README からの依存（優先）
    if skill_name in readme_deps:
        for dep_str, dep_type in readme_deps[skill_name]:
            name = dep_str.strip().lower()
            if name and name not in seen:
                deps.append({"name": name, "type": dep_type, "source": "README"})
                seen.add(name)

    # SKILL.md から補完
    # `command -v <cmd>` パターン
    cmd_refs = re.findall(r"`command -v (\w+)`", content)
    for cmd in cmd_refs:
        if cmd.lower() not in seen:
            dep_type = KNOWN_EXTERNAL.get(cmd.lower(), "required")
            deps.append({"name": cmd.lower(), "type": dep_type, "source": "SKILL.md (command -v)"})
            seen.add(cmd.lower())

    # `which <cmd>` パターン
    which_refs = re.findall(r"`which (\w+)`", content)
    for cmd in which_refs:
        if cmd.lower() not in seen:
            deps.append({"name": cmd.lower(), "type": "required", "source": "SKILL.md (which)"})
            seen.add(cmd.lower())

    # スクリプト参照: scripts/xxx や import 文 (コードブロックに限定、マルチバイト文字を除外)
    # コードブロック内の import/from 文
    for code in re.findall(r"```(?:py|python|bash|sh)?\n(.*?)```", content, re.DOTALL):
        for imp in re.findall(r"(?:^|\n)(?:from|import)\s+([a-zA-Z_]\w+)", code):
            if imp.lower() in ("os", "sys", "json", "re", "yaml", "pathlib", "subprocess", "shutil", "typing", "io"):
                continue
            if imp.lower() not in seen:
                deps.append({"name": imp.lower(), "type": "required", "source": "SKILL.md (code-import)"})
                seen.add(imp.lower())

    return deps


def parse_readme_deps() -> dict[str, list[tuple[str, str]]]:
    """README.md の Available Skills テーブルから外部依存を取得する。"""
    readme_path = REPO_ROOT / "README.md"
    if not readme_path.exists():
        return {}

    with open(readme_path) as f:
        content = f.read()

    deps = {}
    # | [skill-name](path/SKILL.md) | description | dependencies |
    for m in re.finditer(
        r"\[([^\]]+)\]\(([^)]+/SKILL\.md)\)\s*\|[^|]*\|(.+?)\|",
        content
    ):
        name = m.group(1)
        dep_text = m.group(3).strip()

        if dep_text in ("—", "—", ""):
            continue

        dep_list = []
        # カンマ区切り、(conditional) など
        for part in re.split(r",\s*", dep_text):
            part = part.strip()
            dep_type = "required"
            for dt in DEP_TYPES:
                if f"({dt})" in part:
                    dep_type = dt
                    part = part.replace(f"({dt})", "").strip()
            # バッククォート除去
            part = part.strip("`").strip()
            if part and part != "\u2014" and part != "—":
                dep_list.append((part, dep_type))
        deps[name] = dep_list

    return deps


def build_dependency_graph(skills_meta: list[dict]) -> dict:
    """依存グラフを構築し、循環参照・逆方向依存・物理パス参照を検出する。"""
    graph = {
        "nodes": [],
        "edges": [],
        "cycles": [],
        "reverse_dependencies": [],
        "physical_path_refs": [],
    }

    # スキル名→メタデータ のマップ
    name_to_skill = {}
    # スキル名→配置（ディレクトリ）
    name_to_path = {}

    for s in skills_meta:
        name = s["name"]
        node = {
            "name": name,
            "current_path": s["current_path"],
            "classification": s["classification"],
            "line_count": s["line_count"],
        }
        graph["nodes"].append(node)
        name_to_skill[name] = s
        name_to_path[name] = Path(s["current_path"]).parent

    # 依存エッジ
    for s in skills_meta:
        from_name = s["name"]
        from_path = name_to_path[from_name]
        for ref_name in s["skill_references"]:
            if ref_name in name_to_skill:
                edge = {
                    "from": from_name,
                    "to": ref_name,
                    "from_classification": s["classification"],
                    "to_classification": name_to_skill[ref_name]["classification"],
                }
                graph["edges"].append(edge)

    # 循環参照の検出（DFS）
    adj = {}
    for edge in graph["edges"]:
        from_node = edge["from"]
        to_node = edge["to"]
        if from_node not in adj:
            adj[from_node] = set()
        adj[from_node].add(to_node)
        # to_node もキーとして登録（参照されないノードのため）
        if to_node not in adj:
            adj[to_node] = set()

    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in adj.get(node, set()):
            if neighbor not in visited:
                cycle = dfs(neighbor, path + [node])
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # パス上に neighbor がいる → 循環
                if neighbor in path:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [node, neighbor]
        rec_stack.discard(node)
        return None

    for node in list(adj.keys()):
        if node not in visited:
            cycle = dfs(node, [])
            if cycle:
                graph["cycles"].append(cycle)

    # 逆方向依存の候補（レイヤーをまたぐ依存）
    # 仮のレイヤー: Skill → Workflow → Agent → Herdr のような順序
    layer_order = {
        "": 0,
    }
    # 命名 prefix でレイヤーを推測
    for s in skills_meta:
        name = s["name"]
        parts = name.split("-")
        if len(parts) >= 1:
            prefix = parts[0]
            if prefix not in layer_order:
                layer_order[prefix] = len(layer_order)

    for edge in graph["edges"]:
        from_prefix = edge["from"].split("-")[0]
        to_prefix = edge["to"].split("-")[0]
        from_layer = layer_order.get(from_prefix, 0)
        to_layer = layer_order.get(to_prefix, 0)
        # 下位レイヤーから上位レイヤーへの依存
        if from_layer > to_layer and from_prefix != to_prefix:
            graph["reverse_dependencies"].append({
                "from": edge["from"],
                "to": edge["to"],
                "reason": f"{from_prefix} → {to_prefix} (lower to higher layer)",
            })

    # 物理パス参照の収集
    for s in skills_meta:
        for path_ref in s.get("path_references", []):
            graph["physical_path_refs"].append({
                "skill": s["name"],
                "path": path_ref,
            })

    return graph


def analyze_findings(skills_meta: list[dict]) -> list[dict]:
    """自動検出可能な所見（肥大化・行数超過）だけを返す。重複責務は人手判断に任せる。"""
    findings = []

    # 肥大化候補（SKILL.md が180行超、または150行超）
    for s in skills_meta:
        if s["line_count"] > 180:
            findings.append({
                "type": "oversize",
                "skill": s["name"],
                "line_count": s["line_count"],
                "reason": f"exceeds 180-line limit ({s['line_count']})",
                "recommendation": "split or shorten",
                "auto_detected": True,
            })
        elif s["line_count"] > 150:
            findings.append({
                "type": "near_limit",
                "skill": s["name"],
                "line_count": s["line_count"],
                "reason": f"approaches 180-line limit ({s['line_count']})",
                "recommendation": "monitor, consider reducing",
                "auto_detected": True,
            })

    return findings


def main():
    print(f"Scanning {REPO_ROOT} ...")

    # 全スキル発見
    skill_files = find_skill_files()
    print(f"Found {len(skill_files)} SKILL.md files (distributable + maintenance)")

    # README から外部依存を取得
    readme_deps = parse_readme_deps()

    # 全スキル名を収集（依存抽出用）
    all_skill_names = set()
    for sf in skill_files:
        with open(REPO_ROOT / sf) as f:
            content = f.read()
        fm = parse_frontmatter(content)
        name = fm.get("name", "")
        if name:
            all_skill_names.add(name)

    # 各スキルのメタデータを収集
    skills_meta = []
    for sf in skill_files:
        full_path = REPO_ROOT / sf
        rel_path = str(sf)
        skill_dir = full_path.parent

        with open(full_path) as f:
            content = f.read()

        fm = parse_frontmatter(content)
        name = fm.get("name", "")
        if not name:
            name = skill_dir.name

        classification = classify_skill(sf)
        responsibility = extract_responsibility(name, fm)
        line_count = count_lines(full_path)
        subdirs = check_subdirs(skill_dir)
        skill_refs = extract_skill_references(content, all_skill_names)
        # 自分自身を除外
        skill_refs = [r for r in skill_refs if r != name]
        path_refs = extract_path_references(content)
        ext_deps = extract_external_deps(name, content, readme_deps)

        meta = {
            "name": name,
            "current_path": str(skill_dir.relative_to(REPO_ROOT)),
            "classification": classification,
            "responsibility": responsibility,
            "description": fm.get("description", ""),
            "line_count": line_count,
            "has_references": subdirs.get("references", False),
            "has_scripts": subdirs.get("scripts", False),
            "has_tests": subdirs.get("tests", False),
            "has_evaluation_samples": subdirs.get("evaluation-samples", False),
            "skill_references": skill_refs,
            "path_references": path_refs,
            "external_dependencies": ext_deps,
            "disposition": "keep",  # 後続 Phase で判断
            "findings": [],
        }
        skills_meta.append(meta)

    # 依存グラフ構築
    dep_graph = build_dependency_graph(skills_meta)

    # 所見の分析
    findings = analyze_findings(skills_meta)

    # 人手判断による追加所見を追記
    manual_findings = add_manual_findings(skills_meta)
    findings.extend(manual_findings)

    # 出力ディレクトリ作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # スキルメタデータ出力
    skills_yaml = {
        "generated_by": ".scripts/inventory.py",
        "scope": "distributable + .claude/skills/ (maintenance-only)",
        "total_count": len(skills_meta),
        "distributable_count": sum(1 for s in skills_meta if s["classification"] == "distributable"),
        "maintenance_count": sum(1 for s in skills_meta if s["classification"] == "maintenance"),
        "skills": skills_meta,
    }

    with open(OUTPUT_DIR / "skills.yaml", "w") as f:
        yaml.dump(skills_yaml, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"Wrote {OUTPUT_DIR / 'skills.yaml'}")

    # 依存グラフ出力
    with open(OUTPUT_DIR / "dependency-graph.yaml", "w") as f:
        yaml.dump(dep_graph, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"Wrote {OUTPUT_DIR / 'dependency-graph.yaml'}")

    # 所見出力
    findings_yaml = {
        "generated_by": ".scripts/inventory.py",
        "total_findings": len(findings),
        "auto_detected": sum(1 for f in findings if f.get("auto_detected")),
        "manual": sum(1 for f in findings if not f.get("auto_detected")),
        "findings": findings,
    }
    with open(OUTPUT_DIR / "findings.yaml", "w") as f:
        yaml.dump(findings_yaml, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"Wrote {OUTPUT_DIR / 'findings.yaml'}")

    # サマリ出力
    summary = {
        "generated_by": ".scripts/inventory.py",
        "scope": "distributable + .claude/skills/ (maintenance-only)",
        "total_skills": len(skills_meta),
        "distributable": sum(1 for s in skills_meta if s["classification"] == "distributable"),
        "maintenance": sum(1 for s in skills_meta if s["classification"] == "maintenance"),
        "total_dependency_edges": len(dep_graph["edges"]),
        "cycles_found": len(dep_graph["cycles"]),
        "reverse_dependencies_found": len(dep_graph["reverse_dependencies"]),
        "physical_path_refs_found": len(dep_graph["physical_path_refs"]),
        "total_findings": len(findings),
        "oversize_skills": sum(1 for f in findings if f.get("type") == "oversize"),
        "near_limit_skills": sum(1 for f in findings if f.get("type") == "near_limit"),
        "duplication_candidates": sum(1 for f in findings if f.get("type") == "duplication_candidate"),
    }
    with open(OUTPUT_DIR / "summary.yaml", "w") as f:
        yaml.dump(summary, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"Wrote {OUTPUT_DIR / 'summary.yaml'}")

    print("\n=== Summary ===")
    for k, v in summary.items():
        if k != "generated_by" and k != "scope":
            print(f"  {k}: {v}")


def add_manual_findings(skills_meta: list[dict]) -> list[dict]:
    """人手判断による所見を追加する。"""
    name_map = {s["name"]: s for s in skills_meta}
    findings = []

    # ── 重複責務候補 ──
    # git-worktree-create / herdr-worktree-create
    gwt = name_map.get("git-worktree-create")
    hwt = name_map.get("herdr-worktree-create")
    if gwt and hwt:
        findings.append({
            "type": "duplication_candidate",
            "skills": [gwt["name"], hwt["name"]],
            "reason": "両者とも独立したworktree作成が責務。git-worktree-create は純粋なgit操作、herdr-worktree-create はHerdrコマンドによる作成。責務が重複しているが、利用コンテキストが異なるため統合には慎重な判断が必要。",
            "auto_detected": False,
            "recommendation": "統合候補。共通のworktree作成ロジックを抽出し、ラッパーとしてgit/herdr版を提供する構成を検討。",
        })

    # grilling / design-plan-grill
    gr = name_map.get("grilling")
    dpg = name_map.get("design-plan-grill")
    if gr and dpg:
        findings.append({
            "type": "duplication_candidate",
            "skills": [gr["name"], dpg["name"]],
            "reason": "grilling は領域非依存の壁打ち、design-plan-grill は設計に特化した壁打ち。責務が重複しており、design-plan-grill は grilling の特殊化。grilling の SKILL.md 内でも design-plan-grill への委譲を指示している。",
            "auto_detected": False,
            "recommendation": "統合候補。design-plan-grill を grilling のサブモードとして統合するか、grilling を design-plan-grill に吸収。",
        })

    # github-pr-orchestrate / herdr-github-pr-orchestrate
    gpo = name_map.get("github-pr-orchestrate")
    hgo = name_map.get("herdr-github-pr-orchestrate")
    if gpo and hgo:
        findings.append({
            "type": "duplication_candidate",
            "skills": [gpo["name"], hgo["name"]],
            "reason": "両者ともPR作成の統括フロー。github-pr-orchestrate は非Herdr環境、herdr-github-pr-orchestrate はHerdr環境向け。herdr版はgithub版の共通スキルを参照している。",
            "auto_detected": False,
            "recommendation": "統合候補。共通フローを抽出し、Herdr/非Herdrの差異だけを切り替え可能にする。",
        })

    # agent-skill-design / agent-skill-refine
    asd = name_map.get("agent-skill-design")
    asr = name_map.get("agent-skill-refine")
    if asd and asr:
        findings.append({
            "type": "duplication_candidate",
            "skills": [asd["name"], asr["name"]],
            "reason": "agent-skill-design は新規作成・要件追加・全面再設計、agent-skill-refine は挙動を変えずに短文化・高密度化。責務は明確に分離されているが、密接に関連しており、参照関係も強い。",
            "auto_detected": False,
            "recommendation": "分割統合は不要。責務境界が明確で適切に分離されている。",
        })

    # ── 肥大化候補 ──
    # herdr-agent-delegate (173行)
    had = name_map.get("herdr-agent-delegate")
    if had and had["line_count"] > 170:
        findings.append({
            "type": "oversize_detail",
            "skill": had["name"],
            "line_count": had["line_count"],
            "reason": "173行。Agent委譲の全工程（プリフライト、宛先解決、pane配置、依頼送信、結果回収）を1ファイルに収めており、責務が大きい。references/ は既に存在するが、SKILL.md 自体の構造を再検討する余地がある。",
            "recommendation": "工程ごとに references/ へ分割し、SKILL.md はルーティングと主要ルールのみに絞る。",
            "auto_detected": False,
        })

    # herdr-github-pr-orchestrate (156行)
    if hgo and hgo["line_count"] > 150:
        findings.append({
            "type": "near_limit_detail",
            "skill": hgo["name"],
            "line_count": hgo["line_count"],
            "reason": "156行。実装委譲からPR作成、レビュー、FB対応までの全工程をカバーしており、工程ごとの分岐条件も多い。references/ に実装委譲とレビューループの詳細は分離済み。",
            "recommendation": "モニタリング。180行を超える前に工程分岐の一部を references/ に移すことを検討。",
            "auto_detected": False,
        })

    # ── 分割候補 ──
    # cagent-agent-command-resolve (103行、scripts/ あり)
    car = name_map.get("cagent-agent-command-resolve")
    if car and car.get("has_scripts"):
        findings.append({
            "type": "complexity",
            "skill": car["name"],
            "reason": "cagent の解決ロジックと Agent Command の生成を1スキルで扱っている。scripts/ に実装があり、SKILL.md はそれらの使い方を説明する構成。責務は明確だが、cagent 自体のバージョンアップに追従が必要。",
            "recommendation": "現状維持。scripts/ への分離は適切に行われている。",
            "auto_detected": False,
        })

    # ── 外部依存の確認 ──
    # 共通: Git, POSIX shell が大半のスキルで required
    deps_summary = {}
    for s in skills_meta:
        for dep in s.get("external_dependencies", []):
            key = (dep["name"], dep["type"])
            deps_summary[key] = deps_summary.get(key, 0) + 1

    # 全スキルで必須の依存を報告
    for (name, dtype), count in sorted(deps_summary.items(), key=lambda x: -x[1]):
        if count >= len(skills_meta) * 0.5:  # 50%以上のスキルが依存
            findings.append({
                "type": "common_dependency",
                "dependency": name,
                "type_class": dtype,
                "usage_count": count,
                "reason": f"全スキルの {count}/{len(skills_meta)} が依存。共通依存として暗黙的に扱うことを検討。",
                "auto_detected": False,
            })

    return findings


if __name__ == "__main__":
    main()
