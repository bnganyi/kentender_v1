# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-1000 — append-only publication audits on ``Audit Event``.

Metadata follows pack §18 shape: ``event_code`` (pack semantic), ``tender_code``,
``instance_code``, snapshot codes, ``actor``, nested ``details``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services.audit_event_service import log_audit_event

from kentender_procurement.tender_management.services.tm2_tender_resolve import resolve_tm2_tender_document
from kentender_procurement.tender_management.tender_publication.audit.codes import EVENT_TYPE_TO_PACK_EVENT_CODE


def _compact(meta: dict[str, Any]) -> dict[str, Any]:
	return {k: v for k, v in meta.items() if v is not None}


def emit_publication_audit_event(
	*,
	event_type: str,
	tender_code: str,
	action: str,
	performed_by: str | None = None,
	instance_code: str | None = None,
	configuration_snapshot_code: str | None = None,
	publication_snapshot_code: str | None = None,
	std_publication_snapshot_code: str | None = None,
	pack_event_code: str | None = None,
	details: dict[str, Any] | None = None,
	timestamp: datetime | None = None,
) -> str:
	"""Insert one ``Audit Event`` row; returns the new document name."""
	tc = (tender_code or "").strip()
	user = (performed_by or "").strip() or getattr(frappe.session, "user", None) or "Administrator"
	pec = pack_event_code or EVENT_TYPE_TO_PACK_EVENT_CODE.get(event_type) or event_type
	tm2 = resolve_tm2_tender_document(tc)
	if not tm2:
		frappe.throw(frappe._("TM2 Tender not found for audit event: {0}").format(tc))
	doc_type = "TM2 Tender"
	doc_name = tm2.name
	meta = _compact(
		{
			"event_code": pec,
			"tender_code": tc or None,
			"instance_code": (instance_code or "").strip() or None,
			"configuration_snapshot_code": (configuration_snapshot_code or "").strip() or None,
			"publication_snapshot_code": (publication_snapshot_code or "").strip() or None,
			"std_publication_snapshot_code": (std_publication_snapshot_code or "").strip() or None,
			"actor": user,
			"details": details if details else {},
		}
	)
	return log_audit_event(
		event_type=event_type,
		entity="TENDER_PUBLICATION",
		document_type=doc_type,
		document_name=doc_name,
		action=action,
		performed_by=user,
		timestamp=timestamp or now_datetime(),
		metadata=meta,
	)


class PublicationAuditService:
	"""Namespace for PUB-1000 helpers (``emit_publication_audit_event``)."""

	emit = staticmethod(emit_publication_audit_event)
