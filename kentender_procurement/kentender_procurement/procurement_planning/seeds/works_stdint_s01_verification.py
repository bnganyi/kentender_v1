# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 3 §28–29 — WORKS ``STDINT-WORKS-S01`` seed verification + integration smoke.

§28: structural checks after seed (strategy chain, demands, plan, package, tender linkage, roll-up).
§29: tender-stage smoke — ``validate_tender_configuration`` → ``generate_sample_boq`` → re-validate →
``generate_required_forms`` → ``generate_tender_pack_preview`` (existing ``Procurement Tender`` APIs),
then **doc 5 §25 / WH-013** — ``run_works_tender_stage_hardening`` after preview (order differs from doc 5
bullet list; BoQ/forms/preview must exist before orchestration — see planning handoff tracker).

Run via ``seed_works_stdint_s01.run()`` return keys ``section_28_verification`` / ``section_29_smoke``, or
``bench execute kentender_procurement.procurement_planning.seeds.works_stdint_s01_verification.run_smoke_for_package_code``.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import flt

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_controller,
)
from kentender_procurement.tender_management.services import works_tender_hardening
from kentender_procurement.tender_management.services.works_tender_hardening_validation import (
	HARDENING_STATUS_BLOCKED,
	HARDENING_STATUS_FAILED,
)

# Doc 3 §28 table lists **15** for the full primary ``sample_tender.json`` scenario (STD-WORKS-POC Step 16).
# Handoff + labelled officer seed (no ``load_sample_tender`` demo narrative) resolves **defaults + partial
# rule activation** only — currently **8** forms (7× ``default_required`` in ``forms.json`` + one rule-driven).
EXPECTED_REQUIRED_FORMS_INTEGRATED_SEED = 8
# After ``load_sample_tender`` (WH-013 gate): primary ``sample_tender.json`` activation count (Step 16).
EXPECTED_REQUIRED_FORMS_PRIMARY_SAMPLE = 15
EXPECTED_BOQ_ROWS = 9

# Doc 3 §20 audit keys (same strings as ``seed_works_stdint_s01``) — re-stamped after ``load_sample_tender`` (WH-013).
_WH013_SEED_OFFICER_APPLIED = "SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_APPLIED"
_WH013_SEED_OFFICER_LABEL = "SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_LABEL"
_WH013_SEED_MERGE_VERSION = "SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_MERGE_VERSION"
_WH013_SEED_OFFICER_LABEL_TEXT = (
	"Sample officer completion (doc 3 §20, §28) — NOT Planning authority data. Scenario STDINT-WORKS-S01."
)
_WH013_SEED_MERGE_VERSION_INT = 3


def _stamp_seed_officer_audit_flags_after_sample(tender_name: str) -> None:
	"""``load_sample_tender`` replaces ``configuration_json``; restore §20 SEED markers without altering sample keys."""
	doc = frappe.get_doc("Procurement Tender", tender_name)
	try:
		cfg: dict[str, Any] = json.loads(doc.configuration_json or "{}")
	except json.JSONDecodeError:
		cfg = {}
	cfg[_WH013_SEED_OFFICER_APPLIED] = 1
	cfg[_WH013_SEED_OFFICER_LABEL] = _WH013_SEED_OFFICER_LABEL_TEXT
	cfg[_WH013_SEED_MERGE_VERSION] = _WH013_SEED_MERGE_VERSION_INT
	doc.configuration_json = json.dumps(cfg, indent=2, ensure_ascii=False)
	doc.save(ignore_permissions=True)


def _ensure_two_smoke_lots(tender_name: str) -> None:
	"""Two lots (LOT-001 / LOT-002) so sample BoQ validates against lot refs (doc 3 §29 / STD-POC)."""
	t = frappe.get_doc("Procurement Tender", tender_name)
	if len(t.get("lots") or []) >= 2:
		return
	t.set("lots", [])
	t.append(
		"lots",
		{
			"lot_code": "LOT-001",
			"lot_title": "Hospital renovation — main building (WORKS S01 seed)",
			"description": "Outpatient and ward blocks, roofing, finishes (seed verification).",
			"estimated_value": 68_000_000.0,
			"currency": "KES",
		},
	)
	t.append(
		"lots",
		{
			"lot_code": "LOT-002",
			"lot_title": "Hospital renovation — drainage and external (WORKS S01 seed)",
			"description": "Drainage, external works, paving (seed verification).",
			"estimated_value": 27_000_000.0,
			"currency": "KES",
		},
	)
	t.save(ignore_permissions=True)


def _append(
	checks: list[dict[str, Any]],
	check_id: str,
	ok: bool,
	detail: str = "",
) -> None:
	checks.append({"id": check_id, "ok": bool(ok), "detail": (detail or "")[:500]})


def gather_doc3_section_28_checks(
	*,
	tender_name: str,
	package_name: str,
	plan_name: str,
	budget_line_name: str,
	demand_ids: tuple[str, ...],
	std_template_code: str,
) -> dict[str, Any]:
	"""Return §28 checklist results (no writes)."""
	checks: list[dict[str, Any]] = []

	if not frappe.db.exists("Budget Line", budget_line_name):
		_append(checks, "budget_line_exists", False, budget_line_name)
	else:
		_append(checks, "budget_line_exists", True, budget_line_name)
		bl = frappe.get_doc("Budget Line", budget_line_name)
		has_strategy = bool(
			(getattr(bl, "strategic_plan", None) or "").strip()
			or (getattr(bl, "program", None) or "").strip()
		)
		_append(checks, "strategy_link_on_budget_line", has_strategy, "strategic_plan or program")

	for did in demand_ids:
		dn = frappe.db.get_value("Demand", {"demand_id": did}, "name")
		if not dn:
			_append(checks, f"demand_{did}", False, "missing")
			continue
		bl_on_d = frappe.db.get_value("Demand", dn, "budget_line")
		ok = bool(bl_on_d) and bl_on_d == budget_line_name
		_append(checks, f"demand_{did}_links_budget_line", ok, str(bl_on_d or ""))

	if not frappe.db.exists("Procurement Plan", plan_name):
		_append(checks, "procurement_plan_exists", False, plan_name)
	else:
		st = (frappe.db.get_value("Procurement Plan", plan_name, "status") or "").strip()
		_append(checks, "procurement_plan_approved", st == "Approved", st)

	tpl_id = frappe.db.get_value("Procurement Package", package_name, "template_id")
	if tpl_id:
		dst = frappe.db.get_value("Procurement Template", tpl_id, "default_std_template")
		_append(
			checks,
			"procurement_template_resolves_std",
			(dst or "").strip() == std_template_code,
			str(dst or ""),
		)
	else:
		_append(checks, "procurement_template_resolves_std", False, "no template_id")

	line_count = frappe.db.count("Procurement Package Line", {"package_id": package_name})
	_append(checks, "package_has_lines", line_count >= 1, f"count={line_count}")

	lines = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_name},
		fields=["amount"],
	)
	line_total = sum(flt(r.amount) for r in lines)
	pkg_ev = flt(frappe.db.get_value("Procurement Package", package_name, "estimated_value"))
	_append(
		checks,
		"package_estimated_equals_line_total",
		abs(pkg_ev - line_total) < 0.01 or line_total == 0,
		f"pkg={pkg_ev} lines={line_total}",
	)

	pkg_st = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()
	_append(
		checks,
		"package_released_or_releasable",
		pkg_st == "Released to Tender",
		pkg_st,
	)

	if not frappe.db.exists("Procurement Tender", tender_name):
		_append(checks, "tender_exists", False, tender_name)
	else:
		_append(checks, "tender_exists", True, tender_name)
		t_pkg = frappe.db.get_value("Procurement Tender", tender_name, "procurement_package")
		t_plan = frappe.db.get_value("Procurement Tender", tender_name, "procurement_plan")
		t_std = (frappe.db.get_value("Procurement Tender", tender_name, "std_template") or "").strip()
		_append(checks, "tender_links_package", t_pkg == package_name, str(t_pkg or ""))
		exp_plan = frappe.db.get_value("Procurement Package", package_name, "plan_id")
		_append(checks, "tender_links_plan", t_plan == exp_plan, str(t_plan or ""))
		_append(checks, "tender_links_std", t_std == std_template_code, t_std)

		raw = frappe.db.get_value("Procurement Tender", tender_name, "configuration_json") or ""
		_append(checks, "tender_configuration_json_populated", len(raw.strip()) > 20, f"len={len(raw)}")

		src_h = frappe.db.get_value("Procurement Tender", tender_name, "source_package_hash")
		_append(checks, "audit_source_package_hash", bool((src_h or "").strip()), "")

	_append(checks, "no_publication_records_required", True, "v1: no tender-linked publication DocType enforced")

	all_passed = all(c["ok"] for c in checks)
	return {"checks": checks, "all_passed": all_passed}


def run_doc3_section_29_smoke(tender_name: str) -> dict[str, Any]:
	"""Execute §29 tender-stage steps (writes tender). Caller must use Administrator / permissions."""
	frappe.set_user("Administrator")
	out: dict[str, Any] = {"ok": False, "skipped": False, "steps": {}}

	if not tender_name or not frappe.db.exists("Procurement Tender", tender_name):
		out["error"] = "missing_tender"
		return out

	# Re-entry after a prior successful seed (e.g. ``sws.run()`` then ``run_smoke_for_package_code``): tender
	# already has primary sample + WH-013 artefacts — only re-run hardening + assertions.
	td0 = frappe.get_doc("Procurement Tender", tender_name)
	n_existing_forms = len(td0.get("required_forms") or [])
	existing_snap = (
		frappe.db.get_value("Procurement Tender", tender_name, "works_hardening_snapshot_hash") or ""
	).strip()
	if n_existing_forms == EXPECTED_REQUIRED_FORMS_PRIMARY_SAMPLE and existing_snap:
		out["rerun_wh013_short_circuit"] = True
		out["officer_path_required_forms_count"] = EXPECTED_REQUIRED_FORMS_INTEGRATED_SEED
		out["required_forms_count"] = EXPECTED_REQUIRED_FORMS_PRIMARY_SAMPLE
		out["preview_html_length"] = len((td0.generated_tender_pack_html or "").strip())
		out["configuration_hash_present"] = bool((td0.configuration_hash or "").strip())
		out["doc3_section_28_forms_note"] = (
			"§28 '15 forms' = full primary sample_tender activation; integrated seed officer path = "
			f"{EXPECTED_REQUIRED_FORMS_INTEGRATED_SEED} without load_sample_tender."
		)
		try:
			hard_out = works_tender_hardening.run_works_tender_stage_hardening(tender_name)
		except Exception as exc:
			out["error"] = "hardening_exception"
			out["hardening_exception"] = str(exc)
			return out
		out["steps"] = {"run_works_tender_stage_hardening": hard_out}
		val = hard_out.get("validation") or {}
		out["hardening_critical_count"] = int(val.get("critical_count") or 0)
		out["works_hardening_status"] = val.get("status") or ""
		if out["hardening_critical_count"] != 0:
			out["error"] = "hardening_critical_findings"
			return out
		st = str(out["works_hardening_status"] or "").strip()
		if st in (HARDENING_STATUS_BLOCKED, HARDENING_STATUS_FAILED):
			out["error"] = "hardening_status_blocked_or_failed"
			return out
		if st not in ("Pass", "Warning"):
			out["error"] = "hardening_unexpected_status"
			out["hardening_unexpected_status"] = st
			return out
		if not hard_out.get("ok"):
			out["error"] = "hardening_envelope_not_ok"
			return out
		snap_h = (frappe.db.get_value("Procurement Tender", tender_name, "works_hardening_snapshot_hash") or "").strip()
		snap_j = frappe.db.get_value("Procurement Tender", tender_name, "works_hardening_snapshot_json") or ""
		out["hardening_snapshot_hash_present"] = bool(snap_h)
		out["hardening_snapshot_json_present"] = bool((snap_j or "").strip())
		if not out["hardening_snapshot_hash_present"] or not out["hardening_snapshot_json_present"]:
			out["error"] = "hardening_snapshot_missing"
			return out
		out["ok"] = True
		return out

	_ensure_two_smoke_lots(tender_name)
	out["steps"]["validate_1"] = procurement_tender_controller.validate_tender_configuration(tender_name)
	out["steps"]["generate_sample_boq"] = procurement_tender_controller.generate_sample_boq(tender_name)
	boq_ok = bool(out["steps"]["generate_sample_boq"].get("ok"))
	boq_n = int(out["steps"]["generate_sample_boq"].get("boq_row_count") or 0)
	if not boq_ok or boq_n != EXPECTED_BOQ_ROWS:
		out["error"] = "boq_step_failed"
		return out

	out["steps"]["validate_2"] = procurement_tender_controller.validate_tender_configuration(tender_name)
	v2 = out["steps"]["validate_2"]
	if not v2.get("ok"):
		out["error"] = "validation_blocked_after_boq"
		out["validation_status"] = v2.get("validation_status")
		return out

	out["steps"]["generate_required_forms"] = procurement_tender_controller.generate_required_forms(tender_name)
	gf = out["steps"]["generate_required_forms"]
	if gf.get("blocks_generation"):
		out["error"] = "required_forms_step_validation_blocked"
		out["validation_status"] = gf.get("validation_status")
		return out
	n_forms = int(gf.get("required_form_count") or 0)
	if n_forms != EXPECTED_REQUIRED_FORMS_INTEGRATED_SEED:
		out["error"] = "required_forms_count"
		out["required_form_count"] = n_forms
		out["expected"] = EXPECTED_REQUIRED_FORMS_INTEGRATED_SEED
		return out

	out["steps"]["generate_tender_pack_preview"] = procurement_tender_controller.generate_tender_pack_preview(
		tender_name
	)
	pr = out["steps"]["generate_tender_pack_preview"]
	if not pr.get("ok"):
		out["error"] = "preview_failed"
		return out

	td = frappe.get_doc("Procurement Tender", tender_name)
	html = (td.generated_tender_pack_html or "").strip()
	cfg_h = (td.configuration_hash or "").strip()
	out["preview_html_length"] = len(html)
	out["configuration_hash_present"] = bool(cfg_h)
	out["required_forms_count"] = n_forms
	out["doc3_section_28_forms_note"] = (
		"§28 '15 forms' = full primary sample_tender activation; integrated seed officer path = "
		f"{EXPECTED_REQUIRED_FORMS_INTEGRATED_SEED} without load_sample_tender."
	)
	if not (html and cfg_h):
		out["error"] = "preview_empty_or_no_configuration_hash"
		return out

	out["officer_path_required_forms_count"] = n_forms

	# Doc 5 §25 / WH-013 — full primary sample so hardening §18 checks match template (no Critical on seed).
	# Officer merge path alone only yields 8 required forms (doc 3 note); ``load_sample_tender`` aligns BoQ/lots/forms.
	out["steps"]["load_sample_tender_wh013"] = procurement_tender_controller.load_sample_tender(tender_name)
	ls = out["steps"]["load_sample_tender_wh013"]
	if not ls or not (ls.get("message") or "").strip():
		out["error"] = "load_sample_tender_wh013_unexpected_response"
		return out

	_stamp_seed_officer_audit_flags_after_sample(tender_name)

	out["steps"]["validate_after_sample_wh013"] = procurement_tender_controller.validate_tender_configuration(
		tender_name
	)
	v3 = out["steps"]["validate_after_sample_wh013"]
	if not v3.get("ok"):
		out["error"] = "validation_failed_after_sample_load_wh013"
		out["validation_status"] = v3.get("validation_status")
		return out

	out["steps"]["generate_required_forms_after_sample_wh013"] = (
		procurement_tender_controller.generate_required_forms(tender_name)
	)
	gf3 = out["steps"]["generate_required_forms_after_sample_wh013"]
	if gf3.get("blocks_generation"):
		out["error"] = "required_forms_blocked_after_sample_wh013"
		out["validation_status"] = gf3.get("validation_status")
		return out
	n_full = int(gf3.get("required_form_count") or 0)
	if n_full != EXPECTED_REQUIRED_FORMS_PRIMARY_SAMPLE:
		out["error"] = "required_forms_count_after_sample_wh013"
		out["required_form_count"] = n_full
		out["expected"] = EXPECTED_REQUIRED_FORMS_PRIMARY_SAMPLE
		return out

	out["steps"]["generate_tender_pack_preview_after_sample_wh013"] = (
		procurement_tender_controller.generate_tender_pack_preview(tender_name)
	)
	pr3 = out["steps"]["generate_tender_pack_preview_after_sample_wh013"]
	if not pr3.get("ok"):
		out["error"] = "preview_failed_after_sample_wh013"
		return out

	td2 = frappe.get_doc("Procurement Tender", tender_name)
	out["preview_html_length_after_sample_wh013"] = len((td2.generated_tender_pack_html or "").strip())
	out["required_forms_count"] = n_full

	# Doc 5 §25 / WH-013 — tender-stage hardening + snapshot (no Critical; snapshot persisted).
	try:
		hard_out = works_tender_hardening.run_works_tender_stage_hardening(tender_name)
	except Exception as exc:
		out["error"] = "hardening_exception"
		out["hardening_exception"] = str(exc)
		return out

	out["steps"]["run_works_tender_stage_hardening"] = hard_out
	val = hard_out.get("validation") or {}
	out["hardening_critical_count"] = int(val.get("critical_count") or 0)
	out["works_hardening_status"] = val.get("status") or ""

	if out["hardening_critical_count"] != 0:
		out["error"] = "hardening_critical_findings"
		return out

	st = str(out["works_hardening_status"] or "").strip()
	if st in (HARDENING_STATUS_BLOCKED, HARDENING_STATUS_FAILED):
		out["error"] = "hardening_status_blocked_or_failed"
		return out

	if st not in ("Pass", "Warning"):
		out["error"] = "hardening_unexpected_status"
		out["hardening_unexpected_status"] = st
		return out

	if not hard_out.get("ok"):
		out["error"] = "hardening_envelope_not_ok"
		return out

	snap_h = (frappe.db.get_value("Procurement Tender", tender_name, "works_hardening_snapshot_hash") or "").strip()
	snap_j = frappe.db.get_value("Procurement Tender", tender_name, "works_hardening_snapshot_json") or ""
	out["hardening_snapshot_hash_present"] = bool(snap_h)
	out["hardening_snapshot_json_present"] = bool((snap_j or "").strip())
	if not out["hardening_snapshot_hash_present"] or not out["hardening_snapshot_json_present"]:
		out["error"] = "hardening_snapshot_missing"
		return out

	out["ok"] = True
	return out


def run_smoke_for_package_code(package_code: str = "PKG-MOH-2026-001") -> dict[str, Any]:
	"""``bench execute`` helper: resolve tender from package code and run §29 smoke."""
	frappe.only_for(("System Manager", "Administrator"))
	pkg = frappe.db.get_value("Procurement Package", {"package_code": package_code}, "name")
	if not pkg:
		return {"ok": False, "error": "package_not_found"}
	tn = frappe.db.get_value("Procurement Tender", {"procurement_package": pkg}, "name")
	if not tn:
		return {"ok": False, "error": "tender_not_found"}
	return {"ok": True, "tender": tn, "section_29_smoke": run_doc3_section_29_smoke(tn)}
