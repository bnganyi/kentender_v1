# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-27 — Immutability guards (doc 9 §5.4).

Central **backend** checks for “created / append-only / supersede-only” rows so DocTypes do not
each re-implement the same ``meta.fields`` iteration.

**Doc 9 §5.4** — Publication Record, Publication Readiness, Bid Receipt, Closing Record, Audit Event,
etc. must reject ordinary saves that mutate locked content; supersede pointers are explicit
exceptions behind flags (see ``only_supersede_pointer_transition``).
"""

from __future__ import annotations

from typing import Mapping

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

_LAYOUT_FIELD_TYPES: frozenset[str] = frozenset({"Section Break", "Column Break", "Tab Break"})

LAYOUT_FIELD_TYPES: frozenset[str] = _LAYOUT_FIELD_TYPES

DEFAULT_IMMUTABLE_SKIP: frozenset[str] = frozenset(
	{"name", "owner", "creation", "docstatus", "idx", "modified", "modified_by"}
)

__all__ = (
	"DEFAULT_IMMUTABLE_SKIP",
	"LAYOUT_FIELD_TYPES",
	"forbidden_fieldnames_after_create",
	"raise_immutable_after_create",
	"only_supersede_pointer_transition",
	"raise_immutable_or_supersede_pointer",
	"raise_append_only_on_update",
	"only_supersede_pointer_dicts",
)


def forbidden_fieldnames_after_create(
	doc: Document,
	prev: Document,
	*,
	mutable_fieldnames: frozenset[str] | None = None,
	skip_fieldnames: frozenset[str] | None = None,
) -> list[str]:
	"""Return data field names that differ from ``prev`` but are not allowed post-create."""
	if not prev:
		return []
	skip = skip_fieldnames or DEFAULT_IMMUTABLE_SKIP
	mutable = mutable_fieldnames or frozenset()
	bad: list[str] = []
	for df in doc.meta.fields:
		fn = df.fieldname
		if fn in skip or df.fieldtype in _LAYOUT_FIELD_TYPES:
			continue
		if fn in mutable:
			continue
		if prev.get(fn) != doc.get(fn):
			bad.append(fn)
	return bad


def raise_immutable_after_create(
	doc: Document,
	*,
	message: str,
	title: str,
	ignore_flag: str,
	mutable_fieldnames: frozenset[str] | None = None,
	skip_fieldnames: frozenset[str] | None = None,
) -> None:
	"""Reject field changes after insert (e.g. Bid Receipt, Closing Record)."""
	if getattr(doc.flags, ignore_flag, False):
		return
	prev = doc.get_doc_before_save()
	if not prev:
		return
	bad = forbidden_fieldnames_after_create(
		doc, prev, mutable_fieldnames=mutable_fieldnames, skip_fieldnames=skip_fieldnames
	)
	if bad:
		frappe.throw(_(message), title=_(title))


def only_supersede_pointer_transition(
	prev: Document,
	doc: Document,
	*,
	pointer_field: str,
	skip_fieldnames: frozenset[str] | None = None,
) -> bool:
	"""True when only ``pointer_field`` moves from empty → set and all other compared fields match."""
	skip = skip_fieldnames or DEFAULT_IMMUTABLE_SKIP
	if cstr(prev.get(pointer_field)).strip():
		return False
	if not cstr(doc.get(pointer_field)).strip():
		return False
	for df in doc.meta.fields:
		fn = df.fieldname
		if fn in skip or df.fieldtype in _LAYOUT_FIELD_TYPES:
			continue
		if fn == pointer_field:
			continue
		if prev.get(fn) != doc.get(fn):
			return False
	return True


def raise_immutable_or_supersede_pointer(
	doc: Document,
	*,
	pointer_field: str,
	allow_supersede_flag: str,
	message: str,
	title: str,
	skip_fieldnames: frozenset[str] | None = None,
) -> None:
	"""Publication Readiness / Publication Record pattern (TM2-PRD / TM2-PUB immutability)."""
	prev = doc.get_doc_before_save()
	if not prev:
		return
	if getattr(doc.flags, allow_supersede_flag, False) and only_supersede_pointer_transition(
		prev, doc, pointer_field=pointer_field, skip_fieldnames=skip_fieldnames
	):
		return
	frappe.throw(_(message), title=_(title))


def raise_append_only_on_update(
	doc: Document,
	*,
	message: str,
	title: str,
	ignore_flag: str,
) -> None:
	"""Audit-event style: any save after insert is forbidden."""
	if doc.is_new():
		return
	if getattr(doc.flags, ignore_flag, False):
		return
	frappe.throw(_(message), title=_(title))


def only_supersede_pointer_dicts(prev: Mapping, curr: Mapping, *, pointer: str) -> bool:
	"""Pure helper for tests — same semantics as ``only_supersede_pointer_transition`` on flat maps."""
	if cstr(prev.get(pointer)).strip():
		return False
	if not cstr(curr.get(pointer)).strip():
		return False
	for k in set(prev) | set(curr):
		if k == pointer:
			continue
		if prev.get(k) != curr.get(k):
			return False
	return True
