# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Delivery: appointment, arrival, inspection, technical certificate, acceptance, accepted-subset receipt (CM-CHG-001 v0.8 sections 5.4 to 5.6, 6.1, 6.2.1, 7; plan Phase 4).

* **Appointment.** HOP recommends a chair and at least two other members; the Accounting Officer appoints or returns with a reason; each member **personally declares interest** before acting, and a
  declared conflict suspends that member and opens replacement work (CM_APPOINTMENT says who is missing). Appointments supplement the registered Contract inspection responsibility; neither alone grants.
* **Arrival** is recorded once and never edited: what was observed, when, where, by whom. It creates custody and inspection work only; no native receipt exists for goods merely because they arrived.
* **Inspection** is generated from the contract's frozen criteria, never an editable template: typed comparisons give Meets, Does not meet or Needs review (a blank or unreadable reading).
* **Technical certificate** is the technical certifier's personal proof of the exact findings (section 150(3)); it reuses the recorded observations and asks for no repeat of the checks.
* **Acceptance.** The chair prepares one report: for every unit of the covered arrivals, accepted, rejected or deferred, with the quantities adding up to what the report covers. Every required current
  member signs that exact version; the last proof makes one effective decision and one posting intent atomically. `post_accepted_receipt` then posts the accepted subset to ERPNext once.

Each signature is the shared two-step attempt (`signing_flow.py`)."""

from __future__ import annotations

import operator
from typing import Any

import frappe
from frappe.utils import add_days, cint, cstr, flt, get_datetime

from kentender_contracts.native import adapter
from kentender_contracts.services import authority, bindings, clock, events, formation, intents, people, position, preflight, records, segregation, service_principal, signing_flow, work
from kentender_contracts.services.errors import Guards, fail, invalid

CASE = "Contract Case"
APPOINTMENT = "Contract Appointment"
ARRIVAL = "Contract Arrival"
INSPECTION = "Contract Inspection"
CERTIFICATE = "Contract Certificate"
ACCEPTANCE = "Contract Acceptance"
CHAIR = "Chair"
COMPARATORS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "=": operator.eq, "==": operator.eq}
MEETS, DOES_NOT_MEET, NEEDS_REVIEW = "Meets", "Does not meet", "Needs review"


def _case(case: str):
	preflight.exists(case)
	return frappe.get_doc(CASE, case)


def _unit(case: str) -> str:
	return frappe.db.get_value(CASE, case, "managing_unit") or ""


# -- the appointment --------------------------------------------------------------------------------------------------------------------
def appointment_state(case: str) -> dict[str, Any]:
	"""Who may act as an inspector now: the appointment in force, who has declared, who is in conflict, and whether the inspectors are ready."""
	found = bindings.effective_appointment(case)
	if not found:
		return {"appointment": None, "members": [], "ready": False, "missing": [], "conflicts": []}
	members = found["members"]
	missing = [m["user"] for m in members if not m.get("declared_at")]
	conflicts = [m["user"] for m in members if m.get("conflict")]
	return {**found, "ready": not missing and not conflicts, "missing": missing, "conflicts": conflicts}


def require_ready(case: str) -> dict[str, Any]:
	state = appointment_state(case)
	if not state["ready"]:
		fail("CM_APPOINTMENT", appointment=state["appointment"], undeclared=state["missing"], conflicted=state["conflicts"],
			reason="The inspectors are appointed and each has declared interest before they act." if state["appointment"] else "No inspectors are appointed for this contract.")
	return state


def eligibility(user: str, role: str) -> str:
	"""Why this person cannot be named for this responsibility, in the command's own words (the record picker shows the same text), or an empty string."""
	if not user or not frappe.db.exists("User", user):
		return "Every member must be a person with an account."
	if not people.holds(user, role):
		return f"{people.full_name(user)} does not hold the {role} responsibility."
	return ""


def _members(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	problems: dict[str, str] = {}
	members = []
	seen: set[str] = set()
	for row in rows or []:
		user = cstr(row.get("user")).strip()
		problem = eligibility(user, "Contract inspection")
		certifier = bool(row.get("certifier"))
		if not problem and certifier:
			problem = eligibility(user, "Technical certification")
		if problem:
			problems.setdefault("members", problem)
			continue
		if user.lower() in seen:
			problems.setdefault("members", "A person can be named once.")
		seen.add(user.lower())
		members.append({"user": user, "name": people.full_name(user), "capacity": CHAIR if row.get("capacity") == CHAIR else "Member", "certifier": certifier, "role_label": cstr(row.get("role_label")),
			"declared_at": None, "conflict": None})
	if len(members) < 3:
		problems.setdefault("members", "Name a chair and at least two other members.")
	if sum(1 for m in members if m["capacity"] == CHAIR) != 1:
		problems.setdefault("members", "Name exactly one chair.")
	if not any(m["certifier"] for m in members):
		problems.setdefault("members", "Name the member who gives the technical confirmation.")
	invalid(problems)
	return members


ACCEPTANCE_AUTHORITY = ("Committee accepts", "Accounting Officer decides")


def recommend_inspectors(case: str, *, expected_version: int, idempotency_key: str, actor: str, members: list[dict[str, Any]], scope: str = "All deliveries under this contract", reason: str = "",
		from_date: str = "", until_date: str = "", acceptance: str = "Committee accepts") -> dict[str, Any]:
	"""`RecommendContractInspectors`: HOP names the written appointment for the Accounting Officer."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		named = _members(members)
		invalid({"acceptance": "" if acceptance in ACCEPTANCE_AUTHORITY else "Choose who accepts."})
		version = records.next_number(APPOINTMENT, {"contract_case": case}, "version_no")
		for earlier in frappe.get_all(APPOINTMENT, filters={"contract_case": case, "state": "Recommended"}, pluck="name"):
			records.update(frappe.get_doc(APPOINTMENT, earlier), state="Superseded")
		row = records.new(APPOINTMENT, contract_case=case, version_no=version, state="Recommended", scope=scope, acceptance=acceptance, reference=f"{case}/APP/{version}", members_json=records.dumps(named), recommended_by=actor,
			reason=reason, effective_from=get_datetime(from_date) if cstr(from_date).strip() else None, effective_to=get_datetime(until_date) if cstr(until_date).strip() else None, record_version=1)
		work.finish(case, command="RecommendContractInspectors", actor=actor)
		work.assign(case, "AppointContractInspectors", "Appoint the inspectors for this contract.", f"appointment {version}", version, work.holders("Accounting Officer"), role="Accounting Officer")
		work.assign(case, work.waiting_command("AppointContractInspectors", "appointment"), "Waiting for the appointment.", f"appointment {version}", version, work.holders(work.HOP), role=work.HOP, state="Waiting")
		events.record(case, "Inspectors recommended", actor, f"Appointment {version} recommended.", appointment=row.name)
		return records.summary(doc, appointment=row.name, appointment_version=version)

	return records.command("RecommendContractInspectors", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "members": members, "scope": scope, "from": from_date, "until": until_date, "acceptance": acceptance},
		body=body, authorise=lambda: preflight.acts_as_preparer(actor, _unit(case)))


def appoint_inspectors(case: str, *, appointment: str, expected_version: int, idempotency_key: str, actor: str, from_date: str = "", until_date: str = "") -> dict[str, Any]:
	"""`AppointContractInspectors`: the Accounting Officer's written appointment. A later appointment applies from then on; the earlier one stays as history."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(APPOINTMENT, appointment)
		if row.contract_case != case or row.state != "Recommended":
			fail("CM_CHANGED", appointment=appointment, state=row.state)
		now = clock.now()
		earlier_rows = [frappe.get_doc(APPOINTMENT, e) for e in frappe.get_all(APPOINTMENT, filters={"contract_case": case, "state": "Appointed"}, pluck="name")]
		for earlier in earlier_rows:
			records.update(earlier, state="Replaced", effective_to=now)
		members = records.loads(row.members_json, [])
		kept = _carry_declarations(members, [m for e in earlier_rows for m in records.loads(e.members_json, [])])
		start = get_datetime(from_date) if cstr(from_date).strip() else (row.effective_from or now)
		end = get_datetime(until_date) if cstr(until_date).strip() else row.effective_to
		records.update(row, state="Appointed", appointed_by=actor, effective_from=start, effective_to=end, members_json=records.dumps(members), record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="AppointContractInspectors", subject=f"appointment {row.version_no}", actor=actor)
		for member in members:
			if member["user"].lower() not in kept:
				work.assign(case, "DeclareContractInterest", "Declare any interest before you act on this contract.", f"appointment {row.version_no}", row.version_no, [member["user"]], role="Contract inspection")
		if any(m["user"].lower() not in kept for m in members):
			work.assign(case, work.waiting_command("DeclareContractInterest", "members"), "Waiting for the declarations.", f"appointment {row.version_no}", row.version_no, work.holders(work.HOP), role=work.HOP, state="Waiting")
		reconstitute(case, earlier_rows, members, actor)
		events.record(case, "Inspectors appointed", actor, f"Appointment {row.version_no} in force.", appointment=row.name)
		return records.summary(doc, appointment=row.name)

	return records.command("AppointContractInspectors", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "appointment": appointment, "from": from_date, "until": until_date},
		body=body, authorise=lambda: authority.require(actor, "Accounting Officer"))


def _carry_declarations(members: list[dict[str, Any]], earlier: list[dict[str, Any]]) -> set[str]:
	"""A member who stays in the successor appointment keeps the personal declaration they already made (and a recorded conflict keeps them out until replaced); a new member declares for themselves.
	Returns the users whose declaration was carried."""
	had = {m["user"].lower(): m for m in earlier if m.get("declared_at") and not m.get("conflict")}
	kept = set()
	for member in members:
		found = had.get(member["user"].lower())
		if found:
			member["declared_at"], member["conflict"] = found["declared_at"], None
			kept.add(member["user"].lower())
	return kept


def reconstitute(case: str, earlier: list[Any], members: list[dict[str, Any]], actor: str) -> None:
	"""A replacement applies from now on and nothing earlier is rewritten (section 5.6). Work held by a member who is no longer appointed passes to the people now appointed, and an acceptance report
	still awaiting signatures is superseded by a reviewed successor: its signatures stay on it as history, so no earlier signature is ever read as a new member's."""
	if not earlier:
		return
	before = {m["user"].lower() for e in earlier for m in records.loads(e.members_json, [])}
	now_users = {m["user"].lower() for m in members}
	removed = before - now_users
	inspectors = [m["user"] for m in members]
	certifiers = [m["user"] for m in members if m.get("certifier")]
	chair = next((m["user"] for m in members if m["capacity"] == CHAIR), "")
	for user in removed:
		for task in frappe.get_all("Contract Task", filters={"contract_case": case, "holder": user, "state": ["in", list(work.LIVE)]}, fields=["name", "command", "subject", "subject_version", "title"]):
			if task.command.startswith("DeclareContractInterest") or task.command.startswith("RecommendContractInspectors"):
				continue
			doc = frappe.get_doc("Contract Task", task.name)
			records.append_json(doc, "history_json", {"state": "Superseded", "at": str(clock.now()), "by": actor, "reason": "The appointment changed."})
			records.update(doc, state="Superseded", completed_at=clock.now())
			if task.command == "RecordInspectionObservations":
				work.assign(case, "RecordInspectionObservations", task.title, task.subject, cint(task.subject_version) or 1, inspectors, role="Contract inspection")
			elif task.command == "SignTechnicalCertificate" and certifiers:
				work.assign(case, "SignTechnicalCertificate", task.title, task.subject, cint(task.subject_version) or 1, certifiers, role="Technical certification")
	if not removed and not (now_users - before):
		return
	for name in frappe.get_all(ACCEPTANCE, filters={"contract_case": case, "state": "Awaiting signatures"}, pluck="name"):
		report = frappe.get_doc(ACCEPTANCE, name)
		if {s["user"].lower() for s in records.loads(report.signers_json, [])} == now_users:
			continue
		records.update(report, state="Superseded", record_version=cint(report.record_version) + 1)
		work.finish(case, subject=f"acceptance {report.version_no}", state="Superseded", actor=actor)
		for arrival in records.loads(report.arrivals_json, []):
			number = frappe.db.get_value(ARRIVAL, arrival, "arrival_no")
			work.assign(case, "PrepareAcceptanceReport", "Prepare the acceptance report again: the appointment changed.", f"arrival {number}", 1, [chair], role=CHAIR)
		events.record(case, "Acceptance report reconstituted", actor, f"Acceptance report {report.version_no} was superseded because the appointment changed; its signatures stay as history.", report=report.name)


def return_appointment(case: str, *, appointment: str, expected_version: int, idempotency_key: str, actor: str, reason: str) -> dict[str, Any]:
	"""`ReturnContractAppointment`: the Accounting Officer returns the recommendation to HOP with reasons."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"reason": "" if cstr(reason).strip() else "Enter the reason."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(APPOINTMENT, appointment)
		if row.contract_case != case or row.state != "Recommended":
			fail("CM_CHANGED", appointment=appointment, state=row.state)
		records.update(row, state="Returned", reason=reason, record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="AppointContractInspectors", subject=f"appointment {row.version_no}", actor=actor)
		work.assign(case, "RecommendContractInspectors", "Recommend the inspectors again: the appointment was returned.", f"appointment {row.version_no + 1}", row.version_no + 1, work.holders(work.HOP), role=work.HOP)
		events.record(case, "Appointment returned", actor, f"Appointment {row.version_no} returned: {reason}", appointment=row.name)
		return records.summary(doc, appointment=row.name)

	return records.command("ReturnContractAppointment", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "appointment": appointment, "reason": reason},
		body=body, authorise=lambda: authority.require(actor, "Accounting Officer"))


def declare_interest(case: str, *, expected_version: int, idempotency_key: str, actor: str, conflict: str = "") -> dict[str, Any]:
	"""`DeclareContractInterest`: the member's own declaration. A declared conflict suspends their authority and opens replacement work for HOP."""
	preflight.exists(case)

	def authorise() -> None:
		if not bindings.member(case, actor):
			fail("CM_AUTHORITY", missing="appointment", capacity="inspector", reason="You are not appointed to this contract.")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		found = bindings.effective_appointment(case)
		row = frappe.get_doc(APPOINTMENT, found["appointment"])
		members = records.loads(row.members_json, [])
		mine = next(m for m in members if m["user"].lower() == actor.lower())
		if mine.get("declared_at") and (mine.get("conflict") or not cstr(conflict).strip()):
			return records.summary(doc, appointment=row.name, already=True)  # a declaration is made once; a conflict that arises later can still be declared, and never withdrawn
		mine["declared_at"] = mine.get("declared_at") or str(clock.now())
		mine["conflict"] = {"reason": conflict.strip(), "at": str(clock.now())} if cstr(conflict).strip() else None
		records.update(row, members_json=records.dumps(members), record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="DeclareContractInterest", subject=f"appointment {row.version_no}", actor=actor, holder=actor)
		if mine["conflict"]:
			for task in frappe.get_all("Contract Task", filters={"contract_case": case, "holder": actor, "state": ["in", list(work.LIVE)], "command": ["not like", "DeclareContractInterest%"]}, pluck="name"):
				held = frappe.get_doc("Contract Task", task)
				records.append_json(held, "history_json", {"state": "Superseded", "at": str(clock.now()), "by": actor, "reason": "A conflict was declared."})
				records.update(held, state="Superseded", completed_at=clock.now())
			work.assign(case, "RecommendContractInspectors", "Recommend a replacement: a member declared a conflict.", f"replacement for {mine['user']}", row.version_no, work.holders(work.HOP), role=work.HOP)
			events.record(case, "Conflict declared", actor, "A member declared a conflict of interest.", appointment=row.name)
		else:
			events.record(case, "Interest declared", actor, f"{mine['name']} declared no conflict of interest.", appointment=row.name)
		if all(m.get("declared_at") for m in members):
			work.finish(case, command=work.waiting_command("DeclareContractInterest", "members"), actor=actor)
		return records.summary(doc, appointment=row.name, conflict=bool(mine["conflict"]))

	return records.command("DeclareContractInterest", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "conflict": conflict}, body=body, authorise=authorise)


# -- arrival --------------------------------------------------------------------------------------------------------------------------
def _terms_for(case: str, *states: str) -> dict[str, Any]:
	name = frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": ["in", list(states)]}, "terms_json", order_by="version_no desc")
	return records.loads(name) if name else {}


def _earlier_references(case: str, reference: str) -> list[Any]:
	if not cstr(reference).strip():
		return []
	return [a for a in frappe.get_all(ARRIVAL, filters={"contract_case": case}, fields=["name", "delivery_reference", "supplier_reference", "items_json"]) if cstr(a.supplier_reference).strip().lower() == reference.strip().lower()]


def record_arrival(case: str, *, expected_version: int, idempotency_key: str, actor: str, received_at: str, destination: str, items: list[dict[str, Any]], notes: str = "", supplier_reference: str = "") -> dict[str, Any]:
	"""`RecordContractArrival`: what physically arrived. Immutable; creates custody and inspection work, never a native receipt.

	Goods the contract does not expect are recorded, not refused, and are attributable exceptions that are never accepted or used: **excess** (more than the unfulfilled entitlement; the surplus units are held
	apart and are neither inspected nor decided), **unexpected** (an item no line names), **premature** (the agreement is not yet in force; inspection waits for it) and **ambiguous** (a supplier delivery
	reference already used for other units). The same units under the same reference are a duplicate and are refused. Replacement units name the rejected units they replace and consume the original
	entitlement, never a new order quantity (section 5.4)."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Awaiting signatures")
		premature = doc.lifecycle == "Awaiting signatures"
		terms = _terms_for(case, "Effective") or _terms_for(case, "Awaiting signatures")
		lines = {l["line_id"]: l for l in terms.get("lines", [])}
		held = position.position(case) if not premature else {"lines": {}, "units": {}}
		services = service_lines(terms)
		number = records.next_number(ARRIVAL, {"contract_case": case}, "arrival_no")
		problems: dict[str, str] = {}
		seen_before = set(held["units"])
		clean, exceptions = [], []
		for item in items or []:
			quantity, units = cint(item.get("quantity")), [cstr(u).strip() for u in item.get("units") or [] if cstr(u).strip()]
			line = lines.get(item.get("line_id"))
			if quantity <= 0 or (line is None and not cstr(item.get("description")).strip()):
				problems["items"] = "Name an ordered line (or describe unexpected goods) and a quantity above zero."
				continue
			if len(units) > quantity or len(set(units)) != len(units):
				problems["items"] = "Each unit is named once, and no more units than the quantity."
				continue
			if set(units) & seen_before:
				fail("CM_DUPLICATE", units=sorted(set(units) & seen_before), reason="A unit with this identity has already arrived.")
			if line is not None and line["line_id"] in services:  # a service is performed, not received: each performance is identified by its reference (or a generated one) so its evidence has something to attach to
				units = units + [f"SVC-{number:03d}-{line['line_id']}-{k}" for k in range(len(units) + 1, quantity + 1)]
			entry: dict[str, Any] = {"line_id": line["line_id"] if line else "", "item": (line.get("description") or line.get("item")) if line else cstr(item.get("description")).strip(), "quantity": quantity, "units": units,
				"unidentified": quantity - len(units)}
			if line is None:
				exceptions.append({"kind": "Unexpected", "item": entry["item"], "quantity": quantity})
			else:
				row = held["lines"].get(line["line_id"], {})
				committed = cint(row.get("accepted")) + cint(row.get("pending_decision")) + cint(row.get("deferred")) + cint(row.get("unidentified"))
				excess = max(0, committed + quantity - cint(line["quantity"])) if not premature else max(0, quantity - cint(line["quantity"]))
				if excess:
					named_excess = units[len(units) - min(excess, len(units)):] if units else []
					entry["excess_quantity"], entry["excess_units"] = excess, named_excess
					entry["unidentified"] = max(0, entry["unidentified"] - (excess - len(named_excess)))
					exceptions.append({"kind": "Excess", "item": entry["item"], "line_id": line["line_id"], "quantity": excess, "units": named_excess})
				replaces = [cstr(u).strip() for u in item.get("replaces") or [] if cstr(u).strip()]
				if replaces:
					bad = [u for u in replaces if (held["units"].get(u) or {}).get("status") not in ("Rejected", "Returned")]
					already = {r for a in arrivals_all(case) for it in a["items"] for r in (it.get("replaces") or {}).values()}
					if bad or len(replaces) > len(units) or set(replaces) & already:
						problems["items"] = "A replacement names the rejected units it replaces, once each: " + (", ".join(bad) + " is not a rejected unit." if bad else "one replacement per rejected unit.")
						continue
					entry["replaces"] = dict(zip(units, replaces))
			clean.append(entry)
		if not clean:
			problems["items"] = problems.get("items") or "Record what arrived."
		if any(e["line_id"] in services for e in clean) and any(e["line_id"] not in services for e in clean):
			problems["items"] = "Record a service on its own: it is inspected on its own evidence."
		if not cstr(received_at).strip():
			problems["received_at"] = "Enter when the goods arrived."
		if not cstr(destination).strip():
			problems["destination"] = "Enter where the goods were received."
		invalid(problems)
		for earlier in _earlier_references(case, supplier_reference):
			before = {u for it in records.loads(earlier.items_json, []) for u in it.get("units", [])}
			now = {u for it in clean for u in it["units"]}
			if not before and not now and sum(i["quantity"] for i in records.loads(earlier.items_json, [])) == sum(i["quantity"] for i in clean):  # (named units that repeat were refused above)
				fail("CM_DUPLICATE", delivery=earlier.delivery_reference, reason="A delivery with this supplier reference and the same goods is already recorded.")
			exceptions.append({"kind": "Ambiguous", "reference": supplier_reference.strip(), "earlier": earlier.delivery_reference})
		if premature:
			exceptions.append({"kind": "Premature", "reason": "The agreement is not yet in force."})
		row = records.new(ARRIVAL, contract_case=case, arrival_no=number, delivery_reference=f"DEL-{number:03d}", supplier_reference=cstr(supplier_reference).strip(), received_at=get_datetime(received_at),
			recorded_at=clock.now(), receiver=actor, destination=destination, items_json=records.dumps(clean), exceptions_json=records.dumps(exceptions), notes=notes, state="Recorded", record_version=1)
		records.bump(doc, delivery_state="Goods received" if not premature else "Goods received before the agreement is in force")
		subject = f"arrival {number}"
		if exceptions:
			work.assign(case, "ResolveDeliveryException", "Review the delivery: it has exceptions.", subject, 1, work.holders(work.HOP), role=work.HOP)
		if not premature:
			_assign_inspection(case, number, clean)
		events.record(case, "Arrival recorded", actor, f"{row.delivery_reference}: {sum(i['quantity'] for i in clean)} units received at {destination}.", arrival=row.name, items=clean, exceptions=exceptions)
		return records.summary(doc, arrival=row.name, arrival_no=number, exceptions=[e["kind"] for e in exceptions])

	return records.command("RecordContractArrival", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "received_at": received_at, "destination": destination, "items": items, "notes": notes, "reference": supplier_reference}, body=body,
		authorise=lambda: authority.require(actor, "Receiving", organisation_unit=_unit(case)))


def arrivals_all(case: str) -> list[dict[str, Any]]:
	return position.arrivals(case)


def inspectable(items: list[dict[str, Any]]) -> list[str]:
	"""The units an inspector reads: those of a named line that are not surplus."""
	return [u for i in items if i.get("line_id") for u in i.get("units", []) if u not in set(i.get("excess_units") or [])]


def _assign_inspection(case: str, number: int, items: list[dict[str, Any]]) -> None:
	if not any(i.get("line_id") and cint(i["quantity"]) - cint(i.get("excess_quantity")) > 0 for i in items):
		return  # nothing here to inspect: surplus and unexpected goods are held, not inspected
	subject = f"arrival {number}"
	appointed = bindings.effective_appointment(case)
	inspectors = [m["user"] for m in appointed["members"]] if appointed else []
	services = service_lines(_terms_for(case, "Effective") or _terms_for(case, "Awaiting signatures"))
	named = [i for i in items if i.get("line_id")]
	line = next((l for l in _terms_for(case, "Effective", "Awaiting signatures").get("lines", []) if named and l["line_id"] == named[0]["line_id"]), {})
	title = f"Record the {cstr(line.get('item') or named[0]['item']).lower()} evidence." if named and named[0]["line_id"] in services else "Inspect the delivery."
	work.assign(case, "RecordInspectionObservations", title, subject, 1, inspectors or work.holders(work.HOP), role="Contract inspection")
	chair = next((m["user"] for m in appointed["members"] if m["capacity"] == CHAIR), "") if appointed else ""
	work.assign(case, work.waiting_command("RecordInspectionObservations", "inspection"), "Waiting for the inspection.", subject, 1, [chair] if chair else work.holders(work.HOP), role=CHAIR, state="Waiting")


def release_premature(case: str, actor: str = "") -> None:
	"""The agreement is now in force: goods that arrived before it become inspectable, with the exception kept on their record."""
	for arrival in frappe.get_all(ARRIVAL, filters={"contract_case": case}, fields=["name", "arrival_no", "items_json", "exceptions_json"]):
		found = records.loads(arrival.exceptions_json, [])
		if any(e["kind"] == "Premature" for e in found) and not frappe.db.exists("Contract Event", {"contract_case": case, "event_type": "Premature delivery released", "detail_json": ["like", f"%{arrival.name}%"]}):
			_assign_inspection(case, arrival.arrival_no, records.loads(arrival.items_json, []))
			events.record(case, "Premature delivery released", actor, f"Delivery {arrival.arrival_no}, which arrived before the agreement was in force, is now open to inspection.", arrival=arrival.name)


def resolve_exception(case: str, *, arrival: str, disposition: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ResolveDeliveryException` (authored; FU-CM-84): HOP records what became of a delivery's exceptions. The arrival is never edited; the disposition is attributed history."""
	preflight.exists(case)
	choices = ("Separate delivery", "Duplicate delivery note", "To be collected by the supplier", "Awaiting the supplier's instruction")

	def body() -> dict[str, Any]:
		invalid({"disposition": "" if disposition in choices else "Choose what became of it.", "reason": "" if cstr(reason).strip() else "Enter the reason."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ARRIVAL, arrival)
		if row.contract_case != case or not records.loads(row.exceptions_json, []):
			fail("CM_CHANGED", arrival=arrival, reason="This delivery has no exception to resolve.")
		records.bump(doc)
		work.finish(case, command="ResolveDeliveryException", subject=f"arrival {row.arrival_no}", actor=actor)
		events.record(case, "Delivery exception resolved", actor, f"{row.delivery_reference}: {disposition}. {reason.strip()}", arrival=row.name, disposition=disposition)
		return records.summary(doc, arrival=row.name, disposition=disposition)

	return records.command("ResolveDeliveryException", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "arrival": arrival, "disposition": disposition, "reason": reason},
		body=body, authorise=lambda: preflight.acts_as_preparer(actor, _unit(case)))


def record_custody_return(case: str, *, expected_version: int, idempotency_key: str, actor: str, units: list[str], evidence: str) -> dict[str, Any]:
	"""`RecordCustodyReturn`: rejected units collected by the supplier. Closes their custody with the collection evidence; nothing already decided is overwritten."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"evidence": "" if cstr(evidence).strip() else "Enter the supplier's collection evidence."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		have = position.position(case)["units"]
		bad = [u for u in units or [] if u not in have or have[u]["status"] not in ("Rejected", "Excess")]
		if not units or bad:
			fail("CM_QUANTITY", units=bad or list(units or []), reason="Only rejected or surplus units still in custody can be collected by the supplier.")
		records.bump(doc)
		events.record(case, position.RETURN_EVENT, actor, f"{len(units)} rejected unit(s) collected by the supplier.", units=list(units), evidence=evidence)
		return records.summary(doc, returned=list(units))

	return records.command("RecordCustodyReturn", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "units": units, "evidence": evidence},
		body=body, authorise=lambda: authority.require(actor, "Receiving", organisation_unit=_unit(case)))


# -- inspection -----------------------------------------------------------------------------------------------------------------------
def _reading(value: Any) -> float | None:
	try:
		return float(str(value).strip().replace(",", "")) if cstr(value).strip() else None
	except ValueError:
		return None


def service_lines(terms: dict[str, Any]) -> set[str]:
	"""The lines that are services: performed and evidenced, never received into stock or made into assets (board D31)."""
	return {l["line_id"] for l in terms.get("lines", []) if l.get("kind") == "service"}


def criteria_for(terms: dict[str, Any], line_id: str) -> list[dict[str, Any]]:
	"""The frozen criteria that apply to a line. A criterion names its line; one that names none applies to the goods lines, never to a service."""
	services = service_lines(terms)
	return [c for c in terms.get("criteria", []) if (c.get("line_id") == line_id if c.get("line_id") else line_id not in services)]


def findings(criteria: list[dict[str, Any]], units: list[str], observations: list[dict[str, Any]], line_of: dict[str, str] | None = None, services: set[str] | frozenset = frozenset()) -> dict[str, Any]:
	"""Meets / Does not meet / Needs review for every unit against every frozen criterion that applies to its line, with requirement, observation and reason. A blank or unreadable reading is Needs review,
	and so is a unit no criterion applies to: nothing is accepted on an absent requirement."""
	given = {(o.get("unit"), o.get("criterion_id")): o for o in observations or []}
	out: dict[str, Any] = {}
	for unit in units:
		by_criterion = {}
		line = (line_of or {}).get(unit)
		for c in criteria:
			if line_of is not None and not (c.get("line_id") == line if c.get("line_id") else line not in services):
				continue
			obs = given.get((unit, c["id"]))
			requirement = f"{c['name']} {c['comparator']} {c['value']} {c.get('unit', '')}".strip()
			raw = obs.get("value") if obs else None
			if not isinstance(c["value"], (int, float)):  # a typed text comparison ("Starts successfully" = "Yes")
				given_text = cstr(raw).strip()
				if not given_text:
					result, reason = NEEDS_REVIEW, "No reading was recorded."
				elif COMPARATORS[c["comparator"]](given_text.lower(), cstr(c["value"]).lower()):
					result, reason = MEETS, ""
				else:
					result, reason = DOES_NOT_MEET, f"{c['name']} is {given_text}, the requirement is {c['value']}."
				by_criterion[c["id"]] = {"requirement": requirement, "observed": cstr(raw), "result": result, "reason": reason, "evidence": (obs or {}).get("evidence", "")}
				continue
			reading = _reading(raw)
			if reading is None:
				result, reason = NEEDS_REVIEW, "No reading was recorded." if not cstr(raw).strip() else "The reading is not a number."
			else:
				ok = COMPARATORS[c["comparator"]](reading, flt(c["value"]))
				result, reason = (MEETS, "") if ok else (DOES_NOT_MEET, f"{c['name']} is {reading:g}, below the requirement." if c["comparator"] in (">=", ">") else f"{c['name']} is {reading:g}, above the requirement.")
			by_criterion[c["id"]] = {"requirement": requirement, "observed": cstr(raw), "result": result, "reason": reason, "evidence": (obs or {}).get("evidence", "")}
		results = {r["result"] for r in by_criterion.values()}
		if line_of is not None and not by_criterion:
			results = {NEEDS_REVIEW}
		out[unit] = {"result": DOES_NOT_MEET if DOES_NOT_MEET in results else NEEDS_REVIEW if NEEDS_REVIEW in results else MEETS, "criteria": by_criterion}
	counts = {k: sum(1 for v in out.values() if v["result"] == k) for k in (MEETS, DOES_NOT_MEET, NEEDS_REVIEW)}
	return {"units": out, "summary": counts}


def current_inspection(case: str, arrival: str):
	name = frappe.db.get_value(INSPECTION, {"contract_case": case, "arrival": arrival, "state": "Recorded"}, "name", order_by="version_no desc")
	return frappe.get_doc(INSPECTION, name) if name else None


def certified_units(case: str, arrival_no: int) -> set[str]:
	"""The units a signed technical certificate covers: what an inspector may no longer re-read, and what an acceptance report may accept."""
	out: set[str] = set()
	dissented = position.dissents(case)
	for cert in frappe.get_all(CERTIFICATE, filters={"contract_case": case, "kind": "Technical", "subject": f"arrival {arrival_no}", "state": "Signed"}, fields=["content_json", "subject_version"]):
		# a member's recorded dissent re-opens the reading: the confirmation it was made against no longer stands for that unit
		out |= {u for u in records.loads(cert.content_json, {}).get("covered", []) if u not in dissented or dissented[u] < cint(cert.subject_version)}
	return out


def record_inspection(case: str, *, arrival: str, expected_version: int, idempotency_key: str, actor: str, observations: list[dict[str, Any]], coverage: str = "every unit") -> dict[str, Any]:
	"""`RecordInspectionObservations`: the inspector's readings against the frozen criteria, with the automatic findings. A new record supersedes the earlier one and keeps it.

	Readings are per unit: a unit with no reading is Needs review, so one inspected serial never stands for a delivery. A sample is accepted only where the approved requirements authorise one (the criteria's
	coverage); there is no local sampling rule. A unit already covered by a signed technical certificate is not read again (a change goes through the acceptance correction route); the rest can be."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require_capacity(case, actor, "inspector")
		require_ready(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = frappe.get_doc(ARRIVAL, arrival)
		if row.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		items = records.loads(row.items_json, [])
		units = inspectable(items)
		terms = records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc"))
		allowed = {cstr(c.get("coverage") or "every unit") for c in terms["criteria"]} or {"every unit"}
		if coverage not in allowed:
			fail("CM_INCOMPLETE", coverage=coverage, reason="The approved requirements do not authorise inspecting a sample: every unit is read.")
		locked = certified_units(case, row.arrival_no)
		unknown = [o.get("unit") for o in observations or [] if o.get("unit") not in units]
		if unknown:
			invalid({"observations": "Readings can only be recorded for the units of this arrival."})
		again = sorted({o.get("unit") for o in observations or [] if o.get("unit") in locked})
		if again:
			fail("CM_RECONCILE", units=again, reason="These units are already covered by a signed technical confirmation; a change goes through the acceptance correction route.")
		previous = current_inspection(case, row.name)
		kept = [o for o in (records.loads(previous.observations_json, []) if previous else []) if o.get("unit") in locked]
		merged = kept + [o for o in observations or [] if o.get("unit") not in locked]
		line_of = {u: i["line_id"] for i in items if i.get("line_id") for u in i.get("units", [])}
		found = findings(terms["criteria"], units, merged, line_of, service_lines(terms))
		version = records.next_number(INSPECTION, {"contract_case": case, "arrival": row.name}, "version_no")
		for earlier in frappe.get_all(INSPECTION, filters={"contract_case": case, "arrival": row.name, "state": "Recorded"}, pluck="name"):
			records.update(frappe.get_doc(INSPECTION, earlier), state="Superseded")
		unnamed = sum(i.get("unidentified", 0) for i in items)
		inspection = records.new(INSPECTION, contract_case=case, arrival=row.name, version_no=version, inspector=actor, state="Recorded", coverage=coverage if not unnamed else f"{coverage}; {unnamed} unit(s) not identified",
			observations_json=records.dumps(merged), findings_json=records.dumps(found), recorded_at=clock.now(), record_version=1)
		records.bump(doc)
		subject = f"arrival {row.arrival_no}"
		work.finish(case, command="RecordInspectionObservations", subject=subject, actor=actor)
		members = bindings.effective_appointment(case)["members"]
		unresolved = sorted(u for u, f in found["units"].items() if f["result"] == NEEDS_REVIEW and u not in locked)
		ready = [u for u, f in found["units"].items() if f["result"] != NEEDS_REVIEW and u not in locked]
		if ready:  # completed independent units may proceed while others wait for their readings
			work.assign(case, "SignTechnicalCertificate", "Sign the technical certificate.", f"inspection {row.arrival_no}", version, [m["user"] for m in members if m.get("certifier")], role="Technical certification")
			chair = next((m["user"] for m in members if m["capacity"] == CHAIR), "")
			work.assign(case, work.waiting_command("SignTechnicalCertificate", "technical"), "Waiting for the technical confirmation.", f"inspection {row.arrival_no}", version, [chair], role=CHAIR, state="Waiting")
		if unresolved:
			work.assign(case, "RecordInspectionObservations", "The inspection evidence needs review.", subject, version + 1, [m["user"] for m in members], role="Contract inspection")
		events.record(case, "Inspection recorded", actor, f"Inspection {version} of {row.delivery_reference}: {found['summary']}.", inspection=inspection.name, counts=found["summary"])
		return records.summary(doc, inspection=inspection.name, inspection_version=version, findings=found["summary"])

	return records.command("RecordInspectionObservations", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "arrival": arrival, "observations": observations, "coverage": coverage}, body=body, authorise=authorise)


# -- technical certificate ------------------------------------------------------------------------------------------------------------
def _certificate_for(case: str, arrival_no: int, version: int | None = None):
	"""The latest technical certificate of an arrival (or of one inspection version)."""
	filters: dict[str, Any] = {"contract_case": case, "kind": "Technical", "subject": f"arrival {arrival_no}", "state": ["!=", "Superseded"]}
	if version is not None:
		filters["subject_version"] = version
	name = frappe.db.get_value(CERTIFICATE, filters, "name", order_by="creation desc")
	return frappe.get_doc(CERTIFICATE, name) if name else None


def signed_certificates(case: str, arrival_no: int) -> list[Any]:
	return [frappe.get_doc(CERTIFICATE, n) for n in frappe.get_all(CERTIFICATE, filters={"contract_case": case, "kind": "Technical", "subject": f"arrival {arrival_no}", "state": "Signed"}, pluck="name", order_by="creation asc")]


def sign_technical_certificate(case: str, *, arrival: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignTechnicalCertificate`: the technical certifier's personal proof of the exact findings. No resolved finding is repeated; an unresolved one stops it (CM_INCOMPLETE)."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require_capacity(case, actor, "technical certifier")
		require_ready(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ARRIVAL, arrival)
		inspection = current_inspection(case, row.name)
		if row.contract_case != case or inspection is None:
			fail("CM_INCOMPLETE", arrival=arrival, reason="No inspection has been recorded for this arrival.")
		found = records.loads(inspection.findings_json)
		already_certified = certified_units(case, row.arrival_no)
		unresolved = sorted(u for u, f in found["units"].items() if f["result"] == NEEDS_REVIEW and u not in already_certified)
		covered = sorted(u for u, f in found["units"].items() if f["result"] != NEEDS_REVIEW and u not in already_certified)
		existing = _certificate_for(case, row.arrival_no, inspection.version_no)
		if existing and existing.state == "Signed":
			return records.summary(doc, certificate=existing.name, already=True)
		if not covered:  # only the units with a reading are confirmed; none to confirm means the readings are still to come
			fail("CM_INCOMPLETE", units=unresolved, reason="Some required readings are missing or unreadable." if unresolved else "Every reading is already confirmed.")
		digest = records.digest({"inspection": inspection.name, "version": inspection.version_no, "findings": found, "covered": covered})
		if existing:
			cert = existing
		else:
			cert = records.new(CERTIFICATE, contract_case=case, kind="Technical", subject=f"arrival {row.arrival_no}", subject_version=inspection.version_no, state="Awaiting signature",
				content_json=records.dumps({"inspection": inspection.name, "digest": digest, "summary": found["summary"], "covered": covered, "not_covered": unresolved}), record_version=1)
		intent = signing_flow.record(case, f"certificate technical arrival {row.arrival_no}", inspection.version_no, "sign")
		return records.summary(doc, certificate=cert.name, intent=intent.name, digest=digest, arrival_no=row.arrival_no, inspection_version=inspection.version_no)

	recorded = records.command("SignTechnicalCertificate", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "arrival": arrival}, body=body, authorise=authorise)
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["certificate"], target_digest=recorded["digest"], version=recorded["inspection_version"],
		action="Sign the technical certificate")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", f"certificate technical arrival {recorded['arrival_no']}", recorded["inspection_version"])
		frappe.db.commit()
		signing_flow.unfinished(result, certificate=recorded["certificate"])
	with records.atomic():
		doc = records.lock(case)
		cert = frappe.get_doc(CERTIFICATE, recorded["certificate"])
		if cert.state != "Signed":
			records.update(cert, state="Signed", signer=actor, proof_reference=result["reference"], signed_at=clock.now(), record_version=cint(cert.record_version) + 1)
			records.bump(doc)
			arrival_no = recorded["arrival_no"]
			work.finish(case, command="SignTechnicalCertificate", subject=f"inspection {arrival_no}", actor=actor)
			work.finish(case, command="RestoreContractOperation", subject=f"certificate technical arrival {arrival_no}", actor=actor)
			chair = next((m["user"] for m in bindings.effective_appointment(case)["members"] if m["capacity"] == CHAIR), "")
			work.assign(case, "PrepareAcceptanceReport", "Prepare the acceptance report.", f"arrival {arrival_no}", 1, [chair], role=CHAIR)
			events.record(case, "Technical certificate signed", actor, f"Technical confirmation of arrival {arrival_no} signed.", certificate=cert.name, proof=result["reference"])
		out = records.summary(doc, certificate=cert.name, state="Signed")
	frappe.db.commit()
	return out


# -- acceptance -----------------------------------------------------------------------------------------------------------------------
def _chair(case: str, user: str) -> bool:
	found = bindings.member(case, user)
	return bool(found and found["member"]["capacity"] == CHAIR)


def current_acceptance(case: str, *states: str):
	filters: dict[str, Any] = {"contract_case": case}
	if states:
		filters["state"] = ["in", list(states)]
	name = frappe.db.get_value(ACCEPTANCE, filters, "name", order_by="version_no desc")
	return frappe.get_doc(ACCEPTANCE, name) if name else None


def prepare_acceptance_report(case: str, *, arrivals: list[str], expected_version: int, idempotency_key: str, actor: str, overrides: dict[str, dict[str, str]] | None = None) -> dict[str, Any]:
	"""`PrepareAcceptanceReport`: the chair's one report. Each unit of the covered arrivals is accepted, rejected or deferred; accepted + rejected + deferred = what the report covers.
	A unit that did not meet cannot be accepted, and a unit under review cannot be accepted or rejected. `overrides` maps a unit to `{disposition, reason}` to reject or defer a unit that met."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require_capacity(case, actor, "inspector")
		require_ready(case)
		if not _chair(case, actor):
			fail("CM_AUTHORITY", missing="appointment", capacity="chair", reason="The chair prepares the acceptance report.")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		decided = position.decided_units(case)
		dissented = position.dissents(case)
		lines: dict[tuple[str, str], dict[str, Any]] = {}
		arrival_rows = []
		for name in arrivals or []:
			row = frappe.get_doc(ARRIVAL, name)
			if row.contract_case != case:
				raise frappe.DoesNotExistError("Not found")
			if not signed_certificates(case, row.arrival_no):
				fail("CM_INCOMPLETE", arrival=row.delivery_reference, reason="The technical confirmation is not signed.")
			arrival_rows.append(row)
			certified = certified_units(case, row.arrival_no)
			found = records.loads(current_inspection(case, row.name).findings_json)
			for item in records.loads(row.items_json, []):
				if not item.get("line_id"):
					continue  # goods the contract does not name are never part of an acceptance
				line = lines.setdefault((row.name, item["line_id"]), {"arrival": row.name, "arrival_no": row.arrival_no, "line_id": item["line_id"], "item": item["item"], "arrived": cint(item["quantity"]) - cint(item.get("excess_quantity")),
					"accepted": 0, "rejected": 0, "deferred": 0, "units": {"accepted": [], "rejected": [], "deferred": []}, "reasons": {}, "unidentified": cint(item.get("unidentified"))})
				for unit in item.get("units", []):
					if unit in decided or unit not in found["units"]:
						continue  # decided already, or surplus (held apart, never inspected)
					result = found["units"][unit]["result"]
					wanted = (overrides or {}).get(unit)
					disposition = "accepted" if result == MEETS and unit in certified else "rejected" if result == DOES_NOT_MEET and unit in certified else "deferred"
					if disposition == "deferred" and result != NEEDS_REVIEW:
						line["reasons"][unit] = "A member's dissent is recorded: the reading is repeated." if unit in dissented else "Not yet confirmed technically."
					if wanted and wanted.get("disposition") in ("rejected", "deferred") and result == MEETS:
						if not cstr(wanted.get("reason")).strip():
							invalid({"overrides": "Give a reason for every unit you reject or defer."})
						disposition = wanted["disposition"]
						line["reasons"][unit] = wanted["reason"]
					elif wanted and wanted.get("disposition") not in (None, disposition):
						fail("CM_INCOMPLETE", units=[unit], reason="A unit that did not meet cannot be accepted, and a unit that met can only be rejected or deferred with a reason.")
					if result == DOES_NOT_MEET:
						line["reasons"][unit] = "; ".join(c["reason"] for c in found["units"][unit]["criteria"].values() if c["reason"])
					line["units"][disposition].append(unit)
		if not lines:
			invalid({"arrivals": "Choose the deliveries this report covers."})
		if not any(line["units"]["accepted"] or line["units"]["rejected"] for line in lines.values()):  # a report that decides nothing asks four people to sign for nothing
			fail("CM_INCOMPLETE", units=sorted(u for line in lines.values() for u in line["units"]["deferred"]), reason="No unit here is ready to be accepted or rejected yet: the readings or confirmations still to come are listed.")
		for line in lines.values():
			line["accepted"], line["rejected"], line["deferred"] = len(line["units"]["accepted"]), len(line["units"]["rejected"]), len(line["units"]["deferred"]) + line["unidentified"]
			prior = sum(1 for u in position.position(case)["units"].values() if u["arrival"] == line["arrival"] and u["line_id"] == line["line_id"] and u["unit"] in decided)
			if line["accepted"] + line["rejected"] + line["deferred"] != line["arrived"] - prior:
				fail("CM_QUANTITY", arrival=line["arrival_no"], line=line["line_id"], accepted=line["accepted"], rejected=line["rejected"], deferred=line["deferred"], covered=line["arrived"] - prior)
		appointed = bindings.effective_appointment(case)
		signers = [{"user": m["user"], "name": m["name"], "capacity": m["capacity"], "state": "Awaiting", "proof": "", "signed_at": ""} for m in appointed["members"]]
		version = records.next_number(ACCEPTANCE, {"contract_case": case}, "version_no")
		for earlier in frappe.get_all(ACCEPTANCE, filters={"contract_case": case, "state": ["in", ["Draft", "Awaiting signatures"]]}, pluck="name"):
			old = frappe.get_doc(ACCEPTANCE, earlier)
			records.update(old, state="Superseded")
			work.finish(case, subject=f"acceptance {old.version_no}", state="Superseded", actor=actor)
		report = records.new(ACCEPTANCE, contract_case=case, version_no=version, state="Awaiting signatures", arrivals_json=records.dumps([r.name for r in arrival_rows]), lines_json=records.dumps(list(lines.values())),
			signers_json=records.dumps(signers), technical_certificate=",".join(c.name for r in arrival_rows for c in signed_certificates(case, r.arrival_no)), chair=actor, record_version=1)
		records.bump(doc, delivery_state="Acceptance report awaiting signatures")
		for arrival_row in arrival_rows:
			work.finish(case, command="PrepareAcceptanceReport", subject=f"arrival {arrival_row.arrival_no}", actor=actor)
		work.assign(case, "SignAcceptanceReport", "Sign the acceptance report.", f"acceptance {version}", version, [s["user"] for s in signers], role="Contract inspection")
		events.record(case, "Acceptance report prepared", actor, f"Acceptance report {version} prepared.", report=report.name, accepted=sum(l["accepted"] for l in lines.values()), rejected=sum(l["rejected"] for l in lines.values()))
		return records.summary(doc, acceptance=report.name, acceptance_version=version)

	return records.command("PrepareAcceptanceReport", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "arrivals": arrivals, "overrides": overrides or {}},
		body=body, authorise=authorise)


def _report_digest(report) -> str:
	return records.digest({"report": report.name, "version": report.version_no, "arrivals": records.loads(report.arrivals_json), "lines": records.loads(report.lines_json),
		"signers": [s["user"] for s in records.loads(report.signers_json)], "technical": report.technical_certificate})


def open_units(report) -> list[str]:
	"""The units a report accepts or rejects: the ones a member can dissent from (a deferred unit is already open)."""
	return [u for line in records.loads(report.lines_json, []) for kind in ("accepted", "rejected") for u in line["units"][kind]]


def _check_dissent(report, units: list[str] | None, reason: str) -> dict[str, Any] | None:
	named = [cstr(u).strip() for u in units or [] if cstr(u).strip()]
	if not named and not cstr(reason).strip():
		return None
	problems: dict[str, str] = {}
	if not cstr(reason).strip():
		problems["dissent_reason"] = "Give the reason for your dissent."
	if not named:
		problems["dissent_units"] = "Name the units you dissent from."
	elif any(u not in open_units(report) for u in named):
		problems["dissent_units"] = "Name only units this report accepts or rejects."
	invalid(problems)
	return {"units": sorted(set(named)), "reason": cstr(reason).strip()}


def decision_of(case: str, report) -> dict[str, Any]:
	"""The decision the signatures make from the chair's report. A recorded dissent cannot be outvoted: its units become needs-review (deferred) and the reading is repeated; every other unit stands."""
	lines = records.loads(report.lines_json, [])
	dissent = []
	for signer in records.loads(report.signers_json, []):
		said = signer.get("dissent")
		if said:
			dissent.append({"user": signer["user"], "name": signer["name"], "units": said["units"], "reason": said["reason"]})
	moved = {u for d in dissent for u in d["units"]}
	versions: dict[str, int] = {}
	for line in lines:
		current = current_inspection(case, line["arrival"])
		for kind in ("accepted", "rejected"):
			gone = [u for u in line["units"][kind] if u in moved]
			line["units"][kind] = [u for u in line["units"][kind] if u not in moved]
			for unit in gone:
				line["units"]["deferred"].append(unit)
				line["reasons"][unit] = "; ".join(f"Dissent recorded by {d['name']}: {d['reason']}" for d in dissent if unit in d["units"])
				versions[unit] = cint(current.version_no) if current else 0
		line["accepted"], line["rejected"] = len(line["units"]["accepted"]), len(line["units"]["rejected"])
		line["deferred"] = len(line["units"]["deferred"]) + cint(line.get("unidentified"))
	return {"lines": lines, "dissent": [{**d, "inspections": {u: versions[u] for u in d["units"] if u in versions}} for d in dissent]}


def sign_acceptance_report(case: str, *, acceptance: str, expected_version: int, idempotency_key: str, actor: str, dissent_units: list[str] | None = None, dissent_reason: str = "") -> dict[str, Any]:
	"""`SignAcceptanceReport`: a required current member signs the exact frozen report, with a recorded dissent from named units if they have one. Where the committee decides, the last proof makes one
	effective decision and one posting intent, atomically; where the Accounting Officer decides, it makes the committee's recommendation."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require_capacity(case, actor, "inspector")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		report = frappe.get_doc(ACCEPTANCE, acceptance)
		if report.contract_case != case or report.state != "Awaiting signatures":
			fail("CM_CHANGED", acceptance=acceptance, state=report.state)
		signers = records.loads(report.signers_json, [])
		mine = next((s for s in signers if s["user"].lower() == actor.lower()), None)
		if mine is None:
			fail("CM_AUTHORITY", missing="appointment", capacity="report signer", reason="You are not a required signer of this report.")
		if mine["state"] == "Signed":
			return records.summary(doc, acceptance=report.name, already=True)
		dissent = _check_dissent(report, dissent_units, dissent_reason)
		recorders = [frappe.db.get_value(ARRIVAL, a, "receiver") for a in records.loads(report.arrivals_json)]
		segregation.receiver_not_acceptance_signer(actor, recorders)
		guards = preflight.rules(doc, "SignAcceptanceReport")
		guards.raise_if_any()
		intent = signing_flow.record(case, f"acceptance {report.version_no} signature", report.version_no, f"sign-{records.short(actor)}")
		return records.summary(doc, acceptance=report.name, intent=intent.name, digest=_report_digest(report), version=report.version_no, dissent=dissent)

	recorded = records.command("SignAcceptanceReport", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "acceptance": acceptance, "dissent_units": sorted(dissent_units or []), "dissent_reason": dissent_reason}, body=body, authorise=authorise)
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["acceptance"], target_digest=recorded["digest"], version=recorded["version"], action="Sign the acceptance report")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", f"acceptance {recorded['version']} signature {records.short(actor)}", recorded["version"])
		frappe.db.commit()
		signing_flow.unfinished(result, acceptance=recorded["acceptance"])
	out = _apply_report_signature(case, recorded["acceptance"], actor, result["reference"], recorded.get("dissent"))
	frappe.db.commit()
	return _after_decision(case, out, recorded["acceptance"], actor)


def _after_decision(case: str, out: dict[str, Any], acceptance: str, actor: str) -> dict[str, Any]:
	if out.get("posting"):
		post_accepted_receipt(case, acceptance=acceptance, actor=actor)
		return records.summary(frappe.get_doc(CASE, case), **{k: v for k, v in out.items() if k not in ("ok", "contract", "lifecycle", "record_version")})
	return out


def _apply_report_signature(case: str, acceptance: str, actor: str, proof: str, dissent: dict[str, Any] | None = None) -> dict[str, Any]:
	with records.atomic():
		doc = records.lock(case)
		report = frappe.get_doc(ACCEPTANCE, acceptance)
		signers = records.loads(report.signers_json, [])
		mine = next(s for s in signers if s["user"].lower() == actor.lower())
		if mine["state"] == "Signed":
			return records.summary(doc, acceptance=acceptance, effective=report.state == "Effective")
		mine.update(state="Signed", proof=proof, signed_at=str(clock.now()), dissent=dissent)
		records.update(report, signers_json=records.dumps(signers), record_version=cint(report.record_version) + 1)
		for name in frappe.get_all("Contract Task", filters={"contract_case": case, "command": "SignAcceptanceReport", "subject": f"acceptance {report.version_no}", "holder": actor, "state": ["in", list(work.LIVE)]}, pluck="name"):
			task = frappe.get_doc("Contract Task", name)
			records.append_json(task, "history_json", {"state": "Done", "at": str(clock.now()), "by": actor})
			records.update(task, state="Done", completed_at=clock.now())
		if dissent:
			events.record(case, "Acceptance report signed with dissent", actor, f"{mine['name']} signed acceptance report {report.version_no} and recorded a dissent from {len(dissent['units'])} unit(s).", report=report.name, proof=proof,
				units=dissent["units"], reason=dissent["reason"])
		else:
			events.record(case, "Acceptance report signed", actor, f"{mine['name']} signed acceptance report {report.version_no}.", report=report.name, proof=proof)
		if not all(s["state"] == "Signed" for s in signers):
			records.bump(doc)
			return records.summary(doc, acceptance=acceptance, effective=False)
		return _conclude(case, doc, report, actor)


def acceptance_authority(case: str) -> str:
	"""Who makes the acceptance a decision: the committee that signed it, or the Accounting Officer on its recommendation (the appointment says which)."""
	found = bindings.effective_appointment(case)
	return (found or {}).get("acceptance") or ACCEPTANCE_AUTHORITY[0]


def _conclude(case: str, doc, report, actor: str) -> dict[str, Any]:
	if acceptance_authority(case) == ACCEPTANCE_AUTHORITY[1]:
		records.update(report, state="Recommended")
		subject = f"acceptance {report.version_no}"
		work.assign(case, "DecideContractAcceptance", "Decide on the acceptance report.", subject, report.version_no, work.holders("Accounting Officer"), role="Accounting Officer")
		chair = next((m["user"] for m in (bindings.effective_appointment(case) or {"members": []})["members"] if m["capacity"] == CHAIR), "")
		work.assign(case, work.waiting_command("DecideContractAcceptance", "acceptance"), "Waiting for the Accounting Officer's decision.", subject, report.version_no, [chair], role=CHAIR, state="Waiting")
		records.bump(doc, delivery_state="Acceptance report awaiting the Accounting Officer")
		events.record(case, "Acceptance recommended", actor, f"Acceptance report {report.version_no} signed by every member and recommended to the Accounting Officer.", report=report.name)
		return records.summary(doc, acceptance=report.name, effective=False, recommended=True)
	return _make_effective(case, doc, report, actor)


def _make_effective(case: str, doc, report, actor: str, *, proof: str = "", decided_by: str = "") -> dict[str, Any]:
	"""One effective decision and, where any unit is accepted, one posting intent."""
	decision = decision_of(case, report)
	decision.update(decided_by=decided_by, proof=proof)
	services = service_lines(_terms_for(case, "Effective"))
	accepted = sum(line["accepted"] for line in decision["lines"] if line["line_id"] not in services)  # only goods are received; an accepted service is entitled, not posted
	records.update(report, state="Effective", decision_at=clock.now(), decision_json=records.dumps(decision))
	if accepted:
		intent = intents.record(case, f"acceptance {report.version_no}", report.version_no, "Accepted receipt", "post", recovery_owner="Technical operator")
		records.update(report, posting_intent=intent.name)
		records.bump(doc, delivery_state="Accepted goods awaiting stock update")
		events.record(case, "Acceptance effective", actor, f"Acceptance report {report.version_no} is effective.", report=report.name, intent=intent.name)
	else:
		records.bump(doc, delivery_state="Acceptance decided; no goods to receive")
		events.record(case, "Acceptance effective", actor, f"Acceptance report {report.version_no} is effective; no goods are to be received.", report=report.name)
	if decision["dissent"]:
		_reopen_readings(case, decision, actor)
	_follow_up_findings(case, report, decision, actor)
	return records.summary(doc, acceptance=report.name, effective=True, posting=bool(accepted))


def _follow_up_findings(case: str, report, decision: dict[str, Any], actor: str) -> None:
	"""What an effective decision asks of the parties: the units that did not meet become a delivery issue the owner sends to the supplier, and replacement units that were accepted close the issue that asked
	for them (the thread is closed with the fact, never with a note)."""
	from kentender_contracts.services import adjustment, issues, warranty

	lines = decision["lines"]
	rejected = [(line, unit) for line in lines for unit in line["units"]["rejected"]]
	if rejected:
		units = [u for _l, u in rejected]
		observed = "; ".join(sorted({line["reasons"].get(u, "") for line, u in rejected if line["reasons"].get(u)}))
		item = cstr(rejected[0][0]["item"]).lower()
		issues.open_issue(case, kind="Delivery issue", title=f"{len(units)} {item}{'' if len(units) == 1 else 's'} need replacement",
			facts={"units": units, "result": "Does not meet", "observed": observed or "The requirements were not met.", "acceptance": report.name, "inspection": f"arrival {rejected[0][0]['arrival_no']}"},
			requested_remedy="Replacement", reply_by=str(add_days(clock.now(), 2))[:10], units=units, links={"acceptance": report.name},
			draft=f"{len(units)} {item}{'' if len(units) == 1 else 's'} did not meet the requirements ({observed or 'see the inspection'}). Please arrange replacement and confirm the delivery date.", actor=actor)
	replaced: dict[str, str] = {}
	accepted = {u for line in lines for u in line["units"]["accepted"]}
	for arrival in arrivals_all(case):
		for item in arrival["items"]:
			replaced.update({unit: old for unit, old in (item.get("replaces") or {}).items() if unit in accepted})
	if replaced:
		issues.close_when_replaced(case, replaced, report.version_no, actor)
		warranty.on_replacement_accepted(case, replaced, actor)
	adjustment.on_delivery_complete(case, actor)  # the delay, if the last unit came after the operative due date
	services = service_lines(_terms_for(case, "Effective"))
	warranty.on_accepted(case, [u for line in lines if line["line_id"] not in services for u in line["units"]["accepted"]], report.version_no, actor)  # the warranty runs from each goods unit's acceptance


def _reopen_readings(case: str, decision: dict[str, Any], actor: str) -> None:
	"""A recorded dissent is unresolved until the reading is repeated: the inspectors are asked to read the dissented units again."""
	appointed = bindings.effective_appointment(case)
	inspectors = [m["user"] for m in appointed["members"]] if appointed else []
	for line in decision["lines"]:
		moved = [u for d in decision["dissent"] for u in d["units"] if u in line["units"]["deferred"]]
		if not moved:
			continue
		current = current_inspection(case, line["arrival"])
		work.assign(case, "RecordInspectionObservations", "A member's dissent needs a repeated reading.", f"arrival {line['arrival_no']}", (cint(current.version_no) if current else 0) + 1, inspectors or work.holders(work.HOP), role="Contract inspection")
		events.record(case, "Dissent reopens reading", actor, f"{len(moved)} unit(s) of {line['item']} are read again.", arrival=line["arrival"], units=moved)


def request_acceptance_correction(case: str, *, acceptance: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RequestAcceptanceCorrection`: a required member (or the Accounting Officer, on a recommendation) sends a report back to the chair before it is effective. The report stays as history with every
	signature it has; the chair prepares a new one, which everyone signs again. Once effective, a change goes through the reversal route, never an edit."""
	preflight.exists(case)

	def authorise() -> None:
		state = frappe.db.get_value(ACCEPTANCE, acceptance, "state")
		if state == "Recommended":
			authority.require(actor, "Accounting Officer")
		else:
			authority.require_capacity(case, actor, "inspector")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		report = frappe.get_doc(ACCEPTANCE, acceptance)
		if report.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		invalid({"reason": "" if cstr(reason).strip() else "Give the reason for the correction."})
		if report.state == "Effective":
			fail("CM_CHANGED", acceptance=acceptance, state=report.state, reason="This acceptance is already effective. A change to an effective acceptance goes through a reversal, not an edit.")
		if report.state not in ("Awaiting signatures", "Recommended"):
			fail("CM_CHANGED", acceptance=acceptance, state=report.state)
		signers = records.loads(report.signers_json, [])
		if report.state == "Awaiting signatures" and not any(s["user"].lower() == actor.lower() for s in signers):
			fail("CM_AUTHORITY", missing="appointment", capacity="report signer", reason="You are not a required signer of this report.")
		records.update(report, state="Superseded", correction_reason=cstr(reason).strip(), record_version=cint(report.record_version) + 1)
		subject = f"acceptance {report.version_no}"
		work.finish(case, subject=subject, state="Superseded", actor=actor)
		chair = next((m["user"] for m in (bindings.effective_appointment(case) or {"members": []})["members"] if m["capacity"] == CHAIR), report.chair)
		for name in records.loads(report.arrivals_json, []):
			number = frappe.db.get_value(ARRIVAL, name, "arrival_no")
			work.assign(case, "PrepareAcceptanceReport", "Correct the acceptance report.", f"arrival {number}", report.version_no + 1, [chair], role=CHAIR)
		records.bump(doc, delivery_state="Acceptance report awaiting correction")
		events.record(case, "Acceptance correction requested", actor, f"Correction of acceptance report {report.version_no} requested: {cstr(reason).strip()}", report=report.name, reason=cstr(reason).strip())
		return records.summary(doc, acceptance=report.name, state="Superseded")

	return records.command("RequestAcceptanceCorrection", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "acceptance": acceptance, "reason": reason}, body=body, authorise=authorise)


def decide_acceptance(case: str, *, acceptance: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`DecideContractAcceptance` (authored; FU-CM-84): where the appointment leaves acceptance to the Accounting Officer, the committee's signed report is a recommendation and the Accounting Officer's
	personal signature on that exact report makes it effective. Where a member already holds the authority, no such extra decision exists (section 5.6)."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Accounting Officer")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		report = frappe.get_doc(ACCEPTANCE, acceptance)
		if report.contract_case != case or report.state != "Recommended":
			fail("CM_CHANGED", acceptance=acceptance, state=report.state)
		recorders = [frappe.db.get_value(ARRIVAL, a, "receiver") for a in records.loads(report.arrivals_json)]
		segregation.receiver_not_acceptance_signer(actor, recorders)
		guards = preflight.rules(doc, "SignAcceptanceReport")
		guards.raise_if_any()
		intent = signing_flow.record(case, f"acceptance {report.version_no} decision", report.version_no, f"decide-{records.short(actor)}")
		return records.summary(doc, acceptance=report.name, intent=intent.name, digest=_report_digest(report), version=report.version_no)

	recorded = records.command("DecideContractAcceptance", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "acceptance": acceptance}, body=body, authorise=authorise)
	frappe.db.commit()
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["acceptance"], target_digest=recorded["digest"], version=recorded["version"], action="Decide the acceptance")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", f"acceptance {recorded['version']} decision", recorded["version"])
		frappe.db.commit()
		signing_flow.unfinished(result, acceptance=recorded["acceptance"])
	with records.atomic():
		doc = records.lock(case)
		report = frappe.get_doc(ACCEPTANCE, recorded["acceptance"])
		if report.state == "Recommended":
			work.finish(case, command="DecideContractAcceptance", subject=f"acceptance {report.version_no}", actor=actor)
			work.finish(case, command="RestoreContractOperation", subject=f"acceptance {report.version_no} decision", actor=actor)
			out = _make_effective(case, doc, report, actor, proof=result["reference"], decided_by=actor)
		else:
			out = records.summary(doc, acceptance=report.name, effective=report.state == "Effective")
	frappe.db.commit()
	return _after_decision(case, out, recorded["acceptance"], actor)


# -- the accepted-subset receipt ------------------------------------------------------------------------------------------------------
def post_accepted_receipt(case: str, *, acceptance: str, actor: str = "") -> dict[str, Any]:
	"""`PostAcceptedReceipt` (service-only): post the accepted units of an effective report to ERPNext once, through the posting intent. A retry reads the owner first; a failure leaves the signed
	acceptance intact and opens technical recovery."""
	report = frappe.get_doc(ACCEPTANCE, acceptance)
	if report.contract_case != case or report.state != "Effective" or not report.posting_intent:
		fail("CM_CHANGED", acceptance=acceptance, state=report.state)
	doc = frappe.get_doc(CASE, case)
	guards = preflight.rules(doc, "PostAcceptedReceipt")
	preflight.holds(guards, case, "post_receipt", except_keys=[f"operation:{report.posting_intent}"])
	guards.raise_if_any()
	order = formation.native_order(case)
	if not order:
		fail("CM_RECONCILE", reason="The contract's purchase order is missing; no stock or asset update can use it.")
	terms = records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc"))
	mapping = terms["particulars"]["item_mapping"]
	accepted: dict[str, list[str]] = {}
	services = service_lines(terms)
	for line in position.effective_lines(report):
		if line["line_id"] not in services:  # a service creates no stock and no asset
			accepted.setdefault(line["line_id"], []).extend(line["units"]["accepted"])
	lines = []
	for line_id, units in accepted.items():
		if not units:
			continue
		code = mapping[line_id]
		item = frappe.db.get_value("Item", code, ["has_serial_no", "is_fixed_asset", "auto_create_assets"], as_dict=True)
		entry: dict[str, Any] = {"item_code": code, "qty": len(units)}
		if item.has_serial_no:
			entry["serials"] = list(units)
		if item.is_fixed_asset and item.auto_create_assets:
			entry["unit_references"] = list(units)
			entry["asset_location"] = terms["particulars"].get("asset_location")
		lines.append(entry)

	def executor(identity: str):
		try:
			with service_principal.acting():
				return adapter.receive(order, identity, lines=lines), "Purchase Receipt"
		except frappe.ValidationError as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(report.posting_intent, executor, lambda identity: adapter.find_by_identity("Purchase Receipt", identity), native_doctype="Purchase Receipt")
	with records.atomic():
		if result["state"] in intents.SETTLED:
			work.finish(case, command="RestoreContractOperation", subject=f"acceptance {report.version_no}", actor=actor)
			records.bump(frappe.get_doc(CASE, case, for_update=True), delivery_state="Accepted goods received")
			events.record(case, "Receipt posted", actor, f"Accepted goods received into stock: {result['reference']}.", receipt=result["reference"], acceptance=report.name)
			differences = reconcile_receipt(case, result["reference"], report)
			if differences:
				work.incident(case, "RestoreContractOperation", "Reconcile the stock or asset update", f"acceptance {report.version_no} reconciliation", report.version_no)
				events.record(case, "Receipt differs", actor, "The receipt does not agree with the acceptance: " + " ".join(differences), receipt=result["reference"], differences=differences)
			else:
				events.record(case, "Receipt reconciled", actor, "The stock, the assets and the ledger agree with the acceptance.", receipt=result["reference"])
			result = {**result, "reconciled": not differences, "differences": differences}
		else:
			work.incident(case, "RestoreContractOperation", "Restore stock or asset update", f"acceptance {report.version_no}", report.version_no)
			events.record(case, "Receipt pending", actor, f"The stock or asset update did not complete ({result['state'].lower()}).", intent=report.posting_intent)
	frappe.db.commit()
	return {"ok": True, **result}


def reconcile_receipt(case: str, receipt: str, report) -> list[str]:
	"""Compare the receipt ERPNext holds with what the acceptance decided: for each catalogue item the quantity and value, the stock a stock item put on the ledger, the assets a fixed-asset item made, and that
	the receipt's ledger balances. Returns the differences in plain words; empty means the stock, the assets and Finance agree with the acceptance. Read only: a difference is reported and recovered by the
	technical operator, never adjusted here."""
	terms = _terms_for(case, "Effective")
	mapping, rates = terms["particulars"]["item_mapping"], {l["line_id"]: flt(l["rate"]) for l in terms["lines"]}
	services = service_lines(terms)
	expected: dict[str, dict[str, float]] = {}
	for line in position.effective_lines(report):
		if line["line_id"] in services or not line["units"]["accepted"]:
			continue
		entry = expected.setdefault(mapping[line["line_id"]], {"qty": 0.0, "amount": 0.0})
		entry["qty"] += len(line["units"]["accepted"])
		entry["amount"] += len(line["units"]["accepted"]) * rates[line["line_id"]]
	facts = adapter.receipt_facts(receipt)
	differences = []
	for code in sorted(set(expected) | set(facts["items"])):
		want, got = expected.get(code, {"qty": 0.0, "amount": 0.0}), facts["items"].get(code, {"qty": 0.0, "amount": 0.0})
		if flt(got["qty"]) != flt(want["qty"]):
			differences.append(f"{code}: {got['qty']:g} on the receipt, {want['qty']:g} accepted.")
		elif abs(flt(got["amount"]) - flt(want["amount"])) > 0.5:
			differences.append(f"{code}: the receipt is worth {got['amount']:,.2f}, the accepted units {want['amount']:,.2f}.")
		item = frappe.db.get_value("Item", code, ["is_stock_item", "is_fixed_asset"], as_dict=True) or frappe._dict()
		if item.is_stock_item and flt(facts["stock"].get(code)) != flt(want["qty"]):
			differences.append(f"{code}: {facts['stock'].get(code, 0):g} on the stock ledger, {want['qty']:g} accepted.")
	made = sum(v["qty"] for code, v in expected.items() if frappe.db.get_value("Item", code, "is_fixed_asset"))
	if facts["assets"] != int(made):
		differences.append(f"{facts['assets']} asset(s) made from the receipt, {int(made)} accepted.")
	ledger = facts["ledger"]
	if abs(ledger["debit"] - ledger["credit"]) > 0.01:
		differences.append(f"The receipt's ledger does not balance: {ledger['debit']:,.2f} debit, {ledger['credit']:,.2f} credit.")
	return differences


def restore_receipts(case: str, actor: str = "") -> list[dict[str, Any]]:
	"""Technical recovery of accepted-receipt postings that did not complete: the owner is read first by identity, so a receipt that exists is linked and nothing is posted twice. A posting another hold stops is left for that hold's owner."""
	out = []
	for name in frappe.get_all(ACCEPTANCE, filters={"contract_case": case, "state": "Effective", "posting_intent": ["is", "set"]}, pluck="name", order_by="version_no asc"):
		report = frappe.get_doc(ACCEPTANCE, name)
		if frappe.db.get_value(intents.INTENT, report.posting_intent, "state") in intents.SETTLED:
			continue
		try:
			out.append({"acceptance": name, **post_accepted_receipt(case, acceptance=name, actor=actor)})
		except Exception as exc:  # noqa: BLE001 - a hold or a refusal leaves it pending for its own owner
			out.append({"acceptance": name, "state": "Pending", "detail": str(exc)})
	return out


def posted_receipts(case: str) -> list[str]:
	return frappe.get_all(intents.INTENT, filters={"contract_case": case, "operation_kind": "Accepted receipt", "state": ["in", list(intents.SETTLED)]}, pluck="result_reference")
