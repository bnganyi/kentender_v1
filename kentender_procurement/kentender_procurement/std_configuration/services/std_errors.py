# Copyright (c) 2026, KenTender and contributors
"""§13.3 error contract — 12 named codes, each with a fixed meaning and a
translatable user-facing message. `frappe.throw(..., title=CODE)` is this
repo's standing convention for a named error code (see Strategy's
STRATEGY_SCOPE_REQUIRED family and `kentender_core.authorization_policy`'s
DENY_* codes) — API responses read the `title` to distinguish cases without
parsing message text.
"""

from __future__ import annotations

import frappe
from frappe import _

STD_CONTEXT_REQUIRED = "STD_CONTEXT_REQUIRED"
STD_DRAFT_CHANGED = "STD_DRAFT_CHANGED"
STD_BINDING_DUPLICATE = "STD_BINDING_DUPLICATE"
STD_BINDING_UNRESOLVED = "STD_BINDING_UNRESOLVED"
STD_COVERAGE_INCOMPLETE = "STD_COVERAGE_INCOMPLETE"
STD_VALIDATION_BLOCKED = "STD_VALIDATION_BLOCKED"
STD_ASSISTANCE_FAILED = "STD_ASSISTANCE_FAILED"
STD_ASSISTANCE_STALE = "STD_ASSISTANCE_STALE"
STD_MAKER_CHECKER = "STD_MAKER_CHECKER"
STD_REVIEW_CHANGED = "STD_REVIEW_CHANGED"
STD_MANIFEST_FAILED = "STD_MANIFEST_FAILED"
STD_VERSION_NOT_ACTIVE = "STD_VERSION_NOT_ACTIVE"

_MESSAGES: dict[str, str] = {
	STD_CONTEXT_REQUIRED: _("No effective STD assignment."),
	STD_DRAFT_CHANGED: _("This Draft has changed since it was loaded. Reload before saving."),
	STD_BINDING_DUPLICATE: _("This key is already used in this Draft."),
	STD_BINDING_UNRESOLVED: _("This block or mapping has no valid target. Open the owning area."),
	STD_COVERAGE_INCOMPLETE: _("One or more required areas are incomplete. Open the Coverage Report."),
	STD_VALIDATION_BLOCKED: _("Blocking findings remain. Open the Readiness Report."),
	STD_ASSISTANCE_FAILED: _("Draft assistance could not produce a proposal. Your Draft is unchanged."),
	STD_ASSISTANCE_STALE: _("This proposal was generated against an older Draft. Regenerate or discard it."),
	STD_MAKER_CHECKER: _("You cannot perform this decision because you completed an incompatible earlier action."),
	STD_REVIEW_CHANGED: _("The submitted snapshot is no longer current. Reload the review task."),
	STD_MANIFEST_FAILED: _("One or more manifests could not be generated. No Active Version was created."),
	STD_VERSION_NOT_ACTIVE: _("The requested STD Version is not available."),
}

# §13.3's own natural exception class per code — used so a caller catching
# frappe.ValidationError vs frappe.PermissionError still gets the behavior the
# HTTP layer expects, while the `title` carries the exact named code.
_EXCEPTION_CLASS: dict[str, type[Exception]] = {
	STD_MAKER_CHECKER: frappe.PermissionError,
	STD_CONTEXT_REQUIRED: frappe.PermissionError,
}


def std_throw(code: str, message: str | None = None) -> None:
	if code not in _MESSAGES:
		frappe.throw(_("Unknown STD error code: {0}").format(code))
	exc_class = _EXCEPTION_CLASS.get(code, frappe.ValidationError)
	frappe.throw(message or _MESSAGES[code], exc_class, title=code)
