import { createApp } from "vue";
import StrategyPortfolio from "./StrategyPortfolio.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by strategy_portfolio_page.js — kentender_core.industry.mountPageRail is used
// directly by the root .vue component, not registered here (AGENTS.md §6.6:
// each bundle carries its own Vue instance, so a component object can't cross
// a bundle boundary as a child vnode — see kt_industry_page_rail.bundle.js).
frappe.kt_mount_strategy_portfolio = function (el) {
	const app = createApp(StrategyPortfolio);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
