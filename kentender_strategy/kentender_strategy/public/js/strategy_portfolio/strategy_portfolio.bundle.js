import { createApp } from "vue";
import StrategyPortfolio from "./StrategyPortfolio.vue";

frappe.kt_mount_strategy_portfolio = function (el) {
	const app = createApp(StrategyPortfolio);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
