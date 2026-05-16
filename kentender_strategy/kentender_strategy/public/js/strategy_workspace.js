// Strategy Management workspace landing — master/detail shell (see Strategy-Landing-Page-Playwright-Contract.md).

(function () {
	const WS_LABEL = "Strategy Management";

	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;
	let lastPayload = null;
	let selectedPlanName = null;

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
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

	function removeStrategyLandingIfWrongRoute() {
		document.querySelectorAll(".kt-strategy-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-strategy-shell");
		selectedPlanName = null;
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
		if (s === "active") return "kt-strategy-badge kt-strategy-badge--active";
		if (s === "archived") return "kt-strategy-badge kt-strategy-badge--archived";
		return "kt-strategy-badge";
	}

	function renderStrategyLandingContent(host, payload) {
		const portfolio = (payload && payload.portfolio) || {};
		const plans = (payload && payload.plans) || [];
		const selected =
			selectedPlanName && plans.length ? findPlan(payload, selectedPlanName) : plans.length ? plans[0] : null;
		if (plans.length && selected) {
			selectedPlanName = selected.name;
		} else if (!plans.length) {
			selectedPlanName = null;
		}

		const emptyPlans = plans.length === 0;
		const totalPlans = Number(portfolio.total_plans != null ? portfolio.total_plans : plans.length) || 0;

		let kpiHtml =
			'<div class="kt-strategy-overview-metrics">' +
			'<div class="row g-1 align-items-stretch">' +
			'<div class="col-6 col-lg-3"><div class="kt-strategy-kpi-card">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("Strategic Plans")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value">' +
			escapeHtml(String(totalPlans)) +
			"</div></div></div>" +
			'<div class="col-6 col-lg-3"><div class="kt-strategy-kpi-card">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("Programs (total)")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value">' +
			escapeHtml(String(portfolio.total_programs != null ? portfolio.total_programs : "0")) +
			"</div></div></div>" +
			'<div class="col-6 col-lg-3"><div class="kt-strategy-kpi-card">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("My drafts")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value">' +
			escapeHtml(String(portfolio.my_drafts_count != null ? portfolio.my_drafts_count : "0")) +
			"</div></div></div>" +
			"</div>" +
			"</div>";

		let listHtml = "";
		for (let i = 0; i < plans.length; i++) {
			const p = plans[i];
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
				'<span class="kt-strategy-plan-row__meta text-muted small">' +
				escapeHtml(String(p.start_year || "—")) +
				"–" +
				escapeHtml(String(p.end_year || "—")) +
				"</span>" +
				"</span>" +
				'<span class="' +
				statusBadgeClass(p.status) +
				'" data-kt-status="' +
				escapeHtml(st) +
				'" data-testid="strategic-plan-row-status-' +
				escapeHtml(p.name) +
				'">' +
				escapeHtml(p.status || "") +
				"</span>" +
				"</button>";
		}

		let emptyHtml = "";
		if (emptyPlans) {
			emptyHtml =
				'<p class="text-muted small mb-0" data-testid="strategic-plans-empty-state">' +
				escapeHtml(__("No strategic plans yet. Create one to begin.")) +
				"</p>";
		}

		let detailHtml = "";
		if (!emptyPlans && selected) {
			const py = String(selected.status || "").toLowerCase();
			detailHtml =
				'<div class="kt-strategy-detail-section kt-surface" data-testid="selected-plan-panel">' +
				'<div class="kt-strategy-detail__hero mb-3">' +
				'<div class="kt-strategy-detail__hero-main">' +
				'<h3 class="kt-strategy-detail__title mb-1" data-testid="selected-plan-title">' +
				escapeHtml(selected.strategic_plan_name || selected.name) +
				"</h3>" +
				'<span class="' +
				statusBadgeClass(selected.status) +
				'" data-kt-status="' +
				escapeHtml(py) +
				'" data-testid="selected-plan-status">' +
				escapeHtml(selected.status || "") +
				"</span>" +
				'<div class="small text-muted mt-2" data-testid="selected-plan-years">' +
				escapeHtml(String(selected.start_year || "—")) +
				" — " +
				escapeHtml(String(selected.end_year || "—")) +
				"</div>" +
				"</div>" +
				"</div>" +
				'<div class="kt-strategy-detail__stats mb-3">' +
				'<div class="kt-strategy-detail-stat">' +
				'<div class="kt-strategy-detail-stat__label">' +
				escapeHtml(__("Programs")) +
				"</div>" +
				'<div class="kt-strategy-detail-stat__num" data-testid="selected-plan-program-count">' +
				escapeHtml(String(selected.program_count != null ? selected.program_count : "0")) +
				"</div>" +
				"</div>" +
				'<div class="kt-strategy-detail-stat">' +
				'<div class="kt-strategy-detail-stat__label">' +
				escapeHtml(__("Objectives")) +
				"</div>" +
				'<div class="kt-strategy-detail-stat__num" data-testid="selected-plan-objective-count">' +
				escapeHtml(String(selected.objective_count != null ? selected.objective_count : "0")) +
				"</div>" +
				"</div>" +
				'<div class="kt-strategy-detail-stat">' +
				'<div class="kt-strategy-detail-stat__label">' +
				escapeHtml(__("Targets")) +
				"</div>" +
				'<div class="kt-strategy-detail-stat__num" data-testid="selected-plan-target-count">' +
				escapeHtml(String(selected.target_count != null ? selected.target_count : "0")) +
				"</div>" +
				"</div>" +
				"</div>" +
				'<div class="kt-strategy-detail__actions mb-0">' +
				'<button type="button" class="btn btn-primary btn-sm" data-testid="selected-plan-open-builder">' +
				escapeHtml(__("Open Strategy Builder")) +
				"</button> " +
				'<button type="button" class="btn btn-default btn-sm" data-testid="selected-plan-edit-plan">' +
				escapeHtml(__("Edit Plan")) +
				"</button>" +
				"</div>" +
				"</div>";
		}

		host.innerHTML =
			'<div class="kt-strategy-workspace-header kt-strategy-workspace-header--compact mb-3">' +
			'<div class="d-flex justify-content-between align-items-start flex-wrap gap-2">' +
			"<div>" +
			'<h1 class="h4 kt-strategy-page-title mb-1" data-testid="strategy-page-title">' +
			escapeHtml(WS_LABEL) +
			"</h1>" +
			'<p class="text-muted mb-0" data-testid="strategy-page-intro">' +
			escapeHtml(__("Portfolio overview and strategic plans.")) +
			"</p>" +
			"</div>" +
			"</div>" +
			"</div>" +
			kpiHtml +
			'<div class="kt-strategy-master-detail kt-strategy-master-detail--tight">' +
			'<div class="kt-strategy-col-list">' +
			'<section class="kt-strategy-section kt-surface" data-testid="strategic-plans-section">' +
			'<div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">' +
			'<h2 class="h5 mb-0">' +
			escapeHtml(__("Strategic Plans")) +
			"</h2>" +
			'<button type="button" class="btn btn-primary btn-sm" data-testid="strategic-plan-create-button">' +
			escapeHtml(__("New Strategic Plan")) +
			"</button>" +
			"</div>" +
			(emptyPlans
				? emptyHtml
				: '<div class="kt-strategy-plan-list" data-testid="strategic-plan-list">' + listHtml + "</div>") +
			"</section>" +
			"</div>" +
			'<div class="kt-strategy-col-detail">' +
			detailHtml +
			"</div>" +
			"</div>";
	}

	function ensureStrategyDelegatedClicks(root) {
		if (!root || root.getAttribute("data-kt-strategy-delegated") === "1") return;
		root.setAttribute("data-kt-strategy-delegated", "1");
		root.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!t || !t.closest) return;
			const row = t.closest(".kt-strategy-plan-row[data-strategy-plan]");
			if (row) {
				const name = row.getAttribute("data-strategy-plan");
				if (name && lastPayload) {
					selectedPlanName = name;
					renderStrategyLandingContent(root, lastPayload);
				}
				return;
			}
			if (t.closest("[data-testid='strategic-plan-create-button']")) {
				if (typeof frappe.new_doc === "function") {
					frappe.new_doc("Strategic Plan");
				} else {
					frappe.set_route("Form", "Strategic Plan", "new-strategic-plan");
				}
				return;
			}
			if (t.closest("[data-testid='selected-plan-open-builder']")) {
				const sel = lastPayload && selectedPlanName ? findPlan(lastPayload, selectedPlanName) : null;
				if (sel && sel.name) frappe.set_route("strategy-builder", sel.name);
				return;
			}
			if (t.closest("[data-testid='selected-plan-edit-plan']")) {
				const sel2 = lastPayload && selectedPlanName ? findPlan(lastPayload, selectedPlanName) : null;
				if (sel2 && sel2.name) frappe.set_route("Form", "Strategic Plan", sel2.name);
				return;
			}
		});
	}

	function injectStrategyShell() {
		if (strategyShellPresent()) {
			return { ok: true, inserted: false };
		}
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
		if (plans.length && !selectedPlanName) {
			selectedPlanName = plans[0].name;
		}
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
		frappe.call({
			method: "kentender_strategy.api.landing.get_strategy_landing_data",
			callback: function (r) {
				if (!isStrategyWorkspaceRoute()) return;
				const msg = r && r.message;
				if (!msg) {
					applyStrategyPayload({ portfolio: {}, plans: [] });
				} else {
					applyStrategyPayload(msg);
				}
			},
			error: function () {
				if (!isStrategyWorkspaceRoute()) return;
				const root = getVisibleWorkspacesPageRoot();
				const shell =
					(root && root.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]')) ||
					document.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]');
				if (!shell) return;
				shell.innerHTML =
					'<div class="alert alert-danger mb-0">' +
					escapeHtml(__("Unable to load strategy workspace data.")) +
					"</div>";
			},
		});
	}

	function tryBindStrategyWorkspace() {
		if (!isStrategyWorkspaceRoute()) {
			removeStrategyLandingIfWrongRoute();
			return;
		}
		syncStrategyShellClass();
		const inj = injectStrategyShell();
		if (inj && inj.ok) {
			loadStrategyLanding();
		}
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
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", scheduleBind);
			}
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
