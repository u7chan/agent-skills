# uv 依存チェック詳細

## pyproject.toml の確認

Read `pyproject.toml` and identify:

- the dependency location: `project.dependencies`, optional dependencies, or `[dependency-groups]`
- whether the package is runtime or development-only
- the available validation commands

Inspect package usage with `rg` before changing a dependency that may affect code behavior.

## uv プロジェクトの下限指定とメジャーアップグレード

Do not assume that the current declared requirement prevents a major bump.
In uv projects, many dependencies are recorded with only a lower bound such as `pkg>=1.2.3`, which can still allow a new major release.
