/* global frappe */
// STD-CFG-0100 — STD Library Desk page (literal port of 1.lib/code.html).
frappe.provide("kentender_procurement.std_library_page");

(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;
	const SUMMARY_API =
		"kentender_procurement.tender_management.api.std_library_summary.get_std_library_summary_counts";
	const TEMPLATES_API =
		"kentender_procurement.tender_management.api.std_library_templates.get_std_library_templates";

	const KPI_CARDS = Object.freeze([
		{
			key: "total",
			countKey: "total_count",
			label: __("Total STDs"),
			testid: "kt-std-lib-kpi-total",
		},
		{
			key: "active",
			countKey: "active_count",
			label: __("Active Versions"),
			testid: "kt-std-lib-kpi-active",
		},
		{
			key: "pending",
			countKey: "pending_approval_count",
			label: __("Pending Approval"),
			testid: "kt-std-lib-kpi-pending",
			warn: true,
		},
		{
			key: "review",
			countKey: "ready_for_review_count",
			label: __("Due for Review"),
			testid: "kt-std-lib-kpi-review",
			warn: true,
		},
	]);

	const HEALTH_ITEMS = Object.freeze([
		{
			key: "unauthorized_active_setup_count",
			label: __("unauthorized STD versions in active tender setup"),
			icon: "check_circle",
			iconClass: "kt-std-lib-health__icon--ok",
			metricClass: "kt-std-lib-health__metric--ok",
		},
		{
			key: "pending_approval_count",
			label: __("versions pending approval"),
			icon: "pending",
			iconClass: "kt-std-lib-health__icon--warn",
			metricClass: "kt-std-lib-health__metric--warn",
		},
		{
			key: "due_for_review_count",
			label: __("versions due for review"),
			icon: "event_busy",
			iconClass: "kt-std-lib-health__icon--exhausted",
			metricClass: "",
		},
		{
			key: "retired_referenced_count",
			label: __("retired/superseded versions referenced by historical tenders"),
			icon: "history",
			iconClass: "kt-std-lib-health__icon--muted",
			metricClass: "",
		},
	]);

	let _searchTimer = null;
	let _listToken = 0;
	let _filters = {
		procurement_category: "",
		procurement_method: "",
		status: "",
	};
	let _pageSize = 10;
	let _pageIndex = 0;
	let _lastItems = [];

	function _categoryIcon(category) {
		return shared._categoryIcon(category);
	}

	function _statusPill(status) {
		return shared._statusPillHtml(status);
	}

	function _routeSegment() {
		const route = frappe.get_route() || [];
		return String(route[1] || "")
			.toLowerCase()
			.trim();
	}

	function _isImportRoute() {
		return _routeSegment() === "import";
	}

	function _userDisplayName() {
		return (
			(frappe.boot && frappe.boot.user && frappe.boot.user.full_name) ||
			frappe.session.user_fullname ||
			frappe.session.user ||
			__("Administrator")
		);
	}

	function _userInitials(name) {
		const parts = String(name || "")
			.trim()
			.split(/\s+/)
			.filter(Boolean);
		if (!parts.length) return "AD";
		if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	function _topbarHtml() {
		const displayName = shared._escapeHtml(_userDisplayName());
		const initials = shared._escapeHtml(_userInitials(_userDisplayName()));
		return `
<header class="kt-std-lib-topbar" data-testid="kt-std-lib-topbar">
	<div class="kt-std-lib-topbar__left">
		<h2 class="kt-std-lib-topbar__title" data-testid="kt-std-lib-topbar-title">${__("STD Library")}</h2>
	</div>
	<div class="kt-std-lib-topbar__right">
		<div class="kt-std-lib-topbar__icons">
			<button type="button" class="kt-std-lib-topbar__icon-btn" data-testid="kt-std-lib-topbar-notifications" aria-label="${__(
				"Notifications",
			)}">
				<span class="material-symbols-outlined kt-std-icon">notifications</span>
			</button>
			<button type="button" class="kt-std-lib-topbar__icon-btn" data-testid="kt-std-lib-topbar-history" aria-label="${__(
				"History",
			)}">
				<span class="material-symbols-outlined kt-std-icon">history</span>
			</button>
			<button type="button" class="kt-std-lib-topbar__icon-btn" data-testid="kt-std-lib-topbar-help" aria-label="${__(
				"Help",
			)}">
				<span class="material-symbols-outlined kt-std-icon">help_outline</span>
			</button>
		</div>
		<div class="kt-std-lib-topbar__divider" aria-hidden="true"></div>
		<div class="kt-std-lib-topbar__user" data-testid="kt-std-lib-topbar-user">
			<div class="kt-std-lib-topbar__user-text">
				<p class="kt-std-lib-topbar__user-name">${displayName}</p>
				<p class="kt-std-lib-topbar__user-role">${__("PROCUREMENT ADMIN")}</p>
			</div>
			<div class="kt-std-lib-topbar__avatar">${initials}</div>
		</div>
	</div>
</header>`;
	}

	function _kpiHtml() {
		return KPI_CARDS.map(function (card) {
			const warnClass = card.warn ? " kt-std-lib-kpi-value--warn" : "";
			return `
				<div class="kt-std-lib-kpi-card" data-testid="${card.testid}">
					<h3 class="kt-std-lib-kpi-label">${card.label}</h3>
					<p class="kt-std-lib-kpi-value${warnClass}" data-kt-std-kpi="${card.key}">—</p>
				</div>`;
		}).join("");
	}

	function _healthHtml() {
		const items = HEALTH_ITEMS.map(function (item) {
			return `
<li class="kt-std-lib-health__item" data-testid="kt-std-lib-health-${item.key}">
	<span class="material-symbols-outlined kt-std-icon ${item.iconClass}">${item.icon}</span>
	<span class="kt-std-lib-health__copy"><strong class="kt-std-lib-health__metric ${item.metricClass}" data-kt-std-health="${item.key}">—</strong> ${item.label}</span>
</li>`;
		}).join("");
		return `
<section class="kt-std-lib-health" data-testid="kt-std-lib-health-panel">
	<h2 class="kt-std-lib-health__title">
		<span class="material-symbols-outlined kt-std-icon">verified</span>
		${__("STD Library Health")}
	</h2>
	<ul class="kt-std-lib-health__list">${items}</ul>
</section>`;
	}

	function _advancedDisclosureHtml() {
		if (!shared.canUseStdAdvancedCatalogue()) {
			return "";
		}
		return `
<details class="std-library-advanced-route-disclosure kt-std-lib-advanced-disclosure">
	<summary data-testid="std-library-advanced-view-toggle" class="std-library-advanced-view-summary">${__(
		"Advanced Technical View",
	)}</summary>
	<div class="std-library-advanced-route-body">
		<p class="text-muted small">${__(
			"Open the advanced catalogue for authorized technical review. This is not the default library experience.",
		)}</p>
		<button type="button" class="kt-std-lib-btn kt-std-lib-btn--primary" data-testid="std-library-advanced-catalogue-open">${__(
			"Open advanced catalogue",
		)}</button>
	</div>
</details>`;
	}

	function _html() {
		return `
<div class="kt-std-lib-root" data-testid="kt-std-lib-root">
	${_topbarHtml()}
	<div class="kt-std-lib-body" data-testid="kt-std-lib-body">
	<div class="kt-std-lib-page-header" data-testid="kt-std-lib-page-header">
		<p class="kt-std-lib-eyebrow">${__("KenTender Procurement System")}</p>
		<h1 class="kt-std-lib-title">${__("Standard Tender Documents")}</h1>
		<p class="kt-std-lib-subtitle">${__(
			"Manage approved Standard Tender Documents, active versions, applicability rules, supplier requirements, and readiness templates used during tender preparation.",
		)}</p>
	</div>
	<div class="kt-std-lib-bento" data-testid="kt-std-lib-bento">
		<div class="kt-std-lib-kpi-grid">${_kpiHtml()}</div>
		${_healthHtml()}
	</div>
	<div class="kt-std-lib-filter-bar" data-testid="kt-std-lib-filter-bar">
		<div class="kt-std-lib-search-wrap" data-testid="kt-std-lib-search-wrap">
			<span class="material-symbols-outlined kt-std-icon kt-std-lib-search-icon">search</span>
			<input
				type="search"
				class="kt-std-lib-search-input"
				data-testid="kt-std-lib-search"
				data-kt-std-search
				placeholder="Search STDs..."
			/>
		</div>
		<div class="kt-std-lib-filter-actions">
			<button type="button" class="kt-std-lib-btn" data-testid="kt-std-lib-filter-btn">
				<span class="material-symbols-outlined kt-std-icon">filter_list</span>${__("Filter")}
			</button>
			${_advancedDisclosureHtml()}
			<button type="button" class="kt-std-lib-btn kt-std-lib-btn--primary" data-testid="kt-std-lib-create-btn">
				<span class="material-symbols-outlined kt-std-icon">add</span>${__("Create STD")}
			</button>
		</div>
	</div>
	<div class="kt-std-lib-table-wrap" data-testid="kt-std-lib-table-wrap">
		<div class="kt-std-lib-table-scroll">
			<table class="kt-std-lib-table" data-testid="kt-std-lib-table">
				<thead>
					<tr>
						<th class="kt-std-lib-th">${__("STD Title")}</th>
						<th class="kt-std-lib-th">${__("Category")}</th>
						<th class="kt-std-lib-th" data-testid="kt-std-lib-col-method">${__("Method")}</th>
						<th class="kt-std-lib-th">${__("Status")}</th>
						<th class="kt-std-lib-th kt-std-lib-th--actions" data-testid="kt-std-lib-col-actions">${__("Actions")}</th>
					</tr>
				</thead>
				<tbody data-kt-std-table-body>
					<tr><td colspan="5" class="kt-std-lib-empty">${__("Loading templates…")}</td></tr>
				</tbody>
			</table>
		</div>
		<div class="kt-std-lib-pagination" data-testid="kt-std-lib-pagination">
			<p class="kt-std-lib-pagination__summary" data-testid="kt-std-lib-pagination-summary" data-kt-std-page-summary></p>
			<div class="kt-std-lib-pagination__size" data-testid="kt-std-lib-pagination-size">
				<span>${__("Rows per page")}</span>
				<div class="kt-std-lib-pagination__select-wrap">
					<select data-kt-std-page-size>
						<option value="10">10</option>
						<option value="25">25</option>
						<option value="50">50</option>
						<option value="100">100</option>
					</select>
					<span class="material-symbols-outlined kt-std-icon kt-std-lib-pagination__select-icon">expand_more</span>
				</div>
			</div>
			<div class="kt-std-lib-pagination__pages" data-testid="kt-std-lib-pagination-pages" data-kt-std-pagination-pages></div>
		</div>
	</div>
	</div>
</div>`;
	}

	function _setKpis(root, counts) {
		const payload = counts || {};
		KPI_CARDS.forEach(function (card) {
			const el = root.querySelector(`[data-kt-std-kpi="${card.key}"]`);
			if (!el) return;
			const value = payload[card.countKey];
			el.textContent = value == null ? "0" : String(value);
		});
		const health = payload.health || {};
		HEALTH_ITEMS.forEach(function (item) {
			const el = root.querySelector(`[data-kt-std-health="${item.key}"]`);
			if (!el) return;
			const value = health[item.key];
			el.textContent = value == null ? "0" : String(value);
		});
	}

	function _loadSummary(root) {
		frappe.call({
			method: SUMMARY_API,
			callback: function (r) {
				_setKpis(root, (r && r.message) || {});
			},
		});
	}

	function _rowActionsHtml(row, code) {
		const actions = row.action_availability || {};
		const buttons = [];
		if (actions.open && actions.open.allowed) {
			buttons.push(
				`<button type="button" class="kt-std-lib-action-btn kt-std-lib-action-btn--secondary" data-kt-std-open="${shared._escapeHtml(code)}">${__(
					"Open",
				)}</button>`,
			);
		}
		if (actions.submit_for_review && actions.submit_for_review.allowed) {
			buttons.push(
				`<button type="button" class="kt-std-lib-action-btn kt-std-lib-action-btn--primary" data-testid="kt-std-lib-review" data-kt-std-configure="${shared._escapeHtml(code)}">${__(
					"Review",
				)}</button>`,
			);
		} else if (actions.activate && actions.activate.allowed) {
			buttons.push(
				`<button type="button" class="kt-std-lib-action-btn kt-std-lib-action-btn--primary" data-kt-std-activate="${shared._escapeHtml(code)}">${__(
					"Activate",
				)}</button>`,
			);
		} else {
			buttons.push(
				`<button type="button" class="kt-std-lib-action-btn kt-std-lib-action-btn--primary" data-testid="kt-std-lib-configure" data-kt-std-configure="${shared._escapeHtml(code)}">${__(
					"View Configuration",
				)}</button>`,
			);
		}
		buttons.push(
			`<button type="button" class="kt-std-lib-action-btn kt-std-lib-action-btn--icon" data-kt-std-row-menu="${shared._escapeHtml(code)}" aria-label="${__(
				"More actions",
			)}"><span class="material-symbols-outlined kt-std-icon">more_vert</span></button>`,
		);
		return `<div class="kt-std-lib-row-actions">${buttons.join("")}</div>`;
	}

	function _paginateItems(items) {
		const total = items.length;
		const pages = Math.max(1, Math.ceil(total / _pageSize));
		if (_pageIndex >= pages) _pageIndex = pages - 1;
		if (_pageIndex < 0) _pageIndex = 0;
		const start = _pageIndex * _pageSize;
		return {
			total: total,
			pages: pages,
			slice: items.slice(start, start + _pageSize),
			start: total ? start + 1 : 0,
			end: Math.min(start + _pageSize, total),
		};
	}

	function _pageNumberItems(pageIndex, totalPages) {
		if (totalPages <= 1) return [1];
		if (totalPages <= 5) {
			return Array.from({ length: totalPages }, function (_, index) {
				return index + 1;
			});
		}
		const current = pageIndex + 1;
		const items = [1];
		if (current > 3) items.push("ellipsis");
		const windowStart = Math.max(2, current - 1);
		const windowEnd = Math.min(totalPages - 1, current + 1);
		for (let page = windowStart; page <= windowEnd; page += 1) {
			items.push(page);
		}
		if (current < totalPages - 2) items.push("ellipsis");
		items.push(totalPages);
		const seen = new Set();
		return items.filter(function (item) {
			if (item === "ellipsis") {
				if (seen.has("ellipsis")) return false;
				seen.add("ellipsis");
				return true;
			}
			if (seen.has(item)) return false;
			seen.add(item);
			return true;
		});
	}

	function _renderPageButtons(root, meta) {
		const host = root.querySelector("[data-kt-std-pagination-pages]");
		if (!host) return;
		const items = _pageNumberItems(_pageIndex, meta.pages);
		const buttons = items
			.map(function (item) {
				if (item === "ellipsis") {
					return `<span class="kt-std-lib-pagination__ellipsis">...</span>`;
				}
				const active = item === _pageIndex + 1 ? " kt-std-lib-pagination__page-btn--active" : "";
				return `<button type="button" class="kt-std-lib-pagination__page-btn${active}" data-kt-std-page-number="${item}">${item}</button>`;
			})
			.join("");
		const prevDisabled = _pageIndex <= 0 ? " disabled" : "";
		const nextDisabled = _pageIndex >= meta.pages - 1 ? " disabled" : "";
		host.innerHTML = `
<button type="button" class="kt-std-lib-pagination__nav-btn" data-kt-std-page-prev aria-label="${__(
			"Previous page",
		)}"${prevDisabled}>
	<span class="material-symbols-outlined kt-std-icon">chevron_left</span>
</button>
${buttons}
<button type="button" class="kt-std-lib-pagination__nav-btn" data-kt-std-page-next aria-label="${__(
			"Next page",
		)}"${nextDisabled}>
	<span class="material-symbols-outlined kt-std-icon">chevron_right</span>
</button>`;
	}

	function _updatePagination(root, meta) {
		const summary = root.querySelector("[data-kt-std-page-summary]");
		if (summary) {
			if (meta.total === 0) {
				summary.textContent = __("No results");
			} else {
				summary.innerHTML = `${__("Showing")} <span class="kt-std-lib-pagination__range">${meta.start} - ${meta.end}</span> ${__(
					"of",
				)} <span class="kt-std-lib-pagination__total">${meta.total}</span> ${__("results")}`;
			}
		}
		const pageSize = root.querySelector("[data-kt-std-page-size]");
		if (pageSize) pageSize.value = String(_pageSize);
		_renderPageButtons(root, meta);
	}

	function _renderRows(root, items) {
		const tbody = root.querySelector("[data-kt-std-table-body]");
		if (!tbody) return;
		_lastItems = Array.isArray(items) ? items : [];
		const meta = _paginateItems(_lastItems);
		_updatePagination(root, meta);
		const rows = meta.slice;
		if (!rows.length) {
			tbody.innerHTML = `<tr><td colspan="5" class="kt-std-lib-empty">${__(
				"No STD templates match your search.",
			)}</td></tr>`;
			return;
		}

		tbody.innerHTML = rows
			.map(function (row) {
				const code = String(row.version_code || row.template_code || "").trim();
				const title = shared._escapeHtml(row.title || code || "—");
				const codeLabel = shared._escapeHtml(code || "—");
				const category = shared._escapeHtml(row.procurement_category || "—");
				const method = shared._escapeHtml(
					row.procurement_method || (row.supported_methods && row.supported_methods[0]) || "—",
				);
				const status = String(row.status || row.lifecycle_status || "—");
				const icon = _categoryIcon(row.procurement_category);
				return `
<tr class="kt-std-lib-row" data-testid="kt-std-lib-row" data-template-code="${shared._escapeHtml(code)}">
	<td class="kt-std-lib-td">
		<div class="kt-std-lib-row-title-wrap">
			<span class="material-symbols-outlined kt-std-icon kt-std-lib-row-icon">${icon}</span>
			<div>
				<p class="kt-std-lib-row-title">${title}</p>
				<p class="kt-std-lib-row-code">${__("ID")}: ${codeLabel}</p>
			</div>
		</div>
	</td>
	<td class="kt-std-lib-td"><span class="kt-std-lib-chip">${category}</span></td>
	<td class="kt-std-lib-td" data-testid="kt-std-lib-row-method">${method}</td>
	<td class="kt-std-lib-td">${_statusPill(status)}</td>
	<td class="kt-std-lib-td kt-std-lib-td--actions">${_rowActionsHtml(row, code)}</td>
</tr>`;
			})
			.join("");
	}

	function _loadTemplates(root, search) {
		const token = ++_listToken;
		frappe.call({
			method: TEMPLATES_API,
			args: {
				search: search || "",
				procurement_category: _filters.procurement_category || undefined,
				procurement_method: _filters.procurement_method || undefined,
				status: _filters.status || undefined,
			},
			callback: function (r) {
				if (token !== _listToken) return;
				const msg = (r && r.message) || {};
				_pageIndex = 0;
				_renderRows(root, msg.items || msg.rows || []);
			},
		});
	}

	function _openFilterDialog(root) {
		const dialog = new frappe.ui.Dialog({
			title: __("Filter STD Library"),
			fields: [
				{
					fieldname: "procurement_category",
					fieldtype: "Select",
					label: __("Category"),
					options: ["", "WORKS", "GOODS", "SERVICES", "CONSULTANCY"],
				},
				{
					fieldname: "procurement_method",
					fieldtype: "Select",
					label: __("Method"),
					options: ["", "Open Tender", "RFQ", "Restricted Tender"],
				},
				{
					fieldname: "status",
					fieldtype: "Select",
					label: __("Status"),
					options: [
						"",
						"Active",
						"Imported Draft",
						"Ready for Review",
						"Under Review",
						"Superseded",
					],
				},
			],
			primary_action_label: __("Apply"),
			primary_action: function () {
				const values = dialog.get_values() || {};
				_filters.procurement_category = values.procurement_category || "";
				_filters.procurement_method = values.procurement_method || "";
				_filters.status = values.status || "";
				dialog.hide();
				const searchInput = root.querySelector("[data-kt-std-search]");
				_loadTemplates(root, searchInput ? searchInput.value : "");
			},
			secondary_action_label: __("Clear"),
			secondary_action: function () {
				_filters = { procurement_category: "", procurement_method: "", status: "" };
				dialog.set_values({
					procurement_category: "",
					procurement_method: "",
					status: "",
				});
				dialog.hide();
				const searchInput = root.querySelector("[data-kt-std-search]");
				_loadTemplates(root, searchInput ? searchInput.value : "");
			},
		});
		dialog.set_values(_filters);
		dialog.show();
	}

	function _bindEvents(root) {
		const searchInput = root.querySelector("[data-kt-std-search]");
		if (searchInput) {
			searchInput.addEventListener("input", function () {
				clearTimeout(_searchTimer);
				const value = searchInput.value || "";
				_searchTimer = setTimeout(function () {
					_loadTemplates(root, value);
				}, 250);
			});
		}
		const pageSize = root.querySelector("[data-kt-std-page-size]");
		if (pageSize) {
			pageSize.addEventListener("change", function () {
				_pageSize = parseInt(pageSize.value, 10) || 10;
				_pageIndex = 0;
				_renderRows(root, _lastItems);
			});
		}

		root.addEventListener("click", function (event) {
			const createBtn = event.target.closest("[data-testid='kt-std-lib-create-btn']");
			if (createBtn) {
				frappe.show_alert({
					message: __("Create STD flow will open here."),
					indicator: "blue",
				});
				return;
			}
			const filterBtn = event.target.closest("[data-testid='kt-std-lib-filter-btn']");
			if (filterBtn) {
				_openFilterDialog(root);
				return;
			}
			const prevBtn = event.target.closest("[data-kt-std-page-prev]");
			if (prevBtn && !prevBtn.disabled) {
				_pageIndex -= 1;
				_renderRows(root, _lastItems);
				return;
			}
			const nextBtn = event.target.closest("[data-kt-std-page-next]");
			if (nextBtn && !nextBtn.disabled) {
				_pageIndex += 1;
				_renderRows(root, _lastItems);
				return;
			}
			const pageBtn = event.target.closest("[data-kt-std-page-number]");
			if (pageBtn) {
				const pageNumber = parseInt(pageBtn.getAttribute("data-kt-std-page-number"), 10);
				if (!Number.isNaN(pageNumber)) {
					_pageIndex = pageNumber - 1;
					_renderRows(root, _lastItems);
				}
				return;
			}
			const openBtn = event.target.closest("[data-kt-std-open]");
			if (openBtn) {
				frappe.set_route("Form", "STD Template", openBtn.getAttribute("data-kt-std-open"));
				return;
			}
			const configureBtn = event.target.closest("[data-kt-std-configure]");
			if (configureBtn) {
				const code = configureBtn.getAttribute("data-kt-std-configure");
				if (code) {
					frappe.set_route("std-configurator", code, "overview");
				}
				return;
			}
			const advCatOpen = event.target.closest("[data-testid='std-library-advanced-catalogue-open']");
			if (advCatOpen) {
				frappe.set_route("std-engine-advanced");
				return;
			}
			const activateBtn = event.target.closest("[data-kt-std-activate]");
			if (activateBtn) {
				frappe.show_alert({
					message: __("Activate flow for {0}", [activateBtn.getAttribute("data-kt-std-activate")]),
					indicator: "blue",
				});
				return;
			}
			const menuBtn = event.target.closest("[data-kt-std-row-menu]");
			if (menuBtn) {
				const code = menuBtn.getAttribute("data-kt-std-row-menu");
				const menuDialog = new frappe.ui.Dialog({
					title: __("Actions"),
					size: "small",
				});
				menuDialog.$body.html(`
<div class="kt-std-lib-row-menu">
	<button type="button" class="kt-std-lib-btn kt-std-lib-btn--block" data-kt-std-menu-import>${__("Import Package")}</button>
	<button type="button" class="kt-std-lib-btn kt-std-lib-btn--block" data-kt-std-menu-row>${__(
		"Row actions for {0}",
		[code],
	)}</button>
</div>`);
				menuDialog.$body.find("[data-kt-std-menu-import]").on("click", function () {
					menuDialog.hide();
					frappe.set_route("std-library", "import");
				});
				menuDialog.$body.find("[data-kt-std-menu-row]").on("click", function () {
					menuDialog.hide();
					frappe.show_alert({
						message: __("Row actions for {0}", [code]),
						indicator: "blue",
					});
				});
				menuDialog.show();
			}
		});
	}

	function _mountList(wrapper) {
		shared._ensureFonts();
		if (!wrapper) return;
		if (wrapper.querySelector("[data-testid='kt-std-lib-root']")) return;
		wrapper.innerHTML = _html();
		const root = wrapper.querySelector("[data-testid='kt-std-lib-root']");
		if (!root) return;
		_bindEvents(root);
		_loadSummary(root);
		_loadTemplates(root, "");
	}

	function _mountImport(wrapper) {
		const importPage = kentender_procurement.std_library_import_page;
		if (importPage && typeof importPage.mount === "function") {
			importPage.mount(wrapper);
			return;
		}
		wrapper.innerHTML = `<div class="kt-std-lib-root" data-testid="kt-std-lib-import-placeholder"><p class="kt-std-lib-empty">${__(
			"Import wizard module is not loaded.",
		)}</p></div>`;
	}

	function _mount(wrapper) {
		if (!wrapper) return;
		if (_isImportRoute()) {
			_mountImport(wrapper);
			return;
		}
		_mountList(wrapper);
	}

	function _ensureSidebar() {
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup("Governance & Configuration");
		}
	}

	frappe.pages["std-library"].on_page_load = function (wrapper) {
		_mount(wrapper);
	};

	frappe.pages["std-library"].on_page_show = function (wrapper) {
		document.body.classList.add("kt-std-lib-shell");
		setTimeout(_ensureSidebar, 0);
		_mount(wrapper);
		if (!_isImportRoute()) {
			const root = wrapper.querySelector("[data-testid='kt-std-lib-root']");
			if (root) {
				_loadSummary(root);
				const searchInput = root.querySelector("[data-kt-std-search]");
				_loadTemplates(root, searchInput ? searchInput.value : "");
			}
		}
	};

	frappe.pages["std-library"].on_page_hide = function () {
		document.body.classList.remove("kt-std-lib-shell");
	};
})();
