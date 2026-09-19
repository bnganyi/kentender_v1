// TPR-DES-01 — exact copy, count cards per role, row status/action from the
// server, the empty result, and the Forbidden card rendered by the root.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import WorkspaceScreen from "./WorkspaceScreen.vue";
import CommonState from "./CommonState.vue";

const ROW = { kind: "tender", tender: "TDR-1", tender_reference: "TND-MOH-2027-033", purchase: "Supply and delivery of business laptops", plan_item_id: "PPI-MOH-2027-033", requisition_reference: "REQ-MOH-2027-033-001", fiscal_year: "2027-2028", status_key: "draft", status_label: "Draft — Tender details need attention", secondary: "", required_by: "30 Sep 2027", action_key: "continue", action_label: "Continue", route: ["tenders", "TND-MOH-2027-033", "details"] };
const WS = { outcome: "OK", counts: [{ key: "ready", label: "Ready to start", value: 1, sub: "Approved requisitions awaiting a tender" }, { key: "draft", label: "Drafts", value: 0, sub: "Started, not yet submitted" }, { key: "returned", label: "Returned to me", value: 0, sub: "Sent back for correction" }], rows: [ROW], filters: { statuses: [{ key: "draft", label: "Draft" }], fiscal_years: ["2027-2028"] }, empty_text: "" };

function make(overrides = {}) {
	return mount(WorkspaceScreen, { props: { loading: false, workspace: WS, filters: { search: "", status: "", fiscal_year: "" }, pending: false, ...overrides } });
}

describe("WorkspaceScreen — TPR-DES-01", () => {
	it("renders the masthead copy, the count cards and the queue row from the server", async () => {
		const w = make();
		expect(w.find("h1").text()).toBe("Tenders");
		expect(w.find(".tnd-lede").text()).toBe("Prepare approved requisitions, complete approvals and follow publication.");
		expect(w.findAll(".kt-kpi-card")).toHaveLength(3);
		expect(w.find('[data-testid="tnd-count-ready"]').classes()).toContain("is-live");
		expect(w.find('[data-testid="tnd-count-draft"]').classes()).not.toContain("is-live");
		const row = w.find('[data-testid="tnd-row-draft"]');
		expect(row.text()).toContain("Draft — Tender details need attention");
		const action = row.find('[data-testid="tnd-action-continue"]');
		expect(action.text()).toBe("Continue");
		expect(action.classes()).toContain("kt-btn-primary");
		await action.trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["tenders", "TND-MOH-2027-033", "details"]);
	});

	it("shows no count cards for a reader and a secondary View action", () => {
		const w = make({ workspace: { ...WS, counts: [], rows: [{ ...ROW, status_key: "published", status_label: "Published — open", action_key: "view", action_label: "View" }] } });
		expect(w.find('[data-testid="tnd-counts"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-action-view"]').classes()).toContain("kt-btn-secondary");
		expect(w.find('[data-testid="tnd-row-published"] .kt-status').classes()).toContain("is-live");
	});

	it("renders the empty result with its own Clear filters and emits the filter change", async () => {
		const w = make({ workspace: { ...WS, rows: [], empty_text: "No Tenders match these filters." } });
		expect(w.find('[data-testid="tnd-empty"]').text()).toContain("No Tenders match these filters.");
		await w.find('[data-testid="tnd-filter-search"]').setValue("laptop");
		expect(w.emitted("filter")[0][0]).toEqual({ search: "laptop", status: "", fiscal_year: "" });
		await w.find('[data-testid="tnd-empty"] button').trigger("click");
		expect(w.emitted("clear-filters")).toHaveLength(1);
	});

	it("CommonState carries the Forbidden copy from the server and no action", () => {
		const w = mount(CommonState, { props: { kind: "forbidden", heading: "You do not have access to Tenders", text: "This area needs one of these responsibilities: Procurement Officer." } });
		expect(w.find("h2").text()).toBe("You do not have access to Tenders");
		expect(w.find("button").exists()).toBe(false);
		const nf = mount(CommonState, { props: { kind: "not-found" } });
		expect(nf.find("button").text()).toBe("Back to Tenders");
	});
});
