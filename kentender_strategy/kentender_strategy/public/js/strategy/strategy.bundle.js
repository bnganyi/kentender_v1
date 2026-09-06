import { createApp } from "vue";
import Strategy from "./Strategy.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by strategy_page.js — kentender_core.industry.mountPageRail is used
// by the root component through usePageRail, not registered here (AGENTS.md
// §6.6: each bundle carries its own Vue instance, so a component object can't
// cross a bundle boundary as a child vnode).
frappe.kt_mount_strategy = function (el) {
	const app = createApp(Strategy);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
