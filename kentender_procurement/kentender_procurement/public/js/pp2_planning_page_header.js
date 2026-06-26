/**
 * P5B-001 — Shared Planning page header (title, purpose, optional primary action).
 */
(function () {
	frappe.provide("kentender_procurement");

	const ROOT_PATH = "/desk/procurement-planning";

	const SURFACE_HEADER_CONFIG = {
		"": {
			title: __("Workbench"),
			purpose: __("Plan approved demands into tender-ready procurement packages."),
		},
		"approved-demands": {
			title: __("Approved Demands"),
			purpose: __("Which approved demands can be planned now?"),
		},
		plans: {
			title: __("Procurement Plans"),
			purpose: __("Create, activate, and review procurement plans."),
			primaryAction: {
				label: __("Create Plan"),
				testId: "pp3-create-plan-button",
				action: "create_plan",
			},
		},
		packages: {
			title: __("Packages"),
			purpose: __("Which packages need work, review, release, or follow-up?"),
		},
		"package-detail": {
			title: __("Package Detail"),
			purpose: __("Review package status, funding, readiness, and release actions."),
		},
		releases: {
			title: __("Released to Tender"),
			purpose: __("Which packages have left Planning, and where did they go?"),
		},
	};

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function configForSlug(slug) {
		const key = slug == null ? "" : String(slug);
		return SURFACE_HEADER_CONFIG[key] || SURFACE_HEADER_CONFIG[""];
	}

	function workbenchToolbarHtml() {
		return (
			'<div class="pp3-workbench-toolbar" data-testid="pp3-workbench-toolbar">' +
			'<div class="pp3-workbench-toolbar__left">' +
			'<h2 class="pp3-workbench-toolbar__title">' +
			esc(__("Procurement Workbench")) +
			"</h2>" +
			'<label class="pp3-workbench-toolbar__search" aria-label="' +
			esc(__("Search workbench")) +
			'">' +
			'<span class="material-symbols-outlined pp3-workbench-toolbar__search-icon" aria-hidden="true">search</span>' +
			'<input type="search" class="pp3-workbench-toolbar__search-input" data-testid="pp3-workbench-search" placeholder="' +
			esc(__("Search demands, IDs, or vendors...")) +
			'" />' +
			"</label>" +
			"</div>" +
			'<div class="pp3-workbench-toolbar__right">' +
			'<button type="button" class="pp3-workbench-toolbar__icon-button" aria-label="' +
			esc(__("Notifications")) +
			'"><span class="material-symbols-outlined" aria-hidden="true">notifications</span><span class="pp3-workbench-toolbar__dot" aria-hidden="true"></span></button>' +
			'<button type="button" class="pp3-workbench-toolbar__icon-button" aria-label="' +
			esc(__("History")) +
			'"><span class="material-symbols-outlined" aria-hidden="true">history</span></button>' +
			'<span class="pp3-workbench-toolbar__session"><span class="material-symbols-outlined" aria-hidden="true">account_circle</span>' +
			esc(__("Session: Active")) +
			"</span>" +
			"</div>" +
			"</div>"
		);
	}

	function html(opts) {
		const o = opts || {};
		const title = String(o.title || "").trim();
		const purpose = String(o.purpose || "").trim();
		const primaryAction = o.primaryAction || null;
		const slug = String(o.slug || "").trim();
		const isWorkbench = slug === "";
		let actionsHtml = "";
		if (primaryAction && primaryAction.label) {
			const disabled = primaryAction.disabled ? " disabled" : "";
			const href = String(primaryAction.href || "").trim();
			const action = String(primaryAction.action || "").trim();
			actionsHtml =
				'<div class="pp2-page-header__actions" data-testid="pp2-page-actions">' +
				'<button type="button" class="btn btn-primary btn-sm pp2-page-header__primary-action"' +
				' data-testid="' +
				esc(primaryAction.testId || "pp2-page-primary-action") +
				'"' +
				(href ? ' data-pp2-primary-href="' + esc(href) + '"' : "") +
				(action ? ' data-pp3-action="' + esc(action) + '"' : "") +
				disabled +
				">" +
				esc(primaryAction.label) +
				"</button></div>";
		}
		if (isWorkbench) {
			return (
				'<header class="pp2-page-header pp2-page-header--workbench" data-testid="pp2-page-header">' +
				workbenchToolbarHtml() +
				'<div class="pp2-page-header__meta sr-only" aria-hidden="true">' +
				'<h2 class="h5 pp2-page-header__title mb-1" data-testid="pp2-page-title">' +
				esc(title || __("Workbench")) +
				"</h2>" +
				'<p class="text-muted small pp2-page-header__purpose mb-0" data-testid="pp2-page-purpose">' +
				esc(purpose || __("Plan approved demands into tender-ready procurement packages.")) +
				"</p>" +
				"</div>" +
				"</header>"
			);
		}
		return (
			'<header class="pp2-page-header" data-testid="pp2-page-header">' +
			'<div class="pp2-page-header__row">' +
			'<div class="pp2-page-header__copy">' +
			'<h2 class="h5 pp2-page-header__title mb-1" data-testid="pp2-page-title">' +
			esc(title) +
			"</h2>" +
			'<p class="text-muted small pp2-page-header__purpose mb-0" data-testid="pp2-page-purpose">' +
			esc(purpose) +
			"</p>" +
			"</div>" +
			actionsHtml +
			"</div></header>"
		);
	}

	function bindPrimaryAction(host) {
		if (!host) return;
		const button = host.querySelector(
			'[data-testid="pp2-page-primary-action"], [data-testid="pp3-create-plan-button"]',
		);
		if (!button || button.getAttribute("data-bound") === "1") return;
		button.setAttribute("data-bound", "1");
		button.addEventListener("click", function () {
			const action = String(button.getAttribute("data-pp3-action") || "").trim();
			if (action === "create_plan") {
				if (
					kentender_procurement.PlanningCreatePlanModal &&
					typeof kentender_procurement.PlanningCreatePlanModal.show === "function"
				) {
					kentender_procurement.PlanningCreatePlanModal.show({
						onCreated: function () {
							if (typeof window.__kt_pp_refresh_procurement_plans === "function") {
								window.__kt_pp_refresh_procurement_plans();
							}
						},
					});
				}
				return;
			}
			const href = String(button.getAttribute("data-pp2-primary-href") || "").trim();
			if (!href) return;
			try {
				if (frappe.router && typeof frappe.router.push_state === "function") {
					frappe.router.push_state(href);
					return;
				}
			} catch (e) {
				/* ignore */
			}
			window.location.href = href;
		});
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		const markup = html(opts || {});
		target.innerHTML = markup;
		bindPrimaryAction(target);
	}

	function renderForSlug(host, slug) {
		const cfg = configForSlug(slug);
		render(host, {
			slug: slug,
			title: cfg.title,
			purpose: cfg.purpose,
			primaryAction: cfg.primaryAction || null,
		});
	}

	kentender_procurement.PlanningPageHeader = {
		html: html,
		render: render,
		renderForSlug: renderForSlug,
		configForSlug: configForSlug,
	};
})();
