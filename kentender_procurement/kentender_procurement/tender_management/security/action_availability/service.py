# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ActionAvailabilityService — SEC-0400 / doc 9 §7.

Read-only backend source of truth for action availability used by UI and
enforceable workflows. Delegates authorization to
``AuthorizationDecisionEngine.evaluate`` and reshapes the result to **doc 9 §7.3**
(plus legacy SEC keys for existing callers).

Pack-ordered entrypoint: ``get_action_availability(action_code, object_type,
object_code, actor, context=None)`` (§7.2).

Exit gate (doc 9 §25 **EX-15**, partial): ``tender_management.tests.test_ex_15_action_availability_controls_legal_services``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

from kentender_procurement.tender_management.security.authorization.decision_engine import (
	AuthorizationDecisionEngine,
)

# Doc 9 §7.3 — required top-level keys (always present on service responses).
PACK_ACTION_AVAILABILITY_V73_KEYS: tuple[str, ...] = (
	"action_code",
	"object_type",
	"object_code",
	"allowed",
	"denial_code",
	"risk_level",
	"required_permission",
	"user_message",
	"blockers",
	"confirmation_required",
	"reason_required",
)

PACK_ACTION_AVAILABILITY_BLOCKER_KEYS: frozenset[str] = frozenset(
	{"blocker_code", "severity", "owner_module", "required_action"}
)


class ActionAvailabilityResponse(TypedDict, total=False):
	"""§7.3 fields plus legacy SEC keys (``message``, ``requires_confirmation``, …)."""

	action_code: str
	object_type: str
	object_code: str
	allowed: bool
	denial_code: str
	risk_level: str
	required_permission: str
	user_message: str
	blockers: list[dict[str, str]]
	confirmation_required: bool
	reason_required: bool
	# Legacy / SEC compatibility (still emitted for gradual migration)
	message: str
	requires_confirmation: bool
	audit_on_attempt: bool
	object_state: str


def pack_action_availability_v73_errors(response: Mapping[str, Any]) -> list[str]:
	"""Return human-readable validation errors for a §7.3-shaped dict (unit tests)."""
	errs: list[str] = []
	for key in PACK_ACTION_AVAILABILITY_V73_KEYS:
		if key not in response:
			errs.append(f"missing_top_level:{key}")
	blockers = response.get("blockers")
	if not isinstance(blockers, list):
		errs.append("blockers_not_list")
	else:
		for idx, item in enumerate(blockers):
			if not isinstance(item, dict):
				errs.append(f"blocker[{idx}]_not_dict")
				continue
			missing = sorted(PACK_ACTION_AVAILABILITY_BLOCKER_KEYS - set(item.keys()))
			if missing:
				errs.append(f"blocker[{idx}]_missing:{','.join(missing)}")
			for bk in PACK_ACTION_AVAILABILITY_BLOCKER_KEYS:
				if bk in item and not isinstance(item[bk], str):
					errs.append(f"blocker[{idx}]_{bk}_not_str")
	return errs


def _normalize_context_blockers(raw: Any) -> list[dict[str, str]]:
	out: list[dict[str, str]] = []
	if not isinstance(raw, list):
		return out
	for item in raw:
		if not isinstance(item, dict):
			continue
		row = {k: str(item.get(k) or "").strip() for k in PACK_ACTION_AVAILABILITY_BLOCKER_KEYS}
		if all(row.values()):
			out.append(row)
	return out


def _synthetic_blocker(
	ctx: dict[str, Any],
	*,
	denial_code: str,
	risk_level: str,
	user_message: str,
) -> dict[str, str]:
	code = str(denial_code or "").strip() or "UNKNOWN"
	sev = str(risk_level or "").strip() or "Medium"
	owner = str(ctx.get("blocker_owner_module") or "Tender Management").strip() or "Tender Management"
	req = str(ctx.get("blocker_required_action") or "").strip()
	if not req:
		req = str(user_message or "").strip() or "Resolve blockers before retrying."
	return {
		"blocker_code": code,
		"severity": sev,
		"owner_module": owner,
		"required_action": req,
	}


def _build_blockers(
	ctx: dict[str, Any],
	*,
	allowed: bool,
	denial_code: str,
	risk_level: str,
	user_message: str,
) -> list[dict[str, str]]:
	if allowed:
		return []
	normalized = _normalize_context_blockers(ctx.get("availability_blockers"))
	if normalized:
		return normalized
	return [_synthetic_blocker(ctx, denial_code=denial_code, risk_level=risk_level, user_message=user_message)]


def _compose_user_message(
	raw: Mapping[str, Any],
	ctx: dict[str, Any],
	*,
	allowed: bool,
	denial_code: str,
) -> str:
	msg = str(raw.get("message") or "").strip()
	if not msg and not allowed:
		msg = str(ctx.get("state_message") or "").strip()
	if not msg and not allowed:
		msg = str(denial_code or "").strip()
	if not msg and allowed:
		msg = "Allowed"
	return msg


def _shape_pack_response(
	raw: Mapping[str, Any],
	*,
	action_code: str,
	object_type: str,
	object_code: str,
	context: dict[str, Any],
) -> dict[str, Any]:
	allowed = bool(raw.get("allowed"))
	ac = str(raw.get("action_code") or action_code or "").strip()
	ot = str(object_type or "").strip()
	oc = str(object_code or "").strip()
	risk_level = str(raw.get("risk_level") or "Medium").strip() or "Medium"
	required_permission = str(raw.get("required_permission") or "").strip()
	denial_code = str(raw.get("denial_code") or "").strip() if not allowed else ""
	user_message = _compose_user_message(raw, context, allowed=allowed, denial_code=denial_code)
	confirmation_required = bool(raw.get("requires_confirmation", False))
	reason_required = bool(context.get("reason_required", False))
	blockers = _build_blockers(
		context,
		allowed=allowed,
		denial_code=denial_code,
		risk_level=risk_level,
		user_message=user_message,
	)
	object_state = (
		str(context.get("object_state") or "").strip()
		or str((context.get("state_authorization") or {}).get("status") or "").strip()
	)

	out: dict[str, Any] = {
		"action_code": ac,
		"object_type": ot,
		"object_code": oc,
		"allowed": allowed,
		"denial_code": denial_code,
		"risk_level": risk_level,
		"required_permission": required_permission,
		"user_message": user_message,
		"blockers": blockers,
		"confirmation_required": confirmation_required,
		"reason_required": reason_required,
		# Legacy SEC / std-engine hints
		"message": user_message,
		"requires_confirmation": confirmation_required,
		"audit_on_attempt": bool(raw.get("audit_on_attempt", False)),
	}
	if object_state:
		out["object_state"] = object_state
	return out


class ActionAvailabilityService:
	"""Pack §12 implementation with no object mutation side effects."""

	@staticmethod
	def get_action_availability(
		actor: str,
		action_code: str,
		object_type: str,
		object_code: str,
		context: dict[str, Any] | None = None,
	) -> ActionAvailabilityResponse:
		ctx = dict(context) if context else {}
		raw = AuthorizationDecisionEngine.evaluate(actor, action_code, object_type, object_code, ctx)
		return _shape_pack_response(
			raw,
			action_code=action_code,
			object_type=object_type,
			object_code=object_code,
			context=ctx,
		)  # type: ignore[return-value]

	@classmethod
	def getActionAvailability(
		cls,
		actor: str,
		action_code: str,
		object_type: str,
		object_code: str,
		context: dict[str, Any] | None = None,
	) -> ActionAvailabilityResponse:
		"""Pack camelCase alias."""
		return cls.get_action_availability(actor, action_code, object_type, object_code, context=context)


def get_action_availability(
	action_code: str,
	object_type: str,
	object_code: str,
	actor: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §7.2 pack-ordered API (delegates to ``ActionAvailabilityService``)."""
	return ActionAvailabilityService.get_action_availability(actor, action_code, object_type, object_code, context=context)
