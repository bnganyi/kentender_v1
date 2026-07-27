# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Org-scoped idempotency with canonical request fingerprints."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_IDEMPOTENCY_RECORD,
)


def canonical_request_fingerprint(payload: dict[str, Any]) -> str:
	blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
	return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _cstr(value: Any) -> str:
	return "" if value is None else str(value)


def _lookup(*, organization: str, operation: str, idempotency_key: str) -> dict[str, Any] | None:
	return frappe.db.get_value(
		DT_IDEMPOTENCY_RECORD,
		{"organization": organization, "operation": operation, "idempotency_key": idempotency_key},
		["name", "request_fingerprint", "result_name", "result_doctype"],
		as_dict=True,
	)


def _assert_fingerprint(existing: dict[str, Any], request_fingerprint: str) -> None:
	if _cstr(existing.request_fingerprint) != _cstr(request_fingerprint):
		frappe.throw(
			_("Idempotency key reused with a different request fingerprint."),
			title="BWMF_IDEMPOTENCY_FINGERPRINT_MISMATCH",
		)


def resolve_idempotency(
	*,
	organization: str,
	operation: str,
	idempotency_key: str,
	request_fingerprint: str,
	result_doctype: str,
	create_result: Callable[[], str],
) -> str:
	"""Same key+fingerprint → original result; same key+different fingerprint → fail.

	Uses MySQL GET_LOCK so concurrent callers create one authoritative record.
	"""
	existing = _lookup(
		organization=organization, operation=operation, idempotency_key=idempotency_key
	)
	if existing:
		_assert_fingerprint(existing, request_fingerprint)
		return existing.result_name

	lock_name = f"bwmf_idem:{organization}:{operation}:{idempotency_key}"
	got = frappe.db.sql("select get_lock(%s, 30)", (lock_name,))
	if not got or int(got[0][0] or 0) != 1:
		frappe.throw(_("Could not acquire idempotency lock."), title="BWMF_IDEMPOTENCY_LOCK_TIMEOUT")
	try:
		existing = _lookup(
			organization=organization, operation=operation, idempotency_key=idempotency_key
		)
		if existing:
			_assert_fingerprint(existing, request_fingerprint)
			return existing.result_name

		result_name = create_result()
		rec = frappe.get_doc(
			{
				"doctype": DT_IDEMPOTENCY_RECORD,
				"organization": organization,
				"operation": operation,
				"idempotency_key": idempotency_key,
				"request_fingerprint": request_fingerprint,
				"result_doctype": result_doctype,
				"result_name": result_name,
				"created_at": now_datetime(),
			}
		)
		rec.insert(ignore_permissions=True)
		return result_name
	finally:
		frappe.db.sql("select release_lock(%s)", (lock_name,))
