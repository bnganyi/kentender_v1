# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AuthorizationDecisionEngine — SEC-0300 / Cursor pack §8.

Centralizes authorization evaluation in stable order. Sub-services SEC-0310–SEC-0330
feed results via ``context`` until their implementations call into this engine directly.

Evaluation order (pack §8):

1. Actor exists and is active (Frappe ``User``).
2. Actor holds required permission (``granted_permissions`` and/or ``security_role_codes``).
3. Object scope (``context["object_scope_ok"]`` — omit to defer SEC-0310).
4. Target object exists (``context["object_exists"]`` — omit to defer).
5. Object state allows action (``context["state_authorization"]`` — SEC-0320 — and/or
   legacy ``context["state_allows"]`` / ``state_denial_code``).
6. Lifecycle allows (``context["lifecycle_allows"]`` / ``lifecycle_denial_code``).
7. Negative permission rules (``context["enforce_negative_permission_rules"]`` →
   :class:`~kentender_procurement.tender_management.security.authorization.negative_permissions.NegativePermissionService`
   and/or legacy ``context["negative_denial_codes"]``).
8. Additional policy (``context["policy_ok"]`` / ``policy_denial_code``).
9. ``risk_level``, ``audit_on_attempt``, and when allowed ``requires_confirmation``.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict, cast

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
	is_known_denial_code,
)
from kentender_procurement.tender_management.security.authorization.object_scope import (
	ObjectScopeOutcome,
	ObjectScopeService,
)
from kentender_procurement.tender_management.security.authorization.state_authorization import (
	StateAuthorizationService,
)
from kentender_procurement.tender_management.security.authorization.negative_permissions import (
	NegativePermissionService,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class AuthorizationEvaluationAllowed(TypedDict, total=False):
	allowed: Literal[True]
	action_code: str
	required_permission: str
	risk_level: str
	requires_confirmation: bool
	audit_on_attempt: bool
	message: str


class AuthorizationEvaluationDenied(TypedDict, total=False):
	allowed: Literal[False]
	action_code: str
	required_permission: str
	denial_code: str
	risk_level: str
	audit_on_attempt: bool
	message: str


def _norm_ctx(context: dict[str, Any] | None) -> dict[str, Any]:
	return dict(context) if context else {}


def _norm_str(value: Any) -> str:
	if value is None:
		return ""
	return str(value).strip()


def _effective_risk(spec_risk: str, context: dict[str, Any]) -> str:
	override = (context.get("risk_level") or "").strip()
	if override in ("Low", "Medium", "High", "Critical"):
		return override
	return spec_risk


def _audit_and_confirmation(risk_level: str, *, outcome_allowed: bool) -> tuple[bool, bool]:
	r = (risk_level or "Medium").strip()
	audit_on = r in ("Medium", "High", "Critical")
	requires_confirmation = bool(outcome_allowed and r == "Critical")
	return audit_on, requires_confirmation


def _collect_granted_permissions(context: dict[str, Any]) -> frozenset[str]:
	if "granted_permissions" in context:
		raw = context.get("granted_permissions") or ()
		return frozenset(str(x).strip() for x in raw if str(x).strip())
	roles = context.get("security_role_codes") or ()
	if not isinstance(roles, (list, tuple, frozenset, set)):
		roles = (roles,)
	out: set[str] = set()
	for rc in roles:
		code = str(rc).strip()
		if not code:
			continue
		out |= RolePermissionService.granted_ids_for_role(code)
	return frozenset(out)


def _actor_row(actor: str) -> dict[str, Any] | None:
	uid = (actor or "").strip()
	if not uid:
		return None
	if not frappe.db.exists("User", uid):
		return None
	return frappe.db.get_value(
		"User",
		uid,
		["name", "enabled", "user_type"],
		as_dict=True,
	)


def _denied(
	*,
	action_code: str,
	required_permission: str,
	denial_code: str,
	risk_level: str,
	message: str,
) -> AuthorizationEvaluationDenied:
	if not is_known_denial_code(denial_code):
		denial_code = DenialCode.STD_AUTH_PERMISSION_DENIED
	audit_on, _ = _audit_and_confirmation(risk_level, outcome_allowed=False)
	return cast(
		AuthorizationEvaluationDenied,
		{
			"allowed": False,
			"action_code": action_code,
			"required_permission": required_permission,
			"denial_code": denial_code,
			"risk_level": risk_level,
			"audit_on_attempt": audit_on,
			"message": (message or "").strip() or denial_code,
		},
	)


def _allowed(
	*,
	action_code: str,
	required_permission: str,
	risk_level: str,
	message: str = "Allowed",
) -> AuthorizationEvaluationAllowed:
	audit_on, req_conf = _audit_and_confirmation(risk_level, outcome_allowed=True)
	return cast(
		AuthorizationEvaluationAllowed,
		{
			"allowed": True,
			"action_code": action_code,
			"required_permission": required_permission,
			"risk_level": risk_level,
			"requires_confirmation": req_conf,
			"audit_on_attempt": audit_on,
			"message": (message or "").strip() or "Allowed",
		},
	)


class AuthorizationDecisionEngine:
	"""Pack §8 — ordered authorization evaluation with stable JSON-shaped results."""

	@staticmethod
	def evaluate(
		actor: str,
		action_code: str,
		object_type: str,
		object_code: str,
		context: dict[str, Any] | None = None,
	) -> AuthorizationEvaluationAllowed | AuthorizationEvaluationDenied:
		"""Return an allow/deny payload. ``object_type`` / ``object_code`` are reserved for SEC-0310."""
		ctx = _norm_ctx(context)
		ac = (action_code or "").strip()
		ot = (object_type or "").strip()
		oc = (object_code or "").strip()
		_ = (ot, oc)  # reserved for future scope hooks

		# --- 1) Actor ---------------------------------------------------------
		row = _actor_row(actor)
		if not row or int(row.get("enabled") or 0) != 1:
			return _denied(
				action_code=ac,
				required_permission="",
				denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
				risk_level="Medium",
				message="Actor is missing, disabled, or not permitted.",
			)

		spec = spec_for_action(ac)
		if spec is None:
			return _denied(
				action_code=ac,
				required_permission="",
				denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
				risk_level="Medium",
				message=f"Unknown action_code: {ac!r}",
			)

		if str(row.get("user_type") or "").strip() == "Website User":
			granted_portal = _collect_granted_permissions(ctx)
			if spec.required_permission not in granted_portal:
				return _denied(
					action_code=ac,
					required_permission=spec.required_permission,
					denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
					risk_level="Low",
					message="Website User cannot perform this action.",
				)

		risk = _effective_risk(spec.default_risk_level, ctx)
		req_perm = spec.required_permission

		# --- 2) Permission ----------------------------------------------------
		granted = _collect_granted_permissions(ctx)
		if req_perm not in granted:
			return _denied(
				action_code=ac,
				required_permission=req_perm,
				denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
				risk_level=risk,
				message=ctx.get("permission_denial_message")
				or "Actor does not hold the required permission.",
			)

		# --- 3) Object scope (SEC-0310) ---------------------------------------
		scope_kind = str(ctx.get("object_scope_kind") or "").strip().lower()
		oc = (object_code or "").strip()
		ot = (object_type or "").strip()
		if ctx.get("enforce_object_scope") and scope_kind and oc:
			so: ObjectScopeOutcome
			if scope_kind == "package":
				so = ObjectScopeService.check_package_scope(actor, oc)
			elif scope_kind == "tender":
				so = ObjectScopeService.check_tender_scope(actor, oc)
			elif scope_kind == "std_template":
				so = ObjectScopeService.check_std_template_scope(actor, oc)
			elif scope_kind == "std_instance":
				so = ObjectScopeService.check_std_instance_scope(actor, oc)
			elif scope_kind == "committee":
				ct = str(ctx.get("committee_type") or "").strip()
				so = ObjectScopeService.check_committee_scope(actor, oc, ct)
			elif scope_kind == "audit":
				if not ot:
					so = ObjectScopeOutcome(
						False,
						DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED,
						"audit scope requires evaluate(..., object_type=<DocType name>)",
					)
				else:
					so = ObjectScopeService.check_audit_scope(actor, ot, oc)
			else:
				return _denied(
					action_code=ac,
					required_permission=req_perm,
					denial_code=DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED,
					risk_level=risk,
					message=f"Unknown object_scope_kind: {scope_kind!r}",
				)
			if not so.allowed:
				dc = str(so.denial_code or DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED)
				if not is_known_denial_code(dc):
					dc = DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED
				return _denied(
					action_code=ac,
					required_permission=req_perm,
					denial_code=dc,
					risk_level=risk,
					message=str(so.message or "Object scope denied."),
				)
		elif "object_scope_ok" in ctx and ctx["object_scope_ok"] is False:
			return _denied(
				action_code=ac,
				required_permission=req_perm,
				denial_code=DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED,
				risk_level=risk,
				message=str(ctx.get("object_scope_message") or "Object scope denied."),
			)

		# --- 4) Object exists -------------------------------------------------
		if "object_exists" in ctx and ctx["object_exists"] is False:
			return _denied(
				action_code=ac,
				required_permission=req_perm,
				denial_code=DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED,
				risk_level=risk,
				message=str(ctx.get("object_exists_message") or "Object does not exist."),
			)

		# --- 5) State (SEC-0320 + legacy hook) -------------------------------
		sa = ctx.get("state_authorization")
		if isinstance(sa, dict) and _norm_str(sa.get("kind")):
			sr = StateAuthorizationService.check(
				ac,
				kind=_norm_str(sa.get("kind")),
				status=_norm_str(sa.get("status")),
			)
			if not sr.allowed:
				dc = str(sr.denial_code or DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)
				if not is_known_denial_code(dc):
					dc = DenialCode.STD_AUTH_PERMISSION_DENIED
				return _denied(
					action_code=ac,
					required_permission=req_perm,
					denial_code=dc,
					risk_level=risk,
					message=str(sr.message or "Object state does not allow this action."),
				)
		if "state_allows" in ctx and ctx["state_allows"] is False:
			dc = str(ctx.get("state_denial_code") or DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED)
			return _denied(
				action_code=ac,
				required_permission=req_perm,
				denial_code=dc,
				risk_level=risk,
				message=str(ctx.get("state_message") or "Object state does not allow this action."),
			)

		# --- 6) Lifecycle -----------------------------------------------------
		if "lifecycle_allows" in ctx and ctx["lifecycle_allows"] is False:
			dc = str(ctx.get("lifecycle_denial_code") or DenialCode.STD_AUTH_ADDENDUM_REQUIRED)
			return _denied(
				action_code=ac,
				required_permission=req_perm,
				denial_code=dc,
				risk_level=risk,
				message=str(ctx.get("lifecycle_message") or "Lifecycle context does not allow this action."),
			)

		# --- 7) Negative rules (SEC-0330) -------------------------------------
		if ctx.get("enforce_negative_permission_rules"):
			npo = NegativePermissionService.evaluate_negative_rules(actor, ac, ot, oc, ctx)
			if not npo.allowed and npo.denial_codes:
				first = str(npo.denial_codes[0]).strip()
				if not is_known_denial_code(first):
					first = DenialCode.STD_AUTH_PERMISSION_DENIED
				return _denied(
					action_code=ac,
					required_permission=req_perm,
					denial_code=first,
					risk_level=risk,
					message=str(npo.message or "Negative permission rule blocks this action."),
				)
		raw_neg = ctx.get("negative_denial_codes")
		if raw_neg:
			if isinstance(raw_neg, str):
				first_raw = raw_neg
			else:
				seq = list(raw_neg)
				first_raw = seq[0] if seq else ""
			first = str(first_raw).strip()
			if first:
				if not is_known_denial_code(first):
					first = DenialCode.STD_AUTH_PERMISSION_DENIED
				return _denied(
					action_code=ac,
					required_permission=req_perm,
					denial_code=first,
					risk_level=risk,
					message=str(
						ctx.get("negative_message")
						or "Negative permission rule blocks this action.",
					),
				)

		# --- 8) Policy --------------------------------------------------------
		if "policy_ok" in ctx and ctx["policy_ok"] is False:
			dc = str(ctx.get("policy_denial_code") or DenialCode.STD_AUTH_PERMISSION_DENIED)
			return _denied(
				action_code=ac,
				required_permission=req_perm,
				denial_code=dc,
				risk_level=risk,
				message=str(ctx.get("policy_message") or "Policy check failed."),
			)

		# --- 9) Allowed + audit hints -----------------------------------------
		return _allowed(
			action_code=ac,
			required_permission=req_perm,
			risk_level=risk,
			message=str(ctx.get("allowed_message") or "Allowed"),
		)
