# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 2 sec. 12 — STD Template selection for planning-to-tender handoff (Tracker B6).

Resolution order (12.1):

1. ``Procurement Template.default_std_template`` when set and the STD row exists.
2. Mapping pass: eligible STD rows (allowed for tender creation + status allowlist),
   filtered by planning template **category** vs ``STD Template.procurement_category``.
   If more than one remains, handoff is **ambiguous** and must not guess (12.1 / §21).
3. Fixed Works POC fallback (12.2) only when mapping produced no candidates: Works +
   Open Tender + a non-empty contract type from the package field options.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

_STD_STATUS_HANDOFF = ("Imported", "POC Approved")

HandoffStdPath = Literal[
	"default_std_template",
	"mapping_service",
	"works_poc_fallback",
	"unresolved",
	"ambiguous",
	"invalid_default",
]


@dataclass(frozen=True, slots=True)
class HandoffStdResolution:
	"""Outcome of ``resolve_std_template_for_handoff``."""

	std_name: str | None
	path: HandoffStdPath
	ambiguous_candidates: tuple[str, ...] = ()
	invalid_default_link: str | None = None

	@property
	def is_ambiguous(self) -> bool:
		return self.path == "ambiguous"


def _base_eligible_std_names() -> list[str]:
	return frappe.get_all(
		"STD Template",
		filters={
			"allowed_for_tender_creation": 1,
			"status": ("in", _STD_STATUS_HANDOFF),
		},
		pluck="name",
	)


def filter_std_names_for_planning_category(std_names: list[str], planning_category: str) -> list[str]:
	"""Narrow eligible STD rows by planning template category (doc 2 sec. 12.1 step 2)."""
	cat = (planning_category or "").strip().upper()
	out: list[str] = []
	for n in std_names:
		std_cat = (frappe.db.get_value("STD Template", n, "procurement_category") or "").strip().upper()
		if cat == "WORKS":
			if std_cat == "WORKS":
				out.append(n)
		elif cat in ("GOODS", "SERVICES"):
			if std_cat != "WORKS":
				out.append(n)
		elif not cat:
			continue
		else:
			out.append(n)
	return out


def _works_poc_fallback_eligible(pkg: Document) -> bool:
	"""Doc 2 sec. 12.2 — narrow Works + Open Tender + contract posture."""
	tid = pkg.get("template_id")
	if not tid:
		return False
	tpl_cat = (frappe.db.get_value("Procurement Template", tid, "category") or "").strip().lower()
	if tpl_cat != "works":
		return False
	if (pkg.get("procurement_method") or "").strip() != "Open Tender":
		return False
	ct = (pkg.get("contract_type") or "").strip()
	if not ct:
		return False
	return ct in ("Fixed Price", "Cost Reimbursable", "T&M")


def resolve_std_template_for_handoff(pkg: Document) -> HandoffStdResolution:
	"""Deterministic STD resolution for ``Procurement Package`` handoff (fail-closed)."""
	tid = pkg.get("template_id")
	if not tid:
		return HandoffStdResolution(None, "unresolved")

	default_std = (
		frappe.db.get_value("Procurement Template", tid, "default_std_template") or ""
	).strip()
	if default_std:
		if not frappe.db.exists("STD Template", default_std):
			return HandoffStdResolution(
				None,
				"invalid_default",
				invalid_default_link=default_std,
			)
		return HandoffStdResolution(default_std, "default_std_template")

	tpl_category = frappe.db.get_value("Procurement Template", tid, "category")
	base = _base_eligible_std_names()
	mapping = filter_std_names_for_planning_category(base, tpl_category or "")

	if len(mapping) > 1:
		return HandoffStdResolution(None, "ambiguous", ambiguous_candidates=tuple(mapping))
	if len(mapping) == 1:
		return HandoffStdResolution(mapping[0], "mapping_service")

	if _works_poc_fallback_eligible(pkg) and frappe.db.exists("STD Template", TEMPLATE_CODE):
		return HandoffStdResolution(TEMPLATE_CODE, "works_poc_fallback")

	return HandoffStdResolution(None, "unresolved")


def format_ambiguous_std_message(candidates: tuple[str, ...]) -> str:
	"""Human-readable list of ambiguous STD rows (code + name, no raw internal id emphasis)."""
	parts: list[str] = []
	for name in candidates:
		row = frappe.db.get_value(
			"STD Template",
			name,
			["template_code", "template_name"],
			as_dict=True,
		)
		if row:
			code = (row.get("template_code") or name).strip()
			tn = (row.get("template_name") or "").strip()
			parts.append(f"{tn} ({code})" if tn else code)
		else:
			parts.append(name)
	return "; ".join(parts)
