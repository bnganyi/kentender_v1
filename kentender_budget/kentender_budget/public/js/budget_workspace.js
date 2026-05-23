// Budget Management workspace — strategy-pattern aligned shell.

frappe.provide("kentender_budget.budget_workspace");

(function () {
	const WS_LABEL = "Budget Management";
	const DETAIL_TABS = [
		{ id: "summary", label: __("Summary"), testId: "budget-tab-summary" },
		{ id: "allocations", label: __("Allocations"), testId: "budget-tab-allocations" },
		{ id: "review", label: __("Review"), testId: "budget-tab-review" },
		{ id: "audit", label: __("Audit"), testId: "budget-tab-audit" },
	];

	let bindScheduled = false;
	let hooksBound = false;
	let pollStarted = false;
	let workspaceDomObserver = null;
	let landingLoadInFlight = false;
	let lastPayload = null;
	let selectedBudgetName = null;
	let activeWorkTab = null;
	let activeDetailTab = "summary";
	let searchQuery = "";
	let stateInitialized = false;
	let currentShell = null;
	let currentList = null;
	let currentDetail = null;
	let reviewLoadToken = 0;
	const reviewCacheByBudget = Object.create(null);
	const reviewInFlightByBudget = Object.create(null);

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function workspaceNameMatchesBudget(name) {
		if (name == null || name === "") return false;
		if (name === WS_LABEL) return true;
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(WS_LABEL);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "budget-management";
	}

	function isBudgetWorkspaceRoute() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesBudget(workspaceName)) return true;
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
			if (path.includes("budget-management") || path.includes("budget%20management")) return true;
		} catch (e2) {
			/* ignore */
		}
		try {
			const route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				const w = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceNameMatchesBudget(w)) return true;
				if (w) return false;
			}
		} catch (e3) {
			return false;
		}
		return false;
	}

	function syncBudgetShellClass() {
		document.body.classList.toggle("kt-budget-shell", isBudgetWorkspaceRoute());
	}

	function removeBudgetLandingIfWrongRoute() {
		document.querySelectorAll(".kt-budget-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-budget-shell");
		selectedBudgetName = null;
		lastPayload = null;
		activeWorkTab = null;
		activeDetailTab = "summary";
		searchQuery = "";
		stateInitialized = false;
		reviewLoadToken = 0;
		currentShell = null;
		currentList = null;
		currentDetail = null;
		bindScheduled = false;
	}

	function saveBudgetWorkbenchState() {
		if (typeof kentender_core === "undefined" || !kentender_core.kt_state) return;
		kentender_core.kt_state.save("budget", {
			workTab: activeWorkTab,
			detailTab: activeDetailTab,
			searchQuery: searchQuery,
			selectedRecord: selectedBudgetName,
		});
		if (selectedBudgetName) {
			kentender_core.kt_state.setSelectedRecord("budget", selectedBudgetName);
		}
	}

	function isBudgetReadOnly(status) {
		const st = String(status || "").trim();
		return st === "Approved" || st === "Submitted";
	}

	function testIdPart(value) {
		if (value == null || value === "") return "unknown";
		return String(value).replace(/[^a-zA-Z0-9 _-]/g, "_");
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

	function budgetShellPresent() {
		const root = getVisibleWorkspacesPageRoot();
		if (!root) return false;
		return root.querySelector('.kt-budget-injected-shell[data-testid="budget-landing-page"]') != null;
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

	function userRoles() {
		return ((frappe.boot && frappe.boot.user && frappe.boot.user.roles) || []).slice();
	}

	function sessionUser() {
		return (frappe.session && frappe.session.user) || "";
	}

	function hasRole(role) {
		return userRoles().indexOf(role) >= 0;
	}

	function isStrategyManager() {
		if (sessionUser() === "Administrator") return true;
		return hasRole("Strategy Manager") || hasRole("System Manager");
	}

	function isPlanningAuthority() {
		if (sessionUser() === "Administrator") return true;
		return hasRole("Planning Authority");
	}

	function canCreateBudget() {
		if (sessionUser() === "Administrator") return true;
		const roles = userRoles();
		return roles.indexOf("System Manager") >= 0 || roles.indexOf("Strategy Manager") >= 0;
	}

	function canSubmitBudget() {
		return isStrategyManager();
	}

	function canApproveBudget() {
		return isPlanningAuthority();
	}

	function defaultWorkTab() {
		if (isPlanningAuthority() && !isStrategyManager() && sessionUser() !== "Administrator") {
			return "mywork";
		}
		if (isStrategyManager()) return "draft";
		return "all";
	}

	function initializeStateFromStore() {
		if (stateInitialized) return;
		stateInitialized = true;
		activeWorkTab = defaultWorkTab();
		activeDetailTab = "summary";
		if (typeof kentender_core !== "undefined" && kentender_core.kt_state) {
			const st = kentender_core.kt_state.restore("budget");
			if (st && st.workTab) activeWorkTab = st.workTab;
			if (st && st.detailTab) activeDetailTab = st.detailTab;
			if (st && st.searchQuery) searchQuery = String(st.searchQuery);
			const selected = kentender_core.kt_state.consumeSelectedRecord("budget");
			if (selected) selectedBudgetName = selected;
		}
	}

	function findBudget(payload, name) {
		const budgets = (payload && payload.budgets) || [];
		for (let i = 0; i < budgets.length; i++) {
			if (budgets[i].name === name) return budgets[i];
		}
		return null;
	}

	function isMyWorkBudget(b) {
		const user = sessionUser();
		const st = String(b.status || "").trim();
		if (isPlanningAuthority() && st === "Submitted") return true;
		if (isStrategyManager() && (st === "Draft" || st === "Rejected")) {
			return b.owner === user || b.created_by === user;
		}
		if (sessionUser() === "Administrator") {
			if (st === "Submitted") return true;
			if (st === "Draft" || st === "Rejected") return true;
		}
		return false;
	}

	function filterBudgetsByTab(budgets, tab) {
		const t = String(tab || "all").toLowerCase();
		if (t === "all") return budgets.slice();
		if (t === "mywork") return budgets.filter(isMyWorkBudget);
		if (t === "draft") return budgets.filter(function (b) { return b.status === "Draft"; });
		if (t === "submitted") return budgets.filter(function (b) { return b.status === "Submitted"; });
		if (t === "approved") return budgets.filter(function (b) { return b.status === "Approved"; });
		if (t === "rejected") return budgets.filter(function (b) { return b.status === "Rejected"; });
		return budgets.slice();
	}

	function tabCount(portfolio, tab) {
		const p = portfolio || {};
		const t = String(tab || "all").toLowerCase();
		if (t === "all") return (lastPayload && lastPayload.budgets && lastPayload.budgets.length) || 0;
		if (t === "mywork") {
			return filterBudgetsByTab((lastPayload && lastPayload.budgets) || [], "mywork").length;
		}
		if (t === "draft") return p.draft_count != null ? p.draft_count : 0;
		if (t === "submitted") return p.submitted_count != null ? p.submitted_count : 0;
		if (t === "approved") return p.approved_count != null ? p.approved_count : 0;
		if (t === "rejected") return p.rejected_count != null ? p.rejected_count : 0;
		return 0;
	}

	function statusKeyFromRaw(status) {
		return String(status || "")
			.trim()
			.toLowerCase();
	}

	function inlineStatusHtml(status) {
		const st = statusKeyFromRaw(status);
		return (
			'<span class="kt-budget-inline-status kt-budget-inline-status--' +
			esc(st) +
			'" data-testid="budget-row-status-inline">' +
			esc(status || "") +
			"</span>"
		);
	}

	function statusBadgeClass(status) {
		const s = statusKeyFromRaw(status);
		if (s === "draft") return "kt-budget-badge kt-budget-badge--draft";
		if (s === "submitted") return "kt-budget-badge kt-budget-badge--submitted";
		if (s === "approved") return "kt-budget-badge kt-budget-badge--approved";
		if (s === "rejected") return "kt-budget-badge kt-budget-badge--rejected";
		return "kt-budget-badge";
	}

	function editabilityBadgeClass(status) {
		return isBudgetReadOnly(status)
			? "kt-budget-badge kt-budget-badge--locked"
			: "kt-budget-badge kt-budget-badge--editable";
	}

	function editabilityLabel(status) {
		return isBudgetReadOnly(status) ? __("Locked") : __("Editable");
	}

	function compactMoney(n, currency) {
		if (n == null || n === "") return "—";
		const num = Number(n);
		if (Number.isNaN(num)) return "—";
		const cur = String(currency || "").trim();
		if (num >= 1e9) return cur + " " + (num / 1e9).toFixed(1) + "B";
		if (num >= 1e6) return cur + " " + (num / 1e6).toFixed(1) + "M";
		if (num >= 1e3) return cur + " " + (num / 1e3).toFixed(1) + "K";
		return fmtMoney(n, currency);
	}

	function formatAmount(value, digits) {
		const n = Number(value);
		if (Number.isNaN(n)) return "0";
		const precision = Number.isInteger(digits) ? digits : 2;
		return n.toLocaleString("en-US", {
			minimumFractionDigits: precision,
			maximumFractionDigits: precision,
		});
	}

	function fmtMoney(n, currency) {
		if (n == null || n === "") return "—";
		const num = Number(n);
		if (Number.isNaN(num)) return "—";
		const amount = formatAmount(num, 2);
		const cur = String(currency || "").trim();
		return cur ? cur + " " + amount : amount;
	}

	function getReviewLines(payload) {
		return (payload && payload.budget_lines) || [];
	}

	function nextStepLabel(status) {
		const st = String(status || "").trim();
		if (st === "Draft") return __("Next step: add allocations and submit for approval.");
		if (st === "Submitted") return __("Next step: review and approve or reject.");
		if (st === "Approved") return __("This budget is approved and locked.");
		if (st === "Rejected") return __("Next step: revise and resubmit.");
		return __("Next step: review readiness.");
	}

	function normalizeBudgetName(raw) {
		return String(raw || "").trim().replace(/\s+\d{10,}$/, "");
	}

	function renderStatusChips(portfolio) {
		const tabs = [
			{ id: "all", label: __("All"), testId: "budget-tab-all" },
			{ id: "mywork", label: __("My Work"), testId: "budget-tab-my-work" },
			{ id: "draft", label: __("Draft"), testId: "budget-tab-draft" },
			{ id: "submitted", label: __("Submitted"), testId: "budget-tab-submitted" },
			{ id: "approved", label: __("Approved"), testId: "budget-tab-approved" },
			{ id: "rejected", label: __("Rejected"), testId: "budget-tab-rejected" },
		];
		let html = '<div class="kt-status-filter-row" role="group">';
		for (let i = 0; i < tabs.length; i++) {
			const tab = tabs[i];
			const on = activeWorkTab === tab.id;
			const count = tabCount(portfolio, tab.id);
			const isZero = Number(count) === 0;
			html +=
				'<button type="button" class="kt-status-filter kt-budget-status-chip' +
				(on ? " is-active kt-status-filter-active" : "") +
				(isZero ? " is-zero" : "") +
				'" data-kt-budget-work-tab="' +
				esc(tab.id) +
				'" data-testid="' +
				esc(tab.testId) +
				'" aria-selected="' +
				(on ? "true" : "false") +
				'">' +
				'<span class="kt-status-filter__label">' +
				esc(tab.label) +
				'</span> <span class="kt-status-filter__count">' +
				esc(String(count)) +
				"</span></button>";
		}
		html += "</div>";
		return html;
	}

	function renderPrimaryTabs() {
		let html = '<div class="kt-primary-tabs kt-budget-detail-tabs" role="tablist">';
		for (let i = 0; i < DETAIL_TABS.length; i++) {
			const tab = DETAIL_TABS[i];
			const on = tab.id === activeDetailTab;
			html +=
				'<button type="button" class="kt-primary-tab kt-budget-tab' +
				(on ? " is-active kt-primary-tab-active" : "") +
				'" data-kt-budget-detail-tab="' +
				esc(tab.id) +
				'" data-testid="' +
				esc(tab.testId) +
				'" role="tab" aria-selected="' +
				(on ? "true" : "false") +
				'">' +
				esc(tab.label) +
				"</button>";
		}
		html += "</div>";
		return html;
	}

	function renderTabPanels() {
		let html = '<div class="kt-budget-tab-panel-wrap">';
		for (let i = 0; i < DETAIL_TABS.length; i++) {
			const tab = DETAIL_TABS[i];
			const on = tab.id === activeDetailTab;
			html +=
				'<section class="kt-budget-tab-panel' +
				(on ? " is-active" : "") +
				'" data-kt-budget-panel="' +
				esc(tab.id) +
				'" data-testid="budget-tab-panel-' +
				esc(tab.id) +
				'"><div data-testid="budget-panel-host-' +
				esc(tab.id) +
				'"></div></section>';
		}
		html += "</div>";
		return html;
	}

	function renderDetailHeader(selected, reviewPayload) {
		const st = String(selected.status || "").trim();
		const totals = (reviewPayload && reviewPayload.totals) || {};
		const cur = selected.currency || "";
		const programsFunded =
			totals && totals.programs_funded != null
				? totals.programs_funded
				: selected.budget_lines_allocated != null
					? selected.budget_lines_allocated
					: 0;
		return (
			'<section class="kt-budget-detail-section kt-surface" data-testid="selected-budget-panel">' +
			'<div class="kt-budget-detail-overview">' +
			'<header class="kt-budget-detail__hero">' +
			'<div class="kt-budget-detail__hero-main">' +
			'<h2 class="kt-budget-detail__title" data-testid="selected-budget-title">' +
			esc(normalizeBudgetName(selected.budget_name || selected.name)) +
			"</h2>" +
			'<div class="text-muted" data-testid="selected-budget-meta">' +
			esc(selected.fiscal_year || "—") +
			" · " +
			esc(selected.strategic_plan_title || selected.strategic_plan || "—") +
			" · " +
			esc(cur || "—") +
			"</div>" +
			'<div class="kt-budget-status-guidance mt-2">' +
			'<span class="' +
			statusBadgeClass(st) +
			'" data-testid="selected-budget-status-badge">' +
			esc(st) +
			'</span> <span class="' +
			editabilityBadgeClass(st) +
			'" data-testid="selected-budget-editability-badge">' +
			esc(editabilityLabel(st)) +
			'</span><span class="kt-budget-next-step-inline text-muted small">' +
			esc(nextStepLabel(st)) +
			"</span></div>" +
			"</div>" +
			'<div class="kt-budget-detail__hero-actions" data-testid="selected-budget-actions">' +
			renderStateActions(selected) +
			"</div>" +
			"</header>" +
			(isBudgetReadOnly(st)
				? '<div class="alert alert-info py-2 mb-2 kt-budget-builder-lock-banner" data-testid="budget-builder-readonly-banner">' +
					esc(st === "Approved" ? __("This budget is approved and locked.") : __("This budget is submitted and awaiting approval.")) +
					"</div>"
				: "") +
			(st === "Rejected" && (selected.rejection_reason || "")
				? '<div class="alert alert-danger py-2 mb-2" data-testid="budget-rejection-summary">' +
					esc(__("This budget was rejected.")) +
					" " +
					esc(selected.rejection_reason || "") +
					"</div>"
				: "") +
			'<div class="kt-budget-detail__stats">' +
			'<div class="kt-budget-detail-stat"><div class="kt-budget-detail-stat__label">' +
			esc(__("Total")) +
			'</div><div class="kt-budget-detail-stat__num" data-testid="selected-budget-total">' +
			esc(fmtMoney(totals.total_budget_amount != null ? totals.total_budget_amount : selected.total_budget_amount, cur)) +
			"</div></div>" +
			'<div class="kt-budget-detail-stat"><div class="kt-budget-detail-stat__label">' +
			esc(__("Allocated")) +
			'</div><div class="kt-budget-detail-stat__num" data-testid="selected-budget-allocated">' +
			esc(fmtMoney(totals.allocated_sum != null ? totals.allocated_sum : selected.allocated_amount, cur)) +
			"</div></div>" +
			'<div class="kt-budget-detail-stat"><div class="kt-budget-detail-stat__label">' +
			esc(__("Remaining")) +
			'</div><div class="kt-budget-detail-stat__num" data-testid="selected-budget-remaining">' +
			esc(fmtMoney(totals.remaining_amount != null ? totals.remaining_amount : selected.remaining_amount, cur)) +
			"</div></div>" +
			'<div class="kt-budget-detail-stat"><div class="kt-budget-detail-stat__label">' +
			esc(__("Programs funded")) +
			'</div><div class="kt-budget-detail-stat__num" data-testid="budget-programs-funded">' +
			esc(String(programsFunded || 0)) +
			"</div></div>" +
			"</div>" +
			renderPrimaryTabs() +
			renderTabPanels() +
			"</div></section>"
		);
	}

	function renderStateActions(selected) {
		const st = String(selected.status || "").trim();
		const actions = [];
		if ((st === "Draft" || st === "Rejected") && canSubmitBudget()) {
			actions.push(
				'<button type="button" class="btn btn-default btn-sm kt-context-action" data-testid="selected-budget-edit">' +
					esc(__("Edit Budget Info")) +
					"</button>",
			);
		} else if (st === "Approved") {
			actions.push(
				'<button type="button" class="btn btn-default btn-sm kt-context-action" data-testid="selected-budget-view-audit">' +
					esc(__("View Audit")) +
					"</button>",
			);
		}
		return actions.join("");
	}

	function renderRowList(filtered, selected) {
		if (!filtered.length) {
			return '<div class="kt-budget-plan-list-empty"><p class="text-muted small mb-0" data-testid="budget-tab-empty-state">' + esc(__("No budgets in this queue.")) + "</p></div>";
		}
		let html = "";
		for (let i = 0; i < filtered.length; i++) {
			const b = filtered[i];
			const on = selected && selected.name === b.name;
			const programCount = b.budget_lines_allocated != null ? b.budget_lines_allocated : 0;
			const programLabel = programCount === 1 ? __("program") : __("programs");
			const amountLine = compactMoney(b.allocated_amount, b.currency) + " · " + programCount + " " + programLabel;
			const planLine = b.strategic_plan_title || b.strategic_plan || "";
			html +=
				'<button type="button" class="kt-budget-row' +
				(on ? " is-active" : "") +
				'" data-budget="' +
				esc(b.name) +
				'" data-budget-name="' +
				esc(b.name) +
				'" data-testid="budget-row-' +
				esc(testIdPart(b.name)) +
				'"><span class="kt-budget-row__main"><span class="kt-budget-row__title">' +
				esc(normalizeBudgetName(b.budget_name || b.name)) +
				'</span><span class="kt-budget-row__meta text-muted small">' +
				esc(b.fiscal_year || "—") +
				" · " +
				inlineStatusHtml(b.status) +
				'</span><span class="kt-budget-row__meta text-muted small">' +
				esc(amountLine) +
				"</span>" +
				(planLine
					? '<span class="kt-budget-row__meta text-muted small">' + esc(planLine) + "</span>"
					: "") +
				"</span></button>";
		}
		return '<div class="kt-budget-row-list" data-testid="budget-list">' + html + "</div>";
	}

	function filterBudgets(payload) {
		const source = filterBudgetsByTab((payload && payload.budgets) || [], activeWorkTab);
		const q = String(searchQuery || "").trim().toLowerCase();
		if (!q) return source;
		return source.filter(function (b) {
			const n = String(b.budget_name || b.name || "").toLowerCase();
			const fy = String(b.fiscal_year || "").toLowerCase();
			const st = String(b.status || "").toLowerCase();
			return n.indexOf(q) >= 0 || fy.indexOf(q) >= 0 || st.indexOf(q) >= 0;
		});
	}

	function ensureSelectedBudget(payload, filtered) {
		if (!filtered.length) {
			selectedBudgetName = null;
			return null;
		}
		let selected = selectedBudgetName ? findBudget(payload, selectedBudgetName) : null;
		if (!selected || filtered.every(function (b) { return b.name !== selected.name; })) {
			selected = filtered[0];
		}
		selectedBudgetName = selected ? selected.name : null;
		return selected;
	}

	function ensureShell(root) {
		if (!root) return null;
		if (!currentShell || !currentShell.isConnected) {
			currentShell =
				root.querySelector('.kt-budget-injected-shell[data-testid="budget-landing-page"]') ||
				document.querySelector('.kt-budget-injected-shell[data-testid="budget-landing-page"]');
		}
		if (currentShell) return currentShell;
		const esc = resolveWorkspaceEditorMount();
		if (!esc) return null;
		const wrap = document.createElement("div");
		wrap.className = "kt-budget-injected-shell kt-budget-review-shell";
		wrap.setAttribute("data-testid", "budget-landing-page");
		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) {
			esc.insertBefore(wrap, ed);
			ed.style.display = "none";
		} else {
			esc.insertBefore(wrap, esc.firstChild);
		}
		currentShell = wrap;
		return wrap;
	}

	function mountPanel(panelId, host, selected, reviewPayload) {
		const ctx = {
			selected: selected,
			reviewPayload: reviewPayload,
			canEditBudget: canSubmitBudget() && !isBudgetReadOnly(selected.status),
			canSubmitBudget: canSubmitBudget(),
			canApproveBudget: canApproveBudget(),
			isBudgetReadOnly: isBudgetReadOnly,
			formatMoney: fmtMoney,
			nextStepLabel: nextStepLabel,
		};
		if (panelId === "summary" && kentender_budget.budget_summary_panel) {
			kentender_budget.budget_summary_panel.mount(host, ctx);
			return;
		}
		if (panelId === "allocations" && kentender_budget.budget_allocations_panel) {
			kentender_budget.budget_allocations_panel.mount(host, ctx);
			return;
		}
		if (panelId === "review" && kentender_budget.budget_review_panel) {
			kentender_budget.budget_review_panel.mount(host, ctx);
			return;
		}
		if (panelId === "audit" && kentender_budget.budget_audit_panel) {
			kentender_budget.budget_audit_panel.mount(host, ctx);
			return;
		}
		host.innerHTML = '<div class="text-muted small py-2">' + esc(__("Loading…")) + "</div>";
	}

	function setTabVisibility() {
		if (!currentDetail) return;
		const tabButtons = currentDetail.querySelectorAll("[data-kt-budget-detail-tab]");
		for (let i = 0; i < tabButtons.length; i++) {
			const el = tabButtons[i];
			const on = el.getAttribute("data-kt-budget-detail-tab") === activeDetailTab;
			el.classList.toggle("is-active", on);
			el.classList.toggle("kt-primary-tab-active", on);
			el.setAttribute("aria-selected", on ? "true" : "false");
		}
		const panels = currentDetail.querySelectorAll(".kt-budget-tab-panel");
		for (let i = 0; i < panels.length; i++) {
			const panel = panels[i];
			const on = panel.getAttribute("data-kt-budget-panel") === activeDetailTab;
			panel.classList.toggle("is-active", on);
		}
	}

	function ensureReviewData(budgetName, callback) {
		if (!budgetName) {
			callback(null);
			return;
		}
		if (reviewCacheByBudget[budgetName]) {
			callback(reviewCacheByBudget[budgetName]);
			return;
		}
		if (reviewInFlightByBudget[budgetName]) {
			reviewInFlightByBudget[budgetName].push(callback);
			return;
		}
		reviewInFlightByBudget[budgetName] = [callback];
		const token = ++reviewLoadToken;
		frappe.call({
			method: "kentender_budget.api.review.get_budget_review_data",
			args: { budget_name: budgetName },
			callback: function (r) {
				if (!isBudgetWorkspaceRoute() || token !== reviewLoadToken) return;
				const payload = (r && r.message) || null;
				if (payload) reviewCacheByBudget[budgetName] = payload;
				const waiters = reviewInFlightByBudget[budgetName] || [];
				delete reviewInFlightByBudget[budgetName];
				for (let i = 0; i < waiters.length; i++) waiters[i](payload);
			},
			error: function () {
				const waiters = reviewInFlightByBudget[budgetName] || [];
				delete reviewInFlightByBudget[budgetName];
				for (let i = 0; i < waiters.length; i++) waiters[i](null);
			},
		});
	}

	function updatePanels(selected) {
		if (!currentDetail || !selected) return;
		const reviewPayload = reviewCacheByBudget[selected.name] || null;
		for (let i = 0; i < DETAIL_TABS.length; i++) {
			const tab = DETAIL_TABS[i];
			const host = currentDetail.querySelector('[data-testid="budget-panel-host-' + tab.id + '"]');
			if (!host) continue;
			mountPanel(tab.id, host, selected, reviewPayload);
		}
		setTabVisibility();
		if (!reviewPayload) {
			ensureReviewData(selected.name, function () {
				if (!lastPayload || selected.name !== selectedBudgetName) return;
				const nextSelected = findBudget(lastPayload, selectedBudgetName);
				if (nextSelected) updatePanels(nextSelected);
			});
		}
	}

	function renderWorkspace(payload) {
		const root = getVisibleWorkspacesPageRoot();
		if (!root) return;
		const shell = ensureShell(root);
		if (!shell) return;
		const filtered = filterBudgets(payload);
		const selected = ensureSelectedBudget(payload, filtered);
		shell.innerHTML =
			'<div class="kt-budget-workspace-header kt-budget-workspace-header--compact">' +
			'<div class="kt-budget-header-row">' +
			'<div><h1 class="h4 kt-budget-page-title" data-testid="budget-page-title">' +
			esc(WS_LABEL) +
			'</h1><p class="text-muted kt-budget-page-intro" data-testid="budget-page-intro">' +
			esc(__("Create, review, approve, and manage strategy-linked budget allocations.")) +
			"</p></div>" +
			(canCreateBudget()
				? '<button type="button" class="btn btn-primary btn-sm kt-page-action-primary" data-testid="budget-create-button"><span aria-hidden="true">+</span> ' +
					esc(__("New Budget")) +
					"</button>"
				: "") +
			"</div>" +
			'<div class="kt-budget-status-chips" data-testid="budget-status-chips">' +
			renderStatusChips(payload.portfolio || {}) +
			"</div>" +
			"</div>" +
			'<div class="kt-budget-master-detail">' +
			'<div class="kt-budget-col-list"><section class="kt-budget-section kt-surface kt-budget-list-section">' +
			'<div class="kt-budget-list-head" data-testid="budget-list-head"><h2 class="kt-budget-section__title">' +
			esc(__("Budgets")) +
			'</h2><input type="search" class="form-control form-control-sm kt-budget-list-search" data-testid="budget-search" placeholder="' +
			esc(__("Search budgets…")) +
			'" value="' +
			esc(searchQuery) +
			'"/></div>' +
			renderRowList(filtered, selected) +
			"</section></div>" +
			'<div class="kt-budget-col-detail" data-testid="budget-detail-col">' +
			(selected ? renderDetailHeader(selected, reviewCacheByBudget[selected.name] || null) : '<div class="kt-budget-section kt-surface"><p class="text-muted mb-0" data-testid="budget-review-empty-tab">' + esc(__("Select a budget to view details.")) + "</p></div>") +
			"</div></div>";
		currentShell = shell;
		currentList = shell.querySelector('[data-testid="budget-list"]');
		currentDetail = shell.querySelector('[data-testid="budget-detail-col"]');
		if (selected) updatePanels(selected);
		saveBudgetWorkbenchState();
	}

	function loadBudgetLanding(force) {
		if (!isBudgetWorkspaceRoute()) return;
		if (landingLoadInFlight) return;
		if (!force && lastPayload && budgetShellPresent()) return;
		landingLoadInFlight = true;
		frappe.call({
			method: "kentender_budget.api.landing.get_budget_landing_data",
			callback: function (r) {
				landingLoadInFlight = false;
				if (!isBudgetWorkspaceRoute()) return;
				lastPayload = (r && r.message) || { portfolio: {}, budgets: [] };
				renderWorkspace(lastPayload);
			},
			error: function (r) {
				landingLoadInFlight = false;
				document.querySelectorAll(".kt-budget-injected-shell").forEach(function (el) {
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
				const host = ensureShell(getVisibleWorkspacesPageRoot());
				if (!host) return;
				const wrap = document.createElement("div");
				wrap.className = "kt-budget-injected-shell";
				wrap.innerHTML =
					'<div class="alert alert-danger mb-0">' + esc(__("Unable to load budget workspace data.")) + "</div>";
				host.innerHTML = wrap.innerHTML;
			},
		});
	}

	function tryBindBudgetWorkspace() {
		if (!isBudgetWorkspaceRoute()) {
			removeBudgetLandingIfWrongRoute();
			return;
		}
		syncBudgetShellClass();
		initializeStateFromStore();
		if (!ensureShell(getVisibleWorkspacesPageRoot())) return;
		if (!lastPayload) {
			loadBudgetLanding(true);
		}
	}

	function requestBind(delayMs) {
		if (bindScheduled) return;
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindBudgetWorkspace();
		}, delayMs || 0);
	}

	function scheduleBind() {
		if (!isBudgetWorkspaceRoute()) {
			removeBudgetLandingIfWrongRoute();
			return;
		}
		syncBudgetShellClass();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(function () { requestBind(0); });
		} else {
			requestBind(0);
		}
		requestBind(120);
		requestBind(450);
		requestBind(950);
	}

	function ensureDomObserver() {
		if (workspaceDomObserver || typeof MutationObserver === "undefined") return;
		const target = document.body || document.documentElement;
		if (!target) return;
		workspaceDomObserver = new MutationObserver(function () {
			if (!isBudgetWorkspaceRoute() || budgetShellPresent()) return;
			tryBindBudgetWorkspace();
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
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", scheduleBind);
			}
			ensureDomObserver();
			document.addEventListener("kt-budget-panel-changed", function (ev) {
				const budgetName =
					(ev && ev.detail && ev.detail.budget_name) || selectedBudgetName;
				if (budgetName) {
					delete reviewCacheByBudget[budgetName];
					if (
						kentender_budget.budget_audit_panel &&
						typeof kentender_budget.budget_audit_panel.invalidate === "function"
					) {
						kentender_budget.budget_audit_panel.invalidate(budgetName);
					}
				}
				loadBudgetLanding(true);
			});
			document.addEventListener("kt-budget-workflow-changed", function (ev) {
				const budgetName =
					(ev && ev.detail && ev.detail.budget_name) || selectedBudgetName;
				if (budgetName) {
					delete reviewCacheByBudget[budgetName];
					if (
						kentender_budget.budget_audit_panel &&
						typeof kentender_budget.budget_audit_panel.invalidate === "function"
					) {
						kentender_budget.budget_audit_panel.invalidate(budgetName);
					}
				}
				loadBudgetLanding(true);
			});
		}
		syncBudgetShellClass();
		scheduleBind();
	}

	function ensurePoll() {
		if (pollStarted) return;
		pollStarted = true;
		function tick() {
			if (!isBudgetWorkspaceRoute()) removeBudgetLandingIfWrongRoute();
			else if (!budgetShellPresent() && resolveWorkspaceEditorMount()) tryBindBudgetWorkspace();
			setTimeout(tick, 400);
		}
		tick();
	}

	function kick() {
		bindHooks();
		ensurePoll();
		setTimeout(scheduleBind, 400);
	}

	function openCreateDialog() {
		const d = new frappe.ui.Dialog({
			title: __("New Budget"),
			fields: [
				{ fieldname: "budget_name", label: __("Budget name"), fieldtype: "Data", reqd: 1 },
				{ fieldname: "strategic_plan", label: __("Strategic plan"), fieldtype: "Link", options: "Strategic Plan", reqd: 1 },
				{ fieldname: "procuring_entity", label: __("Procuring entity"), fieldtype: "Link", options: "Procuring Entity", reqd: 1 },
				{ fieldname: "fiscal_year", label: __("Fiscal year"), fieldtype: "Int", reqd: 1 },
				{ fieldname: "currency", label: __("Currency"), fieldtype: "Link", options: "Currency", reqd: 1, default: "KES" },
				{ fieldname: "total_budget_amount", label: __("Total budget amount"), fieldtype: "Currency", reqd: 1 },
				{ fieldname: "notes", label: __("Notes"), fieldtype: "Small Text" },
			],
			primary_action_label: __("Create Budget"),
			primary_action: function (values) {
				frappe.call({
					method: "frappe.client.insert",
					args: {
						doc: {
							doctype: "Budget",
							budget_name: values.budget_name,
							strategic_plan: values.strategic_plan,
							procuring_entity: values.procuring_entity,
							fiscal_year: values.fiscal_year,
							currency: values.currency,
							total_budget_amount: values.total_budget_amount,
							notes: values.notes || "",
						},
					},
					callback: function (r) {
						if (!r || !r.message || !r.message.name) return;
						selectedBudgetName = r.message.name;
						activeDetailTab = "allocations";
						if (typeof kentender_core !== "undefined" && kentender_core.kt_state) {
							kentender_core.kt_state.save("budget", {
								selectedRecord: r.message.name,
								detailTab: "allocations",
							});
						}
						d.hide();
						loadBudgetLanding(true);
					},
				});
			},
		});
		d.show();
	}

	function bindInteractions() {
		document.addEventListener("click", function (ev) {
			if (!isBudgetWorkspaceRoute() || !lastPayload) return;
			const t = ev.target;
			if (!t || !t.closest) return;

			const statusChip = t.closest("[data-kt-budget-work-tab]");
			if (statusChip) {
				activeWorkTab = statusChip.getAttribute("data-kt-budget-work-tab") || "all";
				renderWorkspace(lastPayload);
				return;
			}

			const row = t.closest(".kt-budget-row[data-budget]");
			if (row) {
				selectedBudgetName = row.getAttribute("data-budget");
				renderWorkspace(lastPayload);
				return;
			}

			const detailTab = t.closest("[data-kt-budget-detail-tab]");
			if (detailTab) {
				activeDetailTab = detailTab.getAttribute("data-kt-budget-detail-tab") || "summary";
				setTabVisibility();
				const selected = selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (selected) updatePanels(selected);
				saveBudgetWorkbenchState();
				return;
			}

			if (t.closest("[data-testid='budget-create-button']")) {
				openCreateDialog();
				return;
			}
			if (t.closest("[data-testid='selected-budget-view-audit']")) {
				activeDetailTab = "audit";
				setTabVisibility();
				const selected = selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (selected) updatePanels(selected);
				saveBudgetWorkbenchState();
				return;
			}
			if (t.closest("[data-testid='selected-budget-edit']")) {
				const selected = selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (
					selected &&
					selected.name &&
					kentender_budget.budget_metadata_drawer
				) {
					kentender_budget.budget_metadata_drawer.openEdit(selected.name, function () {
						loadBudgetLanding(true);
					});
				}
				return;
			}
		});

		document.addEventListener("input", function (ev) {
			if (!isBudgetWorkspaceRoute() || !lastPayload) return;
			const t = ev.target;
			if (!t || !t.matches) return;
			if (t.matches('[data-testid="budget-search"]')) {
				searchQuery = t.value || "";
				renderWorkspace(lastPayload);
			}
		});
	}

	function bootstrap() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kick();
			if (typeof frappe.ready === "function") {
				frappe.ready(kick);
			}
		}
		whenFrappeExists();
		bindInteractions();
		window.addEventListener("load", kick);
		setTimeout(kick, 900);
	}

	bootstrap();
})();
