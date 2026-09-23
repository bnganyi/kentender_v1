// PLN-CHG-001 v1.24 §10.8 U09-REMOVE, ported from Artboards-U09.dc.html.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DissolveItemDialog from "./DissolveItemDialog.vue";

const SOURCES = [
	{ requirement: "Clinical training laptops", department: "HRMD", amount_display: "KES 20,000,000" },
	{ requirement: "Clinical deployment laptops", department: "Digital Health", amount_display: "KES 30,000,000" },
];

function make(props = {}) {
	return mount(DissolveItemDialog, { props: { pending: false, error: "", sources: SOURCES, ...props } });
}

describe("DissolveItemDialog", () => {
	it("names what happens to the requirements and to the money", () => {
		const w = make();
		expect(w.text()).toContain("Remove this purchase?");
		expect(w.text()).toContain("These requirements will return to this draft plan so they can be added again.");
		expect(w.text()).toContain("No funds are released.");
	});

	it("lists the requirements that will be returned, without repeating department", () => {
		const w = make();
		const table = w.get('[data-testid="pln-dissolve-sources"]');
		expect(table.text()).toContain("Clinical training laptops");
		expect(table.text()).toContain("KES 30,000,000");
		expect(table.text()).not.toContain("HRMD");
		expect(table.text()).not.toContain("Digital Health");
	});

	it("names the exact purchase being removed when the caller supplies it", () => {
		const w = make({ item: { title: "Clinical training and deployment laptops for digital health rollout", plan_item_id: "PPI-MOH-2027-033" } });
		const summary = w.get('[data-testid="pln-dissolve-item-summary"]');
		expect(summary.text()).toContain("Clinical training and deployment laptops for digital health rollout");
		expect(summary.text()).toContain("PPI-MOH-2027-033");
	});

	it("shows no item summary block when the caller does not supply one", () => {
		const w = make();
		expect(w.find('[data-testid="pln-dissolve-item-summary"]').exists()).toBe(false);
	});

	it("emits confirm and cancel", async () => {
		const w = make();
		await w.get('[data-testid="pln-dissolve-item-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toHaveLength(1);
		await w.findAll("button")[0].trigger("click");
		expect(w.emitted("cancel")).toHaveLength(1);
	});

	it("shows a command error", () => {
		const w = make({ error: "This item can no longer be removed from the draft." });
		expect(w.get('[data-testid="pln-dissolve-item-error"]').text()).toContain("can no longer be removed");
	});
});
