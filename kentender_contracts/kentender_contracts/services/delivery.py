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
from frappe.utils import cint, cstr, flt, get_datetime

from kentender_contracts.native import adapter
from kentender_contracts.services import authority, bindings, clock, events, formation, intents, people, position, preflight, records, segregation, signing_flow, work
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


def recommend_inspectors(case: str, *, expected_version: int, idempotency_key: str, actor: str, members: list[dict[str, Any]], scope: str = "All deliveries under this contract", reason: str = "",
		from_date: str = "", until_date: str = "") -> dict[str, Any]:
	"""`RecommendContractInspectors`: HOP names the written appointment for the Accounting Officer."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		named = _members(members)
		version = records.next_number(APPOINTMENT, {"contract_case": case}, "version_no")
		for earlier in frappe.get_all(APPOINTMENT, filters={"contract_case": case, "state": "Recommended"}, pluck="name"):
			records.update(frappe.get_doc(APPOINTMENT, earlier), state="Superseded")
		row = records.new(APPOINTMENT, contract_case=case, version_no=version, state="Recommended", scope=scope, reference=f"{case}/APP/{version}", members_json=records.dumps(named), recommended_by=actor,
			reason=reason, effective_from=get_datetime(from_date) if cstr(from_date).strip() else None, effective_to=get_datetime(until_date) if cstr(until_date).strip() else None, record_version=1)
		work.finish(case, command="RecommendContractInspectors", actor=actor)
		work.assign(case, "AppointContractInspectors", "Appoint the inspectors for this contract.", f"appointment {version}", version, work.holders("Accounting Officer"), role="Accounting Officer")
		work.assign(case, work.waiting_command("AppointContractInspectors", "appointment"), "Waiting for the appointment.", f"appointment {version}", version, work.holders(work.HOP), role=work.HOP, state="Waiting")
		events.record(case, "Inspectors recommended", actor, f"Appointment {version} recommended.", appointment=row.name)
		return records.summary(doc, appointment=row.name, appointment_version=version)

	return records.command("RecommendContractInspectors", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "members": members, "scope": scope, "from": from_date, "until": until_date},
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
		for earlier in frappe.get_all(APPOINTMENT, filters={"contract_case": case, "state": "Appointed"}, pluck="name"):
			records.update(frappe.get_doc(APPOINTMENT, earlier), state="Replaced", effective_to=now)
		start = get_datetime(from_date) if cstr(from_date).strip() else (row.effective_from or now)
		end = get_datetime(until_date) if cstr(until_date).strip() else row.effective_to
		records.update(row, state="Appointed", appointed_by=actor, effective_from=start, effective_to=end, record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="AppointContractInspectors", subject=f"appointment {row.version_no}", actor=actor)
		for member in records.loads(row.members_json, []):
			work.assign(case, "DeclareContractInterest", "Declare any interest before you act on this contract.", f"appointment {row.version_no}", row.version_no, [member["user"]], role="Contract inspection")
		work.assign(case, work.waiting_command("DeclareContractInterest", "members"), "Waiting for the declarations.", f"appointment {row.version_no}", row.version_no, work.holders(work.HOP), role=work.HOP, state="Waiting")
		events.record(case, "Inspectors appointed", actor, f"Appointment {row.version_no} in force.", appointment=row.name)
		return records.summary(doc, appointment=row.name)

	return records.command("AppointContractInspectors", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "appointment": appointment, "from": from_date, "until": until_date},
		body=body, authorise=lambda: authority.require(actor, "Accounting Officer"))


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
		if mine.get("declared_at"):
			return records.summary(doc, appointment=row.name, already=True)
		mine["declared_at"] = str(clock.now())
		mine["conflict"] = {"reason": conflict.strip(), "at": str(clock.now())} if cstr(conflict).strip() else None
		records.update(row, members_json=records.dumps(members), record_version=cint(row.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="DeclareContractInterest", subject=f"appointment {row.version_no}", actor=actor)
		if mine["conflict"]:
			work.assign(case, "RecommendContractInspectors", "Recommend a replacement: a member declared a conflict.", f"replacement for {mine['user']}", row.version_no, work.holders(work.HOP), role=work.HOP)
			events.record(case, "Conflict declared", actor, "A member declared a conflict of interest.", appointment=row.name)
		else:
			events.record(case, "Interest declared", actor, f"{mine['name']} declared no conflict of interest.", appointment=row.name)
		if all(m.get("declared_at") for m in members):
			work.finish(case, command=work.waiting_command("DeclareContractInterest", "members"), actor=actor)
		return records.summary(doc, appointment=row.name, conflict=bool(mine["conflict"]))

	return records.command("DeclareContractInterest", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "conflict": conflict}, body=body, authorise=authorise)


# -- arrival --------------------------------------------------------------------------------------------------------------------------
def record_arrival(case: str, *, expected_version: int, idempotency_key: str, actor: str, received_at: str, destination: str, items: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
	"""`RecordContractArrival`: what physically arrived. Immutable; creates custody and inspection work, never a native receipt."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		terms = records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc"))
		lines = {l["line_id"]: l for l in terms["lines"]}
		problems: dict[str, str] = {}
		seen_before = set(position.position(case)["units"])
		clean = []
		for item in items or []:
			line, quantity, units = lines.get(item.get("line_id")), cint(item.get("quantity")), [cstr(u).strip() for u in item.get("units") or [] if cstr(u).strip()]
			if line is None or quantity <= 0:
				problems["items"] = "Name an ordered line and a quantity above zero."
				continue
			if len(units) > quantity or len(set(units)) != len(units):
				problems["items"] = "Each unit is named once, and no more units than the quantity."
				continue
			if set(units) & seen_before:
				fail("CM_DUPLICATE", units=sorted(set(units) & seen_before), reason="A unit with this identity has already arrived.")
			clean.append({"line_id": line["line_id"], "item": line.get("description") or line.get("item"), "quantity": quantity, "units": units, "unidentified": quantity - len(units)})
		if not clean:
			problems["items"] = "Record what arrived."
		if not cstr(received_at).strip():
			problems["received_at"] = "Enter when the goods arrived."
		if not cstr(destination).strip():
			problems["destination"] = "Enter where the goods were received."
		invalid(problems)
		number = records.next_number(ARRIVAL, {"contract_case": case}, "arrival_no")
		row = records.new(ARRIVAL, contract_case=case, arrival_no=number, delivery_reference=f"DEL-{number:03d}", received_at=get_datetime(received_at), recorded_at=clock.now(), receiver=actor,
			destination=destination, items_json=records.dumps(clean), notes=notes, state="Recorded", record_version=1)
		records.bump(doc, delivery_state="Goods received")
		subject = f"arrival {number}"
		appointed = bindings.effective_appointment(case)
		inspectors = [m["user"] for m in appointed["members"]] if appointed else []
		work.assign(case, "RecordInspectionObservations", "Inspect the delivery.", subject, 1, inspectors or work.holders(work.HOP), role="Contract inspection")
		chair = next((m["user"] for m in appointed["members"] if m["capacity"] == CHAIR), "") if appointed else ""
		work.assign(case, work.waiting_command("RecordInspectionObservations", "inspection"), "Waiting for the inspection.", subject, 1, [chair] if chair else work.holders(work.HOP), role=CHAIR, state="Waiting")
		events.record(case, "Arrival recorded", actor, f"{row.delivery_reference}: {sum(i['quantity'] for i in clean)} units received at {destination}.", arrival=row.name, items=clean)
		return records.summary(doc, arrival=row.name, arrival_no=number)

	return records.command("RecordContractArrival", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "received_at": received_at, "destination": destination, "items": items, "notes": notes}, body=body,
		authorise=lambda: authority.require(actor, "Receiving", organisation_unit=_unit(case)))


def record_custody_return(case: str, *, expected_version: int, idempotency_key: str, actor: str, units: list[str], evidence: str) -> dict[str, Any]:
	"""`RecordCustodyReturn`: rejected units collected by the supplier. Closes their custody with the collection evidence; nothing already decided is overwritten."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		invalid({"evidence": "" if cstr(evidence).strip() else "Enter the supplier's collection evidence."})
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		have = position.position(case)["units"]
		bad = [u for u in units or [] if u not in have or have[u]["status"] != "Rejected"]
		if not units or bad:
			fail("CM_QUANTITY", units=bad or list(units or []), reason="Only rejected units still in custody can be collected by the supplier.")
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


def findings(criteria: list[dict[str, Any]], units: list[str], observations: list[dict[str, Any]]) -> dict[str, Any]:
	"""Meets / Does not meet / Needs review for every unit against every frozen criterion, with requirement, observation and reason. A blank or unreadable reading is Needs review."""
	given = {(o.get("unit"), o.get("criterion_id")): o for o in observations or []}
	out: dict[str, Any] = {}
	for unit in units:
		by_criterion = {}
		for c in criteria:
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
		out[unit] = {"result": DOES_NOT_MEET if DOES_NOT_MEET in results else NEEDS_REVIEW if NEEDS_REVIEW in results else MEETS, "criteria": by_criterion}
	counts = {k: sum(1 for v in out.values() if v["result"] == k) for k in (MEETS, DOES_NOT_MEET, NEEDS_REVIEW)}
	return {"units": out, "summary": counts}


def current_inspection(case: str, arrival: str):
	name = frappe.db.get_value(INSPECTION, {"contract_case": case, "arrival": arrival, "state": "Recorded"}, "name", order_by="version_no desc")
	return frappe.get_doc(INSPECTION, name) if name else None


def record_inspection(case: str, *, arrival: str, expected_version: int, idempotency_key: str, actor: str, observations: list[dict[str, Any]], coverage: str = "every unit") -> dict[str, Any]:
	"""`RecordInspectionObservations`: the inspector's readings against the frozen criteria, with the automatic findings. A new record supersedes the earlier one and keeps it."""
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
		if frappe.db.exists(CERTIFICATE, {"contract_case": case, "kind": "Technical", "subject": f"arrival {row.arrival_no}", "state": "Signed"}):
			fail("CM_RECONCILE", arrival=row.name, reason="The technical confirmation is already signed; a change goes through the acceptance correction route.")
		items = records.loads(row.items_json, [])
		units = [u for i in items for u in i.get("units", [])]
		terms = records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc"))
		unknown = [o.get("unit") for o in observations or [] if o.get("unit") not in units]
		if unknown:
			invalid({"observations": "Readings can only be recorded for the units of this arrival."})
		found = findings(terms["criteria"], units, observations)
		version = records.next_number(INSPECTION, {"contract_case": case, "arrival": row.name}, "version_no")
		for earlier in frappe.get_all(INSPECTION, filters={"contract_case": case, "arrival": row.name, "state": "Recorded"}, pluck="name"):
			records.update(frappe.get_doc(INSPECTION, earlier), state="Superseded")
		unnamed = sum(i.get("unidentified", 0) for i in items)
		inspection = records.new(INSPECTION, contract_case=case, arrival=row.name, version_no=version, inspector=actor, state="Recorded", coverage=coverage if not unnamed else f"{coverage}; {unnamed} unit(s) not identified",
			observations_json=records.dumps(observations or []), findings_json=records.dumps(found), recorded_at=clock.now(), record_version=1)
		records.bump(doc)
		subject = f"arrival {row.arrival_no}"
		work.finish(case, command="RecordInspectionObservations", subject=subject, actor=actor)
		certifiers = [m["user"] for m in bindings.effective_appointment(case)["members"] if m.get("certifier")]
		work.assign(case, "SignTechnicalCertificate", "Sign the technical certificate.", f"inspection {row.arrival_no}", version, certifiers, role="Technical certification")
		chair = next((m["user"] for m in bindings.effective_appointment(case)["members"] if m["capacity"] == CHAIR), "")
		work.assign(case, work.waiting_command("SignTechnicalCertificate", "technical"), "Waiting for the technical confirmation.", f"inspection {row.arrival_no}", version, [chair], role=CHAIR, state="Waiting")
		events.record(case, "Inspection recorded", actor, f"Inspection {version} of {row.delivery_reference}: {found['summary']}.", inspection=inspection.name, counts=found["summary"])
		return records.summary(doc, inspection=inspection.name, inspection_version=version, findings=found["summary"])

	return records.command("RecordInspectionObservations", case=case, idempotency_key=idempotency_key, actor=actor,
		payload={"expected": expected_version, "arrival": arrival, "observations": observations, "coverage": coverage}, body=body, authorise=authorise)


# -- technical certificate ------------------------------------------------------------------------------------------------------------
def _certificate_for(case: str, arrival_no: int):
	name = frappe.db.get_value(CERTIFICATE, {"contract_case": case, "kind": "Technical", "subject": f"arrival {arrival_no}", "state": ["!=", "Superseded"]}, "name", order_by="creation desc")
	return frappe.get_doc(CERTIFICATE, name) if name else None


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
		unresolved = sorted(u for u, f in found["units"].items() if f["result"] == NEEDS_REVIEW)
		if unresolved:
			fail("CM_INCOMPLETE", units=unresolved, reason="Some required readings are missing or unreadable.")
		digest = records.digest({"inspection": inspection.name, "version": inspection.version_no, "findings": found})
		existing = _certificate_for(case, row.arrival_no)
		if existing and existing.state == "Signed":
			return records.summary(doc, certificate=existing.name, already=True)
		if existing:
			cert = existing
		else:
			cert = records.new(CERTIFICATE, contract_case=case, kind="Technical", subject=f"arrival {row.arrival_no}", subject_version=inspection.version_no, state="Awaiting signature",
				content_json=records.dumps({"inspection": inspection.name, "digest": digest, "summary": found["summary"]}), record_version=1)
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
		lines: dict[tuple[str, str], dict[str, Any]] = {}
		arrival_rows = []
		for name in arrivals or []:
			row = frappe.get_doc(ARRIVAL, name)
			if row.contract_case != case:
				raise frappe.DoesNotExistError("Not found")
			cert = _certificate_for(case, row.arrival_no)
			if not cert or cert.state != "Signed":
				fail("CM_INCOMPLETE", arrival=row.delivery_reference, reason="The technical confirmation is not signed.")
			arrival_rows.append(row)
			found = records.loads(current_inspection(case, row.name).findings_json)
			for item in records.loads(row.items_json, []):
				line = lines.setdefault((row.name, item["line_id"]), {"arrival": row.name, "arrival_no": row.arrival_no, "line_id": item["line_id"], "item": item["item"], "arrived": cint(item["quantity"]),
					"accepted": 0, "rejected": 0, "deferred": 0, "units": {"accepted": [], "rejected": [], "deferred": []}, "reasons": {}, "unidentified": cint(item.get("unidentified"))})
				for unit in item.get("units", []):
					if unit in decided:
						continue
					result = found["units"][unit]["result"]
					wanted = (overrides or {}).get(unit)
					disposition = "accepted" if result == MEETS else "rejected" if result == DOES_NOT_MEET else "deferred"
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
			signers_json=records.dumps(signers), technical_certificate=",".join(_certificate_for(case, r.arrival_no).name for r in arrival_rows), chair=actor, record_version=1)
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


def sign_acceptance_report(case: str, *, acceptance: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignAcceptanceReport`: a required current member signs the exact frozen report. The last proof makes one effective decision and one posting intent, atomically."""
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
		recorders = [frappe.db.get_value(ARRIVAL, a, "receiver") for a in records.loads(report.arrivals_json)]
		segregation.receiver_not_acceptance_signer(actor, recorders)
		guards = preflight.rules(doc, "SignAcceptanceReport")
		guards.raise_if_any()
		intent = signing_flow.record(case, f"acceptance {report.version_no} signature", report.version_no, f"sign-{records.short(actor)}")
		return records.summary(doc, acceptance=report.name, intent=intent.name, digest=_report_digest(report), version=report.version_no)

	recorded = records.command("SignAcceptanceReport", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "acceptance": acceptance}, body=body, authorise=authorise)
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["acceptance"], target_digest=recorded["digest"], version=recorded["version"], action="Sign the acceptance report")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", f"acceptance {recorded['version']} signature {records.short(actor)}", recorded["version"])
		frappe.db.commit()
		signing_flow.unfinished(result, acceptance=recorded["acceptance"])
	out = _apply_report_signature(case, recorded["acceptance"], actor, result["reference"])
	frappe.db.commit()
	if out.get("effective"):
		post_accepted_receipt(case, acceptance=recorded["acceptance"], actor=actor)
		out = records.summary(frappe.get_doc(CASE, case), **{k: v for k, v in out.items() if k not in ("ok", "contract", "lifecycle", "record_version")})
	return out


def _apply_report_signature(case: str, acceptance: str, actor: str, proof: str) -> dict[str, Any]:
	with records.atomic():
		doc = records.lock(case)
		report = frappe.get_doc(ACCEPTANCE, acceptance)
		signers = records.loads(report.signers_json, [])
		mine = next(s for s in signers if s["user"].lower() == actor.lower())
		if mine["state"] == "Signed":
			return records.summary(doc, acceptance=acceptance, effective=report.state == "Effective")
		mine.update(state="Signed", proof=proof, signed_at=str(clock.now()))
		records.update(report, signers_json=records.dumps(signers), record_version=cint(report.record_version) + 1)
		for name in frappe.get_all("Contract Task", filters={"contract_case": case, "command": "SignAcceptanceReport", "subject": f"acceptance {report.version_no}", "holder": actor, "state": ["in", list(work.LIVE)]}, pluck="name"):
			task = frappe.get_doc("Contract Task", name)
			records.append_json(task, "history_json", {"state": "Done", "at": str(clock.now()), "by": actor})
			records.update(task, state="Done", completed_at=clock.now())
		events.record(case, "Acceptance report signed", actor, f"{mine['name']} signed acceptance report {report.version_no}.", report=report.name, proof=proof)
		everyone = all(s["state"] == "Signed" for s in signers)
		if everyone:
			records.update(report, state="Effective", decision_at=clock.now())
			intent = intents.record(case, f"acceptance {report.version_no}", report.version_no, "Accepted receipt", "post", recovery_owner="Technical operator")
			records.update(report, posting_intent=intent.name)
			records.bump(doc, delivery_state="Accepted goods awaiting stock update")
			events.record(case, "Acceptance effective", actor, f"Acceptance report {report.version_no} is effective.", report=report.name, intent=intent.name)
		else:
			records.bump(doc)
	return records.summary(doc, acceptance=acceptance, effective=everyone)


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
	for line in records.loads(report.lines_json, []):
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
			return adapter.receive(order, identity, lines=lines), "Purchase Receipt"
		except frappe.ValidationError as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(report.posting_intent, executor, lambda identity: adapter.find_by_identity("Purchase Receipt", identity), native_doctype="Purchase Receipt")
	with records.atomic():
		if result["state"] in intents.SETTLED:
			work.finish(case, command="RestoreContractOperation", subject=f"acceptance {report.version_no}", actor=actor)
			records.bump(frappe.get_doc(CASE, case, for_update=True), delivery_state="Accepted goods received")
			events.record(case, "Receipt posted", actor, f"Accepted goods received into stock: {result['reference']}.", receipt=result["reference"], acceptance=report.name)
		else:
			work.incident(case, "RestoreContractOperation", "Restore stock or asset update", f"acceptance {report.version_no}", report.version_no)
			events.record(case, "Receipt pending", actor, f"The stock or asset update did not complete ({result['state'].lower()}).", intent=report.posting_intent)
	frappe.db.commit()
	return {"ok": True, **result}


def posted_receipts(case: str) -> list[str]:
	return frappe.get_all(intents.INTENT, filters={"contract_case": case, "operation_kind": "Accepted receipt", "state": ["in", list(intents.SETTLED)]}, pluck="result_reference")
