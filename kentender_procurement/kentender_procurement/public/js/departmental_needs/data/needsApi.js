// Departmental Needs data adapter — NDS-CHG-001 v1.6 §8.
//
// One function per published contract, named after it. Nothing here builds a
// URL by hand or reads a DocType directly: §16.1 requires every mutation to go
// through a command, and every read through a §8.1 contract.
import { frappeCall } from "../../nds_shared/data/frappeCall.js";

const API = "kentender_procurement.departmental_needs.api";

// --- §8.1 reads ------------------------------------------------------------

export const resolveNeedsScope = (args) => frappeCall(`${API}.resolve_needs_scope`, args || {});

export const listNeedsFinancialYears = () => frappeCall(`${API}.list_needs_financial_years`, {});

export const listNeedCreateTargets = () => frappeCall(`${API}.list_need_create_targets`, {});

export const getNeedsWorkspace = (args) => frappeCall(`${API}.get_needs_workspace`, args);

export const getDepartmentalNeed = (need) =>
	frappeCall(`${API}.get_departmental_need`, { need });

export const getDepartmentalReviewTask = (task, decisionToken) =>
	frappeCall(`${API}.get_departmental_review_task`, {
		task,
		decision_token: decisionToken || "",
	});

export const getNeedsSubmissionState = () => frappeCall(`${API}.get_needs_submission_state`, {});

export const getCurrentAcceptedNeed = (args) =>
	frappeCall(`${API}.get_current_accepted_need`, args);

export const checkWithdrawalDependency = (need, acceptedVersion) =>
	frappeCall(`${API}.check_accepted_need_withdrawal_dependency`, {
		need,
		accepted_version: acceptedVersion,
	});

// --- §8.2 commands ---------------------------------------------------------
//
// Every command takes an idempotency key. §12.3 requires one key to be reused
// across retries of the *same* attempt, so the caller creates it once per user
// action (see newIdempotencyKey) rather than per request.

export const saveNeedDraft = (args) => frappeCall(`${API}.save_need_draft`, args);
export const submitNeedVersion = (args) => frappeCall(`${API}.submit_need_version`, args);
export const returnNeedVersion = (args) => frappeCall(`${API}.return_need_version`, args);
export const acceptNeedVersion = (args) => frappeCall(`${API}.accept_need_version`, args);
export const declineNeedVersion = (args) => frappeCall(`${API}.decline_need_version`, args);
export const withdrawUnacceptedNeed = (args) =>
	frappeCall(`${API}.withdraw_unaccepted_need`, args);
export const createAcceptedNeedSuccessor = (args) =>
	frappeCall(`${API}.create_accepted_need_successor`, args);
export const cancelAcceptedNeedSuccessor = (args) =>
	frappeCall(`${API}.cancel_accepted_need_successor`, args);
export const requestAcceptedNeedWithdrawal = (args) =>
	frappeCall(`${API}.request_accepted_need_withdrawal`, args);
export const decideAcceptedNeedWithdrawal = (args) =>
	frappeCall(`${API}.decide_accepted_need_withdrawal`, args);

/**
 * A key for one user action, reused across retries of that same action.
 *
 * §9 makes reuse with a *different* payload NDS_IDEMPOTENCY_CONFLICT, so a new
 * key is minted per attempt, not per screen: retrying the identical request
 * replays, while changing a field and pressing the button again is correctly a
 * new command.
 */
export function newIdempotencyKey(action) {
	const random =
		window.crypto && window.crypto.randomUUID
			? window.crypto.randomUUID()
			: `${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `nds-ui:${action}:${random}`;
}
