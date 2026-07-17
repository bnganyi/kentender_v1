/* ── IT Tender Configurations — Screen 01 (native screen module) ─────────── */
(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.screens.dashboard");

	var api = kentender.it_wizard.api;
	var routes = kentender.it_wizard.routes;
	var components = kentender.it_wizard.components;
	var shell = kentender.it_wizard.shell;

	var SEARCH_DEBOUNCE_MS = 300;
	var PAGE_SIZE_OPTIONS = [10, 25, 50, 100];
	var SCREEN_SHELL = "it-wizard-dashboard-shell";

	var _state = {
		wrapper: null,
		loading: false,
		kpis: { in_configuration: 0, needs_action: 0, ready_for_review: 0, publication_ready: 0 },
		todayDeltas: {},
		filterOptions: { statuses: [], entities: [], methods: [] },
		rows: [],
		total: 0,
		page: 1,
		pageSize: 25,
		filters: {
			q: "",
			state: "",
			procurement_entity_id: "",
			procurement_method_code: "",
			overdue_only: false,
		},
		createContext: null,
		createOpen: false,
		drawerOpen: false,
		searchTimer: null,
	};

	var KPI_CARDS = [
		{
			key: "in_configuration",
			label: "In Configuration",
			tone: "info",
			delta: function (v, d) {
				return d > 0
					? { text: "+" + d + " today", tone: "info" }
					: { text: "Steady", tone: "info" };
			},
		},
		{
			key: "needs_action",
			label: "Needs Action",
			tone: "danger",
			delta: function (v) {
				return v > 0 ? { text: "Critical", tone: "danger" } : { text: "Clear", tone: "success" };
			},
		},
		{
			key: "ready_for_review",
			label: "Ready for Review",
			tone: "success",
			delta: function (v) {
				return v > 0 ? { text: "Queue", tone: "success" } : { text: "Empty", tone: "success" };
			},
		},
		{
			key: "publication_ready",
			label: "Publication Ready",
			tone: "success",
			delta: function () {
				return { text: "Approved", tone: "success" };
			},
		},
	];

	function _esc(s) {
		return components.escape_html(s);
	}

	function _icon(name, cls) {
		return components.icon(name, cls);
	}

	function _badgeTone(state) {
		if (state === "VALIDATION_FAILED") return "danger";
		if (
			state === "READY_FOR_REVIEW" ||
			state === "APPROVED_FOR_TENDER_CREATION" ||
			state === "BOUND_TO_TENDER" ||
			state === "PUBLISHED"
		) {
			return "success";
		}
		if (state === "RETURNED_FOR_CORRECTION") return "warn";
		return "info";
	}

	function _shellHtml() {
		var user = (frappe.session && (frappe.session.user_fullname || frappe.session.user)) || "User";
		return (
			'<div class="kt-itw-root" data-testid="it-wizard-dashboard">' +
			components.appbar({ user: user, title: "IT Tender Configurations" }) +
			'<main class="kt-itw-canvas">' +
			'<div class="kt-itw-page-head">' +
			'<div class="kt-itw-page-head-text">' +
			'<h2 class="kt-itw-page-title">IT Tender Configurations</h2>' +
			'<p class="kt-itw-page-sub">Create or continue IT tender configurations from approved procurement packages.</p>' +
			"</div>" +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-open-create-modal="1">' +
			_icon("add") +
			"Create IT Tender Configuration" +
			"</button>" +
			"</div>" +
			'<section class="kt-itw-kpi-grid" data-itw-kpi-grid="1"></section>' +
			'<section class="kt-itw-toolbar" data-itw-filter-bar="1">' +
			'<div class="kt-itw-search-wrap">' +
			_icon("search") +
			'<input type="text" class="kt-itw-search" data-itw-search="1" placeholder="Search Tender Ref / Title..." aria-label="Search tender configurations" />' +
			"</div>" +
			'<div class="kt-itw-toolbar-actions">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--outline" data-itw-open-filter-drawer="1">' +
			_icon("filter_list", "kt-itw-ico--sm") +
			"Filters" +
			"</button>" +
			'<div class="kt-itw-toolbar-divider"></div>' +
			'<div class="kt-itw-chips" data-itw-filter-chips="1"></div>' +
			"</div></section>" +
			'<section class="kt-itw-table-card" data-itw-table-surface="1">' +
			'<div class="kt-itw-table-scroll" data-itw-table-scroll-host="1">' +
			'<table class="kt-itw-table"><thead><tr>' +
			"<th>Tender</th><th>Procuring Entity</th><th>Procurement Method</th><th>Wizard State</th>" +
			"<th>Progress</th><th>Issues</th><th>Next Action</th><th class=\"kt-itw-right\">Updated</th>" +
			"</tr></thead><tbody data-itw-tbody=\"1\"></tbody></table></div>" +
			'<div class="kt-itw-table-footer" data-itw-table-footer="1"></div></section></main>' +
			components.footer() +
			"</div>" +
			_createModalHtml() +
			_drawerHtml()
		);
	}

	function _createModalHtml() {
		return (
			'<div class="kt-itw-modal" id="create-modal" data-itw-create-modal="1" hidden>' +
			'<div class="kt-itw-modal-backdrop" data-itw-create-close="1"></div>' +
			'<div class="kt-itw-modal-card" role="dialog" aria-modal="true" aria-label="Create IT Tender Configuration">' +
			'<div class="kt-itw-modal-head"><h3 class="kt-itw-modal-title">Create IT Tender Configuration</h3>' +
			'<button type="button" class="kt-itw-icon-btn kt-itw-icon-btn--round" data-itw-create-close="1" aria-label="Close">' +
			_icon("close") + "</button></div>" +
			'<div class="kt-itw-modal-body">' +
			'<p class="kt-itw-modal-helper" data-itw-create-helper="1">Select the approved procurement package that requires an IT tender configuration. The planning reference, procuring entity, procurement method, and applicable standard tender document will be filled from the package.</p>' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Approved Procurement Package</label>' +
			'<select class="kt-itw-select" data-itw-create-package="1"><option value="">Select an approved procurement package...</option></select></div>' +
			'<div class="kt-itw-field-grid">' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Planning Package Ref</label><input type="text" class="kt-itw-input kt-itw-input--readonly kt-itw-mono" data-itw-create-planning="1" readonly /></div>' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Procuring Entity</label><input type="text" class="kt-itw-input kt-itw-input--readonly" data-itw-create-entity="1" readonly /></div></div>' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Procurement Method</label><input type="text" class="kt-itw-input kt-itw-input--readonly" data-itw-create-method="1" readonly /></div>' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Standard Tender Document</label><select class="kt-itw-select" data-itw-create-std="1" disabled></select></div>' +
			'<div class="kt-itw-modal-foot">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--ghost" data-itw-create-close="1">Cancel</button>' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-create-submit="1">Create Configuration</button></div></div></div></div>'
		);
	}

	function _drawerHtml() {
		return (
			'<div class="kt-itw-drawer" data-itw-filter-drawer="1" hidden>' +
			'<div class="kt-itw-drawer-backdrop" data-itw-drawer-action="close"></div>' +
			'<div class="kt-itw-drawer-panel" role="dialog" aria-modal="true" aria-label="Advanced Filters">' +
			'<div class="kt-itw-drawer-head"><h3 class="kt-itw-modal-title">Advanced Filters</h3>' +
			'<button type="button" class="kt-itw-icon-btn kt-itw-icon-btn--round" data-itw-drawer-action="close" aria-label="Close">' +
			_icon("close") + "</button></div>" +
			'<div class="kt-itw-drawer-body">' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Status</label><select class="kt-itw-select" data-itw-drawer-filter="state"></select></div>' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Procurement Method</label><select class="kt-itw-select" data-itw-drawer-filter="method"></select></div>' +
			'<div class="kt-itw-field"><label class="kt-itw-label">Procuring Entity</label><select class="kt-itw-select" data-itw-drawer-filter="entity"></select></div>' +
			'<label class="kt-itw-check"><input type="checkbox" data-itw-drawer-filter="overdue" /><span>Due this week</span></label></div>' +
			'<div class="kt-itw-drawer-foot">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--outline" data-itw-drawer-action="clear">Clear All</button>' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-drawer-action="apply">Apply Filters</button></div></div></div>'
		);
	}

	function _q(sel) {
		return _state.wrapper ? _state.wrapper.querySelector(sel) : null;
	}

	function _paintKpis() {
		var host = _q("[data-itw-kpi-grid]");
		if (!host) return;
		var values = KPI_CARDS.map(function (c) {
			return _state.kpis[c.key] || 0;
		});
		var maxValue = Math.max.apply(null, values.concat([1]));
		host.innerHTML = KPI_CARDS.map(function (card) {
			var value = _state.kpis[card.key] || 0;
			var delta = parseInt(_state.todayDeltas[card.key], 10) || 0;
			var q = card.delta(value, delta) || { text: "", tone: card.tone };
			var pct = value > 0 ? Math.max(8, Math.round((value / maxValue) * 100)) : 0;
			return (
				'<div class="kt-itw-kpi-card kt-itw-kpi-card--' + card.tone + '" data-itw-kpi="' + card.key + '">' +
				'<p class="kt-itw-kpi-label">' + _esc(card.label) + "</p>" +
				'<div class="kt-itw-kpi-value-row"><span class="kt-itw-kpi-value">' + value + "</span>" +
				'<span class="kt-itw-kpi-delta kt-itw-kpi-delta--' + q.tone + '">' + _esc(q.text) + "</span></div>" +
				'<div class="kt-itw-kpi-bar"><div class="kt-itw-kpi-bar-fill" style="width:' + pct + '%"></div></div></div>'
			);
		}).join("");
	}

	function _optionList(placeholder, rows, valueKey, labelKey, selected) {
		var html = '<option value="">' + _esc(placeholder) + "</option>";
		(rows || []).forEach(function (row) {
			var value = row[valueKey] || "";
			var label = row[labelKey] || value;
			if (!value) return;
			html += '<option value="' + _esc(value) + '"' + (value === selected ? " selected" : "") + ">" + _esc(label) + "</option>";
		});
		return html;
	}

	function _paintFilterSelects() {
		var opts = _state.filterOptions || {};
		var stateSel = _q('[data-itw-drawer-filter="state"]');
		if (stateSel) stateSel.innerHTML = _optionList("All statuses", opts.statuses || [], "value", "label", _state.filters.state);
		var methodSel = _q('[data-itw-drawer-filter="method"]');
		if (methodSel) methodSel.innerHTML = _optionList("All methods", opts.methods || [], "id", "name", _state.filters.procurement_method_code);
		var entitySel = _q('[data-itw-drawer-filter="entity"]');
		if (entitySel) entitySel.innerHTML = _optionList("All entities", opts.entities || [], "id", "name", _state.filters.procurement_entity_id);
		var overdue = _q('[data-itw-drawer-filter="overdue"]');
		if (overdue) overdue.checked = !!_state.filters.overdue_only;
	}

	function _stateLabel(code) {
		var match = (_state.filterOptions.statuses || []).filter(function (s) {
			return s.value === code;
		})[0];
		return match ? match.label : code;
	}
	function _methodLabel(code) {
		var match = (_state.filterOptions.methods || []).filter(function (m) {
			return m.id === code;
		})[0];
		return match ? match.name : code;
	}
	function _entityLabel(id) {
		var match = (_state.filterOptions.entities || []).filter(function (e) {
			return e.id === id;
		})[0];
		return match ? match.name : id;
	}

	function _paintChips() {
		var host = _q("[data-itw-filter-chips]");
		if (!host) return;
		var f = _state.filters;
		var chips = [{ key: "state", label: "Status: " + (f.state ? _stateLabel(f.state) : "All"), active: true }];
		if (f.procurement_method_code) chips.push({ key: "method", label: "Method: " + _methodLabel(f.procurement_method_code) });
		if (f.procurement_entity_id) chips.push({ key: "entity", label: "Entity: " + _entityLabel(f.procurement_entity_id) });
		if (f.overdue_only) chips.push({ key: "overdue", label: "Due this week" });
		host.innerHTML = chips
			.map(function (chip) {
				return (
					'<span class="kt-itw-chip' + (chip.active ? " kt-itw-chip--active" : "") + '" data-itw-filter-chip="' + _esc(chip.key) + '">' +
					_esc(chip.label) +
					'<button type="button" class="kt-itw-chip-remove" data-itw-chip-remove="' + _esc(chip.key) + '" aria-label="Remove filter">' +
					_icon("close") + "</button></span>"
				);
			})
			.join("");
	}

	function _issuesCell(blockers, warnings) {
		if (blockers > 0) return '<span class="kt-itw-issue kt-itw-issue--danger">' + blockers + " Blockers</span>";
		if (warnings > 0) return '<span class="kt-itw-issue kt-itw-issue--warn">' + warnings + " Warnings</span>";
		return '<span class="kt-itw-issue kt-itw-issue--ok">Passed</span>';
	}

	function _rowHtml(item) {
		var step = item.current_step || {};
		var blockers = item.blocker_count != null ? item.blocker_count : 0;
		var warnings = item.warning_count != null ? item.warning_count : 0;
		var action = item.next_action || "continue_setup";
		var actionLabel = item.next_action_label || "Continue Setup";
		var actionCls = action === "fix_blockers" || action === "open_preview" ? "kt-itw-btn--outline" : "kt-itw-btn--primary";
		var planningRef = item.planning_package_ref || "";
		var progress = item.progress_percent != null ? item.progress_percent : item.completion_percent || 0;
		return (
			'<tr data-configuration-id="' + _esc(item.code || item.configuration_id || "") + '" data-itw-next-action="' + _esc(action) + '">' +
			"<td><div class=\"kt-itw-cell-ref kt-itw-mono\">" + _esc(item.tender_ref || item.code || "") + "</div>" +
			'<div class="kt-itw-cell-title">' + _esc(item.tender_title || item.name || "") + "</div>" +
			(planningRef ? '<div class="kt-itw-cell-meta">' + _esc(planningRef) + "</div>" : "") + "</td>" +
			'<td class="kt-itw-muted">' + _esc(item.procuring_entity_name || "—") + "</td>" +
			'<td class="kt-itw-muted">' + _esc(item.procurement_method_label || "—") + "</td>" +
			'<td><span class="kt-itw-badge kt-itw-badge--' + _badgeTone(item.state || item.wizard_state) + '">' +
			_esc(item.state_label || item.wizard_state_label || "") + "</span></td>" +
			"<td><div class=\"kt-itw-mono kt-itw-progress-num\">" + progress + "%</div>" +
			'<div class="kt-itw-cell-meta">Step: ' + _esc(step.name || step.code || "—") + "</div></td>" +
			"<td>" + _issuesCell(blockers, warnings) + "</td>" +
			'<td><button type="button" class="kt-itw-btn kt-itw-btn--sm ' + actionCls + '" data-itw-action="continue">' + _esc(actionLabel) + "</button></td>" +
			'<td class="kt-itw-right kt-itw-mono kt-itw-muted">' + _esc(item.last_updated_at || item.last_updated || "—") + "</td></tr>"
		);
	}

	function _paintTable() {
		var tbody = _q("[data-itw-tbody]");
		if (!tbody) return;
		if (!_state.rows.length) {
			tbody.innerHTML = '<tr><td colspan="8" class="kt-itw-empty" data-itw-empty="1">' +
				(_state.loading ? "Loading tender configurations…" : "No tender configurations found.") + "</td></tr>";
			return;
		}
		tbody.innerHTML = _state.rows.map(_rowHtml).join("");
	}

	function _pageWindow(page, totalPages) {
		var maxButtons = 6;
		if (totalPages <= maxButtons) {
			var all = [];
			for (var i = 1; i <= totalPages; i++) all.push(i);
			return all;
		}
		var half = Math.floor(maxButtons / 2);
		var start = Math.max(1, page - half);
		var end = start + maxButtons - 1;
		if (end > totalPages) {
			end = totalPages;
			start = end - maxButtons + 1;
		}
		var win = [];
		for (var j = start; j <= end; j++) win.push(j);
		return win;
	}

	function _paintPager() {
		var footer = _q("[data-itw-table-footer]");
		if (!footer) return;
		var total = _state.total || 0;
		var pageSize = _state.pageSize || 25;
		var page = _state.page || 1;
		var totalPages = total > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1;
		var start = total > 0 ? (page - 1) * pageSize + 1 : 0;
		var end = total > 0 ? Math.min(page * pageSize, total) : 0;
		var rowsOpts = PAGE_SIZE_OPTIONS.map(function (n) {
			return '<option value="' + n + '"' + (n === pageSize ? " selected" : "") + ">" + n + "</option>";
		}).join("");
		var pages = _pageWindow(page, totalPages)
			.map(function (n) {
				return '<button type="button" class="kt-itw-pager-page' + (n === page ? " kt-itw-pager-page--active" : "") +
					'" data-itw-pager-page="' + n + '">' + n + "</button>";
			})
			.join("");
		footer.innerHTML =
			'<span class="kt-itw-pager-showing">Showing <b>' + start + "-" + end + "</b> of <b>" + total + "</b></span>" +
			'<div class="kt-itw-pager-right"><div class="kt-itw-pager-rows"><span class="kt-itw-pager-rows-label">Rows:</span>' +
			'<div class="kt-itw-select-wrap"><select class="kt-itw-rows-select" data-itw-rows-select="1">' + rowsOpts + "</select>" +
			_icon("expand_more") + "</div></div><div class=\"kt-itw-pager-nav\">" +
			'<button type="button" class="kt-itw-pager-btn" data-itw-pager="prev"' + (page <= 1 ? " disabled" : "") + ">" + _icon("chevron_left", "kt-itw-ico--sm") + "</button>" +
			pages +
			'<button type="button" class="kt-itw-pager-btn" data-itw-pager="next"' + (page >= totalPages ? " disabled" : "") + ">" + _icon("chevron_right", "kt-itw-ico--sm") + "</button></div></div>";
	}

	function _listArgs() {
		var f = _state.filters;
		return {
			page: _state.page || 1,
			page_size: _state.pageSize || 25,
			q: f.q || undefined,
			state: f.state || undefined,
			procurement_entity_id: f.procurement_entity_id || undefined,
			procurement_method_code: f.procurement_method_code || undefined,
			overdue_only: f.overdue_only ? 1 : undefined,
		};
	}

	function _applyList(list) {
		_state.rows = list.items || [];
		_state.total = list.total || 0;
		_state.page = list.page || 1;
		_state.pageSize = list.page_size || _state.pageSize || 25;
	}

	function _showError(err, fallback) {
		frappe.show_alert({ indicator: "red", message: (err && err.message) || fallback });
	}

	function _fetchAll() {
		_state.loading = true;
		_paintTable();
		return Promise.all([
			api.call("get_dashboard_summary", {}),
			api.call("list_configurations_api", _listArgs()),
		])
			.then(function (results) {
				var summary = (results[0] && results[0].message && results[0].message.data) || {};
				var list = (results[1] && results[1].message && results[1].message.data) || {};
				_state.kpis = summary.kpis || _state.kpis;
				_state.todayDeltas = summary.today_deltas || {};
				_state.filterOptions = summary.filter_options || _state.filterOptions;
				_applyList(list);
				_state.loading = false;
				_paintKpis();
				_paintFilterSelects();
				_paintChips();
				_paintTable();
				_paintPager();
			})
			.catch(function (err) {
				_state.loading = false;
				_paintTable();
				_showError(err, "Unable to load dashboard data.");
			});
	}

	function _fetchList() {
		_state.loading = true;
		_paintTable();
		return api.call("list_configurations_api", _listArgs())
			.then(function (r) {
				_applyList((r && r.message && r.message.data) || {});
				_state.loading = false;
				_paintChips();
				_paintTable();
				_paintPager();
			})
			.catch(function (err) {
				_state.loading = false;
				_paintTable();
				_showError(err, "Unable to load tender configurations.");
			});
	}

	function _openCreateModal(ctx) {
		ctx = ctx || {};
		var modal = _q("[data-itw-create-modal]");
		if (!modal) return;
		modal.hidden = false;
		modal.classList.add("kt-itw-modal--open");
		_state.createOpen = true;
		api.call("get_create_configuration_context_api", {
			procurement_package_id: ctx.procurement_package_id || undefined,
			tender_id: ctx.tender_id || undefined,
			std_version_id: ctx.std_version_id || undefined,
			plan_item_id: ctx.plan_item_id || undefined,
		})
			.then(function (r) {
				var data = (r && r.message && r.message.data) || {};
				_state.createContext = data;
				_applyCreateContext(data, ctx);
			})
			.catch(function (err) {
				_showError(err, "Unable to load create options.");
			});
	}

	function _closeCreateModal() {
		var modal = _q("[data-itw-create-modal]");
		if (!modal) return;
		modal.hidden = true;
		modal.classList.remove("kt-itw-modal--open");
		_state.createOpen = false;
	}

	function _applyCreateContext(data, ctx) {
		var options = data.create_options || [];
		var select = _q("[data-itw-create-package]");
		if (!select) return;
		var html = '<option value="">Select an approved procurement package...</option>';
		options.forEach(function (opt) {
			html +=
				'<option value="' + _esc(opt.procurement_package_id || "") + '" data-planning="' + _esc(opt.planning_package_ref || "") +
				'" data-planning-name="' + _esc(opt.planning_package_name || "") + '" data-entity-id="' + _esc(opt.procuring_entity_id || "") +
				'" data-entity-name="' + _esc(opt.procuring_entity_name || "") + '" data-method-code="' + _esc(opt.procurement_method_code || "") +
				'" data-method-label="' + _esc(opt.procurement_method_label || "") + '" data-std-id="' + _esc(opt.standard_tender_document_id || "") +
				'" data-std-label="' + _esc(opt.standard_tender_document_label || "") + '" data-std-selectable="' +
				(opt.standard_tender_document_selectable ? "1" : "0") + '" data-std-options="' +
				_esc(JSON.stringify(opt.standard_tender_document_options || [])) + '">' + _esc(opt.procurement_package_label || "") + "</option>";
		});
		select.innerHTML = html;
		var preselect = data.preselect_procurement_package_id || (ctx && ctx.procurement_package_id) || (ctx && ctx.tender_id) || "";
		if (preselect) {
			select.value = preselect;
			if (select.value !== preselect && options.length) select.selectedIndex = 1;
		}
		var modal = _q("[data-itw-create-modal]");
		if (modal) modal.setAttribute("data-itw-create-plan-item", data.plan_item_id || (ctx && ctx.plan_item_id) || "");
		_applyPackageSelection();
	}

	function _applyPackageSelection() {
		var select = _q("[data-itw-create-package]");
		if (!select) return;
		var opt = select.options[select.selectedIndex];
		var picked = !!(opt && opt.value);
		var planning = _q("[data-itw-create-planning]");
		var entity = _q("[data-itw-create-entity]");
		var method = _q("[data-itw-create-method]");
		var stdSelect = _q("[data-itw-create-std]");
		if (planning) planning.value = picked ? opt.getAttribute("data-planning") || "" : "";
		if (entity) entity.value = picked ? opt.getAttribute("data-entity-name") || "" : "";
		if (method) method.value = picked ? opt.getAttribute("data-method-label") || "" : "";
		if (!stdSelect) return;
		var modal = _q("[data-itw-create-modal]");
		if (!picked) {
			stdSelect.innerHTML = '<option value=""></option>';
			stdSelect.disabled = true;
			if (modal) modal.setAttribute("data-itw-create-std-id", "");
			return;
		}
		var stdOptions = [];
		try {
			stdOptions = JSON.parse(opt.getAttribute("data-std-options") || "[]");
		} catch (e) {
			stdOptions = [];
		}
		var selectable = opt.getAttribute("data-std-selectable") === "1";
		var stdHtml = stdOptions.map(function (row) {
			return '<option value="' + _esc(row.id || "") + '">' + _esc(row.label || row.id || "") + "</option>";
		}).join("");
		if (!stdHtml) {
			stdHtml = '<option value="' + _esc(opt.getAttribute("data-std-id") || "") + '">' + _esc(opt.getAttribute("data-std-label") || "") + "</option>";
		}
		stdSelect.innerHTML = stdHtml;
		stdSelect.disabled = !selectable;
		if (modal) modal.setAttribute("data-itw-create-std-id", stdSelect.value || opt.getAttribute("data-std-id") || "");
	}

	function _submitCreate() {
		var select = _q("[data-itw-create-package]");
		var opt = select ? select.options[select.selectedIndex] : null;
		if (!opt || !opt.value) {
			frappe.show_alert({ indicator: "orange", message: "Select an approved procurement package to create a configuration." });
			return;
		}
		var stdSelect = _q("[data-itw-create-std]");
		var modal = _q("[data-itw-create-modal]");
		var stdId = (stdSelect && stdSelect.value) || (modal && modal.getAttribute("data-itw-create-std-id")) || "";
		if (!stdId) {
			frappe.show_alert({ indicator: "red", message: "Standard Tender Document is required." });
			return;
		}
		var title = (opt.getAttribute("data-planning-name") || opt.textContent || "").trim() || "IT Tender Configuration";
		var submitBtn = _q("[data-itw-create-submit]");
		if (submitBtn) submitBtn.disabled = true;
		frappe.call({
			method: api.API + ".create_configuration_api",
			args: {
				title: title,
				std_template_version_id: stdId,
				procurement_package_id: opt.value,
				procuring_entity_id: opt.getAttribute("data-entity-id") || undefined,
				procuring_entity_name: opt.getAttribute("data-entity-name") || undefined,
				procurement_method_code: opt.getAttribute("data-method-code") || undefined,
				procurement_method_name: opt.getAttribute("data-method-label") || undefined,
				planning_package_code: opt.getAttribute("data-planning") || undefined,
				planning_package_name: opt.getAttribute("data-planning-name") || undefined,
				procurement_plan_item_id: (modal && modal.getAttribute("data-itw-create-plan-item")) || undefined,
			},
			callback: function (r) {
				if (submitBtn) submitBtn.disabled = false;
				if (r.exc) return;
				var payload = (r.message && r.message.data) || r.message || {};
				var configurationId = (payload.summary && payload.summary.configuration_id) || "";
				_closeCreateModal();
				frappe.show_alert({ indicator: "green", message: "Configuration created" });
				if (configurationId) routes.navigate(routes.ROUTES.OVERVIEW, { configuration_id: configurationId });
			},
			error: function () {
				if (submitBtn) submitBtn.disabled = false;
			},
		});
	}

	function _openDrawer() {
		var drawer = _q("[data-itw-filter-drawer]");
		if (!drawer) return;
		_paintFilterSelects();
		drawer.hidden = false;
		drawer.classList.add("kt-itw-drawer--open");
		_state.drawerOpen = true;
	}
	function _closeDrawer() {
		var drawer = _q("[data-itw-filter-drawer]");
		if (!drawer) return;
		drawer.hidden = true;
		drawer.classList.remove("kt-itw-drawer--open");
		_state.drawerOpen = false;
	}
	function _applyDrawer() {
		var stateSel = _q('[data-itw-drawer-filter="state"]');
		var methodSel = _q('[data-itw-drawer-filter="method"]');
		var entitySel = _q('[data-itw-drawer-filter="entity"]');
		var overdue = _q('[data-itw-drawer-filter="overdue"]');
		_state.filters.state = stateSel ? stateSel.value : "";
		_state.filters.procurement_method_code = methodSel ? methodSel.value : "";
		_state.filters.procurement_entity_id = entitySel ? entitySel.value : "";
		_state.filters.overdue_only = overdue ? overdue.checked : false;
		_state.page = 1;
		_closeDrawer();
		_fetchList();
	}
	function _clearFilters() {
		_state.filters.state = "";
		_state.filters.procurement_method_code = "";
		_state.filters.procurement_entity_id = "";
		_state.filters.overdue_only = false;
		_state.page = 1;
		_paintFilterSelects();
		_closeDrawer();
		_fetchList();
	}

	function _removeChip(key) {
		if (key === "state") _state.filters.state = "";
		else if (key === "method") _state.filters.procurement_method_code = "";
		else if (key === "entity") _state.filters.procurement_entity_id = "";
		else if (key === "overdue") _state.filters.overdue_only = false;
		_state.page = 1;
		_paintFilterSelects();
		_fetchList();
	}

	function _changePage(direction) {
		var totalPages = Math.max(1, Math.ceil((_state.total || 0) / (_state.pageSize || 25)));
		if (direction === "prev" && _state.page > 1) _state.page -= 1;
		else if (direction === "next" && _state.page < totalPages) _state.page += 1;
		else return;
		_fetchList();
	}

	function _gotoPage(n) {
		var totalPages = Math.max(1, Math.ceil((_state.total || 0) / (_state.pageSize || 25)));
		if (!n || n < 1 || n > totalPages || n === _state.page) return;
		_state.page = n;
		_fetchList();
	}

	function _rowNavigate(row) {
		if (!row) return;
		var configurationId = row.getAttribute("data-configuration-id");
		if (!configurationId) return;
		var action = row.getAttribute("data-itw-next-action") || "continue_setup";
		if (action === "fix_blockers") routes.navigate(routes.ROUTES.VALIDATION, { configuration_id: configurationId });
		else if (action === "open_preview") routes.navigate(routes.ROUTES.PREVIEW, { configuration_id: configurationId });
		else routes.navigate(routes.ROUTES.OVERVIEW, { configuration_id: configurationId });
	}

	function _maybeOpenPathA() {
		var ctx = routes.read_route_context();
		if (ctx.procurement_package_id || ctx.tender_id) {
			routes.consume_route_keys(["procurement_package_id", "tender_id", "std_version_id", "plan_item_id"]);
			_openCreateModal(ctx);
		}
	}

	function _resetState() {
		_state.rows = [];
		_state.total = 0;
		_state.page = 1;
		_state.pageSize = 25;
		_state.filters = { q: "", state: "", procurement_entity_id: "", procurement_method_code: "", overdue_only: false };
		_state.createContext = null;
		_state.createOpen = false;
		_state.drawerOpen = false;
		clearTimeout(_state.searchTimer);
	}

	function _bind(wrapper) {
		var search = wrapper.querySelector("[data-itw-search]");
		if (search) {
			search.addEventListener("input", function () {
				clearTimeout(_state.searchTimer);
				_state.searchTimer = setTimeout(function () {
					_state.filters.q = (search.value || "").trim();
					_state.page = 1;
					_fetchList();
				}, SEARCH_DEBOUNCE_MS);
			});
		}
		var pkg = wrapper.querySelector("[data-itw-create-package]");
		if (pkg) pkg.addEventListener("change", _applyPackageSelection);
		var std = wrapper.querySelector("[data-itw-create-std]");
		if (std) {
			std.addEventListener("change", function () {
				var modal = _q("[data-itw-create-modal]");
				if (modal) modal.setAttribute("data-itw-create-std-id", std.value || "");
			});
		}
		wrapper.addEventListener("change", function (event) {
			if (event.target.closest("[data-itw-rows-select]")) {
				var next = parseInt(event.target.value, 10) || 25;
				if (next !== _state.pageSize) {
					_state.pageSize = next;
					_state.page = 1;
					_fetchList();
				}
			}
		});
		wrapper.addEventListener("keydown", function (event) {
			if (event.key === "Escape") {
				_closeCreateModal();
				_closeDrawer();
			}
		});
		wrapper.addEventListener("click", function (event) {
			var target = event.target;
			if (target.closest("[data-itw-back]")) {
				event.preventDefault();
				routes.go_back_to_desk();
				return;
			}
			if (target.closest("[data-itw-open-create-modal]")) {
				event.preventDefault();
				_openCreateModal({});
				return;
			}
			if (target.closest("[data-itw-create-close]")) {
				event.preventDefault();
				_closeCreateModal();
				return;
			}
			if (target.closest("[data-itw-create-submit]")) {
				event.preventDefault();
				_submitCreate();
				return;
			}
			if (target.closest("[data-itw-open-filter-drawer]")) {
				event.preventDefault();
				_openDrawer();
				return;
			}
			var drawerAction = target.closest("[data-itw-drawer-action]");
			if (drawerAction) {
				event.preventDefault();
				var action = drawerAction.getAttribute("data-itw-drawer-action");
				if (action === "close") _closeDrawer();
				else if (action === "apply") _applyDrawer();
				else if (action === "clear") _clearFilters();
				return;
			}
			if (target.closest("[data-itw-chip-remove]")) {
				event.preventDefault();
				_removeChip(target.closest("[data-itw-chip-remove]").getAttribute("data-itw-chip-remove"));
				return;
			}
			if (target.closest("[data-itw-pager-page]")) {
				event.preventDefault();
				_gotoPage(parseInt(target.closest("[data-itw-pager-page]").getAttribute("data-itw-pager-page"), 10));
				return;
			}
			var pager = target.closest("[data-itw-pager]");
			if (pager && !pager.disabled) {
				event.preventDefault();
				_changePage(pager.getAttribute("data-itw-pager"));
				return;
			}
			var rowAction = target.closest("[data-itw-action='continue']");
			if (rowAction) {
				event.preventDefault();
				_rowNavigate(rowAction.closest("tr[data-configuration-id]"));
			}
		});
	}

	function render(wrapper) {
		_state.wrapper = wrapper;
		shell.mount_wrapper(wrapper, _shellHtml());
		_bind(wrapper);
		_paintKpis();
		_paintChips();
		_paintTable();
		_paintPager();
	}

	function show(wrapper) {
		shell.show({ screen_shell_class: SCREEN_SHELL });
		_resetState();
		render(wrapper);
		return _fetchAll().then(function () {
			_maybeOpenPathA();
		});
	}

	kentender.it_wizard.screens.dashboard = {
		init: function (wrapper) {
			_state.wrapper = wrapper;
			shell.show({ screen_shell_class: SCREEN_SHELL });
		},
		show: show,
	};
})();
