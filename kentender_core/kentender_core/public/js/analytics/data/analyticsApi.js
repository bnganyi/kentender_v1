// Thin wrapper over kentender_core.api.analytics. Every authority check, count, percentage, label, band,
// date, amount, order and page of rows is made server-side (ANL §7, §16); this module only shapes the
// call. frappeCall is the shared silent:true adapter (AGENTS.md §6.10), so a refusal never raises
// Frappe's own "Message" dialog on top of the screen's own state.
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.analytics.";

export const analyticsApi = {
	// `tab`, `fy`, `dept`, `state` come from the route; `search` and `cursor` are component state and never
	// enter the URL (ANL §9.1). An empty value is sent as an empty string, which the server reads as absent.
	load: ({ tab = "overview", fy = "", dept = "", state = "", search = "", cursor = null } = {}) =>
		frappeCall(PREFIX + "get_procurement_analytics", { tab, fy, dept, state, search, ...(cursor ? { cursor } : {}) }),
	access: () => frappeCall(PREFIX + "get_analytics_access", {}),
};
