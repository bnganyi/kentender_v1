// The table-pagination standard: the total at the far left, "Rows per page" and
// the numbered pages at the right, the current page marked, and nothing to page
// below the smallest page size.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import TablePager from "./TablePager.vue";
import { pageWindow } from "../pagerWindow.js";

const make = (props = {}) => {
	const calls = { page: [], size: [] };
	const w = mount(TablePager, {
		props: { total: 47, page: 1, pageSize: 10, noun: "need", onPage: (n) => calls.page.push(n), onSize: (n) => calls.size.push(n), ...props },
	});
	return { w, calls };
};
const labels = (w) => w.findAll(".kt-pager-nav .kt-pager-page, .kt-pager-nav .kt-pager-gap").map((n) => n.text());

describe("pageWindow", () => {
	it.each([
		[1, 9, [1, 2, 3, 4, 5, "gap-end", 9]],
		[4, 9, [1, 2, 3, 4, 5, "gap-end", 9]],
		[5, 9, [1, "gap-start", 4, 5, 6, "gap-end", 9]],
		[6, 9, [1, "gap-start", 5, 6, 7, 8, 9]],
		[9, 9, [1, "gap-start", 5, 6, 7, 8, 9]],
		[3, 7, [1, 2, 3, 4, 5, 6, 7]],
		[1, 1, [1]],
	])("page %i of %i", (current, pages, expected) => {
		expect(pageWindow(current, pages)).toEqual(expected);
	});
	it("never offers more than seven slots", () => {
		for (let pages = 1; pages <= 60; pages++) for (let c = 1; c <= pages; c++) expect(pageWindow(c, pages).length).toBeLessThanOrEqual(7);
	});
});

describe("TablePager", () => {
	it("says the total on the left, with the range once there is more than a page", () => {
		expect(make().w.get('[data-testid="kt-pager-count"]').text()).toBe("Showing 1–10 of 47 needs");
		expect(make({ page: 5 }).w.get('[data-testid="kt-pager-count"]').text()).toBe("Showing 41–47 of 47 needs");
		expect(make({ total: 8 }).w.get('[data-testid="kt-pager-count"]').text()).toBe("8 needs");
		expect(make({ total: 1 }).w.get('[data-testid="kt-pager-count"]').text()).toBe("1 need");
	});

	it("uses an irregular plural when given one", () => {
		expect(make({ total: 5, noun: "responsibility", nounPlural: "responsibilities" }).w.get('[data-testid="kt-pager-count"]').text()).toBe("5 responsibilities");
		expect(make({ total: 1, noun: "responsibility", nounPlural: "responsibilities" }).w.get('[data-testid="kt-pager-count"]').text()).toBe("1 responsibility");
	});

	it("shows only the total when there is nothing to page", () => {
		const { w } = make({ total: 8 });
		expect(w.find('[data-testid="kt-pager-size"]').exists()).toBe(false);
		expect(w.find('[data-testid="kt-pager-nav"]').exists()).toBe(false);
	});

	it("draws nothing for an empty list; the screen's own empty state speaks", () => {
		expect(make({ total: 0 }).w.find('[data-testid="kt-pager"]').exists()).toBe(false);
	});

	it("offers 10, 25, 50 and 100 rows per page and reports the pick", async () => {
		const { w, calls } = make();
		const select = w.get('[data-testid="kt-pager-size"]');
		expect(select.findAll("option").map((o) => o.text())).toEqual(["10", "25", "50", "100"]);
		expect(select.element.value).toBe("10");
		await select.setValue("25");
		expect(calls.size).toEqual([25]);
	});

	it("keeps the size choice when everything fits on one page, so it can be undone", () => {
		const { w } = make({ total: 30, pageSize: 100 });
		expect(w.find('[data-testid="kt-pager-size"]').exists()).toBe(true);
		expect(w.find('[data-testid="kt-pager-nav"]').exists()).toBe(false);
		expect(w.get('[data-testid="kt-pager-count"]').text()).toBe("30 needs");
	});

	it("marks the current page and names every page button in full", () => {
		const { w } = make({ total: 90, page: 5 });
		expect(labels(w)).toEqual(["1", "…", "4", "5", "6", "…", "9"]);
		const current = w.get('[data-testid="kt-pager-page-5"]');
		expect(current.attributes("aria-current")).toBe("page");
		expect(current.classes()).toContain("is-current");
		expect(w.get('[data-testid="kt-pager-page-4"]').attributes("aria-current")).toBeUndefined();
		expect(w.get('[data-testid="kt-pager-page-4"]').attributes("aria-label")).toBe("Go to page 4");
		expect(w.get("nav").attributes("aria-label")).toBe("Pagination");
	});

	it("reports a page pick, steps with Prev and Next, and ignores the current page", async () => {
		const { w, calls } = make({ total: 90, page: 5 });
		await w.get('[data-testid="kt-pager-page-6"]').trigger("click");
		await w.get('[data-testid="kt-pager-prev"]').trigger("click");
		await w.get('[data-testid="kt-pager-next"]').trigger("click");
		await w.get('[data-testid="kt-pager-page-5"]').trigger("click");
		expect(calls.page).toEqual([6, 4, 6]);
	});

	it("disables Prev on the first page and Next on the last", () => {
		expect(make().w.get('[data-testid="kt-pager-prev"]').attributes("disabled")).toBeDefined();
		expect(make().w.get('[data-testid="kt-pager-next"]').attributes("disabled")).toBeUndefined();
		const last = make({ page: 5 }).w;
		expect(last.get('[data-testid="kt-pager-next"]').attributes("disabled")).toBeDefined();
	});
});
