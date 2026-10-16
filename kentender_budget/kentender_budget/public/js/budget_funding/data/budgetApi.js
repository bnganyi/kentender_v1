import { frappeCall } from "../../budget_shared/data/frappeCall.js";

const APP = "kentender_budget.api.budget_api";
const REF_DATA = "kentender_core.api.reference_data_api";

// BUD-CHG-001 v1.9 — Budget's own workspace is keyed by Fiscal Year alone
// (one site is one Procuring Entity). Every write carries the version's
// optimistic-lock stamp (`expected_modified`) and a client-minted
// `idempotency_key` (§9.3); the server returns typed results, never a modal.
export function getBudgetWorkspace(fiscalYear) {
	return frappeCall(`${APP}.get_budget_workspace`, { fiscal_year: fiscalYear });
}

export function listAvailableFiscalYears() {
	return frappeCall(`${APP}.list_available_fiscal_years`, {});
}

export function resolveBudgetContext(fiscalYear) {
	return frappeCall(`${APP}.resolve_budget_context`, { fiscal_year: fiscalYear });
}

export function getBudgetVersionDraft(budgetVersion) {
	return frappeCall(`${APP}.get_budget_version_draft`, { budget_version: budgetVersion });
}

export function saveBudgetVersionDraft(payload) {
	return frappeCall(`${APP}.save_budget_version_draft`, { payload });
}

export function createBudgetSuccessorVersion(budget, payload) {
	return frappeCall(`${APP}.create_budget_successor_version`, { budget, payload });
}

export function getBudgetVersionLinesEditor(budgetVersion) {
	return frappeCall(`${APP}.get_budget_version_lines_editor`, { budget_version: budgetVersion });
}

export function saveBudgetLinesDraft(payload) {
	return frappeCall(`${APP}.save_budget_lines_draft`, { payload });
}

export function submitBudgetVersion(budgetVersion, expectedModified, idempotencyKey) {
	return frappeCall(`${APP}.submit_budget_version`, {
		payload: { budget_version: budgetVersion, expected_modified: expectedModified, idempotency_key: idempotencyKey },
	});
}

export function listFundingSources() {
	return frappeCall(`${REF_DATA}.list_funding_sources`, {});
}

export function getBudgetDetail(budget) {
	return frappeCall(`${APP}.get_budget_detail`, { budget });
}

export function getBudgetLinesActive(budget) {
	return frappeCall(`${APP}.get_budget_lines_active`, { budget });
}

export function getFundingActivity(budget, budgetLine, eventType) {
	return frappeCall(`${APP}.get_funding_activity`, { budget, budget_line: budgetLine, event_type: eventType });
}

export function getBudgetVersionHistory(budgetVersion) {
	return frappeCall(`${APP}.get_budget_version_history`, { budget_version: budgetVersion });
}

export function getBudgetApprovalTask(budgetVersion) {
	return frappeCall(`${APP}.get_budget_approval_task`, { budget_version: budgetVersion });
}

export function getBudgetApprovalTaskLines(budgetVersion) {
	return frappeCall(`${APP}.get_budget_approval_task_lines`, { budget_version: budgetVersion });
}

export function getBudgetApprovalTaskChanges(budgetVersion) {
	return frappeCall(`${APP}.get_budget_approval_task_changes`, { budget_version: budgetVersion });
}

export function returnBudgetVersion(budgetVersion, returnReason, expectedModified, idempotencyKey) {
	return frappeCall(`${APP}.return_budget_version`, {
		payload: { budget_version: budgetVersion, return_reason: returnReason, expected_modified: expectedModified, idempotency_key: idempotencyKey },
	});
}

export function approveBudgetVersion(budgetVersion, expectedModified, idempotencyKey) {
	return frappeCall(`${APP}.approve_budget_version`, {
		payload: { budget_version: budgetVersion, expected_modified: expectedModified, idempotency_key: idempotencyKey },
	});
}

export function getBudgetLinePosition(budgetLine) {
	return frappeCall(`${APP}.get_budget_line_position`, { budget_line: budgetLine });
}

export function getBudgetClosureStatus(budget) {
	return frappeCall(`${APP}.get_budget_closure_status`, { budget });
}

export function closeBudget(budget, expectedModified, idempotencyKey) {
	return frappeCall(`${APP}.close_budget`, {
		payload: { budget, expected_modified: expectedModified, idempotency_key: idempotencyKey },
	});
}

// BUD-CHG-001 v1.11 §9.2 — the Budget Officer declines a budget revision
// request from Procurement Planning (BUD-DES-19); the reason (10–500
// characters) reaches the Planner through the outcome event.
export function declineBudgetRevisionRequest(budgetRevisionRequest, reason) {
	return frappeCall(`${APP}.decline_budget_revision_request`, {
		payload: { budget_revision_request: budgetRevisionRequest, reason },
	});
}

// BUD-CHG-001 v1.16 §11.22 — contract funding (BUD-DES-21/22) and the correction of a Closed commitment (BUD-DES-20).
export function getContractFunding(request) {
	return frappeCall(`${APP}.get_contract_funding`, { request });
}

export function recordContractEntry(payload) {
	return frappeCall(`${APP}.record_existing_contract_commitment_entry`, { payload });
}

export function submitContractEntry(payload) {
	return frappeCall(`${APP}.submit_existing_contract_commitment_entry`, { payload });
}

export function decideContractEntry(payload) {
	return frappeCall(`${APP}.decide_existing_contract_commitment_entry`, { payload });
}

export function declineContractRequest(payload) {
	return frappeCall(`${APP}.decline_contract_funding_request`, { payload });
}

export function getCommitmentCorrection(commitment, correction) {
	return frappeCall(`${APP}.get_commitment_correction`, { commitment: commitment || "", correction: correction || "" });
}

export function recordCommitmentCorrection(payload) {
	return frappeCall(`${APP}.record_commitment_correction`, { payload });
}

export function decideCommitmentCorrection(payload) {
	return frappeCall(`${APP}.decide_commitment_correction`, { payload });
}
