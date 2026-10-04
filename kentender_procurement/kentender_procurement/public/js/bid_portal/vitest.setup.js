// Bid portal component tests mount screens outside the portal page: `__`
// is the identity translation and matchMedia reports the width each test
// sets, so a test can render the 1440 table or the 390 cards.
globalThis.__ = (text, args) => (args ? String(text).replace(/\{(\d+)\}/g, (_, i) => args[i]) : text);
globalThis.window.__ = globalThis.__;
globalThis.__narrow = false;
globalThis.window.matchMedia = (query) => ({
	matches: query.includes("max-width") ? globalThis.__narrow : false,
	media: query,
	addEventListener() {},
	removeEventListener() {},
});
// The shared guidance region (journey and next step) mounts through
// kentender_core's real bundle, as the portal page loads it.
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
