// Browser-side paging for a register whose screen already holds every row (the
// table-pagination standard, AGENTS.md §6.11). The page and size are kept per
// screen in module memory, so a visit to a record and back lands on the same page
// even though the register itself unmounts; the size is also remembered across
// visits through pageSize.js.
//
// Reset the page from the reader's own filter actions — or watch the screen's own
// filter refs. Never watch props a load can change: that sent Departmental Needs
// back to page 1 after Back (found live 6 Oct 2026).
//
// Two ways in: `usePagedRows(rows, screen)` for a screen with one register, and
// the keyed functions (`pagedView`, `setPagedPage`, ...) for a board that draws
// many tables from one template and pages only the ones it marks.
import { computed, reactive } from "vue";
import { savePageSize, savedPageSize } from "./pageSize.js";

const memory = reactive({});

function stateOf(key) {
	if (!memory[key]) memory[key] = { page: 1, size: savedPageSize(key) };
	return memory[key];
}

export function clearPagedMemory() {
	for (const key of Object.keys(memory)) delete memory[key];
}

// One page of `rows` for `key`: { rows, total, page, pageSize }.
export function pagedView(key, rows) {
	const state = stateOf(key);
	const all = rows || [];
	const pages = Math.max(1, Math.ceil(all.length / state.size));
	// A page past the end shows the last page rather than an empty table.
	const page = Math.min(Math.max(state.page, 1), pages);
	return { rows: all.slice((page - 1) * state.size, page * state.size), total: all.length, page, pageSize: state.size };
}

export function setPagedPage(key, page) {
	stateOf(key).page = page;
}

export function setPagedSize(key, size) {
	const state = stateOf(key);
	state.size = size;
	state.page = 1;
	savePageSize(key, size);
}

export function resetPaged(key) {
	stateOf(key).page = 1;
}

// `screen` is the memory key, or a function returning it when the same screen shows different
// records (a plan's purchases are paged per plan, so another plan does not inherit this page).
export function usePagedRows(rows, screen) {
	const key = () => (typeof screen === "function" ? screen() : screen);
	const view = computed(() => pagedView(key(), rows.value));
	return {
		pagedRows: computed(() => view.value.rows),
		total: computed(() => view.value.total),
		page: computed(() => view.value.page),
		pageSize: computed(() => view.value.pageSize),
		setPage: (n) => setPagedPage(key(), n),
		setPageSize: (size) => setPagedSize(key(), size),
		reset: () => resetPaged(key()),
	};
}
