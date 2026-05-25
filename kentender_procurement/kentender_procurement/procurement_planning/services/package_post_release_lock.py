# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 post-release baseline lock helpers (P2-012 / governance §11)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_LOCKED_STATUSES,
	PKG_POST_RELEASE_LOCKED_FIELDS,
	POST_RELEASE_LOCK_MESSAGE,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackagePostReleaseLock,
)


def is_post_release_locked(doc_or_row: Any) -> bool:
	"""True when package is Released, Consumed, Superseded, or locked_after_release is set."""
	if isinstance(doc_or_row, dict):
		locked_flag = cint(doc_or_row.get("locked_after_release"))
		status = (doc_or_row.get("status") or "").strip()
	else:
		locked_flag = cint(getattr(doc_or_row, "locked_after_release", 0))
		status = (getattr(doc_or_row, "status", None) or "").strip()
	return bool(locked_flag) or status in PKG_LOCKED_STATUSES


def changed_post_release_locked_fields(doc) -> set[str]:
	if doc.is_new():
		return set()
	changed: set[str] = set()
	for fieldname in PKG_POST_RELEASE_LOCKED_FIELDS:
		if doc.has_value_changed(fieldname):
			changed.add(fieldname)
	return changed


def assert_post_release_baseline_editable(doc) -> None:
	"""Deny baseline field edits on post-release packages (no admin bypass)."""
	if not is_post_release_locked(doc):
		return
	if changed_post_release_locked_fields(doc):
		frappe.throw(
			POST_RELEASE_LOCK_MESSAGE,
			title=PackagePostReleaseLock.LOCKED_AFTER_RELEASE,
		)


def post_release_lock_error() -> dict[str, str]:
	return {
		"code": PackagePostReleaseLock.LOCKED_AFTER_RELEASE,
		"message": POST_RELEASE_LOCK_MESSAGE,
	}
