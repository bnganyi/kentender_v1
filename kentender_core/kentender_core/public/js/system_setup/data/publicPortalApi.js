// CFG-CHG-002 v0.16 §7 — thin wrappers over kentender_core.api.public_portal_api
// (Supplier portal settings). Every rule is applied server-side; this module
// only shapes calls and mints one idempotency key per save.
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.public_portal_api.";

function newIdempotencyKey() {
	return `portal-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export const publicPortalApi = {
	update: (values, expectedVersion) =>
		frappeCall(PREFIX + "update_public_portal_settings", {
			...values,
			expected_version: expectedVersion,
			idempotency_key: newIdempotencyKey(),
		}),
};
