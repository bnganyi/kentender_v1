// NDS-DES-01-RETURNED, ported from NDS Artboards.dc.html — the register
// row's own action reads "Correct and resubmit" for a Returned need, more
// descriptive than the server's bare "Correct" (kept as-is for the detail
// page's single, page-level action button, NDS-DES-04/NDS-DES-08-RETURNED).
// A structural (landmark-only) gate checks that *some* button text is
// present in order; it cannot tell "Correct" from "Correct and resubmit" —
// this asserts the literal rendered string alongside (never instead of)
// that browser-layer gate.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import NeedsTable from "./NeedsTable.vue";

const COLUMNS = [
	{ key: "need", label: "Requirement" },
	{ key: "quantity_required_by", label: "Quantity and required by" },
	{ key: "status", label: "Status", status: true },
	{ key: "action", label: "Action", align: "right" },
];

function row(overrides = {}) {
	return {
		name: "NDS-MOH-2027-0003",
		reference: "NDS-MOH-2027-0003",
		title: "Clinical training laptops for digital health rollout",
		quantity_label: "200 each",
		required_by_label: "31 Dec 2027",
		status: "Returned",
		actions: [{ code: "edit", label: "Correct" }],
		...overrides,
	};
}

function make(rows) {
	return mount(NeedsTable, { props: { needs: rows, columns: COLUMNS } });
}

describe("NeedsTable — register row action label", () => {
	it("reads \"Correct and resubmit\" for a Returned need's edit action", () => {
		const w = make([row()]);
		expect(w.get('[data-testid="nds-row-action"]').text()).toBe("Correct and resubmit");
	});

	it("keeps the server's own label for a Draft need's edit action", () => {
		const w = make([row({ status: "Draft", actions: [{ code: "edit", label: "Continue" }] })]);
		expect(w.get('[data-testid="nds-row-action"]').text()).toBe("Continue");
	});

	it("keeps the server's own label for a non-edit action regardless of status", () => {
		const w = make([row({ status: "Returned", actions: [{ code: "view", label: "View" }] })]);
		expect(w.get('[data-testid="nds-row-action"]').text()).toBe("View");
	});

	it("renders no action button when the server offers none", () => {
		const w = make([row({ actions: [] })]);
		expect(w.find('[data-testid="nds-row-action"]').exists()).toBe(false);
	});
});
