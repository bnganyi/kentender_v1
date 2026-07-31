/* global frappe */
/**
 * Desk browser titles — never leave the tab as bare "Frappe" / "ERPNext".
 * Stitch pages use "KenTender - …" / "KenTender DIA | …"; form/list titles get a KenTender prefix.
 */
(function () {
	"use strict";

	var GENERIC = { Frappe: 1, ERPNext: 1, "": 1 };

	var PAGE_TITLES = {
		"kt-procurement-home": "KenTender - Procurement Home",
		"demand-hub": "KenTender DIA | Demand Management Hub",
		"demand-workbench": "Demand Workbench | KenTender DIA",
		"create-demand": "KenTender DIA - New Demand Intake",
		"planning-hub": "KenTender - Planning Hub",
		"budget-hub": "KenTender | Budget Hub",
		"tender-management-v2": "KenTender - Tender Management",
		"coming-soon": "KenTender - Coming Soon",
		"std-library": "KenTender - STD Library",
	};

	function _alreadyBranded(title) {
		return /^KenTender\b/i.test(String(title || ""));
	}

	function _normalizeTitle(title) {
		var t = String(title == null ? "" : title).replace(/<[^>]*>/g, "").trim();
		if (!t || GENERIC[t]) return "KenTender";
		if (_alreadyBranded(t)) return t;
		return "KenTender - " + t;
	}

	function _installSetTitleWrap() {
		if (!frappe.utils || typeof frappe.utils.set_title !== "function") return;
		if (frappe.utils.set_title.__ktBranded) return;
		var original = frappe.utils.set_title;
		frappe.utils.set_title = function (title) {
			return original.call(this, _normalizeTitle(title));
		};
		frappe.utils.set_title.__ktBranded = true;
	}

	function _titleForCurrentRoute() {
		if (!frappe.get_route) return null;
		var route = frappe.get_route();
		if (!Array.isArray(route) || !route.length) return null;
		if (route[0] === "Workspaces" && route[1]) {
			return "KenTender - " + route[1];
		}
		var pageName = route[0];
		if (PAGE_TITLES[pageName]) return PAGE_TITLES[pageName];
		var pagedoc = locals.Page && locals.Page[pageName];
		if (pagedoc && pagedoc.title) {
			return _normalizeTitle(pagedoc.title);
		}
		return null;
	}

	function _ensureTitle() {
		_installSetTitleWrap();
		var preferred = _titleForCurrentRoute();
		if (preferred) {
			frappe.utils.set_title(preferred);
			return;
		}
		if (GENERIC[document.title]) {
			frappe.utils.set_title("KenTender");
		}
	}

	function _boot() {
		_installSetTitleWrap();
		if (GENERIC[document.title]) {
			document.title = "KenTender";
		}
		$(document).on("page-change", function () {
			setTimeout(_ensureTitle, 0);
		});
		setTimeout(_ensureTitle, 0);
	}

	if (window.frappe && frappe.ready) {
		frappe.ready(_boot);
	} else {
		$(function () {
			if (window.frappe) _boot();
		});
	}
})();
