# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""When a versioned configuration record stops being editable.

Owner decision, 23 Sep 2026: every setting in this module follows one rule,
not four. A Version freezes as soon as it could matter to anyone — the moment
something pins it, the moment a source check is recorded against it, or the
moment it takes effect, whichever comes first. Until then it is unfinished
configuration and is corrected in place; afterwards a correction is a new
Version and the earlier one is retained.

The rule lives here so the services, the DocType controllers and the screens
cannot answer it differently. Each versioned doctype only has to say what
counts as "something pins it".
"""

from __future__ import annotations

import frappe
from frappe.utils import getdate, now_datetime

VERIFICATION_EVENT = "Reference Verification Event"


class VersionedRecord:
	"""One versioned configuration doctype and what depends on its Versions.

	`pins` are (doctype, fieldname) pairs holding a Version's name. They are
	read defensively: the owning app may not be installed, and Configuration
	must not depend on it either way — the same guard
	`_funding_source_referenced` uses.
	"""

	def __init__(self, *, doctype: str, noun: str, pins: tuple[tuple[str, str, str], ...] = (), verifiable: bool = False):
		self.doctype = doctype
		self.noun = noun
		self.pins = pins
		self.verifiable = verifiable


# `pins` entries are (doctype, fieldname, what-uses-it), the last being the
# plain word the administrator is shown: "A plan already uses this schedule".
REGISTRY: dict[str, VersionedRecord] = {
	record.doctype: record
	for record in (
		VersionedRecord(
			doctype="Procurement Method Profile",
			noun="rule",
			pins=(("Annual Plan Item", "method_profile_version", "plan"),),
		),
		VersionedRecord(
			doctype="Procedure Schedule Profile",
			noun="schedule",
			pins=(("Annual Plan Item", "schedule_profile_version", "plan"),),
		),
		VersionedRecord(
			doctype="Business Day Calendar",
			noun="calendar",
			# A schedule that counts working days names the exact calendar
			# version it counts them by, so changing it would change how an
			# already-published schedule was calculated.
			pins=(("Procedure Schedule Profile", "calendar", "schedule"),),
			verifiable=True,
		),
		VersionedRecord(
			doctype="Regulatory Reference",
			noun="rule",
			# Nothing stores a reference version's id: consumers resolve the
			# one in force for the applicable date. Its source check is what
			# fixes it in place.
			verifiable=True,
		),
	)
}


def _pinned_by(record: VersionedRecord, name: str) -> str:
	for doctype, fieldname, what in record.pins:
		if frappe.db.exists("DocType", doctype) and frappe.db.has_column(doctype, fieldname):
			if frappe.db.exists(doctype, {fieldname: name}):
				return what
	return ""


def _verified(record: VersionedRecord, name: str) -> bool:
	"""A recorded source check is evidence about this exact Version. Changing
	what it describes afterwards would make the evidence describe something
	that never existed."""
	if not record.verifiable or not frappe.db.exists("DocType", VERIFICATION_EVENT):
		return False
	return bool(frappe.db.exists(VERIFICATION_EVENT, {"target_doctype": record.doctype, "target_name": name}))


def version_editable(doctype: str, doc) -> tuple[bool, str]:
	"""Whether this Version may still be corrected in place, and if not, why.

	`doc` is the **stored** record, never the values being written: moving the
	effective date into the future must not unfreeze a Version already in
	force. The reason is the sentence the administrator reads, so it names
	what happened and what to do instead.
	"""
	record = REGISTRY.get(doctype)
	if record is None:
		return False, "This record is not one of the versioned settings."
	pinned = _pinned_by(record, doc.name)
	if pinned:
		return False, f"A {pinned} already uses this {record.noun}, so it cannot change. Create a new version instead."
	if _verified(record, doc.name):
		return False, f"A source check has been recorded against this {record.noun}, so it cannot change. Create a new version instead."
	if doc.get("effective_from") and getdate(doc.get("effective_from")) <= getdate(now_datetime()):
		return False, f"This {record.noun} has already taken effect, so it cannot change. Create a new version instead."
	return True, ""


def guard_in_place_edit(doc, *, mutable_fields: frozenset[str], child_tables: tuple[str, ...] = ()) -> None:
	"""The DocType controller half of the rule.

	Called from `validate`, it refuses any change to a Version that has
	frozen, so a raw Desk edit is judged exactly as the service would judge
	it. `flags.kt_supersede` (the status flip) and `flags.kt_correct_unused`
	(a service correction that has already checked) pass through.
	"""
	if doc.is_new():
		return
	before = doc.get_doc_before_save()
	if before is None:
		return
	# `kt_supersede` is the status flip, `kt_correct_unused` a service
	# correction that has already checked, and `kt_validity` the administrator
	# marking the rule valid — which is a statement *about* the version, not a
	# change to what it says, and so is allowed however long it has been in
	# force (owner decision, 23 Sep 2026).
	if any(getattr(doc.flags, flag, False) for flag in ("kt_supersede", "kt_correct_unused", "kt_validity")):
		return
	editable, reason = version_editable(doc.doctype, before)
	if editable:
		return
	for field in doc.meta.get_valid_columns():
		if field in mutable_fields or field.startswith("_"):
			continue
		if (doc.get(field) or None) != (before.get(field) or None):
			frappe.throw(reason, title="CFG_PROFILE_IMMUTABLE")
	for table in child_tables:
		if len(doc.get(table) or []) != len(before.get(table) or []):
			frappe.throw(reason, title="CFG_PROFILE_IMMUTABLE")
