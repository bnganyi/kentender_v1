// Component tests mount Departmental Needs screens that host kentender_core's
// shared guidance region (journey tracker and next step) through
// `useGuidance`. In the browser it comes from kt_industry_guidance.bundle.js;
// here the same bundle module is loaded against a minimal `frappe.provide`, so
// assertions see exactly what a Desk page renders (NDS-CHG-001 v1.15 §5.5).
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
await import("../../../../../kentender_core/kentender_core/public/js/kt_industry/kt_industry_pager.bundle.js");
