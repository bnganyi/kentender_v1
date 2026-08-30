// PLN-CHG-001 v1.2 §15.1(5) — WorkspaceScreen component tests (decision D9).
// Exact fields, absent fields, errors, copy and action visibility for
// PLN-DES-01 and the PLN-DES-16 states rendered by this screen.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import WorkspaceScreen from "./WorkspaceScreen.vue";

const CONTEXT = {
	procuring_entity: "PE-MOH",
	financial_year: "FY-2027-2028",
	procuring_entities: [{ id: "PE-MOH", label: "Ministry of Health" }],
	financial_years: [{ id: "FY-2027-2028", label: "FY 2027/28" }],
};

const WORKSPACE = {
	outcome: "OK",
	context: CONTEXT,
	annual_plan: { plan_reference: "PLN-MOH-2027-001", summary: "Annual Plan · Draft Version 1" },
	your_work: [
		{
			item: "Form Plan Items",
			scope: "1 accepted departmental entry · KES 80,000,000",
			status: "Ready",
			status_kind: "live",
			action: "Open Annual Plan",
			route: ["annual-procurement-plan"],
		},
	],
	departmental_plans: [
		{
			dpp_reference: "DPP-MOH-DHI-2027-001",
			department: "Digital Health",
			version: 1,
			requirements: 1,
			value: "KES 80,000,000",
			status: "Accepted",
			status_kind: "live",
			route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"],
		},
		{
			dpp_reference: "DPP-MOH-HRMD-2027-001",
			department: "Human Resources Management and Development",
			version: 1,
			requirements: 2,
			value: "KES 88,000,000",
			status: "Not submitted — window closed",
			status_kind: "critical",
			route: ["departmental-procurement-plan", "DPP-MOH-HRMD-2027-001"],
		},
	],
	count_label: "2 departmental plans",
	not_included_message:
		"2 accepted Needs are not included because the departmental-plan submission window closed.",
};

function make(overrides = {}) {
	return mount(WorkspaceScreen, {
		props: {
			loading: false,
			error: "",
			supportRef: "",
			workspace: WORKSPACE,
			pending: false,
			...overrides,
		},
	});
}

describe("WorkspaceScreen — PLN-DES-01", () => {
	it("renders the exact masthead copy with no header action button", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("PROCUREMENT PLANNING");
		expect(w.find(".kt-page-title").text()).toBe("Annual procurement planning");
		expect(w.find(".kt-page-lede").text()).toContain(
			"Turn accepted departmental plans into a funded and approved Annual Procurement Plan."
		);
		expect(w.find(".pln-masthead button").exists()).toBe(false);
	});

	it("renders the context strip as editable selects plus the quiet plan line", () => {
		const w = make();
		expect(w.find('[data-testid="pln-pe-select"]').element.tagName).toBe("SELECT");
		expect(w.find('[data-testid="pln-fy-select"]').element.tagName).toBe("SELECT");
		expect(w.find('[data-testid="pln-plan-summary"]').text()).toBe(
			"Annual Plan · Draft Version 1"
		);
	});

	it("renders Your work rows with status pill and action, and emits navigate", async () => {
		const w = make();
		const row = w.find('[data-testid="pln-your-work"] tbody tr');
		expect(row.text()).toContain("Form Plan Items");
		expect(row.text()).toContain("1 accepted departmental entry · KES 80,000,000");
		expect(row.find(".kt-status").classes()).toContain("is-live");
		await row.find("button").trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["annual-procurement-plan"]);
	});

	it("hides the Your work card entirely when the actor has no work", () => {
		const w = make({ workspace: { ...WORKSPACE, your_work: [] } });
		expect(w.find('[data-testid="pln-your-work"]').exists()).toBe(false);
	});

	it("renders the departmental plans table, captions and the not-included line", () => {
		const w = make();
		const rows = w.findAll('[data-testid="pln-departmental-plans"] tbody tr');
		expect(rows).toHaveLength(2);
		expect(rows[1].text()).toContain("Human Resources Management and Development");
		expect(rows[1].find(".kt-status").classes()).toContain("is-critical");
		expect(rows[1].find(".kt-status").text()).toBe("Not submitted — window closed");
		expect(w.find('[data-testid="pln-count-label"]').text()).toBe("2 departmental plans");
		expect(w.find('[data-testid="pln-not-included"]').text()).toBe(
			"2 accepted Needs are not included because the departmental-plan submission window closed."
		);
	});

	it("shows no charts, summary tiles, waiting queues or system support links (§11.2)", () => {
		const w = make();
		expect(w.text()).not.toContain("%");
		expect(w.find("canvas").exists()).toBe(false);
		expect(w.text()).not.toContain("Support workspace");
	});

	it("routes an open-departmental-plan work action through its own event", async () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				your_work: [
					{
						item: "Open departmental plan",
						scope: "Digital Health",
						status: "Ready",
						status_kind: "live",
						action: "Open departmental plan",
						route: ["procurement-planning", "open", "OU-MOH-DHI"],
					},
				],
			},
		});
		await w.find('[data-testid="pln-work-action-0"]').trigger("click");
		expect(w.emitted("open-departmental-plan")[0][0]).toBe("OU-MOH-DHI");
		expect(w.emitted("navigate")).toBeUndefined();
	});
});

describe("WorkspaceScreen — PLN-DES-16 states", () => {
	it("renders the exact no-context state with no control", () => {
		const w = make({ workspace: { outcome: "NO_SCOPE", context: {} } });
		const card = w.find('[data-testid="pln-no-scope"]');
		expect(card.find("h3").text()).toBe("Procurement Planning is not available");
		expect(card.text()).toContain(
			"You do not have an assigned Procuring Entity scope, or no configured Financial Year is available for Planning."
		);
		expect(card.find("button").exists()).toBe(false);
	});

	it("renders the load-error state with Try again and the support reference", async () => {
		const w = make({ error: "boom", supportRef: "PLN-ERR-20261201-0917" });
		const card = w.find('[data-testid="pln-error"]');
		expect(card.find("h3").text()).toBe("Procurement Planning could not be loaded");
		expect(card.text()).toContain("Support reference: PLN-ERR-20261201-0917");
		await card.find("button").trigger("click");
		expect(w.emitted("reload")).toHaveLength(1);
	});

	it("keeps the context strip operable in the selection-required state", () => {
		const w = make({
			workspace: { outcome: "SELECTION_REQUIRED", context: CONTEXT },
		});
		expect(w.find('[data-testid="pln-selection-required"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-pe-select"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-your-work"]').exists()).toBe(false);
	});
});
