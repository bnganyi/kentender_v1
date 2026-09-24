// AUTH-ADR-001 v1.9 §13.9 AUTH-DES-08 (checked in CFG-CHG-002 v0.14 phase 5H,
// tracker CFG14-5H) — the Organisation structure tab's empty and missing-root
// states, with the exact v1.9 copy: an empty root offers "Add organisation
// unit"; a missing root offers no create action, the Administrator the
// governed repair, and a System Manager the escalation instead.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "../components/spec_helpers.js";

const api = vi.hoisted(() => ({ getStructure: vi.fn(), repairRoot: vi.fn() }));
vi.mock("../data/orgStructureApi.js", () => ({ orgStructureApi: api }));
vi.mock("../data/siteConfigApi.js", () => ({ siteConfigApi: {} }));

import OrganisationStructureTab from "./OrganisationStructureTab.vue";

// The selected unit as the server sends it (UnitDetail reads every field).
const ROOT = {
	id: "OU-MOH",
	name: "Ministry of Health",
	code: "MOH",
	status: "Active",
	path: ["Ministry of Health"],
	descendant_count: 0,
	active_assignments: 0,
	actions: { add_child: true, rename: true, deactivate: false, reactivate: false },
};

describe("OrganisationStructureTab — AUTH-DES-08 states", () => {
	let saved;
	beforeEach(() => {
		vi.clearAllMocks();
		// frappe.ui.Tree draws the tree itself; these states are about what
		// surrounds it, so the widget is a stand-in here.
		saved = { frappe: globalThis.frappe, $: globalThis.$ };
		globalThis.frappe = { ...(globalThis.frappe || {}), ui: { Tree: class { constructor() {} } } };
		globalThis.$ = (el) => el;
	});
	afterEach(() => Object.assign(globalThis, saved));

	it("an empty root says so with the v1.9 copy and offers Add organisation unit", async () => {
		api.getStructure.mockResolvedValue({ state: "empty_root", root: "OU-MOH", tree: [{ unit_code: "MOH", status: "Active" }], selected: ROOT });
		const wrapper = mount(OrganisationStructureTab, { props: { canRepair: true }, global: globalMocks() });
		await flushPromises();
		const empty = wrapper.find('[data-testid="kt-org-empty"]');
		expect(empty.find("h3").text()).toBe("No departments or units yet");
		expect(empty.text()).toContain("Add the first organisation unit beneath Ministry of Health.");
		const add = empty.find('[data-testid="kt-org-empty-add"]');
		expect(add.text()).toBe("Add organisation unit");
		expect(add.classes()).toContain("kt-btn-primary");
		// Opening the dialog is proven in the browser (system-setup-worlds.spec),
		// where Frappe's real tree widget runs.
	});

	it("a missing root offers no create action: the governed repair for the Administrator, the escalation for a System Manager", async () => {
		api.getStructure.mockResolvedValue({ state: "needs_repair", root: "", tree: [], selected: null });
		const admin = mount(OrganisationStructureTab, { props: { canRepair: true }, global: globalMocks() });
		await flushPromises();
		const repair = admin.find('[data-testid="kt-org-needs-repair"]');
		expect(repair.text()).toContain("Organisation structure needs repair");
		expect(repair.text()).toContain("The root organisation unit is missing. Run the governed repair before assigning responsibilities.");
		expect(admin.find('[data-testid="kt-org-repair"]').exists()).toBe(true);
		expect(admin.find('[data-testid="kt-org-empty-add"]').exists()).toBe(false);

		const manager = mount(OrganisationStructureTab, { props: { canRepair: false }, global: globalMocks() });
		await flushPromises();
		expect(manager.find('[data-testid="kt-org-repair"]').exists()).toBe(false);
		expect(manager.find('[data-testid="kt-org-repair-escalation"]').text()).toBe("Only the Administrator can run this repair. Ask an Administrator to run it.");
	});
});
