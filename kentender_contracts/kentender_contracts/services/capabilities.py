# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The guarded consequences a hold can block (CM-CHG-001 v0.8 §5.17 "Blocked consequences", §5.18).

A hold never blocks "the contract". It blocks named consequences, and each command declares the consequence it exercises
(Phase 4 onward). The set is closed so a misspelt consequence fails when the hold is built, not silently allows an action.
Factual and protective recording (§5.17: "Factual/protective recording stays possible only within the actor's authority")
is deliberately **not** here: no hold blocks recording a fact, an issue, a supplier claim or a lawfully required
liability. Pure Python, no Frappe: `reconciliation/tools/build_recovery_matrix.py` imports it."""

CAPABILITIES: dict[str, str] = {
	"new_signing_attempt": "Start another signing attempt",
	"activate_contract": "Treat the agreement as in force",
	"convert_funding": "Convert or adjust funding on an assumed effect",
	"create_order": "Create or change the native purchase order on an assumed effect",
	"post_receipt": "Post a native receipt or asset",
	"new_spending": "Begin new supported spending",
	"certify_invoice": "Certify an invoice or claim for payment",
	"certify_advance": "Certify an advance for payment",
	"pay": "Prepare, approve or submit a payment",
	"confirm_settlement": "Confirm that a payment settled",
	"claim_cash_paid": "State that cash was paid",
	"use_goods": "Use or dispose of goods",
	"vary_contract": "Vary, extend or waive a contract term",
	"release_funds": "Release committed funds",
	"mark_financially_finalised": "Show the contract as financially finalised",
	"close_contract": "Sign close-out",
	"close_claim": "Close a warranty claim on a verified remedy",
}
