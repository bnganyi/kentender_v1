// The public portal runtime (BDS-CHG-001 v0.8 plan OD-B): surface mount,
// History-API routing, link interception, bfcache revalidation, the
// fetch-based call and its error shape, and — against kt_desk_page.js
// itself — identical command-runner, sequence-guard and screen-cache
// behaviour, so the two runtimes cannot drift apart.
import fs from "node:fs";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, nextTick, onMounted, onUnmounted, ref } from "vue";
import { mount } from "@vue/test-utils";
import { createPortalRuntime, toError } from "./runtime.js";

const HERE = path.dirname(new URL(import.meta.url).pathname);
const DESK_SOURCE = fs.readFileSync(path.join(HERE, "..", "kt_desk_page.js"), "utf8");

function loadDeskRuntime() {
	globalThis.frappe = {
		provide(name) {
			let node = globalThis;
			for (const part of name.split(".")) node = node[part] = node[part] || {};
		},
		get_route: () => [],
		router: { on: () => {} },
		pages: {},
	};
	globalThis.$ = () => ({ on: () => {} });
	globalThis.kentender_core = undefined;
	// eslint-disable-next-line no-new-func
	new Function(DESK_SOURCE)();
	return globalThis.kentender_core.desk_page;
}

function page(surface, initial = {}) {
	document.body.innerHTML = `
		<header><nav>
			<a href="/tenders" data-kt-portal-nav="tenders">Tenders</a>
			<a href="/my-bids" data-kt-portal-nav="my-bids">My bids</a>
			<a href="/account" data-kt-portal-nav="account">Account</a>
		</nav></header>
		<main id="kt-portal-main" tabindex="-1"><div id="kt-portal-app"></div></main>
		<script type="application/json" id="kt-portal-initial">${JSON.stringify(initial)}</script>`;
	document.body.dataset.ktPortalSurface = surface;
}

function probe(portal) {
	let api;
	const Probe = defineComponent({
		setup() {
			api = portal.useRoute({ ref, onMounted, onUnmounted });
			return () => h("div");
		},
	});
	const wrapper = mount(Probe, { attachTo: document.getElementById("kt-portal-app") });
	return { wrapper, api: () => api };
}

describe("portal_page shared helpers match desk_page", () => {
	const desk = loadDeskRuntime();
	const portal = createPortalRuntime(window);
	for (const [name, runtime] of [["desk_page", desk], ["portal_page", portal]]) {
		it(`${name}: the command runner holds pending across the call and reports errors`, async () => {
			const errors = [];
			const { pending, run } = runtime.createCommandRunner({ ref }, { onError: (e, label) => errors.push([e.message, label]), mintKey: (label) => `key-${label}` });
			let seenKey;
			const first = run(async (key) => {
				seenKey = key;
				expect(pending.value).toBe(true);
				return "done";
			}, "save");
			expect(await run(async () => "second", "save")).toBe(null);
			expect(await first).toBe("done");
			expect(pending.value).toBe(false);
			expect(seenKey).toBe("key-save");
			expect(await run(async () => { throw new Error("boom"); }, "submit")).toBe(null);
			expect(errors).toEqual([["boom", "submit"]]);
		});
		it(`${name}: the sequence guard keeps only the newest token current`, () => {
			const guard = runtime.createSequenceGuard();
			const a = guard.next();
			const b = guard.next();
			expect([guard.isCurrent(a), guard.isCurrent(b)]).toEqual([false, true]);
		});
		it(`${name}: the screen cache stores, removes and clears`, () => {
			const cache = runtime.createScreenCache();
			cache.set("a", 1);
			expect([cache.has("a"), cache.get("a")]).toEqual([true, 1]);
			cache.remove("a");
			cache.set("b", 2);
			cache.clear();
			expect([cache.has("a"), cache.has("b")]).toEqual([false, false]);
		});
	}
});

describe("portal_page.register and useRoute", () => {
	let portal;
	beforeEach(() => {
		window.history.replaceState(null, "", "/tenders");
		page("tenders", { verdict: "OK", payload: { rows: [1] } });
		portal = createPortalRuntime(window);
	});
	afterEach(() => {
		portal.dispose();
		document.body.innerHTML = "";
	});

	it("mounts once, only on the page whose surface registered, with the first payload", () => {
		const other = vi.fn();
		portal.register("account", { prefixes: ["/account"], mount: other });
		expect(other).not.toHaveBeenCalled();
		const mountFn = vi.fn(() => "app");
		expect(portal.register("tenders", { prefixes: ["/tenders"], mount: mountFn })).toBe("app");
		expect(mountFn.mock.calls[0][1].initial).toEqual({ verdict: "OK", payload: { rows: [1] } });
		portal.register("tenders", { prefixes: ["/tenders"], mount: mountFn });
		expect(mountFn).toHaveBeenCalledTimes(1);
	});

	it("moves between owned paths in-app, marks the header and follows back/forward", async () => {
		portal.register("tenders", { prefixes: ["/tenders", "/my-bids"], mount: () => null });
		const { api } = probe(portal);
		api().go("/my-bids", { query: { status: "Draft", empty: "" } });
		expect(window.location.pathname + window.location.search).toBe("/my-bids?status=Draft");
		expect(api().route.value).toMatchObject({ path: "/my-bids", segments: ["my-bids"], query: { status: "Draft" } });
		expect(document.querySelector('[data-kt-portal-nav="my-bids"]').getAttribute("aria-current")).toBe("page");
		expect(document.querySelector('[data-kt-portal-nav="tenders"]').hasAttribute("aria-current")).toBe(false);
		window.history.replaceState(null, "", "/tenders/TND-1");
		window.dispatchEvent(new PopStateEvent("popstate"));
		await nextTick();
		expect(api().route.value.segments).toEqual(["tenders", "TND-1"]);
	});

	it("loads a path another surface owns as a full page", () => {
		portal.register("tenders", { prefixes: ["/tenders"], mount: () => null });
		const { api } = probe(portal);
		const assign = vi.fn();
		const original = window.location;
		Object.defineProperty(window, "location", { configurable: true, value: { ...original, href: original.href, origin: original.origin, assign } });
		try {
			api().go("/account");
			expect(assign).toHaveBeenCalledWith("/account");
		} finally {
			Object.defineProperty(window, "location", { configurable: true, value: original });
		}
	});

	it("leaves a longer prefix another surface owns to that surface (the server's longest-prefix rule)", () => {
		// the Account page: /account is Supplier Accounts', /account/receipts Bid Submission's
		window.history.replaceState(null, "", "/account");
		page("account", { verdict: "OK", owners: [{ prefix: "/tenders", key: "tenders" }, { prefix: "/account", key: "account" }, { prefix: "/account/receipts", key: "tenders" }] });
		portal.dispose();
		portal = createPortalRuntime(window);
		portal.register("account", { prefixes: ["/account"], mount: () => null });
		const { api } = probe(portal);
		const assign = vi.fn();
		const original = window.location;
		Object.defineProperty(window, "location", { configurable: true, value: { ...original, href: original.href, origin: original.origin, assign } });
		try {
			api().go("/account/receipts");
			expect(assign).toHaveBeenCalledWith("/account/receipts");
		} finally {
			Object.defineProperty(window, "location", { configurable: true, value: original });
		}
		api().go("/account/register"); // still this surface's own path
		expect(api().route.value.path).toBe("/account/register");
	});

	it("revalidates in place when restored from the back/forward cache", () => {
		portal.register("tenders", { prefixes: ["/tenders"], mount: () => null });
		const { api } = probe(portal);
		const event = new Event("pageshow");
		event.persisted = true;
		window.dispatchEvent(event);
		expect(api().epoch.value).toBe(1);
	});

	it("intercepts plain clicks on owned links only", () => {
		portal.register("tenders", { prefixes: ["/tenders"], mount: () => null });
		const { api } = probe(portal);
		const link = document.createElement("a");
		link.href = "/tenders/TND-2";
		document.getElementById("kt-portal-app").appendChild(link);
		const modified = new MouseEvent("click", { bubbles: true, cancelable: true, ctrlKey: true });
		link.dispatchEvent(modified);
		expect(modified.defaultPrevented).toBe(false);
		const plain = new MouseEvent("click", { bubbles: true, cancelable: true });
		link.dispatchEvent(plain);
		expect(plain.defaultPrevented).toBe(true);
		expect(api().route.value.path).toBe("/tenders/TND-2");
		const foreign = document.querySelector('[data-kt-portal-nav="account"]');
		const away = new MouseEvent("click", { bubbles: true, cancelable: true });
		foreign.addEventListener("click", (e) => e.preventDefault());
		foreign.dispatchEvent(away);
		expect(api().route.value.path).toBe("/tenders/TND-2");
	});
});

describe("portal_page.call", () => {
	afterEach(() => {
		vi.restoreAllMocks();
	});

	it("sends GET arguments as a query and POST arguments as JSON with the CSRF header", async () => {
		window.frappe = { csrf_token: "tok-1", msgprint: vi.fn() };
		const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ message: { rows: [] } }) }));
		window.fetch = fetchMock;
		const portal = createPortalRuntime(window);
		expect(await portal.call("kt.read", { search: "laptops", skip: null, filters: { a: 1 } })).toEqual({ rows: [] });
		expect(fetchMock.mock.calls[0][0]).toBe("/api/method/kt.read?search=laptops&filters=%7B%22a%22%3A1%7D");
		await portal.call("kt.save", { value: 2 }, { type: "POST" });
		const [url, init] = fetchMock.mock.calls[1];
		expect([url, init.method, init.headers["X-Frappe-CSRF-Token"], init.body]).toEqual(["/api/method/kt.save", "POST", "tok-1", '{"value":2}']);
		expect(window.frappe.msgprint).not.toHaveBeenCalled();
	});

	it("turns a failed response into an Error with the KenTender code, detail and status", async () => {
		window.frappe = { csrf_token: "", msgprint: vi.fn() };
		window.fetch = vi.fn(async () => ({ ok: false, status: 417, json: async () => ({ exc_type: "ValidationError", kt_error_code: "BDS_STALE_VERSION", kt_error_message: "This bid changed.", kt_error_detail: { task: "company" } }) }));
		const portal = createPortalRuntime(window);
		await expect(portal.call("kt.save", {}, { type: "POST" })).rejects.toMatchObject({ message: "This bid changed.", status: 417, code: "BDS_STALE_VERSION", detail: { task: "company" } });
		expect(window.frappe.msgprint).not.toHaveBeenCalled();
	});

	it("uploads fields and files as multipart with the CSRF header and the same error contract", async () => {
		window.frappe = { csrf_token: "tok-2", msgprint: vi.fn() };
		const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ message: { ok: true } }) }));
		window.fetch = fetchMock;
		const portal = createPortalRuntime(window);
		const file = new File(["%PDF-1.4"], "authority.pdf", { type: "application/pdf" });
		expect(await portal.upload("kt.register", { legal_name: "Afya", skip: undefined }, { authority_evidence: file })).toEqual({ ok: true });
		const [url, init] = fetchMock.mock.calls[0];
		expect([url, init.method, init.headers["X-Frappe-CSRF-Token"], init.body.get("legal_name"), init.body.get("authority_evidence").name, init.body.has("skip")]).toEqual(["/api/method/kt.register", "POST", "tok-2", "Afya", "authority.pdf", false]);
		window.fetch = vi.fn(async () => ({ ok: false, status: 417, json: async () => ({ kt_error_code: "BDS_EVIDENCE_REJECTED", kt_error_message: "This file could not be accepted." }) }));
		await expect(portal.upload("kt.register", {}, {})).rejects.toMatchObject({ code: "BDS_EVIDENCE_REJECTED", status: 417 });
	});

	it("reads Frappe server messages as plain text and falls back by status", () => {
		const messages = JSON.stringify([JSON.stringify({ message: "<b>Not permitted</b>" })]);
		expect(toError(403, { exc_type: "PermissionError", _server_messages: messages })).toMatchObject({ message: "Not permitted", code: "PermissionError", status: 403 });
		expect(toError(500, {}).message).toBe("The service could not complete this request. Your saved work is unchanged. Try again.");
		expect(toError(0, {}).status).toBe(0);
	});
});
