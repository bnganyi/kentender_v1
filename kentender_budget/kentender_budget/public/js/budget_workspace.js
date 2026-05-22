// Budget Management — Review workbench (allocation-focused landing; builder is separate route).

(function () {
	const WS_LABEL = "Budget Management";
	const STORAGE_SELECT_BUDGET = "kt_budget_workspace_select";

	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;
	let lastPayload = null;
	let selectedBudgetName = null;
	let lastReviewPayload = null;
	let drawerLineName = null;
	let reviewLoadToken = 0;
	let landingLoadInFlight = false;
	let reviewLoadError = null;
	let activeWorkTab = null;
	let workTabInitialized = false;

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
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
		lastReviewPayload = null;
		drawerLineName = null;
		reviewLoadToken = 0;
		activeWorkTab = null;
		workTabInitialized = false;
		bindScheduled = false;
	}

	function consumeStoredBudgetSelection() {
		if (typeof kentender_core !== "undefined" && kentender_core.kt_state) {
			const fromKt = kentender_core.kt_state.consumeSelectedRecord("budget");
			if (fromKt) return fromKt;
		}
		try {
			const v = sessionStorage.getItem(STORAGE_SELECT_BUDGET);
			if (v) {
				sessionStorage.removeItem(STORAGE_SELECT_BUDGET);
				return v;
			}
		} catch (e) {
			/* ignore */
		}
		return null;
	}

	function saveBudgetWorkbenchState() {
		if (typeof kentender_core === "undefined" || !kentender_core.kt_state) return;
		kentender_core.kt_state.save("budget", {
			workTab: activeWorkTab,
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

	function formatReferenceDisplay(label, code) {
		const cleanLabel = String(label || "").trim();
		const cleanCode = String(code || "").trim();
		if (!cleanLabel && !cleanCode) return "—";
		if (!cleanCode) return cleanLabel || "—";
		return cleanLabel + " (" + cleanCode + ")";
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

	function ensureWorkTab() {
		if (!workTabInitialized) {
			if (typeof kentender_core !== "undefined" && kentender_core.kt_state) {
				const st = kentender_core.kt_state.restore("budget");
				if (st && st.workTab) {
					activeWorkTab = st.workTab;
				} else {
					activeWorkTab = defaultWorkTab();
				}
			} else {
				activeWorkTab = defaultWorkTab();
			}
			workTabInitialized = true;
		}
		if (!activeWorkTab) activeWorkTab = "all";
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

	function statusBadgeClass(status) {
		const s = String(status || "").trim().toLowerCase();
		if (s === "draft") return "kt-budget-badge kt-budget-badge--draft";
		if (s === "submitted") return "kt-budget-badge kt-budget-badge--submitted";
		if (s === "approved") return "kt-budget-badge kt-budget-badge--approved";
		if (s === "rejected") return "kt-budget-badge kt-budget-badge--rejected";
		return "kt-budget-badge";
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

	function findReviewLine(payload, name) {
		const lines = getReviewLines(payload);
		for (let i = 0; i < lines.length; i++) {
			if (lines[i].name === name) return lines[i];
		}
		return null;
	}

	function resetReviewForBudget(budgetName) {
		if (!lastReviewPayload || !lastReviewPayload.budget) {
			drawerLineName = null;
			return;
		}
		if (lastReviewPayload.budget.name !== budgetName) {
			lastReviewPayload = null;
			drawerLineName = null;
		}
	}

	function renderWorkTabs(portfolio) {
		ensureWorkTab();
		const tabs = [
			{ id: "all", label: __("All"), testId: "budget-tab-all" },
			{ id: "mywork", label: __("My Work"), testId: "budget-tab-my-work" },
			{ id: "draft", label: __("Draft"), testId: "budget-tab-draft" },
			{ id: "submitted", label: __("Submitted"), testId: "budget-tab-submitted" },
			{ id: "approved", label: __("Approved"), testId: "budget-tab-approved" },
			{ id: "rejected", label: __("Rejected"), testId: "budget-tab-rejected" },
		];
		let html =
			'<div class="kt-budget-work-tabs mb-2" role="tablist" data-testid="budget-work-tabs">' +
			'<div class="btn-group btn-group-sm flex-wrap kt-budget-tab-group" role="group">';
		for (let i = 0; i < tabs.length; i++) {
			const tab = tabs[i];
			const on = activeWorkTab === tab.id;
			const count = tabCount(portfolio, tab.id);
			html +=
				'<button type="button" class="btn ' +
				(on ? "btn-primary" : "btn-default") +
				' kt-budget-work-tab" data-kt-budget-tab="' +
				escapeHtml(tab.id) +
				'" data-testid="' +
				escapeHtml(tab.testId) +
				'" role="tab" aria-selected="' +
				(on ? "true" : "false") +
				'">' +
				escapeHtml(tab.label) +
				' <span class="badge badge-light">' +
				escapeHtml(String(count)) +
				"</span></button>";
		}
		html += "</div></div>";
		return html;
	}

	function renderAllocationsTable(lines, currency) {
		const cur = String(currency || "KES").trim() || "KES";
		if (!lines || !lines.length) {
			return (
				'<div class="text-muted small py-2" data-testid="budget-allocations-empty">' +
				escapeHtml(__("No program allocations yet.")) +
				"</div>"
			);
		}
		let rows = "";
		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];
			const idPart = testIdPart(line.budget_line_name || line.name);
			const programDisplay = formatReferenceDisplay(line.program_label, line.program_code);
			const notesSnippet = String(line.notes || "").trim();
			const notesCell = notesSnippet
				? escapeHtml(notesSnippet.length > 80 ? notesSnippet.slice(0, 77) + "…" : notesSnippet)
				: '<span class="text-muted">—</span>';
			rows +=
				'<tr class="kt-budget-allocation-row" data-budget-line="' +
				escapeHtml(line.name) +
				'" data-testid="budget-allocation-row-' +
				escapeHtml(idPart) +
				'" tabindex="0" role="button">' +
				'<td><span class="kt-budget-allocation-program">' +
				escapeHtml(programDisplay) +
				"</span></td>" +
				'<td class="text-right" data-testid="budget-allocation-amount-' +
				escapeHtml(idPart) +
				'">' +
				escapeHtml(cur) +
				" " +
				escapeHtml(formatAmount(line.amount_allocated, 2)) +
				"</td>" +
				'<td class="kt-budget-allocation-notes small text-muted">' +
				notesCell +
				"</td></tr>";
		}
		return (
			'<div class="kt-budget-allocations-wrap kt-surface">' +
			'<h3 class="kt-budget-section__title">' +
			escapeHtml(__("Program allocations")) +
			"</h3>" +
			'<table class="table table-sm table-hover mb-0 kt-budget-allocations-table" data-testid="budget-allocations-table">' +
			"<thead><tr>" +
			"<th>" +
			escapeHtml(__("Program")) +
			"</th>" +
			'<th class="text-right">' +
			escapeHtml(__("Allocated")) +
			"</th>" +
			"<th>" +
			escapeHtml(__("Notes")) +
			"</th></tr></thead><tbody>" +
			rows +
			"</tbody></table></div>"
		);
	}

	function renderAllocationDrawer(line, currency, open) {
		if (!line || !open) return "";
		const contextHtml =
			'<details class="kt-budget-drawer-details">' +
			'<summary class="small font-weight-bold">' +
			escapeHtml(__("Strategic context")) +
			"</summary>" +
			'<div class="kt-budget-inspect-grid small pt-2">' +
			"<div><span class=\"text-muted\">" +
			escapeHtml(__("Sub-program")) +
			"</span><div>" +
			escapeHtml(formatReferenceDisplay(line.sub_program_label, line.sub_program_code)) +
			"</div></div>" +
			"<div><span class=\"text-muted\">" +
			escapeHtml(__("Output indicator")) +
			"</span><div>" +
			escapeHtml(formatReferenceDisplay(line.output_indicator_label, line.output_indicator_code)) +
			"</div></div>" +
			"<div><span class=\"text-muted\">" +
			escapeHtml(__("Performance target")) +
			"</span><div>" +
			escapeHtml(formatReferenceDisplay(line.performance_target_label, line.performance_target_code)) +
			"</div></div></div></details>";

		return (
			'<div class="kt-budget-allocation-drawer kt-surface" data-testid="budget-allocation-drawer">' +
			'<div class="kt-budget-allocation-drawer__header">' +
			'<h3 class="h6 mb-1" data-testid="budget-line-editor-title">' +
			escapeHtml(line.budget_line_name || line.name) +
			"</h3>" +
			'<button type="button" class="btn btn-xs btn-default" data-testid="budget-allocation-drawer-close" aria-label="' +
			escapeHtml(__("Close")) +
			'">&times;</button></div>' +
			'<div class="kt-budget-section kt-budget-allocation-drawer__body" data-testid="budget-allocation-editor">' +
			'<div class="mb-2"><span class="text-muted small">' +
			escapeHtml(__("Program")) +
			"</span><div>" +
			escapeHtml(formatReferenceDisplay(line.program_label, line.program_code)) +
			"</div></div>" +
			'<div class="mb-2"><span class="text-muted small">' +
			escapeHtml(__("Allocated")) +
			"</span><div>" +
			escapeHtml(fmtMoney(line.amount_allocated, currency)) +
			"</div></div>" +
			(line.notes
				? '<div class="mb-2"><span class="text-muted small">' +
					escapeHtml(__("Notes")) +
					"</span><div class=\"small\">" +
					escapeHtml(line.notes) +
					"</div></div>"
				: "") +
			contextHtml +
			"</div></div>"
		);
	}

	function renderReviewActions(selected) {
		const st = String(selected.status || "").trim();
		const readOnly = isBudgetReadOnly(st);
		const parts = [];

		if (st === "Draft" || st === "Rejected") {
			if (canSubmitBudget()) {
				parts.push(
					'<button type="button" class="btn btn-primary btn-sm" data-testid="selected-budget-open-builder">' +
						escapeHtml(__("Manage Allocations")) +
						"</button>",
				);
				parts.push(
					'<button type="button" class="btn btn-default btn-sm" data-testid="selected-budget-edit">' +
						escapeHtml(__("Edit budget")) +
						"</button>",
				);
				parts.push(
					'<button type="button" class="btn btn-default btn-sm" data-testid="budget-submit-approval">' +
						escapeHtml(__("Submit for approval")) +
						"</button>",
				);
			}
		} else if (st === "Submitted") {
			parts.push(
				'<button type="button" class="btn btn-default btn-sm" data-testid="selected-budget-open-builder">' +
					escapeHtml(__("Manage Allocations")) +
					"</button>",
			);
			if (canApproveBudget()) {
				parts.push(
					'<button type="button" class="btn btn-primary btn-sm" data-testid="budget-approve">' +
						escapeHtml(__("Approve")) +
						"</button>",
				);
				parts.push(
					'<button type="button" class="btn btn-default btn-sm" data-testid="budget-reject">' +
						escapeHtml(__("Reject")) +
						"</button>",
				);
			}
		} else if (st === "Approved") {
			parts.push(
				'<button type="button" class="btn btn-default btn-sm" data-testid="selected-budget-open-builder">' +
					escapeHtml(__("Manage Allocations")) +
					"</button>",
			);
		}

		if (!parts.length) return "";
		return (
			'<div class="kt-budget-workspace-main__actions" data-testid="selected-budget-actions">' +
			parts.join("") +
			"</div>"
		);
	}

	function renderMetricsStrip(selected, totals, cur) {
		const programsFunded =
			totals && totals.programs_funded != null
				? totals.programs_funded
				: selected.budget_lines_allocated != null
					? selected.budget_lines_allocated
					: 0;
		const total = totals.total_budget_amount != null ? totals.total_budget_amount : selected.total_budget_amount;
		const allocated = totals.allocated_sum != null ? totals.allocated_sum : selected.allocated_amount;
		const remaining = totals.remaining_amount != null ? totals.remaining_amount : selected.remaining_amount;

		return (
			'<div class="kt-budget-metrics-strip kt-surface">' +
			'<div class="kt-budget-inspect-metric">' +
			'<span class="kt-budget-inspect-metric__label">' +
			escapeHtml(__("Total")) +
			'</span><span class="kt-budget-inspect-metric__value kt-budget-money" data-testid="selected-budget-total">' +
			escapeHtml(fmtMoney(total, cur)) +
			"</span></div>" +
			'<div class="kt-budget-inspect-metric">' +
			'<span class="kt-budget-inspect-metric__label">' +
			escapeHtml(__("Allocated")) +
			'</span><span class="kt-budget-inspect-metric__value kt-budget-money" data-testid="selected-budget-allocated">' +
			escapeHtml(fmtMoney(allocated, cur)) +
			'</span><span class="kt-budget-sr-only" data-testid="budget-builder-allocated">' +
			escapeHtml(fmtMoney(allocated, cur)) +
			"</span></div>" +
			'<div class="kt-budget-inspect-metric">' +
			'<span class="kt-budget-inspect-metric__label">' +
			escapeHtml(__("Remaining")) +
			'</span><span class="kt-budget-inspect-metric__value kt-budget-money" data-testid="selected-budget-remaining">' +
			escapeHtml(fmtMoney(remaining, cur)) +
			'</span><span class="kt-budget-sr-only" data-testid="budget-builder-remaining">' +
			escapeHtml(fmtMoney(remaining, cur)) +
			"</span></div>" +
			'<div class="kt-budget-inspect-metric">' +
			'<span class="kt-budget-inspect-metric__label">' +
			escapeHtml(__("Programs funded")) +
			'</span><span class="kt-budget-inspect-metric__value" data-testid="budget-programs-funded">' +
			escapeHtml(String(programsFunded)) +
			'</span><span class="kt-budget-sr-only" data-testid="budget-builder-total">' +
			escapeHtml(fmtMoney(total, cur)) +
			"</span></div></div>"
		);
	}

	function renderReviewPanel(selected, reviewPayload, reviewLoading) {
		const cur = selected.currency || "";
		const st = String(selected.status || "").trim();
		const stLower = st.toLowerCase();
		const readOnly = isBudgetReadOnly(st);
		const budget = (reviewPayload && reviewPayload.budget) || selected;
		const totals = (reviewPayload && reviewPayload.totals) || {};
		const lines = getReviewLines(reviewPayload);
		const drawerLine = drawerLineName ? findReviewLine(reviewPayload, drawerLineName) : null;
		const planLabel = selected.strategic_plan_title || selected.strategic_plan || "—";

		let banners = "";
		if (readOnly) {
			banners +=
				'<div class="alert alert-info py-2 mb-2 kt-budget-builder-lock-banner" data-testid="budget-builder-readonly-banner" role="status">' +
				escapeHtml(
					st === "Approved"
						? __("This budget is approved and locked.")
						: __("This budget is submitted and awaiting approval."),
				) +
				"</div>";
		}
		if (st === "Rejected" && (budget.rejection_reason || selected.rejection_reason)) {
			banners +=
				'<div class="alert alert-danger py-2 mb-2" data-testid="budget-rejection-summary" role="status">' +
				escapeHtml(__("This budget was rejected.")) +
				" " +
				escapeHtml(String(budget.rejection_reason || selected.rejection_reason || "")) +
				"</div>";
		}
		if (canApproveBudget() && st === "Submitted") {
			banners +=
				'<div class="alert alert-warning py-2 mb-2" data-testid="budget-approver-banner" role="status">' +
				escapeHtml(__("This budget is awaiting your approval.")) +
				"</div>";
		}

		let body = "";
		if (reviewLoading) {
			body =
				'<div class="text-muted small py-3" data-testid="budget-detail-loading">' +
				escapeHtml(__("Loading allocations…")) +
				"</div>";
		} else if (reviewLoadError) {
			body =
				'<div class="alert alert-warning mb-0" data-testid="budget-detail-error">' +
				escapeHtml(reviewLoadError) +
				"</div>";
		} else if (reviewPayload) {
			body = renderAllocationsTable(lines, cur);
		}

		const drawerHtml = renderAllocationDrawer(drawerLine, cur, !!drawerLine);

		return (
			'<div class="kt-budget-workspace-main' +
			(readOnly ? " kt-budget-workspace-main--locked" : "") +
			'" data-testid="selected-budget-panel">' +
			'<header class="kt-budget-workspace-main__header kt-budget-anchor-card kt-surface">' +
			'<div class="kt-budget-workspace-main__heading">' +
			'<h2 class="h5 mb-1" data-testid="selected-budget-title">' +
			escapeHtml(selected.budget_name || selected.name) +
			"</h2>" +
			'<div class="kt-budget-meta-line text-muted small" data-testid="selected-budget-status">' +
			'<span class="' +
			statusBadgeClass(selected.status) +
			'" data-testid="selected-budget-status-badge" data-kt-status="' +
			escapeHtml(stLower) +
			'">' +
			escapeHtml(selected.status || "") +
			"</span>" +
			'<span class="kt-budget-meta-sep">·</span>' +
			'<span data-testid="selected-budget-fiscal-year">' +
			escapeHtml(selected.fiscal_year || "—") +
			"</span>" +
			'<span class="kt-budget-meta-sep">·</span>' +
			'<span data-testid="selected-budget-strategy">' +
			escapeHtml(planLabel) +
			"</span>" +
			'<span class="kt-budget-meta-sep">·</span>' +
			'<span data-testid="selected-budget-currency">' +
			escapeHtml(cur || "—") +
			"</span></div></div>" +
			renderReviewActions(selected) +
			"</header>" +
			banners +
			renderMetricsStrip(selected, totals, cur) +
			'<div class="kt-budget-review-body">' +
			body +
			drawerHtml +
			"</div></div>"
		);
	}

	function loadReviewData(host, payload) {
		const selected =
			selectedBudgetName && payload ? findBudget(payload, selectedBudgetName) : null;
		if (!selected || !selected.name) return;

		resetReviewForBudget(selected.name);
		const token = ++reviewLoadToken;
		const needsLoad =
			!lastReviewPayload ||
			!lastReviewPayload.budget ||
			lastReviewPayload.budget.name !== selected.name;

		if (!needsLoad) return;

		reviewLoadError = null;
		renderBudgetLandingContent(host, payload, true);
		frappe.call({
			method: "kentender_budget.api.review.get_budget_review_data",
			args: { budget_name: selected.name },
			callback: function (r) {
				if (token !== reviewLoadToken) return;
				if (!isBudgetWorkspaceRoute()) return;
				if (r.exc) {
					lastReviewPayload = null;
					reviewLoadError = __("Unable to load budget allocations.");
					renderBudgetLandingContent(host, lastPayload, false);
					return;
				}
				reviewLoadError = null;
				lastReviewPayload = r.message || {};
				renderBudgetLandingContent(host, lastPayload, false);
			},
			error: function () {
				if (token !== reviewLoadToken) return;
				lastReviewPayload = null;
				reviewLoadError = __("Unable to load budget allocations.");
				renderBudgetLandingContent(host, lastPayload, false);
			},
		});
	}

	function reloadLandingAfterTransition(host) {
		lastReviewPayload = null;
		drawerLineName = null;
		frappe.call({
			method: "kentender_budget.api.landing.get_budget_landing_data",
			callback: function (r) {
				if (!isBudgetWorkspaceRoute()) return;
				const msg = r.message || { portfolio: {}, budgets: [] };
				lastPayload = msg;
				renderBudgetLandingContent(host, lastPayload, false);
				loadReviewData(host, lastPayload);
			},
		});
	}

	function confirmAndCall(method, args, host) {
		frappe.confirm(__("Are you sure you want to continue?"), function () {
			frappe.call({
				method: method,
				args: args,
				callback: function (r) {
					if (r.exc) return;
					reloadLandingAfterTransition(host);
				},
			});
		});
	}

	function openRejectDialog(budgetName, host) {
		const d = new frappe.ui.Dialog({
			title: __("Reject budget"),
			fields: [
				{
					fieldname: "rejection_reason",
					label: __("Reason for rejection"),
					fieldtype: "Small Text",
					reqd: 1,
				},
			],
			primary_action_label: __("Reject"),
			primary_action: function (values) {
				const reason = (values.rejection_reason || "").trim();
				if (!reason) {
					frappe.msgprint(__("Reason for rejection is required."));
					return;
				}
				frappe.call({
					method: "kentender_budget.api.approval.reject_budget",
					args: { budget_name: budgetName, rejection_reason: reason },
					callback: function (r) {
						if (r.exc) return;
						d.hide();
						reloadLandingAfterTransition(host);
					},
				});
			},
		});
		d.$wrapper.attr("data-testid", "budget-reject-modal");
		d.fields_dict.rejection_reason.$wrapper.find("textarea").attr(
			"data-testid",
			"budget-reject-reason-input",
		);
		d.show();
	}

	function renderBudgetLandingContent(host, payload, reviewLoading) {
		reviewLoading = !!reviewLoading;
		ensureWorkTab();
		const portfolio = (payload && payload.portfolio) || {};
		const allBudgets = (payload && payload.budgets) || [];
		const stored = consumeStoredBudgetSelection();
		if (stored && findBudget(payload, stored)) {
			selectedBudgetName = stored;
		}

		const filteredBudgets = filterBudgetsByTab(allBudgets, activeWorkTab);
		let selected =
			selectedBudgetName && allBudgets.length
				? findBudget(payload, selectedBudgetName)
				: allBudgets.length
					? allBudgets[0]
					: null;
		if (selected && filteredBudgets.length) {
			const inTab = filteredBudgets.some(function (b) { return b.name === selected.name; });
			if (!inTab) selected = filteredBudgets[0];
		} else if (filteredBudgets.length) {
			selected = filteredBudgets[0];
		} else if (!filteredBudgets.length && allBudgets.length) {
			selected = null;
		}

		if (selected) {
			selectedBudgetName = selected.name;
		} else if (!allBudgets.length) {
			selectedBudgetName = null;
			lastReviewPayload = null;
			drawerLineName = null;
		}

		const emptyBudgets = allBudgets.length === 0;
		const emptyTab = !emptyBudgets && filteredBudgets.length === 0;

		const createBtn = canCreateBudget()
			? '<button type="button" class="btn btn-primary btn-sm" data-testid="budget-create-button">' +
				escapeHtml(__("New Budget")) +
				"</button>"
			: "";

		let listHtml = "";
		for (let i = 0; i < filteredBudgets.length; i++) {
			const b = filteredBudgets[i];
			const active = selected && b.name === selected.name ? " is-active" : "";
			const st = String(b.status || "").toLowerCase();
			const needsAction =
				(st === "submitted" && isPlanningAuthority()) ||
				((st === "draft" || st === "rejected") &&
					isStrategyManager() &&
					(b.owner === sessionUser() || b.created_by === sessionUser()));
			const actionClass = needsAction ? " kt-budget-row--action" : "";
			const planLabel = b.strategic_plan_title || b.strategic_plan || "";
			listHtml +=
				'<button type="button" class="kt-budget-row' +
				active +
				actionClass +
				'" data-budget="' +
				escapeHtml(b.name) +
				'" data-budget-name="' +
				escapeHtml(b.name) +
				'" data-testid="budget-row-' +
				escapeHtml(b.name) +
				'">' +
				'<span class="kt-budget-row__main">' +
				'<span class="kt-budget-row__title" data-testid="budget-row-title-' +
				escapeHtml(b.name) +
				'">' +
				escapeHtml(b.budget_name || b.name) +
				"</span>" +
				'<span class="text-muted small">' +
				escapeHtml(b.fiscal_year || "") +
				" · " +
				escapeHtml(b.currency || "") +
				(planLabel ? " · " + escapeHtml(planLabel) : "") +
				"</span>" +
				(needsAction
					? '<span class="kt-budget-row__cue text-primary">' +
						escapeHtml(__("Requires action")) +
						"</span>"
					: "") +
				"</span>" +
				'<span class="' +
				statusBadgeClass(b.status) +
				(st === "submitted" && isPlanningAuthority() ? " kt-budget-badge--submitted-pa" : "") +
				'" data-kt-status="' +
				escapeHtml(st) +
				'" data-testid="budget-row-status-' +
				escapeHtml(b.name) +
				'">' +
				escapeHtml(b.status || "") +
				"</span></button>";
		}

		let emptyHtml = "";
		if (emptyBudgets) {
			emptyHtml =
				'<p class="text-muted small mb-0" data-testid="budget-empty-state">' +
				escapeHtml(__("No budgets yet. Create one to begin.")) +
				"</p>";
		} else if (emptyTab) {
			emptyHtml =
				'<p class="text-muted small mb-0" data-testid="budget-tab-empty-state">' +
				escapeHtml(__("No budgets in this tab.")) +
				"</p>";
		}

		let detailHtml = "";
		if (selected && !emptyTab) {
			const reviewPayload =
				lastReviewPayload &&
				lastReviewPayload.budget &&
				lastReviewPayload.budget.name === selected.name
					? lastReviewPayload
					: null;
			detailHtml = renderReviewPanel(
				selected,
				reviewPayload,
				reviewLoading || !reviewPayload,
			);
		}

		host.className = "kt-budget-injected-shell kt-budget-review-shell";
		host.innerHTML =
			'<div class="kt-budget-workspace-header kt-budget-workspace-header--compact mb-2">' +
			'<div class="d-flex justify-content-between align-items-start flex-wrap gap-2 kt-budget-header-row">' +
			"<div>" +
			'<h1 class="h4 kt-budget-page-title mb-1" data-testid="budget-page-title">' +
			escapeHtml(WS_LABEL) +
			"</h1>" +
			'<p class="text-muted mb-0" data-testid="budget-page-intro">' +
			escapeHtml(__("Review program allocations and manage budget approval.")) +
			"</p></div>" +
			'<div class="kt-budget-header-cta">' +
			createBtn +
			"</div></div>" +
			renderWorkTabs(portfolio) +
			"</div>" +
			(emptyBudgets
				? '<div class="kt-budget-empty-wrap">' + emptyHtml + "</div>"
				: '<div class="kt-budget-workspace-body">' +
					'<aside class="kt-budget-budgets-rail kt-surface">' +
					'<h2 class="h6 mb-2">' +
					escapeHtml(__("Budgets")) +
					"</h2>" +
					(emptyTab
						? emptyHtml
						: '<div class="kt-budget-row-list" data-testid="budget-list">' + listHtml + "</div>") +
					"</aside>" +
					'<div class="kt-budget-workspace-main-wrap">' +
					(emptyTab
						? '<div class="text-muted small" data-testid="budget-review-empty-tab">' +
							escapeHtml(__("Select another tab or create a budget.")) +
							"</div>"
						: detailHtml) +
					"</div></div>");
		host.setAttribute("data-testid", "budget-landing-page");

		if (selected && !emptyTab) {
			const reviewPayload =
				lastReviewPayload &&
				lastReviewPayload.budget &&
				lastReviewPayload.budget.name === selected.name
					? lastReviewPayload
					: null;
			if (!reviewPayload && !reviewLoading) {
				loadReviewData(host, payload);
			}
		}
	}

	function ensureBudgetDelegatedClicks(root) {
		if (!root || root.getAttribute("data-kt-budget-delegated") === "1") return;
		root.setAttribute("data-kt-budget-delegated", "1");
		root.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!t || !t.closest) return;

			const tabBtn = t.closest("[data-kt-budget-tab]");
			if (tabBtn) {
				const nextTab = tabBtn.getAttribute("data-kt-budget-tab") || "all";
				if (nextTab !== activeWorkTab) {
					const prevSelected = selectedBudgetName;
					activeWorkTab = nextTab;
					drawerLineName = null;
					const budgets = (lastPayload && lastPayload.budgets) || [];
					const filtered = filterBudgetsByTab(budgets, activeWorkTab);
					let nextSelected = prevSelected && findBudget(lastPayload, prevSelected);
					if (!nextSelected || !filtered.some(function (b) { return b.name === nextSelected.name; })) {
						nextSelected = filtered.length ? filtered[0] : null;
					}
					const selectedChanged = (nextSelected && nextSelected.name) !== prevSelected;
					selectedBudgetName = nextSelected ? nextSelected.name : null;
					const needReview =
						!!selectedBudgetName &&
						(selectedChanged ||
							!lastReviewPayload ||
							!lastReviewPayload.budget ||
							lastReviewPayload.budget.name !== selectedBudgetName);
					if (selectedChanged) {
						lastReviewPayload = null;
					}
					renderBudgetLandingContent(root, lastPayload, needReview);
					if (needReview) {
						loadReviewData(root, lastPayload);
					}
				}
				return;
			}

			const allocRow = t.closest(".kt-budget-allocation-row[data-budget-line]");
			if (allocRow) {
				const lineName = allocRow.getAttribute("data-budget-line");
				if (lineName) {
					drawerLineName = lineName;
					renderBudgetLandingContent(root, lastPayload, false);
				}
				return;
			}

			if (t.closest("[data-testid='budget-allocation-drawer-close']")) {
				drawerLineName = null;
				renderBudgetLandingContent(root, lastPayload, false);
				return;
			}

			const row = t.closest(".kt-budget-row[data-budget]");
			if (row) {
				const name = row.getAttribute("data-budget");
				if (name && lastPayload) {
					const switching = name !== selectedBudgetName;
					if (switching) {
						selectedBudgetName = name;
						lastReviewPayload = null;
						drawerLineName = null;
						renderBudgetLandingContent(root, lastPayload, true);
						loadReviewData(root, lastPayload);
					} else if (
						!lastReviewPayload ||
						!lastReviewPayload.budget ||
						lastReviewPayload.budget.name !== name
					) {
						loadReviewData(root, lastPayload);
					}
				}
				return;
			}

			if (t.closest("[data-testid='budget-create-button']")) {
				saveBudgetWorkbenchState();
				if (
					typeof kentender_core !== "undefined" &&
					kentender_core.kt_nav
				) {
					kentender_core.kt_nav.toForm("budget", null, true);
				} else if (typeof frappe.new_doc === "function") {
					frappe.new_doc("Budget");
				} else {
					frappe.set_route("Form", "Budget", "new-budget");
				}
				return;
			}

			if (t.closest("[data-testid='selected-budget-open-builder']")) {
				const sel =
					lastPayload && selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (sel && sel.name) {
					saveBudgetWorkbenchState();
					if (
						typeof kentender_core !== "undefined" &&
						kentender_core.kt_nav
					) {
						kentender_core.kt_nav.toBuilder("budget", sel.name);
					} else {
						frappe.set_route("budget-builder", sel.name);
					}
				}
				return;
			}

			if (t.closest("[data-testid='selected-budget-edit']")) {
				const sel2 =
					lastPayload && selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (sel2 && sel2.name) {
					saveBudgetWorkbenchState();
					if (
						typeof kentender_core !== "undefined" &&
						kentender_core.kt_nav
					) {
						kentender_core.kt_nav.toForm("budget", sel2.name);
					} else {
						frappe.set_route("Form", "Budget", sel2.name);
					}
				}
				return;
			}

			if (t.closest("[data-testid='budget-submit-approval']")) {
				const sel3 =
					lastPayload && selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (sel3 && sel3.name) {
					confirmAndCall(
						"kentender_budget.api.approval.submit_budget",
						{ budget_name: sel3.name },
						root,
					);
				}
				return;
			}

			if (t.closest("[data-testid='budget-approve']")) {
				const sel4 =
					lastPayload && selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (sel4 && sel4.name) {
					confirmAndCall(
						"kentender_budget.api.approval.approve_budget",
						{ budget_name: sel4.name },
						root,
					);
				}
				return;
			}

			if (t.closest("[data-testid='budget-reject']")) {
				const sel5 =
					lastPayload && selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (sel5 && sel5.name) openRejectDialog(sel5.name, root);
				return;
			}
		});
	}

	function injectBudgetMount() {
		const esc = resolveWorkspaceEditorMount();
		if (!esc) return { ok: false };
		const wrap = document.createElement("div");
		wrap.className = "kt-budget-injected-shell";
		wrap.innerHTML =
			'<div class="text-muted small py-3">' + escapeHtml(__("Loading budget workspace…")) + "</div>";
		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) {
			esc.insertBefore(wrap, ed);
			ed.style.display = "none";
		} else {
			esc.insertBefore(wrap, esc.firstChild);
		}
		return { ok: true, wrap: wrap };
	}

	function applyBudgetPayload(payload) {
		lastPayload = payload || { portfolio: {}, budgets: [] };
		const budgets = lastPayload.budgets || [];
		if (budgets.length && !selectedBudgetName) {
			selectedBudgetName = budgets[0].name;
		}
		const root = getVisibleWorkspacesPageRoot();
		let shell =
			(root && root.querySelector(".kt-budget-injected-shell")) ||
			document.querySelector(".kt-budget-injected-shell");
		if (!shell) {
			const inj = injectBudgetMount();
			if (!inj.ok) return;
			shell = inj.wrap;
		}
		renderBudgetLandingContent(shell, lastPayload);
		ensureBudgetDelegatedClicks(shell);
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
				const msg = r && r.message;
				if (!msg) {
					applyBudgetPayload({ portfolio: {}, budgets: [] });
				} else {
					applyBudgetPayload(msg);
				}
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
				const esc = resolveWorkspaceEditorMount();
				if (!esc) return;
				const wrap = document.createElement("div");
				wrap.className = "kt-budget-injected-shell";
				wrap.innerHTML =
					'<div class="alert alert-danger mb-0">' +
					escapeHtml(__("Unable to load budget workspace data.")) +
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

	function tryBindBudgetWorkspace() {
		if (!isBudgetWorkspaceRoute()) {
			removeBudgetLandingIfWrongRoute();
			return;
		}
		syncBudgetShellClass();
		const existing =
			getVisibleWorkspacesPageRoot() &&
			getVisibleWorkspacesPageRoot().querySelector(".kt-budget-injected-shell");
		if (!existing) {
			const inj = injectBudgetMount();
			if (!inj.ok) return;
		}
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
		window.addEventListener("load", kick);
		setTimeout(kick, 900);
	}

	bootstrap();
})();
