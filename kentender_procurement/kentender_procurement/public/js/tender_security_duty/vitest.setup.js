// The Desk globals the page expects (AGENTS.md §6.1): the shared runtime's
// sequence guard and screen cache as the real kt_desk_page.js defines them;
// routes, rail and server calls are mocked per spec.
import { vi } from "vitest";

globalThis.__ = (s) => s;
globalThis.frappe = { set_route: vi.fn(), call: vi.fn() };
globalThis.kentender_core = {
	desk_page: {
		createSequenceGuard() {
			let token = 0;
			return { next: () => ++token, isCurrent: (candidate) => candidate === token };
		},
		createScreenCache() {
			const store = new Map();
			return { get: (k) => store.get(k), has: (k) => store.has(k), set: (k, v) => store.set(k, v), remove: (k) => store.delete(k) };
		},
	},
};
// The register hosts kentender_core's shared table pager (kt_industry_pager.bundle.js in the browser).
globalThis.frappe.provide = (path) => {
	let node = globalThis;
	for (const part of path.split(".")) {
		node[part] = node[part] || {};
		node = node[part];
	}
	return node;
};
globalThis.window.kentender_core = globalThis.kentender_core;
await import("../../../../../kentender_core/kentender_core/public/js/kt_industry/kt_industry_pager.bundle.js");
