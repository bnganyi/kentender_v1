# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.16 §5.2 / TRUST-OPS-001 v0.2 §9 — the incident status vocabulary becomes a finding.

post_model_sync, idempotent. An Opening incident used to carry one overwritten status (Open / Resolved / Unresolved). It now carries an incident status (Open /
Closed) and an append-only finding history (Unresolved / Recovered / Cannot recover). Existing rows move as follows, and nothing already recorded is lost:

- Open → Open, finding Unresolved (no finding row: nothing was found);
- Resolved → finding Recovered with one finding row carrying the old note, person and time; the incident is Closed ("Recovered and the opening continued")
  when its pause was already resolved, otherwise it stays Open (recovered, waiting for the chair);
- Unresolved → Open with finding Cannot recover and one finding row; Closed ("Closed after tender cancellation", service follow-up Open) when its opening has
  since ended by cancellation.

An incident that already carries a finding is left alone."""

from __future__ import annotations

import frappe

LEGACY = {"Open": "Unresolved", "Resolved": "Recovered", "Unresolved": "Cannot recover"}


def execute() -> None:
	if not frappe.db.table_exists("Opening Access Incident") or not frappe.db.has_column("Opening Access Incident", "current_finding"):
		return
	rows = frappe.get_all("Opening Access Incident", filters={"status": ("in", tuple(LEGACY))},
		fields=["name", "incident_id", "opening_case", "status", "current_finding", "resolution_note", "resolved_by", "resolved_at", "incident_revision"], limit_page_length=0)
	moved = 0
	for row in rows:
		if row.status == "Open" and row.current_finding and row.current_finding != "Unresolved":
			continue  # already carries a finding
		finding = LEGACY[row.status]
		values = {"current_finding": finding, "status": "Open"}
		revision = int(row.incident_revision or 0)
		if row.status in ("Resolved", "Unresolved") and not frappe.db.exists("Opening Incident Finding", {"incident": row.incident_id}):
			revision = 1
			finding_doc = frappe.get_doc({
				"doctype": "Opening Incident Finding", "finding_id": f"{row.incident_id}-F01", "incident": row.incident_id, "opening_case": row.opening_case, "finding_no": 1,
				"finding": finding, "reason": row.resolution_note or "Recorded before findings were kept as a history.", "recorded_by": row.resolved_by, "recorded_at": row.resolved_at,
				"incident_revision": 1, "opening_revision": 0, "last_committed_event": "", "request_key": "migrated",
			})
			finding_doc.flags.kt_bop_command = True  # written only by Bid Opening commands; this is the one that moves old rows
			finding_doc.insert(ignore_permissions=True, ignore_mandatory=True)
		values["incident_revision"] = revision
		state = frappe.db.get_value("Bid Opening Case", row.opening_case, "state")
		if row.status == "Resolved" and not frappe.db.exists("Opening Exception", {"incident": row.incident_id, "outcome": ("in", ("Open", "Escalated"))}):
			values.update(status="Closed", closure="Recovered and the opening continued", service_followup="Resolved", closed_at=row.resolved_at)
		elif row.status == "Unresolved" and state in ("Cancelled after start", "Not held"):
			values.update(status="Closed", closure="Closed after tender cancellation", service_followup="Open", closed_at=row.resolved_at)
		frappe.db.set_value("Opening Access Incident", row.name, values, update_modified=False)
		moved += 1
	frappe.logger().info("BOP v0.16: %s Opening incidents moved to findings", moved)
