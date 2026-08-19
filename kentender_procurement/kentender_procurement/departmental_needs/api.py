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


for _fn in (
	resolve_creation_context, get_workspace, get_need, get_support_need,
	_create_need, _update_need, _submit_need, _review_need, _withdraw_need,
	_request_withdrawal, _approve_withdrawal,
):
	frappe.whitelist()(_fn)

create_need = _create_need
update_need = _update_need
submit_need = _submit_need
review_need = _review_need
withdraw_need = _withdraw_need
request_withdrawal = _request_withdrawal
approve_withdrawal = _approve_withdrawal
