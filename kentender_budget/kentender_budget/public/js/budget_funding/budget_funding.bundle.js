import { createApp } from "vue";
import Budget from "./Budget.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by budget_funding_page.js — kentender_core.industry.mountPageRail is
// used directly by the root .vue component, not registered here (AGENTS.md
// §6.6: each bundle carries its own Vue instance, so a component object
// can't cross a bundle boundary as a child vnode).
frappe.kt_mount_budget_funding = function (el) {
	const app = createApp(Budget);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
