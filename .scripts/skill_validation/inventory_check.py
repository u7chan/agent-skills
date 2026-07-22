"""Checked-in inventory freshness validation."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile

from .model import RepositoryModel


INVENTORY_FILES = ("skills.yaml", "dependency-graph.yaml", "findings.yaml", "summary.yaml")


def check(model: RepositoryModel) -> None:
    generator = model.root / ".scripts/inventory.py"
    if not generator.is_file():
        model.diagnostics.error("V-INV-001", generator, 1, "inventory generator is missing")
        return
    with tempfile.TemporaryDirectory(prefix="skill-inventory-") as temporary:
        expected_dir = Path(temporary)
        try:
            process = subprocess.run(
                [sys.executable, str(generator), "--output-dir", str(expected_dir)],
                cwd=model.root,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            model.diagnostics.error("V-INV-001", generator, 1, f"cannot run inventory generator: {exc.strerror or exc}")
            return
        if process.returncode != 0:
            detail = (process.stderr or process.stdout).strip().splitlines()
            message = detail[-1] if detail else f"exit {process.returncode}"
            model.diagnostics.error("V-INV-001", generator, 1, f"inventory generator failed: {message}")
            return
        for name in INVENTORY_FILES:
            checked_in = model.root / "inventory" / name
            expected = expected_dir / name
            if not checked_in.is_file():
                model.diagnostics.error("V-INV-001", checked_in, 1, "checked-in inventory file is missing")
            elif not expected.is_file():
                model.diagnostics.error("V-INV-001", expected, 1, "inventory generator did not produce expected file")
            elif checked_in.read_bytes() != expected.read_bytes():
                model.diagnostics.error("V-INV-001", checked_in, 1, "checked-in inventory is stale; regenerate with python3 .scripts/inventory.py")


def register(register_check, register_graph_renderer) -> None:
    del register_graph_renderer
    register_check(check)
