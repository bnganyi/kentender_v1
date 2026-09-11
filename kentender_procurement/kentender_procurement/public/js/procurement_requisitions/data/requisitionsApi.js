// Procurement Requisitions data adapter (REQ-CHG-001 v1.6 §10). One function
// per published endpoint; no Procuring Entity or Fiscal Year argument
// anywhere (§1.1, §8) — a Requisition's Financial Year is inherited display
// data, never a filter this module accepts.
import { frappeCall } from "../../req_shared/frappeCall.js";

const BASE = "kentender_procurement.procurement_requisitions.api";

export function newIdempotencyKey(action) {
	const rand =
		(crypto.randomUUID && crypto.randomUUID()) ||
		`${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `req-${action}-${rand}`;
}

// --- §10.1 reads -----------------------------------------------------------

export function getRequisitionWorkspace() {
	return frappeCall(`${BASE}.get_requisition_workspace`, {});
}

export function getEligiblePlanItemDetail(planItemId) {
	return frappeCall(`${BASE}.get_eligible_plan_item_detail`, { plan_item_id: planItemId });
}

export function getRequisitionEditor(requisition) {
	return frappeCall(`${BASE}.get_requisition_editor`, { requisition });
}

export function getDepartmentApprovalTask(task) {
	return frappeCall(`${BASE}.get_department_approval_task`, { task });
}

export function getProcurementAuthorisationTask(task) {
	return frappeCall(`${BASE}.get_procurement_authorisation_task`, { task });
}

export function getAuthorisedRequisitionHandoff(requisition) {
	return frappeCall(`${BASE}.get_authorised_requisition_handoff`, { requisition });
}

export function getRequisitionHistory(requisition) {
	return frappeCall(`${BASE}.get_requisition_history`, { requisition });
}

// --- §10.2 commands — Draft stage ------------------------------------------

export function prepareItEquipmentRequisition(args) {
	return frappeCall(`${BASE}.prepare_it_equipment_requisition`, args);
}

export function saveRequisitionSummary(args) {
	return frappeCall(`${BASE}.save_requisition_summary`, args);
}

export function addRequisitionItem(args) {
	return frappeCall(`${BASE}.add_requisition_item`, args);
}

export function updateRequisitionItem(args) {
	return frappeCall(`${BASE}.update_requisition_item`, args);
}

export function removeRequisitionItem(args) {
	return frappeCall(`${BASE}.remove_requisition_item`, args);
}

export function addTechnicalRequirement(args) {
	return frappeCall(`${BASE}.add_technical_requirement`, args);
}

export function updateTechnicalRequirement(args) {
	return frappeCall(`${BASE}.update_technical_requirement`, args);
}

export function removeTechnicalRequirement(args) {
	return frappeCall(`${BASE}.remove_technical_requirement`, args);
}

export function confirmProposedRequirement(args) {
	return frappeCall(`${BASE}.confirm_proposed_requirement`, args);
}

export function saveWarrantyAndSupport(args) {
	return frappeCall(`${BASE}.save_warranty_and_support`, args);
}

export function addRelatedService(args) {
	return frappeCall(`${BASE}.add_related_service`, args);
}

export function updateRelatedService(args) {
	return frappeCall(`${BASE}.update_related_service`, args);
}

export function removeRelatedService(args) {
	return frappeCall(`${BASE}.remove_related_service`, args);
}

export function addAcceptanceRequirement(args) {
	return frappeCall(`${BASE}.add_acceptance_requirement`, args);
}

export function updateAcceptanceRequirement(args) {
	return frappeCall(`${BASE}.update_acceptance_requirement`, args);
}

export function removeAcceptanceRequirement(args) {
	return frappeCall(`${BASE}.remove_acceptance_requirement`, args);
}

export function addSupportingMaterial(args) {
	return frappeCall(`${BASE}.add_supporting_material`, args);
}

export function updateSupportingMaterial(args) {
	return frappeCall(`${BASE}.update_supporting_material`, args);
}

export function removeSupportingMaterial(args) {
	return frappeCall(`${BASE}.remove_supporting_material`, args);
}

export function validateRequisition(requisition) {
	return frappeCall(`${BASE}.validate_requisition`, { requisition });
}

// --- §10.2 commands — Lifecycle ---------------------------------------------

export function sendForDepartmentApproval(args) {
	return frappeCall(`${BASE}.send_for_department_approval`, args);
}

export function returnToDepartmentAuthor(args) {
	return frappeCall(`${BASE}.return_to_department_author`, args);
}

export function submitRequisitionToProcurement(args) {
	return frappeCall(`${BASE}.submit_requisition_to_procurement`, args);
}

export function returnRequisitionToDepartment(args) {
	return frappeCall(`${BASE}.return_requisition_to_department`, args);
}

export function withdrawRequisition(args) {
	return frappeCall(`${BASE}.withdraw_requisition`, args);
}

export function requestUpstreamPlanCorrection(args) {
	return frappeCall(`${BASE}.request_upstream_plan_correction`, args);
}

export function changeLeadOrganisationUnit(args) {
	return frappeCall(`${BASE}.change_lead_organisation_unit`, args);
}

// --- §10.2 commands — Authorisation, revocation, Tender consumption --------

export function authoriseRequisition(args) {
	return frappeCall(`${BASE}.authorise_requisition`, args);
}

export function revokeUnconsumedAuthorisation(args) {
	return frappeCall(`${BASE}.revoke_unconsumed_authorisation`, args);
}

export function recordHandoffConsumption(args) {
	return frappeCall(`${BASE}.record_handoff_consumption`, args);
}
