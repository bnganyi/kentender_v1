# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.6 §4.1/§16.4.11/§17 — drop `Needs Intake Window` outright.

Replaced by two namespaced fields already shipped on ERPNext's native
`Fiscal Year` (`kentender_needs_submission_open`, `_closes_at`; see
`kentender_core.install._ensure_fiscal_year_flag_fields`), maintained only
through `kentender_core.services.site_configuration` under `/app/system-setup`.
Departmental Needs owns no intake-window record of its own under v1.6.

No live or seed data referenced this doctype at the time of this patch
(verified: `frappe.db.count("Departmental Need") == 0` on every environment
this migration is expected to run against), so this is a pure schema drop —
unlike `nds_chg_001_v11_drop_retired_need_doctypes`, there is no rebuild-owed
graph to clear alongside it. If a future environment somehow carries rows,
fail loudly rather than silently discard them.
"""

from __future__ import annotations

import frappe

RETIRED_DOCTYPE = "Needs Intake Window"


def execute():
	if not frappe.db.exists("DocType", RETIRED_DOCTYPE):
		return
	count = frappe.db.count(RETIRED_DOCTYPE)
	if count:
		frappe.throw(
			f"NDS-CHG-001 v1.6 teardown found {count} {RETIRED_DOCTYPE} row(s). "
			"This patch only drops an empty doctype; review the rows before rerunning.",
			title="NDS_TEARDOWN_BLOCKED",
		)
	frappe.delete_doc("DocType", RETIRED_DOCTYPE, force=True, ignore_permissions=True)
	frappe.db.sql_ddl(f"drop table if exists `tab{RETIRED_DOCTYPE}`")
