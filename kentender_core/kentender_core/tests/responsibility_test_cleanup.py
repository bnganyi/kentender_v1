"""One cleanup for every configuration/authorization test fixture.

Project Owner rule (2026-09-01): test data never stays in the database. Every
suite in this family registers `purge` as a class cleanup, and the same
function is runnable directly when a crashed run leaves residue behind:

  bench --site <site> execute \\
    kentender_core.tests.responsibility_test_cleanup.purge

Everything the fixtures create is identifiable by construction — users
`kt.test.%`, assignment fixture_namespace `KT_TEST_%`, Organisation Units
with fixture_namespace `KT_TEST_%`, unit_code `KT-TEST-%` or unit_name
`KT Test %` (service-created units get generated codes, so tests name them
`KT Test …`), fiscal years with `start_year >= 2095`, command-journal rows
keyed `KT-TEST-%` — so the purge deletes by those patterns only and can never
touch a real record. Deletion runs in dependency order: assignments first,
then Organisation Units leaves-first (`lft desc`, so the nested-set
child-exists guard never fires), then fiscal years, journal rows, users.

Deliberately NOT deleted: the `Site Procuring Entity` Single and the site's
root Organisation Unit — those are the KT-STD-001 §8 canonical site
configuration, governed records rather than fixtures. Legacy `Procuring
Entity` / `Organisation Unit Type` test rows from the pre-v1.6 suites keep
their old patterns and are still purged.
"""

from __future__ import annotations

import frappe

PE_PATTERN = "KT-TEST-%"
USER_PATTERN = "kt.test.%"
UNIT_TYPE_PATTERN = "KT-TEST-%"
NAMESPACE_PATTERN = "KT_TEST_%"
UNIT_NAME_PATTERN = "KT Test %"
FY_TEST_MIN_START_YEAR = 2095


def purge(*, commit: bool = True) -> dict[str, int]:
	removed: dict[str, int] = {}

	assignments = set(
		frappe.get_all(
			"User Responsibility Assignment",
			filters={"fixture_namespace": ("like", NAMESPACE_PATTERN)},
			pluck="name",
		)
	) | set(
		frappe.get_all(
			"User Responsibility Assignment",
			filters={"user": ("like", USER_PATTERN)},
			pluck="name",
		)
	)
	for name in assignments:
		frappe.delete_doc(
			"User Responsibility Assignment", name, force=1, ignore_permissions=True
		)
	removed["User Responsibility Assignment"] = len(assignments)

	units: list[str] = []
	seen: set[str] = set()
	for filters in (
		{"fixture_namespace": ("like", NAMESPACE_PATTERN)},
		{"unit_code": ("like", PE_PATTERN)},
		{"unit_name": ("like", UNIT_NAME_PATTERN)},
	):
		for name in frappe.get_all(
			"Organisation Unit",
			filters=filters,
			pluck="name",
			order_by="lft desc",
			limit_page_length=0,
		):
			if name not in seen:
				seen.add(name)
				units.append(name)
	# Leaves first across the merged set.
	units.sort(
		key=lambda name: frappe.db.get_value("Organisation Unit", name, "lft") or 0,
		reverse=True,
	)
	for name in units:
		frappe.delete_doc("Organisation Unit", name, force=1, ignore_permissions=True)
	removed["Organisation Unit"] = len(units)

	fiscal_years = frappe.get_all(
		"Fiscal Year",
		filters={"year_start_date": (">=", f"{FY_TEST_MIN_START_YEAR}-01-01")},
		pluck="name",
	)
	audit_rows = 0
	if frappe.db.exists("DocType", "Audit Event"):
		audit = set()
		if fiscal_years:
			audit.update(
				frappe.get_all(
					"Audit Event",
					filters={"document_type": "Fiscal Year", "document_name": ("in", fiscal_years)},
					pluck="name",
				)
			)
		audit.update(
			frappe.get_all(
				"Audit Event",
				filters={
					"document_type": "Site Procuring Entity",
					"metadata": ("like", "%KT-TEST%"),
				},
				pluck="name",
			)
		)
		for name in audit:
			frappe.delete_doc("Audit Event", name, force=1, ignore_permissions=True)
		audit_rows = len(audit)
	removed["Audit Event"] = audit_rows
	for name in fiscal_years:
		frappe.delete_doc("Fiscal Year", name, force=1, ignore_permissions=True)
	removed["Fiscal Year"] = len(fiscal_years)

	journals = frappe.get_all(
		"Reference Data Command Journal",
		filters={"idempotency_key": ("like", PE_PATTERN)},
		pluck="name",
	)
	for name in journals:
		frappe.delete_doc(
			"Reference Data Command Journal", name, force=1, ignore_permissions=True
		)
	removed["Reference Data Command Journal"] = len(journals)

	unit_types = frappe.get_all(
		"Organisation Unit Type", filters={"name": ("like", UNIT_TYPE_PATTERN)}, pluck="name"
	)
	for name in unit_types:
		frappe.delete_doc("Organisation Unit Type", name, force=1, ignore_permissions=True)
	removed["Organisation Unit Type"] = len(unit_types)

	test_entities = frappe.get_all(
		"Procuring Entity", filters={"name": ("like", PE_PATTERN)}, pluck="name"
	)
	for name in test_entities:
		frappe.delete_doc("Procuring Entity", name, force=1, ignore_permissions=True)
	removed["Procuring Entity"] = len(test_entities)

	users = frappe.get_all("User", filters={"name": ("like", USER_PATTERN)}, pluck="name")
	for name in users:
		frappe.delete_doc("User", name, force=1, ignore_permissions=True)
	removed["User"] = len(users)

	if commit:
		frappe.db.commit()
	return removed
