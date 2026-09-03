# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §1.1 — drop the concepts v1.1 removes from Departmental Needs.

Removed outright (not renamed, aliased, dual-read or feature-flagged, per §1
and §17):

* ``Departmental Need Item`` — one Need now represents one requirement, with
  quantity and unit held directly on the version (§1.1, §4.3, NDS-AC-001).
* ``Departmental Need Attachment`` — no approved departmental-review decision
  requires a document (§1.1, NDS-AC-029).
* ``Departmental Need Review`` — superseded by ``Departmental Need Decision``
  (§4.5), which separates the immutable decision record from the version model.

The Departmental Need root is reshaped to §4.2 in the same migration, so its
existing rows cannot be carried forward: they hold requirement content that now
belongs to ``Departmental Need Version``. §1.1 prohibits a migration or
compatibility path, so the seed/fixture rows are cleared and rebuilt from the
§14 seed contract. This patch refuses to run if it finds a row it cannot
account for as seed or test data.
"""

from __future__ import annotations

import frappe

RETIRED_DOCTYPES = (
	"Departmental Need Item",
	"Departmental Need Attachment",
	"Departmental Need Review",
)

# Seed namespaces and test-actor domains that this rebuild is entitled to clear.
SEED_NAMESPACE_PREFIX = "KENTENDER_MVP_1_R1"
TEST_OWNER_DOMAINS = (".example.test", "@example.test")


def execute():
	_guard_unexpected_records()
	frappe.db.delete("Plan Need Allocation")
	frappe.db.delete("Departmental Need")
	for doctype in RETIRED_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)
		frappe.db.sql_ddl(f"drop table if exists `tab{doctype}`")


def _guard_unexpected_records():
	"""Fail closed rather than destroy a record this rebuild did not create."""
	if not frappe.db.exists("DocType", "Departmental Need"):
		return
	unexpected = [
		row.name
		for row in frappe.get_all(
			"Departmental Need", fields=["name", "fixture_namespace", "owner"], limit_page_length=0
		)
		if not _is_disposable(row)
	]
	if unexpected:
		frappe.throw(
			"NDS-CHG-001 v1.1 teardown found Departmental Need rows that are neither seed "
			f"fixtures nor test records: {', '.join(sorted(unexpected))}. "
			"Review them before rerunning this migration.",
			title="NDS_TEARDOWN_BLOCKED",
		)


def _is_disposable(row) -> bool:
	namespace = row.get("fixture_namespace") or ""
	owner = row.get("owner") or ""
	if namespace.startswith(SEED_NAMESPACE_PREFIX):
		return True
	return any(owner.endswith(domain) for domain in TEST_OWNER_DOMAINS)
