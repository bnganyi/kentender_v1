# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.6 / §5.5 / §7.3 — publication authorisation,
withdrawal and the internal publication confirmation.

`AuthoriseTenderPublication` is the Accounting Officer's one decision on
the approved immutable Version: it rechecks authority, segregation from the
Version's own audit columns, compatibility, the current rule and the
minimum-period feasibility, then commits the decision, the rule snapshot
and one Evidence-based confirmation record per required channel — it does
not publish the Tender, call an assumed external interface or make
documents public (§5.5(2), TPR08-AC-041..044). `ConfirmTenderPublished`
runs internally when the final channel is confirmed: `published_at` is the
latest actual availability time among the confirmations (§4.6), the
minimum period is revalidated from it (§5.5(6)), and Planning receives the
invitation actual exactly once (§5.5(7)). Withdrawal is possible only while
no channel is confirmed (AC-055)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

from kentender_procurement.tenders.services import channel_confirmation, clock, compatibility, configuration_gateway, digest, draft_commands, envelope, events, lifecycle, planning_gateway, review, serializer
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import ROLE_ACCOUNTING_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION

TASK_HOPF_CONFIRMATION = "HOPF channel confirmation"
STATUS_EVIDENCE_REQUIRED = "Evidence required"
STATUS_PUBLISHED = "Published"
STATUS_WITHDRAWN = "Withdrawn before confirmation"


def minimum_period_ok(*, published_at, submission_deadline, minimum_days: int) -> bool:
	return getdate(submission_deadline) >= getdate(published_at) + timedelta(days=int(minimum_days))


# --------------------------------------------------------------------------
# AuthoriseTenderPublication
# --------------------------------------------------------------------------


def authorise_tender_publication(*, tender: str, expected_record_version, idempotency_key: str, user: str | None = None, task: str = "", task_token: str = "") -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_ao(actor)
	payload = {"tender": tender}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if version.status != "Approved" or root.overall_status != "Approved" or root.publication:
		fail("TND_STALE_VERSION", "This Tender is not awaiting publication authorisation.")
	lifecycle.require_segregation(version, actor, blocked_columns=("prepared_by", "submitted_by", "approved_by"))
	ao_task = lifecycle.open_task(root, task_type=lifecycle.TASK_AO_AUTHORISATION)
	if task and ao_task and ao_task.name != task:
		fail("TND_STALE_VERSION", "This task has already changed. Reload to see the current decision.")
	if task_token and ao_task:
		envelope.assert_task_token(ao_task, task_token)
	snapshot = snap.load(version)
	compatibility.require_supported(snapshot)
	check = review.run(root, version, with_renders=False)
	if check["must_fix_count"]:
		fail("TND_MUST_FIX", detail={"findings": [f for f in check["findings"] if f["severity"] == review.MUST_FIX]})
	state = serializer.officer_state(version)
	if serializer.package_digest(root, version, snapshot) != cstr(version.package_digest):
		fail("TND_STALE_VERSION", "The approved package no longer matches its digest.")
	rule = configuration_gateway.resolve_publication_rule(applicability_date=state.get("issue_date") or clock.today(), procurement_category=cstr(snapshot.get("procurement_category")) or "Goods")
	# Feasibility: the earliest the Tender could be published is now; the deadline must still allow the minimum period.
	if not minimum_period_ok(published_at=max(getdate(state.get("issue_date")), clock.today()) if state.get("issue_date") else clock.today(), submission_deadline=state.get("submission_deadline"), minimum_days=rule["minimum_preparation_days"]):
		fail("TND_PUBLICATION_PERIOD_INVALID", detail={"minimum_preparation_days": rule["minimum_preparation_days"], "submission_deadline": cstr(state.get("submission_deadline"))})
	with envelope.atomic("authorise-publication"):
		publication = envelope.insert(
			frappe.get_doc(
				{
					"doctype": "Tender Publication", "tender": root.name, "tender_version": version.name, "package_digest": version.package_digest, "authorised_by": actor, "authorised_at": clock.now(),
					"rule_snapshot_id": rule["rule_snapshot_id"], "rule_snapshot_json": configuration_gateway.snapshot_json(rule), "threshold_snapshot_json": configuration_gateway.snapshot_json(rule["threshold_snapshot"]),
					"required_channels_json": configuration_gateway.snapshot_json([{"channel": c["channel"], "label": c["label"], "confirmation_mode": c["confirmation_mode"], "public_url_expected": c["public_url_expected"]} for c in rule["channels"]]),
					"minimum_preparation_days": rule["minimum_preparation_days"], "publication_status": STATUS_EVIDENCE_REQUIRED, "record_version": 0, "fixture_namespace": root.fixture_namespace,
				}
			)
		)
		rows = channel_confirmation.create_rows(root=root, publication_name=publication.name, subject_type=channel_confirmation.SUBJECT_PUBLICATION, subject_id=publication.name, subject_digest=cstr(version.package_digest), channels=rule["channels"])
		decision = lifecycle.record_decision(root, version, decision="Authorise publication", actor=actor, business_role=ROLE_ACCOUNTING_OFFICER, assignment=assignment, idempotency_key=idempotency_key, subject_type="Tender Publication", subject_id=publication.name)
		if ao_task:
			lifecycle.complete_task(ao_task, decision.name)
		confirmation_task = lifecycle.new_task(root, version, task_type=TASK_HOPF_CONFIRMATION, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, subject_type="Tender Publication", subject_id=publication.name)
		envelope.bump(root, overall_status="Publication authorised", publication=publication.name, submission_deadline=state.get("submission_deadline"), clarification_deadline=state.get("clarification_deadline"))
		events.emit(
			tender=root.name, event_type="PublicationAuthorised", command="AuthoriseTenderPublication", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Approved", resulting_status="Publication authorised", record_version=root.record_version, subject_type="Tender Publication", subject_id=publication.name,
			payload={"package_digest": version.package_digest, "rule_snapshot_id": rule["rule_snapshot_id"], "contributing_versions": rule["contributing_versions"], "required_channels": [c["channel"] for c in rule["channels"]], "minimum_preparation_days": rule["minimum_preparation_days"], "confirmations": [r.name for r in rows], "decision": decision.name, "task": confirmation_task.name, "external_call": None},
			fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "publication_authorised", "tender": root.name, "record_version": root.record_version, "publication": publication.name, "required_channels": [c["channel"] for c in rule["channels"]], "confirmations": [r.name for r in rows], "task": confirmation_task.name}
	envelope.record_command(idempotency_key=idempotency_key, command="AuthoriseTenderPublication", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out


# --------------------------------------------------------------------------
# ConfirmPublicationChannel + ConfirmTenderPublished
# --------------------------------------------------------------------------


def confirm_publication_channel(*, tender: str, channel: str, available_at, evidence_reference: str, evidence_file: str, package_digest: str, expected_record_version, idempotency_key: str, public_url: str = "", url_not_applicable_reason: str = "", evidence_notes: str = "", attestation_confirmed: bool = False, user: str | None = None) -> dict[str, Any]:
	name = draft_commands.resolve_tender_name(tender)
	publication = cstr(frappe.db.get_value("Tender", name, "publication"))
	if not publication:
		fail("TND_STALE_VERSION", "Publication has not been authorised for this Tender.")
	return channel_confirmation.confirm_channel(
		subject_type=channel_confirmation.SUBJECT_PUBLICATION, subject_id=publication, channel=channel, available_at=available_at, evidence_reference=evidence_reference, public_url=public_url,
		url_not_applicable_reason=url_not_applicable_reason, evidence_file=evidence_file, evidence_notes=evidence_notes, attestation_confirmed=attestation_confirmed, package_digest=package_digest,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, on_all_confirmed=confirm_tender_published, command="ConfirmPublicationChannel",
	)


def confirm_tender_published(root, rows, *, actor: str, assignment, idempotency_key: str) -> dict[str, Any]:
	"""Internal (§7.3 `ConfirmTenderPublished`): runs inside the final
	channel confirmation's transaction under the Publication row lock so two
	concurrent final confirmations produce one authoritative result."""
	publication = envelope.locked("Tender Publication", root.publication)
	if publication.publication_status == STATUS_PUBLISHED:
		return {"ok": True, "idempotent": True, "published_at": cstr(publication.published_at)}
	for row in rows:
		if cstr(row.subject_digest) != cstr(publication.package_digest):
			fail("TND_PUBLICATION_DIGEST_MISMATCH", detail={"channel": row.channel})
	published_at = channel_confirmation.latest_available_at(channel_confirmation.SUBJECT_PUBLICATION, publication.name)
	if published_at is None:
		fail("TND_PUBLICATION_CONFIRMATION_INCOMPLETE")
	version = frappe.get_doc("Tender Version", publication.tender_version)
	state = serializer.officer_state(version)
	if not minimum_period_ok(published_at=published_at, submission_deadline=state.get("submission_deadline"), minimum_days=int(publication.minimum_preparation_days or 0)):
		# §5.5(6): the Tender cannot become Published until a lawful revised deadline is issued in the same package.
		fail("TND_PUBLICATION_PERIOD_INVALID", detail={"published_at": cstr(published_at), "submission_deadline": cstr(state.get("submission_deadline")), "minimum_preparation_days": int(publication.minimum_preparation_days or 0)})
	publication_digest = digest.sha256_hex({"decision": {"authorised_by": publication.authorised_by, "authorised_at": cstr(publication.authorised_at)}, "package_digest": publication.package_digest, "rule_snapshot_id": publication.rule_snapshot_id, "channels": channel_confirmation.confirmation_digest(channel_confirmation.SUBJECT_PUBLICATION, publication.name), "published_at": cstr(published_at)})
	envelope.bump(publication, publication_status=STATUS_PUBLISHED, published_at=published_at, publication_digest=publication_digest)
	envelope.bump(root, overall_status="Published — open", published_at=published_at, submission_deadline=state.get("submission_deadline"))
	task = lifecycle.open_task(root, task_type=TASK_HOPF_CONFIRMATION, subject_id=publication.name)
	if task:
		envelope.bump(task, status="Completed")
	events.emit(
		tender=root.name, event_type="TenderPublishedOpen", command="ConfirmTenderPublished", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
		previous_status="Publication authorised", resulting_status="Published — open", record_version=root.record_version, subject_type="Tender Publication", subject_id=publication.name,
		payload={"published_at": cstr(published_at), "publication_digest": publication_digest, "package_digest": publication.package_digest, "submission_deadline": cstr(state.get("submission_deadline"))},
		fixture_namespace=root.fixture_namespace,
	)
	planning = planning_gateway.publish_invitation_actual(root=root, publication=publication, published_at=published_at, actor=actor, idempotency_key=idempotency_key)
	if not events.exists(tender=root.name, event_type="TenderOpenForSubmission"):
		# Bidder-facing open-Tender event (§7.3): an outbox contract; no consumer exists in MVP (FOLLOW_UPS FU-12/13).
		events.emit(
			tender=root.name, event_type="TenderOpenForSubmission", command="ConfirmTenderPublished", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Publication authorised", resulting_status="Published — open", record_version=root.record_version, subject_type="Tender Publication", subject_id=publication.name,
			status="Pending", consumer="bidder-service", payload={"tender_reference": root.tender_reference, "published_at": cstr(published_at), "submission_deadline": cstr(state.get("submission_deadline")), "package_digest": publication.package_digest, "invitation_digest": version.invitation_digest, "issued_tender_digest": version.issued_tender_digest},
			fixture_namespace=root.fixture_namespace,
		)
	return {"ok": True, "idempotent": False, "published_at": cstr(published_at), "publication_digest": publication_digest, "planning": planning}


# --------------------------------------------------------------------------
# WithdrawPublicationAuthorisation
# --------------------------------------------------------------------------


def withdraw_publication_authorisation(*, tender: str, reason: str, evidence: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_ao(actor)
	payload = {"tender": tender, "reason": reason, "evidence": evidence}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = " ".join(cstr(reason).split())
	evidence = " ".join(cstr(evidence).split())
	if not (20 <= len(reason) <= 1000):
		fail("TND_CONTROL_INVALID", "A reason of 20–1,000 characters is required.", {"fields": {"reason": "Enter a reason of 20–1,000 characters."}})
	if not (10 <= len(evidence) <= 1000):
		fail("TND_CONTROL_INVALID", "State the accountable evidence that publication did not occur.", {"fields": {"evidence": "Enter the evidence (10–1,000 characters)."}})
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status != "Publication authorised" or not root.publication:
		fail("TND_STALE_VERSION", "This publication authorisation cannot be withdrawn in the current state.")
	publication = envelope.locked("Tender Publication", root.publication)
	if frappe.db.exists(channel_confirmation.DOCTYPE, {"subject_type": channel_confirmation.SUBJECT_PUBLICATION, "subject_id": publication.name, "status": "Confirmed"}):
		fail("TND_PUBLICATION_WITHDRAWAL_BLOCKED")
	with envelope.atomic("withdraw"):
		envelope.bump(publication, publication_status=STATUS_WITHDRAWN, withdrawn_by=actor, withdrawn_at=clock.now(), withdrawal_reason=reason, withdrawal_evidence=evidence)
		decision = lifecycle.record_decision(root, version, decision="Withdraw publication authorisation", actor=actor, business_role=ROLE_ACCOUNTING_OFFICER, assignment=assignment, idempotency_key=idempotency_key, reason=reason, subject_type="Tender Publication", subject_id=publication.name)
		lifecycle.cancel_open_tasks(root, task_types=(TASK_HOPF_CONFIRMATION,))
		ao_task = lifecycle.new_task(root, version, task_type=lifecycle.TASK_AO_AUTHORISATION, business_role=ROLE_ACCOUNTING_OFFICER)
		envelope.bump(root, overall_status="Approved", publication=None)
		events.emit(
			tender=root.name, event_type="PublicationAuthorisationWithdrawn", command="WithdrawPublicationAuthorisation", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Publication authorised", resulting_status="Approved", record_version=root.record_version, subject_type="Tender Publication", subject_id=publication.name, reason=reason,
			payload={"evidence": evidence, "decision": decision.name, "task": ao_task.name}, fixture_namespace=root.fixture_namespace,
		)
	out = {"ok": True, "idempotent": False, "action": "withdrawn", "tender": root.name, "record_version": root.record_version, "publication": publication.name}
	envelope.record_command(idempotency_key=idempotency_key, command="WithdrawPublicationAuthorisation", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out


# --------------------------------------------------------------------------
# GetTenderPublication
# --------------------------------------------------------------------------


def get_tender_publication(*, tender: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.tenders.services import publication_read, read

	actor = authz.actor(user)
	root = frappe.get_doc("Tender", draft_commands.resolve_tender_name(tender))
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	if mode == "department":
		authz.not_found()
	roles = read.actor_roles(actor)
	version = frappe.get_doc("Tender Version", root.approved_version or root.current_version)
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	summary = publication_read.publication_summary(root, actor=actor, roles=roles)
	ao_task = lifecycle.open_task(root, task_type=lifecycle.TASK_AO_AUTHORISATION)
	try:
		rule = configuration_gateway.resolve_publication_rule(applicability_date=state.get("issue_date") or clock.today(), procurement_category=cstr(snapshot.get("procurement_category")) or "Goods") if root.overall_status == "Approved" else None
		rule_error = ""
	except Exception as exc:
		rule, rule_error = None, cstr(getattr(exc, "code", "") or str(exc))
	tendering_days = (getdate(state.get("submission_deadline")) - getdate(state.get("issue_date"))).days if state.get("submission_deadline") and state.get("issue_date") else None
	return {
		"outcome": "OK", "mode": mode, "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "overall_status": cstr(root.overall_status), "badge": read.badge_for(root, version, roles), "record_version": int(root.record_version or 0), "published_at_label": serializer.fmt_datetime_short(root.published_at) if root.published_at else "", "submission_deadline_label": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else ""},
		"version": read.version_summary(version),
		"approval_trail": {"prepared_by_name": read.version_summary(version)["prepared_by_name"], "approved_by_name": read.version_summary(version)["approved_by_name"], "approved_at_label": read.version_summary(version)["approved_at_label"], "version_number": int(version.version_number), "package_digest": cstr(version.package_digest)},
		"review": review.summary(version),
		"key_facts": read.key_facts(root, version, snapshot, internal=True) + [{"label": "Tendering period", "value": f"{tendering_days} days" if tendering_days is not None else ""}],
		"documents": read.documents_for(root, version),
		"sections": read.review_sections(root, version, snapshot, review.summary(version), internal=True),
		"proposed_channels": [{"channel": c["channel"], "label": c["label"], "how": "HOPF confirmation with evidence", "result": "Not started"} for c in (rule or {}).get("channels", [])],
		"rule": {"rule_snapshot_id": rule["rule_snapshot_id"], "minimum_preparation_days": rule["minimum_preparation_days"], "contributing_versions": rule["contributing_versions"]} if rule else None,
		"rule_error": rule_error,
		"publication": summary,
		"ao_task": {"name": ao_task.name, "task_token": ao_task.task_token} if ao_task else None,
		"attestations": {c["channel"]: channel_confirmation.attestation_text(subject_type=channel_confirmation.SUBJECT_PUBLICATION, channel_label=c["label"]) for c in ((summary or {}).get("required_channels") or [])},
		"allowed_actions": read.allowed_actions(root, version, actor, roles),
		"segregation_message": read.segregation_message(root, version, actor, roles),
	}
