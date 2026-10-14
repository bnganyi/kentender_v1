# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Finance and stock configuration readiness (CM-CHG-001 v0.8 §17.10 CFG row, FU-CM-48; plan D7).

Contract Management depends on configuration it does not own: two global ERPNext settings, a payable account, a payment mode's account, a
Payment Entry workflow with a separate approver, the contract fields on native documents, and the mapping from the Finance responsibilities
to ERPNext roles. Each gap is returned with the problem in plain words, **who recovers it** and where to fix it, so a screen or a diagnostic
can name the missing mapping instead of failing later inside a native call. Read only: it changes nothing."""

from __future__ import annotations

import frappe

from kentender_contracts.native import fields
from kentender_core.services import business_role_registry as registry

FINANCE_PREPARATION = "Finance preparation"
FINANCE_APPROVAL = "Finance approval"


def gap(key: str, problem: str, owner: str, fix: str) -> dict[str, str]:
	return {"key": key, "problem": problem, "owner": owner, "fix": fix}


def check(company: str, *, mode_of_payment: str = "") -> list[dict[str, str]]:
	gaps: list[dict[str, str]] = []
	absent = fields.missing()
	if absent:
		gaps.append(gap("custom_fields", f"Contract fields are missing on native documents: {', '.join(absent)}.", "Contract Management install", "Run bench migrate for the site."))
	if not frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item"):
		gaps.append(gap("stock_serial_and_batch", "Serial numbers are not enabled for items, so a serialised delivery cannot be received unit by unit.", "Stock configuration owner (CFG)",
			"Stock Settings: Enable Serial and Batch No for Item."))
	if not frappe.db.get_single_value("Accounts Settings", "check_supplier_invoice_uniqueness"):
		gaps.append(gap("invoice_uniqueness", "Supplier invoice numbers are not checked for uniqueness, so a duplicate invoice would not be stopped natively.", "Finance configuration owner",
			"Accounts Settings: Check Supplier Invoice Number Uniqueness."))
	if not frappe.db.get_value("Company", company, "default_payable_account"):
		gaps.append(gap("payable_account", f"{company} has no default payable account, so supplier invoices cannot post.", "Finance configuration owner", f"Company {company}: Default Payable Account."))
	if mode_of_payment and not frappe.db.exists("Mode of Payment Account", {"parent": mode_of_payment, "company": company}):
		gaps.append(gap("payment_mode_account", f"Payment mode '{mode_of_payment}' has no account for {company}, so a payment cannot name the bank account it is paid from.", "Finance configuration owner",
			f"Mode of Payment {mode_of_payment}: add an account for {company}."))
	gaps += _workflow()
	gaps += _roles()
	return gaps


def _workflow() -> list[dict[str, str]]:
	owner = "Finance configuration owner (maker and approver)"
	fix = "Workflow for Payment Entry: an approval step for a separate approver role, with Allow Self Approval off."
	name = frappe.db.get_value("Workflow", {"document_type": "Payment Entry", "is_active": 1}, "name")
	if not name:
		return [gap("payment_workflow", "Payment Entry has no active workflow, so there is no separate approver for a payment.", owner, fix)]
	workflow = frappe.get_doc("Workflow", name)
	submitted = {row.state for row in workflow.states if str(row.doc_status) == "1"}
	approving = [row for row in workflow.transitions if row.next_state in submitted]
	if not approving:
		return [gap("payment_workflow", f"Workflow {name} has no step that approves a payment.", owner, fix)]
	if any(row.allow_self_approval for row in approving):
		return [gap("payment_workflow", f"Workflow {name} lets the person who prepared a payment approve it (self-approval is allowed).", owner, fix)]
	return _mapping(name, workflow, approving)


def _mapping(name: str, workflow, approving) -> list[dict[str, str]]:
	"""The workflow's roles are the registered Finance responsibilities' roles: the maker step to Finance preparation, the approving step to Finance approval,
	and never the same role for both (FU-CM-48). Skipped while the responsibilities are unregistered; `_roles` names that."""
	if not all(registry.is_registered(role) for role in (FINANCE_PREPARATION, FINANCE_APPROVAL)):
		return []
	preparation, approval = set(registry.projected_frappe_roles(FINANCE_PREPARATION)), set(registry.projected_frappe_roles(FINANCE_APPROVAL))
	approving_roles = {row.allowed for row in approving}
	maker_roles = {row.allowed for row in workflow.transitions if row not in approving and row.action not in ("Return", "Reject")}
	problems = []
	if not approving_roles & approval:
		problems.append(f"the approving step is allowed to {', '.join(sorted(approving_roles))}, not to the Finance approval responsibility's role ({', '.join(sorted(approval))})")
	if maker_roles and not maker_roles & preparation:
		problems.append(f"the preparing step is allowed to {', '.join(sorted(maker_roles))}, not to the Finance preparation responsibility's role ({', '.join(sorted(preparation))})")
	if approving_roles & preparation:
		problems.append("the same role can prepare and approve")
	if not problems:
		return []
	return [gap("finance_role_mapping", f"Workflow {name}: " + "; ".join(problems) + ".", "Finance configuration owner with the authorisation owner (System setup assigns the responsibilities)",
		"Workflow transitions: allow the Finance preparation role to prepare and the Finance approval role to approve.")]


def _roles() -> list[dict[str, str]]:
	missing = [role for role in (FINANCE_PREPARATION, FINANCE_APPROVAL) if not registry.is_registered(role)]
	if missing:
		return [gap("auth_roles", f"The Finance responsibilities are not registered: {', '.join(missing)}, so no ERPNext role is mapped to them.", "Authorisation configuration owner",
			"Register the Finance responsibilities in the business role registry.")]
	return []
