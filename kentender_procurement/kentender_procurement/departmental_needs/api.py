"""Thin whitelisted boundary for Departmental Needs services."""

import frappe

from kentender_procurement.departmental_needs.services.context import resolve_creation_context
from kentender_procurement.departmental_needs.services.lifecycle import (
	approve_withdrawal as _approve_withdrawal,
	create_need as _create_need,
	request_withdrawal as _request_withdrawal,
	review_need as _review_need,
	submit_need as _submit_need,
	update_need as _update_need,
	withdraw_need as _withdraw_need,
)
from kentender_procurement.departmental_needs.services.workspace import get_need, get_support_need, get_workspace


resolve_creation_context = frappe.whitelist()(resolve_creation_context)
get_workspace = frappe.whitelist()(get_workspace)
get_need = frappe.whitelist()(get_need)
get_support_need = frappe.whitelist()(get_support_need)
create_need = frappe.whitelist()(_create_need)
update_need = frappe.whitelist()(_update_need)
submit_need = frappe.whitelist()(_submit_need)
review_need = frappe.whitelist()(_review_need)
withdraw_need = frappe.whitelist()(_withdraw_need)
request_withdrawal = frappe.whitelist()(_request_withdrawal)
approve_withdrawal = frappe.whitelist()(_approve_withdrawal)
