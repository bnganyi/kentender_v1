// Procurement Planning data adapter (PLN-CHG-001 v1.2 §8).
import { frappeCall } from "../../pln_shared/frappeCall.js";

const BASE = "kentender_procurement.procurement_planning.api";

export function newIdempotencyKey(action) {
	const rand =
		(crypto.randomUUID && crypto.randomUUID()) ||
		`${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `pln-${action}-${rand}`;
}

export function getPlanningWorkspace(args) {
	return frappeCall(`${BASE}.get_planning_workspace`, args || {});
}

export function selectPlanningContext(args) {
	return frappeCall(`${BASE}.select_planning_context`, args);
}

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

export function submitDepartmentalPlan(args) {
	return frappeCall(`${BASE}.submit_departmental_plan`, args);
}

export function removeDirectRequirement(args) {
	return frappeCall(`${BASE}.remove_direct_requirement`, args);
}

export function getDppValidationTask(task) {
	return frappeCall(`${BASE}.get_dpp_validation_task`, { task });
}

export function acceptDepartmentalPlan(args) {
	return frappeCall(`${BASE}.accept_departmental_plan`, args);
}

export function returnDepartmentalPlan(args) {
	return frappeCall(`${BASE}.return_departmental_plan`, args);
}

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

export function requestFinanceConfirmation(args) {
	return frappeCall(`${BASE}.request_finance_confirmation`, args);
}

export function getFinanceTask(task) {
	return frappeCall(`${BASE}.get_finance_task`, { task });
}

export function confirmFunding(args) {
	return frappeCall(`${BASE}.confirm_funding`, args);
}

export function returnFromFinance(args) {
	return frappeCall(`${BASE}.return_from_finance`, args);
}
