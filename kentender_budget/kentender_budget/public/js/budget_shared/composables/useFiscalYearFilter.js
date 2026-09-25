import { ref } from "vue";
import { listAvailableFiscalYears } from "../../budget_funding/data/budgetApi.js";

// BUD-CHG-001 v1.3 Phase 7 — one site is one Procuring Entity: Budget has no
// PE+FY "working context" any more, only a local Fiscal Year filter (§10:
// "a changeable filter on the workspace. It is never a gate and never a
// context selector."). Replaces useWorkingContext.js/WorkingContextPicker.vue
// for every Budget screen.
//
// §12.1: "It never chooses the first Budget or the first year... remembered
// only with a visible reset, and is ignored when stale or invalid." So this
// never auto-picks list[0] — only a previously-selected year, read back from
// localStorage and re-validated against the live catalogue on every load,
// counts as "selected". Shared across screens (Workspace, and the pre-
// creation Register flow) via the same storage key, so navigating from one
// to the other carries the same selection with no query-string plumbing.
const STORAGE_KEY = "kt-budget-fiscal-year";

// `frappe.route_options.fiscal_year`, read once: Frappe's router keeps it as
// given after set_route, but as the JSON text it wrote into the query string
// ('"2027-2028"') after a reload.
function routeFiscalYear() {
	const options = window.frappe && window.frappe.route_options;
	if (!options || !options.fiscal_year) return "";
	let value = options.fiscal_year;
	delete options.fiscal_year;
	if (typeof value === "string") {
		try {
			const parsed = JSON.parse(value);
			if (typeof parsed === "string") value = parsed;
		} catch (e) {
			// already plain text
		}
	}
	return String(value);
}

export function useFiscalYearFilter() {
	const loading = ref(true);
	const fiscalYears = ref([]);
	const selected = ref("");

	async function load() {
		loading.value = true;
		try {
			fiscalYears.value = (await listAvailableFiscalYears()) || [];
			// A link into Budget for one year's work (Budget's own My Work row,
			// or Planning's "Open the request in Budget & Funding") names the
			// year, so the item it points at is on screen, not behind a picker.
			const asked = routeFiscalYear();
			if (asked && fiscalYears.value.includes(asked)) {
				select(asked);
				return;
			}
			const remembered = window.localStorage.getItem(STORAGE_KEY) || "";
			selected.value = fiscalYears.value.includes(remembered) ? remembered : "";
		} finally {
			loading.value = false;
		}
	}

	function select(fy) {
		selected.value = fy || "";
		try {
			if (fy) window.localStorage.setItem(STORAGE_KEY, fy);
			else window.localStorage.removeItem(STORAGE_KEY);
		} catch (e) {
			// Private-browsing/storage-blocked contexts: the in-memory selection
			// still works for this page load, it just doesn't persist.
		}
	}

	return { loading, fiscalYears, selected, load, select };
}
