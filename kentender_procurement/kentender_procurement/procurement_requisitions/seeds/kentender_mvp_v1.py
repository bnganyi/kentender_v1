# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §16 — the deterministic Ministry of Health Requisitions
seed, chained after Procurement Planning's own §14 pack (implementation
plan Decision D7: Requisitions is not a canonical seed stage this cycle;
this module reuses Planning's live MOH Annual Plan rather than building a
second world).

**Decision D10 (this module).** §16.4 names six lifecycle fixtures plus a
stopped Version and a Planning correction request, "each its own fixture a
test can load independently." Two constraints close off building seven
concurrent Requisitions: REQ_PLAN_INELIGIBLE / C2 enforce at most one
non-terminal Requisition per Plan Item, and — confirmed live while building
this module — the single-department item ("National digital health
infrastructure upgrade") is classified Non-consulting services in
Planning's own seed, which `compatibility.first_failure` refuses outright
(REQ_PRODUCT_UNSUPPORTED) before a Draft can even be prepared; the
two-department combined item is the ONLY Goods-classified, IT-equipment-
eligible Plan Item the canonical MOH world carries. (Adding a second
eligible Plan Item would also require extending Planning's own governed
Annual Plan, breaking Planning's own `validate_planning_seed()`
— `active.two_items`, `active.value_130m`.)

So, mirroring Planning's own §14.10 "isolated profiles" pattern, every
fixture in §16.4 shares the one eligible combined item, mutually exclusive
with each other exactly as Planning's own profiles are mutually exclusive
with its integrated baseline:

- `upsert_requisitions_base()` is the one fixture `run_kentender_mvp_v1`
  builds by default, matching §16.4's exact Authorised timeline (fixture
  4), extendable in place to the consumed handoff (fixture 6) via the
  separate, additive `seed_consumed_handoff()` (consumption is a one-way
  audit fact, never reversed, so this is not a "profile" in the
  mutually-exclusive sense — it only ever adds);
- `seed_draft_profile()` / `seed_department_task_profile()` /
  `seed_procurement_task_profile()` / `seed_returned_profile()` /
  `seed_upstream_correction_profile()` each tear the fixture down (revoking
  first through the real command if it had reached Authorised and is still
  unconsumed) and rebuild to their own named state — on demand, never
  called by `run_kentender_mvp_v1` itself.

**Technical-row label deviation (recorded, not fought).** §16.3's table
shows Memory/Storage capacity/Storage type scoped to "Business laptops";
the real, tested `_propose_baseline_for_item` widens every baseline row —
valued or not — to "All items" the moment a second item's identical
proposal would duplicate it (the fix that closed the 22-row duplication
defect earlier this build). This seed does not fight that tested behaviour
to chase the illustrative label; the eleven confirmed rows carry the exact
characteristics and values §16.3 lists, all under "All items" scope. See
FOLLOW_UPS.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe
from frappe.utils import cstr, flt

NS = "KENTENDER_MVP_1_R1_REQ"
FY = "2027-2028"

AUTHOR = "grace.wanjiku@moh.example.test"
HOD = "peter.kimani@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"

DHI_NAME = "Digital Health"
HRMD_NAME = "Human Resources Management and Development"

SINGLE_ITEM_TITLE = "National digital health infrastructure upgrade"
COMBINED_ITEM_TITLE = "Clinical training and deployment laptops for digital health rollout"
BL_HWD = "MOH-BL-HWD-2027"
DELIVERY_LOCATION = "Ministry of Health Headquarters, Afya House, Nairobi"

TENDER = "TND-MOH-2027-033"
TENDER_VERSION = "TND-MOH-2027-033-V1"
TEMPLATE_KEY = "IT Equipment — Open Tender"
TEMPLATE_VERSION = "v1.1"

# §16.4's exact fixture-4 timeline, stored as UTC equivalents of the stated
# EAT instants (read models render EAT).
CLOCK = {
	"draft_opened": "2027-03-01 06:00:00",  # 1 Mar 2027, 09:00 EAT
	"steps_completed": "2027-03-01 08:00:00",  # 1 Mar 2027, 11:00 EAT
	"sent_for_department_approval": "2027-03-01 08:05:00",  # 1 Mar 2027, 11:05 EAT
	"submitted_to_procurement": "2027-03-08 06:00:00",  # 8 Mar 2027, 09:00 EAT
	"authorised": "2027-03-15 07:00:00",  # 15 Mar 2027, 10:00 EAT
	"consumed": "2027-03-20 06:00:00",  # 20 Mar 2027, 09:00 EAT
}

# §13.7's eleven confirmed rows beyond the five auto-proposed baseline
# characteristics (electrical_compatibility, new_unused_equipment, memory,
# storage_capacity, storage_type — see the module docstring's label note).
_MANUAL_TECHNICAL_ROWS = (
	{"characteristic_key": "display_size", "value": 14.0},
	{"characteristic_key": "battery_runtime", "value": 8},
	{"characteristic_key": "processor_requirement", "value": "64-bit business-class processor, minimum 10 cores or equivalent benchmark"},
	{"characteristic_key": "operating_system_compatibility", "value": "Approved organisational Windows environment"},
	{"characteristic_key": "network_connectivity", "value": ["Wi-Fi 6", "Bluetooth 5 or later"]},
	{
		"characteristic_key": "required_ports",
		"value": [
			{"port_type": "USB-C", "minimum_count": 2},
			{"port_type": "USB-A", "minimum_count": 2},
			{"port_type": "HDMI", "minimum_count": 1},
		],
	},
)

_ACCEPTANCE_ROWS = (
	{"check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"},
	{"check_type": "Physical condition", "pass_condition": "No visible damage and all listed accessories are present", "evidence_type": "Inspection record"},
	{"check_type": "Required specification", "pass_condition": "Every delivered unit complies with all mandatory technical rows", "evidence_type": "Inspection record"},
	{"check_type": "Functional test", "pass_condition": "Each device powers on and completes the agreed basic functional test", "evidence_type": "Test result"},
	{"check_type": "Documents received", "pass_condition": "Warranty and delivery documents are received and verified", "evidence_type": "Certificate"},
)

_VALUE_LESS_BASELINE_DEFAULTS = {"memory": 16, "storage_capacity": 512}


@contextmanager
def _as(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


def _key(step: str) -> str:
	return f"req-seed:{step}"


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Procurement Requisitions seed fixtures are test/demo data. Enable "
		"developer_mode or allow_tests on this site before building them."
	)


def _unit_for(user: str, role: str, unit_name: str) -> str:
	for unit in frappe.get_all(
		"User Responsibility Assignment", filters={"user": user, "business_role": role, "status": "Enabled"}, pluck="organisation_unit",
	):
		if unit and frappe.db.get_value("Organisation Unit", unit, "unit_name") == unit_name:
			return unit
	return ""


def _plan_item_id(title: str) -> str:
	plan_name = frappe.db.get_value("Annual Plan", {"fiscal_year": FY}, "name")
	if not plan_name:
		return ""
	versions = frappe.get_all("Annual Plan Version", filters={"annual_plan": plan_name}, pluck="name")
	return cstr(frappe.db.get_value("Annual Plan Item", {"plan_version": ("in", versions or ("",)), "title": title}, "plan_item_id"))


def verify_prerequisites() -> dict[str, str]:
	"""§16.1 — every authoritative prerequisite present and usable, or one
	loud failure naming exactly what is absent. Nothing is invented."""
	missing: list[str] = []

	def need(label: str, ok) -> None:
		if not ok:
			missing.append(label)

	need(f"Fiscal Year {FY}", frappe.db.exists("Fiscal Year", FY))
	dhi = _unit_for(AUTHOR, "Departmental Author", DHI_NAME)
	hrmd = _unit_for(AUTHOR, "Departmental Author", HRMD_NAME)
	need(f"Grace's Departmental Author assignment in '{DHI_NAME}'", dhi)
	need(f"Grace's Departmental Author assignment in '{HRMD_NAME}'", hrmd)
	need(f"Peter's Head of User Department assignment in '{DHI_NAME}'", _unit_for(HOD, "Head of User Department", DHI_NAME))
	need(f"Peter's Head of User Department assignment in '{HRMD_NAME}'", _unit_for(HOD, "Head of User Department", HRMD_NAME))
	need("Charles Mutiso holds Head of Procurement Function", frappe.db.exists("User Responsibility Assignment", {"user": HOPF, "business_role": "Head of Procurement Function", "status": "Enabled"}))
	need("Naomi Chebet holds Auditor", frappe.db.exists("User Responsibility Assignment", {"user": AUDITOR, "business_role": "Auditor", "status": "Enabled"}))
	need(f"Delivery Location '{DELIVERY_LOCATION}'", frappe.db.get_value("Delivery Location", DELIVERY_LOCATION, "status") == "Active")
	need(f"Procurement Budget Line {BL_HWD}", frappe.db.exists("Procurement Budget Line", {"generated_reference": BL_HWD}))
	single_item = _plan_item_id(SINGLE_ITEM_TITLE)
	combined_item = _plan_item_id(COMBINED_ITEM_TITLE)
	need(f"Active Plan Item '{SINGLE_ITEM_TITLE}' (run make seed-kentender-mvp-v1 through Planning first)", single_item)
	need(f"Active Plan Item '{COMBINED_ITEM_TITLE}' (run make seed-kentender-mvp-v1 through Planning first)", combined_item)
	if missing:
		frappe.throw(
			"REQ §16 seed prerequisites are absent or differ — seeds never invent "
			"a substitute. Missing: " + "; ".join(missing)
		)
	return {"dhi": dhi, "hrmd": hrmd, "single_item": single_item, "combined_item": combined_item}


# --- shared package-building sequence (§13.5-13.9) ---------------------------


def _build_item_package(requisition: str, item_specs: list[dict[str, Any]]) -> None:
	"""§13.6-13.8 — one Business-laptops item row per spec, all eleven
	confirmed technical rows, warranty/support and the five acceptance rows,
	driven entirely through `draft_commands` (never a direct table write).
	`item_specs` order matches the Requisition's own drawdown lines."""
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	root = frappe.get_doc("Procurement Requisition", requisition)
	version = frappe.get_doc("Requisition Version", root.current_version)
	lines = sorted(version.drawdown_lines, key=lambda r: r.drawdown_line_id)
	if len(lines) != len(item_specs):
		frappe.throw(f"Expected {len(item_specs)} drawdown line(s) on {requisition}, found {len(lines)}.")

	record_version = 0
	package_version = None
	for line, spec in zip(lines, item_specs):
		added = cmd.add_requisition_item(
			requisition=requisition,
			values={
				"plan_item_line_id": line.drawdown_line_id, "equipment_category": "Laptop", "item_name": "Business laptops",
				"quantity": spec["quantity"], "intended_use": spec["intended_use"],
				"delivery_location": DELIVERY_LOCATION, "latest_delivery_date": "2027-09-30",
			},
			expected_record_version=record_version, idempotency_key=_key(f"{requisition}:item-{line.drawdown_line_id}"),
		)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", added["package_version"])
		record_version = package_version.record_version

	for row in list(package_version.technical_requirements):
		if row.row_status != "Proposed":
			continue
		extra = {}
		if not row.required_value_json:
			extra["value"] = _VALUE_LESS_BASELINE_DEFAULTS[row.characteristic_key]
		cmd.confirm_proposed_requirement(
			requisition=requisition, technical_requirement_id=row.technical_requirement_id,
			expected_record_version=package_version.record_version, idempotency_key=_key(f"{requisition}:confirm-{row.technical_requirement_id}"),
			**extra,
		)
		package_version.reload()

	for manual in _MANUAL_TECHNICAL_ROWS:
		cmd.add_technical_requirement(
			requisition=requisition,
			values={"characteristic_key": manual["characteristic_key"], "value": manual["value"], "applies_to_scope": "All items"},
			expected_record_version=package_version.record_version, idempotency_key=_key(f"{requisition}:tech-{manual['characteristic_key']}"),
		)
		package_version.reload()

	cmd.save_warranty_and_support(
		requisition=requisition,
		values={
			"minimum_warranty_months": 36, "onsite_support_required": 1, "maximum_support_response_hours": 8,
			"manufacturer_support_required": 1, "service_location_constraint": "Within Kenya",
			"support_description": "Supplier to provide escalation and warranty-contact details.",
		},
		expected_record_version=package_version.record_version, idempotency_key=_key(f"{requisition}:warranty"),
	)
	package_version.reload()

	for row in _ACCEPTANCE_ROWS:
		cmd.add_acceptance_requirement(
			requisition=requisition,
			values={"applies_to_scope": "All items", **row},
			expected_record_version=package_version.record_version, idempotency_key=_key(f"{requisition}:acceptance-{row['check_type']}"),
		)
		package_version.reload()


# --- fixture 4 (default) / fixture 6 (additive) — the combined item ----------


def upsert_requisitions_base(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4 fixture 4 — one authorised Version with drawdown, both Budget
	reservations, and unconsumed handoff, built through the real commands
	with the named actors. Idempotent: a rerun that finds the combined
	item's Requisition already Authorised returns it untouched."""
	from kentender_procurement.procurement_requisitions.services import authorise, draft_commands as cmd, lifecycle

	_guard()
	prereqs = verify_prerequisites()
	plan_item_id = prereqs["combined_item"]

	existing = frappe.get_all(
		"Procurement Requisition", filters={"plan_item_id": plan_item_id, "current_state": ("not in", ("Withdrawn", "Revoked", "Superseded"))},
		fields=["name", "current_state"], limit_page_length=1,
	)
	if existing:
		row = existing[0]
		if row.current_state != "Authorised":
			frappe.throw(
				f"{row.name} exists mid-lifecycle on the combined item ({row.current_state}) — "
				"run reset_requisitions_seed() before reseeding the base fixture."
			)
		if commit:
			frappe.db.commit()
		return {"ok": True, "idempotent": True, "requisition": row.name}

	with _as(AUTHOR):
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=_key(f"{plan_item_id}:prepare"))
		requisition = prepared["requisition"]
		cmd.save_requisition_summary(
			requisition=requisition,
			values={
				"requirement_title": COMBINED_ITEM_TITLE, "delivery_location": DELIVERY_LOCATION,
				"latest_delivery_date": "2027-09-30", "related_services_required": False,
			},
			expected_record_version=0, idempotency_key=_key(f"{requisition}:summary"),
		)
		_build_item_package(
			requisition,
			[
				{"quantity": 100, "intended_use": f"Clinical training for {HRMD_NAME} staff"},
				{"quantity": 150, "intended_use": "Field digital-health deployment for Digital Health staff"},
			],
		)
		root = frappe.get_doc("Procurement Requisition", requisition)
		sent = lifecycle.send_for_department_approval(
			requisition=requisition, expected_record_version=root.record_version, idempotency_key=_key(f"{requisition}:send"),
		)

	with _as(HOD):
		root.reload()
		submitted = lifecycle.submit_requisition_to_procurement(
			requisition=requisition, task=sent["task"], expected_record_version=root.record_version, idempotency_key=_key(f"{requisition}:submit"),
		)

	with _as(HOPF):
		root.reload()
		authorised = authorise.authorise_requisition(
			requisition=requisition, task=submitted["task"], expected_record_version=root.record_version, idempotency_key=_key(f"{requisition}:authorise"),
		)

	_stamp_design_clock(requisition)
	if commit:
		frappe.db.commit()
	return {
		"ok": True, "idempotent": False, "requisition": requisition,
		"handoff": authorised.get("handoff"), "reservations": authorised.get("reservations"),
	}


def _stamp_design_clock(requisition: str) -> None:
	root = frappe.get_doc("Procurement Requisition", requisition)
	version = root.current_version
	frappe.db.set_value("Requisition Version", version, "creation", CLOCK["draft_opened"], update_modified=False)
	decisions = frappe.get_all(
		"Requisition Decision", filters={"requisition_version": version}, fields=["name", "decision"],
	)
	stamp_by_decision = {
		"Submit to Procurement": CLOCK["submitted_to_procurement"],
		"Authorise for Tender Preparation": CLOCK["authorised"],
	}
	for decision in decisions:
		when = stamp_by_decision.get(decision.decision)
		if when:
			frappe.db.set_value("Requisition Decision", decision.name, "decided_at", when, update_modified=False)
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": root.name}, "name")
	if handoff:
		frappe.db.set_value("Authorised Requisition Handoff", handoff, "creation", CLOCK["authorised"], update_modified=False)


def seed_consumed_handoff(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4 fixture 6 — the same authorised handoff, additionally consumed
	by `TND-MOH-2027-033`. Additive and idempotent (never reverses fixture
	4's authorisation, matching `record_handoff_consumption`'s own one-way
	semantics)."""
	from kentender_procurement.procurement_requisitions.services import handoff as handoff_service

	_guard()
	base = upsert_requisitions_base(commit=False)
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": base["requisition"]}, "name")
	if not handoff:
		frappe.throw(f"{base['requisition']} has no handoff to consume.")
	result = handoff_service.record_handoff_consumption(
		handoff=handoff, tender=TENDER, tender_version=TENDER_VERSION, template_key=TEMPLATE_KEY,
		template_version=TEMPLATE_VERSION, idempotency_key=_key(f"{handoff}:consume"),
	)
	if result.get("action") == "consumed":
		frappe.db.set_value("Authorised Requisition Handoff", handoff, "consumed_at", CLOCK["consumed"], update_modified=False)
		frappe.db.set_value("Procurement Requisition", base["requisition"], "handoff_consumed_at", CLOCK["consumed"], update_modified=False)
		result["consumed_at"] = CLOCK["consumed"]
	if commit:
		frappe.db.commit()
	return {"ok": True, "requisition": base["requisition"], "handoff": handoff, "consumption": result}


# --- the combined item: mutually exclusive, on-demand profiles -------------
#
# The single-department item ("National digital health infrastructure
# upgrade") is classified Non-consulting services in Planning's own seed
# (`_build_accepted_dpp`'s `classifications={entry_id: "Non-consulting
# services"}`) — `compatibility.first_failure` refuses it with
# REQ_PRODUCT_UNSUPPORTED before a Draft can even be prepared, confirmed
# live while building this module. The combined item is the ONLY Goods-
# classified, IT-equipment-eligible Plan Item the canonical MOH world
# carries, so every lifecycle profile below — including the ones that never
# authorise — is necessarily mutually exclusive with `upsert_requisitions_base`
# itself and with each other, sharing the one eligible item exactly as
# Planning's own §14.10 isolated profiles share one Fiscal Year.


def _wipe_combined_item_profile() -> dict[str, int]:
	"""Tear down whatever Requisition currently sits on the combined item,
	revoking first (through the real command) if it reached Authorised and
	is still unconsumed — the "wipe after authorise" hazard this build
	learned the hard way. A consumed handoff cannot be reset; this refuses
	rather than orphaning it."""
	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	root_row = frappe.db.get_value(
		"Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": ("not in", ("Withdrawn", "Revoked", "Superseded"))},
		["name", "current_state", "record_version", "handoff_consumed_at"], as_dict=True,
	)
	deleted: dict[str, int] = {}
	if not root_row:
		return deleted
	if root_row.current_state == "Authorised":
		if root_row.handoff_consumed_at:
			frappe.throw(f"{root_row.name}'s handoff is already consumed — this fixture cannot be reset to a different profile.")
		from kentender_procurement.procurement_requisitions.services import authorise

		with _as(HOPF):
			authorise.revoke_unconsumed_authorisation(
				requisition=root_row.name, reason="KENTENDER_MVP_V1 profile reseed.",
				expected_record_version=root_row.record_version, idempotency_key=_key(f"{root_row.name}:profile-revoke"),
			)
	# The row-shape logic (which doctype hangs off `requisition` directly vs
	# via `task`/`package`) already lives once in `seeds.clear._delete_for_plan_items`
	# — reuse it rather than a second, drifting copy.
	from kentender_procurement.procurement_requisitions.seeds.clear import _delete_for_plan_items

	deleted = _delete_for_plan_items([plan_item_id])
	journal = frappe.get_all("Requisition Command Journal", filters={"idempotency_key": ("like", "req-seed:%")}, pluck="name")
	frappe.db.delete("Requisition Command Journal", {"name": ("in", journal or ("",))})
	deleted["Requisition Command Journal"] = len(journal)
	return deleted


def reset_requisitions_seed(*, commit: bool = False) -> dict[str, int]:
	_guard()
	frappe.set_user("Administrator")
	deleted = _wipe_combined_item_profile()
	if commit:
		frappe.db.commit()
	return deleted


def _fresh_combined_item_profile() -> str:
	_guard()
	reset_requisitions_seed()
	prereqs = verify_prerequisites()
	return prereqs["combined_item"]


def _build_combined_item_draft() -> str:
	"""§13.5-13.9's full two-item package (the same content
	`upsert_requisitions_base` authorises), the common starting point every
	profile below advances further."""
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	plan_item_id = _fresh_combined_item_profile()
	with _as(AUTHOR):
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=_key(f"{plan_item_id}:prepare"))
		requisition = prepared["requisition"]
		cmd.save_requisition_summary(
			requisition=requisition,
			values={
				"requirement_title": COMBINED_ITEM_TITLE, "delivery_location": DELIVERY_LOCATION,
				"latest_delivery_date": "2027-09-30", "related_services_required": False,
			},
			expected_record_version=0, idempotency_key=_key(f"{requisition}:summary"),
		)
		_build_item_package(
			requisition,
			[
				{"quantity": 100, "intended_use": f"Clinical training for {HRMD_NAME} staff"},
				{"quantity": 150, "intended_use": "Field digital-health deployment for Digital Health staff"},
			],
		)
	return requisition


def seed_draft_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4 fixture 1 — one complete Draft owned by Grace Wanjiku (through
	Step 5, ready to submit but never sent)."""
	requisition = _build_combined_item_draft()
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "draft", "requisition": requisition}


def seed_department_task_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4 fixture 2 — one Version awaiting Dr Peter Kimani's department
	decision (complete package, sent for department approval)."""
	from kentender_procurement.procurement_requisitions.services import lifecycle

	requisition = _build_combined_item_draft()
	with _as(AUTHOR):
		root = frappe.get_doc("Procurement Requisition", requisition)
		sent = lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=root.record_version, idempotency_key=_key(f"{requisition}:send"))
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "department_task", "requisition": requisition, "task": sent["task"]}


def seed_procurement_task_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4 fixture 3 — one Version submitted to Charles Mutiso for
	Procurement authorisation."""
	from kentender_procurement.procurement_requisitions.services import lifecycle

	dept = seed_department_task_profile(commit=False)
	requisition = dept["requisition"]
	with _as(HOD):
		root = frappe.get_doc("Procurement Requisition", requisition)
		submitted = lifecycle.submit_requisition_to_procurement(
			requisition=requisition, task=dept["task"], expected_record_version=root.record_version, idempotency_key=_key(f"{requisition}:submit"),
		)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "procurement_task", "requisition": requisition, "task": submitted["task"]}


def seed_returned_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4 fixture 5 — one returned Version with copied Draft successor:
	Charles Mutiso returns the Submitted-to-Procurement Version to the
	department for correction."""
	from kentender_procurement.procurement_requisitions.services import lifecycle

	submitted = seed_procurement_task_profile(commit=False)
	requisition = submitted["requisition"]
	with _as(HOPF):
		task = frappe.get_doc("Requisition Task", submitted["task"])
		returned = lifecycle.return_requisition_to_department(
			task=submitted["task"], reason="Confirm the delivery location matches the Ministry Headquarters address on file.",
			expected_record_version=task.record_version, idempotency_key=_key(f"{requisition}:return"),
		)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "returned", "requisition": requisition, "correction_version": returned["requisition_version"]}


def seed_upstream_correction_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4's stopped Version — a Requisition Version closed with `Upstream
	correction required`, and the Planning-side `Plan Item Correction
	Request` it produces (D3), proving §7.4A's route without depending on
	Planning's own inbound handling screen (not yet built)."""
	from kentender_procurement.procurement_requisitions.services import lifecycle

	submitted = seed_procurement_task_profile(commit=False)
	requisition = submitted["requisition"]
	with _as(HOPF):
		root = frappe.get_doc("Procurement Requisition", requisition)
		result = lifecycle.request_upstream_plan_correction(
			requisition=requisition,
			reason="Planning's remaining balance no longer matches this Requisition's requested value.",
			expected_record_version=root.record_version, idempotency_key=_key(f"{requisition}:upstream"),
		)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "upstream_correction", "requisition": requisition, "correction_request": result.get("correction_request")}


# --- validation ---------------------------------------------------------


def validate_requisitions_seed() -> list[dict[str, Any]]:
	"""§16 — validate the default base fixture (fixture 4) through the same
	read the UI uses, returning check rows for the core validator."""
	from kentender_procurement.procurement_requisitions.services import read as req_read

	checks: list[dict[str, Any]] = []

	def check(name: str, ok: bool, detail: str = "") -> None:
		checks.append({"check": f"requisitions.v16.{name}", "ok": bool(ok), "detail": detail})

	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	check("combined_item.exists", bool(plan_item_id), plan_item_id)
	if not plan_item_id:
		return checks

	root_name = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": "Authorised"}, "name")
	check("requisition.authorised", bool(root_name), str(root_name))
	if not root_name:
		return checks

	root = frappe.get_doc("Procurement Requisition", root_name)
	package_version = frappe.get_doc(
		"IT Equipment Requirement Package Version",
		frappe.get_doc("Requisition Version", root.current_version).package_version,
	)
	check("items.count_2", len(package_version.items) == 2, str(len(package_version.items)))
	confirmed = [r for r in package_version.technical_requirements if r.row_status == "Confirmed"]
	check("technical.confirmed_11", len(confirmed) == 11, str(len(confirmed)))
	check("acceptance.count_5", len(package_version.acceptance_requirements) == 5, str(len(package_version.acceptance_requirements)))
	check("warranty.36_months", package_version.minimum_warranty_months == 36, str(package_version.minimum_warranty_months))

	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": root.name}, "name")
	check("handoff.exists", bool(handoff), str(handoff))
	if handoff:
		reservations = frappe.get_all("Funding Reservation", filters={"calling_module": "Procurement Requisitions", "caller_reference": root.requisition_reference, "status": "Active"}, fields=["original_amount"])
		check("reservations.two", len(reservations) == 2, str(len(reservations)))
		total = sum(flt(r.original_amount) for r in reservations)
		check("reservations.total_50m", abs(total - 50_000_000) < 0.01, str(total))

	handoff_view = req_read.get_authorised_requisition_handoff(requisition=root.name, user=HOPF)
	check("read.authorised_by_hopf", (handoff_view.get("authorised_by") or {}).get("name") == "Charles Mutiso", str(handoff_view.get("authorised_by")))
	return checks
