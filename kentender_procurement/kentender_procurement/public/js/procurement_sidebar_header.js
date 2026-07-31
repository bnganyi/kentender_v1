// Procurement rail header: title stays "Procurement"; subtitle must be "KenTender".
// Frappe's choose_app_name overwrites app_title with Desktop Icon.parent_icon when
// a matching icon exists — even when parent_icon is null — which blanks the subtitle.
(function () {
	"use strict";

	function applyKenTenderSubtitle(sidebar) {
		if (!sidebar || (sidebar.sidebar_title || "") !== "Procurement") {
			return;
		}
		sidebar.header_subtitle = "KenTender";
		var $sub = sidebar.wrapper && sidebar.wrapper.find(".header-subtitle");
		if ($sub && $sub.length) {
			$sub.text("KenTender");
		}
	}

	function patchSidebar() {
		if (!frappe.ui || !frappe.ui.Sidebar || frappe.ui.Sidebar.prototype.__ktProcHeaderPatched) {
			return;
		}
		var original = frappe.ui.Sidebar.prototype.choose_app_name;
		frappe.ui.Sidebar.prototype.choose_app_name = function () {
			original.apply(this, arguments);
			if ((this.sidebar_title || "") === "Procurement") {
				this.header_subtitle = "KenTender";
			} else if (this.header_subtitle == null || this.header_subtitle === "") {
				// Avoid blank subtitle when Desktop Icon.parent_icon is empty.
				var app = frappe.boot && frappe.boot.app_data;
				if (app && app.length && app[0].app_title) {
					this.header_subtitle = app[0].app_title;
				}
			}
		};
		frappe.ui.Sidebar.prototype.__ktProcHeaderPatched = true;
	}

	function patchHeaderMake() {
		if (!frappe.ui || !frappe.ui.SidebarHeader || frappe.ui.SidebarHeader.prototype.__ktProcHeaderPatched) {
			return;
		}
		var originalMake = frappe.ui.SidebarHeader.prototype.make;
		frappe.ui.SidebarHeader.prototype.make = function () {
			if (this.sidebar && (this.sidebar.sidebar_title || "") === "Procurement") {
				this.sidebar.header_subtitle = "KenTender";
			}
			originalMake.apply(this, arguments);
			applyKenTenderSubtitle(this.sidebar);
		};
		frappe.ui.SidebarHeader.prototype.__ktProcHeaderPatched = true;
	}

	function boot() {
		patchSidebar();
		patchHeaderMake();
	}

	boot();
	$(document).on("app_ready", boot);
})();
