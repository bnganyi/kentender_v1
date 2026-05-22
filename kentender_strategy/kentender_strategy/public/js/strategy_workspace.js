// Strategy Management workspace — unified master/detail workbench.

(function () {
	const WS_LABEL = "Strategy Management";
	const PLAN_TABS = [
		{ id: "info", label: __("Plan Info"), testId: "strategy-tab-plan-info" },
		{ id: "structure", label: __("Structure"), testId: "strategy-tab-structure" },
		{ id: "review", label: __("Review"), testId: "strategy-tab-review" },
		{ id: "audit", label: __("Audit"), testId: "strategy-tab-audit" },
	];

	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;
	let lastPayload = null;
	let landingLoadInFlight = false;
	let selectedPlanName = null;
	let activeStatusFilter = "all";
	let planSearchQuery = "";
	let activePlanTab = "info";
	let planTabInitialized = false;
	let planSelectionInitialized = false;
	let pendingPlanListScrollTop = null;
	let structurePanelMounted = false;
	let sidebarSyncTimer = null;

	function saveStrategyWorkbenchState() {
		if (typeof kentender_core === "undefined" || !kentender_core.kt_state) return;
		kentender_core.kt_state.save("strategy", {
			workTab: activePlanTab,
			selectedRecord: selectedPlanName,
			statusFilter: activeStatusFilter,
		});
		if (selectedPlanName) {
			kentender_core.kt_state.setSelectedRecord("strategy", selectedPlanName);
		}
	}

	function applyInitialWorkbenchState(payload) {
		if (planSelectionInitialized) return;
		planSelectionInitialized = true;
		let storedPlan = null;
		if (typeof kentender_core !== "undefined" && kentender_core.kt_state) {
			const st = kentender_core.kt_state.restore("strategy");
			if (st) {
				if (st.workTab) activePlanTab = st.workTab;
				if (st.statusFilter) activeStatusFilter = st.statusFilter;
			}
			if (kentender_core.kt_state.consumeSelectedRecord) {
				storedPlan = kentender_core.kt_state.consumeSelectedRecord("strategy");
			}
		}
		planTabInitialized = true;
		if (storedPlan && payload && findPlan(payload, storedPlan)) {
			selectedPlanName = storedPlan;
		}
	}

	function ensurePlanTab() {
		if (!activePlanTab) activePlanTab = "info";
	}

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function userCanReadStrategicPlan() {
		try {
			return (
				typeof frappe !== "undefined" &&
				frappe.model &&
				typeof frappe.model.can_read === "function" &&
				frappe.model.can_read("Strategic Plan")
			);
		} catch (e) {
			return false;
		}
	}

	function userCanCreateStrategicPlan() {
		try {
			return (
				typeof frappe !== "undefined" &&
				frappe.model &&
				typeof frappe.model.can_create === "function" &&
				frappe.model.can_create("Strategic Plan")
			);
		} catch (e) {
			return false;
		}
	}

	function userCanWriteStrategicPlan() {
		try {
			return (
				typeof frappe !== "undefined" &&
				frappe.model &&
				typeof frappe.model.can_write === "function" &&
				frappe.model.can_write("Strategic Plan")
			);
		} catch (e) {
			return false;
		}
	}

	function workspaceNameMatchesStrategy(name) {
		if (name == null || name === "") return false;
		if (name === WS_LABEL) return true;
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(WS_LABEL);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "strategy-management";
	}

	function isStrategyWorkspaceRoute() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesStrategy(workspaceName)) return true;
					if (workspaceName) return false;
				}
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const loc = window.location;
			const raw = (loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "";
			const path = decodeURIComponent(String(raw).toLowerCase());
			if (path.includes("strategy-management") || path.includes("strategy%20management")) return true;
		} catch (e2) {
			/* ignore */
		}
		try {
			const route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				const w = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceNameMatchesStrategy(w)) return true;
				if (w) return false;
			}
		} catch (e3) {
			return false;
		}
		return false;
	}

	function syncStrategyShellClass() {
		document.body.classList.toggle("kt-strategy-shell", isStrategyWorkspaceRoute());
	}

	function syncStrategySidebarHighlight() {
		if (!isStrategyWorkspaceRoute()) return;
		const items = Array.from(document.querySelectorAll(".standard-sidebar-item"));
		if (!items.length) return;
		let primary = null;
		for (let i = 0; i < items.length; i++) {
			const item = items[i];
			const label = String(item.textContent || "").trim().toLowerCase();
			if (label === "strategy alignment" && !primary) primary = item;
		}
		if (!primary) return;
		for (let i = 0; i < items.length; i++) {
			const item = items[i];
			const label = String(item.textContent || "").trim().toLowerCase();
			if (label === "strategy alignment (full)" || item === primary) {
				item.classList.remove("active-sidebar");
			}
		}
		primary.classList.add("active-sidebar");
	}

	function scheduleStrategySidebarHighlightSync() {
		syncStrategySidebarHighlight();
		if (sidebarSyncTimer) window.clearTimeout(sidebarSyncTimer);
		sidebarSyncTimer = window.setTimeout(function () {
			syncStrategySidebarHighlight();
		}, 120);
	}

	function removeStrategyLandingIfWrongRoute() {
		document.querySelectorAll(".kt-strategy-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-strategy-shell");
		selectedPlanName = null;
		lastPayload = null;
		landingLoadInFlight = false;
		bindScheduled = false;
		planSelectionInitialized = false;
		planTabInitialized = false;
		structurePanelMounted = false;
	}

	function getVisibleWorkspacesPageRoot() {
		try {
			if (typeof frappe !== "undefined" && frappe.container && frappe.container.page) {
				const p = frappe.container.page;
				const route = p.getAttribute && p.getAttribute("data-page-route");
				if (route === "Workspaces" && p.isConnected) return p;
			}
		} catch (e) {
			/* ignore */
		}
		return (
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]')
		);
	}

	function strategyShellPresent() {
		const root = getVisibleWorkspacesPageRoot();
		if (!root) return false;
		return root.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]') != null;
	}

	function resolveWorkspaceEditorMount() {
		const root = getVisibleWorkspacesPageRoot();
		if (root) {
			let esc = root.querySelector(".layout-main-section .editor-js-container");
			if (!esc) esc = root.querySelector(".editor-js-container");
			if (!esc) {
				const lms = root.querySelector(".layout-main-section");
				if (lms) esc = lms;
			}
			if (esc) return esc;
		}
		const candidates = document.querySelectorAll(".editor-js-container");
		let fallback = null;
		for (let i = 0; i < candidates.length; i++) {
			const el = candidates[i];
			if (!el || !el.isConnected) continue;
			if (!fallback) fallback = el;
			if (el.getClientRects && el.getClientRects().length > 0) return el;
		}
		return fallback;
	}

	function findPlan(payload, name) {
		const plans = (payload && payload.plans) || [];
		for (let i = 0; i < plans.length; i++) {
			if (plans[i].name === name) return plans[i];
		}
		return null;
	}

	function statusBadgeClass(status) {
		const s = String(status || "").trim().toLowerCase();
		if (s === "draft") return "kt-strategy-badge kt-strategy-badge--draft";
		if (s === "submitted") return "kt-strategy-badge kt-strategy-badge--submitted";
		if (s === "approved") return "kt-strategy-badge kt-strategy-badge--approved";
		if (s === "active") return "kt-strategy-badge kt-strategy-badge--active";
		if (s === "archived") return "kt-strategy-badge kt-strategy-badge--archived";
		return "kt-strategy-badge";
	}

	function statusChipCount(portfolio, filterId) {
		const p = portfolio || {};
		const id = String(filterId || "all").toLowerCase();
		if (id === "all") return p.total_plans != null ? p.total_plans : 0;
		if (id === "draft") return p.draft_count != null ? p.draft_count : 0;
		if (id === "submitted") return p.submitted_count != null ? p.submitted_count : 0;
		if (id === "approved") return p.approved_count != null ? p.approved_count : 0;
		if (id === "active") return p.active_count != null ? p.active_count : 0;
		if (id === "archived") return p.archived_count != null ? p.archived_count : 0;
		return 0;
	}

	function filterPlansByStatus(plans) {
		const id = String(activeStatusFilter || "all").toLowerCase();
		if (id === "all") return plans.slice();
		return plans.filter(function (p) {
			return String(p.status || "").trim().toLowerCase() === id;
		});
	}

	function filterPlansBySearch(plans) {
		const q = String(planSearchQuery || "")
			.trim()
			.toLowerCase();
		if (!q) return plans.slice();
		return plans.filter(function (p) {
			const title = String(p.strategic_plan_name || p.name || "").toLowerCase();
			return title.indexOf(q) >= 0;
		});
	}

	function readinessLabel(selected) {
		const pc = Number(selected.program_count || 0);
		const spc = Number(selected.sub_program_count || 0);
		const ic = Number(selected.indicator_count != null ? selected.indicator_count : selected.objective_count || 0);
		const tc = Number(selected.target_count || 0);
		if (pc > 0 && spc > 0 && ic > 0 && tc > 0) return __("Ready for downstream use");
		return __("Structure incomplete");
	}

	function renderStatusChips(portfolio) {
		const chips = [
			{ id: "all", label: __("All"), testId: "strategy-status-all" },
			{ id: "draft", label: __("Draft"), testId: "strategy-status-draft" },
			{ id: "submitted", label: __("Submitted"), testId: "strategy-status-submitted" },
			{ id: "approved", label: __("Approved"), testId: "strategy-status-approved" },
			{ id: "active", label: __("Active"), testId: "strategy-status-active" },
			{ id: "archived", label: __("Archived"), testId: "strategy-status-archived" },
		];
		let html =
			'<div class="kt-strategy-status-chips mb-2" data-testid="strategy-status-chips">' +
			'<div class="kt-status-filter-row" role="group" aria-label="' +
			escapeHtml(__("Status Filters")) +
			'">';
		for (let i = 0; i < chips.length; i++) {
			const c = chips[i];
			const on = activeStatusFilter === c.id;
			const count = statusChipCount(portfolio, c.id);
			const isZero = Number(count) === 0;
			html +=
				'<button type="button" class="kt-status-filter kt-strategy-status-chip' +
				(on ? " is-active kt-status-filter-active" : "") +
				(isZero ? " is-zero" : "") +
				'" data-kt-strategy-status="' +
				escapeHtml(c.id) +
				'" data-testid="' +
				escapeHtml(c.testId) +
				'">' +
				'<span class="kt-status-filter__label">' +
				escapeHtml(c.label) +
				'</span> <span class="kt-status-filter__count">' +
				escapeHtml(String(count)) +
				"</span></button>";
		}
		html += "</div></div>";
		return html;
	}

	function renderPlanTabs() {
		ensurePlanTab();
		let html =
			'<div class="kt-strategy-plan-tabs mb-3" role="tablist" data-testid="strategy-plan-tabs">' +
			'<div class="kt-primary-tabs">';
		for (let i = 0; i < PLAN_TABS.length; i++) {
			const tab = PLAN_TABS[i];
			const on = activePlanTab === tab.id;
			html +=
				'<button type="button" class="kt-primary-tab kt-strategy-plan-tab' +
				(on ? " is-active kt-primary-tab-active" : "") +
				'" data-kt-strategy-plan-tab="' +
				escapeHtml(tab.id) +
				'" data-testid="' +
				escapeHtml(tab.testId) +
				'" role="tab" aria-selected="' +
				(on ? "true" : "false") +
				'">' +
				escapeHtml(tab.label) +
				"</button>";
		}
		html += "</div></div>";
		return html;
	}

	function renderPlanTabContent(selected) {
		if (activePlanTab === "structure") {
			return (
				'<div class="kt-strategy-tab-panel" data-testid="strategy-tab-panel-structure">' +
				'<div data-testid="strategy-structure-panel-host"></div>' +
				"</div>"
			);
		}
		if (activePlanTab === "review") {
			return (
				'<div class="kt-strategy-tab-panel" data-testid="strategy-tab-panel-review">' +
				'<div data-testid="strategy-review-panel-host"></div>' +
				"</div>"
			);
		}
		if (activePlanTab === "audit") {
			return (
				'<div class="kt-strategy-tab-panel" data-testid="strategy-tab-panel-audit">' +
				'<div data-testid="strategy-audit-panel-host"></div>' +
				"</div>"
			);
		}
		const entity = selected.procuring_entity || "—";
		const version = selected.version_no != null ? selected.version_no : "—";
		return (
			'<div class="kt-strategy-tab-panel" data-testid="strategy-tab-panel-info">' +
			'<dl class="row mb-2">' +
			'<dt class="col-sm-3">' +
			escapeHtml(__("Entity")) +
			'</dt><dd class="col-sm-9" data-testid="selected-plan-entity">' +
			escapeHtml(entity) +
			"</dd>" +
			'<dt class="col-sm-3">' +
			escapeHtml(__("Period")) +
			"</dt><dd class=\"col-sm-9\">" +
			escapeHtml(String(selected.start_year || "—")) +
			" — " +
			escapeHtml(String(selected.end_year || "—")) +
			"</dd>" +
			'<dt class="col-sm-3">' +
			escapeHtml(__("Version")) +
			'</dt><dd class="col-sm-9" data-testid="selected-plan-version">' +
			escapeHtml(String(version)) +
			"</dd>" +
			"</dl>" +
			'<div class="kt-strategy-detail__actions-group"><div class="kt-strategy-detail__actions">' +
			'<button type="button" class="btn btn-default btn-sm kt-context-action" data-testid="selected-plan-open-builder">' +
			escapeHtml(__("Manage Structure")) +
			"</button>" +
			'<button type="button" class="btn btn-default btn-sm kt-context-action" data-testid="selected-plan-review">' +
			escapeHtml(__("Review")) +
			"</button>" +
			(userCanWriteStrategicPlan()
				? '<button type="button" class="btn btn-default btn-sm kt-context-action" data-testid="selected-plan-edit-plan">' +
				  escapeHtml(__("Edit Plan Info")) +
				  "</button>"
				: "") +
			"</div></div>" +
			"</div>"
		);
	}

	function mountStructurePanelIfNeeded(host, planName) {
		if (activePlanTab !== "structure" || !planName) return;
		const mount = host.querySelector('[data-testid="strategy-structure-panel-host"]');
		if (!mount) return;
		if (typeof kentender_strategy !== "undefined" && kentender_strategy.strategy_structure_panel) {
			kentender_strategy.strategy_structure_panel.mount(mount, planName);
			structurePanelMounted = true;
		} else {
			mount.innerHTML =
				'<div class="text-muted small py-2">' + escapeHtml(__("Loading structure editor…")) + "</div>";
		}
	}

	function mountReviewPanelIfNeeded(host, selectedPlan) {
		if (activePlanTab !== "review" || !selectedPlan || !selectedPlan.name) return;
		const mount = host.querySelector('[data-testid="strategy-review-panel-host"]');
		if (!mount) return;
		if (typeof kentender_strategy !== "undefined" && kentender_strategy.strategy_review_panel) {
			kentender_strategy.strategy_review_panel.mount(mount, selectedPlan.name, selectedPlan);
		} else {
			mount.innerHTML =
				'<div class="text-muted small py-2">' + escapeHtml(__("Loading review panel…")) + "</div>";
		}
	}

	function mountAuditPanelIfNeeded(host, planName) {
		if (activePlanTab !== "audit" || !planName) return;
		const mount = host.querySelector('[data-testid="strategy-audit-panel-host"]');
		if (!mount) return;
		if (typeof kentender_strategy !== "undefined" && kentender_strategy.strategy_audit_panel) {
			kentender_strategy.strategy_audit_panel.mount(mount, planName);
		} else {
			mount.innerHTML =
				'<div class="text-muted small py-2">' + escapeHtml(__("Loading audit panel…")) + "</div>";
		}
	}

	function renderStrategyLandingContent(host, payload) {
		applyInitialWorkbenchState(payload);
		ensurePlanTab();
		const portfolio = (payload && payload.portfolio) || {};
		const plans = (payload && payload.plans) || [];
		const filtered = filterPlansBySearch(filterPlansByStatus(plans));
		const selected =
			selectedPlanName && plans.length ? findPlan(payload, selectedPlanName) : plans.length ? plans[0] : null;
		if (plans.length && selected) {
			selectedPlanName = selected.name;
		} else if (!plans.length) {
			selectedPlanName = null;
		}

		const emptyPlans = plans.length === 0;
		const emptyFiltered = !emptyPlans && filtered.length === 0;

		let listHtml = "";
		for (let i = 0; i < filtered.length; i++) {
			const p = filtered[i];
			const active = selected && p.name === selected.name ? " is-active" : "";
			const st = String(p.status || "").toLowerCase();
			listHtml +=
				'<button type="button" class="kt-strategy-plan-row' +
				active +
				'" data-strategy-plan="' +
				escapeHtml(p.name) +
				'" data-testid="strategic-plan-row-' +
				escapeHtml(p.name) +
				'">' +
				'<span class="kt-strategy-plan-row__main">' +
				'<span class="kt-strategy-plan-row__title" data-testid="strategic-plan-row-title-' +
				escapeHtml(p.name) +
				'">' +
				escapeHtml(p.strategic_plan_name || p.name) +
				"</span>" +
				'<span class="kt-strategy-plan-row__meta text-muted">' +
				escapeHtml(String(p.start_year || "—")) +
				"–" +
				escapeHtml(String(p.end_year || "—")) +
				" · " +
				'<span class="kt-strategy-inline-status kt-strategy-inline-status--' +
				escapeHtml(st) +
				'">' +
				escapeHtml(p.status || "") +
				"</span>" +
				"</span>" +
				"</span>" +
				"</button>";
		}

		let emptyHtml = "";
		if (emptyPlans) {
			emptyHtml =
				'<p class="text-muted small mb-0" data-testid="strategic-plans-empty-state">' +
				escapeHtml(__("No strategic plans yet. Create one to begin.")) +
				"</p>";
		} else if (emptyFiltered) {
			emptyHtml =
				'<p class="text-muted small mb-0" data-testid="strategic-plans-filter-empty">' +
				escapeHtml(__("No plans match the current filter.")) +
				"</p>";
		}

		let detailHtml = "";
		if (!emptyPlans && selected) {
			const py = String(selected.status || "").toLowerCase();
			const ic = selected.indicator_count != null ? selected.indicator_count : selected.objective_count;
			detailHtml =
				'<div class="kt-strategy-detail-section kt-surface" data-testid="selected-plan-panel">' +
				'<div class="kt-strategy-detail-overview">' +
				'<div class="kt-strategy-detail__hero mb-3">' +
				'<div class="kt-strategy-detail__hero-main">' +
				'<h3 class="kt-strategy-detail__title mb-1" data-testid="selected-plan-title">' +
				escapeHtml(selected.strategic_plan_name || selected.name) +
				"</h3>" +
				'<div class="text-muted" data-testid="selected-plan-meta">' +
				escapeHtml(selected.procuring_entity || "—") +
				" · " +
				escapeHtml(String(selected.start_year || "—")) +
				"–" +
				escapeHtml(String(selected.end_year || "—")) +
				" · " +
				escapeHtml(__("Version")) +
				" " +
				escapeHtml(String(selected.version_no != null ? selected.version_no : "1")) +
				"</div>" +
				'<div class="mt-2">' +
				'<span class="' +
				statusBadgeClass(selected.status) +
				'" data-kt-status="' +
				escapeHtml(py) +
				'" data-testid="selected-plan-status">' +
				escapeHtml(selected.status || "") +
				"</span> " +
				'<span class="badge badge-secondary" data-testid="selected-plan-readiness">' +
				escapeHtml(readinessLabel(selected)) +
				"</span>" +
				"</div>" +
				"</div>" +
				"</div>" +
				'<div class="kt-strategy-detail__stats mb-2">' +
				'<div class="kt-strategy-detail-stat">' +
				'<div class="kt-strategy-detail-stat__label">' +
				escapeHtml(__("Programs")) +
				"</div>" +
				'<div class="kt-strategy-detail-stat__num" data-testid="selected-plan-program-count">' +
				escapeHtml(String(selected.program_count != null ? selected.program_count : "0")) +
				"</div></div>" +
				'<div class="kt-strategy-detail-stat">' +
				'<div class="kt-strategy-detail-stat__label">' +
				escapeHtml(__("Sub-programs")) +
				"</div>" +
				'<div class="kt-strategy-detail-stat__num" data-testid="selected-plan-sub-program-count">' +
				escapeHtml(String(selected.sub_program_count != null ? selected.sub_program_count : "0")) +
				"</div></div>" +
				'<div class="kt-strategy-detail-stat">' +
				'<div class="kt-strategy-detail-stat__label">' +
				escapeHtml(__("Indicators")) +
				"</div>" +
				'<div class="kt-strategy-detail-stat__num" data-testid="selected-plan-indicator-count">' +
				escapeHtml(String(ic != null ? ic : "0")) +
				'</div></div>' +
				'<div class="kt-strategy-detail-stat">' +
				'<div class="kt-strategy-detail-stat__label">' +
				escapeHtml(__("Targets")) +
				"</div>" +
				'<div class="kt-strategy-detail-stat__num" data-testid="selected-plan-target-count">' +
				escapeHtml(String(selected.target_count != null ? selected.target_count : "0")) +
				"</div></div>" +
				"</div>" +
				renderPlanTabs() +
				renderPlanTabContent(selected) +
				"</div></div>";
		}

		host.innerHTML =
			'<div class="kt-strategy-workspace-header kt-strategy-workspace-header--compact mb-3">' +
			'<div class="d-flex justify-content-between align-items-start flex-wrap gap-2">' +
			"<div>" +
			'<p class="text-muted mb-0" data-testid="strategy-page-intro">' +
			escapeHtml(__("Define strategic plans, programs, indicators, and targets for downstream planning.")) +
			"</p>" +
			"</div>" +
			(userCanCreateStrategicPlan()
				? '<button type="button" class="btn btn-primary btn-sm kt-strategy-header-create kt-page-action-primary" data-testid="strategic-plan-create-button">' +
				  '<span aria-hidden="true">+</span> ' +
				  escapeHtml(__("New Strategic Plan")) +
				  "</button>"
				: "") +
			"</div></div>" +
			renderStatusChips(portfolio) +
			'<div class="kt-strategy-master-detail kt-strategy-master-detail--tight">' +
			'<div class="kt-strategy-col-list">' +
			'<section class="kt-strategy-section kt-surface kt-strategy-list-section" data-testid="strategic-plans-section">' +
			'<div class="kt-strategy-plan-list-head">' +
			'<h2 class="kt-strategy-section__title">' +
			escapeHtml(__("Strategic Plans")) +
			"</h2>" +
			'<input type="search" class="form-control form-control-sm kt-strategy-plan-search" placeholder="' +
			escapeHtml(__("Search plans…")) +
			'" data-testid="strategic-plan-search" value="' +
			escapeHtml(planSearchQuery) +
			'" />' +
			"</div>" +
			(emptyPlans || emptyFiltered
				? '<div class="kt-strategy-plan-list-empty">' + emptyHtml + "</div>"
				: '<div class="kt-strategy-plan-list" data-testid="strategic-plan-list">' + listHtml + "</div>") +
			"</section></div>" +
			'<div class="kt-strategy-col-detail">' +
			detailHtml +
			"</div></div>";

		if (pendingPlanListScrollTop != null) {
			const listEl = host.querySelector('[data-testid="strategic-plan-list"]');
			if (listEl) listEl.scrollTop = pendingPlanListScrollTop;
			pendingPlanListScrollTop = null;
		}

		if (selected && selected.name) {
			mountStructurePanelIfNeeded(host, selected.name);
			mountReviewPanelIfNeeded(host, selected);
			mountAuditPanelIfNeeded(host, selected.name);
		}
		scheduleStrategySidebarHighlightSync();
	}

	function switchPlanTab(tabId) {
		activePlanTab = tabId;
		saveStrategyWorkbenchState();
		const root = getVisibleWorkspacesPageRoot();
		const shell =
			(root && root.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]')) ||
			document.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]');
		if (shell && lastPayload) {
			const listEl = shell.querySelector('[data-testid="strategic-plan-list"]');
			pendingPlanListScrollTop = listEl ? listEl.scrollTop : null;
			renderStrategyLandingContent(shell, lastPayload);
		}
	}

	function rerenderLandingPreservingSearchFocus(root) {
		if (!root || !lastPayload) return;
		const search = root.querySelector('[data-testid="strategic-plan-search"]');
		const keepFocus = !!search && document.activeElement === search;
		let selectionStart = null;
		let selectionEnd = null;
		if (keepFocus) {
			selectionStart = search.selectionStart;
			selectionEnd = search.selectionEnd;
		}
		renderStrategyLandingContent(root, lastPayload);
		if (!keepFocus) return;
		const nextSearch = root.querySelector('[data-testid="strategic-plan-search"]');
		if (!nextSearch) return;
		nextSearch.focus();
		try {
			const max = String(nextSearch.value || "").length;
			const start =
				typeof selectionStart === "number" ? Math.max(0, Math.min(selectionStart, max)) : max;
			const end = typeof selectionEnd === "number" ? Math.max(start, Math.min(selectionEnd, max)) : start;
			nextSearch.setSelectionRange(start, end);
		} catch (e) {
			/* ignore unsupported input selection */
		}
	}

	function ensureStrategyDelegatedClicks(root) {
		if (!root || root.getAttribute("data-kt-strategy-delegated") === "1") return;
		root.setAttribute("data-kt-strategy-delegated", "1");

		root.addEventListener("input", function (ev) {
			const t = ev.target;
			if (t && t.matches && t.matches('[data-testid="strategic-plan-search"]')) {
				planSearchQuery = t.value || "";
				rerenderLandingPreservingSearchFocus(root);
			}
		});

		root.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!t || !t.closest) return;

			const statusChip = t.closest(".kt-strategy-status-chip[data-kt-strategy-status]");
			if (statusChip) {
				activeStatusFilter = statusChip.getAttribute("data-kt-strategy-status") || "all";
				saveStrategyWorkbenchState();
				if (lastPayload) renderStrategyLandingContent(root, lastPayload);
				return;
			}

			const planTab = t.closest(".kt-strategy-plan-tab[data-kt-strategy-plan-tab]");
			if (planTab) {
				switchPlanTab(planTab.getAttribute("data-kt-strategy-plan-tab") || "info");
				return;
			}

			const row = t.closest(".kt-strategy-plan-row[data-strategy-plan]");
			if (row) {
				const next = row.getAttribute("data-strategy-plan");
				if (next === selectedPlanName) return;
				const listEl = root.querySelector('[data-testid="strategic-plan-list"]');
				pendingPlanListScrollTop = listEl ? listEl.scrollTop : null;
				selectedPlanName = next;
				saveStrategyWorkbenchState();
				if (lastPayload) renderStrategyLandingContent(root, lastPayload);
				return;
			}

			if (t.closest("[data-testid='strategic-plan-create-button']")) {
				saveStrategyWorkbenchState();
				if (typeof kentender_strategy !== "undefined" && kentender_strategy.strategy_plan_drawer) {
					kentender_strategy.strategy_plan_drawer.openCreate(function (planName) {
						selectedPlanName = planName;
						loadStrategyLanding();
					});
				} else if (typeof frappe.new_doc === "function") {
					frappe.new_doc("Strategic Plan");
				} else {
					frappe.set_route("Form", "Strategic Plan", "new-strategic-plan");
				}
				return;
			}

			if (t.closest("[data-testid='selected-plan-open-builder']")) {
				switchPlanTab("structure");
				return;
			}

			if (t.closest("[data-testid='selected-plan-review']")) {
				switchPlanTab("review");
				return;
			}

			if (t.closest("[data-testid='selected-plan-edit-plan']")) {
				const sel = lastPayload && selectedPlanName ? findPlan(lastPayload, selectedPlanName) : null;
				if (sel && sel.name) {
					saveStrategyWorkbenchState();
					if (typeof kentender_strategy !== "undefined" && kentender_strategy.strategy_plan_drawer) {
						kentender_strategy.strategy_plan_drawer.openEdit(sel.name, function () {
							loadStrategyLanding();
						});
					} else if (typeof kentender_core !== "undefined" && kentender_core.kt_nav) {
						kentender_core.kt_nav.toForm("strategy", sel.name);
					} else {
						frappe.set_route("Form", "Strategic Plan", sel.name);
					}
				}
				return;
			}
		});
	}

	function injectStrategyShell() {
		if (strategyShellPresent()) return { ok: true, inserted: false };
		const esc = resolveWorkspaceEditorMount();
		if (!esc) return { ok: false, inserted: false };
		const wrap = document.createElement("div");
		wrap.className = "kt-strategy-injected-shell";
		wrap.setAttribute("data-testid", "strategy-landing-page");
		wrap.innerHTML =
			'<div class="text-muted small py-3">' + escapeHtml(__("Loading strategy workspace…")) + "</div>";
		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) {
			esc.insertBefore(wrap, ed);
			ed.style.display = "none";
		} else {
			esc.insertBefore(wrap, esc.firstChild);
		}
		ensureStrategyDelegatedClicks(wrap);
		return { ok: true, inserted: true, wrap: wrap };
	}

	function applyStrategyPayload(payload) {
		lastPayload = payload || { portfolio: {}, plans: [] };
		const plans = lastPayload.plans || [];
		if (plans.length && !selectedPlanName) selectedPlanName = plans[0].name;
		const root = getVisibleWorkspacesPageRoot();
		const shell =
			(root && root.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]')) ||
			document.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]');
		if (!shell) return;
		renderStrategyLandingContent(shell, lastPayload);
		ensureStrategyDelegatedClicks(shell);
	}

	function loadStrategyLanding() {
		if (!isStrategyWorkspaceRoute()) return;
		if (landingLoadInFlight) return;
		landingLoadInFlight = true;
		frappe.call({
			method: "kentender_strategy.api.landing.get_strategy_landing_data",
			callback: function (r) {
				landingLoadInFlight = false;
				if (!isStrategyWorkspaceRoute()) return;
				applyStrategyPayload((r && r.message) || { portfolio: {}, plans: [] });
			},
			error: function (r) {
				landingLoadInFlight = false;
				if (!isStrategyWorkspaceRoute()) return;
				document.querySelectorAll(".kt-strategy-injected-shell").forEach(function (el) {
					el.remove();
				});
				const exc = r && (r.exc || r._server_messages || "");
				const excStr = typeof exc === "string" ? exc : JSON.stringify(exc);
				if (
					excStr.indexOf("PermissionError") >= 0 ||
					excStr.indexOf("Not permitted") >= 0 ||
					excStr.indexOf("403") >= 0
				) {
					return;
				}
				const esc = resolveWorkspaceEditorMount();
				if (!esc) return;
				const wrap = document.createElement("div");
				wrap.className = "kt-strategy-injected-shell";
				wrap.setAttribute("data-testid", "strategy-landing-page");
				wrap.innerHTML =
					'<div class="alert alert-danger mb-0">' +
					escapeHtml(__("Unable to load strategy workspace data.")) +
					"</div>";
				const ed = document.getElementById("editorjs");
				if (ed && esc.contains(ed)) {
					esc.insertBefore(wrap, ed);
					ed.style.display = "none";
				} else {
					esc.insertBefore(wrap, esc.firstChild);
				}
			},
		});
	}

	function tryBindStrategyWorkspace() {
		if (!isStrategyWorkspaceRoute()) {
			removeStrategyLandingIfWrongRoute();
			return;
		}
		if (!userCanReadStrategicPlan()) {
			removeStrategyLandingIfWrongRoute();
			return;
		}
		syncStrategyShellClass();
		const inj = injectStrategyShell();
		if (inj && inj.ok && (inj.inserted || !lastPayload)) loadStrategyLanding();
	}

	function requestBind(delayMs) {
		if (bindScheduled) return;
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindStrategyWorkspace();
		}, delayMs || 0);
	}

	function scheduleBind() {
		if (!isStrategyWorkspaceRoute()) {
			removeStrategyLandingIfWrongRoute();
			return;
		}
		syncStrategyShellClass();
		scheduleStrategySidebarHighlightSync();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(function () {
				requestBind(0);
			});
		} else {
			requestBind(0);
		}
		requestBind(120);
		requestBind(450);
	}

	function ensureDomObserver() {
		if (workspaceDomObserver || typeof MutationObserver === "undefined") return;
		const target = document.body || document.documentElement;
		if (!target) return;
		workspaceDomObserver = new MutationObserver(function () {
			if (!isStrategyWorkspaceRoute() || strategyShellPresent()) return;
			tryBindStrategyWorkspace();
		});
		workspaceDomObserver.observe(target, { childList: true, subtree: true });
	}

	function bindHooks() {
		if (!hooksBound) {
			hooksBound = true;
			if (window.jQuery) {
				window.jQuery(document).on("page-change", scheduleBind);
				window.jQuery(document).on("app_ready", scheduleBind);
			}
			document.addEventListener("kt-strategy-structure-changed", function () {
				loadStrategyLanding();
			});
			document.addEventListener("kt-strategy-workflow-changed", function () {
				loadStrategyLanding();
			});
			if (frappe.router && frappe.router.on) frappe.router.on("change", scheduleBind);
			ensureDomObserver();
		}
		syncStrategyShellClass();
		scheduleBind();
	}

	function ensurePoll() {
		if (pollStarted) return;
		pollStarted = true;
		function tick() {
			if (!isStrategyWorkspaceRoute()) removeStrategyLandingIfWrongRoute();
			else if (!strategyShellPresent()) tryBindStrategyWorkspace();
			setTimeout(tick, 400);
		}
		tick();
	}

	function kick() {
		bindHooks();
		ensurePoll();
		setTimeout(scheduleBind, 400);
	}

	function bootstrap() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kick();
			if (typeof frappe.ready === "function") frappe.ready(kick);
		}
		whenFrappeExists();
		window.addEventListener("load", kick);
		setTimeout(kick, 900);
	}

	bootstrap();
})();
