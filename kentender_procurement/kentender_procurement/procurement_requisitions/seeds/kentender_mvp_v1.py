# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §16 — the deterministic Ministry of Health Requisitions
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
  4); the consumed handoff (fixture 6) is produced downstream by Tender
  Preparation's own §16 seed through a real `PrepareTender` (TPR-CHG-001
  plan D19 — the synthetic `seed_consumed_handoff()` is retired), which
  also stamps this module's consumption instant via
  `stamp_handoff_consumption_clock()`;
- `seed_draft_profile()` / `seed_department_task_profile()` /
  `seed_procurement_task_profile()` / `seed_returned_profile()` /
  `seed_upstream_correction_profile()` each tear the fixture down (revoking
  first through the real command if it had reached Authorised and is still
  unconsumed) and rebuild to their own named state — on demand, never
  called by `run_kentender_mvp_v1` itself.

**v1.11 package.** The Draft is built exactly as a user builds it: one
`AddSameSpecificationItems` creates both source-linked laptop rows from one
shared definition, which generates the code-owned `LAPTOP-REQUIREMENTS-V1`
proposal (eleven technical rows, six warranty/support values, five
acceptance checks — the §16.3 values); one `ApplySelectedRequirementPackage`
then confirms the whole visible proposal and marks it Reviewed.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from decimal import Decimal

import frappe
from frappe.utils import cstr

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

# §16.4's exact fixture-4 timeline. Site datetimes are naive Africa/Nairobi
# values, rendered as stored (read.presenters.eat).
CLOCK = {
	"draft_opened": "2027-03-01 09:00:00",
	"steps_completed": "2027-03-01 11:00:00",
	"sent_for_department_approval": "2027-03-01 11:05:00",
	"submitted_to_procurement": "2027-03-08 09:00:00",
	"authorised": "2027-03-15 10:00:00",
	"consumed": "2027-03-20 09:00:00",
}

# §16.3 — each department's equipment row (one shared laptop definition).
_INTENDED_USE = {
	HRMD_NAME: f"Clinical training for {HRMD_NAME} staff",
	DHI_NAME: "Field digital-health deployment for Digital Health staff",
}
_SHARED_LAPTOP = {"equipment_category": "Laptop", "item_name": "Business laptops", "delivery_location": DELIVERY_LOCATION, "latest_delivery_date": "2027-09-30"}


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


def _editor(requisition: str) -> dict[str, Any]:
	from kentender_procurement.procurement_requisitions.services import read

	return read.get_requisition_record(requisition=requisition, user=frappe.session.user)


def _build_item_package(requisition: str, amounts: dict[str, tuple[str, str]] | None = None) -> None:
	"""§13.4–13.6 through the real commands, as the author: request
	information, one same-specification laptop set (one row per approved
	requirement), then the standard package applied once. `amounts` maps a
	department name to an exact (quantity, KES value) smaller than what
	remains — a partial draw; every other line keeps the full default."""
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	view = _editor(requisition)
	values: dict[str, Any] = {"requirement_title": COMBINED_ITEM_TITLE, "delivery_location": DELIVERY_LOCATION, "latest_delivery_date": "2027-09-30", "related_services_required": False}
	if amounts:
		values["drawdown_lines"] = [
			{"drawdown_line_id": r["drawdown_line_id"], "requested_quantity": amounts[r["department"]][0], "requested_value": amounts[r["department"]][1]}
			for r in view["amounts"] if r["department"] in amounts
		]
	cmd.save_requisition_summary(
		requisition=requisition, values=values,
		expected_record_version=view["header"]["version_record_version"], idempotency_key=_key(f"{requisition}:summary"),
	)
	view = _editor(requisition)
	rows = [
		{"drawdown_line_id": r["drawdown_line_id"], "quantity": str(r["quantity"]), "intended_use": _INTENDED_USE[r["department"]]}
		for r in view["equipment"]["add_rows"]
	]
	cmd.add_same_specification_items(
		requisition=requisition, shared=dict(_SHARED_LAPTOP), rows=rows,
		expected_record_version=view["package_record_version"], idempotency_key=_key(f"{requisition}:laptops"),
	)
	view = _editor(requisition)
	req = view["requirements"]

	def raw(value: dict[str, Any]):
		return value.get("ports") or value.get("values") or value.get("value")

	technical = [
		{"technical_requirement_id": r["technical_requirement_id"], "characteristic_key": r["characteristic_key"], "value": raw(r["value"]), "selected": True, "applies_to_scope": r["applies_to_scope"] or "All items"}
		for g in req["technical_groups"] for r in g["rows"] if r["state"] == "Proposed"
	]
	acceptance = [
		{k: a[k] for k in ("acceptance_requirement_id", "check_type", "pass_condition", "evidence_type", "applies_to_scope", "applies_to_id")} | {"selected": True}
		for a in req["acceptance"] if a["state"] == "Proposed"
	]
	cmd.apply_selected_requirement_package(
		requisition=requisition, profile_key=req["profile_key"], profile_version=req["profile_version"], proposal_digest=req["proposal_digest"],
		technical=technical, acceptance=acceptance, support=req["support"],
		expected_record_version=view["package_record_version"], idempotency_key=_key(f"{requisition}:apply-package"),
	)


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

	if _namespace_blocked(plan_item_id):
		# An earlier profile left the item locked or held with no live
		# Requisition: restore the namespace as a profile reset does.
		_restore_planning_namespace()
		plan_item_id = verify_prerequisites()["combined_item"]
	with _as(AUTHOR):
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=_key(f"{plan_item_id}:prepare"))
		requisition = prepared["requisition"]
		_build_item_package(requisition)
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
		"Authorise requisition": CLOCK["authorised"],
	}
	for decision in decisions:
		when = stamp_by_decision.get(decision.decision)
		if when:
			frappe.db.set_value("Requisition Decision", decision.name, "decided_at", when, update_modified=False)
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": root.name}, "name")
	if handoff:
		frappe.db.set_value("Authorised Requisition Handoff", handoff, "creation", CLOCK["authorised"], update_modified=False)
		if frappe.get_meta("Authorised Requisition Handoff").has_field("generated_at"):
			frappe.db.set_value("Authorised Requisition Handoff", handoff, "generated_at", CLOCK["authorised"], update_modified=False)


def stamp_handoff_consumption_clock(requisition: str, *, when: str | None = None) -> None:
	"""§16.4 fixture-6 instant on Requisitions' own consumption columns. The
	consumer (Tender Preparation's §16 seed) calls this after its real
	`PrepareTender`; it never writes these rows itself."""
	when = when or CLOCK["consumed"]
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": requisition}, "name")
	if handoff and frappe.db.get_value("Authorised Requisition Handoff", handoff, "consumed_at"):
		frappe.db.set_value("Authorised Requisition Handoff", handoff, "consumed_at", when, update_modified=False)
		frappe.db.set_value("Procurement Requisition", requisition, "handoff_consumed_at", when, update_modified=False)


def seed_consumed_handoff(*, commit: bool = False) -> dict[str, Any]:
	"""Retired. §16.4 fixture 6 — the authorised handoff consumed by a
	Tender — is produced by a real `StartTender` in
	`kentender_procurement.tenders.seeds.kentender_mvp_v1.upsert_tenders`
	(TPR-CHG-001 v0.8 §13), which chains after this module in the canonical
	seed; a synthetic consumption by a Tender that does not exist would
	contradict the live Tenders module."""
	frappe.throw(
		"seed_consumed_handoff() is retired: the consumed handoff is seeded by "
		"kentender_procurement.tenders.seeds.kentender_mvp_v1.upsert_tenders "
		"(a real Tender), chained after upsert_requisitions_base in the canonical seed.",
		frappe.ValidationError,
	)
	return {}  # unreachable


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
	learned the hard way. Every root on the item goes (a profile may leave
	more than one, e.g. REQ-SC-SEQUENTIAL)."""
	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	root_row = frappe.db.get_value(
		"Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": "Authorised", "handoff_consumed_at": ("is", "not set")},
		["name", "current_state", "record_version", "handoff_consumed_at"], as_dict=True,
	) or frappe.db.get_value(
		"Procurement Requisition", {"plan_item_id": plan_item_id},
		["name", "current_state", "record_version", "handoff_consumed_at"], as_dict=True,
	)
	deleted: dict[str, int] = {}
	if not root_row:
		return deleted
	if root_row.current_state == "Authorised" and not root_row.handoff_consumed_at:
		from kentender_procurement.procurement_requisitions.services import authorise

		with _as(HOPF):
			authorise.revoke_unconsumed_authorisation(
				requisition=root_row.name, reason="KENTENDER_MVP_V1 profile reseed.",
				expected_record_version=root_row.record_version, idempotency_key=_key(f"{root_row.name}:profile-revoke"),
			)
	# A consumed handoff (a profile's stand-in Tender, D16) cannot be revoked:
	# its rows go, and the item's permanent scope lock then makes the next
	# profile or base reseed restore the Planning namespace, which reverses
	# nothing by hand — Planning and Budget are rebuilt by their own seeds.
	# The row-shape logic (which doctype hangs off `requisition` directly vs
	# via `task`/`package`) already lives once in `seeds.clear._delete_for_plan_items`
	# — reuse it rather than a second, drifting copy.
	from kentender_procurement.procurement_requisitions.seeds.clear import _delete_for_plan_items

	deleted = _delete_for_plan_items([plan_item_id])
	journal = frappe.get_all("Requisition Command Journal", filters={"idempotency_key": ("like", "req-seed:%")}, pluck="name")
	frappe.db.delete("Requisition Command Journal", {"name": ("in", journal or ("",))})
	deleted["Requisition Command Journal"] = len(journal)
	return deleted


def recover_orphaned_drawdowns(*, commit: bool = False) -> dict[str, Any]:
	"""The "wipe after authorise" hazard's documented repair, as a named seed
	function: a site-wide `wipe_requisition_rows()` (any Requisitions test
	module) deletes an Authorised Requisition's rows but leaves its Planning
	drawdown Active, so the combined item reads as having no remaining
	quantity (REQ_PLAN_INELIGIBLE) and no fixture can be rebuilt. Reverse
	every Active drawdown on the canonical items whose Requisition no longer
	exists — through Planning's own published reversal, as the Head of
	Procurement Function — and nothing else."""
	from kentender_procurement.procurement_requisitions.services import eligibility_gateway as planning

	_guard()
	frappe.set_user("Administrator")
	reversed_rows: list[str] = []
	for title in (SINGLE_ITEM_TITLE, COMBINED_ITEM_TITLE):
		plan_item_id = _plan_item_id(title)
		if not plan_item_id:
			continue
		item_name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": plan_item_id, "item_state": "Active"}, "name")
		allocations = frappe.get_all("Plan Source Allocation", filters={"plan_item": item_name}, pluck="name") if item_name else []
		rows = frappe.get_all(
			"Plan Drawdown Reference", filters={"allocation": ("in", allocations or ("",)), "drawdown_state": "Active"},
			fields=["name", "record_version", "requisition_reference"],
		)
		for row in rows:
			if frappe.db.exists("Procurement Requisition", {"requisition_reference": row.requisition_reference}):
				continue  # a live Requisition still owns this drawdown
			with _as(HOPF):
				planning.reverse_requisition_drawdown(
					drawdown_reference=row.name, expected_record_version=row.record_version,
					idempotency_key=_key(f"{row.name}:orphan-reversal"),
				)
			reversed_rows.append(row.name)
	if commit:
		frappe.db.commit()
	return {"ok": True, "reversed": reversed_rows}


def reset_requisitions_seed(*, commit: bool = False) -> dict[str, int]:
	_guard()
	frappe.set_user("Administrator")
	deleted = _wipe_combined_item_profile()
	if commit:
		frappe.db.commit()
	return deleted


def _namespace_blocked(plan_item_id: str) -> bool:
	"""The item is not the clean §16.2 base, so it cannot carry a fresh
	profile or the base fixture: its scope is permanently locked by an
	earlier authorisation (§7.2), a correction request holds it (§9.1B), it
	is no longer eligible or compatible (a demo profile published a changed
	item), or a Planning update is left open."""
	from kentender_procurement.procurement_requisitions.services import compatibility, eligibility_gateway

	projection = eligibility_gateway.get_requisition_eligible_plan_item(plan_item_id)
	plan = frappe.db.get_value("Annual Plan", {"plan_reference": projection.get("plan_reference")}, "open_successor_version")
	return bool(
		(projection.get("scope") or {}).get("locked") or (projection.get("hold") or {}).get("held") or not projection.get("eligible")
		or compatibility.first_failure(projection) is not None or plan
	)


def _restore_planning_namespace() -> None:
	"""§16.4 — profiles are mutually exclusive resets of one isolated
	namespace. Once the combined item has been authorised its scope lock is
	permanent (§7.2), even after revocation, so the namespace is restored the
	way the canonical seed builds it: downstream modules cleared through their
	own teardown, then Planning (and what it stands on) reseeded through its
	own published seed. Nothing here writes a Planning row."""
	from kentender_core.seeds import canonical

	canonical.clear_canonical_modules()
	canonical.seed(through="planning")


def _fresh_combined_item_profile() -> str:
	_guard()
	reset_requisitions_seed()
	prereqs = verify_prerequisites()
	if _namespace_blocked(prereqs["combined_item"]):
		_restore_planning_namespace()
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
		_build_item_package(requisition)
	return requisition


def seed_draft_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§16.4 fixture 1 — one complete Draft owned by Grace Wanjiku (every
	task complete, ready to send but never sent)."""
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
			task=submitted["task"], reason="Confirm the delivery location matches the Ministry Headquarters address on file.", affected_section="Request details",
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
	reads the UI uses, returning check rows for the core validator."""
	from kentender_procurement.procurement_requisitions.services import read as req_read, records

	checks: list[dict[str, Any]] = []

	def check(name: str, ok: bool, detail: str = "") -> None:
		checks.append({"check": f"requisitions.v111.{name}", "ok": bool(ok), "detail": detail})

	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	check("combined_item.exists", bool(plan_item_id), plan_item_id)
	if not plan_item_id:
		return checks

	root_name = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": "Authorised"}, "name")
	check("requisition.authorised", bool(root_name), str(root_name))
	if not root_name:
		return checks

	root = frappe.get_doc("Procurement Requisition", root_name)
	version = frappe.get_doc("Requisition Version", root.authorised_version or root.current_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	check("items.count_2", len(package_version.items) == 2, str(len(package_version.items)))
	confirmed = [r for r in package_version.technical_requirements if r.row_state == "Confirmed"]
	check("technical.confirmed_11", len(confirmed) == 11 and len(package_version.technical_requirements) == 11, str(len(confirmed)))
	check("acceptance.confirmed_5", sum(1 for r in package_version.acceptance_requirements if r.row_state == "Confirmed") == 5, str(len(package_version.acceptance_requirements)))
	check("warranty.36_months", package_version.minimum_warranty_months == 36, str(package_version.minimum_warranty_months))
	check("package.reviewed", package_version.standard_package_review_state == "Reviewed", cstr(package_version.standard_package_review_state))
	check("amounts.exact_50m", sum((Decimal(cstr(l.requested_value)) for l in version.drawdown_lines), Decimal(0)) == Decimal("50000000.00"), "")

	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": root.name}, "name")
	check("handoff.exists", bool(handoff), str(handoff))
	if handoff:
		reservations = frappe.get_all(
			"Funding Reservation", filters={"calling_module": "Procurement Requisitions", "caller_reference": root.requisition_reference, "status": ("in", ("Active", "Partially Converted"))},
			fields=["original_amount", "drawdown_line_id"],
		)
		check("reservations.one_per_line", len(reservations) == 2 and len({r.drawdown_line_id for r in reservations}) == 2, str(len(reservations)))
		total = sum((Decimal(cstr(r.original_amount)) for r in reservations), Decimal(0))
		check("reservations.total_50m", total == Decimal("50000000"), str(total))
		view = req_read.get_authorised_requisition_handoff(requisition=root.name, user=HOPF)
		check("handoff.version_1_4", view.get("handoff_version") == "1.4", cstr(view.get("handoff_version")))
		payload = view.get("payload") or {}
		check("handoff.two_lines", len(payload.get("drawdown_lines") or []) == 2, "")
		check("handoff.nine_checks", len(payload.get("compatibility") or []) == 9, "")
	decision = records.decision_of(version.name, "Authorise requisition")
	check("authorised_by_hopf", bool(decision) and decision.actor == HOPF, cstr(decision.actor if decision else ""))
	return checks
