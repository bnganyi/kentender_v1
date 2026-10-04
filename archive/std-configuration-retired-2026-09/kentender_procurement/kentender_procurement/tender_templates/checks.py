# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-001 v0.5 §11.3 / §15 — release checks that run against rendered
output: unresolved authoring content, the Invitation/issued-Tender boundary,
shared-value consistency, and the internal-only keys TPR-CHG-001 v0.6
TPR-AC-044 forbids in any supplier-visible output."""

from __future__ import annotations

import re
from typing import Any

UNRESOLVED_PATTERNS = (
	r"\{\{", r"\{%", r"\[insert", r"insert here", r"delete if", r"select one", r"\.\.\.", r"Manual Input", r"Auto Populate",
)
INVITATION_HEADING = "<h1>INVITATION TO TENDER</h1>"

# TPR-AC-044 — never rendered to a bidder (internal policy context only).
INTERNAL_ONLY_MARKERS = ("strategic_objective", "Strategic Objective", "plan_horizon", "Plan horizon", "multi_year_justification")


def unresolved_content(html: str) -> list[str]:
	hits: list[str] = []
	for pattern in UNRESOLVED_PATTERNS:
		for match in re.finditer(pattern, html):
			start = max(0, match.start() - 40)
			hits.append(f"{pattern}: …{html[start:match.end() + 40]!r}")
	return hits


def invitation_absent_from_issued_tender(issued_tender_html: str) -> bool:
	return INVITATION_HEADING not in issued_tender_html


def internal_only_leaks(html: str, context: dict[str, Any] | None = None) -> list[str]:
	"""Marker names, and — when the context is given — the actual internal
	values a Tender carries (objective path text, horizon justification)."""
	leaks = [marker for marker in INTERNAL_ONLY_MARKERS if marker in html]
	if context:
		for value in (context.get("_internal") or {}).values():
			if value and str(value) in html:
				leaks.append(f"value:{value}")
	return leaks


def shared_values(context: dict[str, Any]) -> dict[str, str]:
	tender = context.get("tender", {})
	return {
		"reference": tender.get("reference", ""),
		"title": tender.get("title", ""),
		"procuring_entity": context.get("procuring_entity", {}).get("name", ""),
		"clarification_deadline": tender.get("clarification_deadline", ""),
		"submission_deadline": tender.get("submission_deadline", ""),
		"submission_channel": context.get("platform", {}).get("public_url", ""),
		"tender_security_amount": (tender.get("tender_security") or {}).get("amount", ""),
	}


def cross_output_inconsistencies(context: dict[str, Any], invitation_html: str, issued_tender_html: str) -> list[str]:
	problems: list[str] = []
	for label, value in shared_values(context).items():
		if not value:
			problems.append(f"{label} is empty")
			continue
		if value not in invitation_html:
			problems.append(f"{label} missing from the Invitation")
		if value not in issued_tender_html:
			problems.append(f"{label} missing from the issued Tender")
	return problems
