# Spike evidence summary

Generated from the JSON files in this folder by `tools/summarise_evidence.py`. Result column: **ok** = the step succeeded; **REFUSED** = it failed with the error shown (usually the refusal the scenario is proving); **fact** = a recorded observation. Environment of each file is on its first line.

## s0_world_before.json

Not a step file (a description or comparison output): see the file.

## s1.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 4 steps

| Step | Result | Detail |
|---|---|---|
| S1.create_po | ok | {"result": "PUR-ORD-2026-00001"} |
| S1.replay_returns_same_po | ok | {"result": "PUR-ORD-2026-00001"} |
| S1.po_facts | fact | {"docstatus": 1, "status": "To Receive and Bill", "grand_total": 1000000.0, "per_received": 0.0, "per_billed": 0.0, "supplier": "CM Spike Supplier", "company": "KenTender", "cm_operation_id… |
| S1.same_document | ok | {"first": "PUR-ORD-2026-00001", "again": "PUR-ORD-2026-00001", "count_with_identity": 1} |

## s2_s3_fixed_asset.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 13 steps

| Step | Result | Detail |
|---|---|---|
| S3.receive_8_of_10_fixed_asset | ok | {"result": "MAT-PRE-2026-00037"} |
| S3.po_after_partial_receipt | fact | {"status": "To Receive and Bill", "per_received": 80.0, "per_billed": 0.0} |
| S3.pr_facts | fact | {"docstatus": 1, "status": "To Bill", "total_qty": 8.0, "grand_total": 800000.0, "per_billed": 0.0} |
| S3.pr_gl | fact | {"gl": [{"account": "1720 - Electronic Equipment - K", "debit": 800000.0, "credit": 0.0, "party": ""}, {"account": "2211 - Asset Received But Not Billed - K", "debit": 0.0, "credit": 800000… |
| S3.stock_ledger_entries_for_fixed_asset_receipt | fact | {"count": 2} |
| S3.assets_from_receipt | fact | {"count": 8, "statuses": ["Draft"], "docstatuses": [0], "first": {"name": "ACC-ASS-2026-00070", "status": "Draft", "docstatus": 0, "net_purchase_amount": 100000.0, "purchase_amount": 100000… |
| S3.assign_unit_references_to_assets | ok | {"result": ["SPIKE-UNIT-001", "SPIKE-UNIT-002", "SPIKE-UNIT-003", "SPIKE-UNIT-004", "SPIKE-UNIT-005", "SPIKE-UNIT-006", "SPIKE-UNIT-007", "SPIKE-UNIT-008"]} |
| S2.replacement_2_units_consume_original_order_quantity | ok | {"result": "MAT-PRE-2026-00038"} |
| S2.po_after_replacement | fact | {"status": "To Bill", "per_received": 100.0, "per_billed": 0.0} |
| S2.native_receipt_of_a_fully_received_order_is_empty | fact | {"items": 0} |
| S2.over_receipt_beyond_order_is_refused | REFUSED | OverAllowanceError: This document is over limit by Qty 1.0 for item CM-SPIKE-LAPTOP-FA. Are you making another Purchase Receipt against the same Purchase Order Item?To allow over receipt / … |
| S3.submit_one_asset_after_receipt_no_second_valuation | ok | {"result": {"asset": "ACC-ASS-2026-00070", "status": "Submitted", "docstatus": 1, "gl": [], "depreciation_rows": 1}} |
| S3.total_gl_for_receipt_vouchers | fact | {"receipts": [{"account": "1720 - Electronic Equipment - K", "debit": 800000.0, "credit": 0.0, "party": ""}, {"account": "2211 - Asset Received But Not Billed - K", "debit": 0.0, "credit": … |

## s2_stock_inspection.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 13 steps

| Step | Result | Detail |
|---|---|---|
| S2.serial_batch_setting | fact | {"before": 0, "during_test": 1} |
| S2.settings_unchanged | fact | {"action_if_quality_inspection_is_not_submitted": "Stop", "action_if_quality_inspection_is_rejected": "Stop"} |
| S2.arrival_creates_no_receipt | fact | {"receipts_for_order": 0, "order": {"per_received": 0.0}} |
| S2.draft_receipt_for_8_accepted_serials | ok | {"result": "MAT-PRE-2026-00063"} |
| S2.submit_receipt_without_a_submitted_inspection_is_stopped | REFUSED | QualityInspectionRequiredError: Row #1: Quality Inspection is required for Item CM-SPIKE-LAPTOP-STK |
| S2.inspection_with_a_failed_criterion | ok | {"result": "MAT-QA-2026-00013"} |
| S2.submit_receipt_pointing_at_a_rejected_inspection_is_stopped | REFUSED | QualityInspectionRejectedError: Row #1: Quality Inspection MAT-QA-2026-00013 was rejected for item CM-SPIKE-LAPTOP-STK |
| S2.inspection_of_the_accepted_subset_all_criteria_met | ok | {"result": "MAT-QA-2026-00014"} |
| S2.submit_receipt_with_the_accepted_inspection | ok | {"result": {"status": "To Bill", "docstatus": 1}} |
| S3.stock_receipt_facts | fact | {"po": {"status": "To Receive and Bill", "per_received": 80.0}, "gl": [{"account": "1410 - Stock In Hand - K", "debit": 800000.0, "credit": 0.0, "party": ""}, {"account": "2210 - Stock Rece… |
| S3.rejected_serials_never_exist | fact | {"rejected_serials_present": []} |
| S2.replacement_2_units_with_their_own_serials | ok | {"result": "MAT-PRE-2026-00064"} |
| S2.replacement_receipt_posts_and_completes_the_order | ok | {"result": {"po_per_received": 100.0}} |

## s3b_missing_serial.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 1 steps

| Step | Result | Detail |
|---|---|---|
| S3b.receipt_row_without_a_serial | ok | {"result": {"submitted": true, "serials_created_without_being_supplied": ["CMSPK-00003"], "row_serial_no_field": null}} |

## s4_invoice.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 11 steps

| Step | Result | Detail |
|---|---|---|
| S4.invoice_for_accepted_8_units | ok | {"result": "ACC-PINV-2026-00001"} |
| S4.pi1_facts | fact | {"docstatus": 1, "status": "Unpaid", "grand_total": 800000.0, "outstanding_amount": 800000.0, "bill_no": "INV-01-v2"} |
| S4.pi1_gl | fact | {"gl": [{"account": "2110 - Creditors - K", "debit": 0.0, "credit": 800000.0, "party": "CM Spike Supplier"}, {"account": "2211 - Asset Received But Not Billed - K", "debit": 800000.0, "cred… |
| S4.after_invoice_1 | fact | {"po": {"status": "To Bill", "per_received": 100.0, "per_billed": 80.0}, "pr1": {"status": "Completed", "per_billed": 100.0}} |
| S4.second_invoice_beyond_received_billed_quantity_is_refused | REFUSED | ValidationError: Over Billing Allowance exceeded for Purchase Receipt Item q4q4a8t6cg (CM-SPIKE-LAPTOP-FA) by 12.000000000000014% |
| S4.invoice_for_the_2_replacement_units | ok | {"result": "ACC-PINV-2026-00002"} |
| S4.after_invoice_2 | fact | {"po": {"status": "Completed", "per_received": 100.0, "per_billed": 100.0}, "pi2": {"grand_total": 200000.0, "outstanding_amount": 200000.0}} |
| S4.credit_note_after_liability_native_return | ok | {"result": {"debit_note": "ACC-PINV-2026-00003", "grand_total": -200000.0, "return_against": "ACC-PINV-2026-00002", "gl": [{"account": "2110 - Creditors - K", "debit": 200000.0, "credit": 0… |
| S4.supplier_invoice_uniqueness_setting_before | fact | {"value": 0} |
| S4.duplicate_bill_no_with_uniqueness_check_off | ok | {"result": "ACC-PINV-2026-00004"} |
| S4.duplicate_bill_no_with_uniqueness_check_on | REFUSED | ValidationError: Supplier Invoice No exists in Purchase Invoice ACC-PINV-2026-00001 |

## s4b_credit_note_net_position.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 3 steps

| Step | Result | Detail |
|---|---|---|
| S4b.invoices | fact | {"ACC-PINV-2026-00001": {"docstatus": 1, "status": "Unpaid", "grand_total": 800000.0, "outstanding_amount": 800000.0, "is_return": 0, "return_against": null, "update_outstanding_for_self": … |
| S4b.payment_ledger_entries | fact | {"rows": [{"voucher_no": "ACC-PINV-2026-00001", "against_voucher_no": "ACC-PINV-2026-00001", "amount": 800000.0, "account_type": "Payable"}, {"voucher_no": "ACC-PINV-2026-00002", "against_v… |
| S4b.supplier_balance_in_ledger | fact | {"gl_balance": -800000.0} |

## s5a_workflow_maker_approver.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 14 steps

| Step | Result | Detail |
|---|---|---|
| S5a.workflow | fact | {"states": [["Draft", "0"], ["Pending Approval", "0"], ["Approved", "1"]], "pe_has_workflow_state_field": true} |
| S5a.maker_creates_payment_draft | ok | {"result": "ACC-PAY-2026-00001"} |
| S5a.maker_submits_for_approval | ok | {"result": {"workflow_state": "Pending Approval", "docstatus": 0}} |
| S5a.maker_cannot_approve_lacking_the_role | REFUSED | WorkflowTransitionError: Not a valid Workflow Action |
| S5a.separate_approver_approves | ok | {"result": {"workflow_state": "Approved", "docstatus": 1}} |
| S5a.payment_posted | fact | {"pe": {"docstatus": 1, "workflow_state": "Approved", "paid_amount": 100000.0, "status": "Submitted"}, "gl": [{"account": "2110 - Creditors - K", "debit": 100000.0, "credit": 0.0, "party": … |
| S5a.dual_role_user_creates_own_payment | ok | {"result": "ACC-PAY-2026-00002"} |
| S5a.own_entry_approval_is_refused_allow_self_approval_off | REFUSED | ValidationError: Self approval is not allowed |
| S5a.draft_for_direct_submit | ok | {"result": "ACC-PAY-2026-00003"} |
| S5a.bypass_doc_submit_by_accounts_manager_in_draft_state | ok | {"result": {"docstatus": 1, "workflow_state": "Approved"}} |
| S5a.entry_after_bypass_attempt | fact | {"docstatus": 1, "workflow_state": "Approved"} |
| S5a.draft_for_api_submit | ok | {"result": "ACC-PAY-2026-00004"} |
| S5a.bypass_desk_savedocs_submit_in_draft_state | ok | {"result": {"docstatus": 1, "workflow_state": "Approved"}} |
| S5a.bypass_doc_submit_by_administrator | ok | {"result": {"docstatus": 1, "workflow_state": "Approved"}} |

## s5b_paths_probe_native_hold.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 8 steps

| Step | Result | Detail |
|---|---|---|
| S5b.probe.direct_entry | ok | {"invoice": "ACC-PINV-2026-00009", "native_hold": true, "result": {"stage_reached": "posted", "payment_entry": "ACC-PAY-2026-00005"}} |
| S5b.probe.direct_entry.events | fact | {"events": ["Payment Entry:before_submit", "Payment Entry:on_submit", "Payment Entry:validate"], "posted": true, "invoice": {"status": "Unpaid", "outstanding_amount": 100000.0, "on_hold": 1… |
| S5b.probe.api_entry | ok | {"invoice": "ACC-PINV-2026-00010", "native_hold": true, "result": {"stage_reached": "posted", "payment_entry": "ACC-PAY-2026-00006"}} |
| S5b.probe.api_entry.events | fact | {"events": ["Payment Entry:before_submit", "Payment Entry:on_submit", "Payment Entry:validate"], "posted": true, "invoice": {"status": "Unpaid", "outstanding_amount": 100000.0, "on_hold": 1… |
| S5b.probe.journal_entry | ok | {"invoice": "ACC-PINV-2026-00011", "native_hold": true, "result": {"stage_reached": "posted", "journal_entry": "ACC-JV-2026-00001", "invoice_outstanding": 0.0}} |
| S5b.probe.journal_entry.events | fact | {"events": ["Journal Entry:before_submit", "Journal Entry:on_submit", "Journal Entry:validate"], "posted": true, "invoice": {"status": "Paid", "outstanding_amount": 0.0, "on_hold": 1}} |
| S5b.probe.reconcile_advance | REFUSED | ValidationError: No records found in Allocation table |
| S5b.probe.reconcile_advance.events | fact | {"events": [], "posted": false, "invoice": {"status": "Unpaid", "outstanding_amount": 100000.0, "on_hold": 1}} |

## s5b_paths_probe_uncertified.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 8 steps

| Step | Result | Detail |
|---|---|---|
| S5b.probe.direct_entry | ok | {"invoice": "ACC-PINV-2026-00013", "native_hold": false, "result": {"stage_reached": "posted", "payment_entry": "ACC-PAY-2026-00008"}} |
| S5b.probe.direct_entry.events | fact | {"events": ["Payment Entry:before_submit", "Payment Entry:on_submit", "Payment Entry:validate"], "posted": true, "invoice": {"status": "Paid", "outstanding_amount": 0.0, "on_hold": 0}} |
| S5b.probe.api_entry | ok | {"invoice": "ACC-PINV-2026-00014", "native_hold": false, "result": {"stage_reached": "posted", "payment_entry": "ACC-PAY-2026-00009"}} |
| S5b.probe.api_entry.events | fact | {"events": ["Payment Entry:before_submit", "Payment Entry:on_submit", "Payment Entry:validate"], "posted": true, "invoice": {"status": "Paid", "outstanding_amount": 0.0, "on_hold": 0}} |
| S5b.probe.journal_entry | ok | {"invoice": "ACC-PINV-2026-00015", "native_hold": false, "result": {"stage_reached": "posted", "journal_entry": "ACC-JV-2026-00002", "invoice_outstanding": 0.0}} |
| S5b.probe.journal_entry.events | fact | {"events": ["Journal Entry:before_submit", "Journal Entry:on_submit", "Journal Entry:validate"], "posted": true, "invoice": {"status": "Paid", "outstanding_amount": 0.0, "on_hold": 0}} |
| S5b.probe.reconcile_advance | ok | {"invoice": "ACC-PINV-2026-00016", "native_hold": false, "result": {"stage_reached": "reconciled", "advance": "ACC-PAY-2026-00010", "counts": {"invoices_listed": 4, "payments_listed": 5, "i… |
| S5b.probe.reconcile_advance.events | fact | {"events": ["Payment Entry:before_update_after_submit", "Payment Entry:on_update_after_submit"], "posted": true, "invoice": {"status": "Paid", "outstanding_amount": 0.0, "on_hold": 0}} |

## s5c_enforce.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 23 steps

| Step | Result | Detail |
|---|---|---|
| S5c.route_direct_entry_outside_the_operation | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.route_direct_entry.state_after | fact | {"invoice": {"status": "Unpaid", "outstanding_amount": 100000.0}, "submitted_payments_added": null, "journal_entries_posted_for_invoice": 0} |
| S5c.route_api_entry_outside_the_operation | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.route_api_entry.state_after | fact | {"invoice": {"status": "Unpaid", "outstanding_amount": 100000.0}, "submitted_payments_added": null, "journal_entries_posted_for_invoice": 0} |
| S5c.route_journal_entry_outside_the_operation | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.route_journal_entry.state_after | fact | {"invoice": {"status": "Unpaid", "outstanding_amount": 100000.0}, "submitted_payments_added": null, "journal_entries_posted_for_invoice": 0} |
| S5c.route_reconcile_advance_outside_the_operation | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.route_reconcile_advance.state_after | fact | {"invoice": {"status": "Unpaid", "outstanding_amount": 100000.0}, "submitted_payments_added": null, "journal_entries_posted_for_invoice": 0} |
| S5c.approve_500k_inside_operation | ok | {"result": {"workflow_state": "Approved", "docstatus": 1}} |
| S5c.approve_300k_inside_operation | ok | {"result": {"workflow_state": "Approved", "docstatus": 1}} |
| S5c.invoice_after_500k_and_300k | fact | {"status": "Paid", "outstanding_amount": 0.0, "cm_certified_amount": 800000.0} |
| S5c.certified_600k_first_500k_inside_operation | ok | {"result": {"workflow_state": "Approved", "docstatus": 1}} |
| S5c.certified_600k_next_200k_exceeds_the_supported_amount_even_though_the_invoice_allows_it | REFUSED | ValidationError: CM_HOLD: ACC-PINV-2026-00022 is certified for 600,000.00, already settled 500,000.00; 200,000.00 exceeds the supported amount. |
| S5c.invoice_after_over_entitlement_attempt | fact | {"status": "Partly Paid", "outstanding_amount": 300000.0, "cm_certified_amount": 600000.0, "second_payment_state": {"docstatus": 0, "workflow_state": "Pending Approval"}} |
| S5c.bypass_direct_submit_by_dual_role_user | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.bypass_direct_submit_by_administrator | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.bypass_desk_savedocs_submit | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.bypass_workflow_approve_outside_the_operation_by_a_separate_approver | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5c.own_entry_approval_inside_the_operation_still_refused | REFUSED | ValidationError: Self approval is not allowed |
| S5c.bypass_target_state | fact | {"docstatus": 0, "workflow_state": "Pending Approval", "invoice": {"status": "Unpaid", "outstanding_amount": 200000.0}} |
| S5c.pending_before_edit | fact | {"workflow_state": "Pending Approval", "paid_amount": 300000.0} |
| S5c.edit_amount_while_pending_returns_the_entry_to_draft | ok | {"result": {"workflow_state_after_save": "Draft", "paid_amount": 400000, "invalidated_fields": ["paid_amount", "received_amount", "references"]}} |
| S5c.approve_after_edit_without_resubmission_is_refused | REFUSED | WorkflowTransitionError: Not a valid Workflow Action |

## s5d_beneficiary_change.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 3 steps

| Step | Result | Detail |
|---|---|---|
| S5d.pending_with_beneficiary_1 | fact | {"workflow_state": "Pending Approval", "party_bank_account": "CM Spike Supplier Account 1 - CM Spike Bank Ltd"} |
| S5d.beneficiary_swapped_while_pending_returns_the_entry_to_draft | ok | {"result": {"workflow_state_after_save": "Draft", "party_bank_account": "CM Spike Supplier Account 2 - CM Spike Bank Ltd", "invalidated_fields": ["party_bank_account"]}} |
| S5d.approve_without_resubmission_is_refused | REFUSED | WorkflowTransitionError: Not a valid Workflow Action |

## s5e_race.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 2 steps

| Step | Result | Detail |
|---|---|---|
| S5e.race_without_row_lock | fact | {"contenders": [{"pe": "ACC-PAY-2026-00019", "ok": true, "result": {"workflow_state": "Approved", "docstatus": 1}, "waited_s": 0.77}, {"pe": "ACC-PAY-2026-00020", "ok": true, "result": {"wo… |
| S5e.race_with_row_lock | fact | {"contenders": [{"pe": "ACC-PAY-2026-00021", "ok": true, "result": {"workflow_state": "Approved", "docstatus": 1}, "waited_s": 0.97}, {"pe": "ACC-PAY-2026-00022", "ok": false, "error": "Val… |

## s5f_background_route.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 2 steps

| Step | Result | Detail |
|---|---|---|
| S5f.background_job_submitting_a_payment_outside_the_operation | REFUSED | PermissionError: CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation. |
| S5f.state_after_job | fact | {"payment": {"docstatus": 0, "workflow_state": "Draft"}, "invoice": {"status": "Unpaid", "outstanding_amount": 100000.0}} |

## s6_signing.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 14 steps

| Step | Result | Detail |
|---|---|---|
| S6.provider_found_through_the_hook | fact | {"hook": ["kentender_procurement.proceedings.test_services.attestation.service"], "provider": "TestAttestationService"} |
| S6.package_digest | fact | {"digest": "b18b637eec8b4f61c4a8bfe79ca6d284d3424a0dbafccf7b79ccd405a4b145ec", "entries": 8} |
| S6.supplier_signs_first | ok | {"result": {"replay": false, "state": "Succeeded", "proof": "TATT-6A62A52A98", "provider_outcome": "Accepted/Verified"}} |
| S6.entity_signs_second_on_the_same_digest | ok | {"result": {"replay": false, "state": "Succeeded", "proof": "TATT-EFE5B5002A", "provider_outcome": "Accepted/Verified"}} |
| S6.replay_of_a_succeeded_signature_does_not_call_the_provider_again | ok | {"result": {"replay": true, "state": "Succeeded", "proof": "TATT-6A62A52A98"}} |
| S6.provider_calls_so_far | fact | {"calls": ["CM-SPIKE-CASE-S6/agreement/1/Signing attempt/supplier", "CM-SPIKE-CASE-S6/agreement/1/Signing attempt/entity", "CM-SPIKE-CASE-S6/agreement/2/Signing attempt/forced-Unavailable",… |
| S6.seam_same_correlation_id_twice | fact | {"first": "TATT-5D383532E2", "second": "TATT-BE5116C939", "same_proof": false, "result_keys": ["label", "method", "outcome", "proof_reference"], "status_or_reconcile_function_on_provider": … |
| S6.outcome_unavailable | ok | {"result": {"replay": false, "state": "Uncertain", "proof": "", "provider_outcome": "Unavailable"}} |
| S6.outcome_indeterminate | ok | {"result": {"replay": false, "state": "Uncertain", "proof": "", "provider_outcome": "Indeterminate"}} |
| S6.outcome_rejected | ok | {"result": {"replay": false, "state": "Failed", "proof": "", "provider_outcome": "Rejected"}} |
| S6.uncertain_attempt_retried_under_the_same_identity | ok | {"result": {"replay": false, "state": "Succeeded", "proof": "TATT-2F292CCF57", "provider_outcome": "Accepted/Verified"}} |
| S6.intent_states | fact | {"rows": [{"identity": "CM-SPIKE-CASE-S7/agreement 1/1/Purchase order/crash-1", "state": "Reconciled", "proof": "PUR-ORD-2026-00028"}, {"identity": "CM-SPIKE-CASE-S6/agreement/1/Signing att… |
| S6.changed_version_changes_the_digest | fact | {"old": "b18b637eec8b4f61c4a8bfe79ca6d284d3424a0dbafccf7b79ccd405a4b145ec", "new": "6dd7164000fb08105aac0900323d432e6053873d69adec32ae86a3f1af1f9318", "different": true} |
| S6.version_1_proofs_remain_bound_to_version_1_only | fact | {"proofs_for_version_1": 2, "proofs_for_version_2": 1} |

## s7a_crash_recovery.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 5 steps

| Step | Result | Detail |
|---|---|---|
| S7a.process_crashed | fact | {"exit_code": 137, "output": ["CRASH native order PUR-ORD-2026-00028 committed; dying before the link is written"]} |
| S7a.state_after_crash | fact | {"orders_with_identity": 1, "intent_state": "Attempting", "link": null} |
| S7a.recovery_reads_the_owner_first_and_links_the_existing_order | ok | {"result": {"order": "PUR-ORD-2026-00028", "created_new_order": false, "intent_state": "Reconciled"}} |
| S7a.second_recovery_is_a_no_op | ok | {"result": {"order": "PUR-ORD-2026-00028", "created_new_order": false, "intent_state": "Reconciled"}} |
| S7a.final | fact | {"orders_with_identity": 1, "intent_state": "Reconciled", "link": "PUR-ORD-2026-00028"} |

## s7b2_cancel_in_the_right_order.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 1 steps

| Step | Result | Detail |
|---|---|---|
| S7b2.cancel_inspection_then_receipt | ok | {"result": {"before": {"sle": 1, "serials": 2, "order_per_received": 100.0}, "after": {"docstatus": 2, "live_sle": 0, "cancelled_sle": 2, "serials": 2, "order_per_received": 0.0, "active_gl… |

## s7b_reversals.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 10 steps

| Step | Result | Detail |
|---|---|---|
| S7b.receipt_posted | fact | {"sle": [{"qty": 2.0, "cancelled": 0}], "serials": ["SPIKE-SN-C01", "SPIKE-SN-C02"]} |
| S7b.cancel_receipt_without_downstream_documents | REFUSED | LinkExistsError: Cannot delete or cancel because Purchase Receipt MAT-PRE-2026-00066 is linked with Quality Inspection MAT-QA-2026-00017  |
| S7b.cancel_receipt_after_invoice_is_refused | REFUSED | ValidationError: Purchase Invoice ACC-PINV-2026-00029 is already submitted |
| S7b.pay_the_invoice_natively | ok | {"result": {"payment_entry": "ACC-PAY-2026-00024", "invoice_status": "Paid"}} |
| S7b.return_one_paid_unit_with_its_serial | ok | {"result": {"return_receipt": "MAT-PRE-2026-00068", "sle": [{"qty": -1.0, "cancelled": 0}], "serial_status": "Delivered"}} |
| S7b.credit_note_for_the_returned_unit | ok | {"result": {"debit_note": "ACC-PINV-2026-00030", "grand_total": -100000.0, "outstanding": -100000.0, "original_outstanding": 0.0, "supplier_balance_in_ledger": -2400000.0, "payment_entries_… |
| S7b.assets_after_receipt | fact | {"assets": ["ACC-ASS-2026-00137", "ACC-ASS-2026-00138"], "docstatus": [0, 0]} |
| S7b.submit_one_asset | ok | {"result": {"asset": "ACC-ASS-2026-00137", "status": "Submitted"}} |
| S7b.cancel_receipt_with_a_submitted_asset_is_refused | REFUSED | ValidationError: Asset Movement ACC-ASM-2026-342710: Submitted Record cannot be deleted. You must  Cancel  it first. |
| S7b.cancel_the_asset_first_then_the_receipt | ok | {"result": {"receipt_docstatus": 2, "assets_left": 0}} |

## s8_template.json

site `kentender-test.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-14 · 6 steps

| Step | Result | Detail |
|---|---|---|
| S8.master_asset_retrievable_and_verifiable | fact | {"path": "02_master/complete_tender.html", "role": "Document master", "size": 202976, "recorded_size": 202976, "recorded_sha256": "97213079bb5cabcf3a0dfcb0142cab5a5c90fe1654ac30080e2839205f… |
| S8.stable_anchors_in_the_master | fact | {"element_ids": 25, "ids": ["tender-document", "decl-reservation", "qualification-requirements", "form-of-tender", "decl-form-of-tender", "decl-citd", "decl-sd1", "decl-sd2", "decl-code-of-… |
| S8.form_no_4_by_its_heading | fact | {"found": true, "bytes": 3170, "blank_fields": 15, "template_placeholders": ["procuring_entity.address", "procuring_entity.name", "tender.reference", "tender.title"], "incorporated_document… |
| S8.missing_heading_would_fail_visibly | fact | {"fails_when_absent": true} |
| S8.html_generation_is_byte_reproducible | fact | {"sha_a": "0efa7f5e2b16e2961210fd5a08c858bd911b4050d95750544625e3ede0206024", "sha_b": "0efa7f5e2b16e2961210fd5a08c858bd911b4050d95750544625e3ede0206024", "identical": true} |
| S8.pdf_generation_through_the_existing_path | fact | {"bytes": 22830, "sha_a": "e512c9d20d3ecc48ab0b56b855094bcc79c069eb36bb395e288b92251e65dedd", "sha_b": "e512c9d20d3ecc48ab0b56b855094bcc79c069eb36bb395e288b92251e65dedd", "identical": true,… |

## s8b_form4_comparison.json

Not a step file (a description or comparison output): see the file.

## s9_independence.json

site `kentender-cm-only.local` · Frappe 16.12.0 · ERPNext 16.10.1 · 2026-10-15 · 5 steps

| Step | Result | Detail |
|---|---|---|
| S9.installed_apps | fact | {"apps": ["frappe", "erpnext", "kentender_core", "kentender_suppliers", "kentender_contracts"], "tendering_apps_present": []} |
| S9.seams_present_on_this_site | fact | {"hooks": {"kt_trust_signing_services": [], "kt_award_contracting_receivers": [], "kt_supplier_account_provider": ["kentender_suppliers.supplier_accounts.services.provider"], "kt_my_work_pr… |
| S9.signing_provider_absent_fails_closed | fact | {"provider": null, "outcome": "Unavailable"} |
| S9.tendering_doctypes_absent_without_error | fact | {"absent": ["Tender", "Bid", "Award Case", "Evaluation Case", "Procurement Commitment", "Funding Reservation"], "present": []} |
| S9.contract_records_work_here | fact | {"case_doctype": true, "supplier_provider_hook_present": true} |

