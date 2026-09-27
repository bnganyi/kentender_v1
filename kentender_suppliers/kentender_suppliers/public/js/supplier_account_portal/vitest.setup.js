// Account portal component tests mount screens outside the portal page:
// `__` is the identity translation (with {0} substitution), matchMedia
// reports the width each test sets (1440 tables or 390 cards), and the
// shared guidance region mounts through kentender_core's real bundle, as the
// portal page loads it (KT-STD-001 v1.8 §2.9).
globalThis.__ = (text, args) => (args ? String(text).replace(/\{(\d+)\}/g, (_, i) => args[i]) : text);
globalThis.window.__ = globalThis.__;
globalThis.__narrow = false;
globalThis.window.matchMedia = (query) => ({
	matches: query.includes("max-width") ? globalThis.__narrow : false,
	media: query,
	addEventListener() {},
	removeEventListener() {},
});
globalThis.frappe = globalThis.frappe || {};
globalThis.frappe.provide =
	globalThis.frappe.provide ||
	((path) => {
		let node = globalThis;
		for (const part of path.split(".")) {
			node[part] = node[part] || {};
			node = node[part];
		}
		return node;
	});
globalThis.window.kentender_core = globalThis.kentender_core = globalThis.kentender_core || {};
await import("../../../../../kentender_core/kentender_core/public/js/kt_industry/kt_industry_guidance.bundle.js");
