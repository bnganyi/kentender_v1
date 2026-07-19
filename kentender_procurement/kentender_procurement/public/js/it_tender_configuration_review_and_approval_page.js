// WF-02 — Review & Approval (WG-02).
// Route contract: /desk/it-tender-configuration-review-and-approval/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "WF-02";
	var PAGE_SLUG = "it-tender-configuration-review-and-approval";
	var GET_API = "kentender_procurement.tender_configurations.get_tender_configuration_review";
	var SAVE_API = "kentender_procurement.tender_configurations.save_tender_configuration_review";
	var APPROVE_API = "kentender_procurement.tender_configurations.approve_tender_configuration_for_preview";
	var RETURN_API = "kentender_procurement.tender_configurations.return_tender_configuration_for_correction";
	var CLARIFY_API = "kentender_procurement.tender_configurations.request_tender_configuration_clarification";
	var STORAGE_KEY = "kt_cl_wf02_configuration_id";
	var MODAL_HOST_ID = "kt-cl-wf02-modal-host";
	var BACK_ROUTE = "it-tender-configuration-overview";
	var PREVIEW_ROUTE = "it-tender-configuration-render-preview";

	var state = {
		payload: null,
		configurationId: null,
		page: null,
		mounting: false,
		busy: false,
		checklist: [],
		findings: [],
	};

	var STYLE_ID = "kt-cl-wf02-critical-css-v3";

	/** Critical layout travels with page JS so Desk CSS cache cannot leave WF-02 unstyled. */
	function ensureCriticalCss() {
		["kt-cl-wf02-critical-css", "kt-cl-wf02-critical-css-v2"].forEach(function (id) {
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
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-bento{display:grid!important;grid-template-columns:repeat(12,minmax(0,1fr))!important;gap:1rem!important;margin-bottom:1rem!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-summary{grid-column:span 4/span 4!important;background:#fff!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:1rem!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-sections{grid-column:span 8/span 8!important;background:#fff!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;overflow:hidden!important;min-width:0!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-checklist,[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-findings{grid-column:span 6/span 6!important;background:#fff!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;overflow:hidden!important;display:flex!important;flex-direction:column!important;min-width:0!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-panel-head{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:.75rem!important;padding:.65rem 1rem!important;background:#f0f4f8!important;border-bottom:1px solid #c4c6cf!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-panel-head h3{margin:0!important;font-size:11px!important;font-weight:700!important;letter-spacing:.04em!important;text-transform:uppercase!important;color:#5f6368!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi-grid{display:grid!important;grid-template-columns:1fr 1fr!important;gap:.75rem!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi{border-left:4px solid #c4c6cf!important;padding:.5rem .65rem!important;background:#f0f4f8!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi--primary{border-left-color:#002244!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi--success{border-left-color:#16a34a!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi--warning{border-left-color:#d97706!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi--secondary{border-left-color:#5b6470!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi-label{margin:0 0 .2rem!important;font-size:10px!important;font-weight:700!important;text-transform:uppercase!important;color:#5f6368!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi-value{margin:0!important;font-size:1.15rem!important;font-weight:800!important;color:#002244!important;line-height:1.25!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-kpi--success .kt-cl-wf02-kpi-value{color:#15803d!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-meta{margin-top:1rem!important;display:flex!important;flex-direction:column!important;gap:.35rem!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-meta-row{display:flex!important;justify-content:space-between!important;gap:.75rem!important;padding:.45rem 0!important;border-bottom:1px solid rgba(196,198,207,.45)!important;font-size:13px!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-meta-label{color:#5f6368!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-meta-value{font-weight:700!important;color:#002244!important;text-align:right!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-status{display:inline-block!important;padding:.15rem .45rem!important;border-radius:999px!important;font-size:10px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.03em!important;background:#d1fae5!important;color:#065f46!important;border:1px solid #a7f3d0!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-checklist-items{display:flex!important;flex-direction:column!important;gap:1rem!important;padding:1rem!important;max-height:400px!important;overflow-y:auto!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-check-item{display:flex!important;align-items:flex-start!important;gap:.75rem!important;font-size:13px!important;color:#1a1c1e!important;cursor:pointer!important;margin:0!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-check-item input{margin-top:.15rem!important;flex-shrink:0!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-check-note{margin:0!important;padding:1rem!important;border-top:1px solid #c4c6cf!important;font-size:12px!important;font-style:italic!important;color:#5f6368!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-findings-body{padding:1rem!important;flex:1!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-finding-card{border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:.85rem!important;margin-bottom:.75rem!important;background:#f8f9fb!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-finding-empty{display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:.5rem!important;padding:2.5rem 1rem!important;text-align:center!important;color:#5f6368!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-sev{display:inline-block!important;padding:.15rem .45rem!important;border-radius:.25rem!important;font-size:10px!important;font-weight:700!important;text-transform:uppercase!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-sev--correction{background:#f9dedc!important;color:#ba1a1a!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-sev--clarification{background:#dbeafe!important;color:#1e40af!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-sev--note{background:#e7e8eb!important;color:#43474e!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-footer{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:1rem!important;flex-wrap:wrap!important;margin-top:.5rem!important;padding:1rem 0!important;border-top:1px solid #c4c6cf!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-footer-end{display:flex!important;align-items:center!important;gap:.75rem!important;flex-wrap:wrap!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-footer-note{font-size:10px!important;font-style:italic!important;color:#5f6368!important;line-height:1.3!important;text-align:right!important;max-width:9rem!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-return-btn{background:#ba1a1a!important;border-color:#ba1a1a!important;color:#fff!important}" +
			"[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-back-link{display:inline-flex!important;align-items:center!important;gap:.35rem!important}" +
			"@media (max-width:1100px){[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-summary,[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-sections,[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-checklist,[data-testid='kt-cl-wf02-root'] .kt-cl-wf02-findings{grid-column:span 12/span 12!important}}" +
			/* Finding drawer — stacked fields; never Desk side-by-side form chrome */
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-overlay{position:fixed!important;inset:0!important;z-index:1300!important;display:block!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-backdrop{position:absolute!important;inset:0!important;border:0!important;padding:0!important;margin:0!important;background:rgba(0,34,68,.2)!important;cursor:pointer!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer{position:fixed!important;top:0!important;right:0!important;bottom:0!important;width:min(400px,100vw)!important;max-width:100%!important;display:flex!important;flex-direction:column!important;background:#fff!important;border-left:1px solid #c4c6cf!important;box-shadow:-8px 0 24px rgba(16,24,40,.16)!important;z-index:1301!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-header{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:1rem!important;padding:1rem 1.25rem!important;background:#f0f4f8!important;border-bottom:1px solid #c4c6cf!important;flex-shrink:0!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-header h2{margin:0!important;font-size:1.15rem!important;font-weight:700!important;color:#002244!important;line-height:1.3!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-close{display:inline-flex!important;align-items:center!important;justify-content:center!important;width:2.25rem!important;height:2.25rem!important;border:0!important;border-radius:999px!important;background:transparent!important;color:#5f6368!important;cursor:pointer!important;padding:0!important;box-shadow:none!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-close:hover{background:#e7e8eb!important;color:#002244!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-body{flex:1!important;overflow-y:auto!important;padding:1.25rem!important;display:flex!important;flex-direction:column!important;gap:1.25rem!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-field{display:flex!important;flex-direction:column!important;align-items:stretch!important;gap:.45rem!important;width:100%!important;margin:0!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-field-label{display:block!important;margin:0!important;font-size:11px!important;font-weight:700!important;letter-spacing:.04em!important;text-transform:uppercase!important;color:#5f6368!important;float:none!important;width:auto!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-req{color:#ba1a1a!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-control{display:block!important;width:100%!important;max-width:100%!important;box-sizing:border-box!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:.65rem .75rem!important;font-size:13px!important;line-height:1.4!important;background:#f0f4f8!important;color:#1a1c1e!important;box-shadow:none!important;float:none!important;margin:0!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-control--area{min-height:5.5rem!important;resize:vertical!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-sev-picker{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:.5rem!important;width:100%!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-sev-opt{border:1px solid #c4c6cf!important;background:#fff!important;border-radius:.25rem!important;padding:.55rem .35rem!important;font-size:10px!important;font-weight:700!important;text-transform:uppercase!important;color:#5f6368!important;cursor:pointer!important;box-shadow:none!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-sev-opt.is-active{border-color:#002244!important;background:rgba(0,34,68,.08)!important;color:#002244!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-status{margin:0!important;font-size:12px!important;color:#5f6368!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-status strong{color:#d97706!important;text-transform:uppercase!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-footer{display:flex!important;align-items:center!important;justify-content:stretch!important;gap:.75rem!important;padding:1rem 1.25rem!important;border-top:1px solid #c4c6cf!important;background:#f0f4f8!important;flex-shrink:0!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-drawer-footer .kt-cl-wizard-btn{flex:1!important;justify-content:center!important}" +
			/* Centered confirm modals (approve / return) keep stacked fields */
			"#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-overlay .kt-cl-cfg06-field{display:flex!important;flex-direction:column!important;gap:.4rem!important;margin-bottom:.85rem!important;width:100%!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-overlay .kt-cl-cfg06-field label{display:block!important;float:none!important;width:auto!important;margin:0!important;font-size:12px!important;font-weight:600!important;color:#43474e!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-overlay .kt-cl-cfg06-select,#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-overlay .kt-cl-cfg06-input,#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-overlay .kt-cl-cfg06-textarea{display:block!important;width:100%!important;box-sizing:border-box!important;float:none!important;margin:0!important;border:1px solid #c4c6cf!important;border-radius:.25rem!important;padding:.55rem .75rem!important;background:#fff!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-header{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:1rem!important;padding:1rem 1.25rem!important;border-bottom:1px solid #c4c6cf!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-body{padding:1.25rem!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-cfg06-drawer-footer{display:flex!important;gap:.75rem!important;justify-content:flex-end!important;padding:1rem 1.25rem!important;border-top:1px solid #c4c6cf!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-inline-error{margin:.65rem 0 0!important;padding:.55rem .75rem!important;border:1px solid #f2b8b5!important;border-radius:.25rem!important;background:#f9dedc!important;color:#410e0b!important;font-size:13px!important;line-height:1.4!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-inline-error[hidden]{display:none!important}" +
			"#kt-cl-wf02-modal-host .kt-cl-wf02-check-item.is-invalid{outline:2px solid #ba1a1a!important;outline-offset:2px!important;border-radius:.25rem!important}";
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
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-wf02-empty">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="close" data-testid="kt-cl-wf02-close">' +
			__("Close") +
			"</button></div>"
		);
	}

	function stepsCompleteValue(data) {
		var s = (data.summary && data.summary.configuration_steps) || "";
		var m = String(s).match(/(\d+\s+of\s+\d+)/i);
		return m ? m[1] : s || "—";
	}

	function warningsValue(data) {
		var s = (data.summary && data.summary.warnings) || "";
		var m = String(s).match(/(\d+)/);
		if (m) {
			return m[1] + " " + __("Accepted");
		}
		return s || "0 " + __("Accepted");
	}

	function submittedDateValue(data) {
		var raw = (data.summary && data.summary.submitted_on) || "";
		var m = String(raw).match(/^(\d{4}-\d{2}-\d{2})/);
		return m ? m[1] : raw || "—";
	}

	function summaryHtml(data) {
		var s = data.summary || {};
		var readiness = s.readiness_check || data.readiness_result || "—";
		var readinessTone = /pass/i.test(String(readiness)) ? "success" : "secondary";
		return (
			'<aside class="kt-cl-wf02-summary" data-testid="kt-cl-wf02-summary">' +
			'<div class="kt-cl-wf02-summary-title">' +
			"<h3>" +
			__("Review Summary") +
			"</h3>" +
			'<span class="material-symbols-outlined" aria-hidden="true">info</span></div>' +
			'<div class="kt-cl-wf02-kpi-grid">' +
			'<div class="kt-cl-wf02-kpi kt-cl-wf02-kpi--primary" data-testid="kt-cl-wf02-card-steps">' +
			'<p class="kt-cl-wf02-kpi-label">' +
			__("Steps Complete") +
			"</p>" +
			'<p class="kt-cl-wf02-kpi-value">' +
			esc(stepsCompleteValue(data)) +
			"</p></div>" +
			'<div class="kt-cl-wf02-kpi kt-cl-wf02-kpi--' +
			esc(readinessTone) +
			'" data-testid="kt-cl-wf02-card-readiness">' +
			'<p class="kt-cl-wf02-kpi-label">' +
			__("Readiness") +
			"</p>" +
			'<p class="kt-cl-wf02-kpi-value">' +
			esc(readiness) +
			"</p></div>" +
			'<div class="kt-cl-wf02-kpi kt-cl-wf02-kpi--warning" data-testid="kt-cl-wf02-card-warnings">' +
			'<p class="kt-cl-wf02-kpi-label">' +
			__("Warnings") +
			"</p>" +
			'<p class="kt-cl-wf02-kpi-value">' +
			esc(warningsValue(data)) +
			"</p></div>" +
			'<div class="kt-cl-wf02-kpi kt-cl-wf02-kpi--secondary" data-testid="kt-cl-wf02-card-submitted">' +
			'<p class="kt-cl-wf02-kpi-label">' +
			__("Submitted On") +
			"</p>" +
			'<p class="kt-cl-wf02-kpi-value">' +
			esc(submittedDateValue(data)) +
			"</p></div></div>" +
			'<div class="kt-cl-wf02-meta">' +
			'<div class="kt-cl-wf02-meta-row"><span class="kt-cl-wf02-meta-label">' +
			__("Submitted By") +
			'</span><span class="kt-cl-wf02-meta-value">' +
			esc(s.submitted_by || "—") +
			"</span></div>" +
			'<div class="kt-cl-wf02-meta-row"><span class="kt-cl-wf02-meta-label">' +
			__("Assigned Reviewer") +
			'</span><span class="kt-cl-wf02-meta-value">' +
			esc(s.assigned_reviewer || "—") +
			"</span></div></div></aside>"
		);
	}

	function sectionLabel(row) {
		var sid = row.step_id || "";
		var title = row.section || "";
		if (sid && title) {
			return sid + ": " + title;
		}
		return title || sid || "—";
	}

	function sectionsHtml(data) {
		var comp = c();
		var cols = [
			{ label: __("Section") },
			{ label: __("Review Purpose") },
			{ label: __("Status") },
			{ label: __("Action") },
		];
		var rows = (data.sections || []).map(function (row) {
			var route = row.owner_route || "";
			return {
				id: row.step_id || row.section || "",
				cells: [
					{ text: sectionLabel(row) },
					{ text: row.review_purpose || "—" },
					{
						html:
							'<span class="kt-cl-wf02-status">' + esc(row.status || "—") + "</span>",
					},
					{
						html: route
							? '<button type="button" class="kt-cl-wf-row-action" data-action="view-section" data-route="' +
								esc(route) +
								'" data-testid="kt-cl-wf02-section-view-' +
								esc(row.step_id || "") +
								'">' +
								esc(row.action_label || "View") +
								"</button>"
							: esc(row.action_label || "View"),
					},
				],
			};
		});
		return (
			'<section class="kt-cl-wf02-sections" data-testid="kt-cl-wf02-sections">' +
			'<div class="kt-cl-wf02-panel-head">' +
			"<h3>" +
			__("Configuration Sections") +
			"</h3></div>" +
			comp.queueTable({
				columns: cols,
				rows: rows,
				footerText: __("Total sections: {0}", [rows.length]),
				showPageSize: false,
				pagination: null,
			}) +
			"</section>"
		);
	}

	function checklistHtml() {
		var items = state.checklist || [];
		var rows = items
			.map(function (item, idx) {
				var checked = item.checked === 1 || item.checked === true || item.checked === "1";
				return (
					'<label class="kt-cl-wf02-check-item" data-testid="kt-cl-wf02-check-' +
					esc(item.id || String(idx + 1)) +
					'">' +
					'<input type="checkbox" data-check-id="' +
					esc(item.id || "") +
					'" data-testid="kt-cl-wf02-checkbox-' +
					esc(item.id || String(idx + 1)) +
					'"' +
					(checked ? " checked" : "") +
					" />" +
					"<span>" +
					esc(idx + 1 + ". " + (item.label || "")) +
					"</span></label>"
				);
			})
			.join("");
		return (
			'<section class="kt-cl-wf02-checklist" data-testid="kt-cl-wf02-checklist">' +
			'<div class="kt-cl-wf02-panel-head"><h3>' +
			__("Reviewer Checklist") +
			"</h3></div>" +
			'<div class="kt-cl-wf02-checklist-items">' +
			rows +
			"</div>" +
			'<p class="kt-cl-wf02-check-note">' +
			__(
				"Note: Approval here does not publish the tender; it only advances the configuration to the document generation phase."
			) +
			"</p></section>"
		);
	}

	function severityClass(sev) {
		var s = String(sev || "").toLowerCase();
		if (s.indexOf("correction") >= 0) {
			return "correction";
		}
		if (s.indexOf("clarif") >= 0) {
			return "clarification";
		}
		return "note";
	}

	function findingsHtml() {
		var findings = state.findings || [];
		var data = state.payload || {};
		var canAdd = !!(data.return_enabled || data.clarify_enabled);
		var body;
		if (!findings.length) {
			body =
				'<div class="kt-cl-wf02-finding-empty" data-testid="kt-cl-wf02-findings-empty">' +
				'<span class="material-symbols-outlined" aria-hidden="true">rate_review</span>' +
				"<p>" +
				__("No critical findings noted yet.") +
				"</p></div>";
		} else {
			body = findings
				.map(function (f, idx) {
					var sev = f.severity || "Note";
					return (
						'<div class="kt-cl-wf02-finding-card" data-finding-idx="' +
						esc(String(idx)) +
						'" data-testid="kt-cl-wf02-finding-' +
						esc(String(idx)) +
						'">' +
						'<div class="kt-cl-wf02-finding-grid">' +
						'<div><p class="kt-cl-wf02-kpi-label">' +
						__("Type") +
						'</p><span class="kt-cl-wf02-sev kt-cl-wf02-sev--' +
						esc(severityClass(sev)) +
						'">' +
						esc(sev) +
						"</span></div>" +
						'<div><p class="kt-cl-wf02-kpi-label">' +
						__("Area") +
						'</p><span class="kt-cl-wf02-meta-value">' +
						esc(f.section || "—") +
						"</span></div></div>" +
						'<div class="kt-cl-wf02-finding-block"><p class="kt-cl-wf02-kpi-label">' +
						__("Finding") +
						"</p><p>" +
						esc(f.finding || "—") +
						"</p></div>" +
						'<div class="kt-cl-wf02-finding-block"><p class="kt-cl-wf02-kpi-label">' +
						__("Required Action") +
						"</p><p>" +
						esc(f.required_action || "—") +
						"</p></div>" +
						'<div class="kt-cl-wf02-finding-foot">' +
						"<span>" +
						__("Status:") +
						' <strong class="kt-cl-wf02-finding-status">' +
						esc(f.status || "Open") +
						"</strong></span>" +
						'<button type="button" class="kt-cl-wf-row-action" data-action="withdraw-finding" data-finding-idx="' +
						esc(String(idx)) +
						'" data-testid="kt-cl-wf02-finding-withdraw-' +
						esc(String(idx)) +
						'">' +
						__("Withdraw") +
						"</button></div></div>"
					);
				})
				.join("");
		}
		return (
			'<section class="kt-cl-wf02-findings" data-testid="kt-cl-wf02-findings">' +
			'<div class="kt-cl-wf02-panel-head">' +
			"<h3>" +
			__("Review Findings") +
			"</h3>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary kt-cl-wizard-btn--sm" data-action="add-finding" data-testid="kt-cl-wf02-add-finding"' +
			(canAdd ? "" : " disabled") +
			">" +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span> ' +
			__("Add Finding") +
			"</button></div>" +
			'<div class="kt-cl-wf02-findings-body">' +
			body +
			"</div></section>"
		);
	}

	function footerHtml(data) {
		var canApprove = !!(data && data.can_approve);
		return (
			'<div class="kt-cl-wf02-footer" data-testid="kt-cl-wf02-decision">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary kt-cl-wf02-back-link" data-action="close" data-testid="kt-cl-wf02-back">' +
			'<span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>' +
			__("Back to Configuration Home") +
			"</button>" +
			'<div class="kt-cl-wf02-footer-end">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close" data-testid="kt-cl-wf02-close">' +
			__("Close") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--outline" data-action="add-finding" data-testid="kt-cl-wf02-add-finding-footer"' +
			(data.clarify_enabled ? "" : " disabled") +
			">" +
			__("Add Review Finding") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wf02-return-btn" data-action="return" data-testid="kt-cl-wf02-return"' +
			(data.return_enabled && !state.busy ? "" : " disabled") +
			' title="' +
			esc(
				data.return_enabled
					? __("Return using open Correction Required findings")
					: __("Add at least one Correction Required finding before returning")
			) +
			'">' +
			__("Return for Correction") +
			"</button>" +
			'<span class="kt-cl-wf02-footer-note">' +
			__("Non-publication boundary:") +
			"<br/>" +
			__("Advances to preview only") +
			"</span>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="approve" data-testid="kt-cl-wf02-approve"' +
			(canApprove && !state.busy ? "" : " disabled") +
			">" +
			__("Approve for Document Preview") +
			' <span class="material-symbols-outlined" aria-hidden="true">verified</span>' +
			"</button></div></div>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		state.checklist = (data.checklist || []).slice();
		state.findings = (data.findings || []).slice();
		return (
			'<div data-testid="kt-cl-wf02-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			'<div class="kt-cl-wf02-bento" data-testid="kt-cl-wf02-layout">' +
			summaryHtml(data) +
			sectionsHtml(data) +
			checklistHtml() +
			findingsHtml() +
			"</div>" +
			footerHtml(data) +
			"</div>"
		);
	}

	function ensureModalHost() {
		var host = document.getElementById(MODAL_HOST_ID);
		if (!host) {
			host = document.createElement("div");
			host.id = MODAL_HOST_ID;
			document.body.appendChild(host);
		}
		return $(host);
	}

	function closeModal() {
		ensureModalHost().empty().off(".wf02modal");
	}

	function sectionOptions(data) {
		return (data.sections || [])
			.map(function (s) {
				var label = sectionLabel(s);
				return (
					'<option value="' +
					esc(label) +
					'">' +
					esc(label) +
					"</option>"
				);
			})
			.join("");
	}

	function refreshFindingsPanel($root) {
		var $panel = $root.find('[data-testid="kt-cl-wf02-findings"]');
		if ($panel.length) {
			$panel.replaceWith(findingsHtml());
		}
	}

	function openFindingDrawer(page, presetSeverity) {
		closeModal();
		ensureCriticalCss();
		var $host = ensureModalHost();
		var sev = presetSeverity || "Correction Required";
		$host.html(
			'<div class="kt-cl-wf02-drawer-overlay" data-testid="kt-cl-wf02-finding-drawer" role="dialog" aria-modal="true">' +
			'<button type="button" class="kt-cl-wf02-drawer-backdrop" data-action="close-modal" aria-label="' +
			esc(__("Close")) +
			'"></button>' +
			'<aside class="kt-cl-wf02-drawer" data-testid="kt-cl-wf02-finding-drawer-panel">' +
			'<header class="kt-cl-wf02-drawer-header">' +
			"<h2>" +
			__("Add Review Finding") +
			"</h2>" +
			'<button type="button" class="kt-cl-wf02-drawer-close" data-action="close-modal" aria-label="' +
			esc(__("Close")) +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button>' +
			"</header>" +
			'<div class="kt-cl-wf02-drawer-body">' +
			'<div class="kt-cl-wf02-field">' +
			'<label class="kt-cl-wf02-field-label">' +
			__("Type / Severity") +
			"</label>" +
			'<div class="kt-cl-wf02-sev-picker" data-testid="kt-cl-wf02-finding-severity">' +
			'<button type="button" class="kt-cl-wf02-sev-opt' +
			(sev === "Correction Required" ? " is-active" : "") +
			'" data-sev="Correction Required">' +
			__("Correction") +
			"</button>" +
			'<button type="button" class="kt-cl-wf02-sev-opt' +
			(sev === "Clarification" ? " is-active" : "") +
			'" data-sev="Clarification">' +
			__("Clarification") +
			"</button>" +
			'<button type="button" class="kt-cl-wf02-sev-opt' +
			(sev === "Note" ? " is-active" : "") +
			'" data-sev="Note">' +
			__("Note") +
			"</button></div></div>" +
			'<div class="kt-cl-wf02-field">' +
			'<label class="kt-cl-wf02-field-label" for="kt-cl-wf02-finding-section">' +
			__("Configuration Area") +
			' <span class="kt-cl-wf02-req">*</span></label>' +
			'<select id="kt-cl-wf02-finding-section" class="kt-cl-wf02-control" data-testid="kt-cl-wf02-finding-section">' +
			'<option value="">' +
			__("Select…") +
			"</option>" +
			sectionOptions(state.payload || {}) +
			"</select></div>" +
			'<div class="kt-cl-wf02-field">' +
			'<label class="kt-cl-wf02-field-label" for="kt-cl-wf02-finding-title">' +
			__("Finding Title") +
			' <span class="kt-cl-wf02-req">*</span></label>' +
			'<input id="kt-cl-wf02-finding-title" type="text" class="kt-cl-wf02-control" data-testid="kt-cl-wf02-finding-title" placeholder="' +
			esc(__("Short descriptive title")) +
			'" /></div>' +
			'<div class="kt-cl-wf02-field">' +
			'<label class="kt-cl-wf02-field-label" for="kt-cl-wf02-finding-detail">' +
			__("Detailed Finding") +
			"</label>" +
			'<textarea id="kt-cl-wf02-finding-detail" class="kt-cl-wf02-control kt-cl-wf02-control--area" rows="4" data-testid="kt-cl-wf02-finding-detail" placeholder="' +
			esc(__("Describe the issue in plain language…")) +
			'"></textarea></div>' +
			'<div class="kt-cl-wf02-field">' +
			'<label class="kt-cl-wf02-field-label" for="kt-cl-wf02-finding-action">' +
			__("Required Action") +
			' <span class="kt-cl-wf02-req">*</span></label>' +
			'<textarea id="kt-cl-wf02-finding-action" class="kt-cl-wf02-control kt-cl-wf02-control--area" rows="3" data-testid="kt-cl-wf02-finding-action" placeholder="' +
			esc(__("What must be done to resolve this?")) +
			'"></textarea></div>' +
			'<p class="kt-cl-wf02-drawer-status">' +
			__("Status:") +
			' <strong>' +
			__("Open") +
			"</strong></p></div>" +
			'<footer class="kt-cl-wf02-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-modal">' +
			__("Cancel") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-finding" data-testid="kt-cl-wf02-finding-save">' +
			__("Save Finding") +
			"</button></footer></aside></div>"
		);
		$host.data("finding-severity", sev);
		$host.on("click.wf02modal", "[data-action='close-modal']", function (e) {
			e.preventDefault();
			closeModal();
		});
		$host.on("click.wf02modal", ".kt-cl-wf02-sev-opt", function (e) {
			e.preventDefault();
			$host.find(".kt-cl-wf02-sev-opt").removeClass("is-active");
			$(this).addClass("is-active");
			$host.data("finding-severity", $(this).attr("data-sev"));
		});
		$host.on("click.wf02modal", "[data-action='save-finding']", function (e) {
			e.preventDefault();
			var severity = String($host.data("finding-severity") || "Correction Required");
			var section = String($host.find('[data-testid="kt-cl-wf02-finding-section"]').val() || "").trim();
			var title = String($host.find('[data-testid="kt-cl-wf02-finding-title"]').val() || "").trim();
			var detail = String($host.find('[data-testid="kt-cl-wf02-finding-detail"]').val() || "").trim();
			var action = String($host.find('[data-testid="kt-cl-wf02-finding-action"]').val() || "").trim();
			if (!section || !title || !action) {
				frappe.msgprint(__("Area, finding title, and required action are mandatory."));
				return;
			}
			state.findings = (state.findings || []).concat([
				{
					finding: title,
					detail: detail,
					section: section,
					severity: severity,
					required_action: action,
					status: "Open",
				},
			]);
			closeModal();
			saveWorkspaceThen(function () {
				var $root = $(page.main);
				refreshFindingsPanel($root);
				syncDecisionButtons($root);
				frappe.show_alert({ message: __("Finding saved"), indicator: "blue" }, 4);
			});
		});
	}

	function openApproveModal(page) {
		closeModal();
		var $host = ensureModalHost();
		$host.html(
			'<div class="kt-cl-cfg06-drawer-overlay" data-testid="kt-cl-wf02-approve-modal" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-wf-modal">' +
			'<header class="kt-cl-cfg06-drawer-header"><h2>' +
			__("Approve for Document Preview") +
			"</h2></header>" +
			'<div class="kt-cl-cfg06-drawer-body">' +
			"<p>" +
			__(
				"You are approving this tender configuration to proceed to document preview. This does not publish the tender, notify bidders, open bid submission, or approve any award."
			) +
			"</p>" +
			'<label class="kt-cl-wf02-check-item" data-testid="kt-cl-wf02-approve-confirm-wrap">' +
			'<input type="checkbox" data-testid="kt-cl-wf02-approve-confirm" />' +
			"<span>" +
			__(
				"I confirm that this approval only allows the tender document preview to be generated or viewed."
			) +
			"</span></label>" +
			'<p class="kt-cl-wf02-inline-error" data-testid="kt-cl-wf02-approve-confirm-error" hidden></p>' +
			"</div>" +
			'<footer class="kt-cl-cfg06-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="confirm-approve" data-testid="kt-cl-wf02-approve-confirm-btn">' +
			__("Approve for Preview") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-modal">' +
			__("Cancel") +
			"</button></footer></aside></div>"
		);
		function clearApproveError() {
			$host
				.find('[data-testid="kt-cl-wf02-approve-confirm-error"]')
				.attr("hidden", "hidden")
				.text("");
			$host.find('[data-testid="kt-cl-wf02-approve-confirm-wrap"]').removeClass("is-invalid");
		}
		function showApproveError(msg) {
			$host
				.find('[data-testid="kt-cl-wf02-approve-confirm-error"]')
				.removeAttr("hidden")
				.text(msg);
			$host.find('[data-testid="kt-cl-wf02-approve-confirm-wrap"]').addClass("is-invalid");
			$host.find('[data-testid="kt-cl-wf02-approve-confirm"]').trigger("focus");
		}
		$host.on("click.wf02modal", "[data-action='close-modal']", function (e) {
			e.preventDefault();
			closeModal();
		});
		$host.on("click.wf02modal", "[data-testid='kt-cl-wf02-approve-modal']", function (e) {
			if (e.target === this) {
				closeModal();
			}
		});
		$host.on("change.wf02modal", '[data-testid="kt-cl-wf02-approve-confirm"]', function () {
			if ($(this).prop("checked")) {
				clearApproveError();
			}
		});
		$host.on("click.wf02modal", "[data-action='confirm-approve']", function (e) {
			e.preventDefault();
			if (!$host.find('[data-testid="kt-cl-wf02-approve-confirm"]').prop("checked")) {
				// Keep validation inside the approve modal — never stack a Frappe msgprint dialog.
				showApproveError(__("Confirm the approval statement before continuing."));
				return;
			}
			closeModal();
			state.busy = true;
			saveChecklistThen(function () {
				frappe.call({
					method: APPROVE_API,
					args: {
						configuration_id: state.configurationId,
						payload: { confirm_preview_only: 1 },
					},
					callback: function (r) {
						state.busy = false;
						var data = r.message || null;
						if (data && data.approved) {
							frappe.show_alert(
								{ message: __("Approved for document preview"), indicator: "green" },
								5
							);
							frappe.route_options = { configuration_id: state.configurationId };
							frappe.set_route(PREVIEW_ROUTE, state.configurationId);
							return;
						}
						remountWithPayload(page, data || state.payload);
					},
					error: function () {
						state.busy = false;
						remountWithPayload(page, state.payload || {});
					},
				});
			});
		});
	}

	function openCorrectionFindings() {
		var out = [];
		(state.findings || []).forEach(function (f) {
			if (!f || typeof f !== "object") {
				return;
			}
			var sev = String(f.severity || "");
			var st = String(f.status || "Open");
			if (sev === "Correction Required" && (st === "Open" || st === "")) {
				out.push(f);
			}
		});
		return out;
	}

	function openReturnModal(page) {
		closeModal();
		var openCorr = openCorrectionFindings();
		if (!openCorr.length) {
			frappe.msgprint(
				__("Add at least one Correction Required finding before returning for correction.")
			);
			return;
		}
		var $host = ensureModalHost();
		var countLabel =
			openCorr.length === 1
				? __("1 Correction Required finding will be sent to the configuration team.")
				: __("{0} Correction Required findings will be sent to the configuration team.").replace(
						"{0}",
						String(openCorr.length)
					);
		var listHtml = openCorr
			.map(function (f) {
				return (
					'<li><strong>' +
					esc(f.section || "—") +
					"</strong> — " +
					esc(f.finding || f.required_action || "—") +
					"</li>"
				);
			})
			.join("");
		$host.html(
			'<div class="kt-cl-cfg06-drawer-overlay" data-testid="kt-cl-wf02-return-modal" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-wf-modal">' +
			'<header class="kt-cl-cfg06-drawer-header"><h2>' +
			__("Return for Correction") +
			"</h2></header>" +
			'<div class="kt-cl-cfg06-drawer-body" data-testid="kt-cl-wf02-return-confirm-body">' +
			"<p>" +
			__(
				"Returning this configuration will send it back to the configuration team. Open correction findings must be fixed and readiness must pass again before resubmit."
			) +
			"</p>" +
			'<p class="kt-cl-wf02-return-count" data-testid="kt-cl-wf02-return-count">' +
			esc(countLabel) +
			"</p>" +
			'<ul class="kt-cl-wf02-return-list" data-testid="kt-cl-wf02-return-finding-list">' +
			listHtml +
			"</ul></div>" +
			'<footer class="kt-cl-cfg06-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="confirm-return" data-testid="kt-cl-wf02-return-confirm-btn">' +
			__("Return for Correction") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-modal" data-testid="kt-cl-wf02-return-cancel">' +
			__("Cancel") +
			"</button></footer></aside></div>"
		);
		$host.on("click.wf02modal", "[data-action='close-modal']", function (e) {
			e.preventDefault();
			closeModal();
		});
		$host.on("click.wf02modal", "[data-action='confirm-return']", function (e) {
			e.preventDefault();
			closeModal();
			state.busy = true;
			frappe.call({
				method: RETURN_API,
				args: {
					configuration_id: state.configurationId,
					payload: { confirm_return: 1 },
				},
				callback: function (r) {
					state.busy = false;
					var data = r.message || null;
					if (data && data.returned) {
						frappe.show_alert(
							{ message: __("Returned for correction"), indicator: "orange" },
							5
						);
					}
					remountWithPayload(page, data || state.payload);
				},
				error: function () {
					state.busy = false;
					remountWithPayload(page, state.payload || {});
				},
			});
		});
	}

	function openClarifyModal(page) {
		closeModal();
		var $host = ensureModalHost();
		$host.html(
			'<div class="kt-cl-cfg06-drawer-overlay" data-testid="kt-cl-wf02-clarify-modal" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-wf-modal">' +
			'<header class="kt-cl-cfg06-drawer-header"><h2>' +
			__("Request Clarification") +
			"</h2></header>" +
			'<div class="kt-cl-cfg06-drawer-body">' +
			'<div class="kt-cl-cfg06-field"><label>' +
			__("Clarification question") +
			' <span class="kt-cl-cfg06-req">*</span></label>' +
			'<textarea class="kt-cl-cfg06-textarea" rows="3" data-testid="kt-cl-wf02-clarify-question"></textarea></div></div>' +
			'<footer class="kt-cl-cfg06-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="confirm-clarify" data-testid="kt-cl-wf02-clarify-confirm-btn">' +
			__("Request Clarification") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-modal">' +
			__("Cancel") +
			"</button></footer></aside></div>"
		);
		$host.on("click.wf02modal", "[data-action='close-modal']", function (e) {
			e.preventDefault();
			closeModal();
		});
		$host.on("click.wf02modal", "[data-action='confirm-clarify']", function (e) {
			e.preventDefault();
			var question = String($host.find('[data-testid="kt-cl-wf02-clarify-question"]').val() || "").trim();
			if (!question) {
				frappe.msgprint(__("Clarification question is required."));
				return;
			}
			closeModal();
			state.busy = true;
			frappe.call({
				method: CLARIFY_API,
				args: {
					configuration_id: state.configurationId,
					payload: { question: question },
				},
				callback: function (r) {
					state.busy = false;
					remountWithPayload(page, r.message || state.payload);
					frappe.show_alert({ message: __("Clarification recorded"), indicator: "blue" }, 4);
				},
				error: function () {
					state.busy = false;
					remountWithPayload(page, state.payload || {});
				},
			});
		});
	}

	function collectChecklistFromDom($root) {
		var out = (state.checklist || []).map(function (item) {
			return {
				id: item.id,
				label: item.label,
				checked: $root.find('[data-check-id="' + item.id + '"]').prop("checked") ? 1 : 0,
			};
		});
		state.checklist = out;
		return out;
	}

	function syncDecisionButtons($root) {
		var data = state.payload || {};
		var openN = openCorrectionFindings().length;
		// Keep return_enabled in sync with local findings after add/withdraw (before remount).
		data.return_enabled = !!(data.clarify_enabled && openN > 0);
		data.open_correction_count = openN;
		state.payload = data;
		$root
			.find('[data-testid="kt-cl-wf02-approve"]')
			.prop("disabled", !(data.can_approve && !state.busy));
		$root
			.find('[data-testid="kt-cl-wf02-return"]')
			.prop("disabled", !(data.return_enabled && !state.busy));
		$root
			.find('[data-testid="kt-cl-wf02-add-finding"], [data-testid="kt-cl-wf02-add-finding-footer"]')
			.prop("disabled", !data.clarify_enabled || !!state.busy);
	}

	function saveWorkspaceThen(done) {
		frappe.call({
			method: SAVE_API,
			args: {
				configuration_id: state.configurationId,
				payload: {
					checklist: state.checklist || [],
					findings: state.findings || [],
				},
			},
			callback: function (r) {
				state.payload = r.message || state.payload;
				if (state.payload) {
					state.payload.checklist = state.checklist;
					state.payload.findings = state.findings;
					state.findings = (state.payload.findings || state.findings || []).slice();
				}
				if (typeof done === "function") {
					done();
				}
			},
			error: function () {
				if (typeof done === "function") {
					done();
				}
			},
		});
	}

	function saveChecklistThen(done) {
		saveWorkspaceThen(done);
	}

	function remountWithPayload(page, data) {
		ensureCriticalCss();
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Review & Approval"),
			subtitle: __(
				"Review the completed tender configuration and decide whether it can proceed to document preview."
			),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? pageHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
	}

	function bind($root, page) {
		$root.off(".wf02");
		$root.on("change.wf02", "[data-check-id]", function () {
			// Persist in place — never remount (remount resets main scroll to top).
			collectChecklistFromDom($root);
			saveChecklistThen(function () {
				syncDecisionButtons($root);
			});
		});
		$root.on("click.wf02", "[data-action='view-section']", function (e) {
			e.preventDefault();
			var route = String($(this).attr("data-route") || "").trim();
			if (!route || !state.configurationId) {
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(route, state.configurationId);
		});
		$root.on("click.wf02", "[data-action='close']", function (e) {
			e.preventDefault();
			closeModal();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route(BACK_ROUTE, state.configurationId);
		});
		$root.on("click.wf02", "[data-action='approve']", function (e) {
			e.preventDefault();
			collectChecklistFromDom($root);
			openApproveModal(page);
		});
		$root.on("click.wf02", "[data-action='return']", function (e) {
			e.preventDefault();
			openReturnModal(page);
		});
		$root.on("click.wf02", "[data-action='clarify']", function (e) {
			e.preventDefault();
			openFindingDrawer(page, "Clarification");
		});
		$root.on("click.wf02", "[data-action='add-finding']", function (e) {
			e.preventDefault();
			openFindingDrawer(page, "Correction Required");
		});
		$root.on("click.wf02", "[data-action='withdraw-finding']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-finding-idx"), 10);
			if (isNaN(idx) || idx < 0) {
				return;
			}
			state.findings = (state.findings || []).filter(function (_f, i) {
				return i !== idx;
			});
			saveWorkspaceThen(function () {
				refreshFindingsPanel($root);
				syncDecisionButtons($root);
			});
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
			title: __("Review & Approval"),
			subtitle: __(
				"Review the completed tender configuration and decide whether it can proceed to document preview."
			),
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
			title: __("Review & Approval"),
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
