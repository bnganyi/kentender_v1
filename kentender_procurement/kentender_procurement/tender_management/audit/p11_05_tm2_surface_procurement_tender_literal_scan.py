# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P11-05 / R01 — TM2 surface must not reference the legacy ``Procurement Tender`` DocType string.

**Full removal** of ``procurement_tender`` desk JS, WH-* tests on PT, and legacy PT-only
controllers remains gated on the DocType drop.

This gate extends P11-04: any **quoted** ``"Procurement Tender"`` / ``'Procurement Tender'``
in TM2-first Python + v2 desk JS is forbidden (covers ``get_all``, ``delete_doc``,
RPC doctype args, etc., not only ``get_doc`` / ``new_doc``).

Excluded by design: ``procurement_tender.js`` (legacy form must register on
``Procurement Tender``), WH services,
and PT DocType controllers under ``kentender_procurement/doctype/procurement_tender/``.
"""

from __future__ import annotations

import re
from pathlib import Path

from kentender_procurement.tender_management.audit.p11_04_tm2_surface_procurement_tender_scan import (
	tm2_surface_guard_js_paths,
	tm2_surface_guard_python_paths,
)

_PT_QUOTED = re.compile(r"""["']Procurement Tender["']""")


def _display_root() -> Path:
	return Path(__file__).resolve().parent.parent.parent


def run_p11_05_tm2_surface_procurement_tender_literal_scan() -> list[tuple[str, str]]:
	"""Return violations ``(relative_path, matched_snippet)``; empty means pass."""
	base = _display_root()
	violations: list[tuple[str, str]] = []
	for path in tm2_surface_guard_python_paths() + tm2_surface_guard_js_paths():
		try:
			text = path.read_text(encoding="utf-8", errors="replace")
		except OSError:
			continue
		for m in _PT_QUOTED.finditer(text):
			rel = path.relative_to(base).as_posix()
			snip = (m.group(0) or "").strip()
			violations.append((rel, snip))
	return violations


def format_p11_05_violations(violations: list[tuple[str, str]]) -> str:
	if not violations:
		return ""
	lines = [f"{path}: forbidden legacy doctype literal {snippet!r}" for path, snippet in violations]
	return "\n".join(lines)
