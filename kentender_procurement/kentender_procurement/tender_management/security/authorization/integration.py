from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.security.audit.denied_action import (
	DeniedActionAuditService,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.decision_engine import (
	AuthorizationDecisionEngine,
)


def enforce_sec_authorization(
	*,
	action_code: str,
	actor: str | None,
	object_type: str,
	object_code: str,
	context: dict[str, Any] | None = None,
	fallback_message: str | None = None,
) -> dict[str, Any]:
	"""SEC-1000 integration shim for direct service invocation authorization."""
	ac = (action_code or "").strip()
	ot = (object_type or "").strip()
	oc = (object_code or "").strip()
	act = (actor or "").strip() or (frappe.session.user if frappe.session else None) or "Administrator"
	ctx = dict(context or {})

	spec = spec_for_action(ac)
	if spec and "granted_permissions" not in ctx:
		# Keep current service behavior while still forcing engine/state/scope checks.
		ctx["granted_permissions"] = [spec.required_permission]

	outcome = AuthorizationDecisionEngine.evaluate(act, ac, ot, oc, ctx)
	if outcome.get("allowed"):
		return outcome

	denial_code = str(outcome.get("denial_code") or "STD_AUTH_PERMISSION_DENIED").strip()
	message = str(outcome.get("message") or "").strip() or (fallback_message or _("Authorization denied."))
	risk_level = str(outcome.get("risk_level") or "Medium").strip()
	audit_on_attempt = bool(outcome.get("audit_on_attempt"))
	if risk_level in ("High", "Critical") or audit_on_attempt:
		try:
			DeniedActionAuditService.record_denied_action(
				act,
				ac,
				ot,
				oc,
				{
					"denial_code": denial_code,
					"risk_level": risk_level,
					"message": message,
					"audit_on_attempt": audit_on_attempt,
				},
				ctx,
			)
		except Exception:
			pass
	frappe.throw(_(message), title=denial_code, exc=frappe.PermissionError)
