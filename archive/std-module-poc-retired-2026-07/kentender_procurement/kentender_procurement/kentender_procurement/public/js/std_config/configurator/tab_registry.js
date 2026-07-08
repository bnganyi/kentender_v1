/* global frappe */
// STD-CFG-0230 — Tab slug registry (maps mockup screens to render modules).
frappe.provide("kentender_procurement.std_configurator_tab_registry");

(function () {
	"use strict";

	const registry = kentender_procurement.std_configurator_tab_registry;
	const tabs = kentender_procurement.std_configurator_tabs || {};

	registry.SLUGS = Object.freeze([
		"overview",
		"applicability",
		"tender-fields",
		"supplier-requirements",
		"forms-attachments",
		"evaluation-setup",
		"contract-terms",
		"rules-validations",
		"preview",
		"approval",
		"evidence",
		"technical-json",
	]);

	registry.get = function getTabModule(slug) {
		return tabs[slug] || null;
	};

	registry.all = function allTabModules() {
		return registry.SLUGS.reduce(function (out, slug) {
			const mod = registry.get(slug);
			if (mod) out[slug] = mod;
			return out;
		}, {});
	};
})();
