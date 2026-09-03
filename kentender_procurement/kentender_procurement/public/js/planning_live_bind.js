// Gate 03 — live bind for PLN-UI-01…03.
(function () {
	"use strict";

	frappe.provide("kentender_procurement.live");

	var API = "kentender_procurement.procurement_planning.api";

	function navigate(route) {
		if (kentender_procurement.planning_client) {
			kentender_procurement.planning_client.navigate(route);
			return;
		}
		var parsed = new URL(route, window.location.origin);
		frappe.route_options = Object.fromEntries(parsed.searchParams.entries());
		frappe.set_route(parsed.pathname.replace(/^\/(app|desk)\//, "").replace(/^\//, ""));
	}

	function call(method, args) {
		return frappe
			.call({
				method: API + "." + method,
				args: args || {},
				freeze: false,
			})
			.then(function (r) {
				return r && r.message;
			});
	}

	function esc(s) {
		return frappe.utils.escape_html(String(s == null ? "" : s));
	}

	/** Stitch semantic tones: available=green, reserved=amber, exhausted=red, primary=blue, neutral=grey. */
	function validationTone(value) {
		var s = String(value || "")
			.trim()
			.toLowerCase();
		if (s === "ready") {
			return "available";
		}
		if (s === "blocked") {
			return "exhausted";
		}
		// Needs attention, Stale, Not run — warning family (PLN-UI-01 / UI-05).
		return "reserved";
	}

	function lifecycleTone(value) {
		var s = String(value || "")
			.trim()
			.toLowerCase();
		if (s === "open") {
			return "primary";
		}
		if (s === "in review") {
			return "reserved";
		}
		if (s === "approved" || s === "active") {
			return "available";
		}
		// Draft, Returned, Closed, Superseded, empty — neutral chip (Stitch Draft).
		return "neutral";
	}

	/** Readiness / status chip tones (workspace + builder). */
	function contributionTone(label) {
		var s = String(label || "")
			.trim()
			.toLowerCase();
		if (s === "submitted" || s === "ready") {
			return "available";
		}
		var m = s.match(/^(\d+)\s+of\s+(\d+)\s+(submitted|ready)$/);
		if (m) {
			var done = parseInt(m[1], 10);
			var total = parseInt(m[2], 10);
			if (total > 0 && done >= total) {
				return "available";
			}
			return "reserved";
		}
		if (/awaiting|preparing/.test(s)) {
			return "reserved";
		}
		return "neutral";
	}

	function statusPillClasses(tone) {
		if (tone === "available") {
			return "bg-status-available/10 text-status-available border-status-available/20";
		}
		if (tone === "reserved") {
			return "bg-status-reserved/10 text-status-reserved border-status-reserved/20";
		}
		if (tone === "exhausted") {
			return "bg-status-exhausted/10 text-status-exhausted border-status-exhausted/20";
		}
		if (tone === "primary") {
			return "bg-primary/10 text-primary border-primary/20";
		}
		return "bg-surface-variant text-on-surface border-outline-variant";
	}

	function statusTextClass(tone) {
		if (tone === "available") {
			return "text-status-available";
		}
		if (tone === "reserved") {
			return "text-status-reserved";
		}
		if (tone === "exhausted") {
			return "text-status-exhausted";
		}
		if (tone === "primary") {
			return "text-primary";
		}
		return "text-on-surface";
	}

	function validationIcon(value, tone) {
		var s = String(value || "")
			.trim()
			.toLowerCase();
		if (tone === "available") {
			return "check_circle";
		}
		if (tone === "exhausted") {
			return "error";
		}
		if (s === "not run" || s === "stale") {
			return "pending";
		}
		return "error";
	}

	function validationPillHtml(value) {
		var label = String(value || "Not run");
		var tone = validationTone(label);
		var icon = validationIcon(label, tone);
		return (
			'<div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-label-caps text-label-caps border whitespace-nowrap ' +
			statusPillClasses(tone) +
			'">' +
			'<span class="material-symbols-outlined text-[12px]" aria-hidden="true">' +
			icon +
			"</span>" +
			esc(label) +
			"</div>"
		);
	}

	function contributionPillHtml(label) {
		var text = String(label || "Preparing");
		var tone = contributionTone(text);
		return (
			'<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-label-caps text-label-caps border whitespace-nowrap ' +
			statusPillClasses(tone) +
			'">' +
			esc(text) +
			"</span>"
		);
	}

	function fillSelect($el, options, selected) {
		var html = (options || [])
			.map(function (o) {
				var id = o.id || o.value || "";
				var label = o.label || o.name || id;
				if (o.code && o.name) {
					label = o.name + " (" + o.code + ")";
				}
				return (
					'<option value="' +
					esc(id) +
					'">' +
					esc(label) +
					"</option>"
				);
			})
			.join("");
		$el.html(html);
		if (selected) {
			$el.val(selected);
		}
	}

	function setHidden($el, hidden) {
		if (hidden) {
			$el.addClass("hidden").attr("hidden", "hidden");
		} else {
			$el.removeClass("hidden").removeAttr("hidden");
		}
	}

	function bindPlanningWorkspaceLegacy($root) {
		if (!$root || !$root.length) {
			return;
		}
		$root.attr("data-kt-pln-live", "0");
		var state = {
			pe: $root.attr("data-kt-pln-pe") || "",
			fy: $root.attr("data-kt-pln-fy") || "",
			workFilter: $root.attr("data-kt-pln-work-filter") || "all",
			search: "",
			queueRows: [],
		};

		function openPlanLabelHtml() {
			return (
				__("Open current plan") +
				' <span class="material-symbols-outlined text-[20px]" aria-hidden="true">arrow_forward</span>'
			);
		}

		function formatPlannedAmount(plan) {
			var display = String(plan.planned_total_display || "").trim();
			if (display) {
				return display;
			}
			if (plan.planned_total != null) {
				return "KES " + String(plan.planned_total);
			}
			return "KES 0";
		}

		function lifecycleDotClass(life) {
			var tone = lifecycleTone(life);
			if (tone === "available") {
				return "w-2 h-2 rounded-full bg-status-available";
			}
			if (tone === "exhausted") {
				return "w-2 h-2 rounded-full bg-status-exhausted";
			}
			if (tone === "reserved") {
				return "w-2 h-2 rounded-full bg-status-reserved";
			}
			if (tone === "primary") {
				return "w-2 h-2 rounded-full bg-primary";
			}
			return "w-2 h-2 rounded-full bg-outline-variant";
		}

		function validationIcon(planVal) {
			var tone = validationTone(planVal);
			if (tone === "available") {
				return "check_circle";
			}
			if (tone === "exhausted") {
				return "error";
			}
			return "warning";
		}

		function rowMatchesSearch(r, q) {
			if (!q) {
				return true;
			}
			var hay = [
				r.title,
				r.demand_code,
				r.organisation_unit_label,
				r.organisation_unit,
				r.reason,
				r.status,
			]
				.join(" ")
				.toLowerCase();
			return hay.indexOf(q) !== -1;
		}

		function renderQueueRows(pageRows) {
			var $tbody = $root.find("[data-kt-pln-queue-body]");
			if (!pageRows || !pageRows.length) {
				$tbody.html(
					'<tr><td colspan="6" class="p-3 font-body-md text-body-md text-on-surface-variant">' +
						__("No work items for this filter.") +
						"</td></tr>"
				);
				return;
			}
			var body = pageRows
				.map(function (r) {
					var status = String(r.status || "Ready");
					var pillTone = "available";
					if (/return/i.test(status)) {
						pillTone = "exhausted";
					} else if (/attention|pending/i.test(status)) {
						pillTone = "reserved";
					}
					var actionIcon =
						r.action === "add_to_plan" ? "add_circle" : "arrow_forward";
					return (
						'<tr class="hover:bg-surface-container-lowest transition-colors group" data-kt-pln-queue-row data-kt-pln-demand="' +
						esc(r.demand || "") +
						'">' +
						'<td class="p-3 font-medium whitespace-normal">' +
						esc(r.title || "") +
						(r.demand_code
							? '<div class="font-body-sm text-body-sm text-on-surface-variant font-data-mono mt-0.5">' +
							  esc(r.demand_code) +
							  "</div>"
							: "") +
						"</td>" +
						'<td class="p-3 text-on-surface-variant whitespace-normal">' +
						esc(r.organisation_unit_label || r.organisation_unit || "") +
						"</td>" +
						'<td class="p-3 text-right font-data-md whitespace-normal">' +
						esc(r.amount_display || "") +
						"</td>" +
						'<td class="p-3 text-on-surface-variant whitespace-normal">' +
						esc(r.reason || "") +
						"</td>" +
						'<td class="p-3"><span class="inline-flex items-center px-2 py-0.5 rounded-full bg-status-' +
						pillTone +
						"/10 text-status-" +
						pillTone +
						' text-xs font-semibold">' +
						esc(status) +
						"</span></td>" +
						'<td class="p-3 text-right"><button type="button" class="text-primary hover:text-primary-container font-medium text-sm flex items-center justify-end gap-1 ml-auto" data-kt-pln-queue-action="' +
						esc(r.action || "view") +
						'" data-kt-pln-demand="' +
						esc(r.demand || "") +
						'" data-kt-pln-builder-route="' +
						esc(r.builder_route || "") +
						'" data-kt-pln-demand-route="' +
						esc(r.demand_route || "") +
						'">' +
						'<span class="material-symbols-outlined text-[18px]" aria-hidden="true">' +
						actionIcon +
						"</span> " +
						esc(r.action_label || "View") +
						"</button></td></tr>"
					);
				})
				.join("");
			$tbody.html(body);
		}

		function paintQueue() {
			var q = String(state.search || "")
				.trim()
				.toLowerCase();
			var filtered = (state.queueRows || []).filter(function (r) {
				return rowMatchesSearch(r, q);
			});
			if (
				window.kentender_core &&
				kentender_core.table &&
				typeof kentender_core.table.attachPagination === "function"
			) {
				kentender_core.table
					.attachPagination($root, {
						renderPage: function (pageRows) {
							renderQueueRows(pageRows);
						},
					})
					.setRows(filtered, true);
			} else {
				renderQueueRows(filtered);
			}
		}

		function paint(dto) {
			$root.attr("data-kt-pln-live", "1");
			$root.attr("data-kt-pln-mode", dto.selection_mode || "");
			var readOnly = !!dto.read_only;
			$root.attr("data-kt-pln-read-only", readOnly ? "1" : "0");
			fillSelect(
				$root.find('[data-kt-pln-filter="procuring_entity"]'),
				dto.procuring_entities || [],
				dto.procuring_entity || ""
			);
			fillSelect(
				$root.find('[data-kt-pln-filter="financial_year"]'),
				dto.financial_years || [],
				dto.financial_year || state.fy
			);
			state.pe = dto.procuring_entity || "";
			state.fy = dto.financial_year || state.fy;
			$root.attr("data-kt-pln-pe", state.pe);
			$root.attr("data-kt-pln-fy", state.fy);

			$root
				.find("[data-kt-pln-helper-text]")
				.text(
					dto.helper_text ||
						__(
							"These controls define the workspace scope; they do not assign ownership to records."
						)
				);

			var $workType = $root.find('[data-kt-pln-filter="work_type"]');
			if ($workType.length && $workType.val() !== state.workFilter) {
				$workType.val(state.workFilter || "all");
			}

			var blocked = dto.selection_mode === "blocked";
			setHidden($root.find("[data-kt-pln-blocked]"), !blocked);
			if (blocked) {
				$root
					.find("[data-kt-pln-blocked-msg]")
					.text(
						dto.blocked_reason ||
							__("An authorised Procuring Entity assignment is required.")
					);
			}

			var canCreate = !readOnly && !!dto.can_create_plan;
			$root.attr("data-kt-pln-can-create", canCreate ? "1" : "0");
			setHidden($root.find('[data-testid="kt-pln-ui01-register"]'), !canCreate);

			var plan = dto.current_plan;
			var $noPlan = $root.find("[data-kt-pln-no-plan]");
			var $open = $root.find('[data-kt-pln-action="open-plan"]');
			var $continue = $root.find('[data-kt-pln-action="continue-plan"]');
			if (plan) {
				setHidden($noPlan, true);
				$root.find("[data-kt-pln-plan-title]").text(plan.title || plan.plan_code || plan.plan);
				var life = plan.lifecycle_state || "—";
				$root.find("[data-kt-pln-plan-lifecycle]").text(life);
				$root.find("[data-kt-pln-plan-lifecycle-dot]").attr("class", lifecycleDotClass(life));
				$root
					.find("[data-kt-pln-plan-version]")
					.text(plan.version_label || plan.contributions_display || "—");
				$root.find("[data-kt-pln-plan-items]").text(String(plan.item_count || 0));
				$root.find("[data-kt-pln-plan-total-amount]").text(formatPlannedAmount(plan));
				var planVal = plan.validation_projection || "Not run";
				$root.find("[data-kt-pln-plan-validation]").text(planVal);
				$root.find("[data-kt-pln-plan-validation-icon]").text(validationIcon(planVal));
				$root.attr("data-kt-pln-plan", plan.plan || "");
				$root.attr("data-kt-pln-builder-route", plan.builder_route || "");
				setHidden($open, false);
				setHidden($continue, false);
				$open
					.html(openPlanLabelHtml())
					.prop("disabled", false)
					.attr("aria-disabled", "false");
				$continue
					.text(__("Continue planning"))
					.prop("disabled", false)
					.attr("aria-disabled", "false");
				setHidden($root.find('[data-testid="kt-pln-ui01-header-create"]'), true);
			} else {
				$root.find("[data-kt-pln-plan-title]").text(__("No annual plan for this context"));
				$root.find("[data-kt-pln-plan-lifecycle]").text("—");
				$root
					.find("[data-kt-pln-plan-lifecycle-dot]")
					.attr("class", "w-2 h-2 rounded-full bg-outline-variant");
				$root.find("[data-kt-pln-plan-version]").text("—");
				$root.find("[data-kt-pln-plan-items]").text("0");
				$root.find("[data-kt-pln-plan-total-amount]").text("KES 0");
				$root.find("[data-kt-pln-plan-validation]").text("Not run");
				$root.find("[data-kt-pln-plan-validation-icon]").text("warning");
				$root.removeAttr("data-kt-pln-plan");
				$root.removeAttr("data-kt-pln-builder-route");

				var peChosen = !!dto.procuring_entity && dto.procuring_entity !== "__all__";
				var showCreateEmpty = !blocked && canCreate && peChosen;
				var showReadOnlyEmpty = !blocked && !canCreate && peChosen;

				var $headerCreate = $root.find('[data-testid="kt-pln-ui01-header-create"]');
				if (!$headerCreate.length) {
					$headerCreate = $(
						'<button type="button" class="w-full sm:w-auto bg-primary text-on-primary font-body-md px-6 py-2.5 rounded-lg hover:bg-primary-container-low shadow-sm transition-colors flex justify-center items-center gap-2 whitespace-nowrap" data-kt-pln-action="register" data-testid="kt-pln-ui01-header-create"></button>'
					);
					$root.find('[data-testid="kt-pln-ui01-header-actions"]').append($headerCreate);
				}

				if (showCreateEmpty) {
					setHidden($noPlan, false);
					$noPlan
						.find("[data-kt-pln-no-plan-msg]")
						.text(
							__("No plan registered for this Procuring Entity and financial year.")
						);
					setHidden($noPlan.find('[data-testid="kt-pln-ui01-register"]'), false);
					setHidden($open, true);
					setHidden($continue, true);
					$headerCreate.text(__("Create annual plan"));
					setHidden($headerCreate, false);
				} else if (showReadOnlyEmpty) {
					setHidden($noPlan, false);
					$noPlan
						.find("[data-kt-pln-no-plan-msg]")
						.text(
							__(
								"No plan registered for this Procuring Entity and financial year. Support viewers can browse existing plans only; create stays with operational Planning roles."
							)
						);
					setHidden($noPlan.find('[data-testid="kt-pln-ui01-register"]'), true);
					setHidden($open, true);
					setHidden($continue, true);
					setHidden($headerCreate, true);
				} else {
					setHidden($noPlan, true);
					setHidden($open, blocked || !peChosen);
					setHidden($continue, true);
					setHidden($headerCreate, true);
					if (!peChosen && !blocked) {
						$open
							.html(openPlanLabelHtml())
							.prop("disabled", true)
							.attr("aria-disabled", "true");
					}
				}
			}

			state.queueRows = blocked ? [] : dto.work_queue || [];
			paintQueue();
		}

		function refresh() {
			return call("get_planning_workspace", {
				procuring_entity: state.pe || null,
				financial_year: state.fy || "",
				work_filter: state.workFilter || "all",
			})
				.then(paint)
				.catch(function (err) {
					$root.attr("data-kt-pln-live", "1");
					$root.attr("data-kt-pln-error", "1");
					$root.attr("data-kt-pln-mode", "blocked");
					setHidden($root.find("[data-kt-pln-blocked]"), false);
					$root
						.find("[data-kt-pln-blocked-msg]")
						.text(__("An authorised Procuring Entity assignment is required."));
					console.warn("Planning workspace load failed", err);
				});
		}

		$root.off(".ktPlnWs");
		$root.on("change.ktPlnWs", "[data-kt-pln-filter]", function () {
			var key = $(this).attr("data-kt-pln-filter");
			if (key === "procuring_entity") {
				state.pe = $(this).val() || "";
			}
			if (key === "financial_year") {
				state.fy = $(this).val() || "";
			}
			if (key === "work_type") {
				state.workFilter = $(this).val() || "all";
				$root.attr("data-kt-pln-work-filter", state.workFilter);
			}
			refresh();
		});
		$root.on("input.ktPlnWs", "[data-kt-pln-work-search]", function () {
			state.search = $(this).val() || "";
			paintQueue();
		});
		$root.on("click.ktPlnWs", '[data-kt-pln-action="register"]', function (e) {
			e.preventDefault();
			frappe.set_route("procurement-plan-register");
		});
		$root.on(
			"click.ktPlnWs",
			'[data-kt-pln-action="open-plan"], [data-kt-pln-action="continue-plan"]',
			function (e) {
				e.preventDefault();
				var route = $root.attr("data-kt-pln-builder-route");
				var plan = $root.attr("data-kt-pln-plan");
				if (route) {
					navigate(route);
					return;
				}
				if (plan) {
					frappe.set_route("procurement-plan-builder", { plan: plan });
					return;
				}
				if (
					$root.attr("data-kt-pln-can-create") === "1" &&
					$root.attr("data-kt-pln-mode") !== "blocked"
				) {
					frappe.set_route("procurement-plan-register");
					return;
				}
				frappe.show_alert({
					message: __(
						"No annual plan exists for this context. Create requires an operational Planning assignment."
					),
					indicator: "orange",
				});
			}
		);
		$root.on("click.ktPlnWs", "[data-kt-pln-queue-action]", function (e) {
			e.preventDefault();
			var action = $(this).attr("data-kt-pln-queue-action") || "view";
			var demand = $(this).attr("data-kt-pln-demand") || "";
			var demandRoute = $(this).attr("data-kt-pln-demand-route") || "";
			var plan = $root.attr("data-kt-pln-plan");
			var builder = $root.attr("data-kt-pln-builder-route");
			if (action === "add_to_plan" && (builder || plan)) {
				if (builder) {
					navigate(builder);
					return;
				}
				frappe.set_route("procurement-plan-builder", { plan: plan });
				return;
			}
			if (action === "confirm_funding") {
				var financeRoute = $(this).attr("data-kt-pln-builder-route") || builder;
				if (financeRoute) {
					navigate(financeRoute);
					return;
				}
			}
			if (demand && demandRoute) {
				var routeParts = demandRoute
					.replace(/^\/?(?:desk|app)\//, "")
					.split("/")
					.filter(Boolean);
				frappe.set_route(routeParts);
			}
		});

		return refresh();
	}

	function bindPlanningWorkspace($root) {
		if (!$root || !$root.length) {
			return;
		}
		$root.attr("data-kt-pln-live", "0");
		var savedContext = kentender_procurement.planning_client
			? kentender_procurement.planning_client.routeContext()
			: {};
		var state = {
			pe: $root.attr("data-kt-pln-pe") || savedContext.procuring_entity || "",
			fy: $root.attr("data-kt-pln-fy") || savedContext.financial_year || "",
			workFilter: $root.attr("data-kt-pln-work-filter") || "all",
			search: "",
			request: 0,
			dto: null,
		};
		var searchTimer = null;

		function setBackgroundRefreshing(refreshing) {
			$root.attr("data-kt-pln-refreshing", refreshing ? "1" : "0");
			$root.attr("aria-busy", refreshing ? "true" : "false");
			$root
				.find('[data-testid="kt-pln-ui01-work-section"]')
				.attr("aria-busy", refreshing ? "true" : "false");
		}

		function navigate(route) {
			if (!route) {
				return;
			}
			var url = new URL(route, window.location.origin);
			var parts = url.pathname
				.replace(/^\/(?:app|desk)\//, "")
				.split("/")
				.filter(Boolean);
			var query = {};
			url.searchParams.forEach(function (value, key) {
				query[key] = value;
			});
			frappe.route_options = Object.assign({}, query);
			if (parts.length === 1 && query.plan) {
				parts.push(query.plan);
			} else if (parts.length === 1 && query.plan_item) {
				parts.push(query.plan_item);
			}
			frappe.set_route(parts);
		}

		function metric(label, value, kind, validation) {
			var valueClass = kind === "money" ? "font-data-md kt-pln-data-value" : "font-body-md";
			var icon = "";
			if (kind === "finance") {
				icon = '<span class="material-symbols-outlined kt-pln-icon-filled kt-pln-available" aria-hidden="true">verified</span>';
			}
			if (kind === "validation") {
				var tone = validationTone(validation);
				icon = '<span class="material-symbols-outlined kt-pln-icon-filled kt-pln-' + tone + '" aria-hidden="true">' + validationIcon(validation, tone) + "</span>";
				valueClass += " kt-pln-" + tone;
			}
			return (
				'<div class="kt-pln-metric"><span class="font-label-caps text-label-caps text-on-surface-variant">' +
				esc(label) +
				'</span><div class="kt-pln-metric-value">' + icon + '<span class="' + valueClass + '">' + esc(value) + "</span></div></div>"
			);
		}

		function renderSummary(plan) {
			var html = (plan.summary_metrics || []).map(function (item) {
				return metric(
					item.label || "",
					String(item.value || "").replace(/\.00\b/g, ""),
					item.kind || "text",
					item.status || item.value || ""
				);
			}).join("");
			$root.find("[data-kt-pln-summary-grid]").html(html);
		}

		function renderStatusLine(plan) {
			var html = '<span class="kt-pln-plan-state">' + esc((plan.lifecycle_state || "Open") + " Plan") + "</span>";
			(plan.status_parts || []).slice(1).forEach(function (part) {
				html += '<span class="kt-pln-status-separator" aria-hidden="true">·</span>';
				var approved = /^Approved Version/.test(part);
				html += '<span class="kt-pln-version-status">' +
					(approved ? '<span class="material-symbols-outlined kt-pln-icon-filled kt-pln-available" aria-hidden="true">check_circle</span>' : "") +
					esc(part) + "</span>";
			});
			if (plan.supporting_text) {
				html += '<span class="kt-pln-status-separator" aria-hidden="true">|</span><em>' + esc(plan.supporting_text) + "</em>";
			}
			$root.find("[data-kt-pln-plan-status-line]").html(html);
		}

		function statusTone(status) {
			var value = String(status || "").toLowerCase();
			if (/return|blocked|stale/.test(value)) {
				return "exhausted";
			}
			if (/awaiting|attention|incomplete|draft|no changes/.test(value)) {
				return "reserved";
			}
			return "primary";
		}

		function rowsHtml(rows) {
			return (rows || [])
				.map(function (row) {
					var action = row.action || {};
					var tone = statusTone(row.status);
					var actionHtml = action.route && action.label
						? '<button type="button" class="kt-pln-row-action" data-kt-pln-route="' + esc(action.route) +
							'" data-kt-pln-row-action="' + esc(action.code || "view") + '" aria-label="' +
							esc(action.label + " " + (row.title || "")) + '">' + esc(action.label) +
							'<span class="material-symbols-outlined text-xs" aria-hidden="true">arrow_forward</span></button>'
						: "";
					return (
							'<tr data-kt-pln-row="' + esc(row.resource_key || "") + '"><td><div class="kt-pln-work-title">' +
							esc(row.title || "") +
							'</div><span class="font-data-md kt-pln-reference">' + esc(row.reference || row.demand_code || "") +
							"</span></td><td>" + esc(row.work_type || "") + "</td><td>" +
							esc(row.organisation_unit_label || row.organisation_unit || "") +
							'</td><td class="text-right font-data-md kt-pln-data-value">' + esc(String(row.amount_display || "—").replace(/\.00$/, "")) +
						"</td><td>" + esc(row.reason || "") + '</td><td><span class="kt-pln-status-pill kt-pln-status-' + tone + '">' +
						esc(row.status || "") +
						'</span></td><td>' + actionHtml + "</td></tr>"
					);
				})
				.join("");
		}

		function waitingRowsHtml(rows) {
			return (rows || []).map(function (row) {
				return '<tr data-kt-pln-row="' + esc(row.resource_key || "") + '"><td><div class="kt-pln-work-title">' +
					esc(row.title || "") + '</div><span class="font-data-md kt-pln-reference">' + esc(row.reference || "") +
					'</span></td><td>' + esc(row.stage || "") + '</td><td><span class="kt-pln-status-pill kt-pln-status-' +
					statusTone(row.status) + '">' + esc(row.status || "") + '</span></td><td>' + esc(row.with_role || "") + "</td></tr>";
			}).join("");
		}

		function paint(dto) {
			state.dto = dto;
			state.pe = dto.procuring_entity || state.pe;
			state.fy = dto.financial_year || state.fy;
			$root
				.attr("data-kt-pln-live", "1")
				.attr("data-kt-pln-mode", dto.selection_mode || "")
				.removeAttr("data-kt-pln-error");
			setBackgroundRefreshing(false);
			$root.attr("data-kt-pln-state", dto.workspace_state || "");
			$root.attr("data-kt-pln-projection", dto.projection_token || "");
			$root.attr("data-kt-pln-read-only", dto.read_only ? "1" : "0");
			$root.attr("data-kt-pln-can-create", dto.can_create_plan ? "1" : "0");
			$root.attr("data-kt-pln-pe", state.pe).attr("data-kt-pln-fy", state.fy);
			setHidden($root.find("[data-kt-pln-loading]"), true);
			setHidden($root.find("[data-kt-pln-error]"), true);
			var blocked = dto.selection_mode === "blocked";
			setHidden($root.find("[data-kt-pln-blocked]"), !blocked);
			$root.find("[data-kt-pln-blocked-msg]").text(dto.blocked_reason || "An authorised Procuring Entity assignment is required.");
			setHidden($root.find("[data-kt-pln-content]"), blocked);
			if (blocked) {
				return;
			}
			var single = dto.selection_mode === "single_readonly";
			var $peSelect = $root.find("[data-kt-pln-pe-select]");
			fillSelect($peSelect, dto.procuring_entities || [], dto.procuring_entity || "");
			if (!single && !dto.procuring_entity) {
				$peSelect.prepend(
					'<option value="">' + esc(__("Select a Procuring Entity")) + "</option>"
				);
				$peSelect.val("");
			}
			setHidden($peSelect, single);
			$root.find("[data-kt-pln-pe-readonly]").text(dto.procuring_entity_label || "Select a Procuring Entity");
			fillSelect($root.find('[data-kt-pln-filter="financial_year"]'), dto.financial_years || [], state.fy);
			fillSelect($root.find('[data-kt-pln-filter="work_type"]'), dto.filter_options || [], state.workFilter);
			$root.find("[data-kt-pln-fy-readonly]").text(state.fy || "");
			$root.find("[data-kt-pln-context-helper]").text(dto.helper_text || "");
			var editingContext = $root.attr("data-kt-pln-context-editing") === "1";
			var needsSelection = !dto.procuring_entity;
			setHidden($root.find("[data-kt-pln-context-summary]"), needsSelection || editingContext);
			setHidden($root.find("[data-kt-pln-context-controls]"), !needsSelection && !editingContext);

			var plan = dto.current_plan;
			setHidden($root.find("[data-kt-pln-plan-panel]"), !dto.procuring_entity);
			setHidden($root.find("[data-kt-pln-current-plan]"), !plan);
			setHidden($root.find("[data-kt-pln-no-plan]"), !!plan || !dto.procuring_entity);
			if (plan) {
				$root.attr("data-kt-pln-plan", plan.plan || "");
				$root.find("[data-kt-pln-plan-reference]").text(plan.plan_code || plan.plan || "");
				$root.find("[data-kt-pln-plan-title]").text(String(plan.title || "").replace(/ Annual Procurement Plan FY (\d{4}\/\d{2})$/, " Annual Procurement Plan $1"));
				renderStatusLine(plan);
				renderSummary(plan);
			} else {
				$root.removeAttr("data-kt-pln-plan");
				var emptyStates = dto.empty_states || {};
				$root.find("[data-kt-pln-no-plan-heading]").text(emptyStates.current_plan_heading || "No annual Procurement Plan");
				$root.find("[data-kt-pln-no-plan-msg]").text(emptyStates.current_plan || "No annual Procurement Plan exists for this context.");
				$root.find("[data-kt-pln-no-plan-supporting]").text(emptyStates.current_plan_supporting || "");
			}
			var primary = dto.primary_action;
			setHidden($root.find("[data-kt-pln-primary-action]"), !primary);
			if (primary) {
				$root.find("[data-kt-pln-primary-label]").text(primary.label || "Continue");
				$root.find("[data-kt-pln-primary-action]").attr("data-kt-pln-route", primary.route || "");
			}

			var work = dto.work_requiring_action || dto.work_queue || [];
			var waiting = dto.waiting_on_others || [];
			setHidden($root.find("[data-kt-pln-work-controls]"), !dto.show_work_controls);
			$root.find("[data-kt-pln-work-body]").html(rowsHtml(work));
			$root.find("[data-kt-pln-waiting-body]").html(waitingRowsHtml(waiting));
			setHidden($root.find("[data-kt-pln-work-table]"), !work.length);
			setHidden($root.find("[data-kt-pln-work-empty]"), !!work.length);
			setHidden($root.find("[data-kt-pln-waiting-table]"), !waiting.length);
			setHidden($root.find("[data-kt-pln-waiting-empty]"), !!waiting.length);
			$root.find("[data-kt-pln-work-empty-text]").text((dto.empty_states || {}).work_requiring_action || "Nothing currently requires your planning action.");
			$root.find("[data-kt-pln-waiting-empty-text]").text((dto.empty_states || {}).waiting_on_others || "Nothing is currently waiting on another reviewer.");
			if (state.persistContext && state.pe && state.fy) {
				state.persistContext = false;
				call("select_planning_context", { procuring_entity: state.pe, financial_year: state.fy }).catch(function (error) {
					console.warn("Planning context selection could not be saved", error);
				});
			}
		}

		function refresh() {
			var request = ++state.request;
			var initialLoad = !state.dto;
			setHidden($root.find("[data-kt-pln-loading]"), !initialLoad);
			setHidden($root.find("[data-kt-pln-error]"), true);
			setBackgroundRefreshing(!initialLoad);
			return call("get_planning_workspace", {
				procuring_entity: state.pe || null,
				financial_year: state.fy,
				work_filter: state.workFilter,
				search: state.search,
			})
				.then(function (dto) {
					if (request === state.request) {
						paint(dto || {});
					}
				})
				.catch(function (error) {
					if (request !== state.request) {
						return;
					}
					setBackgroundRefreshing(false);
					setHidden($root.find("[data-kt-pln-loading]"), true);
					if (initialLoad) {
						setHidden($root.find("[data-kt-pln-content]"), true);
						setHidden($root.find("[data-kt-pln-error]"), false);
						$root.find("[data-kt-pln-error]").trigger("focus");
						$root.attr("data-kt-pln-live", "1").attr("data-kt-pln-error", "1");
					} else if (frappe.show_alert) {
						frappe.show_alert({
							message: __("The planning work list could not be refreshed."),
							indicator: "red",
						});
					}
					console.warn("Planning workspace load failed", error);
				});
		}

		$root.off(".ktPlnWs");
		// CTX-CHG-001 — a PE switched from the shared rail on any Vue page is a
		// change to the same global preference this workspace resolves from;
		// re-resolve rather than keep painting the old entity.
		$(document).off("kt:working-pe-changed.ktPlnWs").on(
			"kt:working-pe-changed.ktPlnWs",
			function () {
				if (!$root.closest("body").length) return; // page unmounted
				state.pe = "";
				state.fy = "";
				refresh();
			}
		);
		$root.on("change.ktPlnWs", '[data-kt-pln-filter="procuring_entity"]', function () {
			state.pe = $(this).val() || "";
			state.fy = "";
			state.persistContext = true;
			$root.attr("data-kt-pln-context-editing", "0");
			refresh();
		});
		$root.on("change.ktPlnWs", '[data-kt-pln-filter="financial_year"]', function () {
			state.fy = $(this).val() || "";
			state.persistContext = true;
			$root.attr("data-kt-pln-context-editing", "0");
			refresh();
		});
		$root.on("click.ktPlnWs", '[data-kt-pln-action="change-context"]', function () {
			$root.attr("data-kt-pln-context-editing", "1");
			setHidden($root.find("[data-kt-pln-context-summary]"), true);
			setHidden($root.find("[data-kt-pln-context-controls]"), false);
			var $target = $root.find('[data-kt-pln-filter="procuring_entity"]:visible');
			if (!$target.length) {
				$target = $root.find('[data-kt-pln-filter="financial_year"]');
			}
			$target.trigger("focus");
		});
		$root.on("change.ktPlnWs", '[data-kt-pln-filter="work_type"]', function () {
			state.workFilter = $(this).val() || "all";
			$root.attr("data-kt-pln-work-filter", state.workFilter);
			refresh();
		});
		$root.on("input.ktPlnWs", "[data-kt-pln-work-search]", function () {
			state.search = $(this).val() || "";
			window.clearTimeout(searchTimer);
			searchTimer = window.setTimeout(refresh, 250);
		});
		$root.on("click.ktPlnWs", "[data-kt-pln-primary-action], [data-kt-pln-row-action]", function (event) {
			event.preventDefault();
			navigate($(this).attr("data-kt-pln-route") || "");
		});
		$root.on("click.ktPlnWs", '[data-kt-pln-action="retry"]', function () {
			refresh();
		});
		$root.on("kt:teardown.ktPlnWs", function () {
			state.request += 1;
			window.clearTimeout(searchTimer);
			setBackgroundRefreshing(false);
		});
		return refresh();
	}

	function bindPlanningRegister($root) {
		if (!$root || !$root.length) {
			return;
		}
		$root.attr("data-kt-pln-live", "0");
		var titleDefault = "";
		var monthNames = [
			"January",
			"February",
			"March",
			"April",
			"May",
			"June",
			"July",
			"August",
			"September",
			"October",
			"November",
			"December",
		];

		function formatPlanPeriodDate(iso) {
			if (!iso || iso === "—") {
				return iso || "—";
			}
			var m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
			if (!m) {
				return iso;
			}
			return parseInt(m[3], 10) + " " + monthNames[parseInt(m[2], 10) - 1] + " " + m[1];
		}

		function clearErrors() {
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($root);
			} else {
				$root.find("[data-kt-field-error]").text("").attr("hidden", "hidden");
			}
		}

		function showErrors(errors) {
			if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
				window.ktFormErrors.show($root, errors || {});
			}
			// Ensure HTML hidden attribute is cleared (fixture slots use both class + attr).
			Object.keys(errors || {}).forEach(function (k) {
				$root
					.find('[data-kt-field-error="' + k + '"]')
					.removeAttr("hidden")
					.removeClass("hidden");
			});
		}

		function paint(scope) {
			$root.attr("data-kt-pln-live", "1");
			$root.attr("data-kt-pln-mode", scope.selection_mode || "");
			titleDefault = scope.title_default || "";
			$root.find("[data-kt-pln-title]").val(titleDefault);

			var blocked = scope.selection_mode === "blocked";
			setHidden($root.find("[data-kt-pln-register-blocked]"), !blocked);
			setHidden($root.find("[data-kt-pln-register-form]"), blocked);
			if (blocked) {
				$root
					.find("[data-kt-pln-register-blocked-msg]")
					.text(
						scope.blocked_reason ||
							__("An authorised Procuring Entity assignment is required before you can register a plan.")
					);
				return;
			}

			var $pe = $root.find('[data-kt-field="procuring_entity"]');
			var $peReadonly = $root.find("[data-kt-pln-pe-readonly]");
			var $peWrap = $root.find("[data-kt-pln-pe-select-wrap]");
			var mode = scope.selection_mode || "";
			// Contract modes: single_readonly | multi_required | blocked
			if (mode === "single_readonly" || mode === "single") {
				setHidden($peWrap, true);
				setHidden($pe, true);
				setHidden($peReadonly, false);
				var pe = (scope.procuring_entities || []).find(function (e) {
					return e.id === scope.procuring_entity;
				});
				var peLabel = pe
					? pe.name + " (" + (pe.code || pe.id) + ")"
					: scope.procuring_entity;
				$peReadonly.text(peLabel);
				$peReadonly.attr("data-kt-pln-pe-id", scope.procuring_entity || "");
				$root.find("[data-kt-pln-pe-helper]").text(scope.single_pe_helper || "");
				fillSelect($pe, scope.procuring_entities || [], scope.procuring_entity);
			} else {
				setHidden($peWrap, false);
				setHidden($pe, false);
				setHidden($peReadonly, true);
				fillSelect($pe, scope.procuring_entities || [], scope.procuring_entity || "");
				$root.find("[data-kt-pln-pe-helper]").text(scope.helper_pe || "");
			}

			fillSelect(
				$root.find('[data-kt-field="financial_year"]'),
				scope.financial_years || [],
				scope.financial_year
			);
			var periodStart = scope.period_start || "—";
			var periodEnd = scope.period_end || "—";
			$root
				.find("[data-kt-pln-period-label]")
				.text(formatPlanPeriodDate(periodStart) + " – " + formatPlanPeriodDate(periodEnd));
			var currencies = scope.currencies || [{ id: "KES", label: "KES - Kenyan Shilling" }];
			fillSelect(
				$root.find('[data-kt-field="currency"]'),
				currencies,
				scope.currency || "KES"
			);
		}

		function reload(selectedPe) {
			return call("get_planning_create_scope", {
				selected_pe: selectedPe || null,
				financial_year: $root.find('[data-kt-field="financial_year"]').val() || "",
			})
				.then(paint)
				.catch(function (err) {
					$root.attr("data-kt-pln-live", "1");
					$root.attr("data-kt-pln-error", "1");
					$root.attr("data-kt-pln-mode", "blocked");
					console.warn("Planning create scope failed", err);
					setHidden($root.find("[data-kt-pln-register-blocked]"), false);
					setHidden($root.find("[data-kt-pln-register-form]"), true);
					$root
						.find("[data-kt-pln-register-blocked-msg]")
						.text(
							__(
								"An authorised Procuring Entity assignment is required before you can register a plan."
							)
						);
				});
		}

		$root.off(".ktPlnReg");
		$root.on("change.ktPlnReg", '[data-kt-field="procuring_entity"]', function () {
			reload($(this).val() || null);
		});
		$root.on("change.ktPlnReg", '[data-kt-field="financial_year"]', function () {
			reload(
				$root.find('[data-kt-field="procuring_entity"]').val() ||
					$root.find("[data-kt-pln-pe-readonly]").attr("data-kt-pln-pe-id") ||
					null
			);
		});
		$root.on("submit.ktPlnReg", "[data-kt-pln-register-form]", function (e) {
			e.preventDefault();
			clearErrors();
			var pe =
				$root.find('[data-kt-field="procuring_entity"]').val() ||
				$root.find("[data-kt-pln-pe-readonly]").attr("data-kt-pln-pe-id") ||
				"";
			var fy = $root.find('[data-kt-field="financial_year"]').val() || "";
			var $btn = $root.find('[data-testid="kt-pln-ui02-submit"]');
			$btn.prop("disabled", true);
			call("create_procurement_plan", {
				procuring_entity: pe,
				financial_year: fy,
			})
				.then(function (result) {
					if (!result || result.ok === false) {
						showErrors((result && result.errors) || { form: __("Could not create plan") });
						$btn.prop("disabled", false);
						return;
					}
					frappe.show_alert({
						message: __("Annual plan created"),
						indicator: "green",
					});
					if (result.redirect) {
						navigate(result.redirect);
					} else if (result.plan) {
						frappe.set_route("procurement-plan-builder", { plan: result.plan });
					}
				})
				.catch(function (err) {
					console.warn("Create plan failed", err);
					$btn.prop("disabled", false);
					frappe.show_alert({
						message: __("Could not create plan"),
						indicator: "red",
					});
				});
		});

		return reload(null);
	}


	kentender_procurement.live.bindPlanningWorkspace = bindPlanningWorkspace;
	// UI-02–09 are exported by their focused revision binders loaded after this workspace binder.
})();
