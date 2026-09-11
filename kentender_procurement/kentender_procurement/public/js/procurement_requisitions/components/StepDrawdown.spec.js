// REQ-DES-03 Step 1: Request and drawdown (§13.5) — the four read-only
// context cards, the four editable fields, and the drawdown table with its
// "Request full balance" default-restoring link.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StepDrawdown from "./StepDrawdown.vue";

const EDITOR = {
	business_need: "Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout.",
	expected_operational_result: "Staff can use secure, supported equipment for training and field digital-health work.",
	planning_projection: { procurement_method: "Open Tender", planned_dates: { delivery_completion_date: "2027-09-30" } },
	version: {
		record_version: 1,
		requirement_title: "Clinical training and deployment laptops for digital health rollout",
		delivery_location: "MOH-HQ",
		latest_delivery_date: "2027-09-30",
		related_services_required: false,
		drawdown_lines: [
			{ drawdown_line_id: "DL-001", requested_quantity: 100, requested_value: 20000000 },
			{ drawdown_line_id: "DL-002", requested_quantity: 150, requested_value: 30000000 },
		],
	},
	drawdown_context: [
		{ drawdown_line_id: "DL-001", organisation_unit_label: "Human Resources Management and Development", source_title: "Business laptops", remaining_quantity: 100, remaining_value: 20000000, unit: "Each" },
		{ drawdown_line_id: "DL-002", organisation_unit_label: "Digital Health", source_title: "Business laptops", remaining_quantity: 150, remaining_value: 30000000, unit: "Each" },
	],
	delivery_locations: [{ name: "MOH-HQ", location_name: "Ministry of Health Headquarters, Afya House, Nairobi" }],
};

function make(overrides = {}) {
	return mount(StepDrawdown, { props: { editor: { ...EDITOR, ...overrides } } });
}

describe("StepDrawdown — REQ-DES-03", () => {
	it("renders the four read-only context cards with the exact inherited copy", () => {
		const w = make();
		const cards = w.findAll(".req-context-card");
		expect(cards).toHaveLength(4);
		expect(cards[0].find(".req-context-title").text()).toBe("Business need");
		expect(cards[0].find(".req-context-body").text()).toBe(EDITOR.business_need);
		expect(cards[1].find(".req-context-title").text()).toBe("Expected operational result");
		expect(cards[2].find(".req-context-body").text()).toBe("Open Tender");
		expect(cards[3].find(".req-context-title").text()).toBe("Planned completion");
	});

	it("hydrates the editable fields from the Draft Version", () => {
		const w = make();
		expect(w.find("#req-title").element.value).toBe("Clinical training and deployment laptops for digital health rollout");
		expect(w.find("#req-location").element.value).toBe("MOH-HQ");
		expect(w.find("#req-date").element.value).toBe("2027-09-30");
		expect(w.find('input[type="radio"]:checked').element.parentElement.textContent.trim()).toBe("No");
	});

	it("defaults an empty delivery location to the first available one, never a silently-empty selection", () => {
		// confirmed live: a native <select> visually highlights its first
		// <option> even when the bound value is "" and matches nothing, so
		// Save/Continue silently persisted no delivery location at all
		// unless the field is defaulted explicitly.
		const w = make({ version: { ...EDITOR.version, delivery_location: "" } });
		expect(w.find("#req-location").element.value).toBe("MOH-HQ");
		expect(w.vm.getPayload().delivery_location).toBe("MOH-HQ");
	});

	it("renders the drawdown table with the two contributing-department rows", () => {
		const w = make();
		const rows = w.findAll("tbody tr");
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Human Resources Management and Development");
		expect(rows[0].text()).toContain("100 Each");
		expect(rows[0].text()).toContain("KES 20,000,000.00");
		expect(rows[0].find('[data-testid="req-drawdown-qty-DL-001"]').element.value).toBe("100");
	});

	it("restores the full remaining balance when Request full balance is clicked after a partial edit", async () => {
		const w = make();
		const qtyInput = w.find('[data-testid="req-drawdown-qty-DL-001"]');
		await qtyInput.setValue(40);
		expect(w.vm.getPayload().drawdown_lines.find((l) => l.drawdown_line_id === "DL-001").requested_quantity).toBe(40);
		await w.find("tbody tr").find(".req-quiet-link").trigger("click");
		const payload = w.vm.getPayload();
		const line = payload.drawdown_lines.find((l) => l.drawdown_line_id === "DL-001");
		expect(line.requested_quantity).toBe(100);
		expect(line.requested_value).toBe(20000000);
	});

	it("exposes getPayload with every editable field for the parent's Save draft/Continue", () => {
		const w = make();
		const payload = w.vm.getPayload();
		expect(payload.requirement_title).toBe("Clinical training and deployment laptops for digital health rollout");
		expect(payload.delivery_location).toBe("MOH-HQ");
		expect(payload.latest_delivery_date).toBe("2027-09-30");
		expect(payload.related_services_required).toBe(false);
		expect(payload.drawdown_lines).toHaveLength(2);
	});

	it("does not re-hydrate from an in-place refresh carrying the same record_version (AGENTS.md §6.4)", async () => {
		const w = make();
		await w.find("#req-title").setValue("Typed by the author, not yet saved");
		await w.setProps({ editor: { ...EDITOR } }); // same record_version
		expect(w.find("#req-title").element.value).toBe("Typed by the author, not yet saved");
	});
});
