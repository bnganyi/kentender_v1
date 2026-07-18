// UI-01 — Tender Configuration Home (C1-M3).
// Route contract: /desk/it-tender-configuration-overview/<configuration_id>
// (refresh-safe). route_options / ?configuration_id= are accepted then rewritten.
(function () {
	"use strict";

	var SURFACE_ID = "UI-01";
	var PAGE_SLUG = "it-tender-configuration-overview";
	var API = "kentender_procurement.tender_configurations.get_tender_configuration_home";
	var STORAGE_KEY = "kt_cl_ui01_configuration_id";
	var state = { payload: null, configurationId: null, mounting: false };

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function c() {
		return kentender_core.cl_components || kentender_core.cl.components;
	}

	function configurationId() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		if (frappe.route_options && frappe.route_options.configuration_id) {
			return String(frappe.route_options.configuration_id).trim();
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("configuration_id")) {
				return String(params.get("configuration_id")).trim();
			}
		} catch (e) {
			/* ignore */
		}
		try {
			var stored = window.sessionStorage.getItem(STORAGE_KEY);
			if (stored) {
				return stored;
			}
		} catch (e2) {
			/* ignore */
		}
		return null;
	}

	function persistRoute(id) {
		if (!id) {
			return;
		}
		try {
			window.sessionStorage.setItem(STORAGE_KEY, id);
		} catch (e) {
			/* ignore */
		}
		var route = frappe.get_route() || [];
		if (route[0] === PAGE_SLUG && route[1] === id) {
			return;
		}
		// Canonical refresh-safe URL without wiping in-memory route_options mid-flight.
		frappe.set_route(PAGE_SLUG, id);
	}

	function goCfgRoute(deskSlug) {
		if (!deskSlug || !state.configurationId) {
			return;
		}
		frappe.route_options = { configuration_id: state.configurationId };
		frappe.set_route(deskSlug, state.configurationId);
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-ui01-root">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from the dashboard.") +
			"</p>" +
			'<button type="button" class="mt-4 h-8 px-4 rounded bg-primary text-on-primary text-label-sm" data-action="back" data-testid="kt-cl-ui01-back">' +
			__("Back to Tender Configurations") +
			"</button></div>"
		);
	}

	function homeHtml(data) {
		var comp = c();
		var h = (kentender_core.cl_code_spec && kentender_core.cl_code_spec.CONFIG_HOME) || {};
		var next = data.next_action || {};
		var steps = data.configuration_steps || [];
		var overall = data.overall_progress || {};
		var completeCount =
			overall.complete_count != null
				? parseInt(overall.complete_count, 10)
				: steps.filter(function (s) {
						return s.status_label === "Complete";
				  }).length;
		var totalSteps = overall.total != null ? parseInt(overall.total, 10) : steps.length || 9;
		var overallPct =
			overall.progress_pct != null
				? parseInt(overall.progress_pct, 10)
				: steps.length
					? Math.round(
							steps.reduce(function (sum, s) {
								var p = parseInt(s.progress_pct, 10);
								return sum + (isNaN(p) ? 0 : p);
							}, 0) / steps.length
					  )
					: 0;
		var ctx = data.context || data;
		var stdDoc =
			ctx.standard_tender_document_label ||
			data.standard_tender_document_label ||
			__("IT Standard Tender Document");
		var tone = steps.some(function (s) {
			return s.status_label === "Needs attention";
		})
			? "attention"
			: "default";
		return (
			'<div data-testid="kt-cl-ui01-root" data-configuration-id="' +
			frappe.utils.escape_html(data.configuration_id || "") +
			'">' +
			'<span class="hidden" data-testid="kt-cl-ui01-ref">' +
			frappe.utils.escape_html(data.configuration_ref || data.configuration_id || "") +
			"</span>" +
			comp.configurationContextStrip(ctx) +
			'<div class="kt-cl-ui01-layout ' +
			(h.layoutGrid || "") +
			'" data-testid="kt-cl-ui01-layout">' +
			'<div class="kt-cl-ui01-main ' +
			(h.mainCol || "") +
			'" data-testid="kt-cl-ui01-main">' +
			comp.nextBestActionPanel({
				label: next.label,
				reason: next.reason,
				buttonLabel: next.button_label,
				route: next.route,
				tone: tone,
			}) +
			comp.configurationStepsGrid({ steps: steps }) +
			"</div>" +
			'<aside class="kt-cl-ui01-side ' +
			(h.sideCol || "") +
			'" data-testid="kt-cl-ui01-side">' +
			comp.handoffPanel({ handoff: data.handoff || {} }) +
			comp.overallProgressPanel({
				complete: completeCount,
				total: totalSteps,
				progressPct: overallPct,
			}) +
			comp.resourcesPanel({
				items: [
					{ label: stdDoc, icon: "download" },
					{ label: __("Configuration Guide"), icon: "launch" },
				],
			}) +
			'<button type="button" class="kt-cl-ui01-back-btn" data-action="back" data-testid="kt-cl-ui01-back">' +
			'<span class="material-symbols-outlined kt-cl-ui01-back-icon" aria-hidden="true">arrow_back</span>' +
			"<span>" +
			__("Back to Tender Configurations") +
			"</span></button></aside></div></div>"
		);
	}

	function findStep(stepId) {
		var steps = (state.payload && state.payload.configuration_steps) || [];
		for (var i = 0; i < steps.length; i++) {
			if (steps[i].id === stepId) {
				return steps[i];
			}
		}
		return null;
	}

	function closeDrawer() {
		$(document.body)
			.find('[data-testid="kt-cl-ui01-drawer-overlay"]')
			.remove();
	}

	function openDrawer($root, stepId) {
		var step = findStep(stepId);
		if (!step) {
			return;
		}
		closeDrawer();
		/* Mount on body so position:fixed is not clipped by page scroll/transform hosts. */
		$(document.body).append(c().stepDetailsDrawer({ step: step }));
	}

	function bind($root) {
		$root.off(".ui01");
		$root.on("click.ui01", "[data-action='back']", function (e) {
			e.preventDefault();
			try {
				window.sessionStorage.removeItem(STORAGE_KEY);
			} catch (err) {
				/* ignore */
			}
			frappe.set_route("it-tender-configuration-dashboard");
		});
		$root.on("click.ui01", "[data-action='next-action'], [data-action='handoff']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			goCfgRoute($(this).attr("data-route"));
		});
		/* Card body + Review/Continue share open-step — navigate to the step form (not the drawer). */
		$root.on("click.ui01", "[data-action='open-step']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var $el = $(this);
			var status =
				$el.attr("data-step-status") ||
				$el.closest("[data-step-status]").attr("data-step-status") ||
				"";
			var stepId =
				$el.attr("data-step-id") || $el.closest("[data-step-id]").attr("data-step-id");
			var route = $el.attr("data-route") || $el.closest("[data-route]").attr("data-route");
			if (status === "Not available yet") {
				openDrawer($root, stepId);
				return;
			}
			goCfgRoute(route);
		});
		/* Explicit info control opens the lightweight step drawer. */
		$root.on("click.ui01", "[data-action='open-drawer']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var stepId =
				$(this).attr("data-step-id") ||
				$(this).closest("[data-step-id]").attr("data-step-id");
			openDrawer($root, stepId);
		});
		/* Drawer is mounted on body — bind on document so actions still work. */
		$(document)
			.off(".ui01drawer")
			.on("click.ui01drawer", "[data-action='close-drawer']", function (e) {
				e.preventDefault();
				e.stopPropagation();
				closeDrawer();
			})
			.on("click.ui01drawer", "[data-action='drawer-primary']", function (e) {
				e.preventDefault();
				e.stopPropagation();
				var route = $(this).attr("data-route");
				closeDrawer();
				goCfgRoute(route);
			})
			.on("click.ui01drawer", '[data-testid="kt-cl-ui01-drawer-overlay"]', function (e) {
				if (e.target === this) {
					closeDrawer();
				}
			})
			.on("keydown.ui01drawer", function (e) {
				if (e.key === "Escape") {
					closeDrawer();
				}
			});
	}

	function mount(page) {
		if (state.mounting) {
			return;
		}
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		var pageHeader = {
			title: __("Tender Configuration Home"),
			subtitle: __(
				"Complete the required configuration steps before review, preview, and publication handoff."
			),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}

		var id = configurationId();
		state.configurationId = id;
		if (!id) {
			sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
			bind($(page.main));
			return;
		}

		// Ensure refresh-safe segment URL (from route_options / query / session).
		var route = frappe.get_route() || [];
		if (!(route[0] === PAGE_SLUG && route[1] === id)) {
			state.mounting = true;
			frappe.set_route(PAGE_SLUG, id);
			// on_page_show will remount after route settles
			setTimeout(function () {
				state.mounting = false;
			}, 0);
			return;
		}

		try {
			window.sessionStorage.setItem(STORAGE_KEY, id);
		} catch (e) {
			/* ignore */
		}

		frappe.call({
			method: API,
			args: { configuration_id: id },
			callback: function (r) {
				state.payload = r.message || null;
				sh.mountContent(page.main, {
					pageHeader: pageHeader,
					mainHtml: state.payload ? homeHtml(state.payload) : emptyHtml(),
				});
				bind($(page.main));
			},
			error: function () {
				sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
				bind($(page.main));
			},
		});
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Tender Configuration Home"),
			single_column: true,
		});
		wrapper.page = page;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
})();
