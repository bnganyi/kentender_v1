# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.31 §5.5.2.2 / §5.5.2.4 / §7.2 — the Procurement Planner's
publication confirmation.

For MVP 1 the entity submits the approved Annual Plan to the National Treasury
and publishes it on its own website outside KenTender (Project Owner
instruction, 9 October 2026). The Planner records both completed facts for the
exact approved Version in one action. Confirmation stores the evidence
immutably and then invokes the existing activation logic
(`publication_pipeline.activate_plan_version`) once, in the same transaction;
it is never a direct status change to Active. It grants no authority to approve
or change the plan.

Three commands: `save_publication_draft` (incomplete evidence, never evidence),
`confirm_plan_publication` and `correct_publication_details` (append and
supersede, with a reason; the earlier record is kept)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import frappe
from frappe.utils import add_days, cstr, getdate, nowdate, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, publication_pipeline
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER
from kentender_procurement.procurement_planning.write_family import planning_command

DOCTYPE = "Plan Publication Confirmation"
CONFIRMATION_STATEMENT = "I confirm that this approved version was submitted to the National Treasury and published on the entity’s website."

#: A Version the Planner may confirm. `Publication failed` is historical: no
#: MVP 1 command enters it, but a Version already there is not stranded.
OPEN_STATES = ("Approved — publication pending", "Publication failed")
#: A Version whose recorded details may be corrected (the plan content never is).
CORRECTABLE_STATES = ("Active", "Published — activation held", "Superseded")

FIELDS = (
	"treasury_submitted_on", "treasury_reference", "treasury_attachment", "website_published_on", "public_plan_url", "confirmation_acknowledged",
)
_EVIDENCE_TYPES = ("pdf", "png", "jpg", "jpeg")
_TRUE = (True, 1, "1", "true", "True")


def _as_values(values: Any) -> dict[str, Any]:
	if isinstance(values, str):
		import json

		values = json.loads(values) if values.strip() else {}
	values = dict(values or {})
	unknown = sorted(set(values) - set(FIELDS))
	if unknown:
		fail("PLN_ENTRY_INCOMPLETE", f"These details are not part of a publication confirmation: {', '.join(unknown)}.", {"fields": unknown})
	return values


def _date(value: Any):
	text = cstr(value).strip()
	if not text:
		return None
	try:
		return getdate(text)
	except Exception:
		return False


def _approval_date(snapshot):
	return getdate(snapshot.approved_at) if snapshot and snapshot.approved_at else None


def _clean(values: dict[str, Any], *, complete: bool, snapshot=None, carried_attachment: str = "") -> tuple[dict[str, Any], dict[str, str]]:
	"""The evidence as it will be stored, and what is wrong with it. A Draft
	checks only the values it is given; a confirmation also needs every
	required one (§5.5.2.2)."""
	clean: dict[str, Any] = {}
	errors: dict[str, str] = {}
	today = getdate(nowdate())

	for field in ("treasury_submitted_on", "website_published_on"):
		parsed = _date(values.get(field))
		if parsed is False:
			errors[field] = "Enter a valid date."
		elif parsed is None:
			if complete:
				errors[field] = "Enter the date."
		elif complete and parsed > today:
			errors[field] = "A date in the future cannot be confirmed."
		else:
			clean[field] = parsed
	# These rules decide what can be *confirmed*. A Draft is unfinished work and keeps whatever was
	# typed (found live 9 Oct 2026: a Draft refused for an address without http:// lost every field).
	approved_on = _approval_date(snapshot)
	if complete and "treasury_submitted_on" in clean and approved_on and clean["treasury_submitted_on"] < approved_on:
		errors["treasury_submitted_on"] = f"The plan was approved on {approved_on}. It cannot have been submitted before then."
	if complete and "treasury_submitted_on" in clean and "website_published_on" in clean and clean["website_published_on"] < clean["treasury_submitted_on"]:
		errors["website_published_on"] = "The website publication date cannot be before the Treasury submission date."

	reference = " ".join(cstr(values.get("treasury_reference")).split())
	if len(reference) > 140:
		errors["treasury_reference"] = "Use 140 characters or fewer."
	else:
		clean["treasury_reference"] = reference

	url = cstr(values.get("public_plan_url")).strip()
	if url:
		parts = urlparse(url)
		if len(url) > 500:
			errors["public_plan_url"] = "Use 500 characters or fewer."
		elif complete and (parts.scheme not in ("http", "https") or not parts.netloc or " " in url):
			errors["public_plan_url"] = "Enter the address of the published plan, starting with http:// or https://."
		else:
			clean["public_plan_url"] = url
	elif complete:
		errors["public_plan_url"] = "Enter the address of the published plan."

	clean["treasury_attachment"] = cstr(values.get("treasury_attachment")).strip() or cstr(carried_attachment)
	if complete and not clean["treasury_reference"] and not clean["treasury_attachment"]:
		errors["treasury_reference"] = "Enter a submission reference or attach the submission evidence."

	acknowledged = values.get("confirmation_acknowledged") in _TRUE
	clean["confirmation_acknowledged"] = 1 if acknowledged else 0
	if complete and not acknowledged:
		errors["confirmation_acknowledged"] = "Tick the confirmation to continue."
	return clean, errors


#: What the Planner calls each field, so a refusal can name it.
FIELD_LABELS = {
	"treasury_submitted_on": "Treasury submission date",
	"treasury_reference": "Submission reference",
	"treasury_attachment": "Submission evidence",
	"website_published_on": "Entity website publication date",
	"public_plan_url": "Public plan URL",
	"confirmation_acknowledged": "Confirmation",
}


def _refuse_if_invalid(errors: dict[str, str]) -> None:
	"""Name what is wrong and where. The message lists only the fields that are
	wrong, each with its own problem; `detail.fields` carries the same by field
	so the page can mark them."""
	if errors:
		message = " ".join(f"{FIELD_LABELS.get(field, field)}: {problem}" for field, problem in errors.items())
		fail("PLN_TREASURY_EVIDENCE_REQUIRED", message, {"fields": errors})


def _resolve_file(value: str, *, actor: str, version) -> Any | None:
	"""A File the Planner uploaded (its name) or one already attached to this
	Version, never an arbitrary address. Returns the File row or None."""
	if not value:
		return None
	row = frappe.db.get_value(
		"File", value if frappe.db.exists("File", value) else {"file_url": value},
		["name", "owner", "file_name", "file_url", "attached_to_doctype", "attached_to_name", "file_size"], as_dict=True,
	)
	if not row:
		return False
	ours = (
		(not row.attached_to_doctype and row.owner == actor)
		or (row.attached_to_doctype == "Annual Plan Version" and row.attached_to_name == version.name)
		or (row.attached_to_doctype == DOCTYPE and frappe.db.get_value(DOCTYPE, row.attached_to_name, "plan_version") == version.name)
	)
	if not ours:
		return False
	extension = cstr(row.file_name).rsplit(".", 1)[-1].lower() if "." in cstr(row.file_name) else ""
	from kentender_core.services.file_integrity import MAX_FILE_SIZE_BYTES

	if extension not in _EVIDENCE_TYPES or int(row.file_size or 0) > MAX_FILE_SIZE_BYTES:
		return False
	return row


def _normalise_attachment(clean: dict[str, Any], errors: dict[str, str], *, actor: str, version, carried: str) -> Any | None:
	"""Replace the supplied File name with its URL; report an unusable file."""
	supplied = clean.get("treasury_attachment")
	if not supplied or supplied == carried:
		return None
	row = _resolve_file(supplied, actor=actor, version=version)
	if row is False:
		errors["treasury_attachment"] = "Attach the file again. Use a PDF, PNG or JPG of 20 MB or less."
		return None
	clean["treasury_attachment"] = row.file_url
	return row


def _attach(row, record_name: str) -> None:
	if row is None or row.attached_to_doctype:
		return
	file_doc = frappe.get_doc("File", row.name)
	file_doc.is_private = 1
	file_doc.attached_to_doctype = DOCTYPE
	file_doc.attached_to_name = record_name
	file_doc.save(ignore_permissions=True)


def _context(plan_version: str):
	"""The locked approved Version, its snapshot and its publication."""
	if not plan_version or not frappe.db.exists("Annual Plan Version", plan_version):
		authz.not_found()
	version = envelope.locked("Annual Plan Version", plan_version)
	snapshot = frappe.db.get_value("Approved Plan Snapshot", {"plan_version": version.name}, ["name", "content_digest", "approved_at"], as_dict=True)
	if not snapshot:
		fail("PLN_REVIEW_STALE", "Only an approved Plan Version takes a publication confirmation.")
	publication = frappe.db.get_value("Plan Publication", {"plan_version": version.name}, ["name", "package_hash"], as_dict=True)
	if not publication:
		fail("PLN_REVIEW_STALE", "Approval has not committed a publication yet.")
	return version, snapshot, publication


def current_confirmation(plan_version: str):
	return frappe.db.get_value(DOCTYPE, {"plan_version": plan_version, "confirmation_state": "Current"}, "name")


def draft_confirmation(plan_version: str):
	return frappe.db.get_value(DOCTYPE, {"plan_version": plan_version, "confirmation_state": "Draft"}, "name")


def _stamp(record, *, clean: dict[str, Any], snapshot, publication, version, actor: str, assignment, state: str, **extra) -> dict[str, Any]:
	return {
		**{field: clean.get(field) or None for field in ("treasury_submitted_on", "treasury_reference", "treasury_attachment", "website_published_on", "public_plan_url")},
		"confirmation_acknowledged": clean["confirmation_acknowledged"],
		"snapshot": snapshot.name, "publication": publication.name, "document_hash": snapshot.content_digest, "package_hash": publication.package_hash,
		"confirmation_state": state, "actor": actor, "authority_snapshot": authz.authority_snapshot(assignment), "recorded_at": now_datetime(),
		**extra,
	}


def _new_row(version, fixture_namespace: str, fields: dict[str, Any]):
	return frappe.get_doc(
		{"doctype": DOCTYPE, "plan_version": version.name, "record_version": 0, "fixture_namespace": fixture_namespace, **fields}
	).insert(ignore_permissions=True)


@planning_command
def save_publication_draft(*, plan_version: str, values: Any, expected_record_version=None, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `SavePublicationDraft` — keep incomplete evidence as the one Draft
	for the Version. It releases nothing, changes no state and is not evidence."""
	actor = authz.actor(user)
	values = _as_values(values)
	payload = {"plan_version": plan_version, "values": {k: cstr(v) for k, v in values.items()}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	version, snapshot, publication = _context(plan_version)
	if version.version_status not in OPEN_STATES:
		fail("PLN_REVIEW_STALE")
	draft_name = draft_confirmation(version.name)
	draft = envelope.locked(DOCTYPE, draft_name) if draft_name else None
	if draft:
		envelope.check_record_version(draft, expected_record_version)
	clean, errors = _clean(values, complete=False, snapshot=snapshot, carried_attachment=draft.treasury_attachment if draft else "")
	file_row = _normalise_attachment(clean, errors, actor=actor, version=version, carried=draft.treasury_attachment if draft else "")
	_refuse_if_invalid(errors)
	fields = _stamp(None, clean=clean, snapshot=snapshot, publication=publication, version=version, actor=actor, assignment=assignment, state="Draft")
	fields.pop("recorded_at")  # a Draft is not recorded evidence
	if draft:
		envelope.bump(draft, **fields)
	else:
		draft = _new_row(version, cstr(version.fixture_namespace), fields)
	_attach(file_row, draft.name)
	result = {"ok": True, "idempotent": False, "action": "publication_draft_saved", "confirmation": draft.name, "record_version": int(draft.record_version or 0)}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SavePublicationDraft", payload=payload, result=result,
		document_type=DOCTYPE, document_name=draft.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
	)
	return result


@planning_command
def confirm_plan_publication(*, plan_version: str, values: Any, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `ConfirmPlanPublication` — require the Planner, the exact approved
	Version in a confirmable state, no active hold and complete evidence; store
	the Current confirmation immutably; then invoke `ActivatePlanVersion` once.
	The evidence is preserved when activation is held."""
	actor = authz.actor(user)
	values = _as_values(values)
	payload = {"plan_version": plan_version, "values": {k: cstr(v) for k, v in values.items()}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	version, snapshot, publication = _context(plan_version)
	envelope.check_record_version(version, expected_record_version)
	if version.version_status not in OPEN_STATES or current_confirmation(version.name):
		fail("PLN_REVIEW_STALE")
	if publication_pipeline._active_hold(version.name):
		fail("PLN_PUBLICATION_HELD")
	draft_name = draft_confirmation(version.name)
	draft = envelope.locked(DOCTYPE, draft_name) if draft_name else None
	clean, errors = _clean(values, complete=True, snapshot=snapshot, carried_attachment=draft.treasury_attachment if draft else "")
	file_row = _normalise_attachment(clean, errors, actor=actor, version=version, carried=draft.treasury_attachment if draft else "")
	_refuse_if_invalid(errors)

	fields = _stamp(None, clean=clean, snapshot=snapshot, publication=publication, version=version, actor=actor, assignment=assignment, state="Current")
	if draft:
		envelope.bump(draft, **fields)
		record = draft
	else:
		record = _new_row(version, cstr(version.fixture_namespace), fields)
	_attach(file_row, record.name)
	frappe.db.set_value(
		"Plan Publication", publication.name, {"publication_state": "Confirmed", "public_location": clean["public_plan_url"]}, update_modified=False,
	)

	activation = publication_pipeline.activate_plan_version(plan_version=version.name, user=actor)
	version.reload()
	result = {
		"ok": True, "idempotent": False, "action": "publication_confirmed", "confirmation": record.name,
		"activation": cstr(activation.get("action")), "blockers": list(activation.get("blockers") or []), "version_status": version.version_status,
		"publication": publication.name,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ConfirmPlanPublication", payload=payload, result=result,
		document_type=DOCTYPE, document_name=record.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
	)
	return result


@planning_command
def correct_publication_details(*, confirmation: str, values: Any, reason: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `CorrectPublicationDetails` — append a superseding Current record
	with a reason; the earlier one is kept. It edits no approved content,
	deactivates no Active Version, runs no second activation and repeats no
	approval."""
	actor = authz.actor(user)
	values = _as_values(values)
	reason = " ".join(cstr(reason).split())
	payload = {"confirmation": confirmation, "values": {k: cstr(v) for k, v in values.items()}, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	if not (10 <= len(reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State the reason for the correction (10–500 characters).", {"field": "reason"})
	if not confirmation or not frappe.db.exists(DOCTYPE, confirmation):
		authz.not_found()
	prior = frappe.get_doc(DOCTYPE, confirmation)
	if prior.confirmation_state != "Current":
		fail("PLN_REVIEW_STALE", "Only the current record can be corrected.")
	version, snapshot, publication = _context(prior.plan_version)
	if version.version_status not in CORRECTABLE_STATES:
		fail("PLN_REVIEW_STALE")
	carried = {field: cstr(prior.get(field)) for field in FIELDS if field != "confirmation_acknowledged"}
	carried["treasury_submitted_on"] = cstr(prior.treasury_submitted_on)
	carried["website_published_on"] = cstr(prior.website_published_on)
	merged = {**carried, "confirmation_acknowledged": 1, **values}
	clean, errors = _clean(merged, complete=True, snapshot=snapshot, carried_attachment=prior.treasury_attachment)
	file_row = _normalise_attachment(clean, errors, actor=actor, version=version, carried=cstr(prior.treasury_attachment))
	_refuse_if_invalid(errors)
	fields = _stamp(None, clean=clean, snapshot=snapshot, publication=publication, version=version, actor=actor, assignment=assignment, state="Current", correction_reason=reason)
	corrected = _new_row(version, cstr(version.fixture_namespace), fields)
	_attach(file_row, corrected.name)
	frappe.db.set_value(DOCTYPE, prior.name, {"confirmation_state": "Superseded", "superseded_by": corrected.name}, update_modified=False)
	frappe.db.set_value("Plan Publication", publication.name, "public_location", clean["public_plan_url"], update_modified=False)
	result = {"ok": True, "idempotent": False, "action": "publication_details_corrected", "confirmation": corrected.name, "supersedes": prior.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="CorrectPublicationDetails", payload=payload, result=result,
		document_type=DOCTYPE, document_name=corrected.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
	)
	return result
