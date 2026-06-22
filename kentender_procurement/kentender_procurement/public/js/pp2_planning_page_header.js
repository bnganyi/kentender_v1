/**
 * P5B-001 — Shared Planning page header (title, purpose, optional primary action).
 */
(function () {
	frappe.provide("kentender_procurement");

	const ROOT_PATH = "/desk/procurement-planning";

	const SURFACE_HEADER_CONFIG = {
		"": {
			title: __("Planning Home"),
			purpose: __("Convert approved demand into tender-ready procurement packages."),
			primaryAction: {
				label: __("New package from approved demand"),
				testId: "pp2-page-primary-action",
				href: ROOT_PATH + "?queue=needs-planning",
			},
		},
		"approved-demands": {
			title: __("Approved Demands"),
			purpose: __("Which approved demands can be planned now?"),
		},
		plans: {
			title: __("Plans"),
			purpose: __("Which plan owns this procurement work?"),
		},
		packages: {
			title: __("Packages"),
			purpose: __("Which packages need work, review, release, or follow-up?"),
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

	function html(opts) {
		const o = opts || {};
		const title = String(o.title || "").trim();
		const purpose = String(o.purpose || "").trim();
		const primaryAction = o.primaryAction || null;
		let actionsHtml = "";
		if (primaryAction && primaryAction.label) {
			const disabled = primaryAction.disabled ? " disabled" : "";
			const href = String(primaryAction.href || "").trim();
			actionsHtml =
				'<div class="pp2-page-header__actions" data-testid="pp2-page-actions">' +
				'<button type="button" class="btn btn-primary btn-sm pp2-page-header__primary-action"' +
				' data-testid="' +
				esc(primaryAction.testId || "pp2-page-primary-action") +
				'"' +
				(href ? ' data-pp2-primary-href="' + esc(href) + '"' : "") +
				disabled +
				">" +
				esc(primaryAction.label) +
				"</button></div>";
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
		const button = host.querySelector('[data-testid="pp2-page-primary-action"]');
		if (!button || button.getAttribute("data-bound") === "1") return;
		button.setAttribute("data-bound", "1");
		button.addEventListener("click", function () {
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
		render(host, configForSlug(slug));
	}

	kentender_procurement.PlanningPageHeader = {
		html: html,
		render: render,
		renderForSlug: renderForSlug,
		configForSlug: configForSlug,
	};
})();
