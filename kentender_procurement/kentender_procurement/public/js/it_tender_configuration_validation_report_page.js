// WF-01 — Readiness Check & Report (WG-01).
// Route contract: /desk/it-tender-configuration-validation-report/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "WF-01";
	var PAGE_SLUG = "it-tender-configuration-validation-report";
	var GET_API = "kentender_procurement.tender_configurations.get_tender_configuration_readiness";
	var RUN_API = "kentender_procurement.tender_configurations.run_tender_configuration_readiness_check";
	var SUBMIT_API = "kentender_procurement.tender_configurations.submit_tender_configuration_for_review";
	var RESOLVE_API =
		"kentender_procurement.tender_configurations.resolve_tender_configuration_review_finding";
	var STORAGE_KEY = "kt_cl_wf01_configuration_id";
	var BACK_ROUTE = "it-tender-configuration-overview";
	var REVIEW_ROUTE = "it-tender-configuration-review-and-approval";
	var DRAWER_HOST_ID = "kt-cl-wf01-drawer-host";

	var state = {
		payload: null,
		configurationId: null,
		page: null,
		mounting: false,
		busy: false,
	};

	var STYLE_ID = "kt-cl-wf01-critical-css-v4";

	/** Critical layout travels with page JS so Desk CSS cache cannot leave WF-01 unstyled. */
	function ensureCriticalCss() {
		["kt-cl-wf01-critical-css", "kt-cl-wf01-critical-css-v3"].forEach(function (id) {
			var stale = document.getElementById(id);
			if (stale && stale.parentNode) {
				stale.parentNode.removeChild(stale);
			}
		});
		if (document.getElementById(STYLE_ID)) {
			return;
		}
		var style = document.createElement("style");
		style.id = STYLE_ID;
		style.textContent =
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:1rem!important;margin:1.25rem 0 1rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi{position:relative!important;overflow:hidden!important;background:#fff!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:1rem 1rem 1rem 1.15rem!important;min-height:5.5rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-accent{position:absolute!important;left:0!important;top:0!important;bottom:0!important;width:4px!important;background:#c4c6cf!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--success .kt-cl-wf01-kpi-accent{background:#16a34a!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--error .kt-cl-wf01-kpi-accent{background:#ba1a1a!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--warning .kt-cl-wf01-kpi-accent{background:#d97706!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--primary .kt-cl-wf01-kpi-accent{background:#002244!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-label{margin:0 0 .5rem!important;font-size:11px!important;font-weight:700!important;color:#5f6368!important;text-transform:uppercase!important;letter-spacing:.04em!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-overall{display:flex!important;align-items:center!important;gap:.5rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-overall-text{margin:0!important;font-size:1.1rem!important;font-weight:700!important;line-height:1.3!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--success .kt-cl-wf01-kpi-overall-text,[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--success .material-symbols-outlined{color:#16a34a!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--error .kt-cl-wf01-kpi-overall-text,[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--error .material-symbols-outlined{color:#ba1a1a!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--warning .kt-cl-wf01-kpi-overall-text,[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--warning .material-symbols-outlined{color:#d97706!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-num{margin:0!important;font-size:2.25rem!important;font-weight:700!important;line-height:1.1!important;color:#002244!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--error .kt-cl-wf01-kpi-num{color:#ba1a1a!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi--neutral .kt-cl-wf01-kpi-num{color:#8e9199!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-date{margin:.35rem 0 0!important;font-size:.95rem!important;font-weight:700!important;color:#002244!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-time{margin:.15rem 0 0!important;font-size:12px!important;color:#5f6368!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-banner{display:flex!important;align-items:flex-start!important;gap:1rem!important;padding:1rem!important;margin-bottom:1.25rem!important;border-radius:.25rem!important;border:1px solid transparent!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-banner--success{background:rgba(22,163,74,.1)!important;border-color:rgba(22,163,74,.2)!important;color:#15803d!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-banner--error{background:#f9dedc!important;border-color:#f2b8b5!important;color:#410e0b!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-banner--warning{background:#fff8e6!important;border-color:#f5d78e!important;color:#92400e!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-banner--neutral{background:#f0f4f8!important;border-color:#c4c6cf!important;color:#43474e!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-banner-title{margin:0 0 .25rem!important;font-size:14px!important;font-weight:700!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-banner-detail{margin:0!important;font-size:13px!important;line-height:1.45!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-bento,[data-testid='kt-cl-wf01-root'] [data-testid='kt-cl-wf01-layout']{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,2fr)!important;gap:1rem!important;align-items:start!important;margin-bottom:1rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-checklist{background:#fff!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:1rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-checklist-head{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:.75rem!important;margin-bottom:1rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-checklist-head h3{margin:0!important;font-size:1.05rem!important;font-weight:700!important;color:#002244!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-checklist-badge{font-size:11px!important;font-weight:600!important;color:#5f6368!important;background:#e7e8eb!important;padding:.15rem .5rem!important;border-radius:.25rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-checklist-list{display:flex!important;flex-direction:column!important;gap:.25rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:.5rem!important;width:100%!important;padding:.5rem!important;border:none!important;border-radius:.25rem!important;background:transparent!important;text-align:left!important;cursor:pointer!important;box-shadow:none!important;appearance:none!important;-webkit-appearance:none!important;color:inherit!important;font:inherit!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--error{background:rgba(186,26,26,.08)!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--warning{background:#fff8e6!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-main{display:flex!important;align-items:center!important;gap:.5rem!important;min-width:0!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-label{font-size:13px!important;color:#1a1c1e!important;line-height:1.35!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-status{font-size:12px!important;font-weight:600!important;white-space:nowrap!important;flex-shrink:0!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--success .material-symbols-outlined,[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--success .kt-cl-wf01-check-status{color:#15803d!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--error .material-symbols-outlined,[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--error .kt-cl-wf01-check-status,[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--error .kt-cl-wf01-check-label{color:#ba1a1a!important;font-weight:700!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--warning .material-symbols-outlined,[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-check-row--warning .kt-cl-wf01-check-status{color:#b45309!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-findings{background:#fff!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;overflow:hidden!important;min-width:0!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-findings-head{padding:1rem!important;border-bottom:1px solid #c4c6cf!important;background:#f0f4f8!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-findings-head h3{margin:0!important;font-size:1.05rem!important;font-weight:700!important;color:#002244!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-findings-empty{display:flex!important;flex-direction:column!important;align-items:center!important;gap:.5rem!important;padding:3rem 1.5rem!important;text-align:center!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections{background:#fff!important;border:1px solid #f2b8b5!important;border-radius:.25rem!important;padding:1rem!important;margin-bottom:1.25rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-head{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:.75rem!important;margin-bottom:.5rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-head h3{margin:0!important;font-size:1.05rem!important;font-weight:700!important;color:#ba1a1a!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-intro{margin:0 0 1rem!important;font-size:13px!important;color:#43474e!important;line-height:1.45!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-list{display:flex!important;flex-direction:column!important;gap:.75rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-card{border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:.85rem 1rem!important;background:#fafafa!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-card--resolved{opacity:.75!important;background:#f5f7f5!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-top{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:.5rem!important;margin-bottom:.35rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-sev{font-size:11px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.03em!important;padding:.1rem .4rem!important;border-radius:.2rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-sev--error{background:#f9dedc!important;color:#ba1a1a!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-status{font-size:12px!important;font-weight:600!important;color:#5f6368!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-section{margin:0 0 .25rem!important;font-size:12px!important;font-weight:600!important;color:#5f6368!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-finding{margin:0 0 .35rem!important;font-size:14px!important;font-weight:600!important;color:#1a1c1e!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-action{margin:0 0 .75rem!important;font-size:13px!important;color:#43474e!important;line-height:1.4!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-actions{display:flex!important;flex-wrap:wrap!important;gap:.5rem!important;align-items:center!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corr-done{font-size:12px!important;font-weight:700!important;color:#15803d!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-foot{display:flex!important;justify-content:flex-end!important;margin-top:.85rem!important;padding-top:.75rem!important;border-top:1px solid #e7e8eb!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-history{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:1rem!important;flex-wrap:wrap!important;background:#fff!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:.75rem 1rem!important;margin-bottom:1.25rem!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-history-copy{margin:0!important;font-size:13px!important;color:#43474e!important;line-height:1.4!important}" +
			"[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-corrections-history-copy strong{color:#002244!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-overlay{position:fixed!important;inset:0!important;z-index:1300!important;display:block!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-backdrop{position:absolute!important;inset:0!important;border:0!important;padding:0!important;margin:0!important;background:rgba(0,34,68,.2)!important;cursor:pointer!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer{position:fixed!important;top:0!important;right:0!important;bottom:0!important;width:min(420px,100vw)!important;max-width:100%!important;display:flex!important;flex-direction:column!important;background:#fff!important;border-left:1px solid #c4c6cf!important;box-shadow:-8px 0 24px rgba(16,24,40,.16)!important;z-index:1301!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-header{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:1rem!important;padding:1rem 1.25rem!important;background:#f0f4f8!important;border-bottom:1px solid #c4c6cf!important;flex-shrink:0!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-header h2{margin:0!important;font-size:1.15rem!important;font-weight:700!important;color:#002244!important;line-height:1.3!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-close{display:inline-flex!important;align-items:center!important;justify-content:center!important;width:2.25rem!important;height:2.25rem!important;border:0!important;border-radius:999px!important;background:transparent!important;color:#5f6368!important;cursor:pointer!important;padding:0!important;box-shadow:none!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-close:hover{background:#e7e8eb!important;color:#002244!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-body{flex:1!important;overflow-y:auto!important;padding:1.25rem!important;display:flex!important;flex-direction:column!important;gap:.75rem!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-drawer-intro{margin:0 0 .25rem!important;font-size:13px!important;color:#43474e!important;line-height:1.45!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-corr-card{border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:.85rem 1rem!important;background:#f5f7f5!important}" +
			"#" +
			DRAWER_HOST_ID +
			" .kt-cl-wf01-corr-card--resolved{opacity:.9!important}" +
			"@media (max-width:1100px){[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}[data-testid='kt-cl-wf01-root'] .kt-cl-wf01-bento,[data-testid='kt-cl-wf01-root'] [data-testid='kt-cl-wf01-layout']{grid-template-columns:1fr!important}}";
		document.head.appendChild(style);
	}

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function c() {
		return kentender_core.cl_components || kentender_core.cl.components;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function configurationId() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		if (frappe.route_options && frappe.route_options.configuration_id) {
			return String(frappe.route_options.configuration_id).trim();
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("configuration_id")) {
				return String(params.get("configuration_id")).trim();
			}
		} catch (e) {
			/* ignore */
		}
		try {
			var stored = window.sessionStorage.getItem(STORAGE_KEY);
			if (stored) {
				return stored;
			}
		} catch (e2) {
			/* ignore */
		}
		return null;
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-wf01-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-wf01-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function pad2(n) {
		var s = String(n == null ? 0 : n);
		return s.length < 2 ? "0" + s : s;
	}

	function overallTone(overall) {
		var o = String(overall || "").toLowerCase();
		if (o.indexOf("not ready") >= 0) {
			return "error";
		}
		if (o.indexOf("warning") >= 0) {
			return "warning";
		}
		if (o.indexOf("ready for review") >= 0) {
			return "success";
		}
		return "neutral";
	}

	function overallIcon(tone) {
		if (tone === "success") {
			return "check_circle";
		}
		if (tone === "error") {
			return "error";
		}
		if (tone === "warning") {
			return "warning";
		}
		return "pending";
	}

	function splitCheckedAt(raw) {
		var s = String(raw || "").trim();
		if (!s) {
			return { date: __("Not run"), time: "" };
		}
		// "2026-07-19 10:30:00.xxxxxx" or ISO
		var m = s.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/);
		if (m) {
			return { date: m[1], time: m[2] + " EAT" };
		}
		return { date: s, time: "" };
	}

	function summaryCardsHtml(data) {
		var overall = data.overall_result || __("Check Not Run");
		var tone = overallTone(overall);
		var blockers = int(data.blocker_count);
		var warnings = int(data.warning_count);
		var when = splitCheckedAt(data.last_checked_at);
		var blockerTone = blockers > 0 ? "error" : "neutral";
		var warningTone = warnings > 0 ? "warning" : "neutral";
		return (
			'<div class="kt-cl-wf01-kpi-grid" data-testid="kt-cl-wf01-summary">' +
			'<div class="kt-cl-wf01-kpi kt-cl-wf01-kpi--' +
			esc(tone) +
			'" data-testid="kt-cl-wf01-card-overall">' +
			'<span class="kt-cl-wf01-kpi-accent" aria-hidden="true"></span>' +
			'<p class="kt-cl-wf01-kpi-label">' +
			__("Overall Result") +
			"</p>" +
			'<div class="kt-cl-wf01-kpi-overall">' +
			'<span class="material-symbols-outlined" aria-hidden="true">' +
			overallIcon(tone) +
			"</span>" +
			'<p class="kt-cl-wf01-kpi-overall-text">' +
			esc(overall) +
			"</p></div></div>" +
			'<div class="kt-cl-wf01-kpi kt-cl-wf01-kpi--' +
			esc(blockerTone) +
			'" data-testid="kt-cl-wf01-card-blockers">' +
			'<span class="kt-cl-wf01-kpi-accent" aria-hidden="true"></span>' +
			'<p class="kt-cl-wf01-kpi-label">' +
			__("Blockers") +
			"</p>" +
			'<p class="kt-cl-wf01-kpi-num">' +
			esc(pad2(blockers)) +
			"</p></div>" +
			'<div class="kt-cl-wf01-kpi kt-cl-wf01-kpi--' +
			esc(warningTone) +
			'" data-testid="kt-cl-wf01-card-warnings">' +
			'<span class="kt-cl-wf01-kpi-accent" aria-hidden="true"></span>' +
			'<p class="kt-cl-wf01-kpi-label">' +
			__("Warnings") +
			"</p>" +
			'<p class="kt-cl-wf01-kpi-num">' +
			esc(pad2(warnings)) +
			"</p></div>" +
			'<div class="kt-cl-wf01-kpi kt-cl-wf01-kpi--primary" data-testid="kt-cl-wf01-card-last-checked">' +
			'<span class="kt-cl-wf01-kpi-accent" aria-hidden="true"></span>' +
			'<p class="kt-cl-wf01-kpi-label">' +
			__("Last Checked") +
			"</p>" +
			'<p class="kt-cl-wf01-kpi-date">' +
			esc(when.date) +
			"</p>" +
			(when.time
				? '<p class="kt-cl-wf01-kpi-time">' + esc(when.time) + "</p>"
				: "") +
			"</div></div>"
		);
	}

	function guidanceHtml(data) {
		var openCorr = int(data && data.open_correction_count);
		var overall = data.overall_result || __("Check Not Run");
		var tone = openCorr > 0 ? "error" : overallTone(overall);
		var icon = openCorr > 0 ? "assignment_return" : overallIcon(tone);
		var title;
		var detail;
		if (openCorr > 0) {
			title = __("This configuration was returned for correction.");
			detail = __(
				"Mark all reviewer corrections as fixed, open the affected sections to make changes, then re-run readiness before submitting for review."
			);
		} else if (tone === "success") {
			title = __("This configuration is ready to submit for review.");
			detail = __("All mandatory requirements have been met and no blockers were identified.");
		} else if (tone === "error") {
			title = __("This configuration cannot be submitted for review yet.");
			detail = __("Fix the blockers listed below, then re-run the readiness check to generate an updated report.");
		} else if (tone === "warning") {
			title = __("This configuration has no blockers.");
			detail = __("Review the warnings before submitting for review.");
		} else {
			title = __("Run the readiness check to see whether this configuration can be submitted for review.");
			detail = __("Use Re-run Check to validate CFG-01 through CFG-09.");
		}
		return (
			'<div class="kt-cl-wf01-banner kt-cl-wf01-banner--' +
			esc(tone) +
			'" data-testid="kt-cl-wf01-guidance" role="status">' +
			'<span class="material-symbols-outlined" aria-hidden="true">' +
			icon +
			"</span>" +
			"<div>" +
			'<p class="kt-cl-wf01-banner-title">' +
			esc(title) +
			"</p>" +
			'<p class="kt-cl-wf01-banner-detail">' +
			esc(detail) +
			"</p></div></div>"
		);
	}

	function partitionCorrections(items) {
		var open = [];
		var resolved = [];
		(items || []).forEach(function (f) {
			var status = String(f.status || "Open");
			if (status === "Open" || status === "") {
				open.push(f);
			} else {
				resolved.push(f);
			}
		});
		return { open: open, resolved: resolved };
	}

	function correctionCardHtml(f, opts) {
		opts = opts || {};
		var status = String(f.status || "Open");
		var isOpen = status === "Open" || status === "";
		var fid = f.id || "";
		var route = f.owner_route || "";
		var showMarkFixed = opts.showMarkFixed !== false && isOpen;
		return (
			'<div class="kt-cl-wf01-corr-card' +
			(isOpen ? "" : " kt-cl-wf01-corr-card--resolved") +
			'" data-testid="kt-cl-wf01-correction-' +
			esc(fid) +
			'">' +
			'<div class="kt-cl-wf01-corr-top">' +
			'<span class="kt-cl-wf01-sev kt-cl-wf01-sev--error">' +
			esc(f.severity || __("Correction Required")) +
			"</span>" +
			'<span class="kt-cl-wf01-corr-status">' +
			esc(status || "Open") +
			"</span></div>" +
			'<p class="kt-cl-wf01-corr-section">' +
			esc(f.section || "—") +
			"</p>" +
			'<p class="kt-cl-wf01-corr-finding">' +
			esc(f.finding || "—") +
			"</p>" +
			'<p class="kt-cl-wf01-corr-action"><strong>' +
			__("Required action:") +
			"</strong> " +
			esc(f.required_action || "—") +
			"</p>" +
			'<div class="kt-cl-wf01-corr-actions">' +
			(route && isOpen
				? '<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary kt-cl-wizard-btn--sm" data-action="goto-owner" data-route="' +
					esc(route) +
					'" data-testid="kt-cl-wf01-corr-open-' +
					esc(fid) +
					'">' +
					__("Open section") +
					"</button>"
				: "") +
			(showMarkFixed
				? '<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary kt-cl-wizard-btn--sm" data-action="mark-fixed" data-finding-id="' +
					esc(fid) +
					'" data-testid="kt-cl-wf01-corr-fix-' +
					esc(fid) +
					'"' +
					(state.busy ? " disabled" : "") +
					">" +
					__("Mark as fixed") +
					"</button>"
				: isOpen
					? ""
					: '<span class="kt-cl-wf01-corr-done">' + __("Fixed") + "</span>") +
			"</div></div>"
		);
	}

	function viewFixedButtonHtml(resolvedCount) {
		if (!resolvedCount) {
			return "";
		}
		return (
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary kt-cl-wizard-btn--sm" data-action="open-fixed-corrections" data-testid="kt-cl-wf01-view-fixed-corrections">' +
			__("View {0} fixed", [resolvedCount]) +
			"</button>"
		);
	}

	function reviewCorrectionsHtml(data) {
		var parts = partitionCorrections(data.review_corrections || []);
		var openItems = parts.open;
		var resolvedItems = parts.resolved;
		if (!openItems.length && !resolvedItems.length) {
			return "";
		}
		var html = "";
		if (openItems.length) {
			html +=
				'<section class="kt-cl-wf01-corrections" data-testid="kt-cl-wf01-corrections">' +
				'<div class="kt-cl-wf01-corrections-head">' +
				"<h3>" +
				__("Corrections Required") +
				"</h3>" +
				'<span class="kt-cl-wf01-checklist-badge">' +
				esc(String(openItems.length)) +
				" " +
				__("OPEN") +
				"</span></div>" +
				'<p class="kt-cl-wf01-corrections-intro">' +
				__(
					"These items were raised by the reviewer. Fix the affected configuration sections, then mark each item as fixed before submitting for review."
				) +
				"</p>" +
				'<div class="kt-cl-wf01-corrections-list">' +
				openItems.map(function (f) {
					return correctionCardHtml(f, { showMarkFixed: true });
				}).join("") +
				"</div>" +
				(resolvedItems.length
					? '<div class="kt-cl-wf01-corrections-foot">' +
						viewFixedButtonHtml(resolvedItems.length) +
						"</div>"
					: "") +
				"</section>";
		} else if (resolvedItems.length) {
			html +=
				'<div class="kt-cl-wf01-corrections-history" data-testid="kt-cl-wf01-corrections-history">' +
				'<p class="kt-cl-wf01-corrections-history-copy">' +
				__("All reviewer corrections are fixed.") +
				" <strong>" +
				esc(String(resolvedItems.length)) +
				"</strong> " +
				__(resolvedItems.length === 1 ? "item archived." : "items archived.") +
				"</p>" +
				viewFixedButtonHtml(resolvedItems.length) +
				"</div>";
		}
		return html;
	}

	function drawerHost() {
		var el = document.getElementById(DRAWER_HOST_ID);
		if (!el) {
			el = document.createElement("div");
			el.id = DRAWER_HOST_ID;
			document.body.appendChild(el);
		}
		return $(el);
	}

	function closeFixedCorrectionsDrawer() {
		var $host = drawerHost();
		$host.off(".wf01drawer");
		$host.empty();
	}

	function openFixedCorrectionsDrawer() {
		var parts = partitionCorrections((state.payload && state.payload.review_corrections) || []);
		var resolved = parts.resolved;
		if (!resolved.length) {
			frappe.show_alert(
				{ message: __("No fixed corrections to show."), indicator: "blue" },
				4
			);
			return;
		}
		var $host = drawerHost();
		$host.off(".wf01drawer");
		$host.html(
			'<div class="kt-cl-wf01-drawer-overlay" data-testid="kt-cl-wf01-fixed-drawer" role="dialog" aria-modal="true" aria-labelledby="kt-cl-wf01-fixed-drawer-title">' +
				'<button type="button" class="kt-cl-wf01-drawer-backdrop" data-action="close-fixed-corrections" aria-label="' +
				esc(__("Close")) +
				'"></button>' +
				'<aside class="kt-cl-wf01-drawer" data-testid="kt-cl-wf01-fixed-drawer-panel">' +
				'<header class="kt-cl-wf01-drawer-header">' +
				'<h2 id="kt-cl-wf01-fixed-drawer-title">' +
				__("Fixed Corrections") +
				"</h2>" +
				'<button type="button" class="kt-cl-wf01-drawer-close" data-action="close-fixed-corrections" data-testid="kt-cl-wf01-fixed-drawer-close" aria-label="' +
				esc(__("Close")) +
				'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button>' +
				"</header>" +
				'<div class="kt-cl-wf01-drawer-body">' +
				'<p class="kt-cl-wf01-drawer-intro">' +
				__(
					"These reviewer items were marked fixed. They stay available for audit but no longer block submit."
				) +
				"</p>" +
				resolved
					.map(function (f) {
						return correctionCardHtml(f, { showMarkFixed: false });
					})
					.join("") +
				"</div></aside></div>"
		);
		$host.on("click.wf01drawer", "[data-action='close-fixed-corrections']", function (e) {
			e.preventDefault();
			closeFixedCorrectionsDrawer();
		});
	}

	function checklistResultMeta(result) {
		var r = String(result || "").toLowerCase();
		if (r.indexOf("complete") >= 0) {
			return { tone: "success", icon: "check_circle" };
		}
		if (r.indexOf("attention") >= 0 || r.indexOf("not started") >= 0) {
			return { tone: "error", icon: "error" };
		}
		if (r.indexOf("warning") >= 0) {
			return { tone: "warning", icon: "warning" };
		}
		return { tone: "neutral", icon: "radio_button_unchecked" };
	}

	function checklistHtml(data) {
		var items = data.checklist || [];
		var rows = items
			.map(function (row, idx) {
				var meta = checklistResultMeta(row.check_result);
				var label =
					(row.step_id ? String(row.step_id) + " " : "") + (row.area || "");
				var route = row.owner_route || "";
				return (
					'<div role="button" tabindex="' +
					(route ? "0" : "-1") +
					'" class="kt-cl-wf01-check-row kt-cl-wf01-check-row--' +
					esc(meta.tone) +
					'" data-action="goto-owner" data-route="' +
					esc(route) +
					'" data-testid="kt-cl-wf01-checklist-action-' +
					esc(row.step_id || String(idx)) +
					'"' +
					(route ? "" : ' aria-disabled="true"') +
					">" +
					'<span class="kt-cl-wf01-check-main">' +
					'<span class="material-symbols-outlined" aria-hidden="true">' +
					meta.icon +
					"</span>" +
					'<span class="kt-cl-wf01-check-label">' +
					esc(label) +
					"</span></span>" +
					'<span class="kt-cl-wf01-check-status">' +
					esc(row.check_result || "—") +
					"</span></div>"
				);
			})
			.join("");
		return (
			'<aside class="kt-cl-wf01-checklist" data-testid="kt-cl-wf01-checklist">' +
			'<div class="kt-cl-wf01-checklist-head">' +
			"<h3>" +
			__("Configuration Checklist") +
			"</h3>" +
			'<span class="kt-cl-wf01-checklist-badge">' +
			esc(String(items.length || 9)) +
			" " +
			__("STEPS") +
			"</span></div>" +
			'<div class="kt-cl-wf01-checklist-list">' +
			(rows ||
				'<p class="kt-cl-wf01-empty-hint">' +
					__("Run the readiness check to populate the checklist.") +
					"</p>") +
			"</div></aside>"
		);
	}

	function severityChip(sev) {
		var s = String(sev || "");
		var tone = /blocker/i.test(s) ? "error" : /warning/i.test(s) ? "warning" : "neutral";
		return (
			'<span class="kt-cl-wf01-sev kt-cl-wf01-sev--' +
			esc(tone) +
			'">' +
			esc(s || "—") +
			"</span>"
		);
	}

	function findingsTableHtml(data) {
		var comp = c();
		var findings = data.findings || [];
		var cols = [
			{ label: __("Severity") },
			{ label: __("Configuration Area") },
			{ label: __("Issue") },
			{ label: __("Why it matters") },
			{ label: __("Required action") },
			{ label: __("Action") },
		];
		var body;
		if (!findings.length && data.has_run) {
			body =
				'<div class="kt-cl-wf01-findings-empty" data-testid="kt-cl-wf01-findings-empty">' +
				'<span class="material-symbols-outlined" aria-hidden="true">verified</span>' +
				'<p class="kt-cl-wf01-findings-empty-title">' +
				__("No blockers or warnings found") +
				"</p>" +
				"<p>" +
				__("The configuration meets all readiness requirements for submission.") +
				"</p></div>";
		} else {
			var rows = findings.map(function (f, idx) {
				var route = f.owner_route || "";
				var actionLabel = f.action_label || "Fix";
				return {
					id: String(idx),
					cells: [
						{ html: severityChip(f.severity) },
						{ text: f.area || "—" },
						{ text: f.issue || "—" },
						{ text: f.why_it_matters || "—" },
						{ text: f.required_action || "—" },
						{
							html: route
								? '<button type="button" class="kt-cl-wf-row-action" data-action="goto-owner" data-route="' +
									esc(route) +
									'" data-testid="kt-cl-wf01-finding-action-' +
									esc(String(idx)) +
									'">' +
									esc(actionLabel) +
									"</button>"
								: esc(actionLabel),
						},
					],
				};
			});
			body = comp.queueTable({
				columns: cols,
				rows: rows,
				footerText: __("Total findings: {0}", [rows.length]),
				showPageSize: false,
				pagination: null,
			});
		}
		return (
			'<section class="kt-cl-wf01-findings" data-testid="kt-cl-wf01-findings">' +
			'<div class="kt-cl-wf01-findings-head">' +
			"<h3>" +
			__("Detailed Findings") +
			"</h3></div>" +
			'<div class="kt-cl-wf01-findings-body">' +
			body +
			"</div></section>"
		);
	}

	function footerHtml(data) {
		var canSubmit = !!(data && data.can_submit_for_review);
		var blockers = int(data && data.blocker_count);
		var openCorr = int(data && data.open_correction_count);
		var hasRun = !!(data && data.has_run);
		var primaryAction = "submit-review";
		var primaryLabel = __("Submit for Review");
		var primaryTest = "kt-cl-wf01-submit";
		var primaryDisabled = !(canSubmit && !state.busy);
		if (openCorr > 0) {
			primaryAction = "scroll-corrections";
			primaryLabel = __("Fix Corrections");
			primaryTest = "kt-cl-wf01-fix-corrections";
			primaryDisabled = false;
		} else if (!hasRun) {
			primaryAction = "run-check";
			primaryLabel = __("Run Readiness Check");
			primaryTest = "kt-cl-wf01-primary-run";
			primaryDisabled = !!state.busy;
		} else if (blockers > 0) {
			primaryAction = "fix-first";
			primaryLabel = __("Fix Blockers");
			primaryTest = "kt-cl-wf01-fix-blockers";
			primaryDisabled = false;
		}
		return (
			'<div class="kt-cl-wizard-footer kt-cl-wf01-footer" data-testid="kt-cl-wf01-footer">' +
			'<div class="kt-cl-wizard-footer-start">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary kt-cl-wf01-back-link" data-action="back-home" data-testid="kt-cl-wf01-back">' +
			'<span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>' +
			__("Return to Configuration Home") +
			"</button></div>" +
			'<div class="kt-cl-wizard-footer-end">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="run-check" data-testid="kt-cl-wf01-run-check"' +
			(state.busy ? " disabled" : "") +
			">" +
			__("Re-run Check") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="export-report" data-testid="kt-cl-wf01-export"' +
			(hasRun && !state.busy ? "" : " disabled") +
			">" +
			__("Export Report") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="' +
			esc(primaryAction) +
			'" data-testid="' +
			esc(primaryTest) +
			'"' +
			(primaryDisabled ? " disabled" : "") +
			">" +
			esc(primaryLabel) +
			"</button></div></div>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-wf01-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			summaryCardsHtml(data) +
			guidanceHtml(data) +
			reviewCorrectionsHtml(data) +
			'<div class="kt-cl-wf01-bento" data-testid="kt-cl-wf01-layout">' +
			checklistHtml(data) +
			findingsTableHtml(data) +
			"</div>" +
			footerHtml(data) +
			"</div>"
		);
	}

	function refreshCorrectionsInPlace($root, data) {
		var html = reviewCorrectionsHtml(data || {});
		$root.find('[data-testid="kt-cl-wf01-corrections"]').remove();
		$root.find('[data-testid="kt-cl-wf01-corrections-history"]').remove();
		$root.find('[data-testid="kt-cl-wf01-guidance"]').replaceWith(guidanceHtml(data || {}));
		if (html) {
			$root.find('[data-testid="kt-cl-wf01-guidance"]').after(html);
		}
		$root.find('[data-testid="kt-cl-wf01-footer"]').replaceWith(footerHtml(data || {}));
		closeFixedCorrectionsDrawer();
	}

	function remountWithPayload(page, data) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Readiness Check & Report"),
			subtitle: __("Check whether this tender configuration is complete enough for review."),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		closeFixedCorrectionsDrawer();
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? pageHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
	}

	function runCheck(page) {
		if (state.busy || !state.configurationId) {
			return;
		}
		state.busy = true;
		remountWithPayload(page, state.payload || {});
		frappe.call({
			method: RUN_API,
			args: { configuration_id: state.configurationId },
			callback: function (r) {
				state.busy = false;
				var data = r.message || null;
				if (data) {
					frappe.show_alert(
						{
							message:
								int(data.blocker_count || 0) === 0
									? __("Check complete: no blockers.")
									: __(
											"Check complete: {0} blocker(s), {1} warning(s).",
											[data.blocker_count || 0, data.warning_count || 0]
									  ),
							indicator: int(data.blocker_count || 0) === 0 ? "green" : "orange",
						},
						6
					);
				}
				remountWithPayload(page, data || state.payload);
			},
			error: function () {
				state.busy = false;
				remountWithPayload(page, state.payload || {});
			},
		});
	}

	function int(v) {
		return parseInt(v, 10) || 0;
	}

	function submitForReview(page) {
		if (state.busy || !state.configurationId || !(state.payload && state.payload.can_submit_for_review)) {
			return;
		}
		kentender_core.cl.confirm({
			title: __("Submit for review?"),
			message: __(
				"This sends the configuration to the review workspace. It does not publish the tender."
			),
			confirmLabel: __("Submit for Review"),
			cancelLabel: __("Cancel"),
			onConfirm: function () {
				state.busy = true;
				remountWithPayload(page, state.payload || {});
				frappe.call({
					method: SUBMIT_API,
					args: { configuration_id: state.configurationId, payload: {} },
					callback: function (r) {
						state.busy = false;
						var data = r.message || null;
						if (data && data.submitted) {
							frappe.show_alert(
								{ message: __("Submitted for review"), indicator: "green" },
								5
							);
							frappe.route_options = { configuration_id: state.configurationId };
							frappe.set_route(REVIEW_ROUTE, state.configurationId);
							return;
						}
						remountWithPayload(page, data || state.payload);
					},
					error: function () {
						state.busy = false;
						remountWithPayload(page, state.payload || {});
					},
				});
			},
		});
	}

	function bind($root, page) {
		$root.off(".wf01");
		$root.on("click.wf01", "[data-action='back-home']", function (e) {
			e.preventDefault();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.wf01", "[data-action='run-check']", function (e) {
			e.preventDefault();
			runCheck(page);
		});
		$root.on("click.wf01", "[data-action='submit-review']", function (e) {
			e.preventDefault();
			submitForReview(page);
		});
		$root.on("click.wf01", "[data-action='fix-first']", function (e) {
			e.preventDefault();
			var payload = state.payload || {};
			var first = null;
			(payload.findings || []).some(function (f) {
				if (String(f.severity || "").toLowerCase().indexOf("blocker") >= 0 && f.owner_route) {
					first = f;
					return true;
				}
				return false;
			});
			if (!first) {
				(payload.checklist || []).some(function (row) {
					var r = String(row.check_result || "").toLowerCase();
					if ((r.indexOf("attention") >= 0 || r.indexOf("not started") >= 0) && row.owner_route) {
						first = row;
						return true;
					}
					return false;
				});
			}
			var route = first && first.owner_route ? String(first.owner_route).trim() : "";
			if (!route || !state.configurationId) {
				frappe.show_alert({ message: __("No owner screen found for the first blocker."), indicator: "orange" }, 5);
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(route, state.configurationId);
		});
		$root.on("click.wf01", "[data-action='scroll-corrections']", function (e) {
			e.preventDefault();
			var el = $root.find('[data-testid="kt-cl-wf01-corrections"]')[0];
			if (el && typeof el.scrollIntoView === "function") {
				el.scrollIntoView({ behavior: "smooth", block: "start" });
			}
		});
		$root.on("click.wf01", "[data-action='open-fixed-corrections']", function (e) {
			e.preventDefault();
			openFixedCorrectionsDrawer();
		});
		$root.on("click.wf01", "[data-action='mark-fixed']", function (e) {
			e.preventDefault();
			if (state.busy || !state.configurationId) {
				return;
			}
			var findingId = String($(this).attr("data-finding-id") || "").trim();
			if (!findingId) {
				return;
			}
			state.busy = true;
			frappe.call({
				method: RESOLVE_API,
				args: {
					configuration_id: state.configurationId,
					finding_id: findingId,
				},
				callback: function (r) {
					state.busy = false;
					if (r && r.exc) {
						return;
					}
					var data = (r && r.message) || {};
					state.payload = data;
					refreshCorrectionsInPlace($root, data);
					frappe.show_alert(
						{ message: __("Correction marked as fixed"), indicator: "green" },
						4
					);
				},
				error: function () {
					state.busy = false;
				},
			});
		});
		$root.on("click.wf01", "[data-action='export-report']", function (e) {
			e.preventDefault();
			var payload = state.payload || {};
			if (!payload.has_run) {
				frappe.show_alert({ message: __("Run the readiness check before exporting."), indicator: "orange" }, 5);
				return;
			}
			var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
			var url = URL.createObjectURL(blob);
			var a = document.createElement("a");
			a.href = url;
			a.download =
				"readiness-report-" +
				String(payload.configuration_ref || payload.configuration_id || "report").replace(/[^\w.-]+/g, "_") +
				".json";
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			frappe.show_alert({ message: __("Readiness report exported"), indicator: "green" }, 4);
		});
		$root.on("click.wf01", "[data-action='goto-owner']", function (e) {
			e.preventDefault();
			if ($(this).attr("aria-disabled") === "true") {
				return;
			}
			var route = String($(this).attr("data-route") || "").trim();
			if (!route || !state.configurationId) {
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(route, state.configurationId);
		});
		$root.on("keydown.wf01", "[data-action='goto-owner']", function (e) {
			if (e.key !== "Enter" && e.key !== " ") {
				return;
			}
			e.preventDefault();
			$(this).trigger("click");
		});
	}

	function mount(page) {
		if (state.mounting) {
			return;
		}
		ensureCriticalCss();
		state.page = page;
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		var pageHeader = {
			title: __("Readiness Check & Report"),
			subtitle: __("Check whether this tender configuration is complete enough for review."),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}

		var id = configurationId();
		state.configurationId = id;
		if (!id) {
			sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
			bind($(page.main), page);
			return;
		}

		var route = frappe.get_route() || [];
		if (!(route[0] === PAGE_SLUG && route[1] === id)) {
			state.mounting = true;
			frappe.set_route(PAGE_SLUG, id);
			setTimeout(function () {
				state.mounting = false;
			}, 0);
			return;
		}

		try {
			window.sessionStorage.setItem(STORAGE_KEY, id);
		} catch (e) {
			/* ignore */
		}

		frappe.call({
			method: GET_API,
			args: { configuration_id: id },
			callback: function (r) {
				remountWithPayload(page, r.message || null);
			},
			error: function () {
				sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
				bind($(page.main), page);
			},
		});
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Readiness Check & Report"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			frappe.pages[PAGE_SLUG].page = wrapper.page;
			mount(wrapper.page);
		}
	};
})();
