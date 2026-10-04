# Copyright (c) 2026, KenTender and contributors
"""System-generated immutable STD Configuration identifiers.

STD Configuration is global config (no procuring-entity scoping, unlike Strategy's
{PE}-{TYPE}-#### references) — one simple sequential series per DocType is enough.
"""

from __future__ import annotations

import frappe
from frappe import _

# Each DocType's own JSON `autoname` is the real naming-series template (e.g.
# "STDCFG-DRAFT-.####") — Frappe resolves `self.name` from it via `set_new_name()`,
# which runs AFTER `before_insert()`. Setting `self.name` by hand inside
# `before_insert` is therefore pointless (confirmed live: it gets silently
# overwritten). This helper only ever copies the already-resolved `self.name` into
# the spec-named id field, and must run in `validate()` (or later), not
# `before_insert()`.
ID_FIELD: dict[str, str] = {
	"STD Cfg Draft": "draft_id",
	"STD Cfg Version": "version_id",
	"STD Cfg Source Document": "source_document_id",
	"STD Cfg Content Block": "content_block_id",
}


def assign_generated_id(doc) -> None:
	"""Mirror the resolved document name into the spec-named id field on insert."""
	field = ID_FIELD.get(doc.doctype)
	if not field or doc.get(field):
		return
	doc.set(field, doc.name)


def assert_generated_id_immutable(doc, field: str) -> None:
	if doc.is_new():
		return
	if not doc.has_value_changed(field):
		return
	frappe.throw(
		_("{0} is system-generated and cannot be edited").format(frappe.unscrub(field)),
		frappe.ValidationError,
	)
