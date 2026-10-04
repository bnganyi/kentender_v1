"""Purge ERPNext's own `_Test Fiscal Year %` / `_Test Short Fiscal Year %`
rows — not KenTender seed data, not owned by `kentender_core.seeds.canonical`.

These come from ERPNext's own test suite (`erpnext/accounts/doctype/fiscal_year/
test_fiscal_year.py`, `erpnext/tests/utils.py`), created whenever an ERPNext
Python test runs on this site. `canonical.py`'s `wipe` deliberately never
touches them (SEED-OPS-001 §3.2 — ERPNext-owned records), so they accumulate
indefinitely across dev-site test runs with no other cleanup path. This is a
separate, one-off purge for that specific clutter, run by hand:

  bench --site <site> execute \\
    kentender_core.tests.erpnext_test_fixture_cleanup.purge

A row this can't delete (something still links to it) is skipped, not fatal —
reported under `skipped` rather than raising, so one stuck row never blocks
the rest.
"""

from __future__ import annotations

import frappe

NAME_PATTERNS = ("_Test Fiscal Year%", "_Test Short Fiscal Year%")


def purge(*, commit: bool = True) -> dict[str, object]:
	names: list[str] = []
	seen: set[str] = set()
	for pattern in NAME_PATTERNS:
		for name in frappe.get_all("Fiscal Year", filters={"name": ("like", pattern)}, pluck="name"):
			if name not in seen:
				seen.add(name)
				names.append(name)

	deleted: list[str] = []
	skipped: dict[str, str] = {}
	for name in names:
		try:
			frappe.delete_doc("Fiscal Year", name, ignore_permissions=True)
			deleted.append(name)
		except Exception as exc:  # noqa: BLE001 - a stuck row must not block the rest
			skipped[name] = str(exc)

	if commit:
		frappe.db.commit()
	return {"found": len(names), "deleted": len(deleted), "skipped": skipped}
