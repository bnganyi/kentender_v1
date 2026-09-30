// Bid Evaluation data adapter (EVL-CHG-001 v0.4 §7.2, §10). One function per
// endpoint of kentender_procurement.bid_evaluation.api; no other server path.
import { frappeCall } from "./frappeCall.js";

const BASE = "kentender_procurement.bid_evaluation.api";

export function newKey(action) {
	const rand = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `evl-${action}-${rand}`;
}

const get = (method, args) => frappeCall(`${BASE}.${method}`, args, "GET");
const post = (method, args) => frappeCall(`${BASE}.${method}`, args, "POST");

export const getEvaluation = (ref) => get("get_evaluation", { tender_reference: ref });
export const getBid = (ref, bid) => get("get_bid", { tender_reference: ref, bid });
export const getReport = (ref, version = "") => get("get_report", { tender_reference: ref, version });
export const getCommitteeRecord = (ref) => get("get_committee_record", { tender_reference: ref });
export const listWork = (query = "", state = "") => get("list_work", { query, state });
export const getOwnClarification = (ref, clarification, organisation = "") => get("get_own_clarification", { tender_reference: ref, clarification, organisation });
export const heartbeat = (ref) => post("heartbeat", { tender_reference: ref });

export const getCandidates = (ref, purpose) => get("get_candidates", { tender_reference: ref, purpose });

// A command carries a fresh idempotency key, or the caller's own key when it
// reconciles the same attempt (a signature whose proof was unconfirmed).
export function command(method, ref, args, key) {
	return post(method, { tender_reference: ref, idempotency_key: key || newKey(method), ...args });
}

export function evidenceUrl(ref, bid, digest) {
	return `/api/method/${BASE}.get_evidence?tender_reference=${encodeURIComponent(ref)}&bid=${encodeURIComponent(bid)}&digest=${encodeURIComponent(digest)}`;
}
