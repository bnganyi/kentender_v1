# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.16 §4.5 — ``Departmental Plan Submission.submission_number``
equals the ``version_number`` of the ``Departmental Plan Version`` it certifies.

Before v1.16 ``submit_departmental_plan`` derived ``submission_number`` as
"count of earlier submissions on the DPP root + 1", so a plan whose first
Submission was withdrawn (Version 1 never certified, Version 2 certified
first) carried ``submission_number = 1`` on a snapshot the screen labels
"Submission 2". The command now writes ``version.version_number`` directly;
this patch backfills every existing snapshot the same way so the number an
actor reads on screen and the number on the certified snapshot never differ.

Idempotent: a row already aligned is not rewritten. Plain column update via
``frappe.db.set_value(update_modified=False)`` — the snapshot's audit fields
are not touched, and no controller hook or event fires for a backfill.
"""

from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Departmental Plan Submission"):
		return
	if not frappe.db.has_column("Departmental Plan Submission", "submission_number"):
		return
	rows = frappe.get_all(
		"Departmental Plan Submission",
		fields=["name", "dpp_version", "submission_number"],
		limit_page_length=0,
	)
	for row in rows:
		if not row.dpp_version:
			continue
		version_number = frappe.db.get_value("Departmental Plan Version", row.dpp_version, "version_number")
		if version_number is None:
			continue
		if int(row.submission_number or 0) == int(version_number):
			continue
		frappe.db.set_value(
			"Departmental Plan Submission", row.name, "submission_number", int(version_number), update_modified=False,
		)
	frappe.db.commit()
