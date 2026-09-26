import { createApp } from "vue";
import StdCfgPackage from "./StdCfgPackage.vue";

frappe.kt_mount_std_cfg_package = function (el) {
	const app = createApp(StdCfgPackage);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
