# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AuditEventService — SEC-0520.

Append-only façade for recording and querying ``Audit Event`` rows with the
SEC-0500 metadata contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe

from kentender_core.services.audit_event_service import log_audit_event
from kentender_procurement.tender_management.security.audit.metadata import (
	AuditEventResult,
	AuditRiskLevel,
	validate_audit_metadata,
)


def _norm_text(value: Any) -> str:
	return str(value or "").strip()


def _as_filters(raw: dict[str, Any] | None) -> dict[str, Any]:
	return dict(raw) if isinstance(raw, dict) else {}


def _event_row_payload(row: dict[str, Any]) -> dict[str, Any]:
	meta = row.get("metadata")
	if isinstance(meta, str):
		parsed = frappe.parse_json(meta)
		meta = parsed if isinstance(parsed, dict) else {}
	if not isinstance(meta, dict):
		meta = {}
	return {
		"name": row.get("name"),
		"event_type": row.get("event_type"),
		"entity": row.get("entity"),
		"document_type": row.get("document_type"),
		"document_name": row.get("document_name"),
		"action": row.get("action"),
		"performed_by": row.get("performed_by"),
		"timestamp": row.get("timestamp"),
		"metadata": meta,
	}


class AuditEventService:
	"""Pack §16 append-only service (`record*` + object/tender queries)."""

	@classmethod
	def record_success(cls, event_type: str, metadata: dict[str, Any]) -> str:
		meta = cls._prepare_metadata(event_type, metadata, result=AuditEventResult.SUCCESS, denial_code=None)
		return cls._insert_event(meta)

	@classmethod
	def record_denied(cls, event_type: str, denial_code: str, metadata: dict[str, Any]) -> str:
		meta = cls._prepare_metadata(event_type, metadata, result=AuditEventResult.DENIED, denial_code=denial_code)
		return cls._insert_event(meta)

	@classmethod
	def record_failed(cls, event_type: str, error_code: str, metadata: dict[str, Any]) -> str:
		meta = cls._prepare_metadata(event_type, metadata, result=AuditEventResult.FAILED, denial_code=error_code)
		return cls._insert_event(meta)

	@classmethod
	def get_audit_events_for_object(
		cls,
		object_type: str,
		object_code: str,
		filters: dict[str, Any] | None = None,
	) -> list[dict[str, Any]]:
		ot = _norm_text(object_type)
		oc = _norm_text(object_code)
		if not ot or not oc:
			return []
		opts = _as_filters(filters)
		limit = int(opts.get("limit") or 100)
		start = int(opts.get("start") or 0)
		rows = frappe.get_all(
			"Audit Event",
			filters={"document_type": ot, "document_name": oc},
			fields=[
				"name",
				"event_type",
				"entity",
				"document_type",
				"document_name",
				"action",
				"performed_by",
				"timestamp",
				"metadata",
			],
			order_by="timestamp desc",
			limit_start=start,
			limit=limit,
		)
		return [r for r in (cls._post_filter(_event_row_payload(x), opts) for x in rows) if r]

	@classmethod
	def get_audit_events_for_tender(
		cls,
		tender_code: str,
		filters: dict[str, Any] | None = None,
	) -> list[dict[str, Any]]:
		tc = _norm_text(tender_code)
		if not tc:
			return []
		opts = _as_filters(filters)
		limit = int(opts.get("limit") or 100)
		scan_limit = int(opts.get("scan_limit") or max(limit * 5, 500))
		rows = frappe.get_all(
			"Audit Event",
			fields=[
				"name",
				"event_type",
				"entity",
				"document_type",
				"document_name",
				"action",
				"performed_by",
				"timestamp",
				"metadata",
			],
			order_by="timestamp desc",
			limit=scan_limit,
		)
		out: list[dict[str, Any]] = []
		for row in rows:
			payload = _event_row_payload(row)
			meta = payload.get("metadata") or {}
			mtc = _norm_text(meta.get("tender_code"))
			if not mtc:
				if payload.get("document_type") == "Procurement Tender" and _norm_text(payload.get("document_name")) == tc:
					mtc = tc
			if mtc != tc:
				continue
			filtered = cls._post_filter(payload, opts)
			if filtered:
				out.append(filtered)
			if len(out) >= limit:
				break
		return out

	# Pack method aliases (camelCase)
	recordSuccess = record_success
	recordDenied = record_denied
	recordFailed = record_failed
	getAuditEventsForObject = get_audit_events_for_object
	getAuditEventsForTender = get_audit_events_for_tender

	@staticmethod
	def assert_append_only_operation(operation: str) -> None:
		op = _norm_text(operation).lower()
		if op in {"update", "delete", "truncate"}:
			raise frappe.PermissionError("AuditEventService is append-only; mutating operations are forbidden.")

	@classmethod
	def _prepare_metadata(
		cls,
		event_type: str,
		metadata: dict[str, Any] | None,
		*,
		result: AuditEventResult,
		denial_code: str | None,
	) -> dict[str, Any]:
		raw = dict(metadata or {})
		raw["event_type"] = _norm_text(event_type) or _norm_text(raw.get("event_type"))
		raw["audit_event_code"] = _norm_text(raw.get("audit_event_code")) or raw["event_type"]
		if denial_code:
			raw["denial_code"] = _norm_text(denial_code)
		if not _norm_text(raw.get("actor_user_code")):
			raw["actor_user_code"] = _norm_text(getattr(frappe.session, "user", None)) or "Administrator"
		if "timestamp" not in raw or not isinstance(raw.get("timestamp"), datetime):
			raw["timestamp"] = datetime.utcnow()
		if not _norm_text(raw.get("result")):
			raw["result"] = result.value
		if not _norm_text(raw.get("risk_level")):
			raw["risk_level"] = AuditRiskLevel.MEDIUM.value
		return validate_audit_metadata(raw)

	@staticmethod
	def _insert_event(meta: dict[str, Any]) -> str:
		doc_type = _norm_text(meta.get("object_type")) or "Audit Event Object"
		doc_name = _norm_text(meta.get("object_code")) or _norm_text(meta.get("tender_code")) or "UNKNOWN"
		action = _norm_text(meta.get("action_code")) or _norm_text(meta.get("result")).lower() or "audit_event"
		entity = doc_type.upper().replace(" ", "_")
		safe_meta = frappe.parse_json(frappe.as_json(meta))
		performed_by = _norm_text(meta.get("actor_user_code"))
		if performed_by and not frappe.db.exists("User", performed_by):
			performed_by = _norm_text(getattr(frappe.session, "user", None)) or "Administrator"
		return log_audit_event(
			event_type=_norm_text(meta.get("event_type")),
			entity=entity,
			document_type=doc_type,
			document_name=doc_name,
			action=action,
			performed_by=performed_by or None,
			timestamp=meta.get("timestamp"),
			metadata=safe_meta if isinstance(safe_meta, dict) else {},
		)

	@classmethod
	def _post_filter(cls, payload: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any] | None:
		meta = payload.get("metadata") or {}
		ev = _norm_text(filters.get("event_type"))
		res = _norm_text(filters.get("result"))
		rl = _norm_text(filters.get("risk_level"))
		df = filters.get("timestamp_from")
		dt = filters.get("timestamp_to")
		if ev and _norm_text(payload.get("event_type")) != ev:
			return None
		if res and _norm_text(meta.get("result")) != res:
			return None
		if rl and _norm_text(meta.get("risk_level")) != rl:
			return None
		ts = payload.get("timestamp")
		if isinstance(df, datetime) and isinstance(ts, datetime) and ts < df:
			return None
		if isinstance(dt, datetime) and isinstance(ts, datetime) and ts > dt:
			return None
		return payload
