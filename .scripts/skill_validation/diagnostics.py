"""Stable diagnostics shared by all validation phases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Diagnostic:
    level: str
    check_id: str
    path: str
    line: int
    message: str

    def format(self) -> str:
        return f"{self.level} [{self.check_id}] {self.path}:{self.line}: {self.message}"


@dataclass(frozen=True)
class Suppression:
    check_id: str
    targets: tuple[str, ...]
    reason: str


class Diagnostics:
    """Collect diagnostics and render them deterministically at the boundary."""

    def __init__(self, root: Path):
        self.root = root
        self.items: list[Diagnostic] = []
        self.suppressions: tuple[Suppression, ...] = ()

    def configure_suppressions(self, suppressions: list[Suppression]) -> None:
        self.suppressions = tuple(suppressions)

    def add(self, level: str, check_id: str, path: Path | str, line: int, message: str) -> None:
        if isinstance(path, Path):
            try:
                path = path.relative_to(self.root).as_posix()
            except ValueError:
                path = path.as_posix()
        path = str(path)
        suppression = next(
            (
                item
                for item in self.suppressions
                if item.check_id == check_id
                and any(path == target or path.startswith(target.rstrip("/") + "/") for target in item.targets)
            ),
            None,
        )
        if suppression is not None:
            message = f"suppressed by configured exception ({suppression.reason}); original: {message}"
            level = "WARNING"
        self.items.append(Diagnostic(level, check_id, path, max(1, line), message))

    def error(self, check_id: str, path: Path | str, line: int, message: str) -> None:
        self.add("ERROR", check_id, path, line, message)

    def warning(self, check_id: str, path: Path | str, line: int, message: str) -> None:
        self.add("WARNING", check_id, path, line, message)

    def sorted(self) -> list[Diagnostic]:
        return sorted(self.items, key=lambda d: (d.path, d.line, d.check_id, d.level, d.message))

    @property
    def has_errors(self) -> bool:
        return any(item.level == "ERROR" for item in self.items)
