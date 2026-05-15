# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-04 / R01 — TM2-surface guard: no ``Procurement Tender`` document API in TM2 paths.

**Full DocType removal** (drop ``Procurement Tender`` + PT-only children, migrate data) is
**in progress** alongside STD/publication refactors.
This module enforces the tracker sub-goal: **no** ``frappe.get_doc("Procurement Tender")`` /
``frappe.new_doc("Procurement Tender")`` in TM2-facing Python entrypoints.
:func:`tm2_surface_guard_python_paths` / :func:`tm2_surface_guard_js_paths` are shared with **P11-05**
(quoted ``Procurement Tender`` literal ban on the same Python set plus v2 desk JS).

Scanned trees (relative to ``tender_management/``):

- ``api/tm2_workbench.py``, ``api/supplier_portal.py``
- ``services/tm2_*.py``, ``services/supplier_portal_*.py``
- ``services/release_procurement_package_to_tender.py``, ``services/publish_tender.py``,
  ``services/create_tender_from_package.py``,
  ``services/submit_tender_for_publication_review.py``, ``services/approve_tender_publication.py``,
  ``services/bind_tender_std_instance.py``, ``services/run_publication_readiness.py`` (when present)
- ``services/planning_tender_handoff_*.py`` (package → TM2 release / audit / XMV chain)
- ``std_instance/tm2_publication_readiness_service.py``
"""

from __future__ import annotations

import re
from pathlib import Path

_PT_GET_OR_NEW = re.compile(
	r"frappe\.(get_doc|new_doc)\s*\(\s*[\"']Procurement Tender[\"']",
	re.MULTILINE,
)


def _tender_management_root() -> Path:
	return Path(__file__).resolve().parent.parent


def _tm2_surface_py_files() -> list[Path]:
	tm = _tender_management_root()
	out: list[Path] = []
	for rel in (
		tm / "api" / "tm2_workbench.py",
		tm / "api" / "supplier_portal.py",
	):
		if rel.is_file():
			out.append(rel)
	for folder, pattern in (
		(tm / "services", "tm2_*.py"),
		(tm / "services", "supplier_portal_*.py"),
	):
		if folder.is_dir():
			out.extend(sorted(folder.glob(pattern)))
	for name in (
		"release_procurement_package_to_tender.py",
		"publish_tender.py",
		"create_tender_from_package.py",
		"submit_tender_for_publication_review.py",
		"approve_tender_publication.py",
		"bind_tender_std_instance.py",
		"run_publication_readiness.py",
	):
		p = tm / "services" / name
		if p.is_file():
			out.append(p)
	services_dir = tm / "services"
	if services_dir.is_dir():
		out.extend(sorted(services_dir.glob("planning_tender_handoff_*.py")))
	extra = tm / "std_instance" / "tm2_publication_readiness_service.py"
	if extra.is_file():
		out.append(extra)
	# Stable order, unique
	seen: set[Path] = set()
	uniq: list[Path] = []
	for p in out:
		rp = p.resolve()
		if rp not in seen:
			seen.add(rp)
			uniq.append(rp)
	return sorted(uniq)


def tm2_surface_guard_python_paths() -> list[Path]:
	"""Python modules scanned by P11-04 / P11-05 TM2 surface legacy guards."""
	return _tm2_surface_py_files()


def tm2_surface_guard_js_paths() -> list[Path]:
	"""Desk JS bundles for Tender Management v2 workbench + ``TM2 Tender`` form."""
	base = _tender_management_root().parent
	paths = (
		base / "public/js/tender_management_v2_workbench_page.js",
		base / "kentender_procurement/doctype/tm2_tender/tm2_tender.js",
	)
	return sorted(p.resolve() for p in paths if p.is_file())


def run_p11_04_tm2_surface_procurement_tender_scan() -> list[tuple[str, str]]:
	"""Return violations ``(relative_path, matched_snippet)``; empty means pass."""
	root = _tender_management_root()
	violations: list[tuple[str, str]] = []
	for path in _tm2_surface_py_files():
		try:
			text = path.read_text(encoding="utf-8", errors="replace")
		except OSError:
			continue
		for m in _PT_GET_OR_NEW.finditer(text):
			rel = path.relative_to(root).as_posix()
			snip = (m.group(0) or "").strip().replace("\n", " ")
			if len(snip) > 120:
				snip = snip[:117] + "..."
			violations.append((rel, snip))
	return violations


def format_p11_04_violations(violations: list[tuple[str, str]]) -> str:
	if not violations:
		return ""
	lines = [f"{path}: {snippet}" for path, snippet in violations]
	return "\n".join(lines)
