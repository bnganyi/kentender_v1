// Scoped UX for Strategy Management workspace only (Desk).
// Data-bound master–detail: KPIs, work tabs, Strategic Plan list + selected plan detail (counts from landing API).

(function () {
	let workspaceLoadGen = 0;
	/** @type {Array<object>|null} */
	let landingPlans = null;
	let selectedPlanName = null;
	let bindScheduled = false;
	/** @type {string|null} */
	let pendingLandingReselect = null;
	/** @type {'all'|'mywork'|'draft'|'active'|'archived'} */
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

	function shouldUseInboxMyWorkSemantics() {
		return userHasRole("Planning Authority") || userHasRole("Strategy Manager");
	}

	function passesMyWorkFilter(p) {
		if (!shouldUseInboxMyWorkSemantics()) {
			return true;
		}
		const uid = frappe.session.user;
		const mine = p.owner === uid;
		const st = String(p.status || "").trim();
		if (userHasRole("Planning Authority")) {
			return st === "Active";
		}
		if (userHasRole("Strategy Manager")) {
			return mine;
		}
		return mine;
	}

	function filterPlansForWorkTab(plans, tab) {
		if (!plans || !plans.length) {
			return [];
		}
		if (tab === "all") {
			return plans.slice();
		}
		if (tab === "mywork") {
			return plans.filter(passesMyWorkFilter);
		}
		if (tab === "draft") {
			return plans.filter(function (p) {
				return String(p.status || "").trim() === "Draft";
			});
		}
		if (tab === "active") {
			return plans.filter(function (p) {
				return String(p.status || "").trim() === "Active";
			});
		}
		if (tab === "archived") {
			return plans.filter(function (p) {
				return String(p.status || "").trim() === "Archived";
			});
		}
		return plans.slice();
	}

	function getDefaultWorkTab() {
		if (frappe.session && frappe.session.user === "Administrator") {
			return "all";
		}
		if (userHasRole("Planning Authority")) {
			return "active";
		}
		if (userHasRole("Strategy Manager")) {
			return "draft";
		}
		return "all";
	}

	function syncWorkTabButtons() {
		const wrap = document.getElementById("kt-strategy-work-tabs");
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
		const wrap = document.getElementById("kt-strategy-work-tabs");
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
			const plansRoot = document.getElementById("kt-strategy-plans-root");
			const detailRoot = document.getElementById("kt-strategy-detail-root");
			if (plansRoot && detailRoot) {
				renderLandingListAndDetail(plansRoot, detailRoot);
			}
		});
	}

	function refreshStrategyLanding(resumeName) {
		pendingLandingReselect = resumeName || selectedPlanName;
		const plansRoot = document.getElementById("kt-strategy-plans-root");
		const detailRoot = document.getElementById("kt-strategy-detail-root");
		if (!plansRoot || !detailRoot) {
			return;
		}
		plansRoot.dataset.ktStrategyLoaded = "0";
		loadStrategyWorkspace(plansRoot, detailRoot);
	}

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
			'<div class="kt-strategy-workspace-header kt-strategy-workspace-header--compact mb-2">' +
			'<div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-1">' +
			'<h2 class="kt-strategy-page-title h5 mb-0" data-testid="strategy-page-title">' +
			escapeHtml(__("Strategy Management")) +
			"</h2>" +
			'<button type="button" class="btn btn-xs btn-default" data-testid="strategy-workspace-back-desktop">' +
			escapeHtml(__("← Back to Desktop")) +
			"</button>" +
			"</div>" +
			'<p class="kt-strategy-page-intro text-muted mb-0" data-testid="strategy-page-intro">' +
			escapeHtml(__("Create and manage strategic plans and hierarchy.")) +
			"</p>" +
			'<div class="kt-strategy-header-create-slot" data-testid="strategic-plan-create-slot"></div>' +
			"</div>" +
			'<div class="kt-strategy-overview-metrics row g-2 mb-1" data-testid="strategy-overview-metrics">' +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-strategy-kpi-card kt-surface">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("Total plans")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value" data-testid="strategy-metric-total-plans">0</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-strategy-kpi-card kt-surface">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("Active")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value" data-testid="strategy-metric-active">0</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-strategy-kpi-card kt-surface">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("Draft")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value" data-testid="strategy-metric-draft">0</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3">' +
			'<div class="kt-strategy-kpi-card kt-surface">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("Programs (total)")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value" data-testid="strategy-metric-total-programs">0</div>' +
			"</div></div>" +
			"</div>" +
			'<div class="row kt-strategy-overview-metrics kt-strategy-overview-metrics--secondary g-2 mb-1" data-testid="strategy-overview-metrics-secondary">' +
			'<div class="col-6 col-lg-3 d-none" data-testid="strategy-kpi-my-drafts-wrap">' +
			'<div class="kt-strategy-kpi-card kt-surface">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("My drafts")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value" data-testid="strategy-metric-my-drafts">0</div>' +
			"</div></div>" +
			'<div class="col-6 col-lg-3" data-testid="strategy-kpi-archived-wrap">' +
			'<div class="kt-strategy-kpi-card kt-surface">' +
			'<div class="kt-strategy-kpi-label">' +
			escapeHtml(__("Archived")) +
			"</div>" +
			'<div class="kt-strategy-kpi-value" data-testid="strategy-metric-archived">0</div>' +
			"</div></div>" +
			"</div>" +
			'<div class="row g-2 kt-strategy-master-detail kt-strategy-master-detail--tight">' +
			'<div class="kt-strategy-col-list">' +
			'<div class="kt-strategy-section kt-surface" data-testid="strategic-plans-section">' +
			'<h4 class="kt-strategy-section__title">' +
			escapeHtml(__("Strategic Plans")) +
			"</h4>" +
			'<div class="kt-strategy-work-tabs mb-2" role="tablist" id="kt-strategy-work-tabs" data-testid="strategy-work-tabs">' +
			'<div class="btn-group btn-group-sm flex-wrap kt-strategy-tab-group" role="group">' +
			'<button type="button" class="btn btn-primary" data-testid="strategy-tab-all" data-kt-tab="all" role="tab" aria-selected="true">' +
			escapeHtml(__("All")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="strategy-tab-my-work" data-kt-tab="mywork" role="tab" aria-selected="false">' +
			escapeHtml(__("My Work")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="strategy-tab-draft" data-kt-tab="draft" role="tab" aria-selected="false">' +
			escapeHtml(__("Draft")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="strategy-tab-active" data-kt-tab="active" role="tab" aria-selected="false">' +
			escapeHtml(__("Active")) +
			"</button>" +
			'<button type="button" class="btn btn-default" data-testid="strategy-tab-archived" data-kt-tab="archived" role="tab" aria-selected="false">' +
			escapeHtml(__("Archived")) +
			"</button>" +
			"</div></div>" +
			'<div id="kt-strategy-plans-root"></div>' +
			"</div></div>" +
			'<div class="kt-strategy-col-detail">' +
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

	function removeStrategyLandingIfWrongRoute() {
		document.querySelectorAll(".kt-strategy-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-strategy-shell");
		landingPlans = null;
		selectedPlanName = null;
		activeWorkTab = "all";
		workTabInitialized = false;
		workTabBindingsDone = false;
		bindScheduled = false;
		pendingLandingReselect = null;
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

	function updateOverviewMetrics(portfolio) {
		const p = portfolio || {};
		const elTotal = document.querySelector('[data-testid="strategy-metric-total-plans"]');
		const elActive = document.querySelector('[data-testid="strategy-metric-active"]');
		const elDraft = document.querySelector('[data-testid="strategy-metric-draft"]');
		const elProg = document.querySelector('[data-testid="strategy-metric-total-programs"]');
		const elArch = document.querySelector('[data-testid="strategy-metric-archived"]');
		const elMyD = document.querySelector('[data-testid="strategy-metric-my-drafts"]');
		const wrapD = document.querySelector('[data-testid="strategy-kpi-my-drafts-wrap"]');
		if (elTotal) {
			const v = String(p.total_plans != null ? p.total_plans : 0);
			elTotal.textContent = v;
			elTotal.title = v;
		}
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
		if (elProg) {
			const v = String(p.total_programs != null ? p.total_programs : 0);
			elProg.textContent = v;
			elProg.title = v;
		}
		if (elArch) {
			const v = String(p.archived_count != null ? p.archived_count : 0);
			elArch.textContent = v;
			elArch.title = v;
		}
		if (elMyD) {
			const v = String(p.my_drafts_count != null ? p.my_drafts_count : 0);
			elMyD.textContent = v;
			elMyD.title = v;
		}
		if (wrapD) {
			wrapD.classList.toggle("d-none", !userHasRole("Strategy Manager"));
		}
	}

	function fetchLandingData() {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "kentender_strategy.api.landing.get_strategy_landing_data",
				callback(r) {
					if (r.exc) {
						reject(r);
						return;
					}
					resolve(r.message || { portfolio: {}, plans: [] });
				},
				error(err) {
					reject(err);
				},
			});
		});
	}

	function renderEmptyList(plansRoot, emptyOpts) {
		emptyOpts = emptyOpts || {};
		const filtered = emptyOpts.filteredEmpty;
		const msg = filtered ? __("No strategic plans match this filter.") : __("No strategic plans yet.");
		const sub = filtered ? "" : __("Create one to begin.");
		plansRoot.innerHTML =
			'<div data-testid="strategic-plans-empty-state" class="kt-strategy-empty-wrap">' +
			'<p class="text-muted mb-2 kt-strategy-empty-msg">' +
			escapeHtml(msg) +
			"</p>" +
			(sub ? '<p class="text-muted mb-0 small">' + escapeHtml(sub) + "</p>" : "") +
			"</div>";
	}

	function planIsMine(p) {
		const uid = frappe.session.user;
		return p.owner === uid;
	}

	function rowNeedsActionCue(p) {
		const st = String(p.status || "").trim();
		if (st === "Draft" && userHasRole("Strategy Manager") && planIsMine(p)) {
			return frappe.model && frappe.model.can_write("Strategic Plan", p.name);
		}
		if (st === "Active" && userHasRole("Planning Authority")) {
			return true;
		}
		return false;
	}

	function rowActionCueLabel(p) {
		const st = String(p.status || "").trim();
		if (st === "Draft" && userHasRole("Strategy Manager") && planIsMine(p)) {
			return __("In progress");
		}
		if (st === "Active" && userHasRole("Planning Authority")) {
			return __("In force");
		}
		return "";
	}

	function renderPlanList(plansRoot, plans, selectedName, onSelect, opts) {
		opts = opts || {};
		const items = plans
			.map((p) => {
				const slug = planNameSlug(p.name);
				const active = p.name === selectedName ? " is-active" : "";
				const statusRaw = p.status || "";
				const status = escapeHtml(statusRaw);
				const stKey = statusKeyFromRaw(statusRaw);
				const fullTitle = p.strategic_plan_name || p.name;
				const title = escapeHtml(fullTitle);
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
				const actionCue = rowNeedsActionCue(p) ? " kt-strategy-plan-row--action" : "";
				const cueText = rowActionCueLabel(p);
				const cueHtml = cueText
					? `<span class="kt-strategy-plan-row__cue text-muted" data-testid="strategic-plan-row-cue-${slug}">${escapeHtml(
							cueText
						)}</span>`
					: "";
				const metaSep = cueHtml ? " · " : "";
				const badgeExtra =
					userHasRole("Planning Authority") && String(statusRaw).trim() === "Active"
						? " kt-strategy-badge--active-pa"
						: "";
				return `<button type="button" class="kt-strategy-plan-row${active}${actionCue}" data-plan-name="${escapeHtml(
					p.name
				)}" data-testid="strategic-plan-row-${slug}">
					${selectedMarker}
					<span class="kt-strategy-plan-row__main">
						<span class="kt-strategy-plan-row__title" data-testid="strategic-plan-row-title-${slug}" title="${escapeHtml(
							fullTitle
						)}">${title}</span>
						<span class="kt-strategy-plan-row__meta" data-testid="strategic-plan-row-meta-${slug}">${yearsHtml}${metaSep}${cueHtml}</span>
					</span>
					<span class="${statusBadgeClass(
						statusRaw
					)}${badgeExtra}" data-testid="strategic-plan-row-status-${slug}" data-kt-status="${escapeHtml(
						stKey
					)}">${status}</span>
				</button>`;
			})
			.join("");
		plansRoot.innerHTML = `<div class="kt-strategy-plan-list" data-testid="strategic-plan-list">${items}</div>`;
		const rowList = plansRoot.querySelector('[data-testid="strategic-plan-list"]');
		if (rowList && typeof opts.preserveScrollTop === "number") {
			rowList.scrollTop = opts.preserveScrollTop;
		}
		const selectedSlug = planNameSlug(selectedName);
		const selectedEl = plansRoot.querySelector(`[data-testid="strategic-plan-row-${selectedSlug}"]`);
		if (rowList && selectedEl && opts.ensureSelectedVisible) {
			const rowRect = selectedEl.getBoundingClientRect();
			const listRect = rowList.getBoundingClientRect();
			if (rowRect.top < listRect.top || rowRect.bottom > listRect.bottom) {
				selectedEl.scrollIntoView({ block: "nearest" });
			}
		}
		plansRoot.querySelectorAll(".kt-strategy-plan-row").forEach((btn) => {
			btn.addEventListener("click", () => onSelect(btn.getAttribute("data-plan-name")));
		});
	}

	function syncPlanListSelection(plansRoot, selectedName, opts) {
		opts = opts || {};
		const rowList = plansRoot.querySelector('[data-testid="strategic-plan-list"]');
		if (!rowList) {
			return;
		}
		if (typeof opts.preserveScrollTop === "number") {
			rowList.scrollTop = opts.preserveScrollTop;
		}
		plansRoot.querySelectorAll(".kt-strategy-plan-row").forEach((btn) => {
			const isActive = btn.getAttribute("data-plan-name") === selectedName;
			btn.classList.toggle("is-active", isActive);
		});
		const selectedSlug = planNameSlug(selectedName);
		const selectedEl = plansRoot.querySelector(`[data-testid="strategic-plan-row-${selectedSlug}"]`);
		if (selectedEl && opts.ensureSelectedVisible) {
			const rowRect = selectedEl.getBoundingClientRect();
			const listRect = rowList.getBoundingClientRect();
			if (rowRect.top < listRect.top || rowRect.bottom > listRect.bottom) {
				selectedEl.scrollIntoView({ block: "nearest" });
			}
		}
	}

	function getSelectedPlan() {
		if (!landingPlans || !selectedPlanName) {
			return null;
		}
		return landingPlans.find(function (p) {
			return p.name === selectedPlanName;
		}) || null;
	}

	function renderDetailPanel(detailRoot, plan, opts) {
		opts = opts || {};
		if (!plan) {
			const msg = opts.noPlansInSystem
				? __("When you create a strategic plan, details will appear here.")
				: __("Select a strategic plan from the list, or create one with New Strategic Plan above.");
			detailRoot.innerHTML =
				'<p class="text-muted mb-0 small" data-testid="strategy-detail-stub">' + escapeHtml(msg) + "</p>";
			return;
		}

		const cp = plan.program_count != null ? plan.program_count : 0;
		const co = plan.objective_count != null ? plan.objective_count : 0;
		const ct = plan.target_count != null ? plan.target_count : 0;
		const years = formatYearRange(plan);
		const title = escapeHtml(plan.strategic_plan_name || plan.name);
		const statusRaw = plan.status || "";
		const status = escapeHtml(statusRaw);
		const statusKeyAttr = statusKeyFromRaw(statusRaw);
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
			ob.addEventListener("click", () => {
				frappe.set_route("strategy-builder", plan.name);
			});
		}
		const eb = detailRoot.querySelector('[data-testid="selected-plan-edit-plan"]');
		if (eb) {
			eb.addEventListener("click", () => {
				frappe.set_route("Form", "Strategic Plan", plan.name);
			});
		}
	}

	function renderLandingListAndDetail(plansRoot, detailRoot) {
		const plans = landingPlans || [];
		ensureWorkTabBindings();
		syncWorkTabButtons();

		function selectByName(name) {
			const rowList = plansRoot.querySelector('[data-testid="strategic-plan-list"]');
			const prevScrollTop = rowList ? rowList.scrollTop : 0;
			selectedPlanName = name;
			const p = plans.find(function (x) {
				return x.name === name;
			});
			if (!p) {
				return;
			}
			selectedPlanName = p.name;
			syncPlanListSelection(plansRoot, selectedPlanName, {
				preserveScrollTop: prevScrollTop,
				ensureSelectedVisible: true,
			});
			renderDetailPanel(detailRoot, p);
			syncStrategicPlanCreateButton();
		}

		if (!plans.length) {
			selectedPlanName = null;
			pendingLandingReselect = null;
			renderEmptyList(plansRoot);
			renderDetailPanel(detailRoot, null, { noPlansInSystem: true });
			syncStrategicPlanCreateButton();
			return;
		}

		const view = filterPlansForWorkTab(plans, activeWorkTab);

		if (!view.length) {
			selectedPlanName = null;
			pendingLandingReselect = null;
			renderEmptyList(plansRoot, { filteredEmpty: true });
			renderDetailPanel(detailRoot, null, {});
			syncStrategicPlanCreateButton();
			return;
		}

		let pickName = view[0].name;
		if (pendingLandingReselect && view.some(function (x) { return x.name === pendingLandingReselect; })) {
			pickName = pendingLandingReselect;
		} else if (selectedPlanName && view.some(function (x) { return x.name === selectedPlanName; })) {
			pickName = selectedPlanName;
		}
		pendingLandingReselect = null;
		selectedPlanName = pickName;

		renderPlanList(plansRoot, view, selectedPlanName, selectByName);
		syncPlanListSelection(plansRoot, selectedPlanName);
		renderDetailPanel(detailRoot, getSelectedPlan());
		syncStrategicPlanCreateButton();
	}

	function loadStrategyWorkspace(plansRoot, detailRoot) {
		if (plansRoot.dataset.ktStrategyLoading === "1") {
			return;
		}
		if (plansRoot.dataset.ktStrategyLoaded === "1" && landingPlans) {
			return;
		}
		plansRoot.dataset.ktStrategyLoading = "1";
		const gen = ++workspaceLoadGen;

		if (!landingPlans) {
			detailRoot.innerHTML =
				'<div class="text-muted small" data-testid="strategy-detail-loading">' + escapeHtml(__("Loading…")) + "</div>";
		}

		fetchLandingData()
			.then((payload) => {
				if (gen !== workspaceLoadGen) return;
				plansRoot.dataset.ktStrategyLoading = "0";
				plansRoot.dataset.ktStrategyLoaded = "1";
				const portfolio = payload.portfolio || {};
				const pls = payload.plans || [];
				landingPlans = pls;
				updateOverviewMetrics(portfolio);

				if (!workTabInitialized) {
					activeWorkTab = getDefaultWorkTab();
					workTabInitialized = true;
				}

				renderLandingListAndDetail(plansRoot, detailRoot);
			})
			.catch(() => {
				if (gen !== workspaceLoadGen) return;
				plansRoot.dataset.ktStrategyLoading = "0";
				plansRoot.dataset.ktStrategyLoaded = "0";
				landingPlans = null;
				selectedPlanName = null;
				plansRoot.innerHTML =
					'<p class="text-danger small">' + escapeHtml(__("Could not load strategic plans.")) + "</p>";
				detailRoot.innerHTML = "";
				updateOverviewMetrics({
					total_plans: 0,
					draft_count: 0,
					active_count: 0,
					archived_count: 0,
					my_drafts_count: 0,
					total_programs: 0,
				});
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

	function requestStrategyBind(delayMs) {
		if (bindScheduled) {
			return;
		}
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindStrategyWorkspace();
		}, delayMs || 0);
	}

	function scheduleStrategyWorkspaceBind() {
		if (!isStrategyWorkspaceRoute()) {
			removeStrategyLandingIfWrongRoute();
			return;
		}
		syncStrategyShellClass();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(() => requestStrategyBind(0));
		} else {
			requestStrategyBind(0);
		}
		requestStrategyBind(120);
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
			if (!isStrategyWorkspaceRoute()) {
				removeStrategyLandingIfWrongRoute();
			} else if (!document.getElementById("kt-strategy-plans-root")) {
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
		setTimeout(scheduleStrategyWorkspaceBind, 400);
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

	/* Expose for Doc hooks / future refresh after builder edits */
	window.ktRefreshStrategyLanding = refreshStrategyLanding;
})();
