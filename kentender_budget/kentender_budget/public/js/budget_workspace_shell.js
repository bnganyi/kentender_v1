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

	var STUB_COPY = {};

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

	function chromeActionsHtml(activeSlug) {
		// Audit Stitch: header action is Export only (not Request revision / View performance).
		if (activeSlug === "budget-audit") {
			return (
				'<button type="button" class="kt-bud-audit-export border flex items-center gap-2 px-4 py-2 rounded-lg border-outline-variant text-primary font-body-md hover:bg-surface-container transition-colors bg-surface-container-lowest" data-testid="kt-bud-audit-export" data-kt-bud-audit-export>' +
				'<span class="material-symbols-outlined text-[20px]" aria-hidden="true">download</span>' +
				frappe.utils.escape_html(__("Export audit history")) +
				"</button>"
			);
		}
		return (
			'<button type="button" class="px-4 py-2 rounded-lg border border-outline-variant text-on-surface font-body-md hover:bg-surface-container-low transition-colors bg-surface-container-lowest" data-kt-bud-action="open-performance" data-testid="kt-bud-view-performance">' +
			frappe.utils.escape_html(__("View funding performance")) +
			"</button>" +
			// Hidden until paintChromeActions supplies an explicit action + label
			// (Overview/Lines/Revisions). Read-only tabs keep View performance only.
			'<button type="button" hidden class="hidden px-4 py-2 rounded-lg bg-primary text-on-primary font-body-md" data-kt-bud-action="primary" data-testid="kt-bud-overview-primary"></button>'
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
			'<h1 class="font-headline-lg text-headline-lg text-primary" data-kt-bud-budget-title>—</h1>' +
			"</div>" +
			'<div class="flex flex-wrap gap-3" data-kt-bud-chrome-actions>' +
			chromeActionsHtml(activeSlug) +
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

	/** Cross-tab chrome snapshot — prevents title "—" flash on first visit to a sibling tab. */
	var budgetChromeCache = {};

	function rememberBudgetChrome(budget) {
		if (!budget) {
			return;
		}
		var entry = {
			code: budget.code || "",
			title: budget.title || budget.name || "",
			status: budget.status || "",
			status_label: budget.status_label || budget.status || "",
		};
		if (!entry.code && !entry.title) {
			return;
		}
		if (entry.code) {
			budgetChromeCache[entry.code] = entry;
		}
		if (budget.id) {
			budgetChromeCache[budget.id] = entry;
		}
	}

	function harvestBudgetChrome(budgetCode, $exceptChrome) {
		if (budgetCode && budgetChromeCache[budgetCode]) {
			return budgetChromeCache[budgetCode];
		}
		var found = null;
		$('[data-testid="kt-bud-workspace-chrome"], .kt-bud-injected-chrome').each(function () {
			if ($exceptChrome && $exceptChrome.length && this === $exceptChrome[0]) {
				return;
			}
			var $c = $(this);
			var title = ($c.find("[data-kt-bud-budget-title]").first().text() || "").trim();
			if (!title || title === "—") {
				return;
			}
			var code = ($c.find("[data-kt-bud-budget-code]").first().text() || "").trim();
			var $root = $c.closest(".kt-bud-root");
			var rootCode = ($root.attr("data-kt-bud-budget-code") || "").trim();
			if (budgetCode && code !== budgetCode && rootCode !== budgetCode) {
				return;
			}
			found = {
				code: code || budgetCode || "",
				title: title,
				status: "",
				status_label: ($c.find("[data-kt-bud-budget-status]").first().text() || "").trim(),
			};
			/* Infer status key from pill classes when possible. */
			var $pill = $c.find("[data-kt-bud-status-pill]").first();
			if ($pill.hasClass("text-status-available")) {
				found.status = "Active";
			} else if ($pill.hasClass("text-status-reserved")) {
				found.status = "Submitted";
			}
			if (!found.status && found.status_label && found.status_label !== "—") {
				found.status = found.status_label;
			}
			if (found.code) {
				budgetChromeCache[found.code] = found;
			}
			return false;
		});
		return found;
	}

	function paintCachedStatusPill($chrome, status, statusLabel) {
		var st = status || "";
		var label = statusLabel || st || "—";
		var $pill = $chrome.find("[data-kt-bud-status-pill]");
		var $icon = $chrome.find("[data-kt-bud-status-icon]");
		$chrome.find("[data-kt-bud-budget-status]").text(label);
		$pill
			.removeClass(
				"bg-status-available/10 text-status-available border-status-available/20 bg-status-reserved/10 text-status-reserved border-status-reserved/20 bg-surface-variant text-on-surface-variant border-outline-variant/20"
			)
			.addClass("border");
		if (st === "Active") {
			$pill.addClass(
				"bg-status-available/10 text-status-available border-status-available/20"
			);
			$icon.text("check_circle");
		} else if (st === "Submitted") {
			$pill.addClass("bg-status-reserved/10 text-status-reserved border-status-reserved/20");
			$icon.text("pending");
		} else {
			$pill.addClass("bg-surface-variant text-on-surface-variant border-outline-variant/20");
			$icon.text("radio_button_unchecked");
		}
	}

	function hydrateBudgetChrome($root, budgetCode) {
		var $chrome = $root
			.find('[data-testid="kt-bud-workspace-chrome"], .kt-bud-injected-chrome')
			.first();
		if (!$chrome.length) {
			return false;
		}
		var snap = harvestBudgetChrome(budgetCode, $chrome);
		if (!snap || !snap.title) {
			return false;
		}
		$chrome.find("[data-kt-bud-budget-title]").first().text(snap.title);
		if (snap.code) {
			$chrome.find("[data-kt-bud-budget-code]").first().text(snap.code);
		}
		paintCachedStatusPill($chrome, snap.status || "", snap.status_label || "");
		$chrome.attr("data-kt-bud-chrome-hydrated", "1");
		return true;
	}

	function annotateChrome($root, pageSlug, budgetCode) {
		$root.find('[data-testid="kt-bud-workspace-chrome"]').remove();
		$root.prepend(budgetChromeHtml(budgetCode, pageSlug));
		/* Fill from sibling tab / cache before first paint of empty placeholders. */
		hydrateBudgetChrome($root, budgetCode);
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
					frappe.set_route("budget-revision-create", code);
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
		if (sh && typeof sh.enterNative === "function" && !sh.isNativeActive()) {
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

	function bindLiveTab($root, pageSlug, budgetCode) {
		var live = kentender_budget.live || {};
		var prevGen = parseInt($root.attr("data-kt-bud-mount-gen") || "0", 10) || 0;
		$root.attr("data-kt-bud-mount-gen", String(prevGen + 1));
		$root.attr("data-kt-bud-budget-code", budgetCode);

		if (pageSlug === "budget-lines" && typeof live.bindLines === "function") {
			return live.bindLines($root, budgetCode);
		}
		if (
			pageSlug === "budget-funding-activity" &&
			typeof live.bindFundingActivity === "function"
		) {
			return live.bindFundingActivity($root, budgetCode);
		}
		if (pageSlug === "budget-revisions" && typeof live.bindRevisions === "function") {
			return live.bindRevisions($root, budgetCode);
		}
		if (pageSlug === "budget-downstream" && typeof live.bindDownstream === "function") {
			return live.bindDownstream($root, budgetCode);
		}
		if (pageSlug === "budget-review" && typeof live.bindReview === "function") {
			return live.bindReview($root, budgetCode);
		}
		if (pageSlug === "budget-audit" && typeof live.bindAudit === "function") {
			return live.bindAudit($root, budgetCode);
		}
		if (pageSlug === "budget-overview" && typeof live.bindOverview === "function") {
			return live.bindOverview($root, budgetCode);
		}
		return Promise.resolve(null);
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
		/*
		 * Soft tab navigation: Frappe keeps page DOM and re-fires on_page_show.
		 * Remounting chrome / rebinding live every show flashes title to "—" then
		 * back. Skip wipe when the same route/budget is already mounted.
		 */
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
		$root.attr("data-kt-bud-mounted", "1");
		$root.attr("data-kt-bud-mount-key", nextMountKey);

		annotateChrome($root, pageSlug, budgetCode);
		bindTabs($root, budgetCode);
		bindChromeActions($root, budgetCode);

		bindLiveTab($root, pageSlug, budgetCode).catch(function (err) {
			console.warn("Budget live bind failed", pageSlug, err);
			frappe.show_alert({
				message: __("Could not load budget workspace data"),
				indicator: "orange",
			});
		});
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
		rememberBudgetChrome: rememberBudgetChrome,
		hydrateBudgetChrome: hydrateBudgetChrome,
	};
})();
