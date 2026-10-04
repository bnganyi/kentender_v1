import { createApp } from "vue";
import StdCfgComparison from "./StdCfgComparison.vue";

frappe.kt_mount_std_cfg_comparison = function (el) {
	const app = createApp(StdCfgComparison);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
