// Award data adapter (AWD-CHG-001 v0.4 §7; `reconciliation/command_map.md`).
// One function per endpoint of kentender_procurement.award.api; no other server path.
import { frappeCall } from "./frappeCall.js";

const BASE = "kentender_procurement.award.api";

export function newKey(action) {
	const rand = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
	return `awd-${action}-${rand}`;
}

const get = (method, args) => frappeCall(`${BASE}.${method}`, args, "GET");
const post = (method, args) => frappeCall(`${BASE}.${method}`, args, "POST");

export const getWorkspace = () => get("get_workspace", {});
export const getAward = (award) => get("get_award", { award });
export const getNoticeLetter = (award, notice) => get("get_notice_letter", { award, notice });

// A command carries a fresh idempotency key, or the caller's own key when it
// reconciles the same attempt (a signature whose proof was unconfirmed).
export function command(method, args, key) {
	return post(method, { idempotency_key: key || newKey(method), ...args });
}
