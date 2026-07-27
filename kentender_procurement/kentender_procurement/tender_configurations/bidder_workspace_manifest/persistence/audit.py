# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Append-only BWMF Audit Event emitter."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_AUDIT_EVENT,
)


def _event_digest(payload: dict[str, Any]) -> str:
	blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
	return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def append_audit_event(
	*,
	event_type: str,
	organization: str,
	actor: str | None = None,
	bidder_party: str | None = None,
	workspace: str | None = None,
	manifest_doc: str | None = None,
	response_ref: str | None = None,
	evidence_ref: str | None = None,
	confirmation_ref: str | None = None,
	submission_ref: str | None = None,
	compile_run_ref: str | None = None,
	correlation_ref: str | None = None,
	idempotency_ref: str | None = None,
	metadata: dict[str, Any] | None = None,
) -> str:
	event_at = now_datetime()
	actor = actor or frappe.session.user or "system"
	event_id = f"AUD-{frappe.generate_hash(length=12).upper()}"
	safe_meta = metadata or {}
	digest_material = {
		"event_id": event_id,
		"event_type": event_type,
		"organization": organization,
		"bidder_party": bidder_party,
		"workspace": workspace,
		"actor": actor,
		"event_at": str(event_at),
		"manifest_doc": manifest_doc,
		"response_ref": response_ref,
		"evidence_ref": evidence_ref,
		"confirmation_ref": confirmation_ref,
		"submission_ref": submission_ref,
		"compile_run_ref": compile_run_ref,
		"correlation_ref": correlation_ref,
		"idempotency_ref": idempotency_ref,
		"metadata": safe_meta,
	}
	doc = frappe.get_doc(
		{
			"doctype": DT_AUDIT_EVENT,
			"event_id": event_id,
			"event_type": event_type,
			"organization": organization,
			"bidder_party": bidder_party,
			"workspace": workspace,
			"actor": actor,
			"event_at": event_at,
			"manifest_doc": manifest_doc,
			"response_ref": response_ref,
			"evidence_ref": evidence_ref,
			"confirmation_ref": confirmation_ref,
			"submission_ref": submission_ref,
			"compile_run_ref": compile_run_ref,
			"correlation_ref": correlation_ref,
			"idempotency_ref": idempotency_ref,
			"metadata_json": json.dumps(safe_meta),
			"event_digest": _event_digest(digest_material),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
