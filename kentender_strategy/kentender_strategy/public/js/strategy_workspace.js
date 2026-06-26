// Strategy Management workspace — static design-first workbench (no backend wiring).
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

	function staticPortfolioHubHtml() {
		return `
			<div class="kt-sph-shell" data-testid="strategy-portfolio-hub">
				<!-- Sticky Top Bar -->
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

				<!-- Main Content -->
				<main class="kt-sph-main">
					<!-- Page Header -->
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

					<!-- Metrics Bento Row -->
					<div class="kt-sph-metrics" data-testid="sph-metrics-grid">
						<div class="kt-sph-metric-card">
							<p class="kt-sph-metric-label">Total Budget</p>
							<h3 class="kt-sph-metric-value">$1.42B</h3>
							<p class="kt-sph-metric-sub kt-sph-metric-sub--positive">+4.2% vs Last Period</p>
						</div>
						<div class="kt-sph-metric-card">
							<p class="kt-sph-metric-label">Active Programs</p>
							<h3 class="kt-sph-metric-value">24</h3>
							<p class="kt-sph-metric-sub">Across 8 Strategic Plans</p>
						</div>
						<div class="kt-sph-metric-card">
							<p class="kt-sph-metric-label">Success Rate</p>
							<h3 class="kt-sph-metric-value">92%</h3>
							<div class="kt-sph-progress-track"><div class="kt-sph-progress-fill" style="width:92%"></div></div>
						</div>
						<div class="kt-sph-metric-card">
							<p class="kt-sph-metric-label">Draft Plans</p>
							<h3 class="kt-sph-metric-value">3</h3>
							<p class="kt-sph-metric-sub kt-sph-metric-sub--warn">Awaiting Review</p>
						</div>
					</div>

					<!-- Plans Card Grid -->
					<div class="kt-sph-plans-grid" data-testid="sph-plans-grid">

						<!-- Card 1: Active -->
						<div class="kt-sph-plan-card" data-testid="sph-plan-card">
							<div class="kt-sph-card-header">
								<div>
									<div class="kt-sph-card-header__row">
										<span class="kt-sph-chip kt-sph-chip--active">Active</span>
										<span class="kt-sph-fiscal-year">FY 2024 – 2028</span>
									</div>
									<h3 class="kt-sph-card-title">Ministry of Health 2026-2030</h3>
								</div>
								<button type="button" class="kt-sph-icon-btn"><span class="material-symbols-outlined">more_vert</span></button>
							</div>
							<div class="kt-sph-card-body">
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Budget</p>
									<p class="kt-sph-stat-value">$450M</p>
								</div>
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Programs</p>
									<p class="kt-sph-stat-value">12</p>
								</div>
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Objectives</p>
									<p class="kt-sph-stat-value">48</p>
								</div>
							</div>
							<div class="kt-sph-card-footer">
								<div class="kt-sph-avatar-stack">
									<span class="kt-sph-avatar kt-sph-avatar--slate-300"></span>
									<span class="kt-sph-avatar kt-sph-avatar--slate-400"></span>
									<span class="kt-sph-avatar kt-sph-avatar--slate-500"></span>
								</div>
								<a href="#" class="kt-sph-card-cta">View Workbench <span class="material-symbols-outlined">arrow_forward</span></a>
							</div>
						</div>

						<!-- Card 2: Draft -->
						<div class="kt-sph-plan-card" data-testid="sph-plan-card">
							<div class="kt-sph-card-header">
								<div>
									<div class="kt-sph-card-header__row">
										<span class="kt-sph-chip kt-sph-chip--draft">Draft</span>
										<span class="kt-sph-fiscal-year">FY 2025 – 2030</span>
									</div>
									<h3 class="kt-sph-card-title">Digital Health Roadmap</h3>
								</div>
								<button type="button" class="kt-sph-icon-btn"><span class="material-symbols-outlined">more_vert</span></button>
							</div>
							<div class="kt-sph-card-body">
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Budget</p>
									<p class="kt-sph-stat-value">$180M</p>
								</div>
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Programs</p>
									<p class="kt-sph-stat-value">4</p>
								</div>
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Objectives</p>
									<p class="kt-sph-stat-value">15</p>
								</div>
							</div>
							<div class="kt-sph-card-footer kt-sph-card-footer--draft">
								<div class="kt-sph-draft-hint">
									<span class="material-symbols-outlined kt-sph-draft-hint__icon">edit_note</span>
									<span class="kt-sph-draft-hint__text">Last edited 2 hours ago</span>
								</div>
								<a href="#" class="kt-sph-card-cta">Continue Setup <span class="material-symbols-outlined">edit</span></a>
							</div>
						</div>

						<!-- Card 3: Active -->
						<div class="kt-sph-plan-card" data-testid="sph-plan-card">
							<div class="kt-sph-card-header">
								<div>
									<div class="kt-sph-card-header__row">
										<span class="kt-sph-chip kt-sph-chip--active">Active</span>
										<span class="kt-sph-fiscal-year">FY 2024 – 2026</span>
									</div>
									<h3 class="kt-sph-card-title">Infrastructure Renewal Phase II</h3>
								</div>
								<button type="button" class="kt-sph-icon-btn"><span class="material-symbols-outlined">more_vert</span></button>
							</div>
							<div class="kt-sph-card-body">
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Budget</p>
									<p class="kt-sph-stat-value">$620M</p>
								</div>
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Programs</p>
									<p class="kt-sph-stat-value">8</p>
								</div>
								<div class="kt-sph-stat">
									<p class="kt-sph-stat-label">Objectives</p>
									<p class="kt-sph-stat-value">32</p>
								</div>
							</div>
							<div class="kt-sph-card-footer">
								<div class="kt-sph-avatar-stack">
									<span class="kt-sph-avatar kt-sph-avatar--blue-300"></span>
									<span class="kt-sph-avatar kt-sph-avatar--blue-400"></span>
								</div>
								<a href="#" class="kt-sph-card-cta">View Workbench <span class="material-symbols-outlined">arrow_forward</span></a>
							</div>
						</div>

						<!-- Empty State: Create New -->
						<div class="kt-sph-plan-card kt-sph-plan-card--empty" data-testid="sph-create-new-card">
							<div class="kt-sph-empty-icon-wrap">
								<span class="material-symbols-outlined">add</span>
							</div>
							<h4 class="kt-sph-empty-title">Create New Strategy</h4>
							<p class="kt-sph-empty-text">Define a new planning horizon and budget lineage</p>
						</div>
					</div>

					<!-- Lineage Activity -->
					<section class="kt-sph-activity-section">
						<h3 class="kt-sph-section-heading">Lineage Activity</h3>
						<div class="kt-sph-table-wrap">
							<table class="kt-sph-table" data-testid="sph-activity-table">
								<thead>
									<tr>
										<th>Time</th>
										<th>Action</th>
										<th>Plan</th>
										<th>User</th>
									</tr>
								</thead>
								<tbody>
									<tr>
										<td class="kt-sph-td-muted">10:45 AM</td>
										<td>
											<div class="kt-sph-action-cell">
												<span class="kt-sph-dot kt-sph-dot--primary"></span>
												<span class="kt-sph-action-label">New Objective Added</span>
											</div>
										</td>
										<td>Ministry of Health 2026-2030</td>
										<td>Sarah Chen</td>
									</tr>
									<tr>
										<td class="kt-sph-td-muted">09:12 AM</td>
										<td>
											<div class="kt-sph-action-cell">
												<span class="kt-sph-dot kt-sph-dot--amber"></span>
												<span class="kt-sph-action-label">Budget Re-allocated</span>
											</div>
										</td>
										<td>Digital Health Roadmap</td>
										<td>Marcus Thorne</td>
									</tr>
									<tr>
										<td class="kt-sph-td-muted">Yesterday</td>
										<td>
											<div class="kt-sph-action-cell">
												<span class="kt-sph-dot kt-sph-dot--green"></span>
												<span class="kt-sph-action-label">Plan Finalized</span>
											</div>
										</td>
										<td>Infrastructure Renewal II</td>
										<td>Lydia Vance</td>
									</tr>
								</tbody>
							</table>
						</div>
					</section>
				</main>
			</div>
		`;
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
		shell.innerHTML = staticPortfolioHubHtml();
		shell.setAttribute("data-kt-rendered", "1");
	}

	function bindEvents() {
		if (bound) return;
		bound = true;
		document.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!(t && t.closest)) return;
			if (t.closest('[data-testid="strategic-plan-create-button"]')) {
				if (typeof kentender_strategy !== "undefined" && kentender_strategy.strategy_plan_drawer) {
					kentender_strategy.strategy_plan_drawer.openEdit("one", function () {});
					return;
				}
				if (typeof frappe !== "undefined" && typeof frappe.new_doc === "function") {
					frappe.new_doc("Strategic Plan");
				}
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
