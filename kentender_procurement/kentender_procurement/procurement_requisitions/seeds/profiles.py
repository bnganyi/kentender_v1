# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §16.4A — the thirteen isolated demo-data profiles.

Each profile is one named, mutually exclusive state of the canonical
Ministry of Health world, built on the one eligible combined laptop item
through the same commands the screens call, as the canonical actors (Grace
Wanjiku, Dr Peter Kimani, Charles Mutiso, Mercy Kilonzo, Josphat Mwangi,
Amina Hassan, Daniel Rotich) — plus Asha Odhiambo, the isolated
contributing-department Author §16.1 names, created only by the profiles
that need her.

Loading a profile first returns the item to a clean namespace: the
Requisitions rows on the item are torn down (revoking through the real
command where an unconsumed authorisation exists), and if the item's scope
is permanently locked or held by an earlier profile, the Planning namespace
is rebuilt through the canonical seed (§16.4 "restore it after each
profile"). `restore_base()` puts the §16.4 fixture-4 base back. Every
profile returns a report: what it built, who to log in as and where to look,
and each §16.4A required result as an observed check.

Owner decisions (24 Sep 2026): D16 — a profile that needs a consumed
handoff consumes it through Requisitions' own guarded
`record_handoff_consumption` with a labelled seed stand-in Tender id, to be
replaced by a real Tender after the Tenders revamp; D17 — the profiles live
on the canonical MOH item, not a separate year; D18 — REQ-SC-COMPATIBILITY
builds real failing Plan Items for the checks Planning can publish and
reports the three it cannot (Currency, Award package and Plan horizon are
fixed values in Planning's projection).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.seeds import kentender_mvp_v1 as base

LOADED_KEY = "kt_req_loaded_profile"
ASHA = "asha.odhiambo@moh.example.test"
STAND_IN_TEMPLATE = ("IT-EQUIPMENT-OPEN-V1", "1.1")
CORRECTION_REASON = "The approved source allocation refers to the wrong Budget Line. Please review the departmental funding specification through the governed Planning correction process."
NO_CHANGE_REASON = "The approved source allocation and Budget Line are correct. No Planning change is required."
# §13.12's isolated stopped-work clock (site datetimes are naive EAT).
STOP_CLOCK = {"requested": "2027-03-10 09:00:00", "started": "2027-03-10 11:00:00", "decided": "2027-03-12 10:00:00"}


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------


@contextmanager
def _as(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


class Report:
	def __init__(self, profile: str, summary: str):
		self.data: dict[str, Any] = {"profile": profile, "summary": summary, "look": [], "results": [], "limits": [], "records": {}}

	def check(self, name: str, ok: bool, detail: Any = "") -> None:
		self.data["results"].append({"check": name, "ok": bool(ok), "detail": cstr(detail)})

	def refused(self, name: str, call: Callable[[], Any], code: str) -> None:
		"""The call must be refused with exactly `code`; anything else fails."""
		try:
			call()
		except Exception as exc:  # noqa: BLE001 — the refusal code is the observation
			got = getattr(exc, "code", "") or getattr(exc, "title", "") or type(exc).__name__
			self.check(name, got == code, f"refused with {got}")
			return
		self.check(name, False, "was accepted")

	def look(self, actor: str, route: str, what: str) -> None:
		self.data["look"].append({"actor": actor, "route": route, "what": what})

	def limit(self, text: str) -> None:
		self.data["limits"].append(text)

	def record(self, **values) -> None:
		self.data["records"].update(values)

	@property
	def ok(self) -> bool:
		return all(r["ok"] for r in self.data["results"])


def _key(profile: str, step: str) -> str:
	return f"req-seed:{profile}:{step}:{frappe.generate_hash(length=8)}"


def _svc():
	from kentender_procurement.procurement_requisitions.services import (
		authorise, correction, draft_commands, eligibility_gateway, funding_gateway, handoff, lifecycle, read, records,
	)

	return frappe._dict(
		authorise=authorise, correction=correction, cmd=draft_commands, eligibility=eligibility_gateway, funding=funding_gateway,
		handoff=handoff, lifecycle=lifecycle, read=read, records=records,
	)


def _pln():
	from kentender_procurement.procurement_planning.seeds import kentender_mvp_v1 as seed
	from kentender_procurement.procurement_planning.services import (
		outcome_event, plan_finance, plan_governance, plan_publication, plan_read, plan_requisition, plan_workbench, publication_pipeline, treasury,
	)

	return frappe._dict(
		seed=seed, outcome_event=outcome_event, finance=plan_finance, governance=plan_governance, publication=plan_publication, read=plan_read,
		requisition=plan_requisition, workbench=plan_workbench, pipeline=publication_pipeline, treasury=treasury,
	)


def _root_version(requisition: str) -> int:
	return int(frappe.db.get_value("Procurement Requisition", requisition, "record_version"))


def _open_task(requisition: str, role: str) -> str:
	return cstr(frappe.db.get_value("Requisition Task", {"requisition": requisition, "business_role": role, "status": "Open"}, "name"))


def _route(requisition: str, suffix: str = "") -> str:
	return f"/app/procurement-requisitions/{requisition}{suffix}"


def _reference(requisition: str) -> str:
	return cstr(frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference"))


def _decisions(requisition: str) -> list[str]:
	versions = frappe.get_all("Requisition Version", filters={"requisition": requisition}, pluck="name")
	return frappe.get_all("Requisition Decision", filters={"requisition_version": ("in", versions or ("",))}, pluck="decision")


def _projection(plan_item_id: str) -> dict[str, Any]:
	return _svc().eligibility.get_requisition_eligible_plan_item(plan_item_id)


# --------------------------------------------------------------------------
# namespace: clean before a profile, restore the base after
# --------------------------------------------------------------------------


def _release_profile_holds() -> list[str]:
	"""Release, through Budget's own release command, any hold a profile
	opened for a non-Requisition caller (REQ-SC-SHARED-LINE-SHORT) and the
	reservations of a requisition a stand-in Tender consumed."""
	released = []
	# A requisition consumed by a stand-in Tender (D16) cannot be revoked, so
	# its reservations are released here, before its rows go.
	item = base._plan_item_id(base.COMBINED_ITEM_TITLE)
	consumed = frappe.get_all("Procurement Requisition", filters={"plan_item_id": item, "handoff_consumed_at": ("is", "set")}, pluck="requisition_reference")
	callers = ["REQ-SC-%"] + consumed
	rows = []
	for caller in callers:
		rows += frappe.get_all(
			"Funding Reservation", filters={"caller_reference": ("like", caller), "status": ("in", ("Active", "Partially Converted"))}, pluck="name",
		)
	for row in rows:
		with _as(base.HOPF):
			_svc().funding.release_reservation(reservation=row, requisition_reference=frappe.db.get_value("Funding Reservation", row, "caller_reference"), downstream_event_id=f"REQ-SC-RELEASE-{row}", idempotency_key=f"req-seed:release:{row}")
		released.append(row)
	return released


def _clean_namespace() -> dict[str, str]:
	"""No Requisition on the item, no profile hold, and — when an earlier
	profile left the item's scope locked or held — the Planning namespace
	rebuilt through the canonical seed."""
	base._guard()
	frappe.set_user("Administrator")
	_release_profile_holds()
	base.reset_requisitions_seed()
	prereqs = base.verify_prerequisites()
	if base._namespace_blocked(prereqs["combined_item"]):
		base._restore_planning_namespace()
		prereqs = base.verify_prerequisites()
	return prereqs


def release_loaded_profile() -> dict[str, Any]:
	"""Called by the canonical seed before its own reset: undo a loaded
	profile through the real commands (so no Requisition row is left
	pointing at a Budget reservation the reset would otherwise delete)."""
	loaded = frappe.defaults.get_global_default(LOADED_KEY)
	if not loaded:
		return {"loaded": None}
	_clean_namespace()
	frappe.defaults.set_global_default(LOADED_KEY, "")
	return {"loaded": loaded, "released": True}


def restore_base(*, commit: bool = True) -> dict[str, Any]:
	"""Undo any profile and put back the §16.4 fixture-4 base."""
	_clean_namespace()
	frappe.defaults.set_global_default(LOADED_KEY, "")
	result = base.upsert_requisitions_base(commit=False)
	if commit:
		frappe.db.commit()
	return result


# --------------------------------------------------------------------------
# shared journeys (real commands, canonical actors)
# --------------------------------------------------------------------------


def _draft(profile: str, plan_item_id: str, *, amounts: dict[str, tuple[str, str]] | None = None, author: str = base.AUTHOR) -> str:
	with _as(author):
		prepared = _svc().cmd.prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=_key(profile, "prepare"))
		requisition = prepared["requisition"]
		base._build_item_package(requisition, amounts)
	return requisition


def _submitted(profile: str, plan_item_id: str, **kwargs) -> str:
	svc = _svc()
	requisition = _draft(profile, plan_item_id, **kwargs)
	with _as(base.AUTHOR):
		svc.lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=_root_version(requisition), idempotency_key=_key(profile, "send"))
	with _as(base.HOD):
		svc.lifecycle.submit_requisition_to_procurement(
			requisition=requisition, task=_open_task(requisition, "Head of User Department"),
			expected_record_version=_root_version(requisition), idempotency_key=_key(profile, "submit"),
		)
	return requisition


def _authorise(profile: str, requisition: str) -> dict[str, Any]:
	with _as(base.HOPF):
		return _svc().authorise.authorise_requisition(
			requisition=requisition, task=_open_task(requisition, "Head of Procurement Function"),
			expected_record_version=_root_version(requisition), idempotency_key=_key(profile, "authorise"),
		)


def _consume(profile: str, requisition: str, tender: str) -> dict[str, Any]:
	"""D16 — Requisitions' own guarded consumption, by a labelled seed stand-in
	Tender id (never a real Tender record)."""
	handoff = frappe.db.get_value("Procurement Requisition", requisition, "handoff")
	return _svc().handoff.record_handoff_consumption(
		handoff=handoff, tender=tender, tender_version=f"{tender}-V1", template_key=STAND_IN_TEMPLATE[0], template_version=STAND_IN_TEMPLATE[1],
		idempotency_key=_key(profile, "consume"),
	)


def _stop(profile: str, requisition: str, *, actor: str = base.HOD) -> str:
	with _as(actor):
		result = _svc().lifecycle.request_upstream_plan_correction(
			requisition=requisition, reason=CORRECTION_REASON, expected_record_version=_root_version(requisition), idempotency_key=_key(profile, "stop"),
		)
	# §13.12's isolated clock, on Requisitions' own decision row only.
	version = frappe.db.get_value("Procurement Requisition", requisition, "current_version")
	decision = frappe.db.get_value("Requisition Decision", {"requisition_version": version, "decision": "Request Planning correction"}, "name")
	if decision:
		frappe.db.set_value("Requisition Decision", decision, "decided_at", STOP_CLOCK["requested"], update_modified=False)
	return cstr(result.get("correction_request"))


def _external_request(profile: str, plan_item_id: str, label: str) -> str:
	"""A second correction request against the same item, recorded through
	Planning's published inbound command as raised by another proceeding —
	one item carries at most one open Requisition, so §16.4A's second
	request cannot come from a second Requisition."""
	with _as(base.HOD):
		result = _pln().requisition.receive_plan_item_correction_request(
			plan_item_id=plan_item_id, requisition_reference=label, requisition_version=f"{label}-V1",
			reason="A second approved-plan issue raised against this item by another proceeding, for the seed's isolated profile.",
			idempotency_key=_key(profile, f"external-{label}"),
		)
	return cstr(result.get("correction_request"))


def _dispose(profile: str, request: str, action: str, **kwargs) -> dict[str, Any]:
	pln = _pln()
	fn = {"start": pln.requisition.start_plan_item_correction, "close": pln.requisition.close_plan_item_correction_without_change, "resolve": pln.requisition.resolve_plan_item_correction_request}[action]
	with _as(pln.seed.PLANNER):
		version = frappe.db.get_value("Plan Item Correction Request", request, "record_version")
		return fn(correction_request=request, expected_record_version=version, idempotency_key=_key(profile, f"{action}-{request}"), **kwargs)


def _activate_successor(profile: str, plan_item_id: str, *, edit: dict[str, Any] | None = None) -> str:
	"""A Planning successor carried to Active through Planning's governed
	commands as its canonical actors (begin update → optional item edit →
	funding confirmation → sign/adopt/approve → Treasury evidence → publish).
	Returns the Active correcting Plan Version."""
	pln = _pln()
	plan_reference = _projection(plan_item_id)["plan_reference"]
	with _as(pln.seed.PLANNER):
		pln.publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=_key(profile, "begin-update"))
		if edit:
			item = pln.read.get_plan_item(plan_item_id=plan_item_id)
			pln.workbench.save_plan_item(plan_item=plan_item_id, values=edit, expected_record_version=item["record_version"], idempotency_key=_key(profile, "edit-item"))
		plan = pln.read.get_annual_plan(plan_reference=plan_reference)
		requested = pln.finance.request_plan_funding_confirmation(plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(profile, "funding"))
	task = frappe.get_doc("Plan Finance Task", requested["task"])
	with _as(pln.seed.FINANCE):
		pln.finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=_key(profile, "confirm-funding"))
	with _as(pln.seed.PLANNER):
		plan = pln.read.get_annual_plan(plan_reference=plan_reference)
	with _as(pln.seed.HOPF):
		submitted = pln.governance.submit_consolidated_plan(plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(profile, "sign"))
	ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
	with _as(pln.seed.ACCOUNTING_OFFICER):
		adopted = pln.governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=_key(profile, "adopt"))
	statutory = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	with _as(pln.seed.STATUTORY):
		approved = pln.governance.approve_annual_plan(task=statutory.name, task_token=statutory.task_token, idempotency_key=_key(profile, "approve"))
	version = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
	with _as(pln.seed.ACCOUNTING_OFFICER):
		pln.treasury.record_treasury_submission(
			plan_version=version, submitted_at=frappe.utils.now_datetime(), channel="Official correspondence", destination="National Treasury",
			dispatch_reference=f"MOH/APP/2027/{profile}", exact_document_confirmed=True, idempotency_key=_key(profile, "treasury"),
		)
	with _as("Administrator"):
		pln.pipeline.publish_annual_plan(plan_version=version, idempotency_key=_key(profile, "publish"))
	return cstr(frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference}, "active_version"))


def _asha() -> str:
	"""§16.1's isolated contributing-department Author: HRMD only."""
	from frappe.utils.password import update_password

	from kentender_core.seeds.constants import TEST_PASSWORD
	from kentender_core.services import responsibility_administration as administration

	if not frappe.db.exists("User", ASHA):
		doc = frappe.get_doc({"doctype": "User", "email": ASHA, "first_name": "Asha", "last_name": "Odhiambo", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
		update_password(ASHA, TEST_PASSWORD)
	hrmd = base._unit_for(base.AUTHOR, "Departmental Author", base.HRMD_NAME)
	if not frappe.db.exists("User Responsibility Assignment", {"user": ASHA, "business_role": "Departmental Author", "organisation_unit": hrmd, "status": "Enabled"}):
		administration.grant(user=ASHA, business_role="Departmental Author", organisation_unit=hrmd, fixture_namespace=base.NS, actor="Administrator")
	return ASHA


# --------------------------------------------------------------------------
# the thirteen profiles
# --------------------------------------------------------------------------


def hold(item: str) -> Report:
	"""A submitted requisition whose item is held by an unresolved Planning correction request."""
	svc, r = _svc(), Report("REQ-SC-HOLD", "A submitted requisition whose item is held by an unresolved Planning correction request.")
	requisition = _submitted("HOLD", item)
	request = _external_request("HOLD", item, "REQ-SC-HOLD-EXTERNAL")
	r.record(requisition=requisition, correction_request=request)
	r.refused("authorisation is refused while the item is held", lambda: _authorise("HOLD", requisition), "PLN_ITEM_AUTHORISATION_HELD")
	reference = _reference(requisition)
	r.check("no reservation, drawdown, decision or handoff was created", not frappe.db.count("Funding Reservation", {"caller_reference": reference}) and not frappe.db.get_value("Procurement Requisition", requisition, "handoff"))
	r.check("the requisition is unchanged (Submitted to Procurement)", frappe.db.get_value("Procurement Requisition", requisition, "current_state") == "Submitted to Procurement")
	single = base.verify_prerequisites()["single_item"]
	r.check("the other item is not held", not (_projection(single).get("hold") or {}).get("held"))
	r.limit("No authorised proceeding exists on the held item in this world, so 'existing authorised proceedings unchanged' has nothing to observe beyond the check above.")
	r.look(base.HOPF, f"/app/procurement-requisitions/procurement-task/{_open_task(requisition, 'Head of Procurement Function')}", "REQ-DES-08-HOLD: amber hold result, Authorise absent")
	return r


def multiple_requests(item: str) -> Report:
	"""A stopped requisition with two correction requests on the item; one closed without change, the other still in progress."""
	r = Report("REQ-SC-MULTIPLE-REQUESTS", "A stopped requisition with two correction requests on the item; one closed without change, the other still in progress.")
	requisition = _submitted("MULTIPLE", item)
	first = _stop("MULTIPLE", requisition)
	second = _external_request("MULTIPLE", item, "REQ-SC-MULTIPLE-EXTERNAL")
	_dispose("MULTIPLE", first, "start")
	_dispose("MULTIPLE", second, "start")
	r.check("both requests are In progress", {frappe.db.get_value("Plan Item Correction Request", n, "status") for n in (first, second)} == {"In progress"})
	_dispose("MULTIPLE", first, "close", reason=NO_CHANGE_REASON)
	held = _projection(item).get("hold") or {}
	r.check("closing one leaves the hold in force", bool(held.get("held")) and len(held.get("unresolved_requests") or []) == 1, held)
	pln = _pln()
	plan_reference = _projection(item)["plan_reference"]
	with _as(pln.seed.PLANNER):
		pln.publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=_key("MULTIPLE", "begin-update"))
	draft = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference}, "open_successor_version")
	r.refused("the other request cannot be resolved against a correction that is not Active", lambda: _dispose("MULTIPLE", second, "resolve", correcting_plan_version=draft), "PLN_CORRECTION_NOT_ACTIVE")
	r.check("the stopped requisition recorded the first outcome and stays stopped", frappe.db.get_value("Procurement Requisition", requisition, "current_state") == "Upstream correction required")
	r.record(requisition=requisition, closed_request=first, open_request=second, draft_successor=draft)
	r.look(base.HOD, _route(requisition), "REQ-DES-11 'Another request unresolved': two request rows, the hold notice, no authorise or clear-hold control")
	return r


def correction_resolved(item: str) -> Report:
	"""A stopped requisition whose request Planning resolved against an Active correcting Plan Version, and the explicit fresh start."""
	svc, r = _svc(), Report("REQ-SC-CORRECTION-RESOLVED", "A stopped requisition whose request Planning resolved against an Active correcting Plan Version, and the explicit fresh start.")
	requisition = _submitted("RESOLVED", item)
	request = _stop("RESOLVED", requisition)
	_dispose("RESOLVED", request, "start")
	correcting = _activate_successor("RESOLVED", item)
	_dispose("RESOLVED", request, "resolve", correcting_plan_version=correcting)
	root = frappe.get_doc("Procurement Requisition", requisition)
	outcome = svc.correction.terminal_outcome(root)
	r.check("Requisitions recorded the Resolved outcome with the exact replacement lineage", bool(outcome) and outcome.outcome == "Resolved" and bool(json.loads(outcome.replacement_lineage_json or "{}").get("allocation_ids")))
	r.check("the stopped Version is preserved, not revived", root.current_state == "Upstream correction required")
	with _as(base.AUTHOR):
		fresh = svc.correction.prepare_requisition_after_plan_correction(requisition=requisition, idempotency_key=_key("RESOLVED", "fresh-start"))
	new = fresh.get("requisition")
	r.check("the explicit fresh start created a new linked Draft", bool(new) and new != requisition and frappe.db.get_value("Procurement Requisition", new, "prior_requisition_id") == requisition)
	r.check("the new Draft is pinned to the correcting Plan Version", frappe.db.get_value("Procurement Requisition", new, "plan_version_id") == correcting, correcting)
	r.check("no approval, reservation or handoff was carried across", not frappe.db.get_value("Procurement Requisition", new, "handoff") and not _decisions(new) and not frappe.db.count("Funding Reservation", {"caller_reference": _reference(new)}))
	r.limit("The correcting Plan Version carries the item forward unchanged; the §13.12 narrative (Budget Line corrected from DHI to HWD) is not re-enacted — the canonical item already uses HWD.")
	r.record(requisition=requisition, correction_request=request, correcting_plan_version=correcting, fresh_requisition=new)
	r.look(base.AUTHOR, _route(requisition), "REQ-DES-11 Resolved: 'Planning correction completed' with the outcome text")
	r.look(base.AUTHOR, _route(new), "The linked fresh Draft (REQ-DES-03)")
	return r


def closed_no_change(item: str) -> Report:
	"""A stopped requisition whose request Planning closed without change; the stopped Version never restarts."""
	svc, r = _svc(), Report("REQ-SC-CLOSED-NO-CHANGE", "A stopped requisition whose request Planning closed without change; the stopped Version never restarts.")
	requisition = _submitted("CLOSED", item)
	request = _stop("CLOSED", requisition)
	_dispose("CLOSED", request, "start")
	_dispose("CLOSED", request, "close", reason=NO_CHANGE_REASON)
	root = frappe.get_doc("Procurement Requisition", requisition)
	outcome = svc.correction.terminal_outcome(root)
	r.check("the exact no-change reason and Planner are recorded", bool(outcome) and outcome.reason == NO_CHANGE_REASON and outcome.decided_by == _pln().seed.PLANNER)
	r.check("the stopped Version stays stopped", root.current_state == "Upstream correction required")
	with _as(base.AUTHOR):
		view = svc.read.get_requisition_record(requisition=requisition)
	r.check("a fresh start is offered against unchanged eligible facts", bool((view.get("actions") or {}).get("start_new_requisition")))
	r.limit("Planning's own request/disposition times are the real time of seeding; only Requisitions' stop decision carries the §13.12 clock (10 Mar 2027, 09:00 EAT) — a seed never writes Planning rows.")
	r.record(requisition=requisition, correction_request=request)
	r.look(base.AUTHOR, _route(requisition), "REQ-DES-11 Closed without change + the fresh-start confirmation")
	return r


def outcome_ordering(item: str) -> Report:
	"""The Closed-without-change outcome, then duplicate, changed, unknown-producer, incomplete and out-of-order deliveries of it."""
	svc, pln, r = _svc(), _pln(), Report("REQ-SC-OUTCOME-ORDERING", "The Closed-without-change outcome, then duplicate, changed, unknown-producer, incomplete and out-of-order deliveries of it.")
	requisition = _submitted("ORDERING", item)
	request = _stop("ORDERING", requisition)
	_dispose("ORDERING", request, "start")
	_dispose("ORDERING", request, "close", reason=NO_CHANGE_REASON)
	recorded = frappe.get_doc("Requisition Correction Outcome", {"correction_request_id": request, "status": "Recorded"})
	disposition = frappe.get_doc("Plan Item Correction Disposition", recorded.event_id)
	event = pln.outcome_event.build(
		request=frappe.get_doc("Plan Item Correction Request", request), disposition=disposition, outcome=recorded.outcome,
		hold={"held": bool(recorded.item_hold_state), "open_requests": recorded.unresolved_request_count}, eligibility_revision=recorded.eligibility_revision, reason=recorded.reason,
	)
	stopped_version = frappe.db.get_value("Procurement Requisition", requisition, "current_version")
	stopped_before = frappe.db.get_value("Requisition Version", stopped_version, ["record_version", "content_digest"])
	deliver = svc.correction.record_plan_item_correction_outcome
	r.check("the same payload again is a no-op duplicate", deliver(event=dict(event)).get("action") == "duplicate")
	r.check("the same event identity with a changed payload is quarantined", deliver(event={**event, "reason": NO_CHANGE_REASON + " Changed."}).get("action") == "quarantined")
	r.check("an unknown producer is quarantined", deliver(event={**event, "event_id": f"{event['event_id']}-X", "producer": "Somebody else"}).get("action") == "quarantined")
	r.check("an event missing the owner identity is quarantined", deliver(event={**event, "event_id": f"{event['event_id']}-Y", "correction_request_id": ""}).get("action") == "quarantined")
	r.check("an out-of-order (earlier sequence) event is quarantined", deliver(event={**event, "event_id": f"{event['event_id']}-Z", "producer_sequence": 0}).get("action") == "quarantined")
	r.check("exactly one outcome stays recorded", frappe.db.count("Requisition Correction Outcome", {"correction_request_id": request, "status": "Recorded"}) == 1)
	r.check(
		"the stopped requisition did not change",
		frappe.db.get_value("Procurement Requisition", requisition, "current_state") == "Upstream correction required"
		and frappe.db.get_value("Requisition Version", stopped_version, ["record_version", "content_digest"]) == stopped_before,
	)
	r.check("each rejected delivery left quarantine evidence", frappe.db.count("Requisition Correction Outcome", {"status": "Quarantined", "event_id": ("like", f"Q-%:{event['event_id']}%")}) >= 4)
	r.record(requisition=requisition, correction_request=request, event_id=event["event_id"])
	r.look(base.AUTHOR, _route(requisition), "The stopped record shows one Closed-without-change outcome; the quarantined deliveries are evidence rows only")
	return r


def shared_line_short(item: str) -> Report:
	"""A submitted requisition whose two rows share HWD, with only KES 40,000,000.00 of it available."""
	svc, r = _svc(), Report("REQ-SC-SHARED-LINE-SHORT", "A submitted requisition whose two rows share HWD, with only KES 40,000,000.00 of it available.")
	projection = _projection(item)
	hwd = projection["sources"][0]["budget_line"]
	with _as(base.HOPF):
		token = svc.funding.check_funding(
			plan_item="REQ-SC-SHARED-LINE-SHORT", plan_version="REQ-SC-SHARED-LINE-SHORT", source_set_hash="REQ-SC-SHARED-LINE-SHORT",
			allocations=[{"budget_line": hwd, "plan_source_allocation": "REQ-SC-HOLD-ALLOCATION", "drawdown_line_id": "REQ-SC-HOLD-LINE", "source_organisation_unit": projection["sources"][0]["organisation_unit"], "amount": "20000000.00"}],
			correlation_id=_key("SHORT", "hold"), caller_reference="REQ-SC-SHARED-LINE-SHORT-HOLD",
		)
		svc.funding.reserve_funding(token=token["token"], source_set_hash="REQ-SC-SHARED-LINE-SHORT", idempotency_key=_key("SHORT", "hold-reserve"), caller_reference="REQ-SC-SHARED-LINE-SHORT-HOLD")
	requisition = _submitted("SHORT", item)
	reference = _reference(requisition)
	try:
		_authorise("SHORT", requisition)
		r.check("authorisation is refused for the aggregate shortfall", False, "was accepted")
	except Exception as exc:  # noqa: BLE001
		lines = (getattr(exc, "detail", None) or {}).get("lines") or []
		r.check("authorisation is refused for the aggregate shortfall", getattr(exc, "code", "") == "REQ_FUNDING_UNAVAILABLE", getattr(exc, "code", type(exc).__name__))
		r.check("the shortfall is KES 10,000,000.00 on the shared line", bool(lines) and lines[0].get("shortfall") == "10000000.00", lines)
	r.check("no drawdown, reservation, decision or handoff was created", not frappe.db.count("Funding Reservation", {"caller_reference": reference}) and "Authorise requisition" not in _decisions(requisition) and not frappe.db.get_value("Procurement Requisition", requisition, "handoff"))
	r.limit("The other 20m is held through the published check/reserve contract under the labelled caller reference REQ-SC-SHARED-LINE-SHORT-HOLD (Budget's own fixtures model another requisition's hold the same way); the profile reset releases it through Budget's release command.")
	r.record(requisition=requisition)
	r.look(base.HOPF, f"/app/procurement-requisitions/procurement-task/{_open_task(requisition, 'Head of Procurement Function')}", "REQ-DES-08-BLOCKING-FUNDING: requested 50m, available 40m, shortfall 10m; Authorise absent")
	return r


def scope_lock(item: str) -> Report:
	"""An authorised, fully drawn original proceeding (consumed by a stand-in Tender); the locked item cannot be enlarged or rebound."""
	svc, pln, r = _svc(), _pln(), Report("REQ-SC-SCOPE-LOCK", "An authorised, fully drawn original proceeding (consumed by a stand-in Tender); the locked item cannot be enlarged or rebound.")
	requisition = _submitted("SCOPE", item)
	_authorise("SCOPE", requisition)
	_consume("SCOPE", requisition, "TND-SEED-REQ-SC-SCOPE-LOCK")
	r.check("the item's scope is locked", bool((_projection(item).get("scope") or {}).get("locked")))
	with _as(base.AUTHOR):
		r.refused("a new requisition on the fully drawn locked item is refused", lambda: svc.cmd.prepare_it_equipment_requisition(plan_item_id=item, idempotency_key=_key("SCOPE", "prepare-again")), "PLN_ITEM_SCOPE_LOCKED")
	plan_reference = _projection(item)["plan_reference"]
	with _as(pln.seed.PLANNER):
		pln.publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=_key("SCOPE", "begin-update"))
		plan_item = pln.read.get_plan_item(plan_item_id=item)
		r.refused(
			"a plan update cannot restructure the locked item",
			lambda: pln.workbench.save_plan_item(plan_item=item, values={"lotting_indicator": "Packaged into lots"}, expected_record_version=plan_item["record_version"], idempotency_key=_key("SCOPE", "restructure")),
			"PLN_ITEM_SCOPE_LOCKED",
		)
	r.limit("The canonical world has no second eligible IT-equipment item (the single-department item is Non-consulting services), so 'a separate eligible item follows its own route' is not observable here.")
	r.limit("Consumption is by the seed stand-in Tender TND-SEED-REQ-SC-SCOPE-LOCK (D16), not a real Tender.")
	r.record(requisition=requisition)
	r.look(base.AUTHOR, f"/app/procurement-requisitions/new/{item}", "REQ-DES-12 'Existing procurement scope': no Start requisition")
	r.look(base.HOPF, _route(requisition), "REQ-DES-10 Consumed: 'Tender Preparation started', no Revoke")
	return r


def sequential(item: str) -> Report:
	"""A first requisition for 100 Each / KES 20m authorised and consumed; the remaining 150 Each / KES 30m supports a second requisition under the same scope lock."""
	svc, r = _svc(), Report("REQ-SC-SEQUENTIAL", "A first requisition for 100 Each / KES 20m authorised and consumed; the remaining 150 Each / KES 30m supports a second requisition under the same scope lock.")
	first = _submitted("SEQUENTIAL", item, amounts={base.HRMD_NAME: ("40", "8000000.00"), base.DHI_NAME: ("60", "12000000.00")})
	_authorise("SEQUENTIAL", first)
	_consume("SEQUENTIAL", first, "TND-SEED-REQ-SC-SEQUENTIAL")
	locked_since = (_projection(item).get("scope") or {}).get("locked_since")
	projection = _projection(item)
	r.check("150 Each / KES 30,000,000.00 remain eligible", projection.get("eligible") and projection.get("remaining_value") == "30000000.00", projection.get("remaining_value"))
	second = _draft("SEQUENTIAL-2", item)
	version = frappe.get_doc("Requisition Version", frappe.db.get_value("Procurement Requisition", second, "current_version"))
	r.check("the second requisition draws exactly the remainder", sum(int(l.requested_quantity) for l in version.drawdown_lines) == 150)
	r.check("no extra source or fresh allowance appeared", len(version.drawdown_lines) == 2)
	r.check("the scope lock stayed the first lock", (_projection(item).get("scope") or {}).get("locked_since") == locked_since)
	r.limit("Consumption is by the seed stand-in Tender TND-SEED-REQ-SC-SEQUENTIAL (D16), not a real Tender. Every drawdown line must be above zero, so the first draw splits 40 / 60 across the two departments.")
	r.record(first_requisition=first, second_requisition=second)
	r.look(base.AUTHOR, _route(second), "The second Draft: amounts show the remaining 60 + 90 Each")
	r.look(base.HOPF, _route(first), "The first, consumed requisition")
	return r


def lead_change(item: str) -> Report:
	"""At Procurement review the Head of Procurement Function changes the submitting department; the copied Draft needs the new lead's certification."""
	svc, r = _svc(), Report("REQ-SC-LEAD-CHANGE", "At Procurement review the Head of Procurement Function changes the submitting department; the copied Draft needs the new lead's certification.")
	requisition = _submitted("LEAD", item)
	submitted_version = frappe.db.get_value("Procurement Requisition", requisition, "current_version")
	hrmd = base._unit_for(base.AUTHOR, "Departmental Author", base.HRMD_NAME)
	task = _open_task(requisition, "Head of Procurement Function")
	with _as(base.HOPF):
		svc.lifecycle.change_requisition_lead_department(
			task=task, new_lead_org_unit=hrmd, reason="HR Management and Development leads the training rollout and should certify this requisition.",
			expected_record_version=frappe.db.get_value("Requisition Task", task, "record_version"), idempotency_key=_key("LEAD", "change"),
		)
	root = frappe.get_doc("Procurement Requisition", requisition)
	r.check("the reviewed Version keeps its original certification", frappe.db.get_value("Requisition Version", submitted_version, "certified_lead_org_unit_id") != hrmd)
	r.check("a copied Draft opened with the new lead", root.current_state == "Draft" and root.lead_org_unit_id == hrmd, root.lead_org_unit_id)
	r.check("nothing can be authorised until the new lead submits", not _open_task(requisition, "Head of Procurement Function"))
	r.record(requisition=requisition, reviewed_version=submitted_version)
	r.look(base.AUTHOR, _route(requisition), "REQ-DES-12 'New submitting department': earlier and new departments, Open copied Draft")
	return r


def revoke_consume_race(item: str) -> Report:
	"""Consumption wins: the authorisation is consumed by a stand-in Tender and the later revocation is refused."""
	svc, r = _svc(), Report("REQ-SC-REVOKE-CONSUME-RACE", "Consumption wins: the authorisation is consumed by a stand-in Tender and the later revocation is refused.")
	requisition = _submitted("RACE", item)
	_authorise("RACE", requisition)
	_consume("RACE", requisition, "TND-SEED-REQ-SC-RACE")
	with _as(base.HOPF):
		r.refused(
			"revocation after consumption is refused",
			lambda: svc.authorise.revoke_unconsumed_authorisation(requisition=requisition, reason="Attempted after Tender Preparation already began.", expected_record_version=_root_version(requisition), idempotency_key=_key("RACE", "revoke")),
			"REQ_HANDOFF_CONSUMED",
		)
	reference = _reference(requisition)
	r.check("the funding reservations stay in force", frappe.db.count("Funding Reservation", {"caller_reference": reference, "status": ("in", ("Active", "Partially Converted"))}) == 2)
	r.check("the handoff is consumed and not revoked", bool(frappe.db.get_value("Procurement Requisition", requisition, "handoff_consumed_at")) and frappe.db.get_value("Procurement Requisition", requisition, "current_state") == "Authorised")
	r.refused("a second Tender cannot consume the same handoff", lambda: _consume("RACE-2", requisition, "TND-SEED-REQ-SC-RACE-2"), "REQ_HANDOFF_CONFLICT")
	r.limit("Only the consumption-wins ordering can be left as a state; the revocation-wins ordering (a revoked handoff cannot be consumed) is proven by test_authorise.")
	r.record(requisition=requisition)
	r.look(base.HOPF, _route(requisition), "REQ-DES-10 Consumed; the revoke race notice appears if revocation is attempted")
	return r


def precision(item: str) -> Report:
	"""A Draft whose exact partial amount (KES 19,999,999.99) was accepted after inexact values were refused."""
	svc, r = _svc(), Report("REQ-SC-PRECISION", "A Draft whose exact partial amount (KES 19,999,999.99) was accepted after inexact values were refused.")
	requisition = _draft("PRECISION", item)
	with _as(base.AUTHOR):
		view = svc.read.get_requisition_record(requisition=requisition)
		line = next(l for l in view["amounts"] if l["department"] == base.HRMD_NAME)

		def save(quantity, value):
			current = svc.read.get_requisition_record(requisition=requisition)
			return svc.cmd.save_requisition_summary(
				requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": line["drawdown_line_id"], "requested_quantity": quantity, "requested_value": value}]},
				expected_record_version=current["header"]["version_record_version"], idempotency_key=_key("PRECISION", f"{quantity}-{value}"),
			)

		r.refused("a third decimal place is refused", lambda: save("100", "20000000.005"), "REQ_MONEY_PRECISION_INVALID")
		r.refused("a binary float is refused", lambda: save("100", 20000000.0), "REQ_MONEY_PRECISION_INVALID")
		r.refused("an exponent is refused", lambda: save("100", "2e7"), "REQ_MONEY_PRECISION_INVALID")
		r.refused("an overflowing amount is refused", lambda: save("100", "1" + "0" * 18 + ".00"), "REQ_MONEY_PRECISION_INVALID")
		r.refused("a fractional quantity is refused", lambda: save("99.5", "19999999.99"), "REQ_QUANTITY_PRECISION_INVALID")
		save("100", "19999999.99")
	stored = frappe.db.get_value("Requisition Drawdown Line", {"drawdown_line_id": line["drawdown_line_id"]}, "requested_value")
	r.check("the exact amount is stored exactly, without rounding", stored == "19999999.99", stored)
	r.record(requisition=requisition)
	r.look(base.AUTHOR, _route(requisition), "REQ-DES-03 amounts: HRMD requests KES 19,999,999.99 with Use full available amount")
	return r


def compatibility(item: str) -> Report:
	"""Each §5A check a real Plan Item can fail on this site fails on its own before any Draft is created; one failing case is left in place."""
	from kentender_procurement.procurement_requisitions.services import compatibility as compatibility_service

	svc, r = _svc(), Report("REQ-SC-COMPATIBILITY", "Each §5A check a real Plan Item can fail on this site fails on its own before any Draft is created; one failing case is left in place.")
	single = base.verify_prerequisites()["single_item"]
	with _as(base.AUTHOR):
		preview = svc.read.get_start_preview(plan_item_id=single)
	r.check("the Non-consulting-services item fails before a Draft (procurement category / requirement type)", preview.get("state") == "unsupported" and not preview.get("may_start"), preview.get("failed_check"))
	methods = [m for m in frappe.get_all("Procurement Method", pluck="name") if m != "Open Tender"]
	cases = [
		("procurement_method", {"procurement_method": methods[0]} if methods else None),
		("lotting_indicator", {"lotting_indicator": "Packaged into lots", "lot_count": 2}),
		("county_resident_reservation", {"county_resident_reservation": 1}),
		("reservation_category", {"reservation_category": "Women"}),
		("reservation_category", {"reservation_category": "Persons with disabilities"}),
		("reservation_category", {"reservation_category": "Other disadvantaged group"}),
	]

	def attempt(check: str, edit: dict[str, Any], label: str) -> tuple[str, list[str], str]:
		"""Publish the edit, then try to Prepare. Returns (outcome, failing, detail)."""
		try:
			_activate_successor(f"COMPAT-{label}", item, edit=edit)
		except Exception as exc:  # noqa: BLE001 — Planning refusing to publish is the observation
			return "unpublishable", [], getattr(exc, "code", "") or cstr(exc)[:120]
		failing = [c.test for c in compatibility_service.check(_projection(item)) if not c.ok]
		with _as(base.AUTHOR):
			try:
				svc.cmd.prepare_it_equipment_requisition(plan_item_id=item, idempotency_key=_key("COMPAT", f"prepare-{label}"))
			except Exception as exc:  # noqa: BLE001
				return "refused", failing, getattr(exc, "code", type(exc).__name__)
		return "accepted", failing, ""

	showcase = None
	for check, edit in cases:
		if edit is None:
			r.limit(f"{check}: this site has no other published method to try.")
			continue
		value = list(edit.values())[0]
		label = f"{check}-{value}".replace(" ", "-")
		frappe.db.savepoint("req_sc_compat")
		outcome, failing, detail = attempt(check, edit, label)
		frappe.db.rollback(save_point="req_sc_compat")
		if outcome == "unpublishable":
			r.limit(f"{check}={value}: Planning will not publish this value on its own ({detail}), so no real item can carry it.")
		elif outcome == "accepted":
			r.limit(f"{check}={value}: supported on this site by the installed Tender format and its verified rule, so it cannot fail here.")
		else:
			r.check(f"{check}={value}: only this check fails and Prepare is refused ({detail}), no Draft created", failing == [check] and not frappe.db.count("Procurement Requisition", {"plan_item_id": item}), f"failing={failing}")
			if showcase is None or check == "reservation_category":
				showcase = (check, edit, label)
	r.limit("Currency (always KES), Award package (always 1) and Plan horizon (only 'Single year') are fixed values in Planning's projection, so no real Plan Item can fail them; test_compatibility proves each (D18).")
	r.limit("The requirement-type and procurement-category failures come together on the canonical single-department item; no canonical item fails one without the other.")
	r.limit("Each case is published, observed and rolled back, so the next case starts from the base item.")
	if showcase:
		attempt(*showcase)
		r.look(base.AUTHOR, f"/app/procurement-requisitions/new/{item}", f"REQ-DES-02: {showcase[0]} = {list(showcase[1].values())[0]} refused; Start requisition disabled")
	r.look(base.AUTHOR, f"/app/procurement-requisitions/new/{single}", "REQ-DES-02-UNSUPPORTED on the services item")
	return r


def open_slot(item: str) -> Report:
	"""Two departments start the same item: one root exists. After revocation, a corrected Draft and a fresh start compete for the one slot."""
	svc, r = _svc(), Report("REQ-SC-OPEN-SLOT", "Two departments start the same item: one root exists. After revocation, a corrected Draft and a fresh start compete for the one slot.")
	asha = _asha()
	with _as(base.AUTHOR):
		first = svc.cmd.prepare_it_equipment_requisition(plan_item_id=item, idempotency_key=_key("SLOT", "grace"))
	with _as(asha):
		second = svc.cmd.prepare_it_equipment_requisition(plan_item_id=item, idempotency_key=_key("SLOT", "asha"))
	r.check("the second department is sent to the one existing root", second.get("action") == "existing" and second.get("requisition") == first["requisition"])
	r.check("exactly one root exists", frappe.db.count("Procurement Requisition", {"plan_item_id": item}) == 1)
	requisition = first["requisition"]
	with _as(base.AUTHOR):
		base._build_item_package(requisition)
		svc.lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=_root_version(requisition), idempotency_key=_key("SLOT", "send"))
	with _as(base.HOD):
		svc.lifecycle.submit_requisition_to_procurement(requisition=requisition, task=_open_task(requisition, "Head of User Department"), expected_record_version=_root_version(requisition), idempotency_key=_key("SLOT", "submit"))
	_authorise("SLOT", requisition)
	with _as(base.HOPF):
		svc.authorise.revoke_unconsumed_authorisation(requisition=requisition, reason="The authorised warranty terms must be corrected before tendering.", expected_record_version=_root_version(requisition), idempotency_key=_key("SLOT", "revoke"))
	with _as(base.AUTHOR):
		svc.correction.create_requisition_correction_draft(requisition=requisition, expected_record_version=_root_version(requisition), idempotency_key=_key("SLOT", "correction-draft"))
	with _as(asha):
		competing = svc.cmd.prepare_it_equipment_requisition(plan_item_id=item, idempotency_key=_key("SLOT", "asha-fresh"))
	r.check("the competing fresh start is sent to the corrected Draft holding the slot", competing.get("action") == "existing" and competing.get("requisition") == requisition)
	r.check("still exactly one root", frappe.db.count("Procurement Requisition", {"plan_item_id": item}) == 1)
	r.limit("The two starts run one after the other in one process; the database-level guard under true concurrency (a unique open-slot key) is proven by test_draft_commands.")
	r.record(requisition=requisition, asha=asha)
	r.look(asha, _route(requisition), "Asha (HRMD only) on the combined corrected Draft: her row editable, the rest read-only (REQ-DES-03-CONTRIBUTOR)")
	return r


PROFILES: dict[str, Callable[[str], Report]] = {
	"REQ-SC-HOLD": hold,
	"REQ-SC-MULTIPLE-REQUESTS": multiple_requests,
	"REQ-SC-CORRECTION-RESOLVED": correction_resolved,
	"REQ-SC-CLOSED-NO-CHANGE": closed_no_change,
	"REQ-SC-OUTCOME-ORDERING": outcome_ordering,
	"REQ-SC-SHARED-LINE-SHORT": shared_line_short,
	"REQ-SC-SCOPE-LOCK": scope_lock,
	"REQ-SC-SEQUENTIAL": sequential,
	"REQ-SC-LEAD-CHANGE": lead_change,
	"REQ-SC-REVOKE-CONSUME-RACE": revoke_consume_race,
	"REQ-SC-PRECISION": precision,
	"REQ-SC-COMPATIBILITY": compatibility,
	"REQ-SC-OPEN-SLOT": open_slot,
}


def list_profiles() -> list[dict[str, str]]:
	return [{"profile": name, "summary": (fn.__doc__ or "").strip()} for name, fn in PROFILES.items()]


def load_profile(*, profile: str, commit: bool = True) -> dict[str, Any]:
	"""Clean the namespace, build one §16.4A profile, record it as loaded and
	print a concise created/refused report (§16.5)."""
	if profile not in PROFILES:
		frappe.throw(f"Unknown Requisitions profile {profile!r}. Choose one of: {', '.join(PROFILES)}")
	prereqs = _clean_namespace()
	report = PROFILES[profile](prereqs["combined_item"])
	frappe.defaults.set_global_default(LOADED_KEY, profile)
	if commit:
		frappe.db.commit()
	data = {**report.data, "ok": report.ok}
	lines = [f"{'PROFILE_OK' if report.ok else 'PROFILE_FAILED'} {profile} — {report.data['summary']}"]
	lines += [f"  [{'ok' if row['ok'] else 'FAIL'}] {row['check']}" + (f" ({row['detail']})" if row["detail"] and not row["ok"] else "") for row in report.data["results"]]
	lines += [f"  look: {l['actor']} → {l['route']} — {l['what']}" for l in report.data["look"]]
	lines += [f"  limit: {t}" for t in report.data["limits"]]
	print("\n".join(lines))
	if not report.ok:
		# Loaded and committed as it stands, but the command must not read as a
		# success: a required §16.4A result was not observed.
		missing = [row["check"] for row in report.data["results"] if not row["ok"]]
		frappe.throw(f"{profile} loaded, but {len(missing)} required result(s) were not observed: {'; '.join(missing)}", title="REQ_PROFILE_RESULT_MISSING")
	return data
