import { frappeCall } from "../../budget_shared/data/frappeCall.js";

const APP = "kentender_budget.api.budget_api";
const REF_DATA = "kentender_core.api.reference_data_api";

export function getBudgetWorkspace() {
	return frappeCall(`${APP}.get_budget_workspace`, {});
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

export function submitBudgetVersion(budgetVersion) {
	return frappeCall(`${APP}.submit_budget_version`, { payload: { budget_version: budgetVersion } });
}

export function listOrganisationUnits(procuringEntity) {
	return frappeCall(`${REF_DATA}.list_organisation_units`, { procuring_entity: procuringEntity });
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

export function returnBudgetVersion(budgetVersion, returnReason, expectedModified) {
	return frappeCall(`${APP}.return_budget_version`, {
		payload: { budget_version: budgetVersion, return_reason: returnReason, expected_modified: expectedModified },
	});
}

export function approveBudgetVersion(budgetVersion, expectedModified) {
	return frappeCall(`${APP}.approve_budget_version`, {
		payload: { budget_version: budgetVersion, expected_modified: expectedModified },
	});
}

export function getBudgetLinePosition(budgetLine) {
	return frappeCall(`${APP}.get_budget_line_position`, { budget_line: budgetLine });
}
