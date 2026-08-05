// Budget MVP-1 — shared workspace chrome / tabs / soft-show mount (BUD-UI-03).
frappe.provide("kentender_budget.workspace");

(function () {
	"use strict";

	var FIXTURE_BUDGET = "MOH-BUD-0001";

	var BUDGET_TABS = [
		{ label: "Overview", slug: "budget-overview" },
		{ label: "Budget Lines", slug: "budget-lines" },
		{ label: "Funding Activity", slug: "budget-funding-activity" },
		{ label: "Revisions", slug: "budget-revisions" },
		{ label: "Downstream Usage", slug: "budget-downstream" },
		{ label: "Review", slug: "budget-review" },
		{ label: "Audit", slug: "budget-audit" },
	];

	var STUB_COPY = {
		"budget-revisions": {
			title: "Revisions",
			message: "Budget Revisions is next in the Budget MVP-1 build sequence.",
		},
		"budget-downstream": {
			title: "Downstream Usage",
			message: "Downstream Usage is next in the Budget MVP-1 build sequence.",
		},
		"budget-review": {
			title: "Review",
			message: "Budget Review is next in the Budget MVP-1 build sequence.",
		},
		"budget-audit": {
			title: "Audit",
			message: "Budget Audit is next in the Budget MVP-1 build sequence.",
		},
	};

	function fixtures() {
		return kentender_budget.ui_fixtures || {};
	}

	function shell() {
		return kentender_core.cl_shell;
	}

	function budgetCodeFromRoute(fallback) {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		return fallback || FIXTURE_BUDGET;
	}

	function ensureBudgetRoute(pageSlug, code) {
		var id = code || FIXTURE_BUDGET;
		var route = frappe.get_route() || [];
		if (route[0] === pageSlug && route[1] === id) {
			return id;
		}
		frappe.set_route(pageSlug, id);
		return id;
	}

	function budgetMountKey(pageSlug, budgetCode) {
		return String(pageSlug || "") + "::" + String(budgetCode || "");
	}

	function renderTabButtons(activeSlug) {
		return BUDGET_TABS.map(function (t) {
			// Do NOT add text-primary on the active tab — kt_stitch_desk_chrome
			// zeros padding/border on button.text-primary and kills the underline.
			var active = t.slug === activeSlug ? " is-active" : "";
			return (
				'<button type="button" class="kt-bud-tab font-body-md' +
				active +
				'" data-kt-bud-tab="' +
				t.slug +
				'" data-testid="kt-bud-tab-' +
				t.slug +
				'">' +
				frappe.utils.escape_html(t.label) +
				"</button>"
			);
		}).join("");
	}

	function chromeActionsHtml() {
		return (
			'<button type="button" class="px-4 py-2 rounded-lg border border-outline-variant text-on-surface font-body-md hover:bg-surface-container-low transition-colors bg-surface-container-lowest" data-kt-bud-action="open-performance" data-testid="kt-bud-view-performance">' +
			frappe.utils.escape_html(__("View funding performance")) +
			"</button>" +
			'<button type="button" class="px-4 py-2 rounded-lg bg-primary text-on-primary font-body-md hover:opacity-90 transition-opacity" data-kt-bud-action="primary" data-testid="kt-bud-overview-primary">' +
			frappe.utils.escape_html(__("Request revision")) +
			"</button>"
		);
	}

	function budgetChromeHtml(budgetCode, activeSlug) {
		var code = budgetCode || FIXTURE_BUDGET;
		// Match Stitch header: white surface, code+status, title, actions, then tabs.
		// Tab row owns the bottom hairline (no second border on the outer header).
		return (
			'<header class="kt-bud-injected-chrome mb-0 bg-surface-container-lowest px-container-padding py-6" data-testid="kt-bud-workspace-chrome">' +
			'<div class="max-w-7xl mx-auto w-full">' +
			'<div class="flex flex-col md:flex-row md:items-start justify-between gap-4" data-kt-bud-chrome-title-row>' +
			"<div>" +
			'<div class="flex items-center gap-3 mb-2" data-kt-bud-chrome-code-row>' +
			'<span class="font-data-mono text-on-surface-variant bg-surface-container px-2 py-1 rounded text-xs" data-kt-bud-budget-code>' +
			frappe.utils.escape_html(code) +
			"</span>" +
			'<span class="font-label-caps px-2 py-0.5 rounded-full flex items-center gap-1 uppercase border" data-kt-bud-status-pill>' +
			'<span class="material-symbols-outlined text-[14px]" data-kt-bud-status-icon>radio_button_unchecked</span>' +
			'<span data-kt-bud-budget-status>—</span>' +
			"</span>" +
			"</div>" +
			'<h1 class="font-headline-lg text-on-surface" data-kt-bud-budget-title>—</h1>' +
			"</div>" +
			'<div class="flex flex-wrap gap-3" data-kt-bud-chrome-actions>' +
			chromeActionsHtml() +
			"</div>" +
			"</div>" +
			'<div class="flex gap-6 mt-8 overflow-x-auto hide-scrollbar" data-testid="kt-bud-workspace-tabs">' +
			renderTabButtons(activeSlug) +
			"</div>" +
			"</div>" +
			"</header>"
		);
	}

	function stubBodyHtml(pageSlug) {
		var copy = STUB_COPY[pageSlug] || {
			title: "Budget workspace",
			message: "This Budget workspace tab is next in the MVP-1 build sequence.",
		};
		return (
			'<div class="flex-1 p-container-padding max-w-7xl mx-auto w-full" data-testid="kt-bud-workspace-stub">' +
			'<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-card-padding">' +
			'<h2 class="font-headline-sm text-on-surface mb-2">' +
			frappe.utils.escape_html(__(copy.title)) +
			"</h2>" +
			'<p class="font-body-md text-on-surface-variant mb-4">' +
			frappe.utils.escape_html(__(copy.message)) +
			"</p>" +
			'<button type="button" class="text-primary font-body-md font-medium hover:underline" data-kt-bud-action="back-overview">' +
			frappe.utils.escape_html(__("Back to Overview")) +
			"</button>" +
			"</div></div>"
		);
	}

	function annotateChrome($root, pageSlug, budgetCode) {
		$root.find('[data-testid="kt-bud-workspace-chrome"]').remove();
		$root.prepend(budgetChromeHtml(budgetCode, pageSlug));
	}

	function bindTabs($root, budgetCode) {
		$root.off("click.ktBudTabs").on("click.ktBudTabs", "[data-kt-bud-tab]", function (e) {
			e.preventDefault();
			var slug = $(this).attr("data-kt-bud-tab");
			if (slug) {
				frappe.set_route(slug, budgetCodeFromRoute(budgetCode));
			}
		});
	}

	function bindChromeActions($root, budgetCode) {
		$root.off("click.ktBudChrome").on("click.ktBudChrome", "[data-kt-bud-action]", function (e) {
			e.preventDefault();
			var action = $(this).attr("data-kt-bud-action");
			var code = budgetCodeFromRoute(budgetCode);
			if (action === "open-performance") {
				frappe.set_route("budget-funding-performance");
				return;
			}
			if (action === "open-lines") {
				frappe.set_route("budget-lines", code);
				return;
			}
			if (action === "primary") {
				var primary = ($root.attr("data-kt-bud-primary-action") || "").trim();
				if (primary === "open_lines") {
					frappe.set_route("budget-lines", code);
					return;
				}
				if (primary === "add_line") {
					// Lines page intercepts this for drawer; fallback keeps route stable.
					if (
						kentender_budget.live &&
						typeof kentender_budget.live.bindLines === "function" &&
						$root.attr("data-kt-bud-page") === "budget-lines"
					) {
						$root.find("[data-kt-bud-lines-new]").trigger("click");
					}
					return;
				}
				if (primary === "request_revision") {
					frappe.set_route("budget-revisions", code);
					return;
				}
				frappe.set_route("budget-funding-performance");
				return;
			}
			if (action === "back-overview") {
				frappe.set_route("budget-overview", code);
				return;
			}
			if (action === "open-activity") {
				frappe.set_route("budget-funding-activity", code);
			}
		});
	}

	function existingRoot(page) {
		return $(page.main).find(".kt-bud-root").first();
	}

	function activateSurface() {
		document.body.classList.remove("kt-bud-register-active", "kt-bud-pf-active");
		document.body.classList.add("kt-bud-surface", "kt-bud-workspace-active");
	}

	function enterShell() {
		var sh = shell();
		if (sh && typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding"), route: ["budget-funding"] },
						{ label: __("Budget workspace") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
	}

	function mountBudgetPage(opts) {
		var page = opts.page;
		var pageSlug = opts.pageSlug;
		var softShow = !!opts.softShow;
		var isStub = !!opts.isStub;
		var fixtureKey = opts.fixtureKey || "overview";
		var sh = shell();
		if (!page || !sh || typeof sh.mountContent !== "function") {
			return;
		}

		activateSurface();
		enterShell();

		var budgetCode = ensureBudgetRoute(pageSlug, budgetCodeFromRoute(FIXTURE_BUDGET));
		var nextMountKey = budgetMountKey(pageSlug, budgetCode);
		var $existing = existingRoot(page);
		if (
			softShow &&
			$existing.length &&
			$existing.attr("data-kt-bud-mounted") === "1" &&
			$existing.attr("data-kt-bud-mount-key") === nextMountKey
		) {
			return;
		}

		var mainHtml;
		if (isStub) {
			mainHtml =
				'<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-workspace-page" data-kt-bud-page="' +
				frappe.utils.escape_html(pageSlug) +
				'">' +
				stubBodyHtml(pageSlug) +
				"</div>";
		} else {
			var fx = fixtures();
			var htmlFn = fx[fixtureKey];
			mainHtml =
				typeof htmlFn === "function"
					? htmlFn()
					: '<div class="p-4 text-danger">Missing fixture: ' +
						frappe.utils.escape_html(fixtureKey) +
						"</div>";
		}

		sh.mountContent(page.main, {
			pageHeader: { title: "", subtitle: "", hideBreadcrumbs: true },
			mainHtml: mainHtml,
		});
		$(page.main).find("#kt-cl-page-header-host").attr("hidden", "hidden");

		var $root = $(page.main).find(".kt-bud-root").first();
		if (!$root.length) {
			$root = $(page.main).find('[data-testid="kt-cl-page-body"]');
		}
		var prevGen = parseInt($root.attr("data-kt-bud-mount-gen") || "0", 10) || 0;
		$root.attr("data-kt-bud-mounted", "1");
		$root.attr("data-kt-bud-mount-key", nextMountKey);
		$root.attr("data-kt-bud-mount-gen", String(prevGen + 1));
		$root.attr("data-kt-bud-budget-code", budgetCode);

		annotateChrome($root, pageSlug, budgetCode);
		bindTabs($root, budgetCode);
		bindChromeActions($root, budgetCode);

		var live = kentender_budget.live || {};
		if (pageSlug === "budget-lines" && typeof live.bindLines === "function") {
			live.bindLines($root, budgetCode).catch(function (err) {
				console.warn("Budget lines live bind failed", err);
				frappe.show_alert({
					message: __("Could not load budget lines"),
					indicator: "orange",
				});
			});
		} else if (
			pageSlug === "budget-funding-activity" &&
			typeof live.bindFundingActivity === "function"
		) {
			live.bindFundingActivity($root, budgetCode).catch(function (err) {
				console.warn("Budget funding activity live bind failed", err);
				frappe.show_alert({
					message: __("Could not load funding activity"),
					indicator: "orange",
				});
			});
		} else if (pageSlug === "budget-overview" && typeof live.bindOverview === "function") {
			live.bindOverview($root, budgetCode).catch(function (err) {
				console.warn("Budget overview live bind failed", err);
				frappe.show_alert({
					message: __("Could not load budget overview"),
					indicator: "orange",
				});
			});
		}
	}

	function registerPage(pageSlug, opts) {
		opts = opts || {};
		frappe.pages[pageSlug] = frappe.pages[pageSlug] || {};
		frappe.pages[pageSlug].on_page_load = function (wrapper) {
			activateSurface();
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: opts.title || __("Budget workspace"),
				single_column: true,
			});
			wrapper.page = page;
			frappe.pages[pageSlug].page = page;
			mountBudgetPage(
				Object.assign({}, opts, {
					page: page,
					pageSlug: pageSlug,
					softShow: false,
				})
			);
		};
		frappe.pages[pageSlug].on_page_show = function (wrapper) {
			if (wrapper && wrapper.page) {
				activateSurface();
				mountBudgetPage(
					Object.assign({}, opts, {
						page: wrapper.page,
						pageSlug: pageSlug,
						softShow: true,
					})
				);
			}
		};
	}

	kentender_budget.workspace = {
		FIXTURE_BUDGET: FIXTURE_BUDGET,
		BUDGET_TABS: BUDGET_TABS,
		budgetCodeFromRoute: budgetCodeFromRoute,
		ensureBudgetRoute: ensureBudgetRoute,
		registerPage: registerPage,
		mountBudgetPage: mountBudgetPage,
	};
})();
