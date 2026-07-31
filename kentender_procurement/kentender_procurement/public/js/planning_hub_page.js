/* ── Procurement Planning — Hub Page (v4, wired) ───────────────────────────── */
/* Pattern: Demand Hub + Budget Hub — mount shell once, load via shell API.      */
/* Deferred: Request Revision workflow, global toolbar search, server filter.    */

(function () {
	"use strict";

	var SHELL_API =
		"kentender_procurement.procurement_planning.api.planning_hub.get_pp_planning_hub_shell_data";
	var PLANS_PAGE_API =
		"kentender_procurement.procurement_planning.api.planning_hub.get_pp_planning_hub_plans_page";
	var CLOSE_PLAN_API =
		"kentender_procurement.procurement_planning.api.procurement_plans.close_pp_procurement_plan";
	var ACTIVATE_PLAN_API =
		"kentender_procurement.procurement_planning.api.procurement_plans.activate_pp_procurement_plan";
	var WORKBENCH_ROOT = "/desk/procurement-planning";

	var _state = {
		shell: null,
		ledger: { rows: [], total: 0, start: 0, limit: 20, page: 1 },
		filter: "",
		loading: false,
	};

	function _ensureFonts() {
		if (document.getElementById("kt-pph-fonts")) return;
		var link = document.createElement("link");
		link.id = "kt-pph-fonts";
		link.rel = "stylesheet";
		link.href =
			"https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700&" +
			"family=Inter:wght@400;500;600&" +
			"family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap";
		document.head.appendChild(link);
	}

	function _esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function _formatValue(row) {
		var amount = Number(row.total_value || 0);
		var cur = row.currency || "KES";
		if (!amount) return cur + " 0";
		return cur + " " + amount.toLocaleString(undefined, { maximumFractionDigits: 0 });
	}

	function _navigateWorkbench(planCode, queue) {
		var code = String(planCode || "").trim();
		var q = String(queue || "").trim();
		var url = new URL(window.location.origin + WORKBENCH_ROOT);
		if (code) url.searchParams.set("plan", code);
		if (q) url.searchParams.set("queue", q);
		window.location.href = url.pathname + url.search;
	}

	function _shellHtml() {
		return (
			'<div class="kt-pph-hub" data-testid="kt-pph-hub">' +
			'<div class="kt-pph-toolbar" data-testid="kt-pph-toolbar">' +
			'<span class="kt-pph-toolbar__brand" data-testid="kt-pph-toolbar-title">Plan Management</span>' +
			'<div class="kt-pph-toolbar__search">' +
			'<span class="material-symbols-outlined">search</span>' +
			'<input type="text" placeholder="Search plans, demands, or packages..." data-testid="kt-pph-global-search" disabled>' +
			"</div>" +
			'<div class="kt-pph-toolbar__right">' +
			'<button class="kt-pph-icon-btn" type="button" aria-label="Notifications">' +
			'<span class="material-symbols-outlined">notifications</span>' +
			'<span class="kt-pph-icon-btn__dot"></span></button>' +
			'<button class="kt-pph-icon-btn" type="button" aria-label="Help">' +
			'<span class="material-symbols-outlined">help</span></button>' +
			'<button class="kt-pph-icon-btn" type="button" aria-label="Settings">' +
			'<span class="material-symbols-outlined">settings</span></button>' +
			'<div class="kt-pph-toolbar__sep" aria-hidden="true"></div>' +
			'<div class="kt-pph-avatar"><span class="material-symbols-outlined">person</span></div>' +
			"</div></div>" +
			'<header class="kt-pph-header" data-testid="kt-pph-header">' +
			"<div>" +
			'<h1 class="kt-pph-header__title" data-testid="kt-pph-page-title">Procurement Planning Hub</h1>' +
			'<p class="kt-pph-header__sub">Select the active procurement plan, monitor planning progress, and enter the workbench.</p>' +
			"</div>" +
			'<div class="kt-pph-header__actions" data-pph="header-actions"></div>' +
			"</header>" +
			'<div class="kt-pph-canvas">' +
			'<section class="kt-pph-hero" data-testid="kt-pph-hero">' +
			'<div data-pph="hero-top"></div>' +
			'<div class="kt-pph-stats" data-testid="kt-pph-stats" data-pph="hero-stats"></div>' +
			"</section>" +
			'<section class="kt-pph-ledger" data-testid="kt-pph-ledger">' +
			'<div class="kt-pph-ledger__head">' +
			'<h3 class="kt-pph-ledger__title">' +
			'<span class="material-symbols-outlined">format_list_bulleted</span>Procurement Plans Ledger</h3>' +
			'<div class="kt-pph-ledger__tools">' +
			'<div class="kt-pph-search">' +
			'<span class="material-symbols-outlined">search</span>' +
			'<input type="text" placeholder="Filter plans..." data-testid="kt-pph-ledger-filter">' +
			"</div>" +
			'<button class="kt-pph-btn-outline" type="button" data-testid="kt-pph-filter" disabled>' +
			'<span class="material-symbols-outlined">filter_list</span>Filter</button>' +
			'<button class="kt-pph-btn-primary kt-pph-btn-primary--sm" type="button" data-testid="kt-pph-create-plan">' +
			'<span class="material-symbols-outlined">add</span>Create Plan</button>' +
			"</div></div>" +
			'<div class="kt-pph-table-scroll">' +
			'<table class="kt-pph-table" data-testid="kt-pph-ledger-table">' +
			"<thead><tr>" +
			'<th class="kt-pph-th">Plan Title &amp; Ref</th>' +
			'<th class="kt-pph-th">Entity</th>' +
			'<th class="kt-pph-th">Fiscal Year</th>' +
			'<th class="kt-pph-th">Status</th>' +
			'<th class="kt-pph-th kt-pph-th--right">Total Value</th>' +
			'<th class="kt-pph-th kt-pph-th--right">Actions</th>' +
			"</tr></thead>" +
			'<tbody data-testid="kt-pph-ledger-body" data-pph="ledger-body"></tbody>' +
			"</table></div>" +
			'<div class="kt-pph-ledger__foot">' +
			'<span class="kt-pph-ledger__count" data-testid="kt-pph-ledger-count"></span>' +
			'<div class="kt-pph-pager" data-pph="ledger-pager"></div>' +
			"</div></section>" +
			'<section class="kt-pph-cta" data-testid="kt-pph-wizard-cta">' +
			'<span class="material-symbols-outlined kt-pph-cta__ghost" aria-hidden="true">lightbulb</span>' +
			'<div class="kt-pph-cta__copy">' +
			'<div class="kt-pph-cta__icon"><span class="material-symbols-outlined">add_task</span></div>' +
			"<div>" +
			'<h3 class="kt-pph-cta__title">Need to initiate a new cycle?</h3>' +
			'<p class="kt-pph-cta__desc">Start the \'Plan Wizard\' to define your entity\'s procurement requirements for the upcoming fiscal window. High-level compliance checks will be performed automatically.</p>' +
			"</div></div>" +
			'<button class="kt-pph-cta__btn" type="button" data-testid="kt-pph-launch-wizard">Launch Plan Wizard</button>' +
			"</section></div></div>"
		);
	}

	function _statHtml(stat) {
		var s = stat || {};
		if (s.id === "blocked_items") {
			return (
				'<div class="kt-pph-stat kt-pph-stat--blocked" data-testid="' +
				_esc(s.testid || "kt-pph-stat-blocked") +
				'" data-pph-action="open-blocked">' +
				'<div class="kt-pph-stat__head">' +
				'<span class="material-symbols-outlined kt-pph-stat__icon kt-pph-stat__icon--error">' +
				_esc(s.icon || "warning") +
				"</span>" +
				'<p class="kt-pph-stat__label kt-pph-stat__label--error">' +
				_esc(s.label || "Blocked Items") +
				"</p></div>" +
				'<div class="kt-pph-stat__foot">' +
				'<p class="kt-pph-stat__value kt-pph-stat__value--error">' +
				_esc(s.value || "0") +
				"</p>" +
				'<span class="material-symbols-outlined kt-pph-stat__arrow">arrow_forward</span></div></div>'
			);
		}
		return (
			'<div class="kt-pph-stat" data-testid="' +
			_esc(s.testid || "") +
			'">' +
			'<div class="kt-pph-stat__head">' +
			'<span class="material-symbols-outlined kt-pph-stat__icon kt-pph-stat__icon--' +
			_esc(s.tone || "primary") +
			'">' +
			_esc(s.icon || "") +
			"</span>" +
			'<p class="kt-pph-stat__label">' +
			_esc(s.label || "") +
			"</p></div>" +
			'<p class="kt-pph-stat__value kt-pph-stat__value--' +
			_esc(s.tone || "primary") +
			'">' +
			_esc(s.value || "—") +
			"</p></div>"
		);
	}

	function _rowHtml(row) {
		var r = row || {};
		var archived = r.row_action === "archive" || r.is_archived;
		var titleCls = "kt-pph-plan__title" + (archived ? " kt-pph-plan__title--muted" : "");
		var entityCls = "kt-pph-td kt-pph-td--entity" + (archived ? " kt-pph-td--muted" : "");
		var entityName = (r.entity && r.entity.name) || r.entity_name || "";
		var valueDisplay = _formatValue(r);
		var valueCell = archived
			? '<td class="kt-pph-td kt-pph-td--value kt-pph-td--value-inline kt-pph-td--muted">' +
			  _esc(valueDisplay) +
			  "</td>"
			: '<td class="kt-pph-td kt-pph-td--value"><div class="kt-pph-value"><span class="kt-pph-value__cur">' +
			  _esc(r.currency || "KES") +
			  '</span><span class="kt-pph-value__num">' +
			  _esc(Number(r.total_value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })) +
			  "</span></div></td>";
		var actionCell = archived
			? '<td class="kt-pph-td kt-pph-td--actions"><button type="button" class="kt-pph-rowbtn kt-pph-rowbtn--muted" data-pph-row-action="archive" data-plan-code="' +
			  _esc(r.code || "") +
			  '"><span class="material-symbols-outlined">history</span>ARCHIVE</button></td>'
			: '<td class="kt-pph-td kt-pph-td--actions"><button type="button" class="kt-pph-rowbtn" data-pph-row-action="open" data-plan-code="' +
			  _esc(r.code || "") +
			  '"><span class="material-symbols-outlined">open_in_new</span>OPEN</button></td>';
		return (
			'<tr class="kt-pph-row" data-testid="kt-pph-row" data-plan-code="' +
			_esc(r.code || "") +
			'">' +
			'<td class="kt-pph-td"><p class="' +
			titleCls +
			'">' +
			_esc(r.name || r.title || "") +
			'</p><p class="kt-pph-plan__ref">' +
			_esc(r.code || "") +
			"</p></td>" +
			'<td class="' +
			entityCls +
			'">' +
			_esc(entityName) +
			"</td>" +
			'<td class="kt-pph-td kt-pph-td--muted">' +
			_esc(r.fiscal_year || "") +
			"</td>" +
			'<td class="kt-pph-td"><span class="kt-pph-badge kt-pph-badge--' +
			_esc(r.status_tone || "neutral") +
			'"><span class="kt-pph-badge__dot"></span>' +
			_esc(r.status_label || "") +
			"</span></td>" +
			valueCell +
			actionCell +
			"</tr>"
		);
	}

	function _renderHeaderActions(wrapper, actions, activePlan) {
		var host = wrapper.querySelector('[data-pph="header-actions"]');
		if (!host) return;
		var a = actions || {};
		var html = "";
		if (a.show_request_revision) {
			html +=
				'<button class="kt-pph-btn-ghost" type="button" data-testid="kt-pph-request-revision" data-pph-action="request-revision">' +
				'<span class="material-symbols-outlined">history</span>Request Revision</button>';
		}
		if (a.show_close_plan) {
			html +=
				'<button class="kt-pph-btn-danger" type="button" data-testid="kt-pph-close-plan" data-pph-action="close-plan" data-plan-code="' +
				_esc((activePlan && activePlan.code) || "") +
				'"><span class="material-symbols-outlined">cancel</span>Close Plan</button>';
		}
		host.innerHTML = html;
	}

	function _renderHeroGate(wrapper, activePlan, cta) {
		var host = wrapper.querySelector('[data-pph="hero-top"]');
		if (!host) return;
		var ap = activePlan || {};
		var c = cta || {};
		if (ap.has_active_plan) {
			host.innerHTML =
				'<div class="kt-pph-hero__top">' +
				'<div class="kt-pph-hero__intro">' +
				'<div class="kt-pph-hero__tags">' +
				'<span class="kt-pph-tag kt-pph-tag--success"><span class="kt-pph-tag__pulse"></span>Active Plan</span>' +
				'<span class="kt-pph-tag kt-pph-tag--fy">FY ' +
				_esc(ap.fiscal_year || "") +
				"</span>" +
				"</div>" +
				'<h2 class="kt-pph-hero__title" data-testid="kt-pph-active-plan-title">' +
				_esc(ap.name || ap.plan_title || "") +
				"</h2>" +
				'<p class="kt-pph-hero__desc">' +
				_esc(ap.description || ap.message || "") +
				"</p></div>" +
				'<div class="kt-pph-hero__cta">' +
				'<button class="kt-pph-btn-primary" type="button" data-testid="kt-pph-open-workbench" data-pph-action="open-workbench" data-plan-code="' +
				_esc(ap.code || ap.plan_code || "") +
				'"><span class="material-symbols-outlined">open_in_new</span>Open Workbench</button>' +
				'<button class="kt-pph-btn-neutral" type="button" data-testid="kt-pph-view-plan" data-pph-action="view-plan" data-plan-code="' +
				_esc(ap.code || ap.plan_code || "") +
				'"><span class="material-symbols-outlined">visibility</span>View Plan</button></div></div>';
			return;
		}
		var primary = ap.primary_action || {};
		var secondary = ap.secondary_action || {};
		host.innerHTML =
			'<div class="kt-pph-hero__top kt-pph-hero__top--gate">' +
			'<div class="kt-pph-hero__intro">' +
			'<h2 class="kt-pph-hero__title" data-testid="kt-pph-active-plan-title">' +
			_esc(__("No Active Procurement Plan")) +
			"</h2>" +
			'<p class="kt-pph-hero__desc">' +
			_esc(ap.message || __("Create or activate a procurement plan before planning approved demands.")) +
			"</p></div>" +
			'<div class="kt-pph-hero__cta">' +
			(c.show_create_plan !== false
				? '<button class="kt-pph-btn-primary" type="button" data-testid="kt-pph-create-plan-gate" data-pph-action="create-plan"><span class="material-symbols-outlined">add</span>' +
				  _esc(primary.label || __("Create Plan")) +
				  "</button>"
				: "") +
			(c.show_create_plan !== false
				? '<button class="kt-pph-btn-neutral" type="button" data-testid="kt-pph-activate-plan-gate" data-pph-action="activate-plan">' +
				  _esc(secondary.label || __("Activate Existing Plan")) +
				  "</button>"
				: "") +
			"</div></div>";
	}

	function _renderHeroStats(wrapper, stats) {
		var host = wrapper.querySelector('[data-pph="hero-stats"]');
		if (!host) return;
		var rows = Array.isArray(stats) ? stats : [];
		host.innerHTML = rows.map(_statHtml).join("");
	}

	function _renderLedger(wrapper) {
		var body = wrapper.querySelector('[data-pph="ledger-body"]');
		var countEl = wrapper.querySelector('[data-testid="kt-pph-ledger-count"]');
		if (!body) return;
		var rows = _state.ledger.rows || [];
		if (!rows.length) {
			body.innerHTML =
				'<tr><td class="kt-pph-td" colspan="6"><span class="kt-pph-ledger__empty">' +
				_esc(__("No procurement plans found for your scope.")) +
				"</span></td></tr>";
		} else {
			body.innerHTML = rows.map(_rowHtml).join("");
		}
		var total = Number(_state.ledger.total || rows.length || 0);
		var start = Number(_state.ledger.start || 0);
		var visible = rows.length;
		if (countEl) {
			if (_state.filter) {
				countEl.textContent = __("Showing {0} of {1} plans", [visible, total]);
			} else if (total <= visible) {
				countEl.textContent = total
					? __("Showing {0} plans", [total])
					: __("No plans");
			} else {
				countEl.textContent = __("Showing {0} to {1} of {2} plans", [
					start + 1,
					start + visible,
					total,
				]);
			}
		}
	}

	function _renderCtaActions(wrapper, cta) {
		var c = cta || {};
		var createBtn = wrapper.querySelector('[data-testid="kt-pph-create-plan"]');
		var wizardBtn = wrapper.querySelector('[data-testid="kt-pph-launch-wizard"]');
		if (createBtn) createBtn.style.display = c.show_create_plan ? "" : "none";
		if (wizardBtn) wizardBtn.style.display = c.show_launch_wizard ? "" : "none";
	}

	function _applyShell(wrapper, data) {
		if (!data || !data.ok) {
			_renderInlineError(wrapper, (data && data.message) || __("Unable to load Planning Hub."));
			return;
		}
		_state.shell = data;
		_state.ledger.rows = ((data.ledger_preview && data.ledger_preview.rows) || []).slice();
		_state.ledger.total = Number((data.ledger_preview && data.ledger_preview.total) || _state.ledger.rows.length);
		_state.ledger.start = Number((data.ledger_preview && data.ledger_preview.start) || 0);
		_state.ledger.limit = Number((data.ledger_preview && data.ledger_preview.limit) || 20);
		_renderHeaderActions(wrapper, data.header_actions, data.active_plan);
		_renderHeroGate(wrapper, data.active_plan, data.cta_actions);
		_renderHeroStats(wrapper, data.hero_stats);
		_renderLedger(wrapper);
		_renderCtaActions(wrapper, data.cta_actions);
	}

	function _renderInlineError(wrapper, msg) {
		if (!wrapper) return;
		wrapper.innerHTML =
			'<div class="kt-pph-hub" data-testid="kt-pph-hub">' +
			'<div class="kt-pph-error-banner" role="alert">' +
			'<span class="material-symbols-outlined">error_outline</span>' +
			"<span>" +
			_esc(msg || __("An error occurred.")) +
			"</span></div></div>";
	}

	function _showCreatePlanModal(wrapper) {
		if (
			kentender_procurement.PlanningCreatePlanModal &&
			typeof kentender_procurement.PlanningCreatePlanModal.show === "function"
		) {
			kentender_procurement.PlanningCreatePlanModal.show({
				onCreated: function () {
					_loadHubData(wrapper);
				},
			});
			return;
		}
		frappe.msgprint(__("Create Plan is not available on this page."));
	}

	function _showActivatePlanDialog(wrapper) {
		frappe.call({
			method: PLANS_PAGE_API,
			args: { limit: 200 },
			callback: function (r) {
				var msg = (r && r.message) || {};
				var drafts = (msg.rows || []).filter(function (row) {
					return String(row.status_label || "").toLowerCase() === "draft";
				});
				if (!drafts.length) {
					frappe.msgprint(__("No draft procurement plans are available to activate."));
					return;
				}
				frappe.prompt(
					[
						{
							fieldname: "plan_code",
							fieldtype: "Select",
							label: __("Draft plan"),
							options: drafts
								.map(function (row) {
									return row.code;
								})
								.join("\n"),
							reqd: 1,
						},
					],
					function (values) {
						frappe.call({
							method: ACTIVATE_PLAN_API,
							args: { plan_id: values.plan_code },
							callback: function (resp) {
								var out = (resp && resp.message) || {};
								if (!out.ok) {
									frappe.msgprint(out.message || __("Plan could not be activated."));
									return;
								}
								frappe.show_alert({ message: __("Plan activated."), indicator: "green" });
								_loadHubData(wrapper);
							},
						});
					},
					__("Activate Existing Plan"),
					__("Activate"),
				);
			},
		});
	}

	function _closePlan(wrapper, planCode) {
		var code = String(planCode || "").trim();
		if (!code) return;
		frappe.confirm(__("Close procurement plan {0}?", [code]), function () {
			frappe.call({
				method: CLOSE_PLAN_API,
				args: { plan_id: code },
				callback: function (r) {
					var msg = (r && r.message) || {};
					if (!msg.ok) {
						frappe.msgprint(msg.message || __("Plan could not be closed."));
						return;
					}
					frappe.show_alert({ message: __("Plan closed."), indicator: "green" });
					_loadHubData(wrapper);
				},
			});
		});
	}

	function _viewPlanEvidence(planCode, title) {
		var code = String(planCode || "").trim();
		if (!code) return;
		if (
			kentender_procurement.PlanningWorkbenchEvidenceDrawer &&
			typeof kentender_procurement.PlanningWorkbenchEvidenceDrawer.openForPlan === "function"
		) {
			kentender_procurement.PlanningWorkbenchEvidenceDrawer.openForPlan({
				plan_id: code,
				title: title,
			});
			return;
		}
		frappe.set_route("Form", "Procurement Plan", code);
	}

	function _filterLedgerRows(wrapper, term) {
		_state.filter = String(term || "").trim();
		if (!_state.filter) {
			_state.ledger.rows = ((_state.shell && _state.shell.ledger_preview) || {}).rows || [];
			_renderLedger(wrapper);
			return;
		}
		frappe.call({
			method: PLANS_PAGE_API,
			args: { search: _state.filter, limit: 200 },
			callback: function (r) {
				var msg = (r && r.message) || {};
				if (!msg.ok) return;
				_state.ledger.rows = msg.rows || [];
				_state.ledger.total = Number(msg.total || _state.ledger.rows.length);
				_renderLedger(wrapper);
			},
		});
	}

	function _loadHubData(wrapper) {
		if (!wrapper) return;
		_state.loading = true;
		frappe.call({
			method: SHELL_API,
			freeze: false,
			callback: function (r) {
				_state.loading = false;
				_applyShell(wrapper, (r && r.message) || {});
			},
			error: function () {
				_state.loading = false;
				_renderInlineError(wrapper, __("Could not connect to the server. Please refresh the page."));
			},
		});
	}

	function _bindEvents(wrapper) {
		if (!wrapper || wrapper.getAttribute("data-pph-bound") === "1") return;
		wrapper.setAttribute("data-pph-bound", "1");
		wrapper.addEventListener("click", function (ev) {
			var btn = ev.target.closest("[data-pph-action], [data-pph-row-action]");
			if (!btn) return;
			var action = btn.getAttribute("data-pph-action") || btn.getAttribute("data-pph-row-action");
			var planCode = btn.getAttribute("data-plan-code") || "";
			if (action === "create-plan") {
				_showCreatePlanModal(wrapper);
				return;
			}
			if (action === "activate-plan") {
				_showActivatePlanDialog(wrapper);
				return;
			}
			if (action === "close-plan") {
				_closePlan(wrapper, planCode);
				return;
			}
			if (action === "open-workbench" || action === "open") {
				_navigateWorkbench(planCode);
				return;
			}
			if (action === "view-plan") {
				var active = (_state.shell && _state.shell.active_plan) || {};
				_viewPlanEvidence(planCode, active.name || active.plan_title);
				return;
			}
			if (action === "open-blocked") {
				var activePlan = (_state.shell && _state.shell.active_plan) || {};
				_navigateWorkbench(activePlan.code || activePlan.plan_code, "blocked");
				return;
			}
			if (action === "archive") {
				_viewPlanEvidence(planCode);
			}
		});
		var filter = wrapper.querySelector('[data-testid="kt-pph-ledger-filter"]');
		if (filter) {
			filter.addEventListener("input", function (e) {
				_filterLedgerRows(wrapper, e.target.value);
			});
		}
		var createBtn = wrapper.querySelector('[data-testid="kt-pph-create-plan"]');
		if (createBtn) {
			createBtn.addEventListener("click", function () {
				_showCreatePlanModal(wrapper);
			});
		}
		var wizardBtn = wrapper.querySelector('[data-testid="kt-pph-launch-wizard"]');
		if (wizardBtn) {
			wizardBtn.addEventListener("click", function () {
				_showCreatePlanModal(wrapper);
			});
		}
	}

	function _mount(wrapper) {
		_ensureFonts();
		if (!wrapper) return;
		if (!wrapper.querySelector(".kt-pph-hub")) {
			wrapper.innerHTML = _shellHtml();
			_bindEvents(wrapper);
		}
		_loadHubData(wrapper);
	}

	frappe.pages["planning-hub"].on_page_load = function (wrapper) {
		_mount(wrapper);
	};

	frappe.pages["planning-hub"].on_page_show = function (wrapper) {
		document.body.classList.add("kt-pph-shell");
		setTimeout(function () {
			if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
				// Civic Ledger IA: keep the parent Procurement rail.
				frappe.app.sidebar.setup("Procurement");
			}
		}, 0);
		_mount(wrapper);
	};

	frappe.pages["planning-hub"].on_page_hide = function () {
		document.body.classList.remove("kt-pph-shell");
	};
})();
