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

	it("leaves a link to an anchor on the same page to the browser", () => {
		portal.register("tenders", { prefixes: ["/tenders"], mount: () => null });
		const { api } = probe(portal);
		const before = api().route.value.path;
		const link = document.createElement("a");
		link.href = `${window.location.pathname}${window.location.search}#bds-tender-documents`;
		document.getElementById("kt-portal-app").appendChild(link);
		const click = new MouseEvent("click", { bubbles: true, cancelable: true });
		link.dispatchEvent(click);
		expect(click.defaultPrevented).toBe(false);
		expect(api().route.value.path).toBe(before);
	});
});
