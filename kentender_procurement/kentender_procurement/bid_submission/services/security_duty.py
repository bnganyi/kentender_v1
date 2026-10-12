# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The tender-security intake duty (Project Owner decisions of 10 October 2026).

Recording a physical original or an issuer confirmation is an explicit,
Tender-scoped responsibility — `Tender Security Intake Officer` in the
responsibility registry — assigned by the Head of Procurement Function to an
existing eligible officer, with the effective period and the assigner on the
assignment. Nothing else grants it: not the Head of Procurement Function
office, not an opening or evaluation appointment, not Administrator or
System Manager status.

**Separation (approved product policy, not a statutory prohibition).** On the
same Tender, intake and opening or evaluation duties exclude each other, in
both directions:

- an intake assignment is refused for a person who sits on that Tender's
  opening committee or evaluation committee, is its evaluation secretary, or
  holds the Head of Procurement Function office (the Head is the evaluation
  secretary by office on every Tender);
- an opening or evaluation appointment is refused for a person who holds an
  intake assignment for that Tender (even one not yet used) or who has ever
  recorded or viewed its intake records.

Ending an assignment ends the access; it does not erase the exposure. An
unused assignment may be revoked before an appointment, which makes the
person eligible again; once exposed, the person stays ineligible for that
Tender. Refusal messages name the incompatible duty and never a supplier.

Opening and Evaluation publish who sits on their committees through the
`kt_tender_duty_participants` hook (`{user: duty label}` for a Tender), so
this module never imports a downstream module."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime, now_datetime

from kentender_core.services import authorization
from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

from kentender_procurement.bid_submission.services import clock, records, tenders_gateway

ROLE = "Tender Security Intake Officer"
HEAD = "Head of Procurement Function"
ACCOUNTING_OFFICER = "Accounting Officer"
ASSIGNMENT = authorization.ASSIGNMENT_DOCTYPE
EXPOSURE = "Tender Security Exposure"
CONFLICT = "Tender Security Duty Conflict"
INTAKE = "Tender Security Intake"
PARTICIPANTS_HOOK = "kt_tender_duty_participants"

GENERIC_BASIS = "Holds or has held the intake duty"
RECORDED = "Recorded an intake"
VIEWED = "Viewed intake records"

DENIED = "You are not assigned to record tender-security receipts for this Tender."
ASSIGN_DENIED = "Only the Head of Procurement Function assigns the tender-security intake duty."
HEAD_MESSAGE = "{name} holds the Head of Procurement Function office, which makes them the evaluation secretary of every Tender, so they cannot also take its tender-security intake."
PARTICIPANT_MESSAGE = "{name} is {duty} for this Tender, so cannot also take its tender-security intake."
# One wording for an assigned and for an exposed person, so the message never
# tells the reader whether the duty was actually used.
COMMITTEE_BLOCKED = "{name} holds or has held the tender-security intake duty for this Tender and cannot be appointed to {duty}."
INCOMPATIBLE = "AUTH_SEGREGATION_BLOCKED"


def _name(user: str) -> str:
	return frappe.db.get_value("User", user, "full_name") or user


# -- who holds the duty ----------------------------------------------------------


def published_tender(reference: str):
	return tenders_gateway.tender_root(cstr(reference).strip()) if cstr(reference).strip() else None


def holds_duty(user: str, tender_reference: str, at=None) -> bool:
	"""True when `user` holds an Active Tender-scoped assignment for exactly this
	Tender now. Administrator and System Manager status never counts: command
	purpose admits no technical reader."""
	if not user or user == "Guest" or not cstr(tender_reference).strip():
		return False
	return authorise_record(user=user, business_role=ROLE, at=at, purpose=PURPOSE_COMMAND, scope_reference=cstr(tender_reference).strip()).allowed


def require_officer(user: str, tender_reference: str) -> None:
	if not holds_duty(user, tender_reference):
		raise frappe.PermissionError(DENIED)


def officer_tenders(user: str, at=None) -> list[str]:
	"""The Tender references this person is assigned the duty for, now."""
	if not user or user == "Guest":
		return []
	return sorted({a.scope_reference for a in authorization.resolve_assignments(user, ROLE, at) if a.scope_reference})


def may_assign(user: str) -> bool:
	return bool(user) and user != "Guest" and authorise_record(user=user, business_role=HEAD, purpose=PURPOSE_COMMAND).allowed


def require_head(user: str) -> None:
	if not may_assign(user):
		raise frappe.PermissionError(ASSIGN_DENIED)


# -- exposure ---------------------------------------------------------------------


def record_exposure(tender: str, tender_reference: str, user: str, kind: str, intake_reference: str = "") -> None:
	"""Append one exposure fact (no commit; inside the caller's command)."""
	records.insert(frappe.get_doc({
		"doctype": EXPOSURE, "tender": tender, "tender_reference": tender_reference, "user": user, "kind": kind,
		"intake_reference": intake_reference, "exposed_at": clock.now(),
	}))


def has_exposure(tender: str, user: str) -> bool:
	"""The person recorded intake for this Tender, or viewed its intake records."""
	return bool(frappe.db.exists(EXPOSURE, {"tender": tender, "user": user}) or frappe.db.exists(INTAKE, {"tender": tender, "recorded_by": user}))


def open_assignments(tender_reference: str, user: str = "") -> list[dict[str, Any]]:
	"""Enabled (not revoked) assignments for this Tender, whether in force, scheduled or expired."""
	filters: dict[str, Any] = {"business_role": ROLE, "scope_reference": tender_reference, "status": authorization.STATUS_ENABLED}
	if user:
		filters["user"] = user
	rows = frappe.get_all(ASSIGNMENT, filters=filters, fields=["name", "user", "effective_from", "effective_to", "assigned_by", "assigned_at"], order_by="creation asc", limit_page_length=0)
	at = now_datetime()
	return [r for r in rows if not r.effective_to or get_datetime(r.effective_to) >= at]


# -- who sits on the Tender's opening and evaluation ------------------------------


def participants(tender: str) -> dict[str, list[str]]:
	"""{user: [duty label, ...]} for the Tender's opening and evaluation, as the
	owning modules publish it."""
	out: dict[str, list[str]] = {}
	for path in frappe.get_hooks(PARTICIPANTS_HOOK) or []:
		for user, duty in (frappe.get_attr(path)(tender) or {}).items():
			out.setdefault(user, []).append(duty)
	return out


def intake_blocker(tender: str, user: str) -> str | None:
	"""Why `user` cannot be assigned the intake duty on this Tender, as a plain
	sentence naming the incompatible duty; None when nothing prevents it."""
	name = _name(user)
	if user in authorization.active_holders(HEAD):
		return HEAD_MESSAGE.format(name=name)
	duties = participants(tender).get(user)
	if duties:
		return PARTICIPANT_MESSAGE.format(name=name, duty=" and ".join(sorted(set(duties))))
	return None


def committee_blocker(tender: str, user: str, duty: str, kind: str) -> str | None:
	"""Why `user` cannot be appointed to `duty` (for example "the opening committee")
	on this Tender: they hold an intake assignment for it, or have been exposed to
	its intake records. `kind` is the conflict register's name for the duty
	("Opening committee", "Evaluation committee", "Evaluation secretary"); a
	conflict the Accounting Officer has explicitly resolved for that person and
	duty no longer blocks. None when nothing prevents it."""
	row = frappe.db.get_value("Tender", tender, "tender_reference")
	name = _name(user)
	if frappe.db.exists(CONFLICT, {"tender": tender, "user": user, "conflicting_duty": kind, "status": "Resolved"}):
		return None
	if (row and open_assignments(row, user)) or has_exposure(tender, user):
		return COMMITTEE_BLOCKED.format(name=name, duty=duty)
	return None


def guard_grant(*, user: str, principal: str, scope_reference: str, effective_from=None, effective_to=None) -> tuple[str, str] | None:
	"""The `kt_responsibility_grant_guards` hook for the intake duty: a published
	Tender, an eligible officer, and no overlap with its opening or evaluation."""
	root = published_tender(scope_reference)
	if not root:
		return "AUTH_CONFIGURATION_INVALID", "No published Tender has this reference."
	blocked = intake_blocker(root.name, user)
	if blocked:
		return INCOMPATIBLE, blocked
	if effective_from and effective_to and get_datetime(effective_to) <= get_datetime(effective_from):
		return "AUTH_CONFIGURATION_INVALID", "The end of the effective period must be later than its start."
	return None


# -- the Head of Procurement Function's surface -------------------------------------


def eligible_officers(tender_reference: str, *, user: str | None = None) -> dict[str, Any]:
	"""Existing officers the Head may assign, with the reason anyone is not
	eligible. Carries no supplier or bid information."""
	actor = cstr(user or frappe.session.user)
	require_head(actor)
	root = published_tender(tender_reference)
	if not root:
		return {"found": False, "text": "No published Tender has this reference.", "officers": []}
	holders = set(authorization.active_holders(HEAD))
	candidates = sorted(set(frappe.get_all(ASSIGNMENT, filters={"status": authorization.STATUS_ENABLED}, pluck="user", limit_page_length=0)))
	officers = []
	for candidate in candidates:
		if candidate == actor or authorization.is_technical(candidate) or not frappe.db.get_value("User", candidate, "enabled"):
			continue
		roles = sorted({r["business_role"] for r in authorization.active_assignment_rows(candidate) if r["business_role"] != ROLE})
		if not roles:
			continue
		reason = intake_blocker(root.name, candidate)
		officers.append({"user": candidate, "full_name": _name(candidate), "responsibilities": roles, "eligible": reason is None, "reason": reason or "",
			"assigned": bool(open_assignments(root.tender_reference, candidate)), "is_head": candidate in holders})
	return {"found": True, "tender_reference": root.tender_reference, "tender_title": cstr(frappe.db.get_value("Tender", root.name, "requirement_title") or ""), "officers": officers}


def list_duty(tender_reference: str, *, user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	require_head(actor)
	root = published_tender(tender_reference)
	if not root:
		return {"found": False, "text": "No published Tender has this reference.", "rows": []}
	from kentender_core.services.authorization import derived_status

	rows = frappe.get_all(ASSIGNMENT, filters={"business_role": ROLE, "scope_reference": root.tender_reference}, fields=["name", "user", "status", "effective_from", "effective_to", "assigned_by", "assigned_at", "revoked_by", "revoked_at", "revocation_reason"], order_by="creation desc", limit_page_length=0)
	return {"found": True, "tender_reference": root.tender_reference, "rows": [{
		"assignment": r.name, "user": r.user, "full_name": _name(r.user), "status": derived_status(r.status, r.effective_from, r.effective_to),
		"effective_from": str(r.effective_from or ""), "effective_to": str(r.effective_to or ""), "assigned_by": _name(cstr(r.assigned_by)), "assigned_at": str(r.assigned_at or ""),
		"revoked_by": _name(cstr(r.revoked_by)) if r.revoked_by else "", "revoked_at": str(r.revoked_at or ""), "revocation_reason": cstr(r.revocation_reason),
	} for r in rows]}


def assign_intake_officer(*, tender_reference: str, officer: str, effective_from: str = "", effective_to: str = "", user: str | None = None) -> dict[str, Any]:
	"""The Head of Procurement Function assigns the duty for one Tender (existing
	assignment mechanism: audited, period-bound, revocable)."""
	from kentender_core.services import responsibility_administration as administration

	actor = cstr(user or frappe.session.user)
	require_head(actor)
	result = administration.grant(
		user=officer, business_role=ROLE, scope_reference=cstr(tender_reference).strip(), appointment_type=administration.APPOINTMENT_PERMANENT,
		effective_from=effective_from or None, effective_to=effective_to or None, actor=actor, fixture_namespace=records.namespace(),
	)
	return {"ok": True, **result}


def revoke_intake_officer(*, assignment: str, reason: str, user: str | None = None) -> dict[str, Any]:
	"""Ends the access. Prior exposure stays on record, so a person who already
	recorded or viewed this Tender's intake stays ineligible for its opening and
	evaluation; an unused assignment leaves no such mark."""
	from kentender_core.services import responsibility_administration as administration

	actor = cstr(user or frappe.session.user)
	require_head(actor)
	row = frappe.db.get_value(ASSIGNMENT, assignment, ["business_role"], as_dict=True)
	if not row or row.business_role != ROLE:
		raise frappe.DoesNotExistError("Not found")
	return {"ok": True, **administration.revoke(assignment, reason=reason, actor=actor)}


# -- existing conflicts, flagged for explicit resolution ------------------------------


def detect_conflicts() -> list[str]:
	"""Flag every Tender where someone who holds, held or exercised the intake duty
	also sits on, or is the secretary of, its opening or evaluation. Idempotent:
	an already flagged pair is left as it is. Nothing is deleted or reassigned."""
	found: list[str] = []
	at = clock.now()
	tenders = {r.tender: r.tender_reference for r in frappe.get_all(INTAKE, fields=["tender", "tender_reference"], limit_page_length=0)}
	for r in frappe.get_all(EXPOSURE, fields=["tender", "tender_reference"], limit_page_length=0):
		tenders[r.tender] = r.tender_reference
	for r in frappe.get_all(ASSIGNMENT, filters={"business_role": ROLE}, fields=["scope_reference"], limit_page_length=0):
		root = published_tender(r.scope_reference or "")
		if root:
			tenders[root.name] = root.tender_reference
	for tender, reference in tenders.items():
		if not frappe.db.exists("Tender", tender):
			continue  # a removed Tender leaves nothing to flag
		who = {r.user for r in frappe.get_all(ASSIGNMENT, filters={"business_role": ROLE, "scope_reference": reference}, fields=["user"], limit_page_length=0)}
		who |= {r.user for r in frappe.get_all(EXPOSURE, filters={"tender": tender}, fields=["user"], limit_page_length=0)}
		who |= {r.recorded_by for r in frappe.get_all(INTAKE, filters={"tender": tender}, fields=["recorded_by"], limit_page_length=0)}
		duties = participants(tender)
		for user in sorted(who & set(duties)):
			basis = "Has recorded intake" if frappe.db.exists(INTAKE, {"tender": tender, "recorded_by": user}) else "Has viewed intake records" if frappe.db.exists(EXPOSURE, {"tender": tender, "user": user}) else "Holds the intake duty"
			for duty in sorted(set(duties[user])):
				kind = "Opening committee" if "opening" in duty else "Evaluation secretary" if "secretary" in duty else "Evaluation committee"
				if frappe.db.exists(CONFLICT, {"tender": tender, "user": user, "conflicting_duty": kind}):
					continue
				doc = records.insert(frappe.get_doc({"doctype": CONFLICT, "tender": tender, "tender_reference": reference, "user": user, "conflicting_duty": kind,
					"basis": basis, "status": "Open", "detected_at": at, "detected_by": "System"}))
				found.append(doc.name)
	return found


def list_conflicts(*, status: str = "Open", user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	if not (may_assign(actor) or authorise_record(user=actor, business_role=ACCOUNTING_OFFICER, purpose=PURPOSE_COMMAND).allowed):
		raise frappe.PermissionError(ASSIGN_DENIED)
	rows = frappe.get_all(CONFLICT, filters={"status": status} if status else {}, fields=["name", "tender_reference", "user", "conflicting_duty", "basis", "status", "detected_at", "resolution_reason", "resolved_by", "resolved_at"], order_by="detected_at asc", limit_page_length=0)
	# The stored basis says exactly why (held, recorded, viewed); the Head and the Accounting Officer are not
	# authorised to learn whether any intake exists, so both see one generic basis.
	return {"rows": [{**dict(r), "basis": GENERIC_BASIS, "full_name": _name(r.user), "detected_at": str(r.detected_at), "resolved_at": str(r.resolved_at or "")} for r in rows]}


def resolve_conflict(*, conflict: str, reason: str, user: str | None = None) -> dict[str, Any]:
	"""The Accounting Officer records how a flagged conflict was resolved, with a
	reason. The flagged record, the assignment and the audit history stay."""
	actor = cstr(user or frappe.session.user)
	if not authorise_record(user=actor, business_role=ACCOUNTING_OFFICER, purpose=PURPOSE_COMMAND).allowed:
		raise frappe.PermissionError("Only the Accounting Officer resolves a tender-security duty conflict.")
	reason = " ".join(cstr(reason).split())
	if not 10 <= len(reason) <= 500:
		return {"ok": False, "errors": {"reason": "Enter the resolution (10–500 characters)."}}
	doc = frappe.get_doc(CONFLICT, conflict)
	if doc.status == "Resolved":
		return {"ok": True, "conflict": doc.name, "changed": False}
	doc.status, doc.resolution_reason, doc.resolved_by, doc.resolved_at = "Resolved", reason, actor, clock.now()
	records.save(doc)
	return {"ok": True, "conflict": doc.name, "changed": True}
