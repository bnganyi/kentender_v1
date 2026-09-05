// Thin wrappers over kentender_core.api.site_configuration_api. Every rule —
// authority, validation, version checks, the single-open-year invariant and
// the add-year preview — is applied server-side; this module only shapes calls.
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.site_configuration_api.";

function newIdempotencyKey(prefix) {
	return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export const siteConfigApi = {
	getConfiguration: () => frappeCall(PREFIX + "get_system_setup_workspace", {}),
	configure: (payload) =>
		frappeCall(PREFIX + "configure_procuring_entity", {
			...payload,
			idempotency_key: newIdempotencyKey("cfg"),
		}),
	update: (payload, expectedVersion) =>
		frappeCall(PREFIX + "update_procuring_entity", {
			payload: JSON.stringify(payload),
			expected_version: expectedVersion || null,
		}),
	listFiscalYears: () => frappeCall(PREFIX + "list_fiscal_years", {}),
	previewFiscalYear: (startYear) =>
		frappeCall(PREFIX + "preview_fiscal_year", { start_year: startYear }),
	addFiscalYear: (startYear) =>
		frappeCall(PREFIX + "add_fiscal_year", {
			start_year: startYear,
			idempotency_key: newIdempotencyKey("fy"),
		}),
	openNeedsSubmission: (fiscalYear, closesAt, reason, expectedVersion) =>
		frappeCall(PREFIX + "open_needs_submission", {
			fiscal_year: fiscalYear,
			closes_at: closesAt || null,
			reason: reason || null,
			expected_version: expectedVersion || null,
			idempotency_key: newIdempotencyKey("intake"),
		}),
	closeNeedsSubmission: (fiscalYear, reason, expectedVersion) =>
		frappeCall(PREFIX + "close_needs_submission", {
			fiscal_year: fiscalYear,
			reason: reason || null,
			expected_version: expectedVersion || null,
			idempotency_key: newIdempotencyKey("intake"),
		}),
	repairRoot: () =>
		frappeCall(PREFIX + "repair_organisation_root", {
			idempotency_key: newIdempotencyKey("root"),
		}),
};
