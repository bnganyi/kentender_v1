"""Thin whitelisted boundary for Departmental Needs services.

No writable DocType endpoint bypasses a command (§16.1). Attachment endpoints
are removed with the attachment concept itself (§1.1, NDS-AC-029); the support
lookup is removed with the support-lookup workflow (§1.1).

Phase 4 renames this surface to the exact §8.1/§8.2 contract names.
"""

import frappe

from kentender_procurement.departmental_needs.services.context import (
	intake_window as _intake_window,
	resolve_creation_context as _resolve_creation_context,
	save_intake_window as _save_intake_window,
)
from kentender_procurement.departmental_needs.services.lifecycle import (
	cancel_accepted_need_successor as _cancel_accepted_need_successor,
	check_withdrawal_dependency as _check_withdrawal_dependency,
	create_accepted_need_successor as _create_accepted_need_successor,
	create_need as _create_need,
	decide_withdrawal as _decide_withdrawal,
	request_withdrawal as _request_withdrawal,
	review_need as _review_need,
	submit_need as _submit_need,
	update_need as _update_need,
	withdraw_need as _withdraw_need,
)
from kentender_procurement.departmental_needs.services.workspace import get_need, get_workspace

resolve_creation_context = frappe.whitelist()(_resolve_creation_context)
get_workspace = frappe.whitelist()(get_workspace)
get_need = frappe.whitelist()(get_need)
get_intake_window = frappe.whitelist()(_intake_window)
check_withdrawal_dependency = frappe.whitelist()(_check_withdrawal_dependency)
create_need = frappe.whitelist()(_create_need)
update_need = frappe.whitelist()(_update_need)
submit_need = frappe.whitelist()(_submit_need)
review_need = frappe.whitelist()(_review_need)
withdraw_need = frappe.whitelist()(_withdraw_need)
create_accepted_need_successor = frappe.whitelist()(_create_accepted_need_successor)
cancel_accepted_need_successor = frappe.whitelist()(_cancel_accepted_need_successor)
request_withdrawal = frappe.whitelist()(_request_withdrawal)
decide_withdrawal = frappe.whitelist()(_decide_withdrawal)
save_intake_window = frappe.whitelist()(_save_intake_window)
