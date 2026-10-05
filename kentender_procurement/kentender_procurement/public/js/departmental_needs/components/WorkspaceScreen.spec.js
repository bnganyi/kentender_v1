// NDS-DES-14 LOADING/EMPTY-AUTHOR/EMPTY-READER/FILTERED-EMPTY/CLOSED-
// WORKSPACE/NO-OPEN-YEAR/DENIED/LOAD-FAILURE — literal copy this component
// renders, ported class-for-class from NDS Artboards.dc.html. The design-
// fidelity gate's landmark check only sees structural elements (labels,
// buttons, table headers); the plain headline/body text these states are
// mostly made of is pinned here instead, word for word.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import WorkspaceScreen from "./WorkspaceScreen.vue";

function baseProps(overrides = {}) {
	return {
		loading: false,
		error: "",
		outcome: "",
		context: {},
		contexts: [],
		submission: { open: true, financial_year: "", label: "", closes_at: "" },
		needs: [],
		actions: [],
		search: "",
		status: "",
		financialYears: [],
		selectedFinancialYear: "",
		...overrides,
	};
}

const make = (overrides) => mount(WorkspaceScreen, { props: baseProps(overrides) });

describe("WorkspaceScreen — NDS-DES-14-LOADING", () => {
	it("shows the exact loading line and no controls", () => {
		const w = make({ loading: true });
		expect(w.get('[data-testid="nds-loading-text"]').text()).toBe("Loading departmental needs…");
		expect(w.find("button").exists()).toBe(false);
	});
});

describe("WorkspaceScreen — NDS-DES-14-LOAD-FAILURE", () => {
	it("names the failure and offers Try again, emitting reload", async () => {
		const w = make({ error: "Something went wrong." });
		expect(w.text()).toContain("Departmental Needs could not be loaded.");
		expect(w.text()).toContain("Try again. If the problem continues, contact support.");
		const button = w.findAll("button").find((b) => b.text() === "Try again");
		expect(button).toBeTruthy();
		await button.trigger("click");
		expect(w.emitted("reload")).toHaveLength(1);
	});
});

describe("WorkspaceScreen — NDS-DES-14-DENIED", () => {
	it("names all four read-eligible roles, not just the compact card's three", () => {
		const w = make({ outcome: "NO_AUTHORISED_CONTEXT" });
		expect(w.text()).toContain("You do not have access to Departmental Needs");
		expect(w.text()).toContain(
			"This area needs one of these responsibilities: Departmental Author, Head of User Department, Procurement Planner or Auditor, assigned to an organisation unit.",
		);
		expect(w.find("button").exists()).toBe(false);
	});
});

describe("WorkspaceScreen — NDS-DES-14-EMPTY-AUTHOR", () => {
	it("offers Create need and describes the first requirement", () => {
		const w = make({ actions: [{ code: "create", label: "Create need" }] });
		expect(w.find('[data-testid="nds-create-need"]').exists()).toBe(true);
		expect(w.text()).toContain("No departmental needs yet");
		expect(w.text()).toContain("Describe the first requirement for your department.");
	});
});

describe("WorkspaceScreen — NDS-DES-14-EMPTY-READER", () => {
	it("names the reader's own empty sentence, no Create action", () => {
		const w = make({ actions: [] });
		expect(w.find('[data-testid="nds-create-need"]').exists()).toBe(false);
		expect(w.text()).toContain("No departmental needs to display");
		// The reader's empty state has no second sentence — canCreate false.
		expect(w.text()).not.toContain("Describe the first requirement");
	});
});

describe("WorkspaceScreen — NDS-DES-14-FILTERED-EMPTY", () => {
	it("names the filtered situation, not the create-first empty state", () => {
		const w = make({ actions: [{ code: "create", label: "Create need" }], search: "Unmatched requirement" });
		expect(w.text()).toContain("No needs match your filters");
		expect(w.text()).toContain("Adjust your search or clear the filters.");
		expect(w.text()).not.toContain("No departmental needs yet");
	});
});

describe("WorkspaceScreen — NDS-DES-14-CLOSED-WORKSPACE / NO-OPEN-YEAR", () => {
	const rows = [
		{ name: "n1", reference: "NDS-MOH-2027-0001", title: "A", quantity_label: "1", required_by_label: "31 Aug 2027", status: "Accepted for planning", actions: [{ code: "view", label: "View" }] },
	];

	it("is reachable with isAuthor even though canCreate (open-gated) is false — the bug this fixed", () => {
		// Regression: the notice used to read `v-if="canCreate && !submission.open"`,
		// which can never be true (canCreate already requires submission.open) —
		// permanently dead code. isAuthor is the fix.
		const w = make({ actions: [{ code: "create", label: "Create need" }], submission: { open: false, financial_year: "", label: "", closes_at: "" }, needs: rows });
		expect(w.find('[data-testid="nds-submission-closed-notice"]').exists()).toBe(true);
	});

	it("keeps the Author's own 'My needs' framing while intake is closed, not the reader's", () => {
		const w = make({ actions: [{ code: "create", label: "Create need" }], submission: { open: false, financial_year: "", label: "", closes_at: "" }, needs: rows });
		expect(w.text()).toContain("My needs");
		expect(w.text()).toContain("Describe your department's requirements and follow their review.");
		expect(w.find('[data-testid="nds-create-need"]').exists()).toBe(false);
	});

	it("shows the reduced single-fact form (NO-OPEN-YEAR) when the read carries no financial_year/closes_at", () => {
		const w = make({
			actions: [{ code: "create", label: "Create need" }],
			submission: { open: false, financial_year: "", label: "", closes_at: "" },
			needs: rows,
		});
		const notice = w.get('[data-testid="nds-submission-closed-notice"]');
		expect(notice.text()).toContain("New submissions are closed. You can view existing needs and save changes to existing drafts.");
		expect(notice.text()).toContain("New submissions");
		expect(notice.text()).not.toContain("Financial year");
		expect(notice.text()).not.toContain("Closed at");
	});

	it("shows the full three-fact form (CLOSED-WORKSPACE) once the read actually carries financial_year/closes_at", () => {
		const w = make({
			actions: [{ code: "create", label: "Create need" }],
			submission: { open: false, financial_year: "FY2027", label: "FY 2027/28", closes_at: "2026-11-25 23:59:00" },
			needs: rows,
		});
		const notice = w.get('[data-testid="nds-submission-closed-notice"]');
		expect(notice.text()).toContain("Financial year");
		expect(notice.text()).toContain("FY 2027/28");
		expect(notice.text()).toContain("New submissions");
		expect(notice.text()).toContain("Closed at");
	});
});

// The register names each need's department, straight after the requirement —
// with several departments combined, the page filter no longer says which
// department a row belongs to.
describe("WorkspaceScreen — Department column", () => {
	const need = (overrides = {}) => ({
		name: "n1",
		reference: "NDS-MOH-2027-0001",
		title: "Health information exchange platform upgrade",
		organisation_unit: "OU-MOH-02501",
		organisation_unit_label: "Digital Health",
		author_label: "Grace Wanjiku",
		quantity_label: "1 programme",
		required_by_label: "31 Aug 2027",
		status: "Accepted for planning",
		actions: [{ code: "view", label: "View" }],
		...overrides,
	});
	const headers = (w) => w.findAll("thead th").map((th) => th.text());

	it("sits straight after Requirement in the author's own list", () => {
		const w = make({ needs: [need()] });
		expect(headers(w)).toEqual(["Requirement", "Department", "Quantity and required by", "Status", "Action"]);
		expect(w.get('[data-testid="nds-need-row"]').findAll("td")[1].text()).toBe("Digital Health");
	});

	it("sits straight after Requirement, before Requester, in the reviewer's register", () => {
		const queued = need({ name: "n2", reference: "NDS-MOH-2027-0002", actions: [{ code: "review", label: "Review", review_kind: "Initial requirement" }] });
		const w = make({ needs: [queued, need()] });
		expect(headers(w.get('[data-testid="nds-needs-table"]'))).toEqual([
			"Requirement", "Department", "Requester", "Quantity and required by", "Status", "Action",
		]);
	});
});
