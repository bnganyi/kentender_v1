import { createApp } from "vue";
import DepartmentalNeeds from "./DepartmentalNeeds.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by departmental_needs_page.js — kentender_core.industry.mountPageRail
// is used imperatively by the root component, not registered here (AGENTS.md
// §6.6: each bundle carries its own Vue instance, so a component object cannot
// cross a bundle boundary as a child vnode).
frappe.kt_mount_departmental_needs = function (el) {
	const app = createApp(DepartmentalNeeds);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
