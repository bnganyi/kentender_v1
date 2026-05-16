// Budget Management workspace landing — portfolio KPIs + master/detail (see 6.Budget-Module-Playwright-Smoke-Contract-v1.md).

(function () {
	const WS_LABEL = "Budget Management";

	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;
	let lastPayload = null;
	let selectedBudgetName = null;

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
		bindScheduled = false;
	}

	function getVisibleWorkspacesPageRoot() {
		try {
			if (typeof frappe !== "undefined" && frappe.container && frappe.container.page) {
				const p = frappe.container.page;
				const route = p.getAttribute && p.getAttribute("data-page-route");
				if (route === "Workspaces" && p.isConnected) {
					return p;
				}
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

	function canCreateBudget() {
		if (frappe.session && frappe.session.user === "Administrator") return true;
		const roles = userRoles();
		return (
			roles.indexOf("System Manager") >= 0 ||
			roles.indexOf("Strategy Manager") >= 0
		);
	}

	function findBudget(payload, name) {
		const budgets = (payload && payload.budgets) || [];
		for (let i = 0; i < budgets.length; i++) {
			if (budgets[i].name === name) return budgets[i];
		}
		return null;
	}

	function statusBadgeClass(status) {
		const s = String(status || "").trim().toLowerCase();
		if (s === "draft")
			return "kt-budget-badge kt-budget-badge--draft";
		if (s === "submitted")
			return "kt-budget-badge kt-budget-badge--submitted";
		if (s === "approved")
			return "kt-budget-badge kt-budget-badge--approved";
		if (s === "rejected")
			return "kt-budget-badge kt-budget-badge--rejected";
		return "kt-budget-badge";
	}

	function fmtMoney(n, currency) {
		if (n == null || n === "") return "—";
		const num = Number(n);
		if (Number.isNaN(num)) return "—";
		try {
			if (typeof frappe !== "undefined" && frappe.format) {
				const txt = frappe.format(num, {
					fieldtype: "Currency",
					options: currency || "",
				});
				if (txt) return String(txt);
			}
		} catch (e) {
			/* ignore */
		}
		return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	}

	function renderBudgetLandingContent(host, payload) {
		const portfolio = (payload && payload.portfolio) || {};
		const budgets = (payload && payload.budgets) || [];
		const selected =
			selectedBudgetName && budgets.length
				? findBudget(payload, selectedBudgetName)
				: budgets.length
					? budgets[0]
					: null;
		if (budgets.length && selected) {
			selectedBudgetName = selected.name;
		} else if (!budgets.length) {
			selectedBudgetName = null;
		}

		const emptyBudgets = budgets.length === 0;

		let kpiHtml =
			'<div class="kt-budget-overview-metrics">' +
			'<div class="row g-1 align-items-stretch">' +
			'<div class="col-6 col-lg-3"><div class="kt-budget-kpi-card">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Active")) +
			"</div>" +
			'<div class="kt-budget-kpi-value">' +
			escapeHtml(String(portfolio.approved_count != null ? portfolio.approved_count : "0")) +
			"</div></div></div>" +
			'<div class="col-6 col-lg-3"><div class="kt-budget-kpi-card">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Drafts")) +
			"</div>" +
			'<div class="kt-budget-kpi-value">' +
			escapeHtml(String(portfolio.draft_count != null ? portfolio.draft_count : "0")) +
			"</div></div></div>" +
			'<div class="col-6 col-lg-3"><div class="kt-budget-kpi-card">' +
			'<div class="kt-budget-kpi-label">' +
			escapeHtml(__("Pending approval")) +
			"</div>" +
			'<div class="kt-budget-kpi-value">' +
			escapeHtml(
				String(portfolio.pending_approval_count != null ? portfolio.pending_approval_count : "0"),
			) +
			"</div></div></div>" +
			"</div>" +
			"</div>";

		const createBtn = canCreateBudget()
			? '<button type="button" class="btn btn-primary btn-sm" data-testid="budget-create-button">' +
				escapeHtml(__("New Budget")) +
				"</button>"
			: "";

		let listHtml = "";
		for (let i = 0; i < budgets.length; i++) {
			const b = budgets[i];
			const active = selected && b.name === selected.name ? " is-active" : "";
			const st = String(b.status || "").toLowerCase();
			listHtml +=
				'<button type="button" class="kt-budget-row' +
				active +
				'" data-budget="' +
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
				"</span>" +
				"</span>" +
				'<span class="' +
				statusBadgeClass(b.status) +
				'" data-kt-status="' +
				escapeHtml(st) +
				'" data-testid="budget-row-status-' +
				escapeHtml(b.name) +
				'">' +
				escapeHtml(b.status || "") +
				"</span>" +
				"</button>";
		}

		let emptyHtml = "";
		if (emptyBudgets) {
			emptyHtml =
				'<p class="text-muted small mb-0" data-testid="budget-empty-state">' +
				escapeHtml(__("No budgets yet. Create one to begin.")) +
				"</p>";
		}

		let detailHtml = "";
		if (!emptyBudgets && selected) {
			const cur = selected.currency || "";
			const st = String(selected.status || "").toLowerCase();
			detailHtml =
				'<div class="kt-budget-detail-card" data-testid="selected-budget-panel">' +
				'<h3 class="mb-2" data-testid="selected-budget-title">' +
				escapeHtml(selected.budget_name || selected.name) +
				"</h3>" +
				'<div class="small text-muted mb-2" data-testid="selected-budget-status">' +
				'<span class="' +
				statusBadgeClass(selected.status) +
				'" data-kt-status="' +
				escapeHtml(st) +
				'">' +
				escapeHtml(selected.status || "") +
				"</span>" +
				"</div>" +
				'<dl class="kt-budget-dl">' +
				"<dt>" +
				escapeHtml(__("Fiscal year")) +
				"</dt><dd data-testid=\"selected-budget-fiscal-year\">" +
				escapeHtml(selected.fiscal_year || "—") +
				"</dd>" +
				"<dt>" +
				escapeHtml(__("Strategic plan")) +
				"</dt><dd data-testid=\"selected-budget-strategy\">" +
				escapeHtml(selected.strategic_plan || "—") +
				"</dd>" +
				"<dt>" +
				escapeHtml(__("Currency")) +
				"</dt><dd data-testid=\"selected-budget-currency\">" +
				escapeHtml(cur || "—") +
				"</dd>" +
				"<dt>" +
				escapeHtml(__("Total")) +
				"</dt><dd data-testid=\"selected-budget-total\">" +
				escapeHtml(fmtMoney(selected.total_budget_amount, cur)) +
				"</dd>" +
				"<dt>" +
				escapeHtml(__("Allocated")) +
				"</dt><dd data-testid=\"selected-budget-allocated\">" +
				escapeHtml(fmtMoney(selected.allocated_amount, cur)) +
				"</dd>" +
				"<dt>" +
				escapeHtml(__("Remaining")) +
				"</dt><dd data-testid=\"selected-budget-remaining\">" +
				escapeHtml(fmtMoney(selected.remaining_amount, cur)) +
				"</dd>" +
				"</dl>" +
				'<div class="mt-3" data-testid="selected-budget-actions">' +
				'<button type="button" class="btn btn-primary btn-sm mr-2" data-testid="selected-budget-open-builder">' +
				escapeHtml(__("Open Budget Builder")) +
				"</button>" +
				'<button type="button" class="btn btn-default btn-sm" data-testid="selected-budget-edit">' +
				escapeHtml(__("Edit Budget")) +
				"</button>" +
				"</div>" +
				"</div>";
		}

		host.innerHTML =
			'<div class="kt-budget-workspace-header kt-budget-workspace-header--compact mb-3">' +
			'<div class="d-flex justify-content-between align-items-start flex-wrap gap-2">' +
			"<div>" +
			'<h1 class="h4 kt-budget-page-title mb-1" data-testid="budget-page-title">' +
			escapeHtml(WS_LABEL) +
			"</h1>" +
			'<p class="text-muted mb-0" data-testid="budget-page-intro">' +
			escapeHtml(__("Portfolio KPIs and budgets.")) +
			"</p>" +
			"</div>" +
			"</div>" +
			"</div>" +
			kpiHtml +
			'<div class="kt-budget-master-detail kt-budget-master-detail--tight">' +
			'<div class="kt-budget-col-list">' +
			'<section class="kt-budget-section kt-surface">' +
			'<div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">' +
			'<h2 class="h5 mb-0">' +
			escapeHtml(__("Budgets")) +
			"</h2>" +
			createBtn +
			"</div>" +
			(emptyBudgets
				? emptyHtml
				: '<div class="kt-budget-row-list" data-testid="budget-list">' + listHtml + "</div>") +
			"</section>" +
			"</div>" +
			'<div class="kt-budget-col-detail">' +
			detailHtml +
			"</div>" +
			"</div>";
		host.setAttribute("data-testid", "budget-landing-page");
	}

	function ensureBudgetDelegatedClicks(root) {
		if (!root || root.getAttribute("data-kt-budget-delegated") === "1") return;
		root.setAttribute("data-kt-budget-delegated", "1");
		root.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!t || !t.closest) return;
			const row = t.closest(".kt-budget-row[data-budget]");
			if (row) {
				const name = row.getAttribute("data-budget");
				if (name && lastPayload) {
					selectedBudgetName = name;
					renderBudgetLandingContent(root, lastPayload);
				}
				return;
			}
			if (t.closest("[data-testid='budget-create-button']")) {
				if (typeof frappe.new_doc === "function") {
					frappe.new_doc("Budget");
				} else {
					frappe.set_route("Form", "Budget", "new-budget");
				}
				return;
			}
			if (t.closest("[data-testid='selected-budget-open-builder']")) {
				const sel = lastPayload && selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (sel && sel.name) frappe.set_route("budget-builder", sel.name);
				return;
			}
			if (t.closest("[data-testid='selected-budget-edit']")) {
				const sel2 = lastPayload && selectedBudgetName ? findBudget(lastPayload, selectedBudgetName) : null;
				if (sel2 && sel2.name) frappe.set_route("Form", "Budget", sel2.name);
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

	function loadBudgetLanding() {
		if (!isBudgetWorkspaceRoute()) return;
		frappe.call({
			method: "kentender_budget.api.landing.get_budget_landing_data",
			callback: function (r) {
				if (!isBudgetWorkspaceRoute()) return;
				const msg = r && r.message;
				if (!msg) {
					applyBudgetPayload({ portfolio: {}, budgets: [] });
				} else {
					applyBudgetPayload(msg);
				}
			},
			error: function (r) {
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
		loadBudgetLanding();
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
			frappe.after_ajax(() => requestBind(0));
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
			else if (!budgetShellPresent() && resolveWorkspaceEditorMount())
				tryBindBudgetWorkspace();
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
