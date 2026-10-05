import { describe, expect, it, vi } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";

import StartDialog from "./StartDialog.vue";
import WorkspaceScreen from "./WorkspaceScreen.vue";
import { context, startPreview, workspace } from "./fixtures.js";

const FILTERS = { search: "", status: "", department: "", fiscal_year: "" };

describe("WorkspaceScreen (REQ-DES-01)", () => {
	it("leads with the one purchase ready to start and routes Start to its dialog", async () => {
		const { global, calls } = context();
		const w = mount(WorkspaceScreen, { props: { workspace: workspace(), filters: FILTERS }, global });
		expect(w.find('[data-testid="req-your-work"]').exists()).toBe(false);
		expect(w.findAll('[data-testid="req-ready-row"]')).toHaveLength(1);
		expect(w.text()).toContain("PPI-MOH-2027-033");
		expect(w.find('[data-testid="req-register-empty"]').text()).toBe("You have no requisitions yet.");
		await w.find('[data-testid="req-start"]').trigger("click");
		expect(calls).toContainEqual(["goPath", "/app/procurement-requisitions/new/PI-0001"]);
	});

	it("DRAFT: Your work leads, the Ready section is absent and the register repeats the record quietly", () => {
		const { global } = context();
		const w = mount(WorkspaceScreen, { props: { workspace: workspace("DRAFT"), filters: FILTERS }, global });
		expect(w.find('[data-testid="req-work-row"]').text()).toContain("Complete request details");
		expect(w.find('[data-testid="req-ready"]').exists()).toBe(false);
		expect(w.findAll('[data-testid="req-register-row"]')).toHaveLength(1);
	});

	it("ACTION: the exact decision leads with Review, and only a non-zero Approvals label annotates the register", () => {
		const { global } = context();
		const w = mount(WorkspaceScreen, { props: { workspace: workspace("ACTION"), filters: FILTERS }, global });
		expect(w.find('[data-testid="req-work-row"] .btn').text()).toBe("Review");
		expect(w.find('[data-testid="req-count-approvals"]').text()).toBe("Approvals 1");
		const draft = mount(WorkspaceScreen, { props: { workspace: workspace("DRAFT"), filters: FILTERS }, global });
		expect(draft.find('[data-testid="req-count-approvals"]').exists()).toBe(false);
	});

	it("NONE: says no purchase is ready and keeps the register", () => {
		const { global } = context();
		const w = mount(WorkspaceScreen, { props: { workspace: workspace("NONE"), filters: FILTERS }, global });
		expect(w.find('[data-testid="req-ready-none"]').text()).toContain("No approved purchases are ready for a requisition.");
		expect(w.find('[data-testid="req-register"]').exists()).toBe(true);
	});

	it("TECHNICAL: four filters, the site-wide register and no business action", () => {
		const { global } = context();
		const w = mount(WorkspaceScreen, { props: { workspace: workspace("TECHNICAL"), filters: FILTERS }, global });
		expect(w.findAll(".req-filters .input")).toHaveLength(4);
		expect(w.find('[data-testid="req-clear-filters"]').exists()).toBe(false);
		expect(w.text()).not.toMatch(/Your work|Ready to start|Start requisition|Continue/);
		expect(w.find('[data-testid="req-filter-fiscal-year"]').text()).toContain("FY 2027/28");
	});

	it("an existing open requisition replaces Start requisition rather than sitting beside it", () => {
		const { global } = context();
		const ws = workspace();
		ws.ready_to_start = [{ ...ws.ready_to_start[0], existing: { requisition: "PR-0001", summary: "REQ-MOH-2027-033-001 · Draft · Request details need attention", route: "/app/procurement-requisitions/PR-0001" } }];
		const w = mount(WorkspaceScreen, { props: { workspace: ws, filters: FILTERS }, global });
		expect(w.find('[data-testid="req-start"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-ready-existing"]').text()).toContain("Open existing requisition");
	});

	it("filters are the caller's own selection: typed search survives a re-render and is sent once typing pauses", async () => {
		vi.useFakeTimers();
		const { global } = context();
		const w = mount(WorkspaceScreen, { props: { workspace: workspace("DRAFT"), filters: FILTERS }, global });
		const input = w.find('[data-testid="req-filter-search"]');
		await input.setValue("laptop");
		await w.setProps({ workspace: { ...workspace("DRAFT") } });
		expect(input.element.value).toBe("laptop");
		expect(w.emitted("filters")).toBeUndefined();
		vi.advanceTimersByTime(300);
		expect(w.emitted("filters")[0][0]).toEqual({ search: "laptop" });
		await w.find('[data-testid="req-filter-status"]').setValue("Draft");
		expect(w.emitted("filters")[1][0]).toEqual({ status: "Draft" });
		await w.find('[data-testid="req-clear-filters"]').trigger("click");
		expect(w.emitted("filters")[2][0]).toEqual({ search: "", status: "", department: "", fiscal_year: "" });
		expect(input.element.value).toBe("");
		vi.useRealTimers();
	});
});

describe("StartDialog (REQ-DES-02)", () => {
	it("starts the Draft through the command runner and opens it", async () => {
		const prepare = vi.fn().mockResolvedValue({ requisition: "PR-0009" });
		const { global, calls } = context({ api: { prepare } });
		const w = mount(StartDialog, { props: { preview: startPreview() }, global });
		expect(w.text()).toContain("Digital Health will submit this combined departmental request.");
		expect(w.text()).not.toContain("County requirement");
		await w.find('[data-testid="req-start-confirm"]').trigger("click");
		await flushPromises();
		expect(prepare).toHaveBeenCalledWith({ plan_item_id: "PI-0001", idempotency_key: "test-key" });
		expect(calls).toContainEqual(["go", "PR-0009"]);
	});

	it.each(["unsupported", "rule_unavailable", "reservation_unsupported"])("%s: Start is disabled, Cancel stays, nothing is created", async (state) => {
		const prepare = vi.fn();
		const { global } = context({ api: { prepare } });
		const w = mount(StartDialog, { props: { preview: startPreview(state) }, global });
		const confirm = w.find('[data-testid="req-start-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();
		await confirm.trigger("click");
		expect(prepare).not.toHaveBeenCalled();
		expect(w.find('[data-testid="req-start-cancel"]').exists()).toBe(true);
		expect(w.find(".kt-notice.is-critical").text()).toBe(startPreview(state).message);
	});

	it("shows the server's refusal inline, never as a modal", () => {
		const { global, ctx } = context();
		ctx.commandError.value = { label: "prepare", code: "REQ_OPEN_EXISTS", message: "This Plan Item already has an open Requisition." };
		const w = mount(StartDialog, { props: { preview: startPreview() }, global });
		expect(w.find('[data-testid="req-start-error"]').text()).toBe("This Plan Item already has an open Requisition.");
	});
});
