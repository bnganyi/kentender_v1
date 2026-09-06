// Procurement Planning data adapter (PLN-CHG-001 v1.12 §8). One function per
// published endpoint; no Procuring Entity argument anywhere (§10, §16.2).
import { frappeCall } from "../../pln_shared/frappeCall.js";

const BASE = "kentender_procurement.procurement_planning.api";

export function newIdempotencyKey(action) {
	const rand =
		(crypto.randomUUID && crypto.randomUUID()) ||
		`${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `pln-${action}-${rand}`;
}

// --- context -------------------------------------------------------------

export function getPlanningWorkspace(args) {
	return frappeCall(`${BASE}.get_planning_workspace`, args || {});
}

export function selectPlanningContext(args) {
	return frappeCall(`${BASE}.select_planning_context`, args);
}

export function resetPlanningContext() {
	return frappeCall(`${BASE}.reset_planning_context`, {});
}

export function getRegulatoryReference(fiscalYear) {
	return frappeCall(`${BASE}.get_regulatory_reference`, { fiscal_year: fiscalYear });
}

// --- departmental plan ---------------------------------------------------

export function openDepartmentalPlan(args) {
	return frappeCall(`${BASE}.open_departmental_plan`, args);
}

export function getDepartmentalPlan(dppReference) {
	return frappeCall(`${BASE}.get_departmental_plan`, { dpp_reference: dppReference });
}

export function getDppEntryEditor(dppReference, entryId) {
	return frappeCall(`${BASE}.get_dpp_entry_editor`, {
		dpp_reference: dppReference,
		...(entryId ? { entry_id: entryId } : {}),
	});
}

export function saveNeedFunding(args) {
	return frappeCall(`${BASE}.save_need_funding`, args);
}

export function saveDirectRequirement(args) {
	return frappeCall(`${BASE}.save_direct_requirement`, args);
}

export function removeDirectRequirement(args) {
	return frappeCall(`${BASE}.remove_direct_requirement`, args);
}

export function submitDepartmentalPlan(args) {
	return frappeCall(`${BASE}.submit_departmental_plan`, args);
}

// --- validation ----------------------------------------------------------

export function getDppValidationTask(task) {
	return frappeCall(`${BASE}.get_dpp_validation_task`, { task });
}

export function acceptDepartmentalPlan(args) {
	return frappeCall(`${BASE}.accept_departmental_plan`, args);
}

export function returnDepartmentalPlan(args) {
	return frappeCall(`${BASE}.return_departmental_plan`, args);
}

// --- annual plan + plan items -------------------------------------------

export function getAnnualPlan(planReference) {
	return frappeCall(`${BASE}.get_annual_plan`, { plan_reference: planReference });
}

export function getPlanItem(planItemId) {
	return frappeCall(`${BASE}.get_plan_item`, { plan_item_id: planItemId });
}

export function formPlanItems(args) {
	return frappeCall(`${BASE}.form_plan_items`, args);
}

export function dissolvePlanItem(args) {
	return frappeCall(`${BASE}.dissolve_plan_item`, args);
}

export function savePlanItem(args) {
	return frappeCall(`${BASE}.save_plan_item`, args);
}

export function confirmSplittingAdvisory(args) {
	return frappeCall(`${BASE}.confirm_splitting_advisory`, args);
}

// --- plan-level finance (§5.2, one task per Version) --------------------

export function requestPlanFundingConfirmation(args) {
	return frappeCall(`${BASE}.request_plan_funding_confirmation`, args);
}

export function getFinanceTask(task) {
	return frappeCall(`${BASE}.get_finance_task`, { task });
}

export function confirmPlanFunding(args) {
	return frappeCall(`${BASE}.confirm_plan_funding`, args);
}

export function returnFromFinance(args) {
	return frappeCall(`${BASE}.return_from_finance`, args);
}

// --- governance ----------------------------------------------------------

export function submitConsolidatedPlan(args) {
	return frappeCall(`${BASE}.submit_consolidated_plan`, args);
}

export function submitCorrectedPlan(args) {
	return frappeCall(`${BASE}.submit_corrected_plan`, args);
}

export function getPlanGovernanceTask(task) {
	return frappeCall(`${BASE}.get_plan_governance_task`, { task });
}

export function adoptAndSubmitPlan(args) {
	return frappeCall(`${BASE}.adopt_and_submit_plan`, args);
}

export function approveAnnualPlan(args) {
	return frappeCall(`${BASE}.approve_annual_plan`, args);
}

export function returnPlanVersion(args) {
	return frappeCall(`${BASE}.return_plan_version`, args);
}

// --- publication, successors, schedule ----------------------------------

export function getPublicationTask(publication) {
	return frappeCall(`${BASE}.get_publication_task`, { publication });
}

export function retryPublication(args) {
	return frappeCall(`${BASE}.retry_publication`, args);
}

export function beginPlanUpdate(args) {
	return frappeCall(`${BASE}.begin_plan_update`, args);
}

export function removePlanItemInSuccessor(args) {
	return frappeCall(`${BASE}.remove_plan_item_in_successor`, args);
}

export function cancelPlanUpdate(args) {
	return frappeCall(`${BASE}.cancel_plan_update`, args);
}

export function previewForecastCascade(args) {
	return frappeCall(`${BASE}.preview_forecast_cascade`, args);
}

export function confirmForecastCascade(args) {
	return frappeCall(`${BASE}.confirm_forecast_cascade`, args);
}
