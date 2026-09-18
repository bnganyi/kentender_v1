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

export function setNeedPlanningDisposition(args) {
	return frappeCall(`${BASE}.set_need_planning_disposition`, args);
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

export function createDepartmentalPlanUpdate(args) {
	return frappeCall(`${BASE}.create_departmental_plan_update`, args);
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

// PLN-CHG-001 v1.23 §7.1/§7.2 — accepted-classification evidence and the
// Planning-owned correction of it. There is deliberately no procurement
// category in the correction payload: the server derives it from the governed
// catalogue and rejects a client-supplied one (§4.4).
export function getAcceptedDppClassification(dppSubmission, dppEntryId = "") {
	return frappeCall(`${BASE}.get_accepted_dpp_classification`, {
		dpp_submission: dppSubmission,
		dpp_entry_id: dppEntryId,
	});
}

export function correctAcceptedRequirementClassification(args) {
	return frappeCall(`${BASE}.correct_accepted_requirement_classification`, args);
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

export function savePlanVersionDetails(args) {
	return frappeCall(`${BASE}.save_plan_version_details`, args);
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

export function getSourceEvidence(task, sourceKey) {
	return frappeCall(`${BASE}.get_source_evidence`, { task, source_key: sourceKey });
}

// A plain authenticated file download (§10.4 **Download review pack**),
// not the JSON API layer — the caller binds this straight to an <a href>.
export function reviewPackDownloadUrl(task) {
	return `/api/method/${BASE}.download_review_pack?task=${encodeURIComponent(task)}`;
}

// --- publication, successors, schedule ----------------------------------

export function getPublicationTask(publication) {
	return frappeCall(`${BASE}.get_publication_task`, { publication });
}

export function retryPublication(args) {
	return frappeCall(`${BASE}.retry_publication`, args);
}

// §5.5.2.3 — reads the authoritative destination result for an attempt whose
// outcome is unknown. It never sets success manually, and an unknown result
// that stays unknown stays held.
export function reconcilePublication(args) {
	return frappeCall(`${BASE}.reconcile_publication`, args);
}

// §5.5.2 / §10.12 — the Accounting Officer's record of what was sent outside
// the system, and the correction of it. A correction supersedes the recorded
// evidence with a reason; it never overwrites it.
export function recordTreasurySubmission(args) {
	return frappeCall(`${BASE}.record_treasury_submission`, args);
}

export function correctTreasurySubmissionEvidence(args) {
	return frappeCall(`${BASE}.correct_treasury_submission_evidence`, args);
}

// §10.14 / §6.3 — why an initial plan only became active after its financial
// year began. Append-only: a later explanation names the one it supersedes
// and neither replaces it nor moves the activation instant.
export function recordLateActivationExplanation(args) {
	return frappeCall(`${BASE}.record_late_activation_explanation`, args);
}

// §5.5.2.4 — the recovery route for an approved plan whose content is
// defective and confirmed not published. Two actors, two commands.
export function requestPlanWithdrawal(args) {
	return frappeCall(`${BASE}.request_plan_withdrawal`, args);
}

export function withdrawApprovedPlanForCorrection(args) {
	return frappeCall(`${BASE}.withdraw_approved_plan_for_correction`, args);
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

// --- progress and correction requests (§10.13, §10.15) -------------------

export function getProcurementProgress(planReference) {
	return frappeCall(`${BASE}.get_procurement_progress`, { plan_reference: planReference || "" });
}

export function getPlanCorrectionRequests(planItemId) {
	return frappeCall(`${BASE}.get_plan_correction_requests`, { plan_item_id: planItemId });
}

// §5.4.5 — the three permitted dispositions of one request. None of them
// revives the stopped downstream work; the requesting module starts fresh.
export function startPlanItemCorrection(args) {
	return frappeCall(`${BASE}.start_plan_item_correction`, args);
}

export function resolvePlanItemCorrectionRequest(args) {
	return frappeCall(`${BASE}.resolve_plan_item_correction_request`, args);
}

export function closePlanItemCorrectionWithoutChange(args) {
	return frappeCall(`${BASE}.close_plan_item_correction_without_change`, args);
}

// PLN-CHG-001 v1.23 §7.5 / §15.3 (PLN23-CHG-001): the MVP registers no
// forecast cascade service, so this adapter carries no entry point to one.
// U15 is deferred and U14 shows approved dates and owner-supplied actuals
// only — there is no "Update expected dates" action to call.
