# Copyright (c) 2026, KenTender and contributors
"""RG-36 / AUD-XC-013: every write-capable doctype is either command-only or named here.

Each family test (Requisitions, Tenders, Planning, Needs, Budget, Strategy, ...) hard-codes its own
list of guarded doctypes, which is how the Planning evidence doctypes, the Needs outbox and the
journals slipped through. This test walks every non-child doctype of every installed KenTender app
and fails when a role holds write, create or delete in the doctype JSON and the controller carries
no `command_write_family`, unless the doctype is on a reviewed list below. Adding a doctype to a
list is a decision a reviewer sees; a new doctype cannot become user-writable by accident.

It reads the standard DocPerm in the doctype JSON (what a fresh install gets). Custom DocPerm rows
created by patches are not seen here.

Lists:
- REFERENCE_AND_SETUP: configuration and reference data that people maintain through Desk forms
  or the reference-data API by design.
- OPEN_FINDINGS: doctypes that are user-writable today and are tracked as findings. Remove an entry
  in the same commit that guards the doctype. (The test does not fail on a stale entry, so a lane
  that fixes one is never blocked by another lane's list.)
"""

from __future__ import annotations

import glob
import json

import frappe
from frappe.model.base_document import get_controller
from frappe.tests import IntegrationTestCase

REFERENCE_AND_SETUP = frozenset(
	{
		"Business Day Calendar",
		"Business Unit",
		"Contact Office",
		"Delivery Location",
		"Financial Year",
		"Funding Source",
		"Intake Control",
		"Organisation Unit",
		"Organisation Unit Type",
		"PE Fiscal Year Context",
		"PE Type",
		"Procedure Schedule Profile",
		"Procurement Method",
		"Procurement Method Profile",
		"Procuring Department",
		"Procuring Entity",
		"Procuring Entity Version",
		"Regulatory Reference",
		"Regulatory Reference Set",
		"Requirement Type",
		"Unit Of Measure",
		"KTSM Document Type",
		"KTSM Supplier Category",
		"KTSM Performance Note",
	}
)

OPEN_FINDINGS = frozenset(
	{
		# Journals, counters and evidence rows that System Manager can still write (the same class as RG-40's
		# Strategy Command Journal) but that no Wave 4R row names; a follow-up for the lead.
		"Reference Data Command Journal",
		"Reference Verification Event",
		"Business ID Counter",
		"Typed Attachment",
		"Exception Record",
		"Annual Plan Publication Destination",
		"KTSM Status History",
		# The legacy Journey surfaces (RG-33).
		"Procurement Handoff Card",
		"Procurement Journey",
	}
)

def _kentender_doctype_files():
	for app in frappe.get_installed_apps():
		if not app.startswith("kentender_"):
			continue
		for path in glob.glob(frappe.get_app_path(app) + "/**/doctype/*/*.json", recursive=True):
			try:
				with open(path) as handle:
					meta = json.load(handle)
			except (OSError, ValueError):
				continue
			if meta.get("doctype") == "DocType":
				yield app, meta


def _family(doctype: str) -> str:
	try:
		return getattr(get_controller(doctype), "command_write_family", "") or ""
	except Exception:  # a doctype with no importable controller carries no guard
		return ""


class TestEveryWritableDoctypeIsCommandOnlyOrReviewed(IntegrationTestCase):
	def test_no_unreviewed_doctype_is_user_writable_without_the_guard(self):
		reviewed = REFERENCE_AND_SETUP | OPEN_FINDINGS
		offenders = {}
		for app, meta in _kentender_doctype_files():
			if meta.get("istable") or meta.get("issingle") or meta.get("is_virtual"):
				continue
			grants = sorted(
				{row["role"] for row in meta.get("permissions", []) if row.get("write") or row.get("create") or row.get("delete")}
			)
			if not grants or _family(meta["name"]) or meta["name"] in reviewed:
				continue
			offenders[f"{app}: {meta['name']}"] = grants
		self.assertFalse(
			offenders,
			"These doctypes grant write/create/delete in their JSON and carry no command_write_family. Give them the "
			"CommandWriteGuardMixin and drop the DocPerm, or add them to a reviewed list with a reason: "
			+ json.dumps(offenders, indent=1),
		)

	def test_the_children_of_a_command_only_parent_are_command_only_too(self):
		"""RG-06: Frappe's REST create inserts a child row on its own and a delete runs only the child's controller."""
		unguarded = {}
		for app, meta in _kentender_doctype_files():
			parent = meta["name"]
			family = _family(parent)
			if not family or meta.get("istable"):
				continue
			for field in meta.get("fields", []):
				if field.get("fieldtype") in ("Table", "Table MultiSelect") and field.get("options"):
					child_family = _family(field["options"])
					if child_family != family:
						unguarded[f"{parent}.{field['fieldname']} -> {field['options']}"] = child_family or "none"
		self.assertFalse(unguarded, f"child tables whose family differs from the parent's: {json.dumps(unguarded, indent=1)}")

	def test_a_command_only_doctype_cannot_be_renamed(self):
		"""RG-42: Frappe's rename skips `validate`, so a guarded doctype that allows rename lets Administrator
		rewrite its name past the guard."""
		renamable = sorted(
			meta["name"]
			for _app, meta in _kentender_doctype_files()
			if _family(meta["name"]) and not meta.get("istable") and meta.get("allow_rename")
		)
		self.assertFalse(renamable, f"command-only doctypes that allow rename: {renamable}")
