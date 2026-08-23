import { ref, onMounted, onUnmounted } from "vue";

const PAGE_SLUG = "reference-data";
const TABS = ["pe", "fy", "context"];
const DEFAULT_TAB = "pe";

// route: ["reference-data"] -> {tab: "pe", view: "list"}
// route: ["reference-data", "fy"] -> {tab: "fy", view: "list"}
// route: ["reference-data", "fy", "new"] -> {tab: "fy", view: "new"}
// route: ["reference-data", "fy", "FY-2027-2028"] -> {tab: "fy", view: "detail", code: "FY-2027-2028"}
function readRoute() {
	const route = frappe.get_route() || [];
	const tab = TABS.includes(route[1]) ? route[1] : DEFAULT_TAB;
	const second = route.length > 2 ? String(route[2]).trim() : "";
	if (!second) return { tab, view: "list", code: null };
	if (second === "new") return { tab, view: "new", code: null };
	return { tab, view: "detail", code: second };
}

export function useRouteState() {
	const state = ref(readRoute());

	function goToTab(tab) {
		if (!TABS.includes(tab)) return;
		frappe.set_route(PAGE_SLUG, tab);
	}
	function openRecord(tab, code) {
		frappe.set_route(PAGE_SLUG, tab, code);
	}
	function openNew(tab) {
		frappe.set_route(PAGE_SLUG, tab, "new");
	}
	function closeToList(tab) {
		frappe.set_route(PAGE_SLUG, tab || state.value.tab);
	}

	// frappe.router.off() is a confirmed no-op (see AGENTS.md §6.4 / the pilot's
	// useRouteState.js for the full source-level explanation) — an active-flag
	// guard neutralizes the stale listener instead of trying to remove it.
	let active = true;
	function onRouteChange() {
		if (!active) return;
		state.value = readRoute();
	}

	onMounted(() => frappe.router.on("change", onRouteChange));
	onUnmounted(() => {
		active = false;
		frappe.router.off("change", onRouteChange);
	});

	return { state, goToTab, openRecord, openNew, closeToList };
}
