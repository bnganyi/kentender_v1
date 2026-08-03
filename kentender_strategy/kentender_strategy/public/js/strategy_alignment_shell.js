// Strategy Alignment MVP-1 — shared mount / navigation + live API bind.
frappe.provide("kentender_strategy.alignment");

(function () {
	"use strict";

	var FIXTURE_PLAN = "MOH-SP-2026-2030";
	var FIXTURE_TARGET = "MOH-TGT-01";

	var PLAN_TABS = [
		{ label: "Overview", slug: "strategy-plan-overview" },
		{ label: "Structure", slug: "strategy-plan-structure" },
		{ label: "Value Commitments", slug: "strategy-plan-value-commitments" },
		{ label: "Measurement", slug: "strategy-plan-measurements" },
		{ label: "Downstream Usage", slug: "strategy-plan-downstream-usage" },
		{ label: "Review", slug: "strategy-plan-review" },
		{ label: "Audit", slug: "strategy-plan-audit" },
	];

	function fixtures() {
		return kentender_strategy.ui_fixtures || {};
	}

	function shell() {
		return kentender_core.cl_shell;
	}

	function planCodeFromRoute(fallback) {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		return fallback || FIXTURE_PLAN;
	}

	function targetCodeFromRoute(fallback) {
		var route = frappe.get_route() || [];
		// Prefer plan-scoped measurement routes: [page, planCode, targetCode]
		if (route.length > 2 && route[2]) {
			return String(route[2]).trim();
		}
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		return fallback || FIXTURE_TARGET;
	}

	function measurementRouteParts() {
		var route = frappe.get_route() || [];
		if (route.length >= 3 && route[1] && route[2]) {
			return {
				planCode: String(route[1]).trim(),
				targetCode: String(route[2]).trim(),
			};
		}
		if (route.length >= 2 && route[1]) {
			return { planCode: null, targetCode: String(route[1]).trim() };
		}
		return { planCode: null, targetCode: null };
	}

	function ensureMeasurementRoute(pageSlug, planCode, targetCode) {
		var route = frappe.get_route() || [];
		if (planCode && targetCode) {
			if (route[0] === pageSlug && route[1] === planCode && route[2] === targetCode) {
				return { planCode: planCode, targetCode: targetCode };
			}
			frappe.set_route(pageSlug, planCode, targetCode);
			return { planCode: planCode, targetCode: targetCode };
		}
		if (targetCode) {
			// Legacy deep link: /desk/strategy-measurement-submit/<targetCode>
			if (route[0] === pageSlug && route[1] === targetCode && !route[2]) {
				return { planCode: null, targetCode: targetCode };
			}
			if (!(route[0] === pageSlug && route[1])) {
				frappe.set_route(pageSlug, targetCode);
			}
			return measurementRouteParts();
		}
		return measurementRouteParts();
	}

	function ensurePlanRoute(pageSlug, code) {
		var id = code || FIXTURE_PLAN;
		var route = frappe.get_route() || [];
		if (route[0] === pageSlug && route[1] === id) {
			return id;
		}
		frappe.set_route(pageSlug, id);
		return id;
	}

	function annotatePortfolio($root) {
		var $grids = $root.find(".grid.grid-cols-4");
		if ($grids.length) {
			$grids.first().attr("data-testid", "kt-str-summary-strip");
		}
		var $bento = $root.find(".grid.grid-cols-12").first();
		if ($bento.length) {
			$bento.attr("data-testid", "kt-str-bento");
			var $kids = $bento.children("div");
			if ($kids.length >= 2) {
				$kids.eq(0).attr("data-kt-str-bento-main", "1");
				$kids.eq(1).attr("data-kt-str-bento-aside", "1");
			}
		}
		$root.find("table").first().attr("data-testid", "kt-str-plans-table");
	}

	function planChromeHtml(planCode, activeSlug) {
		var tabs = PLAN_TABS.map(function (t) {
			var active = t.slug === activeSlug ? " is-active text-primary font-bold border-b-2 border-primary" : "";
			return (
				'<button type="button" class="kt-str-tab pb-3 text-on-surface-variant font-body-md' +
				active +
				'" data-kt-str-tab="' +
				t.slug +
				'">' +
				frappe.utils.escape_html(t.label) +
				"</button>"
			);
		}).join("");
		return (
			/* No mb-section-gap: padded tab canvases (VC etc.) supply their own top spacing. */
			'<header class="kt-str-injected-plan-chrome" data-testid="kt-str-plan-chrome">' +
			'<div class="flex flex-col md:flex-row md:items-end justify-between gap-4">' +
			"<div>" +
			'<span class="font-data-mono text-data-mono text-primary bg-primary-fixed px-2 py-0.5 rounded text-xs">' +
			frappe.utils.escape_html(planCode) +
			"</span>" +
			'<h1 class="font-headline-lg text-headline-lg text-on-surface mt-2">Ministry of Health Strategic Plan 2026–2030</h1>' +
			"</div></div>" +
			'<div class="mt-8 flex gap-8 border-b border-outline-variant" data-testid="kt-str-plan-tabs">' +
			tabs +
			"</div></header>"
		);
	}

	function renderTabButtons(activeSlug) {
		return PLAN_TABS.map(function (t) {
			var active = t.slug === activeSlug ? " is-active text-primary font-bold border-b-2 border-primary" : "";
			return (
				'<button type="button" class="kt-str-tab pb-3 text-on-surface-variant font-body-md whitespace-nowrap' +
				active +
				'" data-kt-str-tab="' +
				t.slug +
				'">' +
				frappe.utils.escape_html(t.label) +
				"</button>"
			);
		}).join("");
	}

	function annotatePlanTabs($root, activeSlug, planCode) {
		var $tabRow = $root.find('[data-testid="kt-str-plan-tabs"]').first();
		if (!$tabRow.length) {
			var $overviewBtn = $root
				.find("button, a")
				.filter(function () {
					return $(this).text().replace(/\s+/g, " ").trim() === "Overview";
				})
				.first();
			if ($overviewBtn.length) {
				$tabRow = $overviewBtn.parent();
				$tabRow.attr("data-testid", "kt-str-plan-tabs");
			}
		}
		if (!$tabRow.length) {
			$root.prepend(planChromeHtml(planCode || FIXTURE_PLAN, activeSlug));
			$tabRow = $root.find('[data-testid="kt-str-plan-tabs"]').first();
			return;
		}
		/* Canonicalize to STR-UI plan tabs (some Stitch screens ship divergent labels). */
		$tabRow
			.addClass("flex gap-8 border-b border-outline-variant")
			.html(renderTabButtons(activeSlug));
	}

	function planRouteToken($root, fallback) {
		return (
			$root.attr("data-kt-str-route-token") ||
			$root.attr("data-kt-str-plan-id") ||
			fallback ||
			FIXTURE_PLAN
		);
	}

	function bindPlanTabs($root, planCode) {
		$root.off("click.ktStrTabs").on("click.ktStrTabs", "[data-kt-str-tab]", function (e) {
			e.preventDefault();
			var slug = $(this).attr("data-kt-str-tab");
			if (slug) {
				frappe.set_route(slug, planRouteToken($root, planCode));
			}
		});
	}

	function bindPortfolioNav($root) {
		$root.off("click.ktStrPortfolio");
		$root.on("click.ktStrPortfolio", "button, a", function (e) {
			var $el = $(this);
			var text = $el.text().replace(/\s+/g, " ").trim();
			if (text === "View" || text === "Review") {
				e.preventDefault();
				var code =
					$el.closest("tr").find(".font-data-mono").first().text().trim() || FIXTURE_PLAN;
				frappe.set_route("strategy-plan-overview", code);
				return;
			}
			if (text.indexOf("Create strategic plan") >= 0) {
				e.preventDefault();
				frappe.set_route("strategy-plan-overview", FIXTURE_PLAN);
				return;
			}
			if (text.indexOf("Review submitted plan") >= 0) {
				e.preventDefault();
				frappe.set_route("strategy-plan-review", "MOH-SP-2030-2034");
				return;
			}
			if (text.indexOf("Submit overdue measurement") >= 0) {
				e.preventDefault();
				frappe.set_route("strategy-measurement-submit", FIXTURE_PLAN, FIXTURE_TARGET);
				return;
			}
			if (text.indexOf("Resolve off-track target") >= 0) {
				e.preventDefault();
				frappe.set_route("strategy-corrective-actions");
				return;
			}
			if (text.indexOf("Learn about Strategic Pillars") >= 0) {
				e.preventDefault();
				frappe.set_route("strategy-pvo-catalogue");
			}
		});
	}

	function setSuccessorModalOpen($root, open) {
		var $modal = $root.find('[data-testid="kt-str-successor-modal"]').first();
		if (!$modal.length) {
			$modal = $root.find("#modal-backdrop").first();
		}
		if (!$modal.length) {
			return;
		}
		if (open) {
			$modal.removeAttr("hidden").removeClass("hidden").addClass("is-open");
		} else {
			$modal.attr("hidden", "hidden").addClass("hidden").removeClass("is-open");
		}
	}

	function bindOverviewNav($root, planCode) {
		$root.off("click.ktStrOverview").on("click.ktStrOverview", "button, a", function (e) {
			var $el = $(this);
			var action = $el.attr("data-kt-str-action") || "";
			var text = $el.text().replace(/\s+/g, " ").trim();
			var token = planRouteToken($root, planCode);
			// Live bind owns confirm-successor + measurement routes once data-kt-str-live=1.
			if ($root.attr("data-kt-str-live") === "1" && action === "confirm-successor") {
				return;
			}
			if (
				action === "view-structure" ||
				action === "start-plan-structure" ||
				text === "View structure" ||
				text === "Start plan structure"
			) {
				e.preventDefault();
				frappe.set_route("strategy-plan-structure", token);
			} else if (action === "view-commitments" || text === "View commitments") {
				e.preventDefault();
				frappe.set_route("strategy-plan-value-commitments", token);
			} else if (
				(action === "view-measurement" ||
					action === "submit-measurement" ||
					action === "review-measurement") &&
				$root.attr("data-kt-str-live") === "1"
			) {
				return;
			} else if (action === "view-measurement" || text.indexOf("View measurement") >= 0) {
				e.preventDefault();
				frappe.set_route("strategy-measurement-verify", token, FIXTURE_TARGET);
			} else if (action === "submit-measurement" || text.indexOf("Submit measurement") >= 0) {
				e.preventDefault();
				frappe.set_route("strategy-measurement-submit", token, FIXTURE_TARGET);
			} else if (action === "open-successor-modal" || text.indexOf("Create successor version") >= 0) {
				e.preventDefault();
				setSuccessorModalOpen($root, true);
			} else if (action === "close-successor-modal" || text === "Cancel") {
				if ($el.closest('[data-testid="kt-str-successor-modal"], #modal-backdrop').length) {
					e.preventDefault();
					setSuccessorModalOpen($root, false);
				}
			}
		});
	}

	function setVcDrawerOpen($root, open) {
		var $drawer = $root.find('[data-testid="kt-str-vc-drawer"]').first();
		var $canvas = $root.find('[data-testid="kt-str-vc-canvas"]').first();
		if (!$drawer.length) {
			$drawer = $root.find("#add-commitment-drawer").first();
		}
		if (!$drawer.length) {
			return;
		}
		if (open) {
			$drawer.removeClass("translate-x-full").addClass("is-open");
			$canvas.addClass("drawer-open");
		} else {
			$drawer.addClass("translate-x-full").removeClass("is-open");
			$canvas.removeClass("drawer-open");
		}
	}

	function bindValueCommitmentsNav($root) {
		// Ensure drawer starts closed (Stitch ships translate-x-full).
		setVcDrawerOpen($root, false);
		$root.off("click.ktStrVc").on("click.ktStrVc", "button, a", function (e) {
			// Live bind owns drawer open/save once data-kt-str-live=1.
			if ($root.attr("data-kt-str-live") === "1") {
				return;
			}
			var $el = $(this);
			var action = $el.attr("data-kt-str-action") || "";
			var text = $el.text().replace(/\s+/g, " ").trim();
			if (
				action === "toggle-vc-drawer" ||
				action === "add-vc" ||
				action === "close-vc-drawer" ||
				text === "Add commitment" ||
				(text === "Cancel" && $el.closest('[data-testid="kt-str-vc-drawer"], #add-commitment-drawer').length)
			) {
				e.preventDefault();
				var open = true;
				if (text === "Cancel" || action === "close-vc-drawer") {
					open = false;
				} else if (text === "Add commitment" || action === "add-vc") {
					open = true;
				} else {
					open = !$root.find('[data-testid="kt-str-vc-drawer"]').first().hasClass("is-open");
				}
				setVcDrawerOpen($root, open);
			}
		});
	}

	function bindMeasurementsNav($root) {
		$root.off("click.ktStrMeas").on("click.ktStrMeas", "button, a", function (e) {
			// Live bind owns register actions once data-kt-str-live=1.
			if ($root.attr("data-kt-str-live") === "1") {
				return;
			}
			var $el = $(this);
			var action = $el.attr("data-kt-str-action") || "";
			var text = $el.text().replace(/\s+/g, " ").trim();
			var targetCode =
				$el.attr("data-kt-str-target-code") ||
				$el.closest("tr").attr("data-kt-str-target-code") ||
				"";
			var plan =
				$root.attr("data-kt-str-route-token") ||
				$root.attr("data-kt-str-bound-code") ||
				planCodeFromRoute(FIXTURE_PLAN);
			if (action === "submit-measurement" || /^submit measurement$/i.test(text)) {
				e.preventDefault();
				if (!targetCode) {
					frappe.show_alert({
						message: __(
							"This plan has no Active performance targets to measure. Add targets on the Structure tab first."
						),
						indicator: "orange",
					});
					return;
				}
				frappe.set_route("strategy-measurement-submit", plan, targetCode);
			} else if (
				action === "verify-measurement" ||
				action === "view-measurement" ||
				action === "review-measurement" ||
				(/^verify(\s+measurement)?$/i.test(text) ||
					(/^review$/i.test(text) && $el.closest("table").length) ||
					(/^view$/i.test(text) && $el.closest("table").length))
			) {
				e.preventDefault();
				if (!targetCode) {
					return;
				}
				frappe.set_route("strategy-measurement-verify", plan, targetCode);
			}
		});
	}

	function bindSatelliteNav($root) {
		$root.off("click.ktStrSat").on("click.ktStrSat", "button, a", function (e) {
			// Live bind owns save/submit/verify once data-kt-str-live=1.
			if ($root.attr("data-kt-str-live") === "1") {
				var liveAction = $(this).attr("data-kt-str-action") || "";
				if (
					liveAction === "submit-measurement" ||
					liveAction === "verify-measurement" ||
					liveAction === "save-draft"
				) {
					return;
				}
			}
			var $el = $(this);
			var action = $el.attr("data-kt-str-action") || "";
			var text = $el.text().replace(/\s+/g, " ").trim();
			if (action === "cancel" || action === "return-overview" || /^return to overview$/i.test(text)) {
				e.preventDefault();
				frappe.set_route("strategy-plan-overview", FIXTURE_PLAN);
				return;
			}
			if (action === "create-pvo") {
				e.preventDefault();
				frappe.set_route("strategy-pvo-editor");
				return;
			}
			if (action === "submit-measurement") {
				e.preventDefault();
				frappe.show_alert({
					message: __("Measurement submitted (UI fixture) — no backend yet."),
					indicator: "blue",
				});
				return;
			}
			if (action === "verify-measurement") {
				e.preventDefault();
				frappe.show_alert({
					message: __("Measurement verified (UI fixture) — no backend yet."),
					indicator: "green",
				});
				return;
			}
			if (action === "save-draft") {
				e.preventDefault();
				frappe.show_alert({
					message: __("Draft saved (UI fixture) — no backend yet."),
					indicator: "blue",
				});
			}
		});
	}

	function bindCatalogueNav($root) {
		$root.off("click.ktStrPvo").on("click.ktStrPvo", "button, a", function (e) {
			var text = $(this).text().replace(/\s+/g, " ").trim();
			if (/create|new|add/i.test(text) && /objective|pvo/i.test(text + " objective")) {
				e.preventDefault();
				frappe.set_route("strategy-pvo-editor");
				return;
			}
			if (text === "Create" || /Create public value/i.test(text) || /New objective/i.test(text)) {
				e.preventDefault();
				frappe.set_route("strategy-pvo-editor");
			}
		});
	}

	function closeStructureDrawer($host) {
		$host.find('[data-testid="kt-str-structure-drawer"]').remove();
		$host.find('[data-testid="kt-str-structure-drawer-overlay"]').remove();
	}

	function openStructureDrawer($host) {
		closeStructureDrawer($host);
		var fx = fixtures();
		if (!fx.structure_drawer) {
			return;
		}
		var html = fx.structure_drawer();
		var $tmp = $("<div/>").html(html);
		// Keep kt-str-root wrapper so Strategy tokens / focus chrome apply inside the drawer.
		var $drawer = $tmp.find('[data-testid="kt-str-structure-drawer"]').first();
		var $overlay = $drawer.length
			? $drawer.find('[data-testid="kt-str-structure-drawer-overlay"]').first()
			: $tmp.find('[data-testid="kt-str-structure-drawer-overlay"]').first();
		if (!$overlay.length) {
			$overlay = $tmp.find(".fixed.inset-0").first();
		}
		if (!$overlay.length) {
			return;
		}
		$overlay.attr("data-testid", "kt-str-structure-drawer-overlay");
		$overlay.attr("data-dismiss", "explicit-only");
		var $panel = $overlay.find('[data-testid="kt-str-structure-drawer-panel"]').first();
		if (!$panel.length) {
			$overlay
				.find(".relative")
				.first()
				.attr("data-testid", "kt-str-structure-drawer-panel");
		}
		if ($drawer.length) {
			$host.append($drawer);
		} else {
			$host.append(
				$('<div class="kt-str-root" data-testid="kt-str-structure-drawer"/>').append($overlay)
			);
		}

		$overlay.on("click", function (e) {
			if (e.target === this || $(e.target).hasClass("bg-on-surface/40")) {
				/* explicit-only: backdrop does not dismiss */
				e.preventDefault();
			}
		});
		$overlay.on("click", "[data-kt-str-action='close-drawer'], button", function (e) {
			var $btn = $(this);
			var action = $btn.attr("data-kt-str-action") || "";
			var t = $btn.text().replace(/\s+/g, " ").trim();
			if (action === "close-drawer" || /^cancel$/i.test(t) || $btn.attr("aria-label") === "Close") {
				e.preventDefault();
				closeStructureDrawer($host);
			}
		});
	}

	function bindStructureNav($root, $host) {
		$root.off("click.ktStrStruct").on("click.ktStrStruct", "button, a", function (e) {
			// Live bind owns add/edit/delete drawer once data-kt-str-live=1.
			if ($root.attr("data-kt-str-live") === "1") {
				return;
			}
			var $el = $(this);
			var action = $el.attr("data-kt-str-action") || "";
			var text = $el.text().replace(/\s+/g, " ").trim();
			if (
				action === "add-structure-item" ||
				/Add Structure Item/i.test(text) ||
				/Add Indicator/i.test(text) ||
				/Add Target/i.test(text) ||
				/Performance Target/i.test(text)
			) {
				e.preventDefault();
				openStructureDrawer($host);
			}
		});
	}

	function bindReviewToggle($root, planCode) {
		$root.off("click.ktStrReview").on("click.ktStrReview", "button, a", function (e) {
			var text = $(this).text().replace(/\s+/g, " ").trim();
			if (/show ready|ready for submission|fixture.?ready/i.test(text)) {
				e.preventDefault();
				frappe.route_options = frappe.route_options || {};
				frappe.route_options.kt_str_review_state = "ready";
				frappe.set_route("strategy-plan-review", planCode);
			} else if (/show blockers|readiness|fixture.?blockers/i.test(text)) {
				e.preventDefault();
				frappe.route_options = frappe.route_options || {};
				frappe.route_options.kt_str_review_state = "blockers";
				frappe.set_route("strategy-plan-review", planCode);
			}
		});
	}

	function mountStrategyPage(opts) {
		opts = opts || {};
		var page = opts.page;
		var pageSlug = opts.pageSlug;
		var fixtureKey = opts.fixtureKey;
		var title = opts.title || __("Strategy Alignment");
		var planCode = opts.planCode || null;
		var isPlanPage = !!opts.isPlanPage;
		var isTargetPage = !!opts.isTargetPage;
		var afterBind = opts.afterBind;

		document.body.classList.add("kt-str-surface");

		var sh = shell();
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}

		if (typeof sh.enterNative === "function" && !sh.isNativeActive()) {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Strategy Alignment"), route: ["strategy-alignment"] },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}

		if (isPlanPage) {
			planCode = ensurePlanRoute(pageSlug, planCode || planCodeFromRoute(FIXTURE_PLAN));
			var route = frappe.get_route() || [];
			if (!(route[0] === pageSlug && route[1] === planCode)) {
				return;
			}
		}

		var measurementParts = null;
		if (isTargetPage || opts.isMeasurementPage) {
			measurementParts = measurementRouteParts();
			if (opts.planCode) {
				measurementParts.planCode = opts.planCode;
			}
			if (opts.targetCode) {
				measurementParts.targetCode = opts.targetCode;
			}
			if (!measurementParts.targetCode) {
				measurementParts.targetCode = FIXTURE_TARGET;
			}
			measurementParts = ensureMeasurementRoute(
				pageSlug,
				measurementParts.planCode,
				measurementParts.targetCode
			);
			var troute = frappe.get_route() || [];
			if (measurementParts.planCode && measurementParts.targetCode) {
				if (
					!(
						troute[0] === pageSlug &&
						troute[1] === measurementParts.planCode &&
						troute[2] === measurementParts.targetCode
					)
				) {
					return;
				}
			} else if (measurementParts.targetCode) {
				if (!(troute[0] === pageSlug && troute[1] === measurementParts.targetCode && !troute[2])) {
					return;
				}
			}
		}

		var fx = fixtures();
		var htmlFn = fx[fixtureKey];
		var mainHtml =
			typeof htmlFn === "function"
				? htmlFn()
				: '<div class="p-4 text-danger">Missing fixture: ' +
					frappe.utils.escape_html(fixtureKey) +
					"</div>";

		if (fixtureKey === "review_blockers" || fixtureKey === "review_ready") {
			var state =
				(frappe.route_options && frappe.route_options.kt_str_review_state) || "blockers";
			if (state === "ready" && fx.review_ready) {
				mainHtml = fx.review_ready();
				fixtureKey = "review_ready";
			} else if (fx.review_blockers) {
				mainHtml = fx.review_blockers();
				fixtureKey = "review_blockers";
			}
			mainHtml =
				'<div class="mb-4 flex gap-2 relative z-40" data-testid="kt-str-review-state-toggle">' +
				'<button type="button" class="px-3 py-1.5 border border-outline-variant rounded text-sm bg-surface-container-lowest" data-kt-str-review="blockers">Show blockers</button>' +
				'<button type="button" class="px-3 py-1.5 border border-outline-variant rounded text-sm bg-surface-container-lowest" data-kt-str-review="ready">Show ready for submission</button>' +
				"</div>" +
				mainHtml;
		}

		sh.mountContent(page.main, {
			pageHeader: { title: title, subtitle: "", hideBreadcrumbs: true },
			mainHtml: mainHtml,
		});

		var $body = $(page.main).find('[data-testid="kt-cl-page-body"]');
		var $root = $body.find(".kt-str-root").first();
		if (!$root.length) {
			$root = $body;
		}

		if (fixtureKey === "portfolio") {
			annotatePortfolio($root);
			bindPortfolioNav($root);
		}

		if (isPlanPage) {
			annotatePlanTabs($root, pageSlug, planCode);
			bindPlanTabs($root, planCode);
			if (pageSlug === "strategy-plan-overview") {
				bindOverviewNav($root, planCode);
			}
			if (pageSlug === "strategy-plan-structure") {
				bindStructureNav($root, $body);
			}
			if (pageSlug === "strategy-plan-value-commitments") {
				bindValueCommitmentsNav($root);
			}
			if (pageSlug === "strategy-plan-measurements") {
				bindMeasurementsNav($root);
			}
			if (
				pageSlug === "strategy-plan-downstream-usage" ||
				pageSlug === "strategy-plan-audit" ||
				pageSlug === "strategy-plan-review"
			) {
				bindSatelliteNav($root);
			}
			if (pageSlug === "strategy-plan-review") {
				$body.off("click.ktStrReviewToggle").on(
					"click.ktStrReviewToggle",
					"[data-kt-str-review]",
					function (e) {
						e.preventDefault();
						frappe.route_options = frappe.route_options || {};
						frappe.route_options.kt_str_review_state = $(this).attr("data-kt-str-review");
						frappe.set_route("strategy-plan-review", planCode);
					}
				);
				bindReviewToggle($root, planCode);
			}
		}

		if (fixtureKey === "pvo_catalogue") {
			bindCatalogueNav($root);
			bindSatelliteNav($root);
		}
		if (
			fixtureKey === "pvo_editor" ||
			fixtureKey === "measurement_submit" ||
			fixtureKey === "measurement_verify" ||
			fixtureKey === "corrective_actions"
		) {
			bindSatelliteNav($root);
		}

		$body.off("click.ktStrBack").on("click.ktStrBack", "[data-kt-str-back]", function (e) {
			e.preventDefault();
			frappe.set_route("strategy-alignment");
		});

		if (typeof afterBind === "function") {
			afterBind($root, $body, planCode);
		}

		var targetCode = null;
		var measurementPlanCode = planCode;
		if (measurementParts) {
			targetCode = measurementParts.targetCode;
			measurementPlanCode = measurementParts.planCode || planCode;
			$root.attr("data-kt-str-plan-code", measurementPlanCode || "");
			$root.attr("data-kt-str-target-code-route", targetCode || "");
		} else if (isTargetPage) {
			targetCode = targetCodeFromRoute(FIXTURE_TARGET);
		}
		if (kentender_strategy.live && typeof kentender_strategy.live.afterMount === "function") {
			kentender_strategy.live
				.afterMount(pageSlug, $root, measurementPlanCode || planCode, targetCode)
				.then(function () {
					if (isPlanPage) {
						var token = planRouteToken($root, planCode);
						bindPlanTabs($root, token);
						if (pageSlug === "strategy-plan-overview") {
							bindOverviewNav($root, token);
						}
					}
				})
				.catch(function (err) {
					console.warn("Strategy live bind failed", err);
					frappe.show_alert({
						message: __("Could not load live Strategy data"),
						indicator: "orange",
					});
				});
		}
	}

	function registerPage(pageSlug, opts) {
		frappe.pages[pageSlug] = frappe.pages[pageSlug] || {};
		frappe.pages[pageSlug].on_page_load = function (wrapper) {
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: opts.title || __("Strategy Alignment"),
				single_column: true,
			});
			wrapper.page = page;
			frappe.pages[pageSlug].page = page;
			mountStrategyPage(
				Object.assign({}, opts, {
					page: page,
					pageSlug: pageSlug,
				})
			);
		};
		frappe.pages[pageSlug].on_page_show = function (wrapper) {
			if (wrapper && wrapper.page) {
				mountStrategyPage(
					Object.assign({}, opts, {
						page: wrapper.page,
						pageSlug: pageSlug,
					})
				);
			}
		};
	}

	kentender_strategy.alignment = {
		FIXTURE_PLAN: FIXTURE_PLAN,
		FIXTURE_TARGET: FIXTURE_TARGET,
		PLAN_TABS: PLAN_TABS,
		planCodeFromRoute: planCodeFromRoute,
		targetCodeFromRoute: targetCodeFromRoute,
		measurementRouteParts: measurementRouteParts,
		mountStrategyPage: mountStrategyPage,
		registerPage: registerPage,
		openStructureDrawer: openStructureDrawer,
		annotatePortfolio: annotatePortfolio,
	};
})();
