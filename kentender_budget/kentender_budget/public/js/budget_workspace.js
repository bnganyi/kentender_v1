// Budget Management workspace — Desk only. Dashboard: KPIs, master–detail, action cards.

(function () {
	let workspaceLoadGen = 0;
	/** @type {Array<object>|null} */
	let landingBudgets = null;
	let selectedBudgetName = null;
	let bindScheduled = false;
	/** @type {string|null} */
	let pendingLandingReselect = null;
	/** @type {'all'|'mywork'|'draft'|'submitted'|'approved'|'rejected'} */
	let activeWorkTab = "all";
	let workTabInitialized = false;
	let workTabBindingsDone = false;

	function userRoleNames() {
		if (typeof frappe === "undefined" || !frappe.boot || !frappe.boot.user) {
			return [];
		}
		if (frappe.session && frappe.session.user === "Administrator") {
			return ["Administrator", "System Manager", "Strategy Manager", "Planning Authority"];
		}
		const roles = frappe.boot.user.roles || [];
		return roles.map(function (r) {
			return typeof r === "string" ? r : r.role;
		});
	}

	function userHasRole(roleName) {
		return userRoleNames().indexOf(roleName) !== -1;
	}

	function canSubmitBudgetAction() {
		if (frappe.session && frappe.session.user === "Administrator") {
			return true;
		}
		return (
			userHasRole("Strategy Manager") ||
			userHasRole("System Manager") ||
			userHasRole("Administrator")
		);
	}

	function canApproveBudgetAction() {
		if (frappe.session && frappe.session.user === "Administrator") {
			return true;
		}
		return (
			userHasRole("Planning Authority") ||
			userHasRole("System Manager") ||
			userHasRole("Administrator")
		);
	}

	function shouldUseInboxMyWorkSemantics() {
		return userHasRole("Planning Authority") || userHasRole("Strategy Manager");
	}

	function passesMyWorkFilter(b) {
		if (!shouldUseInboxMyWorkSemantics()) {
			return true;
		}
		const uid = frappe.session.user;
		const mine = (b.owner === uid || b.created_by === uid);
		const st = String(b.status || "").trim();
		if (userHasRole("Planning Authority") && st === "Submitted") {
			return true;
		}
		if (userHasRole("Strategy Manager") && st === "Draft" && mine) {
			return true;
		}
		if (userHasRole("Strategy Manager") && st === "Rejected" && mine) {
			return true;
		}
		return false;
	}

	function filterBudgetsForWorkTab(budgets, tab) {
		if (!budgets || !budgets.length) {
			return [];
		}
		if (tab === "all") {
			return budgets.slice();
		}
		if (tab === "mywork") {
			return budgets.filter(passesMyWorkFilter);
		}
		if (tab === "draft") {
			return budgets.filter(function (b) {
				return String(b.status || "").trim() === "Draft";
			});
		}
		if (tab === "submitted") {
			return budgets.filter(function (b) {
				return String(b.status || "").trim() === "Submitted";
			});
		}
		if (tab === "approved") {
			return budgets.filter(function (b) {
				return String(b.status || "").trim() === "Approved";
			});
		}
		if (tab === "rejected") {
			return budgets.filter(function (b) {
				return String(b.status || "").trim() === "Rejected";
			});
		}
		return budgets.slice();
	}

	function getDefaultWorkTab() {
		if (frappe.session && frappe.session.user === "Administrator") {
			return "all";
		}
		if (userHasRole("Planning Authority")) {
			return "mywork";
		}
		if (userHasRole("Strategy Manager")) {
			return "draft";
		}
		return "all";
	}

	function syncWorkTabButtons() {
		const wrap = document.getElementById("kt-budget-work-tabs");
		if (!wrap) {
			return;
		}
		wrap.querySelectorAll("[data-kt-tab]").forEach(function (btn) {
			const t = btn.getAttribute("data-kt-tab");
			const on = t === activeWorkTab;
			btn.classList.toggle("btn-primary", on);
			btn.classList.toggle("btn-default", !on);
			btn.setAttribute("aria-selected", on ? "true" : "false");
		});
	}

	function ensureWorkTabBindings() {
		if (workTabBindingsDone) {
			return;
		}
		const wrap = document.getElementById("kt-budget-work-tabs");
		if (!wrap) {
			return;
		}
		workTabBindingsDone = true;
		wrap.addEventListener("click", function (ev) {
			const btn = ev.target.closest("button[data-kt-tab]");
			if (!btn || !wrap.contains(btn)) {
				return;
			}
			const tab = btn.getAttribute("data-kt-tab");
			if (!tab || tab === activeWorkTab) {
				return;
			}
			activeWorkTab = tab;
			syncWorkTabButtons();
			const listRoot = document.getElementById("kt-budget-list-root");
			const detailRoot = document.getElementById("kt-budget-detail-root");
			if (listRoot && detailRoot) {
				renderLandingListAndDetail(listRoot, detailRoot);
			}
		});
	}

	function refreshBudgetLanding(resumeName) {
		pendingLandingReselect = resumeName || selectedBudgetName;
		const listRoot = document.getElementById("kt-budget-list-root");
		const detailRoot = document.getElementById("kt-budget-detail-root");
		if (!listRoot || !detailRoot) {
			return;
		}
		listRoot.dataset.ktBudgetLoaded = "0";
		loadBudgetWorkspace(listRoot, detailRoot);
	}

	function getWorkspacesPageRoot() {
		return (
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]')
		);
	}

	function resolveWorkspaceEditorMount() {
		const root = getWorkspacesPageRoot();
		if (root) {
			let esc = root.querySelector(".layout-main-section .editor-js-container");
			if (!esc) {
				esc = root.querySelector(".editor-js-container");
			}
			if (!esc) {
				const lms = root.querySelector(".layout-main-section");
				if (lms) {
					esc = lms;
				}
			}
			if (esc) {
				return esc;
			}
		}
		const candidates = document.querySelectorAll(".editor-js-container");
		let fallback = null;
		for (let i = 0; i < candidates.length; i++) {
			const el = candidates[i];
			if (!el || !el.isConnected) {
				continue;
			}
			if (!fallback) {
				fallback = el;
			}
			if (el.getClientRects && el.getClientRects().length > 0) {
				return el;
			}
		}
		return fallback;
	}

	function workspaceNameMatchesBudgetManagement(name) {
		if (name == null || name === "") {
			return false;
		}
		if (name === "Budget Management") {
			return true;
		}
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug("Budget Management");
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
					if (workspaceNameMatchesBudgetManagement(workspaceName)) {
						return true;
					}
				}
			}
		} catch (e) {
			/* ignore */
		}
		const loc = window.location;
		const path = ((loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "").toLowerCase();
		if (path.includes("budget-management") || path.includes("budget_management")) {
			return true;
		}
		const dr = (document.body && document.body.getAttribute("data-route")) || "";
		if (dr.includes("Budget Management") || dr.toLowerCase().includes("budget-management")) {
			return true;
		}
		if (typeof frappe !== "undefined" && typeof frappe.get_route_str === "function") {
			try {
				const rs = String(frappe.get_route_str() || "").toLowerCase();
				if (rs.includes("budget-management") || rs.includes("budget management")) {
					return true;
				}
			} catch (e) {
				/* ignore */
			}
		}
		try {
			const route = frappe.get_route() || [];
			if (route[0] !== "Workspaces") {
				return false;
			}
			const w = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
			if (!w) {
				return false;
			}
			if (w === "Budget Management" || w === "budget-management") {
				return true;
			}
			if (frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(w) === frappe.router.slug("Budget Management");
			}
			return false;
		} catch (e) {
			return false;
		}
	}

	function syncBudgetShellClass() {
		document.body.classList.toggle("kt-budget-shell", isBudgetWorkspaceRoute());
	}

	function removeBudgetLandingIfWrongRoute() {
		document.querySelectorAll(".kt-budget-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-budget-shell");
		landingBudgets = null;
		selectedBudgetName = null;
		activeWorkTab = "all";
		workTabInitialized = false;
		workTabBindingsDone = false;
		bindScheduled = false;
	}

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function stripHtml(s) {
		if (s == null || s === undefined) {
			return "";
		}
		return String(s).replace(/<[^>]*>/g, "").trim();
	}

	function budgetNameSlug(name) {
		if (name == null || name === undefined) {
			return "unknown";
		}
		return String(name).replace(/[^a-zA-Z0-9_-]/g, "_");
	}

	function displayBudgetLabel(raw) {
		const s = String(raw || "").trim();
		// Hide test-run timestamp suffixes like "Budget Name 1776693067634".
		return s.replace(/\s+\d{10,}$/, "");
	}

	function fiscalYearLabel(raw) {
		const y = Number(raw);
		if (!Number.isInteger(y) || y < 2000 || y > 2099) {
			return __("FY —");
		}
		return __("FY {0}", [String(y)]);
	}

	function statusKeyFromRaw(statusRaw) {
		const s = String(statusRaw || "")
			.toLowerCase()
			.trim();
		if (s === "approved") {
			return "approved";
		}
		if (s === "submitted") {
			return "submitted";
		}
		if (s === "rejected") {
			return "rejected";
		}
		if (s === "archived") {
			return "archived";
		}
		return "draft";
	}

	function budgetBadgeClass(statusRaw) {
		const k = statusKeyFromRaw(statusRaw);
		return "kt-budget-badge kt-budget-badge--" + k;
	}

	function formatAmount(value, digits) {
		const v = Number(value);
		if (Number.isNaN(v)) {
			return "0";
		}
		const precision = Number.isInteger(digits) ? digits : 2;
		return v.toLocaleString("en-US", {
			minimumFractionDigits: precision,
			maximumFractionDigits: precision,
		});
	}

	function formatAmountKpi(value) {
		const v = Number(value);
		if (Number.isNaN(v)) {
			return "0";
		}
		return Math.round(v).toLocaleString("en-US");
	}

	function formatPercent(value) {
		const v = Number(value);
		if (Number.isNaN(v)) {
			return "—";
		}
		return v.toFixed(1) + "%";
	}

	function allocationHealthMeta(value) {
		const v = Number(value);
		if (Number.isNaN(v)) {
			return {
				key: "unknown",
				icon: "❔",
				label: __("Unknown"),
			};
		}
		if (v <= 0) {
			return {
				key: "none",
				icon: "⏺",
				label: __("Not Allocated"),
			};
		}
		if (v <= 40) {
			return {
				key: "low",
				icon: "⚠",
				label: __("Low"),
			};
		}
		if (v >= 100) {
			return {
				key: "full",
				icon: "✅",
				label: __("Fully Allocated"),
			};
		}
		return {
			key: "partial",
			icon: "🟡",
			label: __("Partial"),
		};
	}

	function injectBudgetLandingShell() {
		if (document.getElementById("kt-budget-list-root")) {
			return true;
		}
		const esc = resolveWorkspaceEditorMount();
		if (!esc) {
			return false;
		}
		const wrap = document.createElement("div");
		wrap.className = "kt-budget-injected-shell";
		wrap.setAttribute("data-testid", "budget-landing-page");
		wrap.innerHTML =
			'<div class="kt-budget-workspace-header mb-3">' +
			'<div class="kt-budget-header-row">' +
			'<h2 class="kt-budget-page-title h4 mb-2" data-testid="budget-page-title">' +
			escapeHtml(__("Budget Management")) +
			"</h2>" +
			'<div class="kt-budget-header-cta" data-testid="budget-header-cta"></div>' +
			"</div>" +
			'<p class="kt-budget-page-intro text-muted mb-0" data-testid="budget-page-intro">' +
			escapeHtml(__("Create and manage budgets aligned to strategic plans.")) +
			"</p>" +
			"</div>" +
			'<div class="kt-budget-overview-metrics row g-3 mb-3" data-testid="budget-overview-metrics">' +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-budget-kpi-card kt-surface">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Active budgets")) +
			"</div>" +
			'<div class="kt-budget-kpi-value" data-testid="budget-metric-active">0</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-budget-kpi-card kt-surface">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Draft budgets")) +
			"</div>" +
			'<div class="kt-budget-kpi-value" data-testid="budget-metric-draft">0</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-budget-kpi-card kt-surface">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Total budget amount")) +
			"</div>" +
			'<div class="kt-budget-kpi-value" data-testid="budget-metric-total">—</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-budget-kpi-card kt-surface">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Allocation")) +
			"</div>" +
			'<div class="kt-budget-kpi-value" data-testid="budget-metric-allocation-pct">0%</div>' +
			"</div></div>" +
			"</div>" +
			'<div class="row kt-budget-overview-metrics kt-budget-overview-metrics--secondary g-3 mb-3" data-testid="budget-overview-metrics-secondary">' +
			'<div class="col-6 col-lg-3 d-none" data-testid="budget-kpi-pending-wrap">' +
			'<div class="kt-budget-kpi-card kt-surface">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Pending approval")) +
			"</div>" +
			'<div class="kt-budget-kpi-value" data-testid="budget-metric-pending-approval">0</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3 d-none" data-testid="budget-kpi-drafts-wrap">' +
			'<div class="kt-budget-kpi-card kt-surface">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("My drafts")) +
			"</div>" +
			'<div class="kt-budget-kpi-value" data-testid="budget-metric-my-drafts">0</div>' +
			"</div></div>" +
			"</div>" +
			'<div class="row g-3 kt-budget-master-detail">' +
			'<div class="kt-budget-col-list">' +
			'<div class="kt-budget-section kt-surface">' +
			'<h3 class="kt-budget-section__title">' +
			escapeHtml(__("Budgets")) +
			"</h3>" +
			'<div class="kt-budget-work-tabs mb-2" role="tablist" id="kt-budget-work-tabs" data-testid="budget-work-tabs">' +
			'<div class="btn-group btn-group-sm flex-wrap kt-budget-tab-group" role="group">' +
			'<button type="button" class="btn btn-primary" data-testid="budget-tab-all" data-kt-tab="all" role="tab" aria-selected="true">' +
			escapeHtml(__("All")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="budget-tab-my-work" data-kt-tab="mywork" role="tab" aria-selected="false">' +
			escapeHtml(__("My Work")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="budget-tab-draft" data-kt-tab="draft" role="tab" aria-selected="false">' +
			escapeHtml(__("Draft")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="budget-tab-submitted" data-kt-tab="submitted" role="tab" aria-selected="false">' +
			escapeHtml(__("Submitted")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="budget-tab-approved" data-kt-tab="approved" role="tab" aria-selected="false">' +
			escapeHtml(__("Approved")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="budget-tab-rejected" data-kt-tab="rejected" role="tab" aria-selected="false">' +
			escapeHtml(__("Rejected")) +
			"</button>" +
			"</div></div>" +
			'<div id="kt-budget-list-root"></div>' +
			"</div></div>" +
			'<div class="kt-budget-col-detail">' +
			'<div class="kt-budget-section kt-surface kt-budget-detail-section">' +
			'<div id="kt-budget-detail-root"></div>' +
			"</div></div></div>";
		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) {
			esc.insertBefore(wrap, ed);
		} else {
			esc.insertBefore(wrap, esc.firstChild);
		}
		syncHeaderCreateButton();
		return true;
	}

	function getSelectedBudget() {
		if (!landingBudgets || !selectedBudgetName) {
			return null;
		}
		return landingBudgets.find(function (b) {
			return b.name === selectedBudgetName;
		}) || null;
	}

	function syncHeaderCreateButton() {
		const slot = document.querySelector('[data-testid="budget-header-cta"]');
		if (!slot) {
			return;
		}
		slot.innerHTML = "";
		const canCreate =
			typeof frappe !== "undefined" && frappe.model && frappe.model.can_create("Budget");
		if (canCreate) {
			const btn = document.createElement("button");
			btn.type = "button";
			btn.className = "btn btn-primary btn-sm kt-budget-header-create";
			btn.setAttribute("data-testid", "budget-create-button");
			btn.textContent = __("New Budget");
			btn.addEventListener("click", function () {
				frappe.set_route("Form", "Budget", "new");
			});
			slot.appendChild(btn);
		}
	}

	function updateOverviewMetrics(portfolio) {
		const p = portfolio || {};
		const elActive = document.querySelector('[data-testid="budget-metric-active"]');
		const elDraft = document.querySelector('[data-testid="budget-metric-draft"]');
		const elTotal = document.querySelector('[data-testid="budget-metric-total"]');
		const elPct = document.querySelector('[data-testid="budget-metric-allocation-pct"]');
		if (elActive) {
			const v = String(p.active_count != null ? p.active_count : 0);
			elActive.textContent = v;
			elActive.title = v;
		}
		if (elDraft) {
			const v = String(p.draft_count != null ? p.draft_count : 0);
			elDraft.textContent = v;
			elDraft.title = v;
		}
		if (elTotal) {
			const v = formatAmountKpi(p.total_budget_sum || 0);
			elTotal.textContent = v;
			elTotal.title = v;
		}
		if (elPct) {
			const v = formatPercent(p.allocation_pct || 0);
			elPct.textContent = v;
			elPct.title = v;
		}
		updateExtraKpiCards(p);
	}

	function updateExtraKpiCards(portfolio) {
		const p = portfolio || {};
		const elP = document.querySelector('[data-testid="budget-metric-pending-approval"]');
		const elD = document.querySelector('[data-testid="budget-metric-my-drafts"]');
		const wrapP = document.querySelector('[data-testid="budget-kpi-pending-wrap"]');
		const wrapD = document.querySelector('[data-testid="budget-kpi-drafts-wrap"]');
		if (elP) {
			const v = String(p.pending_approval_count != null ? p.pending_approval_count : 0);
			elP.textContent = v;
			elP.title = v;
		}
		if (elD) {
			const v = String(p.my_drafts_count != null ? p.my_drafts_count : 0);
			elD.textContent = v;
			elD.title = v;
		}
		if (wrapP) {
			wrapP.classList.toggle("d-none", !canApproveBudgetAction());
		}
		if (wrapD) {
			wrapD.classList.toggle("d-none", !userHasRole("Strategy Manager"));
		}
	}

	function formatRejectionDatetime(raw) {
		if (!raw) {
			return "—";
		}
		try {
			if (frappe.datetime && typeof frappe.datetime.str_to_user === "function") {
				return frappe.datetime.str_to_user(String(raw));
			}
		} catch (e) {
			/* ignore */
		}
		return String(raw);
	}

	function showRejectBudgetDialog(budgetName) {
		const d = new frappe.ui.Dialog({
			title: __("Reject budget"),
			fields: [
				{
					fieldname: "rejection_reason",
					label: __("Reason for rejection"),
					fieldtype: "Text",
					reqd: 1,
				},
			],
			primary_action_label: __("Reject Budget"),
			primary_action: function () {
				const values = d.get_values();
				const reason =
					values && values.rejection_reason ? String(values.rejection_reason).trim() : "";
				if (!reason) {
					frappe.msgprint({
						message: __("Reason for rejection is required."),
						indicator: "red",
					});
					return;
				}
				frappe.call({
					method: "kentender_budget.api.approval.reject_budget",
					args: { budget_name: budgetName, rejection_reason: reason },
					freeze: true,
					callback: function () {
						frappe.show_alert({ message: __("Budget rejected."), indicator: "orange" });
						d.hide();
						refreshBudgetLanding(budgetName);
					},
				});
			},
		});
		d.$wrapper.attr("data-testid", "budget-reject-modal");
		d.show();
		setTimeout(function () {
			d.$wrapper.find("textarea").attr("data-testid", "budget-reject-reason-input");
		}, 50);
	}

	function renderDetailPanel(detailRoot, budget, opts) {
		opts = opts || {};
		if (!budget) {
			const msg = opts.noBudgetsInSystem
				? __("When you create a budget, details will appear here.")
				: __("Select a budget to view details.");
			detailRoot.innerHTML =
				'<div class="kt-budget-selected-stub" data-testid="selected-budget-panel">' +
				'<p class="text-muted mb-0">' +
				escapeHtml(msg) +
				"</p></div>";
			return;
		}

		const cur = budget.currency || "";
		const budgetDisplayTitle = displayBudgetLabel(budget.budget_name || budget.name);
		const statusRaw = budget.status || "";
		const stKey = statusKeyFromRaw(statusRaw);
		const statusDisplay = statusRaw ? escapeHtml(__(statusRaw)) : "—";
		const allocationHealth = allocationHealthMeta(budget.allocation_pct);
		const st = String(statusRaw).trim();
		const isDraft = st === "Draft" || st === "";
		const isSubmitted = st === "Submitted";
		const isRejected = st === "Rejected";
		const canWrite = frappe.model && frappe.model.can_write("Budget", budget.name);
		const useOpenBuilder = isDraft || (isRejected && canSubmitBudgetAction());
		const openBuilderLabel = useOpenBuilder ? __("Open Budget Builder") : __("View Budget Builder");
		let actionsHtml = "";
		actionsHtml +=
			'<button type="button" class="btn btn-primary btn-sm" data-testid="selected-budget-open-builder">' +
			escapeHtml(openBuilderLabel) +
			"</button>";
		if ((isDraft || isRejected) && canWrite && canSubmitBudgetAction()) {
			actionsHtml +=
				'<button type="button" class="btn btn-default btn-sm" data-testid="selected-budget-edit">' +
				escapeHtml(__("Edit Budget")) +
				"</button>";
		}
		if ((isDraft || isRejected) && canSubmitBudgetAction()) {
			const submitTestId = isRejected ? "budget-resubmit-approval" : "budget-submit-approval";
			const submitLabel = isRejected ? __("Re-submit for Approval") : __("Submit for Approval");
			actionsHtml +=
				'<button type="button" class="btn btn-success btn-sm" data-testid="' +
				submitTestId +
				'">' +
				escapeHtml(submitLabel) +
				"</button>";
		}
		if (isSubmitted && canApproveBudgetAction()) {
			actionsHtml +=
				'<button type="button" class="btn btn-success btn-sm" data-testid="budget-approve">' +
				escapeHtml(__("Approve Budget")) +
				"</button>" +
				'<button type="button" class="btn btn-danger btn-sm" data-testid="budget-reject">' +
				escapeHtml(__("Reject Budget")) +
				"</button>";
		}

		const approverBannerHtml =
			isSubmitted && canApproveBudgetAction()
				? '<div class="alert alert-warning mb-3 py-2 px-3 small kt-budget-approver-banner" data-testid="budget-approver-banner" role="status">' +
					escapeHtml(__("This budget requires your approval.")) +
					"</div>"
				: "";

		const rejectionSummaryHtml = isRejected
			? '<section class="kt-budget-detail-card kt-budget-detail-block kt-budget-rejection-summary" data-testid="budget-rejection-summary">' +
				'<h4 class="kt-budget-detail-section__title">' +
				escapeHtml(__("Rejection")) +
				"</h4>" +
				'<div class="alert alert-danger mb-0 py-2 px-3 small" role="status">' +
				'<p class="mb-1 fw-semibold" data-testid="budget-rejected-needs-revision">' +
				escapeHtml(__("Needs revision")) +
				"</p>" +
				'<p class="mb-1 small" data-testid="budget-rejection-reason-display">' +
				escapeHtml(String(budget.rejection_reason || "").trim() || "—") +
				"</p>" +
				'<p class="mb-0 text-muted small" data-testid="budget-rejection-meta">' +
				escapeHtml(__("Rejected by")) +
				" " +
				escapeHtml(String(budget.rejected_by || "—")) +
				" · " +
				escapeHtml(formatRejectionDatetime(budget.rejected_at)) +
				"</p></div></section>"
			: "";

		detailRoot.innerHTML =
			'<div data-testid="selected-budget-panel" class="kt-budget-detail-panel">' +
			'<section class="kt-budget-detail-card kt-budget-detail-block">' +
			'<h4 class="kt-budget-detail-section__title">' +
			escapeHtml(__("Budget summary")) +
			"</h4>" +
			'<dl class="kt-budget-dl row mb-0">' +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Budget name")) +
			"</dt>" +
			'<dd class="mb-0 fw-semibold" data-testid="selected-budget-title" title="' +
			escapeHtml(budget.budget_name || budget.name) +
			'">' +
			escapeHtml(budgetDisplayTitle) +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Status")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-status">' +
			'<span class="' +
			budgetBadgeClass(statusRaw) +
			'" data-testid="selected-budget-status-badge" data-kt-status="' +
			escapeHtml(stKey) +
			'">' +
			statusDisplay +
			"</span></dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Fiscal year")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-fiscal-year">' +
			escapeHtml(fiscalYearLabel(budget.fiscal_year)) +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Strategic plan")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-strategy">' +
			escapeHtml(budget.strategic_plan || "—") +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Currency")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-currency">' +
			escapeHtml(cur || "—") +
			"</dd></div>" +
			"</dl></section>" +
			approverBannerHtml +
			rejectionSummaryHtml +
			'<section class="kt-budget-detail-card kt-budget-detail-block">' +
			'<h4 class="kt-budget-detail-section__title">' +
			escapeHtml(__("Allocation overview")) +
			"</h4>" +
			'<dl class="kt-budget-dl row mb-0">' +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Total budget")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-total">' +
			escapeHtml(formatAmount(budget.total_budget_amount, 2)) +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Allocated")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-allocated">' +
			escapeHtml(formatAmount(budget.allocated_amount, 2)) +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Remaining")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-remaining">' +
			escapeHtml(formatAmount(budget.remaining_amount, 2)) +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Reserved")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-reserved">' +
			escapeHtml(formatAmount(budget.reserved_amount, 2)) +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Available")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-available">' +
			escapeHtml(formatAmount(budget.available_amount, 2)) +
			"</dd></div>" +
			'<div class="col-12 col-md-6 mb-2">' +
			'<dt class="small text-muted">' +
			escapeHtml(__("Allocation")) +
			"</dt>" +
			'<dd class="mb-0" data-testid="selected-budget-allocation-pct">' +
			escapeHtml(formatPercent(budget.allocation_pct)) +
			' <span class="kt-budget-health-badge kt-budget-health-badge--' +
			escapeHtml(allocationHealth.key) +
			'" data-testid="selected-budget-allocation-health">' +
			'<span class="kt-budget-health-badge__icon" aria-hidden="true">' +
			escapeHtml(allocationHealth.icon) +
			"</span> " +
			'<span class="kt-budget-health-badge__label">' +
			escapeHtml(allocationHealth.label) +
			"</span>" +
			"</span>" +
			"</dd></div>" +
			"</dl></section>" +
			'<section class="kt-budget-detail-card kt-budget-detail-block">' +
			'<h4 class="kt-budget-detail-section__title">' +
			escapeHtml(__("Structure")) +
			"</h4>" +
			'<ul class="list-unstyled small mb-0">' +
			"<li>" +
			escapeHtml(__("Budget Lines")) +
			": " +
			escapeHtml(String(budget.budget_line_total != null ? budget.budget_line_total : 0)) +
			"</li>" +
			"<li>" +
			escapeHtml(__("Allocated lines")) +
			": " +
			escapeHtml(String(budget.budget_lines_allocated != null ? budget.budget_lines_allocated : 0)) +
			"</li>" +
			"<li>" +
			escapeHtml(__("Unallocated lines")) +
			": " +
			escapeHtml(String(budget.budget_lines_unallocated != null ? budget.budget_lines_unallocated : 0)) +
			"</li>" +
			"</ul></section>" +
			'<section class="kt-budget-detail-card kt-budget-detail-block kt-budget-detail-actions">' +
			'<h4 class="kt-budget-detail-section__title">' +
			escapeHtml(__("Actions")) +
			"</h4>" +
			'<div class="d-flex flex-wrap gap-2" data-testid="selected-budget-actions">' +
			actionsHtml +
			"</div></section>" +
			"</div>";

		const openB = detailRoot.querySelector('[data-testid="selected-budget-open-builder"]');
		const editB = detailRoot.querySelector('[data-testid="selected-budget-edit"]');
		const submitB = detailRoot.querySelector('[data-testid="budget-submit-approval"]');
		const resubmitB = detailRoot.querySelector('[data-testid="budget-resubmit-approval"]');
		const approveB = detailRoot.querySelector('[data-testid="budget-approve"]');
		const rejectB = detailRoot.querySelector('[data-testid="budget-reject"]');
		if (openB) {
			openB.addEventListener("click", function () {
				frappe.set_route("budget-builder", budget.name);
			});
		}
		if (editB) {
			editB.addEventListener("click", function () {
				frappe.set_route("Form", "Budget", budget.name);
			});
		}
		function wireSubmitApproval(btn) {
			if (!btn) {
				return;
			}
			btn.addEventListener("click", function () {
				const isResubmit = btn.getAttribute("data-testid") === "budget-resubmit-approval";
				frappe.confirm(
					isResubmit ? __("Re-submit this budget for approval?") : __("Submit this budget for approval?"),
					function () {
						frappe.call({
							method: "kentender_budget.api.approval.submit_budget",
							args: { budget_name: budget.name },
							freeze: true,
							callback: function () {
								frappe.show_alert({
									message: __("Budget submitted for approval."),
									indicator: "green",
								});
								refreshBudgetLanding(budget.name);
							},
						});
					},
					function () {},
				);
			});
		}
		wireSubmitApproval(submitB);
		wireSubmitApproval(resubmitB);
		if (rejectB) {
			rejectB.addEventListener("click", function () {
				showRejectBudgetDialog(budget.name);
			});
		}
		if (approveB) {
			approveB.addEventListener("click", function () {
				frappe.confirm(
					__("Approve this budget? This cannot be undone from this screen."),
					function () {
						frappe.call({
							method: "kentender_budget.api.approval.approve_budget",
							args: { budget_name: budget.name },
							freeze: true,
							callback: function () {
								frappe.show_alert({
									message: __("Budget approved."),
									indicator: "green",
								});
								refreshBudgetLanding(budget.name);
							},
						});
					},
					function () {},
				);
			});
		}
	}

	function renderEmptyList(listRoot, emptyOpts) {
		emptyOpts = emptyOpts || {};
		const filtered = emptyOpts.filteredEmpty;
		const msg = filtered ? __("No budgets match this filter.") : __("No budgets yet.");
		const sub = filtered ? "" : __("Create one to begin.");
		listRoot.innerHTML =
			'<div data-testid="budget-empty-state" class="kt-budget-empty-wrap">' +
			'<p class="text-muted mb-2 kt-budget-empty-msg">' +
			escapeHtml(msg) +
			"</p>" +
			(sub
				? '<p class="text-muted mb-0 small">' + escapeHtml(sub) + "</p>"
				: "") +
			"</div>";
	}

	function budgetIsMine(b) {
		const uid = frappe.session.user;
		return b.owner === uid || b.created_by === uid;
	}

	function rowNeedsActionCue(b) {
		const st = String(b.status || "").trim();
		if (st === "Submitted" && canApproveBudgetAction()) {
			return true;
		}
		if (
			st === "Draft" &&
			canSubmitBudgetAction() &&
			frappe.model &&
			frappe.model.can_write("Budget", b.name)
		) {
			return true;
		}
		if (
			st === "Rejected" &&
			canSubmitBudgetAction() &&
			budgetIsMine(b) &&
			frappe.model &&
			frappe.model.can_write("Budget", b.name)
		) {
			return true;
		}
		return false;
	}

	function rowActionCueLabel(b) {
		const st = String(b.status || "").trim();
		if (st === "Submitted" && canApproveBudgetAction()) {
			return __("Requires approval");
		}
		if (
			st === "Draft" &&
			canSubmitBudgetAction() &&
			frappe.model &&
			frappe.model.can_write("Budget", b.name)
		) {
			return __("In progress");
		}
		if (st === "Rejected" && canSubmitBudgetAction() && budgetIsMine(b)) {
			return __("Needs revision");
		}
		return "";
	}

	function renderBudgetList(listRoot, budgets, selectedName, onSelect, opts) {
		opts = opts || {};
		const items = budgets
			.map((b) => {
				const slug = budgetNameSlug(b.name);
				const active = b.name === selectedName ? " is-active" : "";
				const statusRaw = b.status || "";
				const status = escapeHtml(statusRaw);
				const stKey = statusKeyFromRaw(statusRaw);
				const fullTitle = b.budget_name || b.name;
				const title = escapeHtml(displayBudgetLabel(fullTitle));
				const fy = escapeHtml(fiscalYearLabel(b.fiscal_year));
				const selectedMarker =
					b.name === selectedName
						? `<span class="kt-budget-sr-only" data-testid="budget-row-selected-${slug}" aria-hidden="true"></span>`
						: "";
				const actionCue = rowNeedsActionCue(b) ? " kt-budget-row--action" : "";
				const cueText = rowActionCueLabel(b);
				const cueHtml = cueText
					? `<span class="kt-budget-row__cue text-muted" data-testid="budget-row-cue-${slug}">${escapeHtml(
							cueText
						)}</span>`
					: "";
				const badgeExtra =
					userHasRole("Planning Authority") && String(statusRaw).trim() === "Submitted"
						? " kt-budget-badge--submitted-pa"
						: "";
				return `<button type="button" class="kt-budget-row${active}${actionCue}" data-budget-name="${escapeHtml(
					b.name
				)}" data-testid="budget-row-${slug}">
					${selectedMarker}
					<span class="kt-budget-row__main">
						<span class="kt-budget-row__title" data-testid="budget-row-title-${slug}" title="${escapeHtml(fullTitle)}">${title}</span>
						<span class="kt-budget-row__meta" data-testid="budget-row-year-${slug}">${fy}${cueHtml ? " · " + cueHtml : ""}</span>
					</span>
					<span class="${budgetBadgeClass(
						statusRaw
					)}${badgeExtra}" data-testid="budget-row-status-${slug}" data-kt-status="${escapeHtml(stKey)}">${status}</span>
				</button>`;
			})
			.join("");
		listRoot.innerHTML = `<div class="kt-budget-row-list" data-testid="budget-list">${items}</div>`;
		const rowList = listRoot.querySelector('[data-testid="budget-list"]');
		if (rowList && typeof opts.preserveScrollTop === "number") {
			rowList.scrollTop = opts.preserveScrollTop;
		}
		const selectedSlug = budgetNameSlug(selectedName);
		const selectedEl = listRoot.querySelector(`[data-testid="budget-row-${selectedSlug}"]`);
		if (rowList && selectedEl && opts.ensureSelectedVisible) {
			const rowRect = selectedEl.getBoundingClientRect();
			const listRect = rowList.getBoundingClientRect();
			if (rowRect.top < listRect.top || rowRect.bottom > listRect.bottom) {
				selectedEl.scrollIntoView({ block: "nearest" });
			}
		}
		listRoot.querySelectorAll(".kt-budget-row").forEach((btn) => {
			btn.addEventListener("click", () => onSelect(btn.getAttribute("data-budget-name")));
		});
	}

	function syncBudgetListSelection(listRoot, selectedName, opts) {
		opts = opts || {};
		const rowList = listRoot.querySelector('[data-testid="budget-list"]');
		if (!rowList) {
			return;
		}
		if (typeof opts.preserveScrollTop === "number") {
			rowList.scrollTop = opts.preserveScrollTop;
		}
		listRoot.querySelectorAll(".kt-budget-row").forEach((btn) => {
			const isActive = btn.getAttribute("data-budget-name") === selectedName;
			btn.classList.toggle("is-active", isActive);
		});
		const selectedSlug = budgetNameSlug(selectedName);
		const selectedEl = listRoot.querySelector(`[data-testid="budget-row-${selectedSlug}"]`);
		if (selectedEl && opts.ensureSelectedVisible) {
			const rowRect = selectedEl.getBoundingClientRect();
			const listRect = rowList.getBoundingClientRect();
			if (rowRect.top < listRect.top || rowRect.bottom > listRect.bottom) {
				selectedEl.scrollIntoView({ block: "nearest" });
			}
		}
	}

	function fetchLandingData() {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "kentender_budget.api.landing.get_budget_landing_data",
				callback(r) {
					if (r.exc) {
						reject(r);
						return;
					}
					resolve(r.message || { portfolio: {}, budgets: [] });
				},
				error(err) {
					reject(err);
				},
			});
		});
	}

	function renderLandingListAndDetail(listRoot, detailRoot) {
		const budgets = landingBudgets || [];
		ensureWorkTabBindings();
		syncWorkTabButtons();

		function selectByName(name) {
			const rowList = listRoot.querySelector('[data-testid="budget-list"]');
			const prevScrollTop = rowList ? rowList.scrollTop : 0;
			selectedBudgetName = name;
			const b = budgets.find(function (x) {
				return x.name === name;
			});
			if (!b) {
				return;
			}
			selectedBudgetName = b.name;
			syncBudgetListSelection(listRoot, selectedBudgetName, {
				preserveScrollTop: prevScrollTop,
				ensureSelectedVisible: true,
			});
			renderDetailPanel(detailRoot, b);
			syncHeaderCreateButton();
		}

		if (!budgets.length) {
			selectedBudgetName = null;
			pendingLandingReselect = null;
			renderEmptyList(listRoot);
			renderDetailPanel(detailRoot, null, { noBudgetsInSystem: true });
			syncHeaderCreateButton();
			return;
		}

		const view = filterBudgetsForWorkTab(budgets, activeWorkTab);

		if (!view.length) {
			selectedBudgetName = null;
			pendingLandingReselect = null;
			renderEmptyList(listRoot, { filteredEmpty: true });
			renderDetailPanel(detailRoot, null, {});
			syncHeaderCreateButton();
			return;
		}

		let pickName = view[0].name;
		if (pendingLandingReselect && view.some(function (x) { return x.name === pendingLandingReselect; })) {
			pickName = pendingLandingReselect;
		} else if (selectedBudgetName && view.some(function (x) { return x.name === selectedBudgetName; })) {
			pickName = selectedBudgetName;
		}
		pendingLandingReselect = null;
		selectedBudgetName = pickName;

		renderBudgetList(listRoot, view, selectedBudgetName, selectByName);
		syncBudgetListSelection(listRoot, selectedBudgetName);
		renderDetailPanel(detailRoot, getSelectedBudget());
		syncHeaderCreateButton();
	}

	function loadBudgetWorkspace(listRoot, detailRoot) {
		if (listRoot.dataset.ktBudgetLoading === "1") {
			return;
		}
		if (listRoot.dataset.ktBudgetLoaded === "1" && landingBudgets) {
			return;
		}
		listRoot.dataset.ktBudgetLoading = "1";
		const gen = ++workspaceLoadGen;

		if (!landingBudgets) {
			detailRoot.innerHTML =
				'<div data-testid="selected-budget-panel">' +
				'<div class="text-muted small">' +
				escapeHtml(__("Loading…")) +
				"</div></div>";
		}

		fetchLandingData()
			.then((payload) => {
				if (gen !== workspaceLoadGen) return;
				listRoot.dataset.ktBudgetLoading = "0";
				listRoot.dataset.ktBudgetLoaded = "1";
				const portfolio = payload.portfolio || {};
				const budgets = payload.budgets || [];
				landingBudgets = budgets;
				updateOverviewMetrics(portfolio);

				if (!workTabInitialized) {
					activeWorkTab = getDefaultWorkTab();
					workTabInitialized = true;
				}

				renderLandingListAndDetail(listRoot, detailRoot);
			})
			.catch(() => {
				if (gen !== workspaceLoadGen) return;
				listRoot.dataset.ktBudgetLoading = "0";
				listRoot.dataset.ktBudgetLoaded = "0";
				landingBudgets = null;
				selectedBudgetName = null;
				listRoot.innerHTML =
					'<p class="text-danger small">' + escapeHtml(__("Could not load budgets.")) + "</p>";
				detailRoot.innerHTML = "";
				updateOverviewMetrics({
					active_count: 0,
					draft_count: 0,
					submitted_count: 0,
					approved_count: 0,
					my_drafts_count: 0,
					rejected_count: 0,
					pending_approval_count: 0,
					total_budget_sum: 0,
					allocation_pct: 0,
				});
			});
	}

	function tryBindBudgetWorkspace() {
		if (!isBudgetWorkspaceRoute()) {
			return;
		}
		if (!injectBudgetLandingShell()) {
			return;
		}
		const listRoot = document.getElementById("kt-budget-list-root");
		const detailRoot = document.getElementById("kt-budget-detail-root");
		if (!listRoot || !detailRoot) {
			return;
		}
		loadBudgetWorkspace(listRoot, detailRoot);
	}

	function requestBudgetBind(delayMs) {
		if (bindScheduled) {
			return;
		}
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindBudgetWorkspace();
		}, delayMs || 0);
	}

	function scheduleBudgetWorkspaceBind() {
		if (!isBudgetWorkspaceRoute()) {
			removeBudgetLandingIfWrongRoute();
			return;
		}
		syncBudgetShellClass();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(() => requestBudgetBind(0));
		} else {
			requestBudgetBind(0);
		}
		requestBudgetBind(120);
	}

	let hooksBound = false;
	let workspaceDomObserver = null;

	function ensureWorkspaceDomObserver() {
		if (workspaceDomObserver || typeof MutationObserver === "undefined") {
			return;
		}
		const target = document.body || document.documentElement;
		if (!target) {
			return;
		}
		workspaceDomObserver = new MutationObserver(function () {
			if (!isBudgetWorkspaceRoute() || document.getElementById("kt-budget-list-root")) {
				return;
			}
			tryBindBudgetWorkspace();
		});
		workspaceDomObserver.observe(target, { childList: true, subtree: true });
	}

	function bindBudgetWorkspaceHooks() {
		if (!hooksBound) {
			hooksBound = true;
			if (window.jQuery) {
				window.jQuery(document).on("page-change", scheduleBudgetWorkspaceBind);
				window.jQuery(document).on("app_ready", scheduleBudgetWorkspaceBind);
			}
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", scheduleBudgetWorkspaceBind);
			}
			ensureWorkspaceDomObserver();
		}
		syncBudgetShellClass();
		scheduleBudgetWorkspaceBind();
	}

	let pollStarted = false;

	function ensurePollBudgetWorkspace() {
		if (pollStarted) {
			return;
		}
		pollStarted = true;
		function tick() {
			if (!isBudgetWorkspaceRoute()) {
				removeBudgetLandingIfWrongRoute();
			} else if (!document.getElementById("kt-budget-list-root")) {
				tryBindBudgetWorkspace();
			}
			setTimeout(tick, 400);
		}
		tick();
	}

	function kickBudgetWorkspace() {
		bindBudgetWorkspaceHooks();
		ensurePollBudgetWorkspace();
		setTimeout(scheduleBudgetWorkspaceBind, 400);
	}

	function bootstrapBudgetWorkspace() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kickBudgetWorkspace();
			if (typeof frappe.ready === "function") {
				frappe.ready(kickBudgetWorkspace);
			}
		}
		whenFrappeExists();
		window.addEventListener("load", kickBudgetWorkspace);
		setTimeout(kickBudgetWorkspace, 900);
	}
	bootstrapBudgetWorkspace();
})();
