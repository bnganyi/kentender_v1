// Thin wrapper over kentender_core.api.technical_search. Every authority
// check, matching and ranking rule is applied server-side; this module only
// shapes calls.
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.technical_search.";

export const technicalSearchApi = {
	search: (query, limit) =>
		frappeCall(PREFIX + "search_technical_records", { query: query || "", limit: limit || 25 }),
	resolve: (reference) =>
		frappeCall(PREFIX + "resolve_technical_reference", { reference: reference || "" }),
};
