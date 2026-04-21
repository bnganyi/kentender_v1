#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

# Conservative guard:
# blocks obvious manual scaffold creation attempts for new Frappe apps/DocTypes.
# Exit code 0 = allow
# Exit code 2 = block (recommended for policy-style hooks)

REPO = Path("/home/midasuser/frappe-bench/apps/kentender_v1").resolve()

# Heuristics: if a new app root is being created manually without pyproject.toml
# or if a doctype scaffold appears to be hand-created before framework generation,
# block and force command-first behavior.

APP_NAMES = {
    "kentender_core",
    "kentender_strategy",
    "kentender_budget",
    "kentender_procurement",
    "kentender_suppliers",
    "kentender_governance",
    "kentender_compliance",
    "kentender_stores",
    "kentender_assets",
    "kentender_integrations",
    "kentender_transparency",
}

def app_root(app: str) -> Path:
    return REPO / app

def looks_like_partial_manual_app(root: Path) -> bool:
    if not root.exists():
        return False
    inner = root / root.name
    has_some = any([
        (root / "modules.txt").exists(),
        (inner / "hooks.py").exists(),
        (inner / "__init__.py").exists(),
        inner.exists(),
    ])
    has_required = (root / "pyproject.toml").exists() and inner.exists()
    return has_some and not has_required

def looks_like_manual_doctype_scaffold(root: Path) -> bool:
    for p in root.rglob("doctype"):
        if not p.is_dir():
            continue
        for child in p.rglob("*"):
            if child.is_file() and child.suffix in {".json", ".py"}:
                # crude signal: doctype files exist while app root is not fully scaffolded
                if not (root / "pyproject.toml").exists():
                    return True
    return False

problems: list[str] = []

for app in APP_NAMES:
    root = app_root(app)
    if looks_like_partial_manual_app(root):
        problems.append(
            f"{app}: partial manual app scaffold detected. Use `bench new-app {app}` first."
        )
    if looks_like_manual_doctype_scaffold(root):
        problems.append(
            f"{app}: possible manual DocType scaffold detected before framework generation."
        )

if problems:
    sys.stderr.write(
        "Blocked by KenTender Frappe scaffold guard.\n"
        "Framework-managed artifacts must be generated first.\n\n"
        + "\n".join(problems)
        + "\n"
    )
    sys.exit(2)

sys.exit(0)