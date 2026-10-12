# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §4.8 / §5.6 / §7.4 — addenda.

An addendum is append-only: it never edits the approved Tender Version.
The affected reference must resolve to the current effective published
package (the approved Version plus every issued addendum); the prior value
must match exactly or the Draft is stale (`TND_ADDENDUM_STALE`); a change
that expands quantity, value or scope, changes method, reservation, lotting
or package structure, introduces a requirement or alters the evaluation
basis is refused (`TND_ADDENDUM_MATERIAL`) and follows cancellation / new-
Tender governance. Deadline-extension applicability is computed from the
issue timing; professional judgement supplies the lawful new deadline.
Issue authority is the Head of Procurement Function. `IssueAddendum`
re-verifies the bound release, builds and freezes the complete successor
Published Bid Definition (the current effective definition plus this exact
addendum, every prior identity classified) and creates the channel
confirmation work in one transaction; the addendum, its revised deadline
and its successor definition become effective together only when every
original required channel confirms the exact addendum digest
(TPR09-AC-057..062, 097..099). Return keeps the submitted row and copies a
Draft (plan W5); a material proposal can be sent to the Accounting Officer
for a cancellation review, and any unissued draft can be discarded
(TPR12-AC-012; plan W6)."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

from kentender_procurement.tenders.services import bid_definition, candidate_notices, channel_confirmation, clock, controls, digest, documents, draft_commands, envelope, events, handoffs, lifecycle, notices, serializer, template_binding
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import ROLE_ACCOUNTING_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

DOCTYPE = "Tender Addendum"
TASK_ISSUE = handoffs.ADDENDUM_ISSUE
OPEN_STATUSES = ("Draft", "Awaiting issue", "Awaiting publication confirmation")
REVIEW_REQUESTED = "Requested"
REVIEW_CLOSED = "Closed"
CHANGE_CLASSES = ("Administrative clarification", "Non-material correction", "Submission deadline extension")
AFFECTED_AREAS = ("Invitation detail", "Technical requirement", "Goods/delivery schedule", "Submission or opening detail", "Evaluation or contract term", "Other stated location")
# Governed late-amendment window: an addendum issued within this many days of
# the current deadline requires a lawful revised deadline at least this many
# days after issue. Statutory figure verification pending (FOLLOW_UPS FU-06
# family); the fixture (issue 31 May, deadline 5 Jun → extended to 12 Jun)
# satisfies it.
LATE_AMENDMENT_DAYS = 7
MATERIAL_TEXT = "This change cannot be made by addendum."
CLARIFICATION_KEY = "clarification_deadline"


def _published_version(root):
	return frappe.get_doc("Tender Version", root.approved_version or root.current_version)


def affected_references(root) -> list[dict[str, Any]]:
	"""§4.8 `affected_reference` catalogue: every published row/section a
	non-material addendum may correct, with its current effective value
	(issued addenda applied), and the rows an addendum may never change."""
	version = _published_version(root)
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	rows: list[dict[str, Any]] = [
		{"key": "delivery_location", "label": "Goods and delivery — delivery location", "area": "Goods/delivery schedule", "value": cstr(snapshot.get("delivery_location")), "material": False},
		{"key": "clarification_deadline", "label": "Invitation — clarification deadline", "area": "Invitation detail", "value": serializer.fmt_datetime_short(state.get("clarification_deadline")), "material": False},
		{"key": "submission_deadline", "label": "Submission — submission deadline", "area": "Submission or opening detail", "value": serializer.fmt_datetime_short(root.submission_deadline or state.get("submission_deadline")), "material": False},
		{"key": "pre_tender_meeting", "label": "Invitation — pre-tender meeting", "area": "Invitation detail", "value": serializer._meeting_details(state) or "No pre-tender meeting", "material": False},
		{"key": "contract_contact_office", "label": "Contract terms — contact office", "area": "Evaluation or contract term", "value": cstr(state.get("contract_contact_office")), "material": False},
		{"key": "inspection_location", "label": "Contract terms — inspection and acceptance location", "area": "Evaluation or contract term", "value": cstr(state.get("inspection_location")), "material": False},
		{"key": "tender_title", "label": "Invitation — Tender title", "area": "Invitation detail", "value": cstr(state.get("tender_title")), "material": False},
	]
	for line in serializer.goods_lines(snapshot):
		rows.append({"key": f"goods:{line['line_number']}:quantity", "label": f"{line['description']} — Quantity", "area": "Goods/delivery schedule", "value": f"{line['quantity']} {line['unit']}", "material": True})
	for tech in serializer.technical_rows(snapshot):
		value = tech["required_value"] + (f" {tech['unit']}" if tech["unit"] else "")
		rows.append({"key": f"technical:{tech['technical_requirement_id']}", "label": f"{tech['label']} — {tech['technical_requirement_id']}", "area": "Technical requirement", "value": value, "material": True})
	rows += [
		{"key": "authorised_value", "label": "Authorised value", "area": "Evaluation or contract term", "value": f"KES {serializer.fmt_money(snap.total_value(snapshot))}", "material": True},
		{"key": "procurement_method", "label": "Procurement method", "area": "Invitation detail", "value": "Open Tender", "material": True},
		{"key": "reservation_category", "label": "Reservation category", "area": "Invitation detail", "value": cstr(snapshot.get("reservation_category_value") or "None"), "material": True},
		{"key": "lotting", "label": "Lotting", "area": "Invitation detail", "value": cstr(snapshot.get("lotting_indicator")), "material": True},
		{"key": "evaluation_basis", "label": "Evaluation basis", "area": "Evaluation or contract term", "value": serializer.EVALUATION_BASIS, "material": True},
	]
	# Apply every issued addendum in order: the current effective value is the last revised one.
	for issued in frappe.get_all(DOCTYPE, filters={"tender": root.name, "status": "Issued"}, fields=["affected_reference_key", "revised_value", "revised_submission_deadline", "deadline_extension_required"], order_by="addendum_number asc"):
		for row in rows:
			if row["key"] == issued.affected_reference_key:
				row["value"] = cstr(issued.revised_value)
			if issued.deadline_extension_required and issued.revised_submission_deadline and row["key"] == "submission_deadline":
				row["value"] = serializer.fmt_datetime_short(issued.revised_submission_deadline)
	return rows


def effective_deadline(root):
	return get_datetime(root.submission_deadline) if root.submission_deadline else None


def deadline_rule(root, *, at=None, change_class: str = "", reference_key: str = "") -> dict[str, Any]:
	"""§5.6: extension is required when the addendum is issued inside the
	governed late-amendment window, when the class is a deadline extension, or
	when the affected row is the submission deadline itself (a changed
	deadline row with no revised deadline would state one date and apply
	another, AUD-TND-004)."""
	now = at or clock.now()
	current = effective_deadline(root)
	required = change_class == "Submission deadline extension" or reference_key == "submission_deadline" or (current is not None and (current - now) < timedelta(days=LATE_AMENDMENT_DAYS))
	earliest = (now + timedelta(days=LATE_AMENDMENT_DAYS)).replace(second=0, microsecond=0)
	return {
		"required": bool(required), "current_deadline": cstr(current), "current_deadline_label": serializer.fmt_datetime_short(current) if current else "",
		"earliest_revised_deadline": cstr(earliest), "earliest_revised_deadline_label": serializer.fmt_datetime_short(earliest), "late_amendment_days": LATE_AMENDMENT_DAYS,
		"explanation": "This addendum is being issued within the governed late-amendment period." if required and change_class != "Submission deadline extension" and reference_key != "submission_deadline" else ("A deadline extension always sets a lawful revised deadline." if required else "The current submission deadline is unchanged."),
	}


def require_period_open(root, *, what: str) -> None:
	"""§5.1 / §5.6 / AUD-TND-001: an addendum, its deadline and its successor
	definition can take effect only inside the open submission period. Once
	the Tender has left `Published — open`, or its deadline is reached (the
	hourly close has only not run yet), the period is over: the frozen
	submission handoff Bid Submission and Bid Opening consume must never
	diverge from the Tender. A deadline can no longer be revised."""
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	deadline = effective_deadline(root)
	if root.overall_status != "Published — open" or (deadline is not None and clock.now() >= deadline):
		fail("TND_STALE_VERSION", f"The submission period has ended, so {what}.")


def _draft_open(root) -> str:
	return cstr(frappe.db.get_value(DOCTYPE, {"tender": root.name, "status": ("in", OPEN_STATUSES)}, "name"))


def _require_open(root) -> None:
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if root.overall_status != "Published — open":
		fail("TND_STALE_VERSION", "Addenda can be prepared only while the Tender is Published — open.")


def _dict(addendum) -> dict[str, Any]:
	return {"name": addendum.name, "addendum_number": int(addendum.addendum_number or 0), "addendum_reference": cstr(addendum.addendum_reference), "status": addendum.status, "record_version": int(addendum.record_version or 0)}


# --------------------------------------------------------------------------
# CreateAddendumDraft / UpdateAddendumDraft
# --------------------------------------------------------------------------


def create_addendum_draft(*, tender: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender}
	replay = envelope.replay_or_none(idempotency_key, payload, command="CreateAddendumDraft", actor=actor)
	if replay:
		return replay
	root, _version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	_require_open(root)
	existing = _draft_open(root)
	if existing:
		doc = frappe.get_doc(DOCTYPE, existing)
		result = {"ok": True, "idempotent": False, "action": "existing", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc)}
		envelope.record_command(idempotency_key=idempotency_key, command="CreateAddendumDraft", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
		return result
	number = int(frappe.db.sql("select coalesce(max(addendum_number), 0) from `tabTender Addendum` where tender=%s", root.name)[0][0]) + 1
	from kentender_procurement.tenders.services import references

	with envelope.atomic("create-addendum"):
		doc = envelope.insert(
			frappe.get_doc(
				{
					"doctype": DOCTYPE, "tender": root.name, "publication": root.publication, "addendum_number": number, "addendum_reference": references.addendum_reference(tender_reference_value=root.tender_reference, addendum_number=number),
					"status": "Draft", "drafted_by": actor, "drafted_at": clock.now(), "baseline_digest": _baseline_digest(root), "record_version": 0, "fixture_namespace": root.fixture_namespace,
				}
			)
		)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="AddendumDraftCreated", command="CreateAddendumDraft", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Published — open", resulting_status="Published — open", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"addendum_reference": doc.addendum_reference, "drafted_as": role}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "created", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc)}
	envelope.record_command(idempotency_key=idempotency_key, command="CreateAddendumDraft", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def _baseline_digest(root) -> str:
	return digest.sha256_hex([{k: r[k] for k in ("key", "value")} for r in affected_references(root)])


def validate_values(root, values: dict[str, Any], *, current: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
	"""Clean + field errors + derived facts (material, deadline rule)."""
	errors: dict[str, str] = {}
	clean: dict[str, Any] = {}
	if not isinstance(values, dict):
		return {}, {"values": "Addendum values must be an object."}, {}
	merged = dict(current)
	merged.update(values)
	change_class = cstr(merged.get("change_class"))
	if change_class and change_class not in CHANGE_CLASSES:
		errors["change_class"] = "Choose one of: " + ", ".join(CHANGE_CLASSES) + "."
	area = cstr(merged.get("affected_area"))
	if area and area not in AFFECTED_AREAS:
		errors["affected_area"] = "Choose one of: " + ", ".join(AFFECTED_AREAS) + "."
	reference_key = cstr(merged.get("affected_reference_key")).strip()
	catalogue = {r["key"]: r for r in affected_references(root)}
	reference = catalogue.get(reference_key)
	if reference_key and not reference:
		errors["affected_reference_key"] = "Choose a published row, section or schedule line."
	for field, maximum in (("revised_value", 2000), ("reason", 1000), ("materiality_statement", 1000)):
		text = " ".join(cstr(merged.get(field)).split())
		if text and any(t in text for t in ("<", ">", "```")):
			errors[field] = "Plain text only."
		elif len(text) > maximum:
			errors[field] = f"Enter at most {maximum} characters."
		clean[field] = text
	if clean.get("reason") and len(clean["reason"]) < 20:
		errors["reason"] = "Enter a reason of 20–1,000 characters."
	clean["change_class"] = change_class
	clean["affected_area"] = area
	clean["affected_reference_key"] = reference_key
	clean["affected_reference"] = reference["label"] if reference else cstr(merged.get("affected_reference"))
	clean["previous_value"] = reference["value"] if reference else ""
	rule = deadline_rule(root, change_class=change_class, reference_key=reference_key)
	clean["deadline_extension_required"] = 1 if rule["required"] else 0
	revised = merged.get("revised_submission_deadline")
	revised_dt = None
	if revised:
		try:
			revised_dt = get_datetime(revised)
			clean["revised_submission_deadline"] = revised_dt.isoformat(sep=" ")
			current_deadline = effective_deadline(root)
			if current_deadline and revised_dt <= current_deadline:
				errors["revised_submission_deadline"] = "The revised deadline must be later than the current deadline."
			elif revised_dt < get_datetime(rule["earliest_revised_deadline"]):
				errors["revised_submission_deadline"] = f"The revised deadline must allow at least {LATE_AMENDMENT_DAYS} days from issue ({rule['earliest_revised_deadline_label']} or later)."
		except Exception:
			revised_dt = None
			errors["revised_submission_deadline"] = "Enter a valid date and time."
	else:
		clean["revised_submission_deadline"] = None
	# a deadline row's revised value is the date itself, kept as the label the notice shows (and parsed back when the addendum takes effect)
	if reference_key == "submission_deadline":
		clean["revised_value"] = serializer.fmt_datetime_short(revised_dt) if revised_dt else ""
	elif reference_key == CLARIFICATION_KEY and clean.get("revised_value"):
		clarification = serializer.parse_datetime_text(clean["revised_value"])
		bound = revised_dt or effective_deadline(root)
		if clarification is None:
			errors["revised_value"] = "Enter the revised clarification deadline as a date and time."
		elif bound is not None and clarification >= bound:
			errors["revised_value"] = "The clarification deadline must be before the submission deadline."
		else:
			clean["revised_value"] = serializer.fmt_datetime_short(clarification)
	for name in set(values) - {"change_class", "affected_area", "affected_reference_key", "revised_value", "reason", "materiality_statement", "revised_submission_deadline"}:
		errors[name] = "Unknown field."
	facts = {"material": bool(reference and reference["material"]), "deadline_rule": rule, "reference": reference}
	return clean, errors, facts


def update_addendum_draft(*, tender: str, addendum: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment, _role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender, "addendum": addendum, "values": json.dumps(values, sort_keys=True, default=str) if isinstance(values, dict) else cstr(values)}
	replay = envelope.replay_or_none(idempotency_key, payload, command="UpdateAddendumDraft", actor=actor)
	if replay:
		return replay
	root, _version = draft_commands.load(tender)
	_require_open(root)
	envelope.check_record_version(root, expected_record_version)
	doc = envelope.locked(DOCTYPE, addendum)
	if doc.tender != root.name or doc.status != "Draft":
		fail("TND_STALE_VERSION", "This addendum is not editable.")
	if cstr(doc.cancellation_review_status):
		fail("TND_STALE_VERSION", "This proposal was sent for a cancellation review and can no longer be changed. Discard it instead.")
	current = {"change_class": doc.change_class, "affected_area": doc.affected_area, "affected_reference_key": doc.affected_reference_key, "revised_value": doc.revised_value, "reason": doc.reason, "materiality_statement": doc.materiality_statement, "revised_submission_deadline": doc.revised_submission_deadline}
	clean, errors, facts = validate_values(root, values, current=current)
	if errors:
		envelope.release_claim(idempotency_key)  # a refusal returned as data is not journalled: the corrected attempt may reuse the key
		return {"ok": False, "errors": errors, "record_version": root.record_version, "material": facts.get("material", False)}
	with envelope.atomic("update-addendum"):
		envelope.bump(doc, **clean, baseline_digest=_baseline_digest(root))
		envelope.bump(root)
		events.emit(tender=root.name, event_type="AddendumDraftSaved", command="UpdateAddendumDraft", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Published — open", resulting_status="Published — open", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"values": clean, "material": facts["material"]}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "saved", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc), "material": facts["material"], "deadline_rule": facts["deadline_rule"]}
	envelope.record_command(idempotency_key=idempotency_key, command="UpdateAddendumDraft", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


# --------------------------------------------------------------------------
# Submit / Return / Issue
# --------------------------------------------------------------------------


def _require_complete_and_non_material(root, doc) -> dict[str, Any]:
	catalogue = {r["key"]: r for r in affected_references(root)}
	reference = catalogue.get(cstr(doc.affected_reference_key))
	fields: dict[str, str] = {}
	if not doc.change_class:
		fields["change_class"] = "Choose the class of change."
	if not doc.affected_area:
		fields["affected_area"] = "Choose the affected area."
	if not reference:
		fields["affected_reference_key"] = "Choose the affected published row."
	if not cstr(doc.revised_value).strip() and cstr(doc.affected_reference_key) != "submission_deadline":  # that row's value is the revised deadline, checked below
		fields["revised_value"] = "Enter the revised value."
	if cstr(doc.affected_reference_key) == CLARIFICATION_KEY and cstr(doc.revised_value).strip() and serializer.parse_datetime_text(doc.revised_value) is None:
		fields["revised_value"] = "Enter the revised clarification deadline as a date and time."
	if not (20 <= len(cstr(doc.reason).strip()) <= 1000):
		fields["reason"] = "Enter a reason of 20–1,000 characters."
	if not cstr(doc.materiality_statement).strip():
		fields["materiality_statement"] = "Explain why the change is not material."
	if fields:
		fail("TND_CONTROL_INVALID", "Complete the addendum before continuing.", {"fields": fields})
	if reference["material"]:
		fail("TND_ADDENDUM_MATERIAL", detail={"affected_reference": reference["label"], "current": reference["value"], "proposed": cstr(doc.revised_value)})
	if cstr(reference["value"]) != cstr(doc.previous_value) or _baseline_digest(root) != cstr(doc.baseline_digest):
		fail("TND_ADDENDUM_STALE", detail={"affected_reference": reference["label"], "current": reference["value"], "recorded": cstr(doc.previous_value)})
	rule = deadline_rule(root, change_class=cstr(doc.change_class), reference_key=cstr(doc.affected_reference_key))
	if rule["required"]:
		if not doc.revised_submission_deadline:
			fail("TND_ADDENDUM_DEADLINE_REQUIRED", detail=rule)
		revised = get_datetime(doc.revised_submission_deadline)
		if revised <= effective_deadline(root) or revised < get_datetime(rule["earliest_revised_deadline"]):
			fail("TND_ADDENDUM_DEADLINE_REQUIRED", detail=rule)
	return rule


def submit_addendum_for_issue(*, tender: str, addendum: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender, "addendum": addendum}
	replay = envelope.replay_or_none(idempotency_key, payload, command="SubmitAddendumForIssue", actor=actor)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	_require_open(root)
	envelope.check_record_version(root, expected_record_version)
	doc = envelope.locked(DOCTYPE, addendum)
	if doc.tender != root.name or doc.status != "Draft":
		fail("TND_STALE_VERSION", "This addendum cannot be submitted in its current state.")
	rule = _require_complete_and_non_material(root, doc)
	with envelope.atomic("submit-addendum"):
		envelope.bump(doc, status="Awaiting issue", submitted_by=actor, submitted_at=clock.now(), deadline_extension_required=1 if rule["required"] else 0)
		decision = lifecycle.record_decision(root, version, decision="Submit addendum for issue", actor=actor, business_role=role, assignment=assignment, idempotency_key=idempotency_key, subject_type=DOCTYPE, subject_id=doc.name)
		handoffs.close_open(root, task_types=(handoffs.CORRECT_ADDENDUM,), subject_id=doc.name, decision=decision.name)
		task = handoffs.open_task(root, version, task_type=TASK_ISSUE, subject_type=DOCTYPE, subject_id=doc.name, sender=actor)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="AddendumSubmittedForIssue", command="SubmitAddendumForIssue", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Draft", resulting_status="Awaiting issue", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"decision": decision.name, "task": task.name, "deadline_rule": rule}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "submitted", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc), "task": task.name}
	envelope.record_command(idempotency_key=idempotency_key, command="SubmitAddendumForIssue", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def return_addendum_for_correction(*, tender: str, addendum: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {"tender": tender, "addendum": addendum, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload, command="ReturnAddendumForCorrection", actor=actor)
	if replay:
		return replay
	reason = " ".join(cstr(reason).split())
	if not (3 <= len(reason) <= 1000):
		fail("TND_CONTROL_INVALID", "A correction comment is required.", {"fields": {"reason": "Enter what must be corrected."}})
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	doc = envelope.locked(DOCTYPE, addendum)
	if doc.tender != root.name or doc.status != "Awaiting issue":
		fail("TND_STALE_VERSION", "This addendum is not awaiting issue.")
	with envelope.atomic("return-addendum"):
		decision = lifecycle.record_decision(root, version, decision="Return addendum for correction", actor=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, assignment=assignment, idempotency_key=idempotency_key, reason=reason, subject_type=DOCTYPE, subject_id=doc.name)
		envelope.bump(doc, status="Returned", returned_by=actor, returned_at=clock.now(), return_reason=reason)
		copy = _copy_draft(root, doc)
		handoffs.close_open(root, task_types=(TASK_ISSUE,), subject_id=doc.name, decision=decision.name)
		handoffs.open_task(root, version, task_type=handoffs.CORRECT_ADDENDUM, subject_type=DOCTYPE, subject_id=copy.name, holder=cstr(doc.drafted_by), comment=reason)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="AddendumReturned", command="ReturnAddendumForCorrection", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Awaiting issue", resulting_status="Returned", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, reason=reason, payload={"decision": decision.name}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "returned", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc), "copied_draft": _dict(copy)}
	envelope.record_command(idempotency_key=idempotency_key, command="ReturnAddendumForCorrection", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def _copy_draft(root, source) -> Any:
	"""Plan W5 / §7.4 — the returned row stays as it was submitted; the
	correction continues on a copied Draft with the same number and
	reference, linked to its predecessor."""
	fields = ("change_class", "affected_area", "affected_reference", "affected_reference_key", "previous_value", "revised_value", "reason", "materiality_statement", "deadline_extension_required", "revised_submission_deadline")
	return envelope.insert(
		frappe.get_doc(
			{
				"doctype": DOCTYPE, "tender": root.name, "publication": source.publication, "addendum_number": source.addendum_number, "addendum_reference": source.addendum_reference,
				"status": "Draft", **{f: source.get(f) for f in fields}, "baseline_digest": _baseline_digest(root), "drafted_by": source.drafted_by, "drafted_at": clock.now(),
				"predecessor_addendum": source.name, "record_version": 0, "fixture_namespace": root.fixture_namespace,
			}
		)
	)


def notice_context(root, doc) -> dict[str, Any]:
	version = _published_version(root)
	state = serializer.officer_state(version)
	contact_display, contact_address = serializer._office_display(state.get("contract_contact_office"))
	return {
		"procuring_entity": {"name": cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name")), "address": contact_address, "contact_office": contact_display},
		"platform": {"name": serializer.PLATFORM_NAME},
		"tender": {"reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "submission_deadline": serializer.fmt_datetime_eat(root.submission_deadline), "published_at": serializer.fmt_datetime_eat(root.published_at)},
		"addendum": {
			"number": int(doc.addendum_number), "reference": cstr(doc.addendum_reference), "issued_at": serializer.fmt_datetime_eat(doc.issue_decided_at or clock.now()), "change_class": cstr(doc.change_class), "affected_area": cstr(doc.affected_area),
			"affected_reference": cstr(doc.affected_reference), "previous_value": cstr(doc.previous_value), "revised_value": cstr(doc.revised_value), "reason": cstr(doc.reason),
			"deadline_extension_required": bool(doc.deadline_extension_required), "revised_submission_deadline": serializer.fmt_datetime_eat(doc.revised_submission_deadline) if doc.revised_submission_deadline else "",
			"issued_by": cstr(frappe.db.get_value("User", doc.issue_decided_by, "full_name") or doc.issue_decided_by) if doc.issue_decided_by else "",
		},
	}


def issue_addendum(*, tender: str, addendum: str, expected_record_version, idempotency_key: str, user: str | None = None, task: str = "", task_token: str = "") -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {"tender": tender, "addendum": addendum}
	replay = envelope.replay_or_none(idempotency_key, payload, command="IssueAddendum", actor=actor)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	_require_open(root)
	require_period_open(root, what="an addendum can no longer be issued")
	envelope.check_record_version(root, expected_record_version)
	doc = envelope.locked(DOCTYPE, addendum)
	if doc.tender != root.name or doc.status != "Awaiting issue":
		fail("TND_STALE_VERSION", "This addendum is not awaiting issue.")
	open_issue = lifecycle.open_task(root, task_type=TASK_ISSUE, subject_id=doc.name)
	if task and open_issue and open_issue.name != task:
		fail("TND_STALE_VERSION", "This task has already changed. Reload to see the current decision.")
	if task_token and open_issue:
		envelope.assert_task_token(open_issue, task_token)
	rule = _require_complete_and_non_material(root, doc)
	publication = frappe.get_doc("Tender Publication", root.publication)
	approved = frappe.get_doc("Tender Version", publication.tender_version)
	# §5.1 / TPR11-AC-004: the bound release must still verify before a
	# successor definition is built on it (Superseded continues, Withdrawn blocks).
	template_binding.require_bound(approved, "publication")
	channels = json.loads(publication.required_channels_json or "[]")
	issued_at = clock.now()
	prior = bid_definition.current(root.name)
	if not prior:
		fail("TND_MAPPING_INCOMPLETE", detail={"reason": "The published Tender has no effective supplier definition to amend."})
	issued = frappe.get_all(DOCTYPE, filters={"tender": root.name, "status": "Issued"}, fields=["name", "affected_reference_key", "revised_value", "deadline_extension_required", "revised_submission_deadline"], order_by="addendum_number asc")
	with envelope.atomic("issue-addendum"):
		# §5.6: freeze the complete successor definition first; any failure
		# leaves the addendum Awaiting issue with no definition and no channel work.
		successor = bid_definition.build_successor(root, approved, publication_id=publication.name, prior=prior["definition"], issued_addenda=issued, candidate=doc)
		definition = successor["definition"]
		doc.issue_decided_by, doc.issue_decided_at = actor, issued_at
		rendered = notices.render_addendum_notice(notice_context(root, doc))
		addendum_digest = digest.sha256_hex({"addendum": cstr(doc.addendum_reference), "change_class": cstr(doc.change_class), "affected_reference_key": cstr(doc.affected_reference_key), "previous_value": cstr(doc.previous_value), "revised_value": cstr(doc.revised_value), "reason": cstr(doc.reason), "materiality_statement": cstr(doc.materiality_statement), "baseline_digest": cstr(doc.baseline_digest), "deadline_extension_required": bool(doc.deadline_extension_required), "revised_submission_deadline": cstr(doc.revised_submission_deadline), "issue_decided_by": actor, "issue_decided_at": cstr(issued_at), "notice_digest": rendered["digest"], "package_digest": cstr(publication.package_digest), "successor_definition_digest": definition["definition_digest"]})
		document = documents.store(tender=root.name, kind=documents.KIND_ADDENDUM, html=rendered["html"], digest_value=rendered["digest"], addendum=doc.name, file_base=f"{cstr(doc.addendum_reference)}-notice", fixture_namespace=root.fixture_namespace)
		definition_row = bid_definition.store(root, approved, definition=definition, publication=publication.name, addendum=doc.name, status="Frozen", at=issued_at, predecessor=prior["name"], identity_map=bid_definition.identity_map_of(successor))
		envelope.bump(
			doc, status="Awaiting publication confirmation", issue_decided_by=actor, issue_decided_at=issued_at, addendum_digest=addendum_digest,
			successor_bid_definition=definition_row.name, successor_bid_definition_id=definition["bid_definition_id"], successor_definition_version=int(definition["definition_version"]),
			successor_definition_digest=definition["definition_digest"],
		)
		rows = channel_confirmation.create_rows(root=root, publication_name=publication.name, subject_type=channel_confirmation.SUBJECT_ADDENDUM, subject_id=doc.name, subject_digest=addendum_digest, channels=[{"channel": c["channel"], "label": c["label"]} for c in channels])
		decision = lifecycle.record_decision(root, version, decision="Issue addendum", actor=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, assignment=assignment, idempotency_key=idempotency_key, subject_type=DOCTYPE, subject_id=doc.name)
		if open_issue:
			lifecycle.complete_task(open_issue, decision.name)
		confirmation_task = handoffs.open_task(root, version, task_type=handoffs.CHANNEL_CONFIRMATION, subject_type=DOCTYPE, subject_id=doc.name, sender=cstr(doc.drafted_by))
		envelope.bump(root)
		events.emit(tender=root.name, event_type="AddendumIssueDecided", command="IssueAddendum", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Awaiting issue", resulting_status="Awaiting publication confirmation", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"addendum_digest": addendum_digest, "notice_digest": rendered["digest"], "document": document, "channels": [r.channel for r in rows], "deadline_rule": rule, "revised_submission_deadline": cstr(doc.revised_submission_deadline), "successor_bid_definition_id": definition["bid_definition_id"], "successor_definition_digest": definition["definition_digest"], "classifications": {c: sum(1 for x in successor["classifications"] if x["classification"] == c) for c in ("unchanged", "converted", "fresh_response_required", "removed", "new")}, "decision": decision.name, "task": confirmation_task.name}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "issued", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc), "addendum_digest": addendum_digest, "confirmations": [r.name for r in rows], "task": confirmation_task.name}
	envelope.record_command(idempotency_key=idempotency_key, command="IssueAddendum", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def confirm_addendum_publication_channel(*, tender: str, addendum: str, channel: str, available_at, evidence_reference: str, evidence_file: str, addendum_digest: str, expected_record_version, idempotency_key: str, public_url: str = "", url_not_applicable_reason: str = "", evidence_notes: str = "", attestation_confirmed: bool = False, user: str | None = None) -> dict[str, Any]:
	name = draft_commands.resolve_tender_name(tender)
	if cstr(frappe.db.get_value(DOCTYPE, addendum, "tender")) != name:
		authz.not_found()
	return channel_confirmation.confirm_channel(
		subject_type=channel_confirmation.SUBJECT_ADDENDUM, subject_id=addendum, channel=channel, available_at=available_at, evidence_reference=evidence_reference, public_url=public_url,
		url_not_applicable_reason=url_not_applicable_reason, evidence_file=evidence_file, evidence_notes=evidence_notes, attestation_confirmed=attestation_confirmed, package_digest=addendum_digest,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, on_all_confirmed=_all_channels_confirmed, command="ConfirmAddendumPublicationChannel",
		precondition=lambda root: require_period_open(root, what="an addendum can no longer become effective"),
	)


def _all_channels_confirmed(root, rows, *, actor: str, assignment, idempotency_key: str) -> dict[str, Any]:
	doc = envelope.locked(DOCTYPE, rows[0].subject_id)
	if doc.status == "Issued":
		return {"ok": True, "idempotent": True, "issued_at": cstr(doc.issued_at)}
	issued_at = channel_confirmation.latest_available_at(channel_confirmation.SUBJECT_ADDENDUM, doc.name)
	# §5.6 / TPR09-AC-099: the addendum, its revised deadline and its frozen
	# successor definition become effective together, once.
	envelope.bump(doc, status="Issued", issued_at=issued_at)
	if doc.successor_bid_definition:
		bid_definition.activate(root, doc.successor_bid_definition, at=issued_at)
	updates: dict[str, Any] = {}
	if doc.deadline_extension_required and doc.revised_submission_deadline:
		updates["submission_deadline"] = doc.revised_submission_deadline
	if cstr(doc.affected_reference_key) == CLARIFICATION_KEY:
		clarification = serializer.parse_datetime_text(doc.revised_value)
		if clarification is not None:
			updates["clarification_deadline"] = clarification
	if updates:
		envelope.bump(root, **updates)
	handoffs.close_open(root, task_types=(handoffs.CHANNEL_CONFIRMATION,), subject_id=doc.name)
	# One candidate notice per registered candidate; a deadline change is part
	# of the same addendum notice, not a second message (§10.1).
	candidate_notices.freeze(
		root, notice_type="Addendum issued", subject_type=DOCTYPE, subject_id=doc.name, subject_digest=cstr(doc.addendum_digest),
		content={"tender_reference": root.tender_reference, "addendum": cstr(doc.addendum_reference), "addendum_digest": cstr(doc.addendum_digest), "issued_at": cstr(issued_at), "revised_submission_deadline": cstr(updates.get("submission_deadline") or "")},
	)
	events.emit(tender=root.name, event_type="AddendumIssued", command="ConfirmAddendumPublicationChannel", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Awaiting publication confirmation", resulting_status="Issued", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"issued_at": cstr(issued_at), "addendum_digest": cstr(doc.addendum_digest), "revised_submission_deadline": cstr(doc.revised_submission_deadline), "successor_bid_definition_id": cstr(doc.successor_bid_definition_id), "channels_digest": channel_confirmation.confirmation_digest(channel_confirmation.SUBJECT_ADDENDUM, doc.name)}, fixture_namespace=root.fixture_namespace)
	return {"ok": True, "idempotent": False, "issued_at": cstr(issued_at), "submission_deadline": cstr(updates.get("submission_deadline") or root.submission_deadline)}


# --------------------------------------------------------------------------
# DiscardAddendumDraft / RequestTenderCancellationReview / CloseTenderCancellationReview
# --------------------------------------------------------------------------


def _material_reference(root, doc) -> dict[str, Any] | None:
	reference = {r["key"]: r for r in affected_references(root)}.get(cstr(doc.affected_reference_key))
	return reference if reference and reference["material"] else None


def discard_addendum_draft(*, tender: str, addendum: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4 — archive one unissued Draft (a material proposal included); an
	issued or publishing addendum is never affected. Returns to the
	unchanged Published Tender."""
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender, "addendum": addendum}
	replay = envelope.replay_or_none(idempotency_key, payload, command="DiscardAddendumDraft", actor=actor)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	doc = envelope.locked(DOCTYPE, addendum)
	if doc.tender != root.name:
		authz.not_found()
	if doc.status != "Draft":
		fail("TND_STALE_VERSION", "Only an unissued addendum draft can be discarded.")
	if cstr(doc.cancellation_review_status) == REVIEW_REQUESTED:
		fail("TND_STALE_VERSION", "The Accounting Officer is considering cancellation for this proposal. Wait for the decision.")
	with envelope.atomic("discard-addendum"):
		envelope.bump(doc, status="Discarded", discarded_by=actor, discarded_at=clock.now())
		decision = lifecycle.record_decision(root, version, decision="Discard addendum draft", actor=actor, business_role=role, assignment=assignment, idempotency_key=idempotency_key, subject_type=DOCTYPE, subject_id=doc.name)
		handoffs.close_open(root, task_types=(handoffs.CORRECT_ADDENDUM,), subject_id=doc.name, decision=decision.name)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="AddendumDraftDiscarded", command="DiscardAddendumDraft", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Draft", resulting_status="Discarded", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"decision": decision.name}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "discarded", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc)}
	envelope.record_command(idempotency_key=idempotency_key, command="DiscardAddendumDraft", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def request_tender_cancellation_review(*, tender: str, addendum: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4 — for a blocked material-addendum proposal, send the reason and
	the affected comparison to the Accounting Officer: one AO item and one
	sender waiting item. Changes neither the published Tender nor the
	addendum; the same proposal cannot request another review once closed."""
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender, "addendum": addendum, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload, command="RequestTenderCancellationReview", actor=actor)
	if replay:
		return replay
	text = " ".join(cstr(reason).split())
	if not (20 <= len(text) <= 1000):
		fail("TND_CONTROL_INVALID", "Enter a reason of 20–1,000 characters.", {"fields": {"reason": "Enter a reason of 20–1,000 characters."}})
	root, version = draft_commands.load(tender)
	_require_open(root)
	envelope.check_record_version(root, expected_record_version)
	doc = envelope.locked(DOCTYPE, addendum)
	if doc.tender != root.name or doc.status != "Draft":
		fail("TND_STALE_VERSION", "Only an unissued addendum proposal can be sent for a cancellation review.")
	reference = _material_reference(root, doc)
	if not reference:
		fail("TND_STALE_VERSION", "This proposal can be issued as an addendum; no cancellation review is needed.")
	status = cstr(doc.cancellation_review_status)
	if status == REVIEW_REQUESTED:
		task = frappe.db.get_value("Tender Task", {"tender": root.name, "task_type": handoffs.CANCELLATION_REVIEW, "subject_id": doc.name, "status": "Open"}, "name")
		result = {"ok": True, "idempotent": True, "action": "already_requested", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc), "task": cstr(task)}
		envelope.record_command(idempotency_key=idempotency_key, command="RequestTenderCancellationReview", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
		return result
	if status == REVIEW_CLOSED:
		fail("TND_STALE_VERSION", "The Accounting Officer already closed the cancellation review for this proposal. Discard the draft instead.")
	comparison = f"{reference['label']}: {reference['value']} → {cstr(doc.revised_value)}"
	with envelope.atomic("request-cancellation-review"):
		envelope.bump(doc, cancellation_review_status=REVIEW_REQUESTED, cancellation_review_reason=text)
		decision = lifecycle.record_decision(root, version, decision="Request cancellation review", actor=actor, business_role=role, assignment=assignment, idempotency_key=idempotency_key, reason=text, subject_type=DOCTYPE, subject_id=doc.name)
		task = handoffs.open_task(root, version, task_type=handoffs.CANCELLATION_REVIEW, subject_type=DOCTYPE, subject_id=doc.name, sender=actor, comment=f"{comparison}. {text}")
		envelope.bump(root)
		events.emit(tender=root.name, event_type="CancellationReviewRequested", command="RequestTenderCancellationReview", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Published — open", resulting_status="Published — open", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, reason=text, payload={"comparison": {"reference": reference["label"], "current": reference["value"], "proposed": cstr(doc.revised_value)}, "decision": decision.name, "task": task.name}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "requested", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc), "task": task.name}
	envelope.record_command(idempotency_key=idempotency_key, command="RequestTenderCancellationReview", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def close_tender_cancellation_review(*, tender: str, addendum: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4 — the Accounting Officer records that cancellation will not be
	pursued: the AO item clears, the Tender stays open and the material
	addendum stays blocked. Not an approval, publication or cancellation."""
	actor = authz.actor(user)
	assignment = authz.require_ao(actor)
	payload = {"tender": tender, "addendum": addendum, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload, command="CloseTenderCancellationReview", actor=actor)
	if replay:
		return replay
	text = " ".join(cstr(reason).split())
	if not (10 <= len(text) <= 1000):
		fail("TND_CONTROL_INVALID", "Enter a reason of 10–1,000 characters.", {"fields": {"reason": "Enter a reason of 10–1,000 characters."}})
	root, version = draft_commands.load(tender)
	_require_open(root)
	envelope.check_record_version(root, expected_record_version)
	doc = envelope.locked(DOCTYPE, addendum)
	if doc.tender != root.name or cstr(doc.cancellation_review_status) != REVIEW_REQUESTED:
		fail("TND_STALE_VERSION", "There is no open cancellation review for this proposal.")
	with envelope.atomic("close-cancellation-review"):
		envelope.bump(doc, cancellation_review_status=REVIEW_CLOSED, cancellation_review_closed_reason=text)
		decision = lifecycle.record_decision(root, version, decision="Close cancellation review", actor=actor, business_role=ROLE_ACCOUNTING_OFFICER, assignment=assignment, idempotency_key=idempotency_key, reason=text, subject_type=DOCTYPE, subject_id=doc.name)
		handoffs.close_open(root, task_types=(handoffs.CANCELLATION_REVIEW,), subject_id=doc.name, decision=decision.name)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="CancellationReviewClosed", command="CloseTenderCancellationReview", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Published — open", resulting_status="Published — open", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, reason=text, payload={"decision": decision.name}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "review_closed", "tender": root.name, "record_version": root.record_version, "addendum": _dict(doc)}
	envelope.record_command(idempotency_key=idempotency_key, command="CloseTenderCancellationReview", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result
