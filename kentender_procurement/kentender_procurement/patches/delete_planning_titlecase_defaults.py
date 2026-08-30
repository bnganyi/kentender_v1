"""CTX-CHG-001 Phase E — delete Planning's dead Title-Case default rows.

"KT Planning Procuring Entity" / "KT Planning Financial Year" never restored
(frappe.defaults' is_a_user_permission_key reroutes any key != scrub(key)),
so there is nothing to migrate — the rows are noise. Idempotent.
"""

from __future__ import annotations

import frappe


def execute():
	frappe.db.delete(
		"DefaultValue",
		{"defkey": ["in", ["KT Planning Procuring Entity", "KT Planning Financial Year"]]},
	)
