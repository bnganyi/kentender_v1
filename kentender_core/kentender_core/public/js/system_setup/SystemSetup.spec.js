// CFG-CHG-002 v0.14 §9 and AGENTS.md §6.4 — the System setup root: the URL
// is read only through the shared route adapter (real kt_desk_page.js here,
// not a stub), tabs stay alive between visits, and the skeleton appears only
// when there is nothing to show yet.
import fs from "node:fs";
import path from "node:path";
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, nextTick, onMounted } from "vue";

const api = vi.hoisted(() => ({ getConfiguration: vi.fn() }));
vi.mock("./data/siteConfigApi.js", () => ({ siteConfigApi: api }));
vi.mock("./composables/usePageRail.js", () => ({ usePageRail: () => {} }));

const mounts = {};
function stubTab(name) {
	return defineComponent({
		name,
		props: { site: Object, subpath: String, route: Object, canRepair: Boolean, initialUnit: String, onUpdated: Function },
		setup(props) {
			onMounted(() => (mounts[name] = (mounts[name] || 0) + 1));
			return () => h("div", { "data-testid": `stub-${name}`, "data-subpath": props.subpath ?? "", "data-section": props.route?.section ?? "" });
		},
	});
}
vi.mock("./tabs/ProcuringEntityTab.vue", () => ({ default: stubTab("ProcuringEntityTab") }));
vi.mock("./tabs/FiscalYearsTab.vue", () => ({ default: stubTab("FiscalYearsTab") }));
vi.mock("./tabs/OrganisationStructureTab.vue", () => ({ default: stubTab("OrganisationStructureTab") }));
vi.mock("./tabs/UserResponsibilitiesTab.vue", () => ({ default: stubTab("UserResponsibilitiesTab") }));
vi.mock("./tabs/ProcurementSettingsTab.vue", () => ({ default: stubTab("ProcurementSettingsTab") }));

import SystemSetup from "./SystemSetup.vue";
import { globalMocks } from "./components/spec_helpers.js";

const RUNTIME = fs.readFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), "..", "kt_desk_page.js"), "utf8");
let saved;
function loadRealRuntime() {
	saved = { frappe: globalThis.frappe, kentender_core: globalThis.kentender_core, $: globalThis.$ };
	globalThis.frappe = {
		provide(name) {
			let node = globalThis;
			for (const part of name.split(".")) node = node[part] = node[part] || {};
		},
		get_route: () => ["system-setup"],
		set_route: () => {},
		router: { on: () => {} },
		pages: {},
		require: () => Promise.resolve(),
		ui: { make_app_page: () => ({}) },
	};
	globalThis.$ = () => ({ on: () => {} });
	const keep = globalThis.kentender_core;
	globalThis.kentender_core = undefined;
	// eslint-disable-next-line no-new-func
	new Function(RUNTIME)();
	globalThis.kentender_core = { ...keep, desk_page: globalThis.kentender_core.desk_page };
}

const CONFIGURED = { configured: true, root_unit: { name: "Ministry of Health", code: "PE-MOH" }, capabilities: {} };

function at(hash) {
	history.replaceState(null, "", `/app/system-setup${hash ? "#" + hash : ""}`);
}
// Every root is unmounted after its test: a live root keeps listening to the
// one shared address bar and would correct the next test's navigation.
const live = [];
function mountLive() {
	const wrapper = mount(SystemSetup, { global: globalMocks(), attachTo: document.body });
	live.push(wrapper);
	return wrapper;
}
async function mountRoot() {
	const wrapper = mountLive();
	await flushPromises();
	return wrapper;
}

describe("SystemSetup root", () => {
	beforeEach(() => {
		for (const key of Object.keys(mounts)) delete mounts[key];
		api.getConfiguration.mockReset();
		loadRealRuntime();
	});
	afterEach(() => {
		while (live.length) live.pop().unmount();
		Object.assign(globalThis, saved);
		document.body.innerHTML = "";
	});

	it("opens the tab the link names, and passes Procurement settings its parsed §9 route", async () => {
		api.getConfiguration.mockResolvedValue(CONFIGURED);
		at("procurement-settings/procurement-rules");
		const wrapper = await mountRoot();
		const tab = wrapper.find('[data-testid="stub-ProcurementSettingsTab"]');
		expect(tab.exists()).toBe(true);
		expect(tab.attributes("data-section")).toBe("procurement-rules");
	});

	it("with no link, an unconfigured site lands on Procuring entity and the address says so, without a Back step", async () => {
		api.getConfiguration.mockResolvedValue({ configured: false });
		at("");
		const before = history.length;
		const wrapper = await mountRoot();
		expect(wrapper.find('[data-testid="stub-ProcuringEntityTab"]').exists()).toBe(true);
		expect(window.location.hash).toBe("#procuring-entity");
		expect(history.length).toBe(before);
	});

	it("a link to a tab first run does not allow falls back to Procuring entity (replacing, not adding, the entry)", async () => {
		api.getConfiguration.mockResolvedValue({ configured: false });
		at("fiscal-years");
		const wrapper = await mountRoot();
		expect(wrapper.find('[data-testid="stub-ProcuringEntityTab"]').exists()).toBe(true);
		expect(window.location.hash).toBe("#procuring-entity");
	});

	it("with the root unit missing and no link, lands on Organisation structure, the first incomplete setup (§9)", async () => {
		api.getConfiguration.mockResolvedValue({ configured: true, root_unit: null, capabilities: {} });
		at("");
		const wrapper = await mountRoot();
		expect(wrapper.find('[data-testid="stub-OrganisationStructureTab"]').exists()).toBe(true);
	});

	it("follows a hash change, and translates the fiscal-year detail link for the current tab", async () => {
		api.getConfiguration.mockResolvedValue(CONFIGURED);
		at("procuring-entity");
		const wrapper = await mountRoot();
		window.location.hash = "fiscal-years/2027-2028";
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await nextTick();
		await nextTick();
		const tab = wrapper.find('[data-testid="stub-FiscalYearsTab"]');
		expect(tab.exists()).toBe(true);
		expect(tab.attributes("data-subpath")).toBe("year/2027-2028");
	});

	it("a Procurement settings section named from another tab crosses to that tab (Procuring entity's View procurement rules)", async () => {
		api.getConfiguration.mockResolvedValue(CONFIGURED);
		at("procuring-entity");
		const wrapper = await mountRoot();
		wrapper.findComponent({ name: "ProcuringEntityTab" }).vm.$emit("navigate", "procurement-rules");
		await flushPromises();
		expect(window.location.hash).toBe("#procurement-settings/procurement-rules");
		expect(wrapper.find('[data-testid="stub-ProcurementSettingsTab"]').attributes("data-section")).toBe("procurement-rules");
	});

	it("keeps a visited tab alive: going away and back does not mount it again", async () => {
		api.getConfiguration.mockResolvedValue(CONFIGURED);
		at("fiscal-years");
		const wrapper = await mountRoot();
		await wrapper.find('[data-testid="kt-setup-tab-procuring-entity"]').trigger("click");
		await flushPromises();
		await wrapper.find('[data-testid="kt-setup-tab-fiscal-years"]').trigger("click");
		await flushPromises();
		expect(mounts.FiscalYearsTab).toBe(1);
		expect(window.location.hash).toBe("#fiscal-years");
	});

	it("Common-States: loading, denied and failed-to-load paint only the state, never the page heading or tabs", async () => {
		let resolve;
		api.getConfiguration.mockImplementationOnce(() => new Promise((r) => (resolve = r)));
		at("procuring-entity");
		const loading = mountLive();
		await nextTick();
		expect(loading.find('[data-testid="kt-setup-loading"]').text()).toBe("Loading System setup…");
		expect(loading.find('[data-testid="kt-setup-loading"]').attributes("role")).toBe("status");
		expect(loading.find(".kt-setup-head").exists()).toBe(false);
		resolve(CONFIGURED);
		await flushPromises();
		expect(loading.find(".kt-setup-head").exists()).toBe(true);

		api.getConfiguration.mockResolvedValueOnce({
			outcome: "FORBIDDEN",
			forbidden: { heading: "You do not have access to System setup", text: "This area needs Administrator or System Manager access. Ask your KenTender administrator to grant it." },
		});
		const denied = await mountRoot();
		// The shared access state: lock spot, heading, then the reason and the hint as separate paragraphs.
		const notice = denied.find('[data-testid="kt-setup-forbidden"]');
		expect(notice.classes()).toEqual(expect.arrayContaining(["kt-empty", "kt-access"]));
		expect(notice.find("h2").text()).toBe("You do not have access to System setup");
		expect(notice.findAll("p").map((p) => p.text())).toEqual([
			"This area needs Administrator or System Manager access.",
			"Ask your KenTender administrator to grant it.",
		]);
		expect(denied.find(".kt-setup-head").exists()).toBe(false);
		expect(denied.find('[data-testid="kt-setup-tabs"]').exists()).toBe(false);

		api.getConfiguration.mockRejectedValueOnce(new Error("boom"));
		const failed = await mountRoot();
		expect(failed.find('[data-testid="kt-setup-error"] .kt-notice').text()).toBe(
			"System setup could not be loaded.Try again. If the problem continues, contact support."
		);
		expect(failed.find(".kt-setup-head").exists()).toBe(false);
		api.getConfiguration.mockResolvedValueOnce(CONFIGURED);
		await failed.find('[data-testid="kt-setup-retry"]').trigger("click");
		await flushPromises();
		expect(failed.find(".kt-setup-head").exists()).toBe(true);
	});

	it("shows the loading skeleton only on a cold load; a later refresh keeps the content on screen", async () => {
		let resolve;
		api.getConfiguration.mockImplementationOnce(() => new Promise((r) => (resolve = r)));
		at("procuring-entity");
		const wrapper = mountLive();
		await nextTick();
		expect(wrapper.find('[data-testid="kt-setup-loading"]').exists()).toBe(true);
		resolve(CONFIGURED);
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-setup-loading"]').exists()).toBe(false);

		let resolveAgain;
		api.getConfiguration.mockImplementationOnce(() => new Promise((r) => (resolveAgain = r)));
		const refresh = wrapper.findComponent({ name: "ProcuringEntityTab" }).props("onUpdated");
		const pending = refresh();
		await nextTick();
		expect(wrapper.find('[data-testid="kt-setup-loading"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="stub-ProcuringEntityTab"]').exists()).toBe(true);
		resolveAgain(CONFIGURED);
		await pending;
	});

	it("a slower, older response never overwrites a newer one", async () => {
		api.getConfiguration.mockResolvedValueOnce(CONFIGURED);
		at("procuring-entity");
		const wrapper = await mountRoot();
		let slow;
		api.getConfiguration.mockImplementationOnce(() => new Promise((r) => (slow = r)));
		api.getConfiguration.mockResolvedValueOnce({ ...CONFIGURED, marker: "newer" });
		const refresh = wrapper.findComponent({ name: "ProcuringEntityTab" }).props("onUpdated");
		const first = refresh();
		await refresh();
		slow({ ...CONFIGURED, marker: "older" });
		await first;
		await flushPromises();
		expect(wrapper.findComponent({ name: "ProcuringEntityTab" }).props("site").marker).toBe("newer");
	});
});
