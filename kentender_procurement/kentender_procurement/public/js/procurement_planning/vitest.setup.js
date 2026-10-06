// Component tests mount Planning screens that host kentender_core's shared
// journey tracker and next-step block through `useGuidance`. In the browser
// those helpers come from kt_industry_guidance.bundle.js; here the same bundle
// module is loaded against a minimal `frappe.provide`, so the structure and
// text assertions see exactly what a Desk page renders (KT-STD-001 v1.8 §2.9).
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
