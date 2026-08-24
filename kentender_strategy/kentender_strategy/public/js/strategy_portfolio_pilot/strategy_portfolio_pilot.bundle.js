import { createApp } from "vue";
import StrategyPortfolioPilot from "./StrategyPortfolioPilot.vue";
import "./styles/tokens.css";

frappe.kt_mount_strategy_portfolio_pilot = function (el) {
	const app = createApp(StrategyPortfolioPilot);
	app.mount(el);
	return app;
};
