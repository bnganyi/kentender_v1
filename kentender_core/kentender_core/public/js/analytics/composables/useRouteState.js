import { onActivated, onDeactivated, onMounted, onUnmounted, ref } from "vue";

// ANL-CHG-001 v0.8 §9.1 and docs/mvp-1-r1/19_analytics/reconciliation/route_spike.md (binding).
//
// The tab is a path segment: /desk/analytics[/<tab>]. The applied filters are the query string: `fy`,
// `dept` and `state`, absent meaning all. Frappe's `set_route` drops the query string and
// `frappe.route_options` keeps stale keys across Back and Forward, so this page writes its own history
// entries (history.pushState, then frappe.router.route()) and reads the filters ONLY from
// location.search, again on every route change. Search text and the paging cursor never enter the URL.
//
// `kentender_core.desk_page.useRoute` still owns the one frappe.router listener, the pause while the page
// is hidden and the `epoch` that ticks when the page is shown again on the same route (AGENTS.md §6.4).
// It compares the route *path* only, so a change of query alone (Apply filters, Back to an earlier
// filter) is followed here through `go()`, a popstate listener and `sync()`.

const PAGE_SLUG = "analytics";
const DEFAULT_TAB = "overview";
export const TAB_KEYS = ["overview", "needs", "departmental-planning", "annual-planning", "requisitions", "tender-proceedings"];

/** `desk` or `app`: the first segment of the current path, never hard-coded (route_spike.md, 16). */
export function pathPrefix(pathname = window.location.pathname) {
	const first = String(pathname || "").split("/").filter(Boolean)[0];
	return first === "app" || first === "desk" ? first : "desk";
}

/** The route state held in the address bar right now: the tab from the path, the filters from location.search. */
export function readUrl(location = window.location) {
	const parts = String(location.pathname || "").split("/").filter(Boolean);
	const at = parts.indexOf(PAGE_SLUG);
	const segment = at >= 0 && parts[at + 1] ? safeDecode(parts[at + 1]) : DEFAULT_TAB;
	const tab = TAB_KEYS.includes(segment) ? segment : DEFAULT_TAB;
	const query = new URLSearchParams(location.search || "");
	const state = { onPage: at >= 0, tab, fy: query.get("fy") || "", dept: query.get("dept") || "", state: query.get("state") || "" };
	state.key = [state.tab, state.fy, state.dept, state.state].join("|");
	return state;
}

function safeDecode(value) {
	try {
		return decodeURIComponent(value);
	} catch (error) {
		return value;
	}
}

/** The address for a tab with its applied filters; an absent filter is not written. */
export function buildUrl({ tab = DEFAULT_TAB, fy = "", dept = "", state = "" } = {}, prefix = pathPrefix()) {
	const path = "/" + prefix + "/" + PAGE_SLUG + (tab && tab !== DEFAULT_TAB ? "/" + encodeURIComponent(tab) : "");
	const query = new URLSearchParams();
	if (fy) query.set("fy", fy);
	if (dept) query.set("dept", dept);
	if (state) query.set("state", state);
	const text = query.toString();
	return text ? path + "?" + text : path;
}

/** The address of an owner record route (the route array a payload carries), for a real href. */
export function recordHref(route) {
	return "/" + pathPrefix() + "/" + (route || []).map((part) => encodeURIComponent(part)).join("/");
}

export function useRouteState() {
	const { route, epoch } = kentender_core.desk_page.useRoute({ ref, onMounted, onUnmounted, onActivated, onDeactivated }, PAGE_SLUG);
	const url = ref(readUrl());

	// Follow the address bar. Only an address that is this page's own is read (a Back to another page is
	// that page's); returns true when the tab or a filter changed.
	function sync() {
		const next = readUrl();
		if (!next.onPage || next.key === url.value.key) return false;
		url.value = next;
		return true;
	}

	// Every navigation of the page: a new history entry, then Frappe's router so the page is shown and the
	// route listeners hear it. Returns false when the address would not change (nothing to push).
	function go(change, { replace = false } = {}) {
		const target = { ...url.value, ...change };
		const href = buildUrl(target);
		if (href === window.location.pathname + window.location.search) return false;
		window.history[replace ? "replaceState" : "pushState"](null, "", href);
		frappe.router.route();
		sync();
		return true;
	}

	// Back and Forward: the browser moved before Frappe routes, so re-read the query string right away.
	const onPop = () => {
		sync();
	};
	onMounted(() => window.addEventListener("popstate", onPop));
	onUnmounted(() => window.removeEventListener("popstate", onPop));

	return { url, route, epoch, go, sync };
}
