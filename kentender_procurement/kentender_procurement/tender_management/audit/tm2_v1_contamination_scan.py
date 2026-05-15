# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-03 / doc 1 §28 — static scan for v1 rule-injection keys in TM2-facing surfaces.

Scans ``tender_management/`` (Python + JS) and TM2 desk shell JS under the inner
``kentender_procurement`` package for occurrences of the five WORKS-LEGACY
configuration flags (same identifiers as :data:`LEGACY_RULE_INJECTION_KEYS`).

Allowlisted paths may retain these strings for enforcement or regression tests
(including ``tests/scenarios/test_tm2_works_s13.py`` for doc 7 **S-13** / **P12-01** and
``tests/test_ex_04_cannot_define_std_rules_inside_tm2_tender.py`` for doc 9 §25 **EX-04**).
Run from tests via :func:`run_tm2_v1_contamination_scan` or ``make tm2-v1-contamination-audit``.
"""

from __future__ import annotations

from pathlib import Path

from kentender_procurement.tender_management.security.legacy_v1_path_guard import (
	LEGACY_RULE_INJECTION_KEYS,
)

_TEXT_SUFFIXES: frozenset[str] = frozenset(
	{".py", ".js", ".ts", ".tsx", ".html", ".vue", ".json", ".md"}
)

_ALLOWLIST_TENDER_MANAGEMENT_RELPATHS: frozenset[str] = frozenset(
	{
		"security/legacy_v1_path_guard.py",
		"services/works_tender_hardening_validation_checks.py",
		"tests/test_p11_01_legacy_path_guard.py",
		"tests/scenarios/test_tm2_works_s13.py",
		"tests/test_ex_04_cannot_define_std_rules_inside_tm2_tender.py",
	}
)

_SKIP_DIR_NAMES: frozenset[str] = frozenset(
	{"__pycache__", ".git", "node_modules", ".pytest_cache", "dist"}
)


def _tender_management_root() -> Path:
	return Path(__file__).resolve().parent.parent


def _inner_procurement_package_root() -> Path:
	"""``.../kentender_procurement/kentender_procurement`` (parent of ``tender_management``)."""
	return _tender_management_root().parent


def _extra_tm2_surface_files() -> tuple[Path, ...]:
	base = _inner_procurement_package_root()
	paths = (
		base / "public/js/tender_management_v2_workbench_page.js",
		base / "kentender_procurement/doctype/tm2_tender/tm2_tender.js",
	)
	return tuple(p for p in paths if p.is_file())


def _path_parts_skip(path: Path) -> bool:
	return any(p in _SKIP_DIR_NAMES for p in path.parts)


def _scan_tree(root: Path, *, allowlist_relpaths: frozenset[str] | None) -> list[tuple[str, str]]:
	violations: list[tuple[str, str]] = []
	if not root.is_dir():
		return violations
	for path in root.rglob("*"):
		if not path.is_file():
			continue
		if _path_parts_skip(path):
			continue
		if path.suffix.lower() not in _TEXT_SUFFIXES:
			continue
		try:
			rel = path.relative_to(root).as_posix()
		except ValueError:
			rel = path.as_posix()
		if allowlist_relpaths is not None and rel in allowlist_relpaths:
			continue
		try:
			raw = path.read_text(encoding="utf-8", errors="replace")
		except OSError:
			continue
		for key in LEGACY_RULE_INJECTION_KEYS:
			if key in raw:
				violations.append((rel, key))
	return violations


def run_tm2_v1_contamination_scan() -> list[tuple[str, str]]:
	"""Run P11-03 static audit; empty list means pass."""
	tm_root = _tender_management_root()
	out = _scan_tree(tm_root, allowlist_relpaths=_ALLOWLIST_TENDER_MANAGEMENT_RELPATHS)
	for extra in _extra_tm2_surface_files():
		try:
			raw = extra.read_text(encoding="utf-8", errors="replace")
		except OSError:
			continue
		pkg_app = _inner_procurement_package_root().parent
		display = extra.relative_to(pkg_app).as_posix()
		for key in LEGACY_RULE_INJECTION_KEYS:
			if key in raw:
				out.append((display, key))
	return out


def format_violations(violations: list[tuple[str, str]]) -> str:
	if not violations:
		return ""
	lines = [f"{path}: forbidden legacy key {key!r}" for path, key in violations]
	return "\n".join(lines)
