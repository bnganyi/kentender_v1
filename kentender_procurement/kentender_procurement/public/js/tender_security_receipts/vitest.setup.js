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
