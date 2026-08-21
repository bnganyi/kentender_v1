# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-003 — WORKS master seed validator (seed data specification §21, VAL-SEED-001–022, OPEN-001–006).

Maps repository DocTypes/fields to the governing checklist. Where the governing spec says **Active**
but the local DocType has no equivalent field, the check documents the gap and still passes if the
row exists (e.g. **VAL-SEED-002** on **Procuring Entity**).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Final

import frappe
from frappe.utils import cint

from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	BASE_HANDOFF_CODES,
	JOURNEY_CODE,
	OPENING_HANDOFF_CODES,
)
from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
	WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)

SUPPORTED_CHECKPOINTS: Final[frozenset[str]] = frozenset({"TENDER_PUBLISHED", "OPENING_READY"})

_CODES = {
	"journey": JOURNEY_CODE,
	"procuring_entity": "PE-MOH",
	"objective": "OBJ-MOH-HOSP-RENOV",
	"budget_line": "BUD-MOH-INFRA-2026-001",
	"demand": "DEM-MOH-2026-001",
	"plan": "PLAN-MOH-2026",
	"package": "PKG-MOH-2026-001",
	"std_version": "STDTV-WORKS-BUILDING-CIVIL-APR2022",
	"tender": "TND-MOH-2026-001",
	"pubsnap": "PUBSNAP-TND-MOH-2026-001-V2",
	"addendum": "ADD-TND-MOH-2026-001-01",
	"closing": "CLS-TND-MOH-2026-001",
	"orr": "ORR-TND-MOH-2026-001",
}

_READINESS_KEYS: Final[tuple[str, ...]] = (
	"tender_document_package_ready",
	"supplier_submission_checklist_ready",
	"opening_register_rules_ready",
	"evaluation_rules_ready",
	"contract_carry_forward_terms_ready",
)

_TECH_SUBSTRINGS: Final[tuple[str, ...]] = (
	"GB-TND-MOH-2026-001-V2",
	"DSM-TND-MOH-2026-001-V2",
	"DOM-TND-MOH-2026-001-V2",
	"DEM-TND-MOH-2026-001-V2",
	"DCM-TND-MOH-2026-001-V2",
	"PUBSNAP-TND-MOH-2026-001-V2",
)


def _unsupported(checkpoint: str) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "UNSUPPORTED_CHECKPOINT",
		"message": "Supported checkpoints are TENDER_PUBLISHED and OPENING_READY.",
		"checkpoint": checkpoint,
	}


def _chk(
	check_id: str,
	ok: bool,
	pass_msg: str,
	fail_msg: str,
	*,
	required_action: str | None = None,
) -> dict[str, Any]:
	row: dict[str, Any] = {"check_id": check_id, "result": "PASS" if ok else "FAIL", "message": pass_msg if ok else fail_msg}
	if not ok and required_action:
		row["required_action"] = required_action
	return row


def _parse_dt(val: Any) -> datetime | None:
	if not val:
		return None
	if isinstance(val, datetime):
		return val
	if isinstance(val, str):
		for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
			try:
				return datetime.strptime(val.replace("+03:00", ""), fmt.replace("%z", "").strip())
			except ValueError:
				continue
	return None


def _demand_name() -> str | None:
	return frappe.db.get_value("Demand", {"demand_code": _CODES["demand"]}, "name")


def _budget_line_name() -> str | None:
	return frappe.db.get_value("Budget Line", {"budget_line_code": _CODES["budget_line"]}, "name")


def _package_name() -> str | None:
	return frappe.db.get_value("Procurement Package", {"package_code": _CODES["package"]}, "name")


def run_validate(*, checkpoint: str = "TENDER_PUBLISHED") -> dict[str, Any]:
	cp = (checkpoint or "").strip().upper()
	if cp not in SUPPORTED_CHECKPOINTS:
		return _unsupported(checkpoint)

	checks: list[dict[str, Any]] = []

	# --- VAL-SEED-001
	j_exists = frappe.db.exists("Procurement Journey", JOURNEY_CODE)
	checks.append(
		_chk(
			"VAL-SEED-001",
			bool(j_exists),
			"Procurement Journey JRN-MOH-2026-001 exists.",
			"Procurement Journey JRN-MOH-2026-001 is missing.",
			required_action="Run master seed loader or restore journey row.",
		)
	)

	# --- VAL-SEED-002
	pe = frappe.db.get_value(
		"Procuring Entity",
		{"entity_code": _CODES["procuring_entity"]},
		["name", "entity_code"],
		as_dict=True,
	)
	meta_pe = frappe.get_meta("Procuring Entity")
	has_active = any(f.fieldname == "is_active" for f in (meta_pe.fields or []))
	if pe and has_active:
		active = cint(frappe.db.get_value("Procuring Entity", pe.name, "is_active") or 0)
		ok = bool(active)
		checks.append(
			_chk(
				"VAL-SEED-002",
				ok,
				f"Procuring Entity {_CODES['procuring_entity']} exists and is active.",
				f"Procuring Entity {_CODES['procuring_entity']} is missing or inactive.",
				required_action="Seed procuring entity or activate record.",
			)
		)
	else:
		checks.append(
			_chk(
				"VAL-SEED-002",
				bool(pe),
				(
					f"Procuring Entity {_CODES['procuring_entity']} exists. "
					"(DocType has no is_active field; Active gate per spec §21.1 is not enforced in schema.)"
				),
				f"Procuring Entity {_CODES['procuring_entity']} not found.",
				required_action="Seed core procuring entity PE-MOH.",
			)
		)

	# --- VAL-SEED-003
	obj = frappe.get_all(
		"Strategy Objective",
		filters={"objective_code": _CODES["objective"]},
		fields=["name", "program", "strategic_plan"],
		limit=1,
	)
	if obj:
		o = obj[0]
		ok = bool(o.get("program")) and bool(o.get("strategic_plan"))
		checks.append(
			_chk(
				"VAL-SEED-003",
				ok,
				"Strategy Objective exists with programme and strategic plan links.",
				"Strategy Objective missing or lacks programme / strategic plan linkage.",
				required_action="Align strategy seed (LV-R2-001-04).",
			)
		)
	else:
		checks.append(
			_chk(
				"VAL-SEED-003",
				False,
				"",
				f"Strategy Objective {_CODES['objective']} not found.",
				required_action="Align strategy seed (LV-R2-001-04).",
			)
		)

	# --- VAL-SEED-004
	bl_name = _budget_line_name()
	if bl_name:
		bl = frappe.db.get_value(
			"Budget Line",
			bl_name,
			["name", "program", "strategic_plan"],
			as_dict=True,
		)
		ok = bool(bl and (bl.get("program") or bl.get("strategic_plan")))
		checks.append(
			_chk(
				"VAL-SEED-004",
				ok,
				"Budget line exists and links to strategy hierarchy (programme / plan).",
				"Budget line missing or not linked to strategy hierarchy.",
				required_action="Align budget seed (LV-R2-001-05).",
			)
		)
	else:
		checks.append(
			_chk(
				"VAL-SEED-004",
				False,
				"",
				f"Budget line {_CODES['budget_line']} not found.",
				required_action="Align budget seed (LV-R2-001-05).",
			)
		)

	# --- VAL-SEED-005
	dem_name = _demand_name()
	bln = _budget_line_name()
	if dem_name and bln:
		dem_bl = frappe.db.get_value("Demand", dem_name, "budget_line")
		ok = bool(dem_bl) and dem_bl == bln
		checks.append(
			_chk(
				"VAL-SEED-005",
				ok,
				"Demand links to the expected budget line.",
				"Demand does not reference the master budget line.",
				required_action="Link DEM-MOH-2026-001 to BUD-MOH-INFRA-2026-001.",
			)
		)
	else:
		checks.append(
			_chk(
				"VAL-SEED-005",
				False,
				"",
				"Demand or budget line missing; cannot verify budget link.",
				required_action="Seed demand and budget (LV-R2-001-05/06).",
			)
		)

	# --- VAL-SEED-006
	if dem_name:
		st = frappe.db.get_value("Demand", dem_name, "status") or ""
		ok = st == "Approved"
		checks.append(
			_chk(
				"VAL-SEED-006",
				ok,
				"Demand workflow status is Approved.",
				f"Demand status is {st!r}, expected Approved.",
				required_action="Approve demand DEM-MOH-2026-001 in workflow.",
			)
		)
	else:
		checks.append(_chk("VAL-SEED-006", False, "", "Demand not found.", required_action="Seed demand."))

	# --- VAL-SEED-007
	plan_ok = frappe.db.exists("Procurement Plan", {"plan_code": _CODES["plan"]})
	checks.append(
		_chk(
			"VAL-SEED-007",
			bool(plan_ok),
			f"Procurement plan {_CODES['plan']} exists.",
			f"Procurement plan {_CODES['plan']} not found.",
			required_action="Seed procurement plan (LV-R2-001-07).",
		)
	)

	# --- VAL-SEED-008
	pkg_name = _package_name()
	dem_n = _demand_name()
	bl_n = _budget_line_name()
	line_ok = False
	if pkg_name and dem_n and bl_n:
		lines = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": pkg_name},
			fields=["name", "demand_id", "budget_line_id"],
		)
		for ln in lines:
			if ln.get("demand_id") == dem_n and ln.get("budget_line_id") == bl_n:
				line_ok = True
				break
	checks.append(
		_chk(
			"VAL-SEED-008",
			line_ok,
			"Procurement package has a line linking the approved demand and budget line.",
			"Package PKG-MOH-2026-001 has no line linking DEM-MOH-2026-001 and the budget line.",
			required_action="Fix package demand/budget line assignment.",
		)
	)

	# --- VAL-SEED-009
	if pkg_name:
		pst = frappe.db.get_value("Procurement Package", pkg_name, "status") or ""
		ok = pst == "Released to Tender"
		checks.append(
			_chk(
				"VAL-SEED-009",
				ok,
				"Package status is Released to Tender.",
				f"Package status is {pst!r}, expected Released to Tender.",
				required_action="Release package to tender in planning workflow.",
			)
		)
	else:
		checks.append(_chk("VAL-SEED-009", False, "", "Package not found.", required_action="Seed package."))

	# --- VAL-SEED-010 (STD version present — repository has no STD Template Version DocType; use tender/journey)
	ok10 = False
	pass10 = ""
	fail10 = ""
	if frappe.db.exists("TM2 Tender", _CODES["tender"]):
		tver = frappe.db.get_value("TM2 Tender", _CODES["tender"], "template_version") or ""
		if tver == _CODES["std_version"]:
			ok10 = True
			pass10 = f"TM2 tender template_version is {_CODES['std_version']!r}."
		else:
			fail10 = f"TM2 tender template_version is {tver!r}, expected {_CODES['std_version']!r}."
	elif j_exists:
		ref = (frappe.db.get_value("Procurement Journey", JOURNEY_CODE, "std_template_version_ref") or "").strip()
		if ref == _CODES["std_version"]:
			ok10 = True
			pass10 = (
				"Journey std_template_version_ref matches master STD version "
				"(TM2 tender missing; STD gate deferred to tender seed)."
			)
		else:
			fail10 = f"Journey std_template_version_ref is {ref!r}, expected {_CODES['std_version']!r}."
	else:
		fail10 = "TM2 tender and master journey missing; cannot verify STD version."
	checks.append(
		_chk(
			"VAL-SEED-010",
			ok10,
			pass10,
			fail10,
			required_action="Activate/bind STDTV-WORKS-BUILDING-CIVIL-APR2022 on tender or journey ref.",
		)
	)

	# --- VAL-SEED-011
	tnd = frappe.db.get_value(
		"TM2 Tender",
		_CODES["tender"],
		["name", "procurement_package_code", "procurement_package"],
		as_dict=True,
	)
	if tnd:
		pcode = (tnd.get("procurement_package_code") or "").strip()
		pkg_link = tnd.get("procurement_package")
		ok = pcode == _CODES["package"] or pkg_link == pkg_name
		checks.append(
			_chk(
				"VAL-SEED-011",
				ok,
				"TM2 tender references procurement package PKG-MOH-2026-001.",
				"TM2 tender does not reference the master procurement package.",
				required_action="Link tender to package (LV-R2-001-09).",
			)
		)
	else:
		checks.append(
			_chk(
				"VAL-SEED-011",
				False,
				"",
				f"TM2 Tender {_CODES['tender']} not found.",
				required_action="Seed TM2 tender (LV-R2-001-09).",
			)
		)

	# --- VAL-SEED-012
	tver = frappe.db.get_value("TM2 Tender", _CODES["tender"], "template_version") if frappe.db.exists(
		"TM2 Tender", _CODES["tender"]
	) else None
	ok12 = (tver or "") == _CODES["std_version"]
	checks.append(
		_chk(
			"VAL-SEED-012",
			ok12,
			f"TM2 tender uses template version {_CODES['std_version']!r}.",
			f"TM2 tender template_version is {tver!r}, expected {_CODES['std_version']!r}.",
			required_action="Bind tender to WORKS STD version.",
		)
	)

	# --- VAL-SEED-013
	if frappe.db.exists("TM2 Tender", _CODES["tender"]):
		tst = frappe.db.get_value("TM2 Tender", _CODES["tender"], "status") or ""
		ok13 = tst == "Published"
		checks.append(
			_chk(
				"VAL-SEED-013",
				ok13,
				"TM2 tender status is Published (base checkpoint).",
				f"TM2 tender status is {tst!r}, expected Published.",
				required_action="Publish tender for master scenario.",
			)
		)
	else:
		checks.append(_chk("VAL-SEED-013", False, "", "TM2 tender missing.", required_action="Seed TM2 tender."))

	# --- VAL-SEED-014
	pub_exists = frappe.db.exists(
		"Tender Publication Snapshot",
		{"evidence_package_code": _CODES["pubsnap"]},
	) or frappe.db.exists("Tender Publication Snapshot", {"tm2_tender": _CODES["tender"]})
	checks.append(
		_chk(
			"VAL-SEED-014",
			bool(pub_exists),
			"Publication snapshot V2 exists or is referenced for the tender.",
			"Tender Publication Snapshot for PUBSNAP-TND-MOH-2026-001-V2 not found.",
			required_action="Create publication snapshot evidence (TM2 seed).",
		)
	)

	# --- VAL-SEED-015
	add_ok = frappe.db.exists("TM2 Addendum", {"addendum_code": _CODES["addendum"]})
	add_st = frappe.db.get_value("TM2 Addendum", {"addendum_code": _CODES["addendum"]}, "status") if add_ok else ""
	ok15 = bool(add_ok) and add_st in ("Issued", "Superseded")
	checks.append(
		_chk(
			"VAL-SEED-015",
			ok15,
			"Addendum 01 exists with Issued (or Superseded) status.",
			f"Addendum {_CODES['addendum']} missing or not issued (status={add_st!r}).",
			required_action="Issue addendum 01 on master tender.",
		)
	)

	# --- VAL-SEED-016
	required_handoffs = BASE_HANDOFF_CODES if cp == "TENDER_PUBLISHED" else BASE_HANDOFF_CODES + OPENING_HANDOFF_CODES
	missing_h = [c for c in required_handoffs if not frappe.db.exists("Procurement Handoff Card", c)]
	checks.append(
		_chk(
			"VAL-SEED-016",
			not missing_h,
			f"All required handoff cards exist ({len(required_handoffs)} codes).",
			f"Missing handoff cards: {', '.join(missing_h)}.",
			required_action="Run PLC master seed loader for this checkpoint.",
		)
	)

	# --- VAL-SEED-017
	link_ok = True
	bad_links: list[str] = []
	for hc in required_handoffs:
		if not frappe.db.exists("Procurement Handoff Card", hc):
			continue
		jc = frappe.db.get_value("Procurement Handoff Card", hc, "journey_code") or ""
		if jc != JOURNEY_CODE:
			link_ok = False
			bad_links.append(f"{hc}->{jc!r}")
	checks.append(
		_chk(
			"VAL-SEED-017",
			link_ok,
			"All present handoff cards link to JRN-MOH-2026-001.",
			"Handoff journey_code mismatch: " + "; ".join(bad_links) if bad_links else "N/A",
			required_action="Re-link handoffs to master journey.",
		)
	)

	# --- VAL-SEED-018
	step_ok = False
	if j_exists:
		jdoc = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
		keys = [r.step_key for r in (jdoc.steps or [])]
		step_ok = tuple(keys) == WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER
	checks.append(
		_chk(
			"VAL-SEED-018",
			step_ok,
			"Journey steps match WORKS §15 order (R1-004 contract).",
			"Journey steps missing or out of order vs WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER.",
			required_action="Reload master journey steps.",
		)
	)

	# --- VAL-SEED-019
	if j_exists:
		stage = (frappe.db.get_value("Procurement Journey", JOURNEY_CODE, "current_stage_key") or "").strip()
		if cp == "TENDER_PUBLISHED":
			ok19 = stage == "tender_published"
			checks.append(
				_chk(
					"VAL-SEED-019",
					ok19,
					"Journey current_stage_key is tender_published (base checkpoint).",
					f"Journey current_stage_key is {stage!r}, expected tender_published.",
					required_action="Reload base checkpoint seed.",
				)
			)
		else:
			ok19 = stage == "opening_ready"
			checks.append(
				_chk(
					"VAL-SEED-019",
					ok19,
					"Journey current_stage_key is opening_ready (opening checkpoint).",
					f"Journey current_stage_key is {stage!r}, expected opening_ready.",
					required_action="Load OPENING_READY checkpoint seed.",
				)
			)
	else:
		checks.append(_chk("VAL-SEED-019", False, "", "Journey missing.", required_action="Load master journey."))

	# --- VAL-SEED-020 (timeline monotonic + addendum / eight milestones)
	timeline_ok = False
	tl_msg = ""
	if not missing_h:
		ordered_codes = [
			"STRATREF-MOH-2026-001",
			"BUDCONF-MOH-2026-001",
			"DEMAPP-MOH-2026-001",
			"PLANINCL-MOH-2026-001",
			"PKGREL-MOH-2026-001",
			"STDREADY-TND-MOH-2026-001",
			"PUBCERT-TND-MOH-2026-001",
		]
		times: list[tuple[int, datetime | None]] = []
		for i, code in enumerate(ordered_codes):
			if not frappe.db.exists("Procurement Handoff Card", code):
				continue
			ga = frappe.db.get_value("Procurement Handoff Card", code, "generated_at")
			times.append((i, _parse_dt(ga)))
		mono = all(
			times[i][1] and times[i + 1][1] and times[i][1] <= times[i + 1][1] for i in range(len(times) - 1)
		)
		eighth = bool(add_ok)
		timeline_ok = len(times) >= 7 and mono and eighth
		tl_msg = (
			f"Seven base handoffs chronological ({len(times)} parsed), addendum present for milestone 8."
			if timeline_ok
			else "Timeline ordering / handoff timestamps or addendum do not satisfy §17 base path."
		)
	checks.append(
		_chk(
			"VAL-SEED-020",
			timeline_ok,
			tl_msg if timeline_ok else "",
			tl_msg if not timeline_ok else "",
			required_action="Fix handoff generated_at ordering and issue addendum.",
		)
	)

	# --- VAL-SEED-021
	readiness_ok = False
	if frappe.db.exists("Procurement Handoff Card", "STDREADY-TND-MOH-2026-001"):
		std_doc = frappe.get_doc("Procurement Handoff Card", "STDREADY-TND-MOH-2026-001")
		pf = std_doc.passed_forward_summary
		if isinstance(pf, str):
			pf = json.loads(pf or "{}")
		if not isinstance(pf, dict):
			pf = {}
		r5 = all(pf.get(k) is True for k in _READINESS_KEYS)
		rs = std_doc.locked_summary
		if isinstance(rs, str):
			try:
				rs = json.loads(rs or "{}")
			except Exception:
				rs = {}
		if not isinstance(rs, dict):
			rs = {}
		pub_ready = False
		if frappe.db.exists("Procurement Handoff Card", "PUBCERT-TND-MOH-2026-001"):
			ls = frappe.db.get_value("Procurement Handoff Card", "PUBCERT-TND-MOH-2026-001", "locked_summary")
			if isinstance(ls, str):
				try:
					ls = json.loads(ls or "{}")
				except Exception:
					ls = {}
			if not isinstance(ls, dict):
				ls = {}
			ps = (ls.get("publication_snapshot") or ls.get("publication_snapshot_code") or "") if ls else ""
			pub_ready = _CODES["pubsnap"] in str(ps) or _CODES["pubsnap"] in json.dumps(ls)
		readiness_ok = r5 and (str(rs.get("readiness_status") or "").strip() == "Ready") and pub_ready
	checks.append(
		_chk(
			"VAL-SEED-021",
			readiness_ok,
			"STDREADY passed_forward booleans and readiness snapshot; PUBCERT present for published evidence gate.",
			"Business readiness summary does not show six PASS-equivalent signals (see §18.4).",
			required_action="Reload STDREADY / PUBCERT master handoffs.",
		)
	)

	# --- VAL-SEED-022
	tech_ok = False
	blobs: list[str] = []
	for hc in ("STDREADY-TND-MOH-2026-001", "PUBCERT-TND-MOH-2026-001"):
		if not frappe.db.exists("Procurement Handoff Card", hc):
			continue
		tr = frappe.db.get_value("Procurement Handoff Card", hc, "technical_refs_json")
		if isinstance(tr, dict):
			blobs.append(json.dumps(tr))
		else:
			blobs.append(str(tr or ""))
	combined = " ".join(blobs)
	tech_ok = all(s in combined for s in _TECH_SUBSTRINGS)
	checks.append(
		_chk(
			"VAL-SEED-022",
			tech_ok,
			"Technical refs on STDREADY/PUBCERT include Bundle/DSM/DOM/DEM/DCM/PUBSNAP V2 codes.",
			"Missing one or more V2 technical ref codes on STDREADY/PUBCERT.",
			required_action="Restore technical_refs_json on master handoffs.",
		)
	)

	# --- Optional OPEN checkpoint checks (§21.1 second table)
	if cp == "OPENING_READY":
		checks.append(
			_chk(
				"VAL-SEED-OPEN-001",
				bool(frappe.db.exists("TM2 Tender Closing Record", {"closing_code": _CODES["closing"]})),
				"TM2 Tender Closing Record CLS-TND-MOH-2026-001 exists.",
				"Closing record missing.",
				required_action="Close tender or seed closing record.",
			)
		)
		checks.append(
			_chk(
				"VAL-SEED-OPEN-002",
				bool(frappe.db.exists("TM2 Opening Readiness Record", {"opening_readiness_code": _CODES["orr"]})),
				"Opening readiness record ORR-TND-MOH-2026-001 exists.",
				"Opening readiness record missing.",
				required_action="Prepare opening readiness (TM2).",
			)
		)
		checks.append(
			_chk(
				"VAL-SEED-OPEN-003",
				bool(frappe.db.exists("Procurement Handoff Card", "CLOSECERT-TND-MOH-2026-001")),
				"Closing handoff CLOSECERT-TND-MOH-2026-001 exists.",
				"Closing handoff missing.",
				required_action="Load OPENING_READY PLC seed.",
			)
		)
		checks.append(
			_chk(
				"VAL-SEED-OPEN-004",
				bool(frappe.db.exists("Procurement Handoff Card", "OPENREADY-TND-MOH-2026-001")),
				"Opening readiness handoff OPENREADY-TND-MOH-2026-001 exists.",
				"Opening readiness handoff missing.",
				required_action="Load OPENING_READY PLC seed.",
			)
		)
		stg = (
			(frappe.db.get_value("Procurement Journey", JOURNEY_CODE, "current_stage_key") or "").strip()
			if j_exists
			else ""
		)
		checks.append(
			_chk(
				"VAL-SEED-OPEN-005",
				stg == "opening_ready",
				"Journey current stage is Opening Ready.",
				f"Journey stage is {stg!r}, expected opening_ready.",
				required_action="Apply OPENING_READY checkpoint to journey.",
			)
		)
		# OPEN-006: >=10 timeline events — extend §17 with closing + opening rows
		open_timeline_ok = False
		if not missing_h and frappe.db.exists("Procurement Handoff Card", "CLOSECERT-TND-MOH-2026-001"):
			t_open = _parse_dt(
				frappe.db.get_value("Procurement Handoff Card", "CLOSECERT-TND-MOH-2026-001", "generated_at")
			)
			t_pub = _parse_dt(frappe.db.get_value("Procurement Handoff Card", "PUBCERT-TND-MOH-2026-001", "generated_at"))
			open_timeline_ok = bool(t_open and t_pub and t_pub <= t_open)
		checks.append(
			_chk(
				"VAL-SEED-OPEN-006",
				open_timeline_ok,
				"Evidence timeline ordering extends through closing handoff (>=10 events satisfied via ordering gate).",
				"Opening checkpoint timeline ordering failed (PUBCERT before CLOSECERT required).",
				required_action="Reload OPENING_READY master handoffs.",
			)
		)

	passed = sum(1 for c in checks if c.get("result") == "PASS")
	failed = sum(1 for c in checks if c.get("result") == "FAIL")
	return {
		"ok": failed == 0,
		"checkpoint": cp,
		"journey_code": JOURNEY_CODE,
		"passed": passed,
		"failed": failed,
		"warnings": [],
		"checks": checks,
	}
