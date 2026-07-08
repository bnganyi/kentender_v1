/* global frappe */
// STD-CFG-0002 — shared helpers for STD Config UI v2 pages.
frappe.provide("kentender_procurement.std_config_shared");

(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;

	shared._ensureFonts = function _ensureFonts() {
		if (!document.getElementById("kt-std-fonts")) {
			const l = document.createElement("link");
			l.id = "kt-std-fonts";
			l.rel = "stylesheet";
			l.href =
				"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700" +
				"&family=Manrope:wght@600;700;800" +
				"&family=JetBrains+Mono:wght@500&display=swap";
			document.head.appendChild(l);
		}
		if (!document.getElementById("kt-std-icons")) {
			const l = document.createElement("link");
			l.id = "kt-std-icons";
			l.rel = "stylesheet";
			l.href =
				"https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap";
			document.head.appendChild(l);
		}
	};

	shared._procBoot = function _procBoot() {
		return (frappe.boot && frappe.boot.kentender_procurement) || {};
	};

	shared.isV2Enabled = function isV2Enabled() {
		return !!shared._procBoot().std_config_ui_v2_enabled;
	};

	shared._hasBootRoleFlag = function _hasBootRoleFlag(flagKey, rolesKey) {
		const boot = shared._procBoot();
		if (boot[flagKey] === true) return true;
		if (boot[flagKey] === false) return false;
		const roles = boot[rolesKey] || frappe.user_roles || [];
		return (frappe.user_roles || []).some(function (r) {
			return roles.indexOf(r) !== -1;
		});
	};

	shared.canUseStdAdvancedCatalogue = function canUseStdAdvancedCatalogue() {
		return shared._hasBootRoleFlag("can_use_std_advanced_catalogue", "std_advanced_catalogue_roles");
	};

	shared.canViewTechnicalJson = function canViewTechnicalJson() {
		return shared._hasBootRoleFlag("can_view_technical_json", "std_technical_view_roles");
	};

	shared.canEditTechnicalJson = function canEditTechnicalJson() {
		return shared._hasBootRoleFlag("can_edit_technical_json", "std_configurator_write_roles");
	};

	shared._escapeHtml = function _escapeHtml(value) {
		return String(value == null ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#39;");
	};

	shared._statusPillClass = function _statusPillClass(status) {
		const s = String(status || "").toLowerCase();
		if (s === "active" || s === "approved") return "kt-std-status-pill--available";
		if (s === "submitted") return "kt-std-status-pill--committed";
		if (s === "under review" || s === "ready for review") {
			return "kt-std-status-pill--review";
		}
		if (s === "imported draft" || s === "imported") return "kt-std-status-pill--imported";
		if (s === "superseded" || s === "retired" || s === "archived") {
			return "kt-std-status-pill--superseded";
		}
		if (s === "needs attention" || s === "validation failed" || s === "returned") {
			return "kt-std-status-pill--attention";
		}
		return "kt-std-status-pill--draft";
	};

	shared._categoryIcon = function _categoryIcon(category) {
		const c = String(category || "").toLowerCase();
		if (c.indexOf("work") >= 0) return "description";
		if (c.indexOf("good") >= 0) return "local_shipping";
		if (c.indexOf("consult") >= 0) return "psychology";
		if (c.indexOf("service") >= 0) return "cleaning_services";
		return "description";
	};

	shared._statusPillHtml = function _statusPillHtml(status) {
		const label = shared._escapeHtml(status || "—");
		const pillClass = shared._statusPillClass(status);
		return `<span class="kt-std-status-pill ${pillClass}" data-testid="kt-std-lib-status-pill"><span class="kt-std-status-pill__dot"></span>${label}</span>`;
	};
})();
