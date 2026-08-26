import { createApp } from "vue";
import StdCfgReadiness from "./StdCfgReadiness.vue";

frappe.kt_mount_std_cfg_readiness = function (el) {
	const app = createApp(StdCfgReadiness);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
