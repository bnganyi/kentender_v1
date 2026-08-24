import { createApp } from "vue";
import StrategyPortfolio from "./StrategyPortfolio.vue";
import "../strategy_shared/styles/tokens.css";

frappe.kt_mount_strategy_portfolio = function (el) {
	const app = createApp(StrategyPortfolio);
	app.mount(el);
	return app;
};
