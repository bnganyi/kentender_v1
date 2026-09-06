// PLN-CHG-001 v1.12 §15 — ActivePlanScreen component tests (D14). PLN-DES-14
// exact fields: the five-field strip with Schedule health, the Plan Items
// table with the projection column, the three-tier schedule card with em-dash
// actuals and "Shift schedule from here" on every shiftable milestone.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ActivePlanScreen from "./ActivePlanScreen.vue";

const SCHEDULE = [
	["invitation", "Invitation or advertisement", "2027-05-01"],
	["bid_opening", "Bid opening", "2027-05-22"],
	["evaluation_completion", "Evaluation completion", "2027-06-21"],
	["award_approval", "Tender award approval", "2027-06-26"],
	["award_notification", "Notification of award", "2027-06-28"],
	["contract_signing", "Contract signing", "2027-07-12"],
	["delivery_completion", "Delivery or implementation completion", "2027-08-31"],
].map(([milestone, label, date], index) => ({
	milestone, label, baseline: date, forecast: date, actual: "",
	variance_baseline_days: null, variance_forecast_days: null, behind: false, can_shift: index < 6,
}));

const PLAN = {
	outcome: "OK",
	plan_reference: "PLN-MOH-2027-001",
	version_reference: "PLN-MOH-2027-001-V1",
	record_version: 3,
	mutable: false,
	can_act: true,
	has_open_successor: false,
	header: { eyebrow: "ANNUAL PROCUREMENT PLAN", title: "Ministry of Health Annual Procurement Plan 2027/28", reference_line: "PLN-MOH-2027-001 · Version 1", badge: "Active" },
	active_view: {
		summary: { plan_items: 1, value_display: "KES 80,000,000", departments: 1, schedule_health_display: "0 of 1 item behind baseline", activated_display: "10 Dec 2026, 15:00 EAT" },
		items: [
			{
				plan_item_id: "PPI-MOH-2027-021", title: "National digital health infrastructure upgrade", department: "Digital Health",
				source_origin: "Accepted Departmental Need", strategic_objective_label: "Strengthen interoperable national digital health services",
				procurement_method: "Open Tender", completion_display: "31 Aug 2027", value_display: "KES 80,000,000",
				requisition_availability_display: "1 programme · KES 80,000,000", behind_baseline: false, schedule: SCHEDULE, record_version: 2,
				route: ["procurement-plan-item", "PPI-MOH-2027-021"],
			},
		],
		governance_card: {
			ao_adoption_line: "Amina Hassan · 8 Dec 2026, 10:00 EAT",
			statutory_approval_line: "Responsible Cabinet Secretary · 9 Dec 2026, 11:00 EAT",
			publication_line: "Acknowledged · 10 Dec 2026, 15:00 EAT",
			publication: "PUB-1",
			publication_route: ["procurement-planning", "publication", "PUB-1"],
		},
	},
};

function make(plan = PLAN) {
	return mount(ActivePlanScreen, { props: { plan, pending: false, errorSummary: "" } });
}

describe("ActivePlanScreen — PLN-DES-14", () => {
	it("renders the header with Prepare plan update, the five-field strip and the nine-column items table", () => {
		const w = make();
		expect(w.find('[data-testid="pln-plan-badge"]').text()).toBe("Active");
		expect(w.find('[data-testid="pln-begin-update"]').text()).toBe("Prepare plan update");
		const strip = w.find('[data-testid="pln-active-summary-strip"]');
		expect(strip.findAll("label").map((l) => l.text())).toEqual(["Plan Items", "Approved value", "Departments", "Schedule health", "Activated"]);
		expect(w.find('[data-testid="pln-active-health"]').text()).toBe("0 of 1 item behind baseline");
		const items = w.find('[data-testid="pln-active-items"]');
		expect(items.findAll("thead th").map((th) => th.text())).toEqual([
			"Plan Item", "Department", "Source origin", "Strategic Objective", "Method", "Completion", "Value", "Requisition availability", "",
		]);
		expect(items.find("tbody tr").text()).toContain("1 programme · KES 80,000,000");
		expect(w.find('[data-testid="pln-schedule-card"]').exists()).toBe(false);
	});

	it("opens the three-tier schedule card with em-dash actuals and Shift on every milestone but the last", async () => {
		const w = make();
		await w.find('[data-testid="pln-active-schedule-PPI-MOH-2027-021"]').trigger("click");
		const card = w.find('[data-testid="pln-schedule-card"]');
		expect(card.find(".kt-card-title").text()).toBe("Schedule — National digital health infrastructure upgrade");
		expect(card.findAll("thead th").map((th) => th.text())).toEqual(["Milestone", "Baseline", "Forecast", "Actual", "Variance vs baseline", ""]);
		const rows = card.findAll("tbody tr");
		expect(rows).toHaveLength(7);
		expect(rows[0].find(".pln-baseline-val").text()).toBe("1 May 2027");
		expect(rows[0].find(".pln-forecast-val").text()).toBe("1 May 2027");
		expect(rows[0].find(".pln-actual-val").text()).toBe("—");
		expect(rows[0].findAll("td")[4].text()).toBe("—");
		expect(w.findAll('[data-testid^="pln-shift-"]')).toHaveLength(6);
		expect(w.find('[data-testid="pln-shift-delivery_completion"]').exists()).toBe(false);
		await w.find('[data-testid="pln-shift-bid_opening"]').trigger("click");
		expect(w.emitted("shift")[0][0]).toMatchObject({ milestone: "bid_opening" });
		expect(w.emitted("shift")[0][0].item.plan_item_id).toBe("PPI-MOH-2027-021");
	});

	it("shows an actual from a projection with its variance, never as an input (PLN-AC-119)", async () => {
		const withActual = JSON.parse(JSON.stringify(PLAN));
		withActual.active_view.items[0].schedule[0] = { ...SCHEDULE[0], actual: "2027-05-03", variance_baseline_days: 2, can_shift: false };
		const w = make(withActual);
		await w.find('[data-testid="pln-active-schedule-PPI-MOH-2027-021"]').trigger("click");
		const row = w.find('[data-testid="pln-schedule-invitation"]');
		expect(row.find(".pln-actual-val").text()).toBe("3 May 2027");
		expect(row.findAll("td")[4].text()).toBe("+2 days");
		expect(row.find("input").exists()).toBe(false);
		expect(w.find('[data-testid="pln-shift-invitation"]').exists()).toBe(false);
	});

	it("renders the adoption, approval and publication card with the publication link", async () => {
		const w = make();
		const card = w.find('[data-testid="pln-active-governance"]');
		expect(card.findAll("label").map((l) => l.text())).toEqual(["Accounting Officer adoption", "Statutory approval", "Publication"]);
		expect(card.text()).toContain("Acknowledged · 10 Dec 2026, 15:00 EAT");
		await w.find('[data-testid="pln-publication-link"]').trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-planning", "publication", "PUB-1"]);
	});

	it("offers Prepare plan update only while no successor is open, and never a baseline or actual input", () => {
		expect(make({ ...PLAN, has_open_successor: true }).find('[data-testid="pln-begin-update"]').exists()).toBe(false);
		const w = make();
		expect(w.findAll("input, textarea, select")).toHaveLength(0);
		expect(w.text()).not.toContain("Create Requisition");
		expect(w.text()).not.toContain("Create Tender");
	});
});
