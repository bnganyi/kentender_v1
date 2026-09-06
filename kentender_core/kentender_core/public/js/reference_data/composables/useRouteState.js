import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated } from "vue";

const PAGE_SLUG = "reference-data";
const TABS = ["pe", "fy", "context"];
const DEFAULT_TAB = "pe";

// route: ["reference-data"] -> {tab: "pe", view: "list"}
// route: ["reference-data", "fy"] -> {tab: "fy", view: "list"}
// route: ["reference-data", "fy", "new"] -> {tab: "fy", view: "new"}
// route: ["reference-data", "fy", "FY-2027-2028"] -> {tab: "fy", view: "detail", code: "FY-2027-2028"}
// route: ["reference-data", "pe", "PE-HIGH", "edit"] -> {tab: "pe", view: "edit", code: "PE-HIGH"}
function readRoute(route) {
	const tab = TABS.includes(route[1]) ? route[1] : DEFAULT_TAB;
	const second = route.length > 2 ? String(route[2]).trim() : "";
	const third = route.length > 3 ? String(route[3]).trim() : "";
	if (!second) return { tab, view: "list", code: null };
	if (second === "new") return { tab, view: "new", code: null };
	if (third === "edit") return { tab, view: "edit", code: second };
	return { tab, view: "detail", code: second };
}

export function useRouteState() {
	// Route listening lives in kentender_core.desk_page (one listener per app,
	// paused while the page is hidden, re-synced on resume); this composable
	// only maps the raw segments onto the tab/view/code shape the screens read.
	const { route, epoch } = kentender_core.desk_page.useRoute(
		{ ref, onMounted, onUnmounted, onActivated, onDeactivated },
		PAGE_SLUG
	);
	const state = computed(() => readRoute(route.value));

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
	function openEdit(tab, code) {
		frappe.set_route(PAGE_SLUG, tab, code, "edit");
	}
	function closeToList(tab) {
		frappe.set_route(PAGE_SLUG, tab || state.value.tab);
	}

	return { state, epoch, goToTab, openRecord, openNew, openEdit, closeToList };
}
