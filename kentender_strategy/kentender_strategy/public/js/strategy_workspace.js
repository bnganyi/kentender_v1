// Strategy Management workspace — Portfolio Hub with live backend wiring.
(function () {
	const WS_LABEL = "Strategy Management";
	let bound = false;
	let observer = null;

	function slug(v) {
		return String(v || "")
			.toLowerCase()
			.replace(/\s+/g, "-");
	}

	function isStrategyWorkspaceRoute() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const w = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					return slug(w) === slug(WS_LABEL);
				}
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const href = (window.location && (window.location.pathname + window.location.hash)) || "";
			return decodeURIComponent(href).toLowerCase().includes("strategy-management");
		} catch (e) {
			return false;
		}
	}

	function resolveMount() {
		const page =
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]');
		if (page) {
			return (
				page.querySelector(".layout-main-section .editor-js-container") ||
				page.querySelector(".editor-js-container") ||
				page.querySelector(".layout-main-section")
			);
		}
		return document.querySelector(".editor-js-container");
	}

	function staticHierarchyWorkbenchHtml() {
		return `
			<div class="kt-strategy-v2-shell" data-testid="strategy-workbench-v2">
				<div class="kt-strategy-v2-hero">
					<div class="kt-strategy-v2-breadcrumb" data-testid="strategy-breadcrumb">All Strategic Plans › Ministry of Health 2026-2030</div>
					<div class="kt-strategy-v2-hero__row">
						<div>
							<h2 class="kt-strategy-v2-hero__title" data-testid="strategy-hero-title">Ministry of Health Strategic Plan 2026-2030</h2>
							<p class="kt-strategy-v2-hero__subtitle" data-testid="strategy-page-intro">Comprehensive modernization of public healthcare infrastructure and digital diagnostics.</p>
						</div>
						<div class="kt-strategy-v2-summary__actions">
							<button type="button" class="kt-strategy-v2-btn kt-strategy-v2-btn--ghost">Export Report</button>
							<button type="button" class="kt-strategy-v2-btn kt-strategy-v2-btn--primary" data-testid="strategic-plan-create-button">Edit Plan</button>
						</div>
					</div>
				</div>

				<div class="kt-strategy-v2-metrics" data-testid="strategy-metric-overall">
					<article class="kt-strategy-v2-metric-card">
						<div class="kt-strategy-v2-metric-head"><span class="kt-strategy-v2-metric-label">Overall Completion</span><span class="material-symbols-outlined">trending_up</span></div>
						<div class="kt-strategy-v2-metric-value">64%</div>
						<div class="kt-strategy-v2-progress"><span style="width:64%"></span></div>
					</article>
					<article class="kt-strategy-v2-metric-card">
						<div class="kt-strategy-v2-metric-head"><span class="kt-strategy-v2-metric-label">Active Programs</span><span class="material-symbols-outlined">layers</span></div>
						<div class="kt-strategy-v2-metric-value">12</div>
						<div class="kt-strategy-v2-metric-subnote"><span class="material-symbols-outlined">check_circle</span>3 Completed this quarter</div>
					</article>
					<article class="kt-strategy-v2-metric-card">
						<div class="kt-strategy-v2-metric-head"><span class="kt-strategy-v2-metric-label">Critical Risks</span><span class="material-symbols-outlined">warning</span></div>
						<div class="kt-strategy-v2-metric-value">02</div>
						<div class="kt-strategy-v2-metric-subnote is-danger">Action required in 'Digital Health'</div>
					</article>
					<article class="kt-strategy-v2-metric-card kt-strategy-v2-metric-card--milestone">
						<div class="kt-strategy-v2-metric-head"><span class="kt-strategy-v2-metric-label">Next Milestone</span><span class="material-symbols-outlined">calendar_today</span></div>
						<div class="kt-strategy-v2-metric-date">Oct 12, 2024</div>
						<p class="kt-strategy-v2-metric-note">Procurement Phase II Close</p>
					</article>
				</div>

				<section class="kt-strategy-v2-hierarchy" data-testid="strategy-hierarchy-workbench">
					<header class="kt-strategy-v2-hierarchy__head">
						<div class="kt-strategy-v2-hierarchy__legend">
							<h4>Strategic Hierarchy</h4>
							<div class="kt-strategy-v2-hierarchy__legend-items">
								<span class="kt-dot is-green"></span><span>On Track</span>
								<span class="kt-dot is-amber"></span><span>At Risk</span>
							</div>
						</div>
						<div class="kt-strategy-v2-hierarchy__tools">
							<button type="button"><span class="material-symbols-outlined">unfold_more</span></button>
							<button type="button"><span class="material-symbols-outlined">filter_list</span></button>
						</div>
					</header>
					<div class="kt-strategy-v2-hierarchy__body">
						<div class="kt-tree-program">
							<div class="kt-tree-node kt-tree-node--program">
								<button type="button" class="kt-tree-expand"><span class="material-symbols-outlined">keyboard_arrow_down</span></button>
								<div class="kt-tree-icon"><span class="material-symbols-outlined">vaccines</span></div>
								<div class="kt-tree-content">
									<div class="kt-tree-title-row"><span class="kt-tree-code">P1</span><h5>National Immunization Infrastructure Upgrade</h5><span class="kt-pill is-green">Active</span></div>
									<div class="kt-tree-meta-row"><div class="kt-inline-progress"><div class="kt-progress-track"><span style="width:78%"></span></div><em>78%</em></div><span>4 Objectives · 12 Targets</span></div>
								</div>
							</div>
							<div class="kt-tree-children">
								<div class="kt-tree-connector-vertical"></div>
								<div class="kt-tree-branch">
									<div class="kt-tree-connector-horizontal"></div>
									<div class="kt-tree-node kt-tree-node--objective">
										<button type="button" class="kt-tree-expand"><span class="material-symbols-outlined">keyboard_arrow_down</span></button>
										<div class="kt-tree-content">
											<div class="kt-tree-title-row"><span class="kt-tree-code">OBJ 1.1</span><h6>Cold-Chain Storage Modernization (Region A)</h6><span class="kt-pill is-amber">At Risk</span></div>
											<div class="kt-tree-meta-row"><div class="kt-inline-progress is-amber"><div class="kt-progress-track"><span style="width:45%"></span></div><em>45%</em></div><span>3 Targets</span></div>
										</div>
									</div>
									<div class="kt-tree-targets">
										<div class="kt-tree-connector-vertical"></div>
										<div class="kt-tree-target">
											<div class="kt-tree-connector-horizontal"></div>
											<div class="kt-tree-target-card is-primary">
												<div class="kt-tree-target-head"><span>TARGET 1.1.1</span><span>Due: Nov 20, 2024</span></div>
												<p>Procurement of 50 Ultra-Low Temperature Freezers</p>
												<div class="kt-tree-target-progress"><div class="kt-progress-track"><span style="width:30%"></span></div><em>15 / 50 Delivered</em></div>
											</div>
										</div>
										<div class="kt-tree-target">
											<div class="kt-tree-connector-horizontal"></div>
											<div class="kt-tree-target-card">
												<div class="kt-tree-target-head"><span>TARGET 1.1.2</span><span>Due: Dec 15, 2024</span></div>
												<p>Installation and Training across 12 Regional Hubs</p>
												<div class="kt-tree-target-progress"><div class="kt-progress-track"><span style="width:0%"></span></div><em>0 / 12 Locations</em></div>
											</div>
										</div>
									</div>
								</div>
								<div class="kt-tree-branch">
									<div class="kt-tree-connector-horizontal"></div>
									<div class="kt-tree-node kt-tree-node--objective">
										<button type="button" class="kt-tree-expand"><span class="material-symbols-outlined">keyboard_arrow_right</span></button>
										<div class="kt-tree-content">
											<div class="kt-tree-title-row"><span class="kt-tree-code">OBJ 1.2</span><h6>Mobile Vaccination Fleet Acquisition</h6><span class="kt-pill is-green">On Track</span></div>
										</div>
									</div>
								</div>
							</div>
						</div>

						<div class="kt-tree-program is-collapsed">
							<div class="kt-tree-node kt-tree-node--program">
								<button type="button" class="kt-tree-expand"><span class="material-symbols-outlined">keyboard_arrow_right</span></button>
								<div class="kt-tree-icon"><span class="material-symbols-outlined">clinical_notes</span></div>
								<div class="kt-tree-content">
									<div class="kt-tree-title-row"><span class="kt-tree-code">P2</span><h5>Digital Health Records System Rollout</h5><span class="kt-pill is-blue">Draft</span></div>
									<div class="kt-tree-meta-row"><div class="kt-inline-progress"><div class="kt-progress-track"><span style="width:12%"></span></div><em>12%</em></div><span>2 Objectives · 6 Targets</span></div>
								</div>
							</div>
						</div>

						<button type="button" class="kt-strategy-v2-add-program"><span class="material-symbols-outlined">add_circle</span>Add New Program</button>
					</div>
				</section>

				<section class="kt-strategy-v2-lower">
					<div class="kt-strategy-v2-activity" data-testid="strategy-activity-feed">
						<h4>Recent Workbench Activity</h4>
						<ul>
							<li><span class="kt-activity-icon"><span class="material-symbols-outlined">update</span></span><div class="kt-activity-copy"><strong>Sarah Jenkins</strong><p>updated target <strong>1.1.1</strong></p><small>2 hours ago · Procurement status changed from 'Ordered' to 'Shipped'</small></div></li>
							<li><span class="kt-activity-icon"><span class="material-symbols-outlined">add</span></span><div class="kt-activity-copy"><strong>Marcus Thorne</strong><p>added Objective <strong>1.3</strong></p><small>Yesterday · New objective for Rural Health Outreach</small></div></li>
							<li><span class="kt-activity-icon is-alert"><span class="material-symbols-outlined">report</span></span><div class="kt-activity-copy"><strong>System Alert:</strong><p>Delay in shipment for <strong>OBJ 1.1</strong></p><small>3 days ago · Automatic status change to 'At Risk'</small></div></li>
						</ul>
					</div>
					<aside class="kt-strategy-v2-side">
						<article class="kt-strategy-v2-insights" data-testid="strategy-insights-card">
							<h4>Insights Engine</h4>
							<p>AI analysis suggests a potential 12% budget overrun on Program 1 due to global supply chain inflation.</p>
							<button type="button" class="kt-strategy-v2-btn kt-strategy-v2-btn--light">View Recommendations</button>
						</article>
						<article class="kt-strategy-v2-stakeholders">
							<h4>Stakeholders</h4>
							<div class="kt-stakeholders-avatars"><span>A</span><span>M</span><span>F</span><span>+8</span></div>
							<button type="button">Manage Team Access <span class="material-symbols-outlined">arrow_forward</span></button>
						</article>
					</aside>
				</section>
			</div>
		`;
	}

	/* ── Portfolio Hub shell skeleton (rendered immediately on mount) ── */
	function portfolioHubShellHtml() {
		return `
			<div class="kt-sph-shell" data-testid="strategy-portfolio-hub">
				<header class="kt-sph-topbar" data-testid="sph-topbar">
					<div class="kt-sph-topbar__left">
						<h2 class="kt-sph-topbar__title">Strategic Alignment</h2>
						<div class="kt-sph-search-wrap">
							<span class="material-symbols-outlined kt-sph-search-icon">search</span>
							<input class="kt-sph-search" placeholder="Search strategies..." type="text" data-testid="sph-search-input">
						</div>
					</div>
					<div class="kt-sph-topbar__right">
						<button type="button" class="kt-sph-icon-btn"><span class="material-symbols-outlined">notifications</span></button>
						<button type="button" class="kt-sph-icon-btn"><span class="material-symbols-outlined">history</span></button>
						<div class="kt-sph-avatar"></div>
					</div>
				</header>

				<main class="kt-sph-main">
					<div class="kt-sph-page-header">
						<div>
							<nav class="kt-sph-breadcrumb" data-testid="sph-breadcrumb">
								<span>Portfolio</span>
								<span class="material-symbols-outlined">chevron_right</span>
								<span class="kt-sph-breadcrumb__active">Active Plans</span>
							</nav>
							<h1 class="kt-sph-page-title" data-testid="sph-page-title">Strategy Management</h1>
						</div>
						<div class="kt-sph-page-actions">
							<button type="button" class="kt-sph-btn kt-sph-btn--outline">Export Portfolio</button>
							<button type="button" class="kt-sph-btn kt-sph-btn--primary" data-testid="sph-create-plan-btn">
								<span class="material-symbols-outlined">add</span>Create New Plan
							</button>
						</div>
					</div>

					<div class="kt-sph-metrics" data-testid="sph-metrics-grid" data-sph-metrics>
						${skeletonKpiHtml()}
					</div>

					<div class="kt-sph-plans-grid" data-testid="sph-plans-grid" data-sph-plans>
						${skeletonCardsHtml()}
					</div>

					<section class="kt-sph-activity-section">
						<h3 class="kt-sph-section-heading">Lineage Activity</h3>
						<div class="kt-sph-table-wrap">
							<table class="kt-sph-table" data-testid="sph-activity-table" data-sph-activity>
								<thead>
									<tr><th>Time</th><th>Action</th><th>Plan</th><th>User</th></tr>
								</thead>
								<tbody data-sph-activity-body>
									<tr><td colspan="4" class="kt-sph-td-muted kt-sph-loading-cell">Loading activity…</td></tr>
								</tbody>
							</table>
						</div>
					</section>
				</main>
			</div>
		`;
	}

	function skeletonKpiHtml() {
		return [
			{ label: "Total Budget", value: "—", sub: "Pending field configuration", subClass: "" },
			{ label: "Active Programs", value: "—", sub: "Loading…", subClass: "" },
			{ label: "Success Rate", value: "—", sub: "", subClass: "" },
			{ label: "Draft Plans", value: "—", sub: "Loading…", subClass: "kt-sph-metric-sub--warn" },
		]
			.map(
				(k) => `
			<div class="kt-sph-metric-card">
				<p class="kt-sph-metric-label">${k.label}</p>
				<h3 class="kt-sph-metric-value">${k.value}</h3>
				${k.sub ? `<p class="kt-sph-metric-sub ${k.subClass}">${k.sub}</p>` : ""}
			</div>`
			)
			.join("");
	}

	function skeletonCardsHtml() {
		return `<div class="kt-sph-skeleton-row">Loading plans…</div>`;
	}

	/* ── Status helpers ── */
	function chipClass(status) {
		const map = {
			Active: "kt-sph-chip--active",
			Draft: "kt-sph-chip--draft",
			Submitted: "kt-sph-chip--submitted",
			Approved: "kt-sph-chip--approved",
			Archived: "kt-sph-chip--archived",
		};
		return map[status] || "kt-sph-chip--draft";
	}

	function prettyTime(isoStr) {
		if (!isoStr) return "";
		try {
			if (typeof frappe !== "undefined" && frappe.datetime && frappe.datetime.prettyDate) {
				return frappe.datetime.prettyDate(isoStr);
			}
			const d = new Date(isoStr.replace(" ", "T"));
			const diff = Date.now() - d.getTime();
			const mins = Math.floor(diff / 60000);
			if (mins < 2) return "just now";
			if (mins < 60) return `${mins}m ago`;
			const hrs = Math.floor(mins / 60);
			if (hrs < 24) return `${hrs}h ago`;
			const days = Math.floor(hrs / 24);
			if (days === 1) return "Yesterday";
			return `${days} days ago`;
		} catch (_) {
			return isoStr;
		}
	}

	/* ── Plan card HTML builder ── */
	function planCardHtml(plan) {
		const title = plan.strategic_plan_name || plan.name;
		const status = plan.status || "Draft";
		const fyLabel = plan.start_year && plan.end_year ? `FY ${plan.start_year} – ${plan.end_year}` : "";
		const programs = plan.program_count != null ? plan.program_count : "—";
		const objectives = plan.objective_count != null ? plan.objective_count : "—";
		const isDraft = status === "Draft" || status === "Submitted";
		const modifiedStr = prettyTime(plan.modified);

		const footer = isDraft
			? `<div class="kt-sph-draft-hint">
					<span class="material-symbols-outlined kt-sph-draft-hint__icon">edit_note</span>
					<span class="kt-sph-draft-hint__text">Last edited ${modifiedStr}</span>
				</div>
				<a href="#" class="kt-sph-card-cta" data-plan="${encodeURIComponent(plan.name)}">Continue Setup <span class="material-symbols-outlined">edit</span></a>`
			: `<div class="kt-sph-avatar-stack">
					<span class="kt-sph-avatar kt-sph-avatar--slate-300"></span>
					<span class="kt-sph-avatar kt-sph-avatar--slate-400"></span>
				</div>
				<a href="#" class="kt-sph-card-cta" data-plan="${encodeURIComponent(plan.name)}">View Workbench <span class="material-symbols-outlined">arrow_forward</span></a>`;

		return `
			<div class="kt-sph-plan-card" data-testid="sph-plan-card" data-plan-name="${encodeURIComponent(plan.name)}">
				<div class="kt-sph-card-header">
					<div>
						<div class="kt-sph-card-header__row">
							<span class="kt-sph-chip ${chipClass(status)}">${status}</span>
							${fyLabel ? `<span class="kt-sph-fiscal-year">${fyLabel}</span>` : ""}
						</div>
						<h3 class="kt-sph-card-title">${title}</h3>
					</div>
					<button type="button" class="kt-sph-icon-btn"><span class="material-symbols-outlined">more_vert</span></button>
				</div>
				<div class="kt-sph-card-body">
					<div class="kt-sph-stat">
						<p class="kt-sph-stat-label">Budget</p>
						<p class="kt-sph-stat-value">—</p>
					</div>
					<div class="kt-sph-stat">
						<p class="kt-sph-stat-label">Programs</p>
						<p class="kt-sph-stat-value">${programs}</p>
					</div>
					<div class="kt-sph-stat">
						<p class="kt-sph-stat-label">Objectives</p>
						<p class="kt-sph-stat-value">${objectives}</p>
					</div>
				</div>
				<div class="kt-sph-card-footer${isDraft ? " kt-sph-card-footer--draft" : ""}">
					${footer}
				</div>
			</div>`;
	}

	function emptyStateCardHtml() {
		return `
			<div class="kt-sph-plan-card kt-sph-plan-card--empty" data-testid="sph-create-new-card">
				<div class="kt-sph-empty-icon-wrap">
					<span class="material-symbols-outlined">add</span>
				</div>
				<h4 class="kt-sph-empty-title">Create New Strategy</h4>
				<p class="kt-sph-empty-text">Define a new planning horizon and budget lineage</p>
			</div>`;
	}

	/* ── DOM patch helpers ── */
	function applyPortfolioData(shell, payload) {
		const portfolio = payload.portfolio || {};
		const plans = Array.isArray(payload.plans) ? payload.plans : [];

		/* KPI cards */
		const metricsEl = shell.querySelector("[data-sph-metrics]");
		if (metricsEl) {
			const activeCount = portfolio.active_count || 0;
			const draftCount = portfolio.draft_count || 0;
			const totalPlans = portfolio.total_plans || 0;
			const totalPrograms = portfolio.total_programs || 0;
			metricsEl.innerHTML = `
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Total Budget</p>
					<h3 class="kt-sph-metric-value">—</h3>
					<p class="kt-sph-metric-sub">Pending field configuration</p>
				</div>
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Active Programs</p>
					<h3 class="kt-sph-metric-value">${totalPrograms}</h3>
					<p class="kt-sph-metric-sub">Across ${activeCount} Active Plan${activeCount !== 1 ? "s" : ""}</p>
				</div>
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Success Rate</p>
					<h3 class="kt-sph-metric-value">—</h3>
					<p class="kt-sph-metric-sub">Pending target completion data</p>
				</div>
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Draft Plans</p>
					<h3 class="kt-sph-metric-value">${draftCount}</h3>
					<p class="kt-sph-metric-sub kt-sph-metric-sub--warn">${draftCount > 0 ? "Awaiting Review" : `${totalPlans} plan${totalPlans !== 1 ? "s" : ""} total`}</p>
				</div>`;
		}

		/* Plan cards */
		const plansEl = shell.querySelector("[data-sph-plans]");
		if (plansEl) {
			const cardsHtml = plans.map((p) => planCardHtml(p)).join("");
			plansEl.innerHTML = cardsHtml + emptyStateCardHtml();
		}

		/* Activity table body — keep static rows for now (deferred to B7) */
		const activityBody = shell.querySelector("[data-sph-activity-body]");
		if (activityBody) {
			activityBody.innerHTML = `
				<tr>
					<td class="kt-sph-td-muted">—</td>
					<td><div class="kt-sph-action-cell"><span class="kt-sph-dot kt-sph-dot--primary"></span><span class="kt-sph-action-label">Activity feed pending wiring</span></div></td>
					<td>—</td><td>—</td>
				</tr>`;
		}

		/* Client-side search */
		wireSearch(shell, plans);
	}

	function wireSearch(shell, allPlans) {
		const input = shell.querySelector("[data-testid='sph-search-input']");
		const grid = shell.querySelector("[data-sph-plans]");
		if (!input || !grid) return;
		input.addEventListener("input", function () {
			const term = (this.value || "").toLowerCase().trim();
			const matched = term
				? allPlans.filter(function (p) {
						const title = (p.strategic_plan_name || p.name || "").toLowerCase();
						const status = (p.status || "").toLowerCase();
						const fy =
							p.start_year && p.end_year ? `${p.start_year} ${p.end_year}` : "";
						return title.includes(term) || status.includes(term) || fy.includes(term);
				  })
				: allPlans;
			grid.innerHTML = matched.map(planCardHtml).join("") + emptyStateCardHtml();
		});
	}

	/* ── API call ── */
	function loadPortfolioHub(shell) {
		if (typeof frappe === "undefined" || typeof frappe.call !== "function") return;
		frappe.call({
			method: "kentender_strategy.api.landing.get_strategy_landing_data",
			callback: function (r) {
				if (r && r.message) {
					applyPortfolioData(shell, r.message);
				}
			},
			error: function () {
				const plansEl = shell.querySelector("[data-sph-plans]");
				if (plansEl) {
					plansEl.innerHTML = `<div class="kt-sph-error-row">Could not load plans. Please refresh.</div>` + emptyStateCardHtml();
				}
			},
		});
	}

	function renderShell() {
		if (!isStrategyWorkspaceRoute()) {
			document.body.classList.remove("kt-strategy-shell");
			document.querySelectorAll(".kt-strategy-injected-shell").forEach((el) => el.remove());
			return;
		}
		document.body.classList.add("kt-strategy-shell");
		const mount = resolveMount();
		if (!mount) return;
		let shell = mount.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]');
		if (!shell) {
			shell = document.createElement("div");
			shell.className = "kt-strategy-injected-shell";
			shell.setAttribute("data-testid", "strategy-landing-page");
			const ed = document.getElementById("editorjs");
			if (ed && mount.contains(ed)) {
				mount.insertBefore(shell, ed);
				ed.style.display = "none";
			} else {
				mount.insertBefore(shell, mount.firstChild);
			}
		}
		if (shell.getAttribute("data-kt-rendered") === "1") return;
		shell.innerHTML = portfolioHubShellHtml();
		shell.setAttribute("data-kt-rendered", "1");
		loadPortfolioHub(shell);
	}

	function bindEvents() {
		if (bound) return;
		bound = true;
		document.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!(t && t.closest)) return;
			/* Create New Plan button */
			if (t.closest('[data-testid="sph-create-plan-btn"]') || t.closest('[data-testid="sph-create-new-card"]')) {
				if (typeof frappe !== "undefined" && typeof frappe.new_doc === "function") {
					frappe.new_doc("Strategic Plan");
				}
				return;
			}
		});
		if (window.jQuery) {
			window.jQuery(document).on("page-change app_ready", renderShell);
		}
		if (typeof frappe !== "undefined" && frappe.router && frappe.router.on) {
			frappe.router.on("change", renderShell);
		}
		if (typeof MutationObserver !== "undefined" && !observer) {
			observer = new MutationObserver(function () {
				if (!isStrategyWorkspaceRoute()) return;
				const existing = document.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]');
				if (!existing) renderShell();
			});
			observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
		}
	}

	function boot() {
		bindEvents();
		renderShell();
		setTimeout(renderShell, 200);
		setTimeout(renderShell, 800);
	}

	function waitForFrappe() {
		if (typeof window.frappe === "undefined") {
			setTimeout(waitForFrappe, 20);
			return;
		}
		boot();
		if (typeof frappe.ready === "function") frappe.ready(boot);
	}

	waitForFrappe();
	window.addEventListener("load", boot);
})();
