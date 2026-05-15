# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0200 — Bundle outline and stable error codes (pack §8)."""

from __future__ import annotations

# Stable ``frappe.throw`` title for generation preconditions / unexpected failures (tracker §4).
BUNDLE_GENERATION_FAILED = "BUNDLE_GENERATION_FAILED"

PLACEHOLDER_PENDING = "placeholder"
PLACEHOLDER_COMPLETE = "complete"

# Pack §8 — full outline: Invitation to Tender + Sections I–X (order is normative).
WORKS_BUNDLE_OUTLINE: tuple[tuple[str, str], ...] = (
	("ITT", "Invitation to Tender"),
	("I", "Section I — Instructions to Tenderers"),
	("II", "Section II — Tender Data Sheet"),
	("III", "Section III — Evaluation and Qualification Criteria"),
	("IV", "Section IV — Tendering Forms"),
	("V", "Section V — Bills of Quantities"),
	("VI", "Section VI — Specifications"),
	("VII", "Section VII — Drawings"),
	("VIII", "Section VIII — General Conditions of Contract"),
	("IX", "Section IX — Special Conditions of Contract"),
	("X", "Section X — Contract Forms"),
)

BUNDLE_SECTION_CODES: tuple[str, ...] = tuple(code for code, _title in WORKS_BUNDLE_OUTLINE)
