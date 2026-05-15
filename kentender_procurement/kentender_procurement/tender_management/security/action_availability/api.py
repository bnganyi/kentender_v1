# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelist handlers for action availability — SEC-0410."""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe import _

from kentender_procurement.tender_management.security.action_availability.service import (
	ActionAvailabilityService,
)

SEC_API_INTERNAL_ERROR = "SEC_API_INTERNAL_ERROR"
SEC_API_PAYLOAD_INVALID = "SEC_API_PAYLOAD_INVALID"
SEC_API_ACTION_CODE_REQUIRED = "SEC_API_ACTION_CODE_REQUIRED"
SEC_API_OBJECT_TYPE_REQUIRED = "SEC_API_OBJECT_TYPE_REQUIRED"
SEC_API_OBJECT_CODE_REQUIRED = "SEC_API_OBJECT_CODE_REQUIRED"
SEC_API_ITEMS_REQUIRED = "SEC_API_ITEMS_REQUIRED"

_KNOWN_VALIDATION_CODES: frozenset[str] = frozenset(
	{
		SEC_API_PAYLOAD_INVALID,
		SEC_API_ACTION_CODE_REQUIRED,
		SEC_API_OBJECT_TYPE_REQUIRED,
		SEC_API_OBJECT_CODE_REQUIRED,
		SEC_API_ITEMS_REQUIRED,
	}
)


def _api_fail(error_code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
	return {
		"success": False,
		"error_code": str(error_code),
		"message": str(message),
		"details": dict(details or {}),
	}


def _api_ok(**payload: Any) -> dict[str, Any]:
	out: dict[str, Any] = {"success": True}
	out.update(payload)
	return out


def _wrap(handler_id: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	frappe.clear_messages()
	try:
		return fn()
	except frappe.ValidationError as exc:
		code = _stable_title_from_message_log()
		if code not in _KNOWN_VALIDATION_CODES:
			code = SEC_API_PAYLOAD_INVALID
		return _api_fail(code, str(exc), details={})
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"SEC-0410 {handler_id}")
		return _api_fail(SEC_API_INTERNAL_ERROR, _("Unexpected server error."), details={})


def _stable_title_from_message_log() -> str | None:
	log = frappe.get_message_log()
	if not log:
		return None
	return str(log[-1].get("title") or "").strip() or None


def _as_payload_dict(raw: Any, *, field: str) -> dict[str, Any]:
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return dict(raw)
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return {}
		try:
			parsed = json.loads(s)
		except json.JSONDecodeError:
			frappe.throw(
				_(f"{field} must be valid JSON."),
				title=SEC_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		if not isinstance(parsed, dict):
			frappe.throw(
				_(f"{field} must be a JSON object."),
				title=SEC_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		return dict(parsed)
	frappe.throw(
		_(f"{field} must be a dict or JSON object."),
		title=SEC_API_PAYLOAD_INVALID,
		exc=frappe.ValidationError,
	)


def _as_items(raw: Any) -> list[dict[str, Any]]:
	if raw is None:
		return []
	if isinstance(raw, list):
		out: list[dict[str, Any]] = []
		for idx, item in enumerate(raw):
			if not isinstance(item, dict):
				frappe.throw(
					_(f"items[{idx}] must be a JSON object."),
					title=SEC_API_PAYLOAD_INVALID,
					exc=frappe.ValidationError,
				)
			out.append(dict(item))
		return out
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return []
		try:
			parsed = json.loads(s)
		except json.JSONDecodeError:
			frappe.throw(
				_("items must be valid JSON."),
				title=SEC_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		if not isinstance(parsed, list):
			frappe.throw(
				_("items must be a JSON array."),
				title=SEC_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		return _as_items(parsed)
	frappe.throw(
		_("items must be a list or JSON array."),
		title=SEC_API_PAYLOAD_INVALID,
		exc=frappe.ValidationError,
	)


def _required_text(value: Any, *, code: str, field: str) -> str:
	txt = str(value or "").strip()
	if txt:
		return txt
	frappe.throw(
		_(f"{field} is required."),
		title=code,
		exc=frappe.ValidationError,
	)


def _resolve_actor(explicit_actor: str | None) -> str:
	explicit = str(explicit_actor or "").strip()
	if explicit:
		return explicit
	return str(frappe.session.user or "").strip()


@frappe.whitelist()
def sec_api_action_availability(
	action_code: str,
	object_type: str,
	object_code: str,
	context: dict[str, Any] | str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""POST ``/api/security/action-availability`` (frappe.call handler)."""

	def _run() -> dict[str, Any]:
		ac = _required_text(action_code, code=SEC_API_ACTION_CODE_REQUIRED, field="action_code")
		ot = _required_text(object_type, code=SEC_API_OBJECT_TYPE_REQUIRED, field="object_type")
		oc = _required_text(object_code, code=SEC_API_OBJECT_CODE_REQUIRED, field="object_code")
		ctx = _as_payload_dict(context, field="context")
		actor_user = _resolve_actor(actor)
		availability = ActionAvailabilityService.get_action_availability(actor_user, ac, ot, oc, context=ctx)
		return _api_ok(actor_user_code=actor_user, **availability)

	return _wrap("action_availability_single", _run)


@frappe.whitelist()
def sec_api_action_availability_batch(
	items: list[dict[str, Any]] | str,
	context: dict[str, Any] | str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""POST ``/api/security/action-availability/batch`` (frappe.call handler)."""

	def _run() -> dict[str, Any]:
		base_ctx = _as_payload_dict(context, field="context")
		rows = _as_items(items)
		if not rows:
			frappe.throw(
				_("items is required and must contain at least one request object."),
				title=SEC_API_ITEMS_REQUIRED,
				exc=frappe.ValidationError,
			)
		actor_user = _resolve_actor(actor)
		out_rows: list[dict[str, Any]] = []
		for idx, row in enumerate(rows):
			ac = _required_text(row.get("action_code"), code=SEC_API_ACTION_CODE_REQUIRED, field=f"items[{idx}].action_code")
			ot = _required_text(row.get("object_type"), code=SEC_API_OBJECT_TYPE_REQUIRED, field=f"items[{idx}].object_type")
			oc = _required_text(row.get("object_code"), code=SEC_API_OBJECT_CODE_REQUIRED, field=f"items[{idx}].object_code")
			row_ctx = _as_payload_dict(row.get("context"), field=f"items[{idx}].context")
			merged_ctx = dict(base_ctx)
			merged_ctx.update(row_ctx)
			availability = ActionAvailabilityService.get_action_availability(actor_user, ac, ot, oc, context=merged_ctx)
			out_rows.append(availability)
		return _api_ok(actor_user_code=actor_user, items=out_rows)

	return _wrap("action_availability_batch", _run)
