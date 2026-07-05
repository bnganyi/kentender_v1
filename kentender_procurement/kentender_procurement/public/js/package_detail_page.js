/* Package Detail Page — dedicated Desk page wired to get_pp3_package_detail */

(function () {
	"use strict";

	frappe.provide("kentender_procurement");

	var DETAIL_API =
		"kentender_procurement.procurement_planning.api.package_detail.get_pp3_package_detail";
	var RUN_READINESS_API =
		"kentender_procurement.procurement_planning.api.package_readiness.run_pp_package_readiness_checks";
	var SUBMIT_API =
		"kentender_procurement.procurement_planning.api.workflow.submit_package";
	var APPROVE_API =
		"kentender_procurement.procurement_planning.api.workflow.approve_package";
	var RETURN_API =
		"kentender_procurement.procurement_planning.api.workflow.return_package";
	var CLARIFY_API =
		"kentender_procurement.procurement_planning.api.workflow.request_clarification";
	var RELEASE_API =
		"kentender_procurement.procurement_planning.api.package_release.release_pp_package_to_tender";

	var TABS = [
		{ id: "overview", label: __("Overview"), testId: "kt-pd-tab-overview" },
		{ id: "lines_funding", label: __("Lines & Funding"), testId: "kt-pd-tab-lines-funding" },
		{ id: "readiness", label: __("Readiness"), testId: "kt-pd-tab-readiness" },
		{ id: "review", label: __("Review"), testId: "kt-pd-tab-review" },
		{ id: "release", label: __("Release"), testId: "kt-pd-tab-release" },
	];

	var _state = {
		packageCode: "",
		activeTab: "overview",
		detail: null,
		reviewSummary: "",
		_wrapper: null,
		_token: 0,
	};

	function _esc(v) {
		return frappe.utils.escape_html(String(v == null ? "" : v));
	}

	function _ico(name, fill) {
		var s = fill ? ' style="font-variation-settings:\'FILL\' 1"' : "";
		return '<span class="material-symbols-outlined"' + s + ">" + name + "</span>";
	}

	function _pillClass(pill) {
		var p = String(pill || "").toUpperCase();
		if (p.indexOf("CREATION") >= 0) return "kt-pd-pill--creation";
		if (p.indexOf("REVIEW") >= 0) return "kt-pd-pill--review";
		if (p.indexOf("READY") >= 0) return "kt-pd-pill--ready";
		if (p.indexOf("BLOCK") >= 0) return "kt-pd-pill--blocked";
		if (p.indexOf("RELEASE") >= 0) return "kt-pd-pill--released";
		if (p.indexOf("APPROVED") >= 0) return "kt-pd-pill--approved";
		return "kt-pd-pill--creation";
	}

	function _resolvePackageCode() {
		var opts = frappe.route_options || {};
		if (opts.package) return String(opts.package).trim();
		var route = frappe.get_route() || [];
		if (route[0] === "package-detail" && route[1]) return String(route[1]).trim();
		return "";
	}

	function _call(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: method,
				args: args || {},
				callback: function (r) {
					resolve((r && r.message) || r || {});
				},
				error: function () {
					reject(new Error(__("Planning information could not be loaded. Try again.")));
				},
			});
		});
	}

	function _evidenceDrawer() {
		return (
			kentender_procurement.PlanningWorkbenchEvidenceDrawer ||
			kentender_procurement.PlanningEvidenceDrawer ||
			null
		);
	}

	function _openEvidence(code, opts) {
		var drawer = _evidenceDrawer();
		if (!drawer || typeof drawer.open !== "function") return;
		drawer.open({
			package_code: String(code || "").trim(),
			title: (opts && opts.title) || __("Evidence"),
			filter: (opts && opts.filter) || "",
		});
	}

	var WORKBENCH_ROOT = "/desk/procurement-planning";
	var WORKBENCH_QUEUE_BY_PKG_STATUS = {
		Draft: "draft_packages",
		"In Review": "needs_review",
		"Returned for Correction": "draft_packages",
		Approved: "ready_to_release",
		"Ready for Release": "ready_to_release",
		"Released to Tender": "recently_released",
		"Consumed by Tender Management": "recently_released",
	};

	function _workbenchQueueForStatus(status) {
		var st = String(status || "").trim();
		return WORKBENCH_QUEUE_BY_PKG_STATUS[st] || "draft_packages";
	}

	function _buildWorkbenchBackUrl(detail) {
		var d = detail || {};
		var url = new URL(window.location.origin + WORKBENCH_ROOT);
		var code = String(d.package_code || _state.packageCode || "").trim();
		var queue = _workbenchQueueForStatus(d.package_status);
		url.searchParams.set("queue", queue);
		if (code) {
			url.searchParams.set("package_code", code);
		}
		return url.pathname + url.search;
	}

	function _ensureFonts() {
		if (document.getElementById("kt-pd-fonts")) return;
		var link = document.createElement("link");
		link.id = "kt-pd-fonts";
		link.rel = "stylesheet";
		link.href =
			"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&" +
			"family=Hanken+Grotesk:wght@600;700;800&" +
			"family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap";
		document.head.appendChild(link);
	}

	function _bannerHtml(d) {
		var b = (d && d.blocker_banner) || {};
		if (!b.visible) return "";
		return (
			'<section class="kt-pd-banner" data-testid="kt-pd-blocker-banner">' +
			'<div class="kt-pd-banner__title">' +
			_ico("error", true) +
			_esc(b.title || __("Blocker Alert")) +
			"</div>" +
			'<p class="kt-pd-banner__body">' +
			_esc(b.message || "") +
			"</p></section>"
		);
	}

	function _tabsHtml(active) {
		var html = '<nav class="kt-pd-tabs" data-testid="kt-pd-tabs">';
		for (var i = 0; i < TABS.length; i += 1) {
			var tab = TABS[i];
			var cls = tab.id === active ? " kt-pd-tab--active" : "";
			html +=
				'<button type="button" class="kt-pd-tab' +
				cls +
				'" data-testid="' +
				_esc(tab.testId) +
				'" data-tab="' +
				_esc(tab.id) +
				'">' +
				_esc(tab.label) +
				"</button>";
		}
		return html + "</nav>";
	}

	function _footerHtml() {
		return (
			'<footer class="kt-pd-footer" data-testid="kt-pd-footer">' +
			'<span class="kt-pd-footer__brand">' +
			__("© 2024 Institutional Procurement System") +
			"</span>" +
			'<div class="kt-pd-footer__links">' +
			'<span class="kt-pd-footer__link">' +
			__("Privacy Policy") +
			"</span>" +
			'<span class="kt-pd-footer__link">' +
			__("Terms of Service") +
			"</span>" +
			'<span class="kt-pd-footer__link">' +
			__("Audit Log") +
			"</span>" +
			'<span class="kt-pd-footer__stable">' +
			'<span class="kt-pd-footer__dot"></span>' +
			__("System Stable") +
			"</span></div></footer>"
		);
	}

	function _tabHostHtml(d) {
		return _bannerHtml(d) + _tabPanelHtml(d);
	}

	function _updateTabButtons(wrapper) {
		wrapper.querySelectorAll("[data-tab]").forEach(function (btn) {
			var tabId = String(btn.getAttribute("data-tab") || "");
			btn.classList.toggle("kt-pd-tab--active", tabId === _state.activeTab);
		});
	}

	function _updateTabHost(wrapper, d) {
		var host = wrapper.querySelector('[data-testid="kt-pd-tab-host"]');
		if (!host || !d) return;
		host.innerHTML = _tabHostHtml(d);
	}

	function _updateSidebar(wrapper, d) {
		var aside = wrapper.querySelector('[data-testid="kt-pd-sidebar"]');
		if (!aside || !d) return;
		aside.innerHTML = _sidebarHtml(d);
	}

	function _activatePageChrome() {
		document.body.classList.add("kt-pd-page-active");
	}

	function _deactivatePageChrome() {
		document.body.classList.remove("kt-pd-page-active");
	}

	function _releaseChecklistHtml(tab) {
		var checks = (tab && tab.readiness_checklist) || [];
		if (!checks.length) return "";
		var rows = checks
			.map(function (c) {
				var mark = c.ok ? _ico("check_circle", true) : _ico("cancel");
				var color = c.ok ? "var(--pd-success)" : "var(--pd-error-bright)";
				return (
					"<li><span style=\"color:" +
					color +
					'">' +
					mark +
					"</span><span>" +
					_esc(c.label) +
					"</span></li>"
				);
			})
			.join("");
		return (
			'<div class="kt-pd-card"><div class="kt-pd-card__head"><h2 class="kt-pd-card__title">' +
			__("Release Checklist") +
			"</h2>" +
			(tab.checklist_summary_label
				? '<span class="kt-pd-checklist-summary">' + _esc(tab.checklist_summary_label) + "</span>"
				: "") +
			'</div><ul class="kt-pd-checklist" data-testid="kt-pd-release-checklist">' +
			rows +
			"</ul></div>"
		);
	}

	function _activityHtml(items) {
		var rows = (items || [])
			.map(function (row) {
				return (
					'<div class="kt-pd-activity-item" data-testid="kt-pd-activity-row">' +
					'<div class="kt-pd-activity-title">' +
					_esc(row.title) +
					"</div>" +
					'<div class="kt-pd-activity-meta">' +
					_esc(row.meta) +
					"</div></div>"
				);
			})
			.join("");
		if (!rows) {
			rows =
				'<p class="kt-pd-muted">' + __("No recent activity recorded yet.") + "</p>";
		}
		return rows;
	}

	function _field(label, value) {
		return (
			'<div><div class="kt-pd-label">' +
			_esc(label) +
			'</div><div class="kt-pd-value">' +
			_esc(value || "—") +
			"</div></div>"
		);
	}

	function _overviewPanel(d) {
		var id = d.package_identity || {};
		var ov = (d.tabs && d.tabs.overview) || {};
		var demands = d.included_demands || [];
		var lines = d.package_lines || [];
		var demandCards = demands
			.map(function (row) {
				return (
					'<div class="kt-pd-demand-card" data-testid="kt-pd-included-demand">' +
					"<div><h4 style=\"font-size:16px;font-weight:600;color:var(--pd-primary)\">" +
					_esc(row.name) +
					"</h4><p style=\"font-size:12px;color:var(--pd-on-muted);margin:4px 0 0\">" +
					_esc(row.code) +
					" • " +
					_esc(row.line_count_label) +
					"</p></div>" +
					'<div style="text-align:right"><div class="kt-pd-label">' +
					__("Est. Value") +
					'</div><div style="font-weight:600">' +
					_esc(row.value_label) +
					"</div></div></div>"
				);
			})
			.join("");
		var tableRows = lines
			.map(function (ln) {
				return (
					"<tr><td><strong>" +
					_esc(ln.title) +
					"</strong></td><td>" +
					_esc(ln.source_item_code) +
					"</td><td>" +
					_esc(ln.quantity_label) +
					"</td><td><strong>" +
					_esc(ln.value_label) +
					"</strong></td></tr>"
				);
			})
			.join("");
		return (
			'<section data-testid="kt-pd-panel-overview">' +
			'<div class="kt-pd-card"><div class="kt-pd-card__head">' +
			'<h2 class="kt-pd-card__title">' +
			__("Package Identity") +
			"</h2>" +
			(d.package_status === "Draft Package"
				? '<button type="button" class="kt-pd-icon-btn" data-action="modify_package" data-testid="kt-pd-modify-package" title="' +
					_esc(__("Modify Package")) +
					'">' +
					_ico("edit") +
					"</button>"
				: "") +
			'</div><div class="kt-pd-grid-2">' +
			'<div class="kt-pd-field-span">' +
			_field(__("Description"), id.description || ov.package_purpose) +
			"</div>" +
			_field(__("Category"), id.category_label) +
			_field(__("Procurement Method"), id.method_label) +
			_field(__("Target Release Date"), id.target_release_date) +
			_field(__("Owner"), id.owner_label) +
			_field(__("Estimated Value"), id.estimated_value_label) +
			"</div></div>" +
			'<div class="kt-pd-section-head"><h3 class="kt-pd-card__title">' +
			__("Included Demands") +
			"</h3></div>" +
			demandCards +
			'<div class="kt-pd-card kt-pd-card--flush">' +
			'<div class="kt-pd-card__head kt-pd-card__head--bordered">' +
			'<h2 class="kt-pd-card__title">' +
			__("Package Lines") +
			"</h2>" +
			'<span class="kt-pd-muted">' +
			String(lines.length) +
			" " +
			__("Lines Identified") +
			"</span></div>" +
			'<table class="kt-pd-table" data-testid="kt-pd-lines-table"><thead><tr><th>' +
			__("Title") +
			"</th><th>" +
			__("Source Demand Item") +
			"</th><th>" +
			__("Quantity") +
			"</th><th>" +
			__("Total Value") +
			"</th></tr></thead><tbody>" +
			(tableRows ||
				'<tr><td colspan="4" style="color:var(--pd-on-muted)">' +
					__("No package lines yet.") +
					"</td></tr>") +
			"</tbody></table></div></section>"
		);
	}

	function _linesPanel(d) {
		var tab = (d.tabs && d.tabs.lines_funding) || {};
		var lines = tab.lines || [];
		var rows = lines
			.map(function (ln) {
				return (
					"<tr><td>" +
					_esc(ln.demand_item_label) +
					"</td><td>" +
					_esc(ln.package_line_label) +
					"</td><td>" +
					_esc(ln.value_label) +
					"</td></tr>"
				);
			})
			.join("");
		return (
			'<section data-testid="kt-pd-panel-lines-funding">' +
			'<div class="kt-pd-card"><div class="kt-pd-grid-2">' +
			_field(__("Package Total"), tab.package_total_label) +
			_field(__("Funding"), tab.funding_label) +
			_field(__("Difference"), tab.difference_label) +
			"</div></div>" +
			'<div class="kt-pd-card" style="padding:0;overflow:hidden"><table class="kt-pd-table"><thead><tr><th>' +
			__("Demand Item") +
			"</th><th>" +
			__("Package Line") +
			"</th><th>" +
			__("Value") +
			"</th></tr></thead><tbody>" +
			(rows ||
				'<tr><td colspan="3">' +
					__("No package lines yet.") +
					"</td></tr>") +
			"</tbody></table></div></section>"
		);
	}

	function _readinessPanel(d) {
		var tab = (d.tabs && d.tabs.readiness) || {};
		var checks = tab.checks || [];
		var list = checks
			.map(function (c) {
				var mark = c.ok ? _ico("check_circle", true) : _ico("cancel");
				var color = c.ok ? "var(--pd-success)" : "var(--pd-error-bright)";
				return (
					"<li><span style=\"color:" +
					color +
					'">' +
					mark +
					"</span><span>" +
					_esc(c.label) +
					"</span></li>"
				);
			})
			.join("");
		var runDisabled = tab.may_run ? "" : " disabled";
		return (
			'<section data-testid="kt-pd-panel-readiness">' +
			'<div class="kt-pd-card">' +
			_field(__("Current Readiness"), tab.summary_label) +
			'<ul class="kt-pd-checklist" data-testid="kt-pd-readiness-checks">' +
			list +
			"</ul>" +
			'<button type="button" class="kt-pd-btn kt-pd-btn--primary" data-action="run_readiness" data-testid="kt-pd-run-readiness"' +
			runDisabled +
			">" +
			_esc(tab.failed ? __("Run Checks Again") : __("Run Readiness Checks")) +
			"</button></div></section>"
		);
	}

	function _reviewPanel(d) {
		var tab = (d.tabs && d.tabs.review) || {};
		var history = tab.decision_history || [];
		var clarifications = tab.clarifications || [];
		var historyHtml = history.length
			? history
					.map(function (row) {
						return (
							'<div class="kt-pd-history-item" data-testid="kt-pd-decision-history-row">' +
							'<div class="kt-pd-history-type">' +
							_esc(row.decision_type) +
							"</div>" +
							'<div class="kt-pd-history-meta">' +
							_esc(row.decided_by_label || row.decided_by) +
							" • " +
							_esc(row.decided_at) +
							(row.decision_reason
								? "<br>" + _esc(row.decision_reason)
								: "") +
							"</div></div>"
						);
					})
					.join("")
			: '<p style="color:var(--pd-on-muted);font-style:italic">' +
				__("No review decisions recorded yet.") +
				"</p>";
		var clarifyNotes = clarifications.length
			? clarifications
					.map(function (c) {
						return (
							'<div class="kt-pd-history-item"><div class="kt-pd-history-type">' +
							__("Clarification Requested") +
							"</div><div class=\"kt-pd-history-meta\">" +
							_esc(c.decision_reason) +
							"</div></div>"
						);
					})
					.join("")
			: "";
		return (
			'<section data-testid="kt-pd-panel-review">' +
			'<div class="kt-pd-card">' +
			_field(__("Review Status"), tab.status_label) +
			clarifyNotes +
			'<label class="kt-pd-label" style="display:block;margin:16px 0 8px">' +
			__("Final Review Summary (Optional)") +
			'</label><textarea class="kt-pd-textarea" data-testid="kt-pd-review-summary" placeholder="' +
			_esc(__("Enter your final assessment or rationale here…")) +
			'">' +
			_esc(_state.reviewSummary) +
			"</textarea></div>" +
			'<div class="kt-pd-card"><h3 class="kt-pd-card__title" style="margin-bottom:12px">' +
			__("Review History") +
			"</h3>" +
			historyHtml +
			"</div></section>"
		);
	}

	function _releasePanel(d) {
		var tab = (d.tabs && d.tabs.release) || {};
		var summary =
			'<div class="kt-pd-card kt-pd-release-summary" data-testid="kt-pd-release-summary">' +
			'<div class="kt-pd-grid-2">' +
			_field(__("Final Package Value"), tab.package_total_label) +
			_field(__("Procurement Method"), tab.method_label) +
			"</div></div>";
		if (tab.released) {
			var handoff = tab.handoff || {};
			return (
				'<section data-testid="kt-pd-panel-release">' +
				'<div class="kt-pd-success-banner"><div>' +
				_ico("task_alt", true) +
				'</div><div><h3 class="kt-pd-success-title">' +
				_esc(tab.headline || __("Package Successfully Released")) +
				"</h3><p class=\"kt-pd-muted\">" +
				_esc(tab.subheadline || "") +
				"</p></div></div>" +
				summary +
				'<div class="kt-pd-bento">' +
				'<div class="kt-pd-bento-card"><div class="kt-pd-label">' +
				__("Financial Handoff") +
				"</div><div class=\"kt-pd-bento-value\">" +
				_esc(handoff.package_value_label || tab.package_total_label) +
				"</div></div>" +
				'<div class="kt-pd-bento-card"><div class="kt-pd-label">' +
				__("Asset Package") +
				"</div><div class=\"kt-pd-bento-value\">" +
				_esc(handoff.method_label || tab.method_label) +
				"</div></div></div>" +
				_releaseChecklistHtml(tab) +
				(tab.tender_open_route
					? '<a class="kt-pd-btn kt-pd-btn--primary" data-testid="kt-pd-open-tender" href="' +
						_esc(tab.tender_open_route) +
						'">' +
						__("Open in Tender Management") +
						" " +
						_ico("open_in_new") +
						"</a>"
					: "") +
				"</section>"
			);
		}
		var blockers = (tab.blockers || [])
			.map(function (b) {
				return "<li>" + _esc(b) + "</li>";
			})
			.join("");
		var releaseDisabled = tab.may_release ? "" : " disabled";
		var approvedNote = tab.approved_pending_readiness
			? '<p class="kt-pd-approved-note" data-testid="kt-pd-approved-note">' +
				_esc(tab.subheadline || "") +
				"</p>"
			: "";
		return (
			'<section data-testid="kt-pd-panel-release">' +
			approvedNote +
			'<div class="kt-pd-card"><h2 class="kt-pd-card__title">' +
			_esc(tab.headline || __("Release to Tender Management")) +
			"</h2>" +
			summary +
			_releaseChecklistHtml(tab) +
			'<div class="kt-pd-grid-2" style="margin-top:16px">' +
			_field(__("Ready to Release"), tab.ready_label) +
			_field(__("Next Action"), tab.next_action_label || "—") +
			"</div>" +
			(blockers
				? '<ul class="kt-pd-blocker-list">' + blockers + "</ul>"
				: "") +
			(tab.warning ? '<p class="kt-pd-muted">' + _esc(tab.warning) + "</p>" : "") +
			'<button type="button" class="kt-pd-btn kt-pd-btn--primary" data-action="release_to_tender" data-testid="kt-pd-release-action"' +
			releaseDisabled +
			">" +
			_ico("rocket_launch") +
			__("Release to Tender") +
			"</button></div></section>"
		);
	}

	function _tabPanelHtml(d) {
		switch (_state.activeTab) {
			case "lines_funding":
				return _linesPanel(d);
			case "readiness":
				return _readinessPanel(d);
			case "review":
				return _reviewPanel(d);
			case "release":
				return _releasePanel(d);
			default:
				return _overviewPanel(d);
		}
	}

	function _sidebarHtml(d) {
		var tab = (d.tabs && d.tabs.review) || {};
		var rel = (d.tabs && d.tabs.release) || {};
		var sum = d.sidebar_summary || {};
		var ctx = d.sidebar_context || {};
		var activity = d.sidebar_activity || [];
		var status = String(d.package_status || "");
		var html = "";

		if (ctx.mode === "blocked") {
			html +=
				'<div class="kt-pd-sidebar-card kt-pd-sidebar-card--alert" data-testid="kt-pd-status-info">' +
				'<div class="kt-pd-sidebar-title">' +
				__("Status Information") +
				"</div>" +
				'<p class="kt-pd-status-lock"><strong>' +
				_esc(ctx.status_title || __("Locked for Editing")) +
				"</strong></p>" +
				'<p class="kt-pd-muted">' +
				_esc(ctx.severity_label || "") +
				"</p></div>" +
				'<div class="kt-pd-sidebar-card"><div class="kt-pd-sidebar-title">' +
				__("Workflow Actions") +
				"</div>" +
				'<button type="button" class="kt-pd-btn kt-pd-btn--primary" data-action="run_readiness" data-testid="kt-pd-resolve-blockers">' +
				_ico("build") +
				__("Resolve Blockers") +
				"</button>";
			if (ctx.show_funding_actions) {
				html +=
					'<button type="button" class="kt-pd-btn kt-pd-btn--secondary" data-action="request_budget_uplift" data-testid="kt-pd-request-budget-uplift">' +
					__("Request Budget Uplift") +
					"</button>" +
					'<button type="button" class="kt-pd-btn kt-pd-btn--secondary" data-action="view_funding_analysis" data-testid="kt-pd-view-funding-analysis">' +
					__("View Detailed Gap Analysis") +
					"</button>";
			}
			html +=
				'<button type="button" class="kt-pd-btn kt-pd-btn--secondary" data-action="view_block_history" data-testid="kt-pd-view-block-history">' +
				_ico("history") +
				__("View Block History") +
				"</button></div>" +
				'<div class="kt-pd-sidebar-card" data-testid="kt-pd-assigned-contacts">' +
				'<div class="kt-pd-sidebar-title">' +
				__("Assigned Contacts") +
				"</div>" +
				_field(__("Package Owner"), ctx.owner_label) +
				_field(__("Last Reviewer"), ctx.last_reviewer_label) +
				"</div>";
		} else if (status === "In Review") {
			html +=
				'<div class="kt-pd-sidebar-card"><div class="kt-pd-sidebar-title">' +
				__("Reviewer Actions") +
				"</div>" +
				'<button type="button" class="kt-pd-btn kt-pd-btn--primary" data-action="approve" data-testid="kt-pd-approve"' +
				(tab.may_approve ? "" : " disabled") +
				">" +
				_ico("verified") +
				__("Approve Package") +
				"</button>" +
				'<button type="button" class="kt-pd-btn kt-pd-btn--danger" data-action="return" data-testid="kt-pd-return"' +
				(tab.may_return ? "" : " disabled") +
				">" +
				_ico("assignment_return") +
				__("Return for Correction") +
				"</button>" +
				'<button type="button" class="kt-pd-btn kt-pd-btn--secondary" data-action="clarify" data-testid="kt-pd-clarify"' +
				(tab.may_clarify ? "" : " disabled") +
				">" +
				_ico("contact_support") +
				__("Request Clarification") +
				"</button></div>" +
				'<div class="kt-pd-locked-note" data-testid="kt-pd-locked-notice">' +
				_ico("lock") +
				" <strong>" +
				__("Package Locked") +
				"</strong><p style=\"font-size:13px;color:var(--pd-on-muted);margin:8px 0 0\">" +
				__(
					"The planner cannot edit this package while it is undergoing review. Changes will only be possible if returned for correction."
				) +
				"</p></div>";
		} else if (rel.released) {
			html +=
				'<div class="kt-pd-sidebar-card"><div class="kt-pd-sidebar-title">' +
				__("Tender Link") +
				"</div>" +
				(rel.tender_open_route
					? '<a class="kt-pd-btn kt-pd-btn--primary" href="' +
						_esc(rel.tender_open_route) +
						'">' +
						__("Open in Tender Management") +
						"</a>"
					: '<p style="font-size:13px;color:var(--pd-on-muted)">' +
						_esc(rel.subheadline || "") +
						"</p>") +
				"</div>";
		} else {
			html +=
				'<div class="kt-pd-sidebar-card kt-pd-sidebar-card--dark" data-testid="kt-pd-summary-card">' +
				'<div class="kt-pd-sidebar-title">' +
				__("Package Summary") +
				"</div>" +
				'<div class="kt-pd-label">' +
				__("Total Estimated Value") +
				'</div><div class="kt-pd-summary-value">' +
				_esc(sum.total_value_label) +
				"</div>" +
				'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,.12)">' +
				_field(__("Funding Status"), sum.funding_status_label) +
				_field(__("Total Lines"), String(sum.line_count || 0)) +
				"</div></div>" +
				'<div class="kt-pd-sidebar-card"><div class="kt-pd-sidebar-title">' +
				__("Workflow Actions") +
				"</div>";
			if (tab.may_submit) {
				html +=
					'<button type="button" class="kt-pd-btn kt-pd-btn--primary" data-action="submit_for_review" data-testid="kt-pd-submit-review">' +
					__("Submit for Review") +
					"</button>";
			}
			html +=
				'<button type="button" class="kt-pd-btn kt-pd-btn--primary" data-action="run_readiness" data-testid="kt-pd-sidebar-run-readiness">' +
				__("Run Readiness Checks") +
				"</button>";
			if (status === "Draft Package" && d.package_docname) {
				html +=
					'<button type="button" class="kt-pd-btn kt-pd-btn--secondary" data-action="modify_package" data-testid="kt-pd-sidebar-modify">' +
					_ico("edit") +
					__("Modify Package") +
					"</button>";
			}
			html +=
				'<button type="button" class="kt-pd-btn kt-pd-btn--secondary" data-action="back_workbench">' +
				__("Back to Workbench") +
				"</button></div>";
			if (status === "Draft Package") {
				html +=
					'<div class="kt-pd-sidebar-card" data-testid="kt-pd-activity-card">' +
					'<div class="kt-pd-sidebar-title">' +
					__("Recent Activity") +
					"</div>" +
					_activityHtml(activity) +
					"</div>";
			}
		}

		html +=
			'<div class="kt-pd-sidebar-card"><div class="kt-pd-sidebar-title">' +
			__("Evidence & History") +
			"</div>" +
			'<button type="button" class="kt-pd-btn kt-pd-btn--secondary" data-action="view_evidence" data-testid="kt-pd-view-evidence">' +
			_ico("description") +
			__("View Evidence") +
			"</button></div>";

		return html;
	}

	function _shellHtml(d) {
		var h = (d && d.header) || {};
		var pill = d.display_status_pill || h.status_label || "";
		var metaParts = [_esc(d.package_code)];
		if (h.meta_line) metaParts.push(_esc(h.meta_line));
		return (
			'<article class="kt-pd-root" data-testid="kt-pd-detail">' +
			'<div class="kt-pd-canvas" data-testid="kt-pd-canvas">' +
			'<nav class="kt-pd-breadcrumb" data-testid="kt-pd-breadcrumb"><a href="#" data-action="back_workbench">' +
			_ico("arrow_back") +
			__("Back to Workbench") +
			'</a><span>/</span><span>' +
			__("Packages") +
			"</span><span>/</span><span class=\"kt-pd-breadcrumb__current\">" +
			_esc(h.title || d.package_name) +
			"</span></nav>" +
			'<header class="kt-pd-header" data-testid="kt-pd-header">' +
			'<div class="kt-pd-header__block">' +
			'<div class="kt-pd-header__title-row">' +
			"<h1 class=\"kt-pd-title\" data-testid=\"kt-pd-title\">" +
			_esc(h.title || d.package_name) +
			"</h1>" +
			'<span class="kt-pd-pill ' +
			_pillClass(pill) +
			'" data-testid="kt-pd-status-pill">' +
			_esc(pill) +
			"</span></div>" +
			'<p class="kt-pd-meta" data-testid="kt-pd-meta">' +
			metaParts.join(" • ") +
			"</p></div></header>" +
			_tabsHtml(_state.activeTab) +
			'<div class="kt-pd-layout">' +
			'<div class="kt-pd-main" data-testid="kt-pd-tab-host">' +
			_tabHostHtml(d) +
			"</div>" +
			'<aside class="kt-pd-sidebar" data-testid="kt-pd-sidebar">' +
			_sidebarHtml(d) +
			"</aside></div>" +
			_footerHtml() +
			"</div></article>"
		);
	}

	function _runAction(action) {
		var code = _state.packageCode;
		var pkgId = (_state.detail && _state.detail.package_code) || code;
		if (!code) return Promise.resolve();
		if (action === "run_readiness") {
			return _call(RUN_READINESS_API, { package_code: code });
		}
		if (action === "submit_for_review") {
			return _call(SUBMIT_API, { package_id: pkgId });
		}
		if (action === "approve") {
			return _call(APPROVE_API, { package_id: pkgId });
		}
		if (action === "return") {
			var reason = window.prompt(__("Enter return reason"));
			if (!reason || !String(reason).trim()) return Promise.resolve({ cancelled: true });
			var correction = window.prompt(__("Describe required correction"));
			return _call(RETURN_API, {
				package_id: pkgId,
				reason: String(reason).trim(),
				required_correction: String(correction || reason).trim(),
			});
		}
		if (action === "clarify") {
			var msg =
				_state.reviewSummary ||
				window.prompt(__("Enter clarification request for the planner"));
			if (!msg || !String(msg).trim()) return Promise.resolve({ cancelled: true });
			return _call(CLARIFY_API, {
				package_id: pkgId,
				message: String(msg).trim(),
			});
		}
		if (action === "release_to_tender") {
			return _call(RELEASE_API, { package_code: code });
		}
		if (action === "back_workbench") {
			window.location.href = _buildWorkbenchBackUrl(_state.detail);
			return Promise.resolve({ navigated: true });
		}
		if (action === "view_evidence") {
			_openEvidence(code);
			return Promise.resolve();
		}
		if (action === "view_block_history") {
			_openEvidence(code, { title: __("Block History"), filter: "blocker" });
			return Promise.resolve();
		}
		if (action === "request_budget_uplift" || action === "view_funding_analysis") {
			frappe.show_alert({
				indicator: "blue",
				message: __("Budget team has been notified about this funding gap."),
			});
			return Promise.resolve({ stub: true });
		}
		if (action === "modify_package") {
			var docname = (_state.detail && _state.detail.package_docname) || "";
			if (docname) {
				frappe.set_route("Form", "Procurement Package", docname);
			}
			return Promise.resolve({ navigated: true });
		}
		return Promise.resolve();
	}

	function _bind(wrapper) {
		if (wrapper.__ktPdBound) return;
		wrapper.__ktPdBound = true;
		wrapper.addEventListener("click", function (ev) {
			var tabBtn = ev.target.closest("[data-tab]");
			if (tabBtn && wrapper.contains(tabBtn)) {
				ev.preventDefault();
				_state.activeTab = String(tabBtn.getAttribute("data-tab") || "overview");
				_updateTabButtons(wrapper);
				_updateTabHost(wrapper, _state.detail);
				return;
			}
			var actionEl = ev.target.closest("[data-action]");
			if (!actionEl || !wrapper.contains(actionEl)) return;
			var action = String(actionEl.getAttribute("data-action") || "").trim();
			if (action === "back_workbench") {
				ev.preventDefault();
			}
			if (actionEl.disabled) return;
			_runAction(action).then(function (res) {
				if (res && res.navigated) return;
				if (res && res.cancelled) return;
				_load(wrapper);
			});
		});
		wrapper.addEventListener("input", function (ev) {
			var summary = ev.target.closest('[data-testid="kt-pd-review-summary"]');
			if (summary && wrapper.contains(summary)) {
				_state.reviewSummary = summary.value;
			}
		});
	}

	function _load(wrapper) {
		var code = _state.packageCode;
		if (!code) {
			wrapper.innerHTML =
				'<div class="kt-pd-error" data-testid="kt-pd-error">' +
				_esc(__("Package code is missing.")) +
				"</div>";
			return;
		}
		var token = (_state._token += 1);
		wrapper.innerHTML =
			'<div class="kt-pd-loading" data-testid="kt-pd-loading">' +
			_esc(__("Loading package…")) +
			"</div>";
		_call(DETAIL_API, { package: code })
			.then(function (payload) {
				if (token !== _state._token) return;
				if (!payload || !payload.ok) {
					wrapper.innerHTML =
						'<div class="kt-pd-error" data-testid="kt-pd-error">' +
						_esc((payload && payload.message) || __("Package detail is unavailable.")) +
						"</div>";
					return;
				}
				if (!_state.activeTab || _state.activeTab === "overview") {
					_state.activeTab = payload.default_tab || "overview";
				}
				_state.detail = payload;
				wrapper.innerHTML = _shellHtml(payload);
				_bind(wrapper);
			})
			.catch(function () {
				if (token !== _state._token) return;
				wrapper.innerHTML =
					'<div class="kt-pd-error" data-testid="kt-pd-error">' +
					_esc(__("Planning information could not be loaded. Try again.")) +
					"</div>";
			});
	}

	frappe.pages["package-detail"].on_page_load = function (wrapper) {
		_ensureFonts();
		_state._wrapper = wrapper;
	};

	frappe.pages["package-detail"].on_page_show = function (wrapper) {
		_ensureFonts();
		_activatePageChrome();
		_state._wrapper = wrapper;
		_state.packageCode = _resolvePackageCode();
		_state.reviewSummary = "";
		if (!_state.packageCode) {
			wrapper.innerHTML =
				'<div class="kt-pd-error">' + _esc(__("Package code is missing.")) + "</div>";
			return;
		}
		_load(wrapper);
	};

	frappe.pages["package-detail"].on_page_hide = function () {
		_deactivatePageChrome();
	};

	kentender_procurement.openPackageDetailPage = function (packageCode) {
		var code = String(packageCode || "").trim();
		frappe.route_options = { package: code };
		frappe.set_route("package-detail", code);
	};
})();
