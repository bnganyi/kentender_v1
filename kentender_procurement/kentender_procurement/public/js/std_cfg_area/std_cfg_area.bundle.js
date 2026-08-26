import { createApp } from "vue";
import StdCfgArea from "./StdCfgArea.vue";

frappe.kt_mount_std_cfg_area = function (el) {
	const app = createApp(StdCfgArea);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
