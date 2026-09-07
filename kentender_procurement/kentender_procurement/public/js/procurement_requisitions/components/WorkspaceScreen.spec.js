// REQ-CHG-001 v1.6 §13.3 — WorkspaceScreen component tests. Exact fields,
// absent fields, copy and action visibility for REQ-DES-01 and its Forbidden
// / load-error states.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import WorkspaceScreen from "./WorkspaceScreen.vue";

const WORKSPACE = {
	outcome: "OK",
	ready_to_prepare: {
		headline: "1 Plan Item ready to prepare",
		rows: [
			{
				plan_item_id: "PPI-MOH-2027-033",
				supporting: "Clinical training and deployment laptops for digital health rollout · Digital Health, HR Management and Development · KES 50,000,000.00",
				route: ["procurement-requisitions", "new", "PPI-MOH-2027-033"],
			},
		],
	},
	requisitions: [
		{
			requisition: "PRQ-0001",
			requisition_reference: "REQ-MOH-2027-033-001",
			plan_item_title: "Clinical training and deployment laptops for digital health rollout",
			status: "Draft",
			status_kind: "is-draft",
			action_label: "Continue",
			route: ["procurement-requisitions", "PRQ-0001"],
		},
	],
	count_label: "1 Requisition",
};

function make(overrides = {}) {
	return mount(WorkspaceScreen, {
		props: { loading: false, error: "", supportRef: "", workspace: WORKSPACE, pending: false, ...overrides },
	});
}

describe("WorkspaceScreen — REQ-DES-01", () => {
	it("renders the exact masthead copy with no eyebrow", () => {
		const w = make();
		expect(w.find(".kt-page-title").text()).toBe("Procurement Requisitions");
		expect(w.find(".kt-page-lede").text()).toBe("Prepare precise departmental requests from approved Plan Items.");
		expect(w.find(".req-masthead").text()).not.toContain("PROCUREMENT REQUISITIONS");
	});

	it("renders the ready-to-prepare card with the exact headline, supporting line and button", async () => {
		const w = make();
		const card = w.find('[data-testid="req-ready-to-prepare"]');
		expect(card.find('[data-testid="req-ready-headline"]').text()).toBe("1 Plan Item ready to prepare");
		const row = card.find('[data-testid="req-ready-row"]');
		expect(row.text()).toContain(
			"Clinical training and deployment laptops for digital health rollout · Digital Health, HR Management and Development · KES 50,000,000.00"
		);
		const button = row.find("button");
		expect(button.text()).toBe("Prepare Requisition");
		expect(button.classes()).toContain("kt-btn-primary");
		await button.trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-requisitions", "new", "PPI-MOH-2027-033"]);
	});

	it("omits the ready-to-prepare card entirely when nothing is eligible", () => {
		const w = make({ workspace: { ...WORKSPACE, ready_to_prepare: null } });
		expect(w.find('[data-testid="req-ready-to-prepare"]').exists()).toBe(false);
	});

	it("renders one row per eligible item when more than one is ready", () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				ready_to_prepare: {
					headline: "2 Plan Items ready to prepare",
					rows: [
						{ plan_item_id: "A", supporting: "Item A · KES 1.00", route: ["procurement-requisitions", "new", "A"] },
						{ plan_item_id: "B", supporting: "Item B · KES 2.00", route: ["procurement-requisitions", "new", "B"] },
					],
				},
			},
		});
		expect(w.findAll('[data-testid="req-ready-row"]')).toHaveLength(2);
		expect(w.findAll('[data-testid="req-ready-to-prepare"]')).toHaveLength(1);
	});

	it("renders Your Requisitions as one connected table with the exact headers, rows and count", async () => {
		const w = make();
		expect(w.find(".req-section-title").text()).toBe("Your Requisitions");
		const table = w.find('[data-testid="req-your-requisitions"]');
		expect(table.findAll("thead th").map((th) => th.text())).toEqual(["Requisition", "Plan Item", "Status", "Action"]);
		const row = table.find("tbody tr");
		expect(row.findAll("td")[0].text()).toBe("REQ-MOH-2027-033-001");
		expect(row.findAll("td")[1].text()).toBe("Clinical training and deployment laptops for digital health rollout");
		expect(row.find(".kt-status").classes()).toContain("is-draft");
		expect(row.find(".kt-status").text()).toBe("Draft");
		const action = row.find("a");
		expect(action.text()).toBe("Continue");
		await action.trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-requisitions", "PRQ-0001"]);
		expect(w.find('[data-testid="req-count-label"]').text()).toBe("1 Requisition");
	});

	it("shows a row awaiting the actor's own decision with no separate action link when none is offered", () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				requisitions: [
					{
						requisition: "PRQ-0002", requisition_reference: "REQ-MOH-2027-033-002", plan_item_title: "Some item",
						status: "Awaiting Department Approval", status_kind: "is-draft", action_label: "", route: [],
					},
				],
			},
		});
		const row = w.find('[data-testid="req-your-requisitions"] tbody tr');
		expect(row.find(".kt-status").text()).toBe("Awaiting Department Approval");
		expect(row.find("a").exists()).toBe(false);
	});

	it("shows no value dashboard, STD Library link or Procuring Entity control", () => {
		const w = make();
		expect(w.text()).not.toContain("STD Library");
		expect(w.text()).not.toContain("Procuring Entity");
		expect(w.find("canvas").exists()).toBe(false);
	});
});

describe("WorkspaceScreen — Forbidden and load-error states", () => {
	it("renders the Forbidden panel with the exact copy and nothing else", () => {
		const w = make({
			workspace: {
				outcome: "FORBIDDEN",
				forbidden: {
					heading: "You do not have access to Procurement Requisitions.",
					text: "This area needs one of these responsibilities: Departmental Author, Head of User Department, Head of Procurement Function or Auditor. Ask your KenTender administrator to assign one in System setup.",
				},
			},
		});
		const card = w.find('[data-testid="req-forbidden"]');
		expect(card.find("h3").text()).toBe("You do not have access to Procurement Requisitions.");
		expect(card.text()).toContain("Ask your KenTender administrator to assign one in System setup.");
		expect(card.find("button").exists()).toBe(false);
		expect(w.find('[data-testid="req-ready-to-prepare"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-your-requisitions"]').exists()).toBe(false);
	});

	it("renders the load-error state with Try again and the support reference", async () => {
		const w = make({ error: "boom", supportRef: "REQ-ERR-20261201-0917" });
		const card = w.find('[data-testid="req-error"]');
		expect(card.find("h3").text()).toBe("Procurement Requisitions could not be loaded.");
		expect(card.text()).toContain("Support reference: REQ-ERR-20261201-0917");
		await card.find("button").trigger("click");
		expect(w.emitted("reload")).toHaveLength(1);
	});

	it("renders the loading skeleton and nothing else", () => {
		const w = make({ loading: true });
		expect(w.find('[data-testid="req-loading"]').exists()).toBe(true);
		expect(w.find('[data-testid="req-your-requisitions"]').exists()).toBe(false);
	});
});
