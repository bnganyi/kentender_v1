# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-001 — WORKS master seed loader (seed data specification §19–20, §15–16 PLC materialization).

This module materializes **Procurement Journey** + **Procurement Journey Step** + **Procurement Handoff Card**
rows for the canonical MOH WORKS scenario. Upstream DocTypes (Strategy, Budget, Demand, TM2, …) are **not**
created here (tracked under LV-R2-001-03 … LV-R2-001-09); the loader emits **warnings** when expected
codes are absent so operators can run prerequisite seeds first.

``reset=True`` deletes only **master-flagged** PLC rows for the WORKS journey / handoff codes (§19.4).
"""

from __future__ import annotations

from typing import Any, Final

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.procurement_lifecycle.evidence_links import parse_validate_and_normalize_evidence_links
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	BASE_HANDOFF_CODES,
	JOURNEY_CODE,
	OPENING_HANDOFF_CODES,
	base_handoff_blueprints,
	opening_handoff_blueprints,
)
from kentender_procurement.procurement_lifecycle.technical_refs import parse_validate_technical_refs_json
from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
	WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)

SUPPORTED_CHECKPOINTS: Final[frozenset[str]] = frozenset({"TENDER_PUBLISHED", "OPENING_READY"})

# Header ``current_stage_key`` must satisfy R1-003 / ``JOURNEY_STEP_KEYS_IN_ORDER`` (not the §14 shorthand ``tender``).
JOURNEY_HEADER_STAGE_KEY: Final[str] = "tender_published"

# §15 base checkpoint — materialized child rows (WORKS §15 step_key vocabulary).
WORKS_BASE_STEP_ROWS: Final[tuple[dict[str, Any], ...]] = (
	{
		"step_order": 1,
		"step_key": "strategy",
		"label": "Strategy Priority",
		"status_category": "Completed",
		"owner_module": "Strategy",
		"source_object_type": "Strategy Objective",
		"source_object_code": "OBJ-MOH-HOSP-RENOV",
		"handoff_code": "STRATREF-MOH-2026-001",
		"last_action": "Priority approved",
		"next_action": "",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 2,
		"step_key": "budget",
		"label": "Funding Available",
		"status_category": "Completed",
		"owner_module": "Budget",
		"source_object_type": "Budget Line",
		"source_object_code": "BUD-MOH-INFRA-2026-001",
		"handoff_code": "BUDCONF-MOH-2026-001",
		"last_action": "Budget funding confirmed",
		"next_action": "",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 3,
		"step_key": "demand",
		"label": "Need Approved",
		"status_category": "Completed",
		"owner_module": "Demand Intake and Approval",
		"source_object_type": "Demand",
		"source_object_code": "DEM-MOH-2026-001",
		"handoff_code": "DEMAPP-MOH-2026-001",
		"last_action": "Demand approved",
		"next_action": "",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 4,
		"step_key": "planning_inclusion",
		"label": "Procurement Planned",
		"status_category": "Completed",
		"owner_module": "Procurement Planning",
		"source_object_type": "Procurement Plan",
		"source_object_code": "PLAN-MOH-2026",
		"handoff_code": "PLANINCL-MOH-2026-001",
		"last_action": "Demand included in procurement plan",
		"next_action": "",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 5,
		"step_key": "package_release",
		"label": "Package Released",
		"status_category": "Handed Off",
		"owner_module": "Procurement Planning",
		"source_object_type": "Procurement Package",
		"source_object_code": "PKG-MOH-2026-001",
		"handoff_code": "PKGREL-MOH-2026-001",
		"last_action": "Package released to Tender Management",
		"next_action": "",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 6,
		"step_key": "std_readiness",
		"label": "Tender Document Ready",
		"status_category": "Completed",
		"owner_module": "STD Engine / Tender Management",
		"source_object_type": "Tender STD Instance",
		"source_object_code": "STDINST-TND-MOH-2026-001",
		"handoff_code": "STDREADY-TND-MOH-2026-001",
		"last_action": "Tender document readiness passed",
		"next_action": "",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 7,
		"step_key": "tender_publication",
		"label": "Tender Published",
		"status_category": "Completed",
		"owner_module": "Tender Management",
		"source_object_type": "TM2 Tender",
		"source_object_code": "TND-MOH-2026-001",
		"handoff_code": "PUBCERT-TND-MOH-2026-001",
		"last_action": "Tender published",
		"next_action": "Await tender closing",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 8,
		"step_key": "tender_closing",
		"label": "Tender Closed",
		"status_category": "Not Started",
		"owner_module": "Tender Management",
		"source_object_type": "Tender Closing Record",
		"source_object_code": "",
		"handoff_code": "",
		"last_action": "",
		"next_action": "Close tender after submission deadline",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 9,
		"step_key": "opening_readiness",
		"label": "Opening Ready",
		"status_category": "Not Started",
		"owner_module": "Tender Management / Bid Opening",
		"source_object_type": "Opening Readiness Record",
		"source_object_code": "",
		"handoff_code": "",
		"last_action": "",
		"next_action": "Prepare opening readiness after tender closes",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 10,
		"step_key": "bid_opening",
		"label": "Opening Complete",
		"status_category": "Not Started",
		"owner_module": "Bid Opening",
		"source_object_type": "Opening Record",
		"source_object_code": "",
		"handoff_code": "",
		"last_action": "",
		"next_action": "Conduct bid opening session",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 11,
		"step_key": "evaluation_award",
		"label": "Evaluation / Award",
		"status_category": "Not Started",
		"owner_module": "Evaluation & Award",
		"source_object_type": "Award Decision",
		"source_object_code": "",
		"handoff_code": "",
		"last_action": "",
		"next_action": "Evaluate opened bids and approve award",
		"blocker_count": 0,
		"blockers_json": {},
	},
	{
		"step_order": 12,
		"step_key": "contract",
		"label": "Contract Handoff",
		"status_category": "Not Started",
		"owner_module": "Contract Management",
		"source_object_type": "Contract Handoff Reference",
		"source_object_code": "",
		"handoff_code": "",
		"last_action": "",
		"next_action": "Form contract after award",
		"blocker_count": 0,
		"blockers_json": {},
	},
)


def _unsupported_checkpoint_response(checkpoint: str) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "UNSUPPORTED_CHECKPOINT",
		"message": "Supported checkpoints are TENDER_PUBLISHED and OPENING_READY.",
		"checkpoint": checkpoint,
	}


def _assert_step_contract() -> None:
	keys = tuple(r["step_key"] for r in WORKS_BASE_STEP_ROWS)
	if keys != WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER:
		raise RuntimeError("WORKS_BASE_STEP_ROWS drifted from WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER")


def _upstream_warnings() -> list[str]:
	out: list[str] = []
	if not frappe.db.exists("Procuring Entity", {"entity_code": "PE-MOH"}) and not frappe.db.exists(
		"Procuring Entity", {"entity_code": "MOH"}
	):
		out.append("Procuring Entity PE-MOH (or MOH) not found — core prerequisite seed may be missing.")
	if not frappe.db.exists("Demand", {"demand_id": "DEM-MOH-2026-001"}):
		out.append("Demand DEM-MOH-2026-001 not found — demand seed not aligned (LV-R2-001-06).")
	if not frappe.db.exists("Procurement Package", {"package_code": "PKG-MOH-2026-001"}):
		out.append("Procurement Package PKG-MOH-2026-001 not found — planning seed not aligned (LV-R2-001-07).")
	if not frappe.db.exists("TM2 Tender", "TND-MOH-2026-001"):
		out.append("TM2 Tender TND-MOH-2026-001 not found — tender seed not aligned (LV-R2-001-09).")
	return out


def _assert_journey_slot_safe_for_master() -> None:
	if not frappe.db.exists("Procurement Journey", JOURNEY_CODE):
		return
	ms = cint(frappe.db.get_value("Procurement Journey", JOURNEY_CODE, "is_master_seed") or 0)
	if not ms:
		frappe.throw(
			_(
				"WORKS master journey code {0} is already used by a non-master row. "
				"Resolve or rename before loading master seed."
			).format(JOURNEY_CODE)
		)


def _reset_master_plc_rows(*, include_opening_handoffs: bool) -> None:
	"""§19.4 / R2-002 / SEED-TEST-006 — safe reset for WORKS master PLC only.

	Deletes **Procurement Handoff Card** rows whose ``handoff_code`` is in the WORKS base (and,
	when ``include_opening_handoffs``, optional opening) allowlist **and** ``is_master_seed`` is
	set, then the **Procurement Journey** named ``JOURNEY_CODE`` if ``is_master_seed`` is set.
	Rows outside those codes, or allowlisted codes with ``is_master_seed=0``, are **not** deleted
	(operators must resolve conflicts separately — :func:`_assert_journey_slot_safe_for_master`).
	Order: handoffs first, then journey (reverse dependency).
	"""
	codes = list(BASE_HANDOFF_CODES)
	if include_opening_handoffs:
		codes.extend(OPENING_HANDOFF_CODES)
	for hc in codes:
		if not frappe.db.exists("Procurement Handoff Card", hc):
			continue
		ms = cint(frappe.db.get_value("Procurement Handoff Card", hc, "is_master_seed") or 0)
		if ms:
			frappe.delete_doc("Procurement Handoff Card", hc, force=True, ignore_permissions=True)
	if frappe.db.exists("Procurement Journey", JOURNEY_CODE):
		ms = cint(frappe.db.get_value("Procurement Journey", JOURNEY_CODE, "is_master_seed") or 0)
		if ms:
			frappe.delete_doc("Procurement Journey", JOURNEY_CODE, force=True, ignore_permissions=True)


def _normalize_evidence_links(raw_links: list[dict[str, Any]]) -> dict[str, Any]:
	links_out: list[dict[str, str]] = []
	for L in raw_links:
		row = {**L, "route": (L.get("route") or "").strip() or "/desk/"}
		links_out.append(row)
	return parse_validate_and_normalize_evidence_links({"links": links_out})


def _upsert_handoff_from_blueprint(bp: dict[str, Any]) -> str:
	code = bp["handoff_code"]
	evidence = _normalize_evidence_links(bp["evidence_links"])
	tech = parse_validate_technical_refs_json(bp["technical_refs"])
	row = {
		"doctype": "Procurement Handoff Card",
		"handoff_code": code,
		"handoff_title": bp["handoff_title"],
		"journey_code": JOURNEY_CODE,
		"source_module": bp["source_module"],
		"target_module": bp["target_module"],
		"source_object_type": bp["source_object_type"],
		"source_object_code": bp["source_object_code"],
		"target_object_type": bp.get("target_object_type") or "",
		"target_object_code": (bp.get("target_object_code") or "").strip(),
		"status": bp["status"],
		"generated_by": bp["generated_by"],
		"generated_at": bp["generated_at"],
		"consumed_by": (bp.get("consumed_by") or "").strip(),
		"consumed_at": (bp.get("consumed_at") or "").strip(),
		"locked_summary": bp["locked_summary"],
		"passed_forward_summary": bp["passed_forward_summary"],
		"next_action": bp["next_action"],
		"evidence_links_json": evidence,
		"technical_refs_json": tech,
		"is_master_seed": 1,
	}
	if frappe.db.exists("Procurement Handoff Card", code):
		doc = frappe.get_doc("Procurement Handoff Card", code)
		for k, v in row.items():
			if k != "doctype":
				doc.set(k, v)
		doc.save(ignore_permissions=True)
		return "updated"
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return "created"


def _upsert_journey_and_steps() -> str:
	"""Create/update master journey + 12 WORKS §15 steps (base ``TENDER_PUBLISHED`` snapshot)."""
	journey_fields = {
		"doctype": "Procurement Journey",
		"journey_code": JOURNEY_CODE,
		"journey_title": "District Hospital Renovation Works",
		"description": (
			"End-to-end procurement journey for building and associated civil engineering works "
			"at Makutano District Hospital."
		),
		"procuring_entity_code": "PE-MOH",
		"fiscal_year": "2026/2027",
		"procurement_category": "Works",
		"procurement_method": "Open Tender",
		"current_stage_key": JOURNEY_HEADER_STAGE_KEY,
		"current_stage_label": "Tender Published",
		"current_status_category": "Completed",
		"current_owner_module": "Tender Management",
		"current_owner_role": "Procurement Officer",
		"next_action": "Await tender closing / prepare bid opening readiness after submission deadline.",
		"blocker_count": 0,
		"critical_blocker_count": 0,
		"strategy_ref": "OBJ-MOH-HOSP-RENOV",
		"budget_line_ref": "BUD-MOH-INFRA-2026-001",
		"demand_ref": "DEM-MOH-2026-001",
		"procurement_plan_ref": "PLAN-MOH-2026",
		"procurement_package_ref": "PKG-MOH-2026-001",
		"std_template_version_ref": "STDTV-WORKS-BUILDING-CIVIL-APR2022",
		"tender_std_instance_ref": "STDINST-TND-MOH-2026-001",
		"tm2_tender_ref": "TND-MOH-2026-001",
		"publication_snapshot_ref": "PUBSNAP-TND-MOH-2026-001-V2",
		"opening_readiness_ref": "",
		"is_master_seed": 1,
	}
	if frappe.db.exists("Procurement Journey", JOURNEY_CODE):
		doc = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
		for k, v in journey_fields.items():
			if k not in ("doctype", "journey_code"):
				doc.set(k, v)
		doc.steps = []
	else:
		doc = frappe.get_doc(journey_fields)
	for row in WORKS_BASE_STEP_ROWS:
		doc.append("steps", dict(row))
	doc.save(ignore_permissions=True)
	return "saved"


def _apply_opening_checkpoint_mutations() -> None:
	"""§15 optional rows + §16.9–16.10 handoffs."""
	j = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
	for row in j.steps:
		if row.step_key == "tender_closing":
			row.status_category = "Completed"
			row.source_object_code = "CLS-TND-MOH-2026-001"
			row.handoff_code = "CLOSECERT-TND-MOH-2026-001"
			row.last_action = "Tender closed by official server time"
			row.next_action = ""
		elif row.step_key == "opening_readiness":
			row.status_category = "Ready for Handoff"
			row.source_object_code = "ORR-TND-MOH-2026-001"
			row.handoff_code = "OPENREADY-TND-MOH-2026-001"
			row.last_action = "Opening readiness prepared"
			row.next_action = "Conduct bid opening session"
	j.opening_readiness_ref = "ORR-TND-MOH-2026-001"
	j.current_stage_key = "opening_ready"
	j.current_stage_label = "Opening Ready"
	j.current_status_category = "Ready for Handoff"
	j.next_action = "Conduct bid opening session using the opening register rules."
	j.save(ignore_permissions=True)
	for bp in opening_handoff_blueprints():
		_upsert_handoff_from_blueprint(bp)


def run_load(*, reset: bool = False, checkpoint: str = "TENDER_PUBLISHED") -> dict[str, Any]:
	"""Internal entry used by :func:`load_procurement_lifecycle_works_master`.

	Seed spec §19.2 lists entity → … → handoff ordering. This tranche implements the **PLC tail**
	(journey, journey steps §15, handoff cards §16) plus optional ``OPENING_READY`` mutations.
	Earlier steps remain **out of scope** here (LV-R2-001-03 … LV-R2-001-09); missing upstream
	records surface as **warnings** so operators can run prerequisite seeds. §19.2 step **16
	validation** is **R2-003** (``validate_procurement_lifecycle_works_master_seed``).
	"""
	_assert_step_contract()
	cp = (checkpoint or "").strip().upper()
	if cp not in SUPPORTED_CHECKPOINTS:
		return _unsupported_checkpoint_response(checkpoint)

	warnings = _upstream_warnings()
	include_opening = cp == "OPENING_READY"
	if reset:
		# Always clear optional opening handoffs on reset so base checkpoint is clean (§19.4).
		_reset_master_plc_rows(include_opening_handoffs=True)

	_assert_journey_slot_safe_for_master()

	_upsert_journey_and_steps()
	for bp in base_handoff_blueprints():
		_upsert_handoff_from_blueprint(bp)

	handoff_count = len(BASE_HANDOFF_CODES)
	if include_opening:
		_apply_opening_checkpoint_mutations()
		handoff_count = len(BASE_HANDOFF_CODES) + len(OPENING_HANDOFF_CODES)

	summary = {
		"ok": True,
		"checkpoint": cp,
		"journey_code": JOURNEY_CODE,
		"master_scenario": "District Hospital Renovation Works",
		"created_or_updated": {
			"procuring_entities": 0,
			"strategy_records": 0,
			"budget_records": 0,
			"demand_records": 0,
			"planning_records": 0,
			"std_reference_records": 0,
			"tm2_reference_records": 0,
			"journey_records": 1,
			"journey_steps": len(WORKS_BASE_STEP_ROWS),
			"handoff_cards": handoff_count,
			"evidence_events": 0,
		},
		"current_stage": "Tender Published" if cp == "TENDER_PUBLISHED" else "Opening Ready",
		"next_action": (
			"Await tender closing / prepare bid opening readiness after submission deadline."
			if cp == "TENDER_PUBLISHED"
			else "Conduct bid opening session using the opening register rules."
		),
		"warnings": warnings,
		"status": "loaded",
	}
	return summary
