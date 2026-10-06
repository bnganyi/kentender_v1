// The shared paging logic every register uses (AGENTS.md §6.11), and a guard that the
// four per-app copies of it have not drifted: a bundle cannot import another app's
// wrapper (AGENTS.md §6.6), so the files are copied, and a copy that is edited alone
// is how two registers would come to page differently.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { beforeEach, describe, expect, it } from "vitest";
import { ref } from "vue";
import { clearPagedMemory, pagedView, resetPaged, setPagedPage, setPagedSize, usePagedRows } from "./usePagedRows.js";

const rows = (n) => Array.from({ length: n }, (_, i) => i + 1);

beforeEach(() => clearPagedMemory());

describe("pagedView", () => {
	it("shows ten rows by default and says how many there are", () => {
		const view = pagedView("t", rows(25));
		expect(view.rows).toEqual(rows(10));
		expect([view.total, view.page, view.pageSize]).toEqual([25, 1, 10]);
	});

	it("keeps each key's page apart, and a size change returns to page 1", () => {
		setPagedPage("a", 3);
		expect(pagedView("a", rows(45)).rows[0]).toBe(21);
		expect(pagedView("b", rows(45)).page).toBe(1);
		setPagedSize("a", 25);
		expect(pagedView("a", rows(45))).toMatchObject({ page: 1, pageSize: 25 });
		resetPaged("a");
	});

	it("a page past the end shows the last page instead of an empty table", () => {
		setPagedPage("c", 99);
		const view = pagedView("c", rows(25));
		expect(view.page).toBe(3);
		expect(view.rows).toEqual([21, 22, 23, 24, 25]);
	});

	it("an empty list is one empty page", () => {
		expect(pagedView("d", [])).toMatchObject({ rows: [], total: 0, page: 1 });
	});
});

describe("usePagedRows", () => {
	it("follows its rows and its key", () => {
		const source = ref(rows(30));
		const key = ref("plan-1");
		const paged = usePagedRows(source, () => key.value);
		paged.setPage(2);
		expect(paged.pagedRows.value[0]).toBe(11);
		key.value = "plan-2";
		expect(paged.page.value).toBe(1); // another record does not inherit this page
		key.value = "plan-1";
		expect(paged.page.value).toBe(2);
		source.value = rows(12);
		expect(paged.pagedRows.value).toEqual([11, 12]);
		paged.reset();
		expect(paged.page.value).toBe(1);
	});
});

describe("per-app copies", () => {
	const roots = [
		"kentender_procurement/kentender_procurement",
		"kentender_budget/kentender_budget",
		"kentender_strategy/kentender_strategy",
		"kentender_core/kentender_core",
	];
	it.each(["TablePagerHost.vue", "pageSize.js", "usePagedRows.js"])("%s is identical in every app", (file) => {
		const read = (root) => readFileSync(resolve(process.cwd(), root, "public/js/pager_shared", file), "utf8");
		const [first, ...rest] = roots.map(read);
		for (const other of rest) expect(other).toBe(first);
	});
});
