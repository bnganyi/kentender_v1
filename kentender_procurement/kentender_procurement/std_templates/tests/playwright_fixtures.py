# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright support for tests/ui/smoke/std_templates (test data only).

`purge_playwright_concerns` removes every concern the browser specs create —
identified by their summary prefix — with its evidence file and audit rows.
A browser pass is test data too; nothing it creates may survive the run.
"""

from __future__ import annotations

import frappe

PREFIX = "Playwright:"


def purge_playwright_concerns() -> int:
	names = frappe.get_all("STD Template Concern", filters={"summary": ["like", f"{PREFIX}%"]}, pluck="name")
	for name in names:
		doc = frappe.get_doc("STD Template Concern", name)
		if doc.evidence_file_id and frappe.db.exists("File", doc.evidence_file_id):
			frappe.delete_doc("File", doc.evidence_file_id, force=True, ignore_permissions=True)
		doc.flags.kt_fixture_wipe = True
		doc.delete(ignore_permissions=True, force=True)
		frappe.db.delete("Audit Event", {"document_name": name})
	frappe.db.commit()
	print(f"purged {len(names)} Playwright concern(s)")
	return len(names)
