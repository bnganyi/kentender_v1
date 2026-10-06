// C05-Organisation-Structure.dc.html #auth-des-08-* (D24) — the Organisation
// structure tab's empty, missing-root and ambiguous states: an empty root
// offers "Add organisation unit"; a missing root offers no create action, the
// Administrator the governed repair and a System Manager the escalation; an
// ambiguous tree offers neither.
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

	it("an empty root shows the board's empty state alone and adds beneath the root", async () => {
		api.getStructure.mockResolvedValue({ state: "empty_root", root: "OU-MOH", tree: [{ unit_code: "MOH", status: "Active" }], selected: ROOT });
		const wrapper = mount(OrganisationStructureTab, { props: { canRepair: true }, global: globalMocks(), attachTo: document.body });
		await flushPromises();
		const empty = wrapper.find('[data-testid="kt-org-empty"]');
		expect(empty.find("p").text()).toBe("No departments or units yet");
		expect(empty.text()).toContain("Add the first organisation unit beneath Ministry of Health.");
		expect(wrapper.find('[data-testid="kt-org-tree"]').exists()).toBe(false);
		const add = empty.find('[data-testid="kt-org-empty-add"]');
		expect(add.text()).toBe("Add organisation unit");
		expect(add.classes()).toContain("btn-primary");

		await add.trigger("click");
		const dialog = wrapper.find('[data-testid="kt-ou-prompt"]');
		expect(dialog.find(".dialog-title").text()).toBe("Add organisation unit");
		expect(dialog.find("#kt-prompt-context-0").element.value).toBe("Ministry of Health");
		expect(dialog.find("#kt-prompt-context-0").attributes("readonly")).toBeDefined();
		expect(dialog.text()).toContain("The unit code is generated when you save.");
		wrapper.unmount();
	});

	it("a missing root offers no create action: Repair organisation root for the Administrator, the escalation for a System Manager (D24)", async () => {
		api.getStructure.mockResolvedValue({ state: "needs_repair", root: "", tree: [], selected: null });
		const admin = mount(OrganisationStructureTab, { props: { canRepair: true }, global: globalMocks() });
		await flushPromises();
		const repair = admin.find('[data-testid="kt-org-needs-repair"]');
		expect(repair.classes()).toEqual(expect.arrayContaining(["kt-notice", "is-critical"]));
		expect(repair.find("strong").text()).toBe("Organisation structure needs repair");
		expect(repair.text()).toContain("The top-level organisation unit is missing.");
		expect(admin.find('[data-testid="kt-org-repair"]').text()).toBe("Repair organisation root");
		expect(admin.find('[data-testid="kt-org-empty-add"]').exists()).toBe(false);

		const manager = mount(OrganisationStructureTab, { props: { canRepair: false }, global: globalMocks() });
		await flushPromises();
		expect(manager.find('[data-testid="kt-org-repair"]').exists()).toBe(false);
		expect(manager.find('[data-testid="kt-org-repair-escalation"]').text()).toBe("Ask an Administrator to repair it.");
	});

	it("an ambiguous structure lists the server's conflicts and offers no repair to either role", async () => {
		const conflicts = ["More than one top-level organisation unit: Ministry of Health (PE-MOH), Stray (OU-X)."];
		api.getStructure.mockResolvedValue({ state: "ambiguous", tree: [], conflicts });
		for (const canRepair of [true, false]) {
			const wrapper = mount(OrganisationStructureTab, { props: { canRepair }, global: globalMocks() });
			await flushPromises();
			const notice = wrapper.find('[data-testid="kt-org-ambiguous"]');
			expect(notice.text()).toContain("The organisation structure cannot be repaired automatically.");
			expect(notice.text()).toContain("Contact support with the listed conflicts.");
			expect(notice.findAll('[data-testid="kt-org-conflicts"] li').map((li) => li.text())).toEqual(conflicts);
			expect(wrapper.find('[data-testid="kt-org-repair"]').exists()).toBe(false);
		}
	});

	it("keeps the linked unit when the tree control selects its root while loading — only a person's click changes the link", async () => {
		// frappe.ui.Tree calls on_click for the root as it expands it on load.
		let options;
		globalThis.frappe.ui.Tree = class {
			constructor(opts) {
				options = opts;
				this.nodes = {};
				this.root_node = null;
			}
		};
		api.getStructure.mockResolvedValue({ state: "ready", root: "OU-MOH", tree: [{ unit_code: "MOH", status: "Active" }], selected: { ...ROOT, id: "OU-MOH-DHP", name: "Directorate", path: ["Ministry of Health", "Directorate"] } });
		const wrapper = mount(OrganisationStructureTab, { props: { unitId: "OU-MOH-DHP" }, global: globalMocks(), attachTo: document.body });
		await flushPromises();
		options.on_click({ is_root: true, value: "OU-MOH", data: { value: "OU-MOH" } });
		await new Promise((resolve) => setTimeout(resolve, 150));
		expect(wrapper.emitted("open")).toBeUndefined();

		// A real click in the tree, then the control's (delayed) on_click.
		wrapper.find('[data-testid="kt-org-tree"] .kt-org-tree-host').element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
		options.on_click({ value: "OU-MOH-HR", data: { value: "OU-MOH-HR" } });
		expect(wrapper.emitted("open")).toEqual([["OU-MOH-HR"]]);
		wrapper.unmount();
	});

	it("reads the unit named by the link", async () => {
		api.getStructure.mockResolvedValue({ state: "empty_root", root: "OU-MOH", tree: [], selected: ROOT });
		mount(OrganisationStructureTab, { props: { unitId: "OU-MOH-DHP" }, global: globalMocks() });
		await flushPromises();
		expect(api.getStructure).toHaveBeenCalledWith("OU-MOH-DHP");
	});
});
