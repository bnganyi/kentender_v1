// The shared Vue-in-Desk page runtime (kt_desk_page.js) had no test of its
// own; every page's routing depends on it. This covers `useRoute`, including
// the opt-in `hash` mode System setup needs (CFG-CHG-002 v0.14 §9 keeps its
// `#tab/section/id` links), so hash navigation gets the same one listener,
// pause-while-hidden and resume-epoch rules as path navigation instead of a
// hand-written `hashchange` listener per page (AGENTS.md §6.4).
import fs from "node:fs";
import path from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, nextTick, onActivated, onDeactivated, onMounted, onUnmounted, ref } from "vue";
import { mount } from "@vue/test-utils";

const SOURCE = fs.readFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), "kt_desk_page.js"), "utf8");

let routeHandlers;
let currentRoute;

function loadRuntime() {
	routeHandlers = [];
	currentRoute = ["system-setup"];
	globalThis.frappe = {
		provide(name) {
			const parts = name.split(".");
			let node = globalThis;
			for (const part of parts) node = node[part] = node[part] || {};
		},
		get_route: () => currentRoute.slice(),
		set_route: (...args) => {
			currentRoute = args.flat();
		},
		router: { on: (event, fn) => event === "change" && routeHandlers.push(fn) },
		pages: {},
		require: () => Promise.resolve(),
		ui: { make_app_page: () => ({}) },
	};
	globalThis.$ = () => ({ on: () => {} });
	globalThis.kentender_core = undefined;
	// eslint-disable-next-line no-new-func
	new Function(SOURCE)();
	return globalThis.kentender_core.desk_page;
}

function probe(desk, opts) {
	let api;
	const Probe = defineComponent({
		setup() {
			api = desk.useRoute({ ref, onMounted, onUnmounted, onActivated, onDeactivated }, "system-setup", opts);
			return () => h("div");
		},
	});
	const wrapper = mount(Probe);
	return { wrapper, api: () => api };
}

function setHash(value) {
	window.location.hash = value;
	window.dispatchEvent(new HashChangeEvent("hashchange"));
}

describe("desk_page.useRoute", () => {
	let desk;
	beforeEach(() => {
		history.replaceState(null, "", "/app/system-setup");
		desk = loadRuntime();
	});

	it("without the hash option, exposes the path route and ignores the fragment (unchanged behaviour)", async () => {
		const { api } = probe(desk);
		expect(api().route.value).toEqual(["system-setup"]);
		expect(api().hash).toBeUndefined();
		setHash("fiscal-years");
		await nextTick();
		expect(api().route.value).toEqual(["system-setup"]);
	});

	it("with the hash option, reads the fragment on mount, without the leading #", () => {
		history.replaceState(null, "", "/app/system-setup#procurement-settings/procurement-rules");
		const { api } = probe(desk, { hash: true });
		expect(api().hash.value).toBe("procurement-settings/procurement-rules");
	});

	it("follows a hash change through the one shared listener", async () => {
		const { api } = probe(desk, { hash: true });
		setHash("fiscal-years/2027-2028");
		await nextTick();
		expect(api().hash.value).toBe("fiscal-years/2027-2028");
	});

	it("goHash pushes a history entry; goHash with replace does not, and both update the state", async () => {
		const { api } = probe(desk, { hash: true });
		const before = history.length;
		api().goHash("procurement-settings");
		await nextTick();
		expect(api().hash.value).toBe("procurement-settings");
		expect(history.length).toBe(before + 1);
		api().goHash("procurement-settings/funding-sources", { replace: true });
		await nextTick();
		expect(api().hash.value).toBe("procurement-settings/funding-sources");
		expect(history.length).toBe(before + 1);
	});

	it("ignores a route that belongs to another page", async () => {
		// 26 Sep 2026 — a link from one module's page to another's (a need's
		// "Update departmental plan", "View annual plan item"): the router
		// announces the new route while the outgoing page is still shown, and
		// the outgoing app read it as its own record id ("need=DPP-…").
		const { api } = probe(desk);
		frappe.set_route("departmental-procurement-plan", "DPP-MOH-02314-2027-001");
		routeHandlers.forEach((fn) => fn());
		await nextTick();
		expect(api().route.value).toEqual(["system-setup"]);
		frappe.set_route("system-setup", "fiscal-years");
		routeHandlers.forEach((fn) => fn());
		await nextTick();
		expect(api().route.value).toEqual(["system-setup", "fiscal-years"]);
	});

	it("follows a route to another page of its own group", async () => {
		frappe.pages["system-setup"] = {};
		desk.register("system-setup", { mount: () => ({}), pages: ["system-setup-sibling"] });
		frappe.pages["system-setup"].on_page_show(document.createElement("div"));
		const { api } = probe(desk);
		frappe.set_route("system-setup-sibling", "x");
		routeHandlers.forEach((fn) => fn());
		await nextTick();
		expect(api().route.value).toEqual(["system-setup-sibling", "x"]);
	});

	it("stops following once unmounted", async () => {
		const { wrapper, api } = probe(desk, { hash: true });
		const held = api();
		wrapper.unmount();
		setHash("organisation-structure");
		await nextTick();
		expect(held.hash.value).not.toBe("organisation-structure");
	});
});

// GitHub #14 (29 Sep 2026) — a screen with unsaved work warned only when the
// user left through the screen's own tabs and links; the rail breadcrumb, the
// sidebar and browser back/forward left silently. `addLeaveGuard` puts one
// guard in front of Frappe's router so every route change asks first.
describe("desk_page.addLeaveGuard", () => {
	let desk;
	let pushed;
	let routed;

	beforeEach(() => {
		history.replaceState(null, "", "/app/strategy/plan/P-1");
		desk = loadRuntime();
		pushed = [];
		routed = [];
		frappe.router.push_state = function (path, query = "") {
			pushed.push(path + query);
			history.pushState(null, "", path + query);
			this.route();
		};
		frappe.router.route = function () {
			routed.push(window.location.pathname + window.location.search);
			return Promise.resolve();
		};
	});

	it("lets every route change through while no guard is registered", () => {
		frappe.router.push_state("/app/todo");
		expect(pushed).toEqual(["/app/todo"]);
		expect(routed).toEqual(["/app/todo"]);
	});

	it("lets a route change through when the guard has nothing to protect", () => {
		desk.addLeaveGuard(() => false);
		frappe.router.push_state("/app/todo");
		expect(pushed).toEqual(["/app/todo"]);
		expect(window.location.pathname).toBe("/app/todo");
	});

	it("holds a link, rail or sidebar route change until the guard proceeds, then makes it once", () => {
		let proceed;
		desk.addLeaveGuard((p) => {
			proceed = p;
			return true;
		});
		frappe.router.push_state("/app/todo");
		expect(pushed).toEqual([]);
		expect(window.location.pathname).toBe("/app/strategy/plan/P-1");
		proceed();
		expect(pushed).toEqual(["/app/todo"]);
		expect(routed).toEqual(["/app/todo"]);
		expect(window.location.pathname).toBe("/app/todo");
	});

	it("puts the page's URL back when browser back is held, and goes back once when the guard proceeds", () => {
		history.pushState(null, "", "/app/strategy/plan/P-1/version/2");
		frappe.router.route(); // the page as Frappe last routed it
		routed = [];
		let proceed;
		desk.addLeaveGuard((p) => {
			proceed = p;
			return true;
		});
		// The browser has already moved when popstate reaches Frappe's router.
		history.replaceState(null, "", "/app/strategy/plan/P-1");
		frappe.router.route();
		expect(routed).toEqual([]);
		expect(window.location.pathname).toBe("/app/strategy/plan/P-1/version/2");
		const back = vi.spyOn(history, "back").mockImplementation(() => {});
		proceed();
		expect(back).toHaveBeenCalledTimes(1);
		// The traversal that follows is not asked again.
		history.replaceState(null, "", "/app/strategy/plan/P-1");
		frappe.router.route();
		expect(routed).toEqual(["/app/strategy/plan/P-1"]);
		back.mockRestore();
	});

	it("does not treat a same-URL re-route as leaving", () => {
		const guard = vi.fn(() => true);
		desk.addLeaveGuard(guard);
		frappe.router.route();
		expect(guard).not.toHaveBeenCalled();
		expect(routed).toEqual(["/app/strategy/plan/P-1"]);
	});

	it("stops asking once the guard is removed", () => {
		const remove = desk.addLeaveGuard(() => true);
		remove();
		frappe.router.push_state("/app/todo");
		expect(pushed).toEqual(["/app/todo"]);
	});
});
