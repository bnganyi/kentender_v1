// Bid Opening data adapter (BOP-CHG-001 v0.10 §7, §11). One function per
// endpoint of kentender_procurement.bid_opening.api; no other server path.
import { frappeCall } from "./frappeCall.js";

const BASE = "kentender_procurement.bid_opening.api";

export function newKey(action) {
	const rand = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `bop-${action}-${rand}`;
}

const get = (method, args) => frappeCall(`${BASE}.${method}`, args, "GET");
const post = (method, args) => frappeCall(`${BASE}.${method}`, args, "POST");

export const getOpening = (ref) => get("get_opening", { tender_reference: ref });
export const heartbeat = (ref) => post("heartbeat", { tender_reference: ref });

export function command(method, ref, args) {
	return post(method, { tender_reference: ref, idempotency_key: newKey(method), ...args });
}

export const exportOpening = (ref) => get("export_opening", { tender_reference: ref });

export function pagesUrl(ref, kind, id) {
	const method = kind === "bid" ? "get_bid_pages" : "get_record_pages";
	const param = kind === "bid" ? "entry" : "minutes_version";
	return `/api/method/${BASE}.${method}?tender_reference=${encodeURIComponent(ref)}&${param}=${encodeURIComponent(id)}`;
}
