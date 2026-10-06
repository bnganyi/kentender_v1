// Requisitions screens host kentender_core's shared table pager through
// pager_shared/TablePagerHost.vue. In the browser the helper comes from
// kt_industry_pager.bundle.js; here the same bundle module is loaded against a
// minimal `frappe.provide`, so assertions see what a Desk page renders.
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
await import("../../../../../kentender_core/kentender_core/public/js/kt_industry/kt_industry_pager.bundle.js");
