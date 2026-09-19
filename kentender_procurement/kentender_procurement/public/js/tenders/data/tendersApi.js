// Tenders data adapter (TPR-CHG-001 v0.8 §7). One function per published
// endpoint of kentender_procurement.tenders.api; no other server path.
import { frappeCall } from "../../tnd_shared/frappeCall.js";

const BASE = "kentender_procurement.tenders.api";

export function newIdempotencyKey(action) {
	const rand = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `tnd-${action}-${rand}`;
}

// --- §7.1 reads -----------------------------------------------------------

export function getTendersWorkspace(filters) {
	return frappeCall(`${BASE}.get_tenders_workspace`, filters || {});
}
export function getTenderStart(handoff) {
	return frappeCall(`${BASE}.get_tender_start`, { handoff });
}
export function getTender(tender) {
	return frappeCall(`${BASE}.get_tender`, { tender });
}
export function getTenderReview(tender) {
	return frappeCall(`${BASE}.get_tender_review`, { tender });
}
export function getTenderHistory(tender) {
	return frappeCall(`${BASE}.get_tender_history`, { tender });
}
export function getTenderPublication(tender) {
	return frappeCall(`${BASE}.get_tender_publication`, { tender });
}
export function getTenderDocument(digest, audience) {
	return frappeCall(`${BASE}.get_tender_document`, { digest, audience: audience || "Internal" });
}
export function previewTenderDocuments(tender) {
	return frappeCall(`${BASE}.preview_tender_documents`, { tender });
}
export function getTenderAddendum(tender, addendum) {
	return frappeCall(`${BASE}.get_tender_addendum`, { tender, addendum: addendum || "" });
}
export function getAddendumInquiry(tender, inquiry) {
	return frappeCall(`${BASE}.get_addendum_inquiry`, { tender, inquiry });
}
export function getTenderCancellation(tender) {
	return frappeCall(`${BASE}.get_tender_cancellation`, { tender });
}
export function getTenderSubmissionHandoff(tender) {
	return frappeCall(`${BASE}.get_tender_submission_handoff`, { tender });
}

// --- §7.2 preparation and approval ---------------------------------------

export const startTender = (args) => frappeCall(`${BASE}.start_tender`, args);
export const saveTenderDraft = (args) => frappeCall(`${BASE}.save_tender_draft`, args);
export const addTenderEvidenceRequirement = (args) => frappeCall(`${BASE}.add_tender_evidence_requirement`, args);
export const updateTenderEvidenceRequirement = (args) => frappeCall(`${BASE}.update_tender_evidence_requirement`, args);
export const removeTenderEvidenceRequirement = (args) => frappeCall(`${BASE}.remove_tender_evidence_requirement`, args);
export const submitTenderForApproval = (args) => frappeCall(`${BASE}.submit_tender_for_approval`, args);
export const returnTenderForCorrection = (args) => frappeCall(`${BASE}.return_tender_for_correction`, args);
export const approveTenderPackage = (args) => frappeCall(`${BASE}.approve_tender_package`, args);
export const reopenApprovedTender = (args) => frappeCall(`${BASE}.reopen_approved_tender`, args);
export const requestRequisitionCorrection = (args) => frappeCall(`${BASE}.request_requisition_correction`, args);
export const startCorrectedTenderVersion = (args) => frappeCall(`${BASE}.start_corrected_tender_version`, args);

// --- §7.3 publication -----------------------------------------------------

export const authoriseTenderPublication = (args) => frappeCall(`${BASE}.authorise_tender_publication`, args);
export const confirmPublicationChannel = (args) => frappeCall(`${BASE}.confirm_publication_channel`, args);
export const withdrawPublicationAuthorisation = (args) => frappeCall(`${BASE}.withdraw_publication_authorisation`, args);

// --- §7.4 open period and cancellation -----------------------------------

export const createAddendumDraft = (args) => frappeCall(`${BASE}.create_addendum_draft`, args);
export const updateAddendumDraft = (args) => frappeCall(`${BASE}.update_addendum_draft`, args);
export const submitAddendumForIssue = (args) => frappeCall(`${BASE}.submit_addendum_for_issue`, args);
export const returnAddendumForCorrection = (args) => frappeCall(`${BASE}.return_addendum_for_correction`, args);
export const issueAddendum = (args) => frappeCall(`${BASE}.issue_addendum`, args);
export const confirmAddendumPublicationChannel = (args) => frappeCall(`${BASE}.confirm_addendum_publication_channel`, args);
export const respondToAddendumInquiry = (args) => frappeCall(`${BASE}.respond_to_addendum_inquiry`, args);
export const recommendTenderCancellation = (args) => frappeCall(`${BASE}.recommend_tender_cancellation`, args);
export const cancelTender = (args) => frappeCall(`${BASE}.cancel_tender`, args);
export const recordCancellationComplianceEvidence = (args) => frappeCall(`${BASE}.record_cancellation_compliance_evidence`, args);
