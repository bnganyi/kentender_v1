// Tender Preparation data adapter (TPR-CHG-001 v0.6 §11). One function per
// published endpoint; no Procuring Entity or Fiscal Year argument anywhere
// (§5, TPR-AC-030).
import { frappeCall } from "../../tpr_shared/frappeCall.js";

const BASE = "kentender_procurement.tender_preparation.api";

export function newIdempotencyKey(action) {
	const rand = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `tpr-${action}-${rand}`;
}

// --- §11.1 reads -----------------------------------------------------------
export function getTenderPreparationWorkspace() {
	return frappeCall(`${BASE}.get_tender_preparation_workspace`, {});
}
export function getTenderCompatibility(handoff) {
	return frappeCall(`${BASE}.get_tender_compatibility`, { handoff });
}
export function getTenderEditor(tender) {
	return frappeCall(`${BASE}.get_tender_editor`, { tender });
}
export function getTenderApprovalTask(task) {
	return frappeCall(`${BASE}.get_tender_approval_task`, { task });
}
export function getApprovedTender(tender) {
	return frappeCall(`${BASE}.get_approved_tender`, { tender });
}
export function getTenderHistory(tender) {
	return frappeCall(`${BASE}.get_tender_history`, { tender });
}
export function getTenderPreview(tender, output) {
	return frappeCall(`${BASE}.get_tender_preview`, { tender, output });
}

// --- §11.2 commands --------------------------------------------------------
export function prepareTender(args) {
	return frappeCall(`${BASE}.prepare_tender`, args);
}
export function saveTenderDraft(args) {
	return frappeCall(`${BASE}.save_tender_draft`, args);
}
export function addTenderEvidenceRequirement(args) {
	return frappeCall(`${BASE}.add_tender_evidence_requirement`, args);
}
export function updateTenderEvidenceRequirement(args) {
	return frappeCall(`${BASE}.update_tender_evidence_requirement`, args);
}
export function removeTenderEvidenceRequirement(args) {
	return frappeCall(`${BASE}.remove_tender_evidence_requirement`, args);
}
export function runTenderReadiness(args) {
	return frappeCall(`${BASE}.run_tender_readiness`, args);
}
export function submitTenderForApproval(args) {
	return frappeCall(`${BASE}.submit_tender_for_approval`, args);
}
export function returnTenderForCorrection(args) {
	return frappeCall(`${BASE}.return_tender_for_correction`, args);
}
export function approveTenderForPublication(args) {
	return frappeCall(`${BASE}.approve_tender_for_publication`, args);
}
export function reopenApprovedTender(args) {
	return frappeCall(`${BASE}.reopen_approved_tender`, args);
}
export function requestTenderUpstreamCorrection(args) {
	return frappeCall(`${BASE}.request_tender_upstream_correction`, args);
}
