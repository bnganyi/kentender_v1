# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender cross-module validation — doc 2 sec. 17 (XMV-BND-001).

Maps governance checks to ``XMV-PT-001`` … ``011`` findings. Critical findings
block ``release_procurement_package_to_tender`` / desk ``release_package_to_tender``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.services.package_completeness import (
	get_package_completeness_blockers,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	format_ambiguous_std_message,
	resolve_std_template_for_handoff,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

BOUNDARY_CODE = "XMV-BND-001"

# Doc 2 sec. 17.1 — all governance codes implemented or intentionally mapped here.
XMV_PT_PLAN_CODES: frozenset[str] = frozenset(f"XMV-PT-{i:03d}" for i in range(1, 12))

_RELEASABLE_PACKAGE_STATUS = frozenset(("Ready for Tender", "Released to Tender"))

_STD_STATUS_ALLOWLIST = frozenset(("Imported", "POC Approved"))

_COMPETITIVE_METHODS = frozenset(("Open Tender", "Restricted Tender", "RFQ", "RFP"))


@dataclass(frozen=True, slots=True)
class XmvFinding:
	code: str
	severity: Literal["critical", "warning"]
	message: str

	def as_dict(self) -> dict[str, str]:
		return asdict(self)


@dataclass
class XmvReleaseValidationResult:
	critical: list[XmvFinding]
	warnings: list[XmvFinding]

	def has_critical(self) -> bool:
		return bool(self.critical)

	def all_findings_dicts(self) -> list[dict[str, str]]:
		return [f.as_dict() for f in self.critical + self.warnings]


def _crit(code: str, message: str) -> XmvFinding:
	return XmvFinding(code=code, severity="critical", message=message)


def _warn(code: str, message: str) -> XmvFinding:
	return XmvFinding(code=code, severity="warning", message=message)


def _active_package_line_count(package_name: str | None) -> int:
	if not package_name:
		return 0
	return cint(
		frappe.db.sql(
			"""select count(*) from `tabProcurement Package Line`
			where package_id = %s and ifnull(is_active, 1) = 1""",
			package_name,
		)[0][0]
	)


def _lines_missing_budget_count(package_name: str | None) -> int:
	if not package_name:
		return 0
	return cint(
		frappe.db.sql(
			"""select count(*) from `tabProcurement Package Line`
			where package_id = %s and ifnull(is_active, 1) = 1
			and ifnull(budget_line_id, '') = ''""",
			package_name,
		)[0][0]
	)


def _non_cancelled_tender_count(package_name: str | None) -> int:
	if not package_name:
		return 0
	return cint(
		frappe.db.count(
			"Procurement Tender",
			{"procurement_package": package_name, "tender_status": ("!=", "Cancelled")},
		)
	)


def resolve_std_template_name_for_xmv(pkg: Document) -> str | None:
	"""Backward-compatible: doc 2 sec. 12 resolution (see ``resolve_std_template_for_handoff``)."""
	return resolve_std_template_for_handoff(pkg).std_name


def validate_package_for_release_xmv(pkg: Document) -> XmvReleaseValidationResult:
	"""Run XMV-PT-001 … 011 for a loaded ``Procurement Package`` document."""
	critical: list[XmvFinding] = []
	warnings: list[XmvFinding] = []

	status = (pkg.get("status") or "").strip()
	if status not in _RELEASABLE_PACKAGE_STATUS:
		critical.append(
			_crit(
				"XMV-PT-001",
				_("[{0}] Package is not in a releasable state (expected Ready for Tender or Released to Tender; got {1}).").format(
					BOUNDARY_CODE, status or _("(empty)")
				),
			)
		)

	if not pkg.get("plan_id"):
		critical.append(
			_crit("XMV-PT-002", _("[{0}] Package has no Procurement Plan.").format(BOUNDARY_CODE))
		)
	else:
		plan_st = frappe.db.get_value("Procurement Plan", pkg.plan_id, "status")
		if (plan_st or "") != "Approved":
			critical.append(
				_crit(
					"XMV-PT-002",
					_("[{0}] Procurement Plan must be Approved (got {1}).").format(
						BOUNDARY_CODE, plan_st or _("(empty)")
					),
				)
			)

	n_lines = _active_package_line_count(pkg.name)
	if n_lines < 1:
		critical.append(
			_crit(
				"XMV-PT-003",
				_("[{0}] Package must have at least one active package line.").format(BOUNDARY_CODE),
			)
		)
	else:
		if pkg.get("template_id"):
			for blocker in get_package_completeness_blockers(pkg):
				critical.append(
					_crit(
						"XMV-PT-007",
						_("[{0}] Planning completeness: {1}").format(BOUNDARY_CODE, blocker),
					)
				)

	if not (pkg.get("procurement_method") or "").strip():
		critical.append(
			_crit("XMV-PT-004", _("[{0}] Procurement method is required.").format(BOUNDARY_CODE))
		)
	if not (pkg.get("contract_type") or "").strip():
		critical.append(
			_crit("XMV-PT-004", _("[{0}] Contract type is required.").format(BOUNDARY_CODE))
		)
	if pkg.get("template_id"):
		cat = (frappe.db.get_value("Procurement Template", pkg.template_id, "category") or "").strip()
		if not cat:
			critical.append(
				_crit(
					"XMV-PT-004",
					_("[{0}] Procurement Template must have a category for release.").format(BOUNDARY_CODE),
				)
			)
	else:
		critical.append(
			_crit("XMV-PT-004", _("[{0}] Procurement Template is required.").format(BOUNDARY_CODE))
		)

	if not (pkg.get("currency") or "").strip():
		critical.append(
			_crit("XMV-PT-005", _("[{0}] Package currency is required.").format(BOUNDARY_CODE))
		)
	elif flt(pkg.get("estimated_value")) <= 0:
		warnings.append(
			_warn(
				"XMV-PT-005",
				_("[{0}] Estimated value is zero; confirm funding before production release.").format(
					BOUNDARY_CODE
				),
			)
		)

	if n_lines >= 1 and _lines_missing_budget_count(pkg.name) > 0:
		critical.append(
			_crit(
				"XMV-PT-006",
				_("[{0}] Active package lines must reference a Budget Line.").format(BOUNDARY_CODE),
			)
		)

	std_res = resolve_std_template_for_handoff(pkg)
	if std_res.path == "invalid_default":
		critical.append(
			_crit(
				"XMV-PT-008",
				_("[{0}] Procurement Template.default_std_template points to a missing STD ({1}).").format(
					BOUNDARY_CODE,
					std_res.invalid_default_link or _("(empty)"),
				),
			)
		)
	elif std_res.is_ambiguous:
		detail = format_ambiguous_std_message(std_res.ambiguous_candidates)
		critical.append(
			_crit(
				"XMV-PT-008",
				_("[{0}] Multiple STD templates match this package; set default_std_template or reduce ambiguity. Candidates: {1}").format(
					BOUNDARY_CODE,
					detail,
				),
			)
		)
	elif not std_res.std_name:
		critical.append(
			_crit(
				"XMV-PT-008",
				_(
					"[{0}] STD Template could not be resolved (set Procurement Template.default_std_template, extend mapping, or use Works + Open Tender with contract type for POC fallback {1})."
				).format(BOUNDARY_CODE, TEMPLATE_CODE),
			)
		)
	else:
		std_name = std_res.std_name
		std_row = frappe.db.get_value(
			"STD Template",
			std_name,
			["status", "allowed_for_tender_creation"],
			as_dict=True,
		)
		if not std_row:
			critical.append(
				_crit(
					"XMV-PT-008",
					_("[{0}] STD Template {1} was not found.").format(BOUNDARY_CODE, std_name),
				)
			)
		else:
			st = (std_row.get("status") or "").strip()
			if st not in _STD_STATUS_ALLOWLIST:
				critical.append(
					_crit(
						"XMV-PT-008",
						_("[{0}] STD Template status must be Imported or POC Approved (got {1}).").format(
							BOUNDARY_CODE, st or _("(empty)")
						),
					)
				)
			if not cint(std_row.get("allowed_for_tender_creation")):
				critical.append(
					_crit(
						"XMV-PT-008",
						_("[{0}] STD Template is not allowed for tender creation.").format(BOUNDARY_CODE),
					)
				)

	tcount = _non_cancelled_tender_count(pkg.name)
	if tcount > 1:
		critical.append(
			_crit(
				"XMV-PT-009",
				_("[{0}] Multiple non-cancelled tenders linked to this package ({1}).").format(
					BOUNDARY_CODE, tcount
				),
			)
		)

	tpl_cat = ""
	if pkg.get("template_id"):
		tpl_cat = (frappe.db.get_value("Procurement Template", pkg.template_id, "category") or "").strip()
	method = (pkg.get("procurement_method") or "").strip()
	if tpl_cat.lower() == "works" and method in _COMPETITIVE_METHODS:
		warnings.append(
			_warn(
				"XMV-PT-010",
				_(
					"[{0}] Works competitive package: full BoQ readiness is enforced in later tracks (B7/WH); posture not fully validated here."
				).format(BOUNDARY_CODE),
			)
		)

	try:
		line_names = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": pkg.name, "is_active": 1},
			pluck="name",
			limit=50,
		)
		snap: dict[str, Any] = {
			"package": pkg.name,
			"package_code": pkg.get("package_code"),
			"plan_id": pkg.get("plan_id"),
			"template_id": pkg.get("template_id"),
			"procurement_method": pkg.get("procurement_method"),
			"estimated_value": flt(pkg.get("estimated_value")),
			"currency": pkg.get("currency"),
			"line_names": line_names,
		}
		json.dumps(snap, default=str)
	except Exception as exc:
		critical.append(
			_crit(
				"XMV-PT-011",
				_("[{0}] Handoff snapshot could not be serialized: {1}").format(BOUNDARY_CODE, exc),
			)
		)

	return XmvReleaseValidationResult(critical=critical, warnings=warnings)


def format_xmv_critical_message(result: XmvReleaseValidationResult) -> str:
	"""Single user-facing string for ``frappe.throw`` / service ``ok: False``."""
	parts = [f.message for f in result.critical]
	return " ".join(parts) if parts else _("Validation failed.")
