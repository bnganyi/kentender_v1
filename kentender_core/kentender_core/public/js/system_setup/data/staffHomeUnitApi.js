// CFG-CHG-002 v0.19 §7 — thin wrappers over kentender_core.api.staff_home_unit_api
// (the Staff home units tab, AUTH-ADR-001 v1.12 AUTH-DES-10 and AUTH-DES-11).
// Every rule is applied server-side; this module only shapes calls. The unit
// choices, the Not recorded state and the record token all come from the server.
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.staff_home_unit_api.";

export function newIdempotencyKey() {
	return `home-unit-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export const staffHomeUnitApi = {
	list: ({ search = "", notRecorded = false } = {}) =>
		frappeCall(PREFIX + "staff_home_units", { search: search || null, not_recorded: notRecorded ? 1 : 0, page_length: 1000 }),
	set: (user, organisationUnit, expectedToken, idempotencyKey) =>
		frappeCall(PREFIX + "set_staff_home_unit", {
			user,
			organisation_unit: organisationUnit || "",
			expected_token: expectedToken,
			idempotency_key: idempotencyKey,
		}),
};
