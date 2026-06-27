"""Backfill domain v2 fields on existing Budget Lines.

New fields added in Budget Domain Revision v2:
  - amount_committed  → default 0 (was not present)
  - line_status       → default 'Active' for all active lines
  - economic_classification → NULL (not backfilled, user sets per line)
  - department        → NULL (not backfilled, user sets per line)
"""

import frappe
from frappe.utils import flt


def execute():
	frappe.reload_doctype("Budget Line")
	frappe.reload_doctype("Budget")
	frappe.reload_doctype("Budget Reservation")
	frappe.reload_doctype("Funding Source")

	# ── Budget Line: backfill amount_committed and line_status ────────────────
	frappe.db.sql("""
		UPDATE `tabBudget Line`
		SET
			amount_committed = COALESCE(amount_committed, 0),
			line_status = CASE
				WHEN line_status IS NULL OR line_status = '' THEN
					CASE WHEN is_active = 1 THEN 'Active' ELSE 'Suspended' END
				ELSE line_status
			END
		WHERE amount_committed IS NULL OR line_status IS NULL OR line_status = ''
	""")

	# ── Budget Line: recompute amount_available with new formula ─────────────
	# available = allocated - reserved - committed - consumed
	frappe.db.sql("""
		UPDATE `tabBudget Line`
		SET amount_available = (
			COALESCE(amount_allocated, 0)
			- COALESCE(amount_reserved, 0)
			- COALESCE(amount_committed, 0)
			- COALESCE(amount_consumed, 0)
		)
	""")

	frappe.db.commit()
	frappe.logger().info("[budget_domain_v2] Backfill complete.")
