# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Owner decision 26 Sep 2026 (FU-V127-01) — Planning instants are stored in
the site timezone, like every other module's and Frappe's own. Two sets of
rows were written in UTC while Planning's reads converted from UTC:

- the canonical seed's design-clock instants — moved only where a row still
  holds the exact old UTC value, so a time written by a command is untouched;
- a budget revision request's `requested_at` / `outcome_at` — moved only
  where the stored value sits three hours behind the row's own `creation` /
  `modified` (the site clock at the same moment), so a row already written in
  site time is left alone.
"""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import get_datetime

from kentender_core.utils.instants import from_utc_iso
from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import CLOCK, CLOCK_BEFORE_SITE_TIME

# (doctype, field, CLOCK key) — every row `_stamp_design_clock` writes.
STAMPED = (
	("Departmental Plan Submission", "submitted_at", "dpp_submitted"),
	("Departmental Plan Validation Decision", "decided_at", "dpp_accepted"),
	("Plan Finance Decision", "decided_at", "finance_confirmed"),
	("Annual Plan Version", "submitted_at", "plan_submitted"),
	("Annual Plan Version", "activated_at", "publication_acknowledged"),
	("Plan Governance Decision", "decided_at", "ao_adopted"),
	("Plan Governance Decision", "decided_at", "statutory_approved"),
	("Plan Publication", "acknowledged_at", "publication_acknowledged"),
	("Publication Attempt", "attempted_at", "publication_attempted"),
	("Publication Attempt", "completed_at", "publication_acknowledged"),
	("Publication Acknowledgement", "acknowledged_at", "publication_acknowledged"),
	("Publication Acknowledgement", "received_at", "publication_acknowledged"),
	("Treasury Submission Evidence", "recorded_at", "treasury_submitted"),
)


def execute():
	for doctype, field, key in STAMPED:
		if not frappe.db.has_column(doctype, field):
			continue
		frappe.db.sql(
			f"update `tab{doctype}` set `{field}` = %s where `{field}` = %s",
			(CLOCK[key], CLOCK_BEFORE_SITE_TIME[key]),
		)

	if not frappe.db.table_exists("Plan Budget Revision Request"):
		return
	for row in frappe.get_all(
		"Plan Budget Revision Request", fields=["name", "requested_at", "outcome_at", "creation", "modified"], limit_page_length=0,
	):
		values = {}
		for field, clock in (("requested_at", row.creation), ("outcome_at", row.modified)):
			stored = row.get(field)
			if stored and abs(get_datetime(clock) - get_datetime(stored) - timedelta(hours=3)) < timedelta(minutes=1):
				values[field] = from_utc_iso(get_datetime(stored).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z")
		if values:
			frappe.db.set_value("Plan Budget Revision Request", row.name, values, update_modified=False)
