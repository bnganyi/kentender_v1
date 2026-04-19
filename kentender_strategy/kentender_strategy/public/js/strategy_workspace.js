// Scoped UX for Strategy Management workspace only (Desk).
// Data-bound master–detail: Strategic Plan list + selected plan detail, counts, actions.

(function () {
	const PLANS_FIELDS = [
		"name",
		"strategic_plan_name",
		"start_year",
		"end_year",
		"status",
		"modified",
	];

	let workspaceLoadGen = 0;

	function getWorkspacesPageRoot() {
		return (
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]')
		);
	}

	/**
	 * Resolve the EditorJS mount under the Workspaces page only (never the first random .layout-main-section on Desk).
	 * After client-side navigation, `#page-Workspaces` can be missing for a tick — fall back to the visible
	 * `.editor-js-container` (Workspace is the only Desk page that uses this class).
	 */
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
		/* Opening from Desktop → Workspaces can leave the container in-DOM with no layout yet; do not require getClientRects(). */
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

	/**
	 * Workspace paragraph blocks sanitize HTML (only span/b/i/a/br), stripping divs and ids.
	 * Inject the master–detail mount DOM from JS so #kt-strategy-plans-root survives.
	 */
	function injectStrategyMasterDetailShell() {
		if (document.getElementById("kt-strategy-plans-root")) {
			return true;
		}
		const esc = resolveWorkspaceEditorMount();
		if (!esc) {
			return false;
		}
		const wrap = document.createElement("div");
		wrap.className = "kt-strategy-injected-shell";
		wrap.setAttribute("data-testid", "strategy-landing-page");
		wrap.innerHTML =
			'<div class="kt-strategy-workspace-header mb-3">' +
			'<div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-2">' +
			'<h2 class="kt-strategy-page-title h4 mb-0" data-testid="strategy-page-title">' +
			escapeHtml(__("Strategy Management")) +
			"</h2>" +
			'<button type="button" class="btn btn-xs btn-default" data-testid="strategy-workspace-back-desktop">' +
			escapeHtml(__("← Back to Desktop")) +
			"</button>" +
			"</div>" +
			'<p class="kt-strategy-page-intro text-muted mb-3 mb-md-2" data-testid="strategy-page-intro">' +
			escapeHtml(__("Create and manage strategic plans and hierarchy.")) +
			"</p>" +
			'<div class="kt-strategy-header-create-slot" data-testid="strategic-plan-create-slot"></div>' +
			"</div>" +
			'<div class="row g-3 kt-strategy-master-detail">' +
			'<div class="col-md-5">' +
			'<div class="kt-strategy-section kt-surface" data-testid="strategic-plans-section">' +
			'<h4 class="kt-strategy-section__title">' +
			escapeHtml(__("Strategic Plans")) +
			"</h4>" +
			'<div id="kt-strategy-plans-root"></div>' +
			"</div></div>" +
			'<div class="col-md-7">' +
			'<div class="kt-strategy-section kt-surface kt-strategy-detail-section">' +
			'<div id="kt-strategy-detail-root"></div>' +
			"</div></div></div>";
		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) {
			esc.insertBefore(wrap, ed);
		} else {
			esc.insertBefore(wrap, esc.firstChild);
		}
		const backDesktop = wrap.querySelector('[data-testid="strategy-workspace-back-desktop"]');
		if (backDesktop) {
			backDesktop.addEventListener("click", function () {
				frappe.set_route("/desk");
			});
		}
		syncStrategicPlanCreateButton();
		return true;
	}

	function strategyWorkspaceSlug() {
		try {
			const route = frappe.get_route() || [];
			if (route[0] !== "Workspaces") return null;
			return route[1] === "private" ? route[2] : route[1];
		} catch (e) {
			return null;
		}
	}

	function workspaceNameMatchesStrategyManagement(name) {
		if (name == null || name === "") {
			return false;
		}
		if (name === "Strategy Management") {
			return true;
		}
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug("Strategy Management");
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "strategy-management";
	}

	/** Workspace route[1] is the Workspace document name (e.g. "Strategy Management"), not the URL slug. */
	function isStrategyWorkspaceRoute() {
		/* Desktop icon → app: URL can still be /desk while router already resolved Workspaces/Strategy Management. */
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesStrategyManagement(workspaceName)) {
						return true;
					}
				}
			}
		} catch (e) {
			/* ignore */
		}
		const loc = window.location;
		const path = ((loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "").toLowerCase();
		if (path.includes("strategy-management") || path.includes("strategy_management")) {
			return true;
		}
		const dr = (document.body && document.body.getAttribute("data-route")) || "";
		if (dr.includes("Strategy Management") || dr.toLowerCase().includes("strategy-management")) {
			return true;
		}
		if (typeof frappe !== "undefined" && typeof frappe.get_route_str === "function") {
			try {
				const rs = String(frappe.get_route_str() || "").toLowerCase();
				if (rs.includes("strategy-management") || rs.includes("strategy management")) {
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
			const w = strategyWorkspaceSlug();
			if (!w) {
				return false;
			}
			if (w === "Strategy Management" || w === "strategy-management") {
				return true;
			}
			if (frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(w) === frappe.router.slug("Strategy Management");
			}
			return false;
		} catch (e) {
			return false;
		}
	}

	function syncStrategyShellClass() {
		document.body.classList.toggle("kt-strategy-shell", isStrategyWorkspaceRoute());
	}

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	/** Safe fragment for data-testid suffixes (Strategic Plan document name). */
	function planNameSlug(name) {
		if (name == null || name === undefined) {
			return "unknown";
		}
		return String(name).replace(/[^a-zA-Z0-9_-]/g, "_");
	}

	function statusKeyFromRaw(statusRaw) {
		const s = String(statusRaw || "")
			.toLowerCase()
			.trim();
		if (s === "active" || s === "activated") {
			return "active";
		}
		if (s === "archived") {
			return "archived";
		}
		return "draft";
	}

	function statusBadgeClass(status) {
		return "kt-strategy-badge kt-strategy-badge--" + statusKeyFromRaw(status);
	}

	/** When strategic_plan_name already embeds start/end years, skip a second years line (avoids "…2030 2026–2030"). */
	function yearRangeAlreadyInName(plan) {
		const name = String(plan.strategic_plan_name || plan.name || "");
		const sy = plan.start_year != null ? String(plan.start_year) : "";
		const ey = plan.end_year != null ? String(plan.end_year) : "";
		if (!name || !sy || !ey) {
			return false;
		}
		return name.includes(sy) && name.includes(ey);
	}

	function formatYearRange(plan) {
		if (plan.start_year == null || plan.end_year == null) {
			return "—";
		}
		return `${escapeHtml(plan.start_year)}–${escapeHtml(plan.end_year)}`;
	}

	function syncStrategicPlanCreateButton() {
		const slot = document.querySelector('[data-testid="strategic-plan-create-slot"]');
		if (!slot) {
			return;
		}
		slot.innerHTML = "";
		if (
			typeof frappe === "undefined" ||
			!frappe.model ||
			!frappe.model.can_create("Strategic Plan")
		) {
			return;
		}
		const btn = document.createElement("button");
		btn.type = "button";
		btn.className = "btn btn-primary btn-sm kt-strategy-header-create";
		btn.setAttribute("data-testid", "strategic-plan-create-button");
		btn.textContent = __("New Strategic Plan");
		btn.addEventListener("click", () => {
			frappe.set_route("Form", "Strategic Plan", "new");
		});
		slot.appendChild(btn);
	}

	function fetchStrategicPlans() {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Strategic Plan",
					fields: PLANS_FIELDS,
					order_by: "modified desc",
					limit_page_length: 1000,
				},
				callback(r) {
					resolve(r.message || []);
				},
				error(r) {
					reject(r);
				},
			});
		});
	}

	function fetchCounts(planName) {
		const f = { strategic_plan: planName };
		return Promise.all([
			frappe.db.count("Strategy Program", { filters: f }),
			frappe.db.count("Strategy Objective", { filters: f }),
			frappe.db.count("Strategy Target", { filters: f }),
		]).then(([programs, objectives, targets]) => [
			programs == null ? 0 : programs,
			objectives == null ? 0 : objectives,
			targets == null ? 0 : targets,
		]);
	}

	function renderEmptyList(plansRoot) {
		plansRoot.innerHTML =
			'<div data-testid="strategic-plans-empty-state" class="kt-strategy-empty-wrap">' +
			'<p class="text-muted mb-0 kt-strategy-empty-msg">' +
			escapeHtml(__("No strategic plans yet. Create one to begin.")) +
			"</p></div>";
	}

	function renderPlanList(plansRoot, plans, selectedName, onSelect) {
		const items = plans
			.map((p) => {
				const slug = planNameSlug(p.name);
				const active = p.name === selectedName ? " is-active" : "";
				const statusRaw = p.status || "";
				const status = escapeHtml(statusRaw);
				const stKey = statusKeyFromRaw(statusRaw);
				const title = escapeHtml(p.strategic_plan_name || p.name);
				const showYears = !yearRangeAlreadyInName(p);
				const yearsHtml = showYears
					? `<span class="kt-strategy-plan-row__meta" data-testid="strategic-plan-row-years-${slug}">${formatYearRange(
							p
					  )}</span>`
					: `<span class="kt-strategy-plan-row__meta kt-strategy-plan-row__meta--empty" data-testid="strategic-plan-row-years-${slug}" aria-hidden="true"></span>`;
				const selectedMarker =
					p.name === selectedName
						? `<span class="kt-strategy-sr-only" data-testid="strategic-plan-row-selected-${slug}" aria-hidden="true"></span>`
						: "";
				return `<button type="button" class="kt-strategy-plan-row${active}" data-plan-name="${escapeHtml(
					p.name
				)}" data-testid="strategic-plan-row-${slug}">
					${selectedMarker}
					<span class="kt-strategy-plan-row__main">
						<span class="kt-strategy-plan-row__title" data-testid="strategic-plan-row-title-${slug}">${title}</span>
						${yearsHtml}
					</span>
					<span class="${statusBadgeClass(
						statusRaw
					)}" data-testid="strategic-plan-row-status-${slug}" data-kt-status="${escapeHtml(
						stKey
					)}">${status}</span>
				</button>`;
			})
			.join("");
		plansRoot.innerHTML = `<div class="kt-strategy-plan-list" data-testid="strategic-plan-list">${items}</div>`;
		plansRoot.querySelectorAll(".kt-strategy-plan-row").forEach((btn) => {
			btn.addEventListener("click", () => onSelect(btn.getAttribute("data-plan-name")));
		});
	}

	function renderDetailLoading(detailRoot) {
		detailRoot.innerHTML =
			'<div class="text-muted small">' + __("Loading…") + "</div>";
	}

	function renderDetail(
		detailRoot,
		plan,
		counts,
		onOpenBuilder,
		onEdit
	) {
		const years = formatYearRange(plan);
		const title = escapeHtml(plan.strategic_plan_name || plan.name);
		const statusRaw = plan.status || "";
		const status = escapeHtml(statusRaw);
		const statusKeyAttr = statusKeyFromRaw(statusRaw);
		const [cp, co, ct] = counts;
		const canWrite =
			typeof frappe !== "undefined" &&
			frappe.model &&
			frappe.model.can_write("Strategic Plan");
		const canRead =
			typeof frappe !== "undefined" &&
			frappe.model &&
			frappe.model.can_read("Strategic Plan");

		const builderBtn = canRead
			? `<button type="button" class="btn btn-primary btn-sm" data-testid="selected-plan-open-builder">${escapeHtml(
					__("Open Strategy Builder")
			  )}</button>`
			: "";
		const editBtn = canWrite
			? `<button type="button" class="btn btn-default btn-sm" data-testid="selected-plan-edit-plan">${escapeHtml(
					__("Edit Plan")
			  )}</button>`
			: "";

		detailRoot.innerHTML = `
			<div class="kt-strategy-detail-overview" data-testid="selected-plan-panel">
				<div class="kt-strategy-detail__overview-heading">${escapeHtml(__("Selected Plan Overview"))}</div>
				<div class="kt-strategy-detail__hero">
					<div class="kt-strategy-detail__hero-main">
						<h4 class="kt-strategy-detail__title" data-testid="selected-plan-title">${title}</h4>
						<div class="kt-strategy-detail__years-row" data-testid="selected-plan-years">
							<span class="kt-strategy-detail__years-label">${escapeHtml(__("Years"))}</span>
							<span class="kt-strategy-detail__years-value">${years}</span>
						</div>
					</div>
					<div class="kt-strategy-detail__hero-badge">
						<span class="${statusBadgeClass(
							statusRaw
						)}" data-testid="selected-plan-status" data-kt-status="${escapeHtml(statusKeyAttr)}">${status}</span>
					</div>
				</div>
				<div class="kt-strategy-detail__stats" role="group" aria-label="${escapeHtml(__("Plan hierarchy counts"))}">
					<div class="kt-strategy-detail-stat">
						<span class="kt-strategy-detail-stat__label">${escapeHtml(__("Programs"))}</span>
						<span class="kt-strategy-detail-stat__num" data-testid="selected-plan-program-count">${escapeHtml(
							String(cp)
						)}</span>
					</div>
					<div class="kt-strategy-detail-stat">
						<span class="kt-strategy-detail-stat__label">${escapeHtml(__("Objectives"))}</span>
						<span class="kt-strategy-detail-stat__num" data-testid="selected-plan-objective-count">${escapeHtml(
							String(co)
						)}</span>
					</div>
					<div class="kt-strategy-detail-stat">
						<span class="kt-strategy-detail-stat__label">${escapeHtml(__("Targets"))}</span>
						<span class="kt-strategy-detail-stat__num" data-testid="selected-plan-target-count">${escapeHtml(
							String(ct)
						)}</span>
					</div>
				</div>
				<div class="kt-strategy-detail__actions-group">
					<div class="kt-strategy-detail__actions d-flex flex-wrap gap-2">
						${builderBtn}
						${editBtn}
					</div>
				</div>
			</div>
		`;

		const ob = detailRoot.querySelector('[data-testid="selected-plan-open-builder"]');
		if (ob) {
			ob.addEventListener("click", onOpenBuilder);
		}
		const eb = detailRoot.querySelector('[data-testid="selected-plan-edit-plan"]');
		if (eb) {
			eb.addEventListener("click", onEdit);
		}
	}

	function renderDetailEmpty(detailRoot) {
		detailRoot.innerHTML =
			'<p class="text-muted mb-0 small">' +
			escapeHtml(
				__("Select a strategic plan from the list, or create one with New Strategic Plan above.")
			) +
			"</p>";
	}

	function loadStrategyWorkspace(plansRoot, detailRoot) {
		const gen = ++workspaceLoadGen;

		renderDetailLoading(detailRoot);
		fetchStrategicPlans()
			.then((plans) => {
				if (gen !== workspaceLoadGen) return;
				if (!plans.length) {
					renderEmptyList(plansRoot);
					renderDetailEmpty(detailRoot);
					return;
				}

				let selected = plans[0];
				const selectedName = selected.name;

				function selectByName(name) {
					selected = plans.find((p) => p.name === name) || selected;
					renderPlanList(plansRoot, plans, selected.name, selectByName);
					refreshDetail();
				}

				function refreshDetail() {
					renderDetailLoading(detailRoot);
					fetchCounts(selected.name)
						.then((counts) => {
							if (gen !== workspaceLoadGen) return;
							renderDetail(
								detailRoot,
								selected,
								counts,
								() => {
									frappe.set_route("strategy-builder", selected.name);
								},
								() => {
									frappe.set_route("Form", "Strategic Plan", selected.name);
								}
							);
						})
						.catch(() => {
							if (gen !== workspaceLoadGen) return;
							renderDetail(
								detailRoot,
								selected,
								[0, 0, 0],
								() => {
									frappe.set_route("strategy-builder", selected.name);
								},
								() => {
									frappe.set_route("Form", "Strategic Plan", selected.name);
								}
							);
						});
				}

				renderPlanList(plansRoot, plans, selectedName, selectByName);
				refreshDetail();
			})
			.catch(() => {
				if (gen !== workspaceLoadGen) return;
				plansRoot.innerHTML =
					'<p class="text-danger small">' +
					__("Could not load strategic plans.") +
					"</p>";
				detailRoot.innerHTML = "";
			});
	}

	function tryBindStrategyWorkspace() {
		if (!isStrategyWorkspaceRoute()) {
			return;
		}
		if (!injectStrategyMasterDetailShell()) {
			return;
		}
		const plansRoot = document.getElementById("kt-strategy-plans-root");
		const detailRoot = document.getElementById("kt-strategy-detail-root");
		if (!plansRoot || !detailRoot) {
			return;
		}
		loadStrategyWorkspace(plansRoot, detailRoot);
	}

	function scheduleStrategyWorkspaceBind() {
		syncStrategyShellClass();
		if (!isStrategyWorkspaceRoute()) {
			return;
		}
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(() => tryBindStrategyWorkspace());
		}
		setTimeout(tryBindStrategyWorkspace, 0);
		setTimeout(tryBindStrategyWorkspace, 400);
	}

	let hooksBound = false;
	let workspaceDomObserver = null;

	/** EditorJS / workspace body mounts after first paint; observe until .editor-js-container exists. */
	function ensureWorkspaceDomObserver() {
		if (workspaceDomObserver || typeof MutationObserver === "undefined") {
			return;
		}
		const target = document.body || document.documentElement;
		if (!target) {
			return;
		}
		workspaceDomObserver = new MutationObserver(function () {
			if (!isStrategyWorkspaceRoute() || document.getElementById("kt-strategy-plans-root")) {
				return;
			}
			tryBindStrategyWorkspace();
		});
		workspaceDomObserver.observe(target, { childList: true, subtree: true });
	}

	function bindStrategyWorkspaceHooks() {
		if (!hooksBound) {
			hooksBound = true;
			if (window.jQuery) {
				window.jQuery(document).on("page-change", scheduleStrategyWorkspaceBind);
				window.jQuery(document).on("app_ready", scheduleStrategyWorkspaceBind);
			}
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", scheduleStrategyWorkspaceBind);
			}
			ensureWorkspaceDomObserver();
		}
		syncStrategyShellClass();
		scheduleStrategyWorkspaceBind();
	}

	let pollStarted = false;

	/** Single interval: workspace DOM mounts after Desk startup; avoid stacking timers from repeated kicks. */
	function ensurePollStrategyWorkspace() {
		if (pollStarted) {
			return;
		}
		pollStarted = true;
		function tick() {
			if (isStrategyWorkspaceRoute() && !document.getElementById("kt-strategy-plans-root")) {
				tryBindStrategyWorkspace();
			}
			setTimeout(tick, 400);
		}
		tick();
	}

	/** Planning Authority (v1): no create on Strategic Plan — hide "New Strategic Plan" workspace shortcut. */
	function hideNewPlanShortcutIfNoCreate() {
		if (typeof frappe === "undefined" || typeof frappe.model === "undefined") {
			return;
		}
		if (frappe.model.can_create("Strategic Plan")) {
			syncStrategicPlanCreateButton();
			return;
		}
		syncStrategicPlanCreateButton();
		document.querySelectorAll("a[href*='Strategic%20Plan']").forEach((a) => {
			const href = a.getAttribute("href") || "";
			if (!href.includes("new")) {
				return;
			}
			const hide = (el) => {
				if (!el) {
					return;
				}
				el.style.display = "none";
			};
			hide(a.closest(".widget.shortcut-box"));
			hide(a.closest(".standard-sidebar-item"));
			hide(a.closest(".shortcut"));
			a.style.display = "none";
		});
	}

	function kickStrategyWorkspace() {
		bindStrategyWorkspaceHooks();
		ensurePollStrategyWorkspace();
		hideNewPlanShortcutIfNoCreate();
		[300, 1200].forEach((ms) => setTimeout(hideNewPlanShortcutIfNoCreate, ms));
	}

	/**
	 * This file loads after `desk.bundle.js` (Frappe hooks order). `app_ready` may have fired already,
	 * so do not rely only on `frappe.ready` after `load` — kick immediately and on deferred ticks.
	 */
	function bootstrapStrategyWorkspace() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kickStrategyWorkspace();
			if (typeof frappe.ready === "function") {
				frappe.ready(kickStrategyWorkspace);
			}
		}
		whenFrappeExists();
		window.addEventListener("load", kickStrategyWorkspace);
		[200, 800, 2000].forEach(function (ms) {
			setTimeout(kickStrategyWorkspace, ms);
		});
	}
	bootstrapStrategyWorkspace();
})();
