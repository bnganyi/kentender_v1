from __future__ import annotations

from typing import Any

import frappe

# STD-CURSOR-0702 — source change → affected output types (Current rows marked stale).
CHANGE_KIND_TO_OUTPUT_TYPES: dict[str, tuple[str, ...]] = {
	"tds_submission_deadline": ("Bundle", "DSM", "DOM"),
	"tds_tender_security": ("Bundle", "DSM", "DEM"),
	"tds_margin_of_preference": ("Bundle", "DEM"),
	"scc_contract_parameter": ("Bundle", "DCM"),
	"works_requirement_change": ("Bundle", "DSM", "DEM", "DCM"),
	"boq_item_quantity": ("Bundle", "DSM", "DEM", "DCM"),
	"drawing_or_spec_attachment": ("Bundle", "DCM", "DEM"),
	"form_definition_change": ("Bundle", "DSM", "DEM", "DCM"),
}


def resolve_parameter_change_kind(parameter_code: str, drives_dem: int, drives_dcm: int) -> str:
	pc = (parameter_code or "").lower()
	if int(drives_dcm or 0):
		return "scc_contract_parameter"
	if "deadline" in pc:
		return "tds_submission_deadline"
	if "security" in pc or "tender_sec" in pc:
		return "tds_tender_security"
	if "margin" in pc or "preference" in pc:
		return "tds_margin_of_preference"
	if int(drives_dem or 0):
		return "tds_tender_security"  # conservative: DEM-driving TDS-style
	return "tds_submission_deadline"


@frappe.whitelist()
def mark_std_outputs_stale(instance_code: str, change_kind: str, actor: str | None = None) -> dict[str, Any]:
	"""Mark Current STD Generated Output rows stale per Phase 7 change-kind matrix."""
	types = CHANGE_KIND_TO_OUTPUT_TYPES.get(change_kind)
	if not types:
		return {"instance_code": instance_code, "change_kind": change_kind, "marked": [], "skipped": True}
	marked: list[str] = []
	reason = f"stale:{change_kind}"
	for output_type in types:
		for row in frappe.get_all(
			"STD Generated Output",
			filters={"instance_code": instance_code, "output_type": output_type, "status": "Current"},
			fields=["name", "output_code"],
		):
			frappe.db.set_value(
				"STD Generated Output",
				row["name"],
				{"is_stale": 1, "stale_reason": reason[:140]},
				update_modified=False,
			)
			marked.append(row["output_code"])
	return {"instance_code": instance_code, "change_kind": change_kind, "marked": marked}


def infer_change_kind_from_attachment_classification(classification: str) -> str:
	if classification in ("Drawing", "Specification"):
		return "drawing_or_spec_attachment"
	return "drawing_or_spec_attachment"
