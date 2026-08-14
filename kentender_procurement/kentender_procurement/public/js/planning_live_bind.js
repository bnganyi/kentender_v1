// Gate 03 — live bind for PLN-UI-01…03.
(function () {
	"use strict";

	frappe.provide("kentender_procurement.live");

	var API = "kentender_procurement.procurement_planning.api";

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

	function bindPlanningWorkspace($root) {
		if (!$root || !$root.length) {
			return;
		}
		$root.attr("data-kt-pln-live", "0");
		var state = {
			pe: $root.attr("data-kt-pln-pe") || "",
			fy: $root.attr("data-kt-pln-fy") || "2027/28",
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
				financial_year: state.fy || "2027/28",
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
				state.fy = $(this).val() || "2027/28";
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
					window.location.href = route;
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
			var plan = $root.attr("data-kt-pln-plan");
			var builder = $root.attr("data-kt-pln-builder-route");
			if (action === "add_to_plan" && (builder || plan)) {
				if (builder) {
					window.location.href = builder;
					return;
				}
				frappe.set_route("procurement-plan-builder", { plan: plan });
				return;
			}
			if (action === "confirm_funding") {
				var financeRoute = $(this).attr("data-kt-pln-builder-route") || builder;
				if (financeRoute) {
					window.location.href = financeRoute;
					return;
				}
			}
			if (demand) {
				frappe.set_route("Form", "Demand", demand);
			}
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
			fillSelect(
				$root.find('[data-kt-field="coordinating_org_unit"]'),
				scope.coordinating_org_units || [],
				scope.coordinating_org_unit || ""
			);
		}

		function reload(selectedPe) {
			return call("get_planning_create_scope", {
				selected_pe: selectedPe || null,
				financial_year: $root.find('[data-kt-field="financial_year"]').val() || "2027/28",
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
			var ou = $root.find('[data-kt-field="coordinating_org_unit"]').val() || "";
			var title = $root.find("[data-kt-pln-title]").val() || titleDefault || "";
			var currency = $root.find('[data-kt-field="currency"]').val() || "KES";
			var $btn = $root.find('[data-testid="kt-pln-ui02-submit"]');
			$btn.prop("disabled", true);
			call("create_procurement_plan", {
				procuring_entity: pe,
				financial_year: fy,
				title: title,
				currency: currency,
				coordinating_org_unit: ou,
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
						window.location.href = result.redirect;
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

	function ensureBuilderDialogs($root) {
		var $host = $root.find("[data-kt-pln-dialog-host]");
		if (!$host.length) {
			$host = $('<div data-kt-pln-dialog-host></div>').appendTo($root);
		}
		if (!$host.find("[data-kt-pln-add-demand-dialog]").length) {
			var addHtml =
				kentender_procurement.ui_fixtures &&
				typeof kentender_procurement.ui_fixtures.planning_add_demand_dialog === "function"
					? kentender_procurement.ui_fixtures.planning_add_demand_dialog()
					: "";
			if (addHtml) {
				$host.append(addHtml);
			}
		}
		if (!$host.find("[data-kt-pln-remove-item-dialog]").length) {
			var removeHtml =
				kentender_procurement.ui_fixtures &&
				typeof kentender_procurement.ui_fixtures.planning_remove_item_dialog === "function"
					? kentender_procurement.ui_fixtures.planning_remove_item_dialog()
					: "";
			if (removeHtml) {
				$host.append(removeHtml);
			}
		}
		if (!$root.find("[data-kt-pln-finance-drawer]").length) {
			var financeHtml =
				kentender_procurement.ui_fixtures &&
				typeof kentender_procurement.ui_fixtures.planning_finance_confirm_drawer ===
					"function"
					? kentender_procurement.ui_fixtures.planning_finance_confirm_drawer()
					: "";
			if (financeHtml) {
				$root.append(financeHtml);
			}
		}
		return {
			$add: $host.find("[data-kt-pln-add-demand-dialog]"),
			$remove: $host.find("[data-kt-pln-remove-item-dialog]"),
			$finance: $root.find("[data-kt-pln-finance-drawer]"),
		};
	}

	function ensureAddDemandDialog($root) {
		return ensureBuilderDialogs($root).$add;
	}

	function bindPlanningBuilder($root, opts) {
		if (!$root || !$root.length) {
			return;
		}
		opts = opts || {};
		$root.attr("data-kt-pln-live", "0");
		var plan = opts.plan || "";
		if (!plan) {
			try {
				plan = new URLSearchParams(window.location.search || "").get("plan") || "";
			} catch (e) {
				plan = "";
			}
		}
		if (!plan) {
			$root.attr("data-kt-pln-error", "1");
			$root.find("[data-kt-pln-builder-title]").text(__("Plan not specified"));
			return;
		}

		var $dialog = ensureAddDemandDialog($root);
		var $removeDialog = ensureBuilderDialogs($root).$remove;
		var $financeDrawer = ensureBuilderDialogs($root).$finance;
		var selectedIds = [];
		var lastEligRows = [];
		var dialogMode = "add";
		var lastBuilderDto = null;
		var removeTargetItem = "";
		var financeTargetItem = "";
		var financeAutoOpened = false;

		function formatKes(n, currency) {
			var cur = currency || "KES";
			var num = Number(n || 0);
			return (
				cur +
				" " +
				num.toLocaleString(undefined, {
					maximumFractionDigits: 0,
				})
			);
		}

		/** Stitch PLN-UI-04: inline "KES 455,000,000" (not stacked). */
		function moneyCellHtml(amount, currency, toneClass) {
			var cur = currency || "KES";
			var num = Number(amount || 0).toLocaleString(undefined, {
				maximumFractionDigits: 0,
			});
			return (
				'<span class="font-data-md text-data-md font-semibold ' +
				(toneClass || "text-on-surface") +
				' whitespace-nowrap">' +
				esc(cur) +
				" " +
				esc(num) +
				"</span>"
			);
		}

		function formatRequiredBy(iso) {
			if (!iso) {
				return "—";
			}
			var m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
			if (!m) {
				return iso;
			}
			var months = [
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
			return parseInt(m[3], 10) + " " + months[parseInt(m[2], 10) - 1] + " " + m[1];
		}

		function findEligRow(demandId) {
			return (lastEligRows || []).find(function (r) {
				return r.demand === demandId;
			});
		}

		function selectedRows() {
			return (selectedIds || [])
				.map(findEligRow)
				.filter(function (r) {
					return !!r;
				});
		}

		function formationModeValue() {
			var $checked = $dialog.find("[data-kt-pln-formation-mode]:checked");
			return ($checked.val() || "separate").trim();
		}

		function selectionCompatibleForCombine(rows) {
			if (!rows || rows.length < 2) {
				return false;
			}
			var ou0 = String(rows[0].organisation_unit || "").trim();
			var cat0 = String(rows[0].category || "").trim();
			return rows.every(function (r) {
				return (
					String(r.organisation_unit || "").trim() === ou0 &&
					String(r.category || "").trim() === cat0
				);
			});
		}

		function paintEligSummary() {
			var rows = selectedRows();
			var n = rows.length;
			var total = rows.reduce(function (sum, r) {
				return sum + Number(r.approved_amount || r.available_to_plan || 0);
			}, 0);
			var cur = (rows[0] && rows[0].currency) || "KES";
			var ouSet = {};
			rows.forEach(function (r) {
				ouSet[String(r.organisation_unit || r.organisation_unit_label || "")] = 1;
			});
			var ouCount = Object.keys(ouSet).filter(Boolean).length;
			$dialog
				.find("[data-kt-pln-elig-count-label]")
				.text(
					n === 1
						? __("1 Approved Demand selected")
						: __("{0} Approved Demands selected", [String(n)])
				);
			$dialog
				.find("[data-kt-pln-elig-ou-count]")
				.text(
					ouCount === 1
						? __("1 Organisation Unit")
						: __("{0} Organisation Units", [String(ouCount)])
				);
			$dialog.find("[data-kt-pln-elig-amount]").text(formatKes(total, cur));

			var showFormation = dialogMode === "add" && n >= 2;
			setHidden($dialog.find("[data-kt-pln-formation-wrap]"), !showFormation);
			// Helper for 0/1 selection only — hide when formation grid is shown.
			setHidden($dialog.find("[data-kt-pln-add-mode-footer]"), showFormation);
			if (n === 1) {
				$dialog
					.find("[data-kt-pln-ui04-helper]")
					.text(__("One Plan Item will be created."));
			} else if (n === 0) {
				$dialog
					.find("[data-kt-pln-ui04-helper]")
					.text(__("Select an Approved Demand to begin."));
			} else {
				$dialog.find("[data-kt-pln-ui04-helper]").text("");
			}

			var canCombine = selectionCompatibleForCombine(rows);
			var $combine = $dialog.find('[data-kt-pln-formation-mode][value="combined"]');
			var $combineLabel = $dialog.find("[data-kt-pln-formation-combine-label]");
			$combine.prop("disabled", !canCombine);
			$combineLabel.toggleClass("opacity-50 cursor-not-allowed", !canCombine);
			if (!canCombine && formationModeValue() === "combined") {
				$dialog
					.find('[data-kt-pln-formation-mode][value="separate"]')
					.prop("checked", true);
			}
			var mode = formationModeValue();
			setHidden(
				$dialog.find("[data-kt-pln-formation-reason-wrap]"),
				!(showFormation && mode === "combined" && canCombine)
			);

			var previewCount = !showFormation ? n : mode === "combined" && canCombine ? 1 : n;
			var callout = "";
			if (showFormation && !canCombine) {
				callout = __(
					"These Demands have different owning Organisation Units and cannot be combined in MVP 1."
				);
			} else if (showFormation && mode === "combined" && canCombine) {
				callout = __(
					"Compatible Demands will form one Proposed Plan Item preserving every source allocation."
				);
			} else if (showFormation) {
				callout = __("Each selected Demand will become its own Proposed Plan Item.");
			}
			$dialog.find("[data-kt-pln-formation-callout-copy]").text(callout);
			$dialog
				.find("[data-kt-pln-formation-preview]")
				.text(
					previewCount === 1
						? __("1 Plan Item will be created.")
						: __("{0} Plan Items will be created.", [String(previewCount)])
				);

			var $cta = $dialog.find('[data-kt-pln-action="elig-add"]');
			$cta.prop("disabled", n === 0);
			var ctaLabel = __("Create Plan Item");
			if (n >= 2 && mode === "combined" && canCombine) {
				ctaLabel = __("Create combined Plan Item");
			} else if (n >= 1) {
				ctaLabel =
					previewCount === 1
						? __("Create 1 Plan Item")
						: __("Create {0} Plan Items", [String(previewCount)]);
			}
			$dialog.find("[data-kt-pln-ui04-cta-label]").text(ctaLabel);
		}

		function applyDialogMode() {
			$dialog.attr("data-kt-pln-dialog-mode", dialogMode);
			$dialog.find("[data-kt-pln-ui04-title]").text(__("Add approved Demands"));
			$dialog
				.find("[data-kt-pln-ui04-subtitle]")
				.text(
					__(
						"Select from pre-approved strategic demands to allocate to this procurement plan."
					)
				);
			paintEligSummary();
		}

		function paintElig(rows) {
			lastEligRows = rows || [];
			selectedIds = (selectedIds || []).filter(function (id) {
				return !!findEligRow(id);
			});
			var body = lastEligRows
				.map(function (r) {
					var isSel = selectedIds.indexOf(r.demand) !== -1;
					var checked = isSel ? " checked" : "";
					// Exactly 7 <td>s — never add an absolute <td> for the left bar (shifts columns).
					var rowClass =
						"hover:bg-surface-container-low transition-colors cursor-pointer relative" +
						(isSel ? " bg-surface-container-low/50 is-selected" : "");
					var ou = r.organisation_unit_label || r.organisation_unit || "";
					var cur = r.currency || "KES";
					var fundingDisplay =
						(r.proposed_budget_line_display ||
							(r.proposed_funding && r.proposed_funding.display) ||
							"—") + "";
					var statusLabel = r.status_label || "Planning Ready";
					var amt = Number(r.approved_amount || 0).toLocaleString(undefined, {
						maximumFractionDigits: 0,
					});
					return (
						'<tr class="' +
						rowClass +
						'" data-kt-pln-elig-row data-demand="' +
						esc(r.demand) +
						'" data-available="' +
						esc(String(r.available_to_plan || 0)) +
						'">' +
						'<td class="px-container-padding py-4">' +
						'<input type="checkbox" name="demand-select" class="w-4 h-4 text-primary border-outline focus:ring-primary focus:ring-offset-0 cursor-pointer rounded"' +
						checked +
						' data-kt-pln-elig-check data-demand="' +
						esc(r.demand) +
						'" aria-label="' +
						esc(r.title || r.demand_code) +
						'" /></td>' +
						'<td class="px-container-padding py-4">' +
						'<p class="font-body-md text-body-md text-on-surface font-medium m-0" data-kt-pln-elig-title>' +
						esc(r.title || "") +
						"</p>" +
						'<p class="font-body-sm text-body-sm text-on-surface-variant mt-1 font-data-lg text-[12px] leading-tight m-0" data-kt-pln-elig-code>' +
						esc(r.demand_code || "") +
						"</p></td>" +
						'<td class="px-container-padding py-4 font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-elig-ou-cell>' +
						esc(ou) +
						"</td>" +
						'<td class="px-container-padding py-4 text-right">' +
						'<span class="font-data-md text-data-md text-on-surface font-semibold">' +
						esc(cur) +
						" " +
						esc(amt) +
						"</span></td>" +
						'<td class="px-container-padding py-4">' +
						'<span class="font-data-md text-[14px] leading-tight text-on-surface-variant">' +
						esc(formatRequiredBy(r.required_by)) +
						"</span></td>" +
						'<td class="px-container-padding py-4 font-body-sm text-body-sm text-on-surface-variant whitespace-normal" data-kt-pln-elig-funding-cell>' +
						esc(fundingDisplay) +
						"</td>" +
						'<td class="px-container-padding py-4">' +
						'<span class="inline-flex items-center px-2 py-1 rounded bg-status-available/10 text-status-available font-label-caps text-label-caps">' +
						esc(statusLabel) +
						"</span></td></tr>"
					);
				})
				.join("");
			if (!body) {
				body =
					'<tr class="hover:bg-surface-container-low transition-colors">' +
					'<td class="px-container-padding py-4 align-top">' +
					'<input aria-label="Disabled row" class="w-4 h-4 text-on-surface-variant/30 border-outline rounded" disabled type="checkbox"/>' +
					"</td>" +
					'<td class="px-container-padding py-4 text-center" colspan="6">' +
					'<span class="font-body-sm text-on-surface-variant italic">' +
					__("No eligible Demands for this filter.") +
					"</span></td></tr>";
			} else {
				body +=
					'<tr class="hover:bg-surface-container-low transition-colors" data-kt-pln-elig-end>' +
					'<td class="px-container-padding py-4 align-top">' +
					'<input aria-label="Disabled row" class="w-4 h-4 text-on-surface-variant/30 border-outline rounded" disabled type="checkbox"/>' +
					"</td>" +
					'<td class="px-container-padding py-4 text-center" colspan="6">' +
					'<span class="font-body-sm text-on-surface-variant italic">' +
					__("End of available demands based on current filters.") +
					"</span></td></tr>";
			}
			$dialog.find("[data-kt-pln-elig-body]").html(body);
			paintEligSummary();
		}

		function loadElig() {
			return call("list_eligible_demands", {
				plan: plan,
				search: $dialog.find("[data-kt-pln-elig-search]").val() || "",
				organisation_unit: $dialog.find("[data-kt-pln-elig-ou]").val() || "",
				category: $dialog.find("[data-kt-pln-elig-category]").val() || "",
				remaining_only: $dialog.find("[data-kt-pln-elig-remaining]").is(":checked")
					? 1
					: 0,
			}).then(function (dto) {
				paintElig(dto.demands || []);
			});
		}

		function openDialog() {
			dialogMode = "add";
			selectedIds = [];
			$dialog.find("[data-kt-pln-formation-reason]").val("");
			$dialog
				.find('[data-kt-pln-formation-mode][value="separate"]')
				.prop("checked", true);
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($dialog);
			}
			applyDialogMode();
			setHidden($dialog, false);
			$dialog.removeClass("hidden").removeAttr("hidden");
			return loadElig();
		}

		function closeDialog() {
			setHidden($dialog, true);
			$dialog.addClass("hidden").attr("hidden", "hidden");
			dialogMode = "add";
			selectedIds = [];
		}

		// Expose for editor "Add another Demand" CTA (same page host or builder).
		$root.data("ktPlnOpenAddDemand", openDialog);

		function paintBuilder(dto) {
			if (dto && dto.update_route && dto.current_approved_version && dto.open_draft_version) {
				window.location.href = dto.update_route;
				return;
			}
			lastBuilderDto = dto || lastBuilderDto;
			$root.attr("data-kt-pln-live", "1");
			$root.attr("data-kt-pln-plan", dto.plan || plan);
			$root.find("[data-kt-pln-builder-title]").text(dto.title || dto.plan_code || "Plan builder");
			// Stitch PLN-UI-03: Open Plan pill + "Draft Version N" + human period.
			$root
				.find("[data-kt-pln-builder-version]")
				.text(dto.version_number_label || "Draft Version 1");
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
			if (dto.period_start && dto.period_end) {
				$root
					.find("[data-kt-pln-builder-period]")
					.text(
						formatPlanPeriodDate(dto.period_start) +
							" – " +
							formatPlanPeriodDate(dto.period_end)
					);
			}
			$root.attr("data-kt-pln-concurrency", dto.concurrency_token || "");
			$root.find("[data-kt-pln-builder-items]").text(String(dto.item_count || 0));
			$root.find("[data-kt-pln-builder-total]").text(dto.planned_total_display || "KES 0");
			var finCount = dto.finance_confirmed_count != null ? dto.finance_confirmed_count : 0;
			var finTotal =
				dto.finance_confirmed_total != null
					? dto.finance_confirmed_total
					: dto.item_count || 0;
			var finDisplay =
				dto.finance_confirmed_display || finCount + " of " + finTotal;
			$root.find("[data-kt-pln-builder-finance]").text(finDisplay);
			var valProj = String(dto.validation_projection || "Not run");
			var valTone = validationTone(valProj);
			var valLower = valProj.trim().toLowerCase();
			var valPillClass =
				valLower === "not run"
					? "inline-flex items-center px-2 py-1 rounded bg-surface-container-high text-on-surface-variant font-label-caps text-label-caps w-fit border border-subtle"
					: valTone === "available"
						? "inline-flex items-center px-2 py-1 rounded bg-status-available/10 text-status-available font-label-caps text-label-caps w-fit"
						: "inline-flex items-center px-2 py-1 rounded bg-status-exhausted/10 text-status-exhausted font-label-caps text-label-caps w-fit";
			var valInner =
				valLower === "not run"
					? '<span class="w-1.5 h-1.5 rounded-full bg-on-surface-variant/40 mr-1.5" aria-hidden="true"></span> ' +
						esc(valProj)
					: valTone === "available"
						? '<span class="w-1.5 h-1.5 rounded-full bg-status-available mr-1.5" aria-hidden="true"></span> ' +
							esc(valProj)
						: '<span class="material-symbols-outlined text-[14px] mr-1" aria-hidden="true">warning</span> ' +
							esc(valProj);
			$root
				.find("[data-kt-pln-builder-validation]")
				.attr("class", valPillClass)
				.html(valInner);
			var life = String(dto.lifecycle_state || "Open");
			var openLabel = life === "Open" ? "Open Plan" : life;
			$root.find("[data-testid='kt-pln-ui03-lifecycle']").text(openLabel);
			$root.find("[data-testid='kt-pln-ui05-lifecycle']").text(openLabel);

			var empty = !!dto.empty;
			$root.attr("data-kt-pln-builder-state", empty ? "empty" : "populated");
			setHidden($root.find("[data-testid='kt-pln-ui03-header']"), !empty);
			setHidden($root.find("[data-testid='kt-pln-ui05-header']"), empty);
			setHidden($root.find("[data-kt-pln-empty-state]"), !empty);
			setHidden($root.find("[data-kt-pln-items-table]"), empty);
			setHidden($root.find('[data-testid="kt-pln-ui03-filters"]'), !empty);
			var canSubmitReview = !empty && !!dto.can_submit_for_review;
			var showIssues = !empty && !canSubmitReview;
			var $strip = $root.find("[data-kt-pln-issue-strip]");
			setHidden($strip, !showIssues);
			if (showIssues) {
				$root
					.find("[data-kt-pln-issue-copy], [data-kt-pln-issue-summary]")
					.text(
						dto.issue_summary ||
							__("Complete the Plan Item before requesting Finance confirmation.")
					);
				setHidden($root.find("[data-kt-pln-issue-action]"), false);
			}
			setHidden($root.find('[data-kt-pln-action="add-demand"]'), !dto.can_add_demand);
			setHidden($root.find('[data-testid="kt-pln-ui05-no-changes"]'), !dto.no_changes_remain);
			setHidden($root.find('[data-kt-pln-action="cancel-update"]'), !dto.can_cancel_update);

			var $run = $root.find('[data-kt-pln-action="run-validation"]');
			var $submitReview = $root.find('[data-kt-pln-action="submit-for-review"]');
			$run.prop("disabled", empty || !!dto.read_only);
			var reviewLockHint = canSubmitReview
				? ""
				: String(dto.next_step_message || "") ||
					__("Complete the Plan Item before requesting Finance confirmation.");
			if (empty) {
				$run.addClass("cursor-not-allowed opacity-50");
			} else {
				$run.removeClass("cursor-not-allowed opacity-50");
			}
			$submitReview.each(function () {
				var $btn = $(this);
				$btn
					.attr("data-kt-pln-action", "submit-for-review")
					.attr("data-testid", "kt-pln-ui05-submit-review")
					.text(__("Submit for review"))
					.prop("disabled", !canSubmitReview)
					.attr("title", canSubmitReview ? "" : reviewLockHint)
					.attr(
						"aria-label",
						canSubmitReview ? __("Submit for review") : reviewLockHint
					);
				if (canSubmitReview) {
					$btn
						.removeClass(
							"cursor-not-allowed opacity-70 bg-surface-variant text-outline bg-primary/50 text-on-primary/50"
						)
						.addClass("bg-primary text-on-primary cursor-pointer");
				} else {
					$btn
						.addClass("cursor-not-allowed opacity-70 bg-surface-variant text-outline")
						.removeClass("bg-primary text-on-primary cursor-pointer bg-primary/50 text-on-primary/50");
				}
			});

			if (!empty) {
				function incompleteCell(iconName) {
					return (
						'<span class="inline-flex items-center text-body-sm">' +
						'<span class="material-symbols-outlined text-[16px] mr-1 text-outline" aria-hidden="true">' +
						iconName +
						"</span> " +
						__("Not completed") +
						"</span>"
					);
				}
				var body = (dto.items || [])
					.map(function (it) {
						var methodText = String(it.method || "").trim();
						var scheduleText = String(it.schedule || "").trim();
						var methodHtml = methodText
							? '<span class="text-on-surface-variant">' + esc(methodText) + "</span>"
							: incompleteCell("pending");
						var scheduleHtml = scheduleText
							? '<span class="text-on-surface-variant">' + esc(scheduleText) + "</span>"
							: incompleteCell("calendar_today");
						var financeLabel = it.finance_status_label || "Not requested";
						var valLabel = it.validation_projection || "Not run";
						var valLower = String(valLabel).trim().toLowerCase();
						var valHtml =
							valLower === "needs attention"
								? '<span class="inline-flex items-center px-2.5 py-1 rounded-full bg-status-exhausted/10 text-status-exhausted font-label-caps text-label-caps">' +
									esc(valLabel) +
									"</span>"
								: validationPillHtml(valLabel);
						return (
							'<tr class="hover:bg-surface-container-low transition-colors group" data-kt-pln-item-row data-plan-item="' +
							esc(it.plan_item) +
							'">' +
							'<td class="p-4">' +
							'<div class="font-body-md text-body-md font-medium text-on-surface mb-1">' +
							esc(it.title || it.plan_item_code) +
							"</div>" +
							'<div class="font-data-md text-data-md text-on-surface-variant text-xs">' +
							esc(it.plan_item_code || "") +
							"</div></td>" +
							'<td class="p-4 font-body-sm text-body-sm text-on-surface">' +
							esc(it.owner_org_unit_label || it.owner_org_unit || "") +
							"</td>" +
							'<td class="p-4 font-data-md text-data-md text-on-surface text-right whitespace-nowrap">' +
							esc(it.amount_display || "") +
							"</td>" +
							'<td class="p-4 text-on-surface-variant">' +
							methodHtml +
							"</td>" +
							'<td class="p-4 text-on-surface-variant">' +
							scheduleHtml +
							"</td>" +
							'<td class="p-4 text-on-surface-variant font-body-sm text-body-sm">' +
							(it.can_open_finance_task
								? '<button type="button" class="text-primary hover:underline font-body-sm" data-kt-pln-action="open-finance" data-plan-item="' +
									esc(it.plan_item) +
									'" data-testid="kt-pln-ui05-open-finance">' +
									esc(financeLabel) +
									"</button>"
								: esc(financeLabel)) +
							"</td>" +
							'<td class="p-4">' +
							valHtml +
							"</td>" +
							'<td class="p-4"><div class="flex items-center justify-end space-x-3">' +
							(!dto.read_only
								? '<a href="#" class="inline-flex items-center text-primary hover:underline font-label-caps text-label-caps transition-colors" data-kt-pln-action="continue-item" data-plan-item="' +
									esc(it.plan_item) +
									'" data-testid="kt-pln-ui05-row-continue">' +
									__("Continue") +
									'<span class="material-symbols-outlined text-[16px] ml-1" aria-hidden="true">arrow_forward</span></a>'
								: "") +
							(it.can_remove_from_draft || it.can_propose_removal
								? '<div class="relative" data-kt-pln-row-overflow>' +
									'<button type="button" class="p-1 rounded-full hover:bg-surface-container-high text-on-surface-variant transition-colors flex items-center justify-center" data-kt-pln-action="row-overflow" data-testid="kt-pln-ui05-row-overflow" aria-label="' +
									__("More actions") +
									'" aria-haspopup="menu"><span class="material-symbols-outlined text-[20px]" aria-hidden="true">more_vert</span></button>' +
									'<div class="hidden absolute right-0 top-full mt-1 w-48 bg-surface-container-lowest border border-subtle rounded shadow-lg z-20" data-kt-pln-overflow-menu hidden role="menu">' +
									(it.can_remove_from_draft
										? '<button type="button" class="w-full text-left px-4 py-2 text-body-sm text-status-exhausted hover:bg-surface-container-low transition-colors flex items-center" data-kt-pln-action="remove-from-draft" data-plan-item="' +
											esc(it.plan_item) +
											'" data-testid="kt-pln-ui05-remove-from-draft" role="menuitem">' +
											'<span class="material-symbols-outlined text-[18px] mr-2" aria-hidden="true">delete</span>' +
											__("Remove from draft") +
											"</button>"
										: "") +
									(it.can_propose_removal
										? '<button type="button" class="w-full text-left px-4 py-2 text-body-sm text-status-exhausted hover:bg-surface-container-low transition-colors flex items-center" data-kt-pln-action="propose-removal" data-plan-item="' +
											esc(it.plan_item) +
											'" data-testid="kt-pln-ui05-propose-removal" role="menuitem">' +
											'<span class="material-symbols-outlined text-[18px] mr-2" aria-hidden="true">delete</span>' +
											__("Propose removal") +
											"</button>"
										: "") +
									"</div></div>"
								: "") +
							"</div></td></tr>"
						);
					})
					.join("");
				body +=
					'<tr class="h-auto" data-kt-pln-items-filler>' +
					'<td class="p-8 text-center text-on-surface-variant font-body-sm text-body-sm border-t-0" colspan="8">' +
					__("No further plan items added yet.") +
					"</td></tr>";
				$root.find("[data-kt-pln-items-body]").html(body);
			} else {
				$root.find("[data-kt-pln-items-body]").html(
					'<tr class="h-auto" data-kt-pln-items-filler>' +
						'<td class="p-8 text-center text-on-surface-variant font-body-sm text-body-sm border-t-0" colspan="8">' +
						__("No further plan items added yet.") +
						"</td></tr>"
				);
			}
		}

		function closeFinanceDrawer() {
			financeTargetItem = "";
			if (!$financeDrawer || !$financeDrawer.length) {
				return;
			}
			$financeDrawer.addClass("hidden").attr("hidden", "hidden");
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($financeDrawer);
			}
		}

		function fillFinanceVariant($variant, dto) {
			$variant.find("[data-kt-pln-07-code]").text(dto.plan_item_code || "");
			$variant.find("[data-kt-pln-07-title]").text(dto.requirement_title || "");
			$variant.find("[data-kt-pln-07-plan]").text(
				(dto.plan_title || "") + (dto.version_label ? " · " + dto.version_label : "")
			);
			$variant.find("[data-kt-pln-07-ou]").text(dto.owner_org_unit_label || dto.owner_org_unit || "");
			$variant.find("[data-kt-pln-07-status]").text(dto.plan_item_status_label || "");
			$variant.find("[data-kt-pln-07-demand]").text(dto.source_demand || "");
			$variant.find("[data-kt-pln-07-line]").text((dto.budget_line && dto.budget_line.name) || "—");
			$variant.find("[data-kt-pln-07-amount]").text(dto.amount_display || "");
			$variant.find("[data-kt-pln-07-available]").text(dto.available_before_display || "");
			$variant.find("[data-kt-pln-07-balance]").text(dto.available_after_display || "");
			$variant.find("[data-kt-pln-07-shortfall]").text(dto.shortfall_display || "");
			if (dto.shortfall_display) {
				$variant.find("[data-kt-pln-07a-notice]").text(
					__("This Plan Item cannot be confirmed because the Budget Line is short by {0}.", [
						dto.shortfall_display,
					])
				);
			}
			var $resolve = $variant.find('[data-testid="kt-pln-ui07a-resolve"]');
			if ($resolve.length && dto.budget_funding_route) {
				$resolve.attr("href", dto.budget_funding_route);
			}
			$variant.find('[data-kt-field="reason"]').val("");
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($variant);
			}
		}

		function openFinanceDrawer(itemId) {
			if (!$financeDrawer || !$financeDrawer.length || !itemId) {
				return;
			}
			return call("get_plan_finance_task", { plan_item: itemId })
				.then(function (dto) {
					if (!dto || dto.ok === false) {
						return;
					}
					financeTargetItem = itemId;
					var variant = dto.variant === "shortfall" ? "shortfall" : "sufficient";
					$financeDrawer.removeClass("hidden").removeAttr("hidden");
					$financeDrawer.find("[data-kt-pln-07-variant]").each(function () {
						var $v = $(this);
						var match = $v.attr("data-kt-pln-07-variant") === variant;
						if (match) {
							$v.removeClass("hidden").removeAttr("hidden");
							fillFinanceVariant($v, dto);
						} else {
							$v.addClass("hidden").attr("hidden", "hidden");
						}
					});
				})
				.catch(function () {
					closeFinanceDrawer();
				});
		}

		function maybeOpenFinanceFromQuery() {
			if (financeAutoOpened) {
				return;
			}
			var item = "";
			try {
				item = new URLSearchParams(window.location.search || "").get("finance_item") || "";
			} catch (e) {
				item = "";
			}
			if (!item) {
				return;
			}
			financeAutoOpened = true;
			var rows = (lastBuilderDto && lastBuilderDto.items) || [];
			var row = rows.filter(function (r) {
				return r.plan_item === item;
			})[0];
			if (!row || !row.can_open_finance_task) {
				return;
			}
			openFinanceDrawer(item);
		}

		function refresh() {
			return call("get_plan_builder", { plan: plan }).then(function (dto) {
				paintBuilder(dto);
				maybeOpenFinanceFromQuery();
				return dto;
			});
		}

		$root.off(".ktPlnBld");
		$root.on("click.ktPlnBld", '[data-kt-pln-action="add-demand"]', function (e) {
			e.preventDefault();
			openDialog("add");
		});
		$root.on(
			"click.ktPlnBld",
			'[data-kt-pln-action="elig-cancel"], [data-kt-pln-action="elig-close"]',
			function (e) {
				e.preventDefault();
				closeDialog();
			}
		);
		$root.on("change.ktPlnBld", "[data-kt-pln-elig-check]", function () {
			var id = $(this).attr("data-demand");
			if (!id) {
				return;
			}
			if ($(this).is(":checked")) {
				if (selectedIds.indexOf(id) === -1) {
					selectedIds.push(id);
				}
				$(this)
					.closest("[data-kt-pln-elig-row]")
					.addClass("bg-surface-container-low/50 is-selected");
			} else {
				selectedIds = selectedIds.filter(function (x) {
					return x !== id;
				});
				$(this)
					.closest("[data-kt-pln-elig-row]")
					.removeClass("bg-surface-container-low/50 is-selected");
			}
			paintEligSummary();
		});
		$root.on("change.ktPlnBld", "[data-kt-pln-formation-mode]", function () {
			paintEligSummary();
		});
		$root.on(
			"input.ktPlnBld change.ktPlnBld",
			"[data-kt-pln-elig-search], [data-kt-pln-elig-ou], [data-kt-pln-elig-category], [data-kt-pln-elig-remaining]",
			function () {
				loadElig();
			}
		);
		$root.on("click.ktPlnBld", '[data-kt-pln-action="elig-add"]', function (e) {
			e.preventDefault();
			if (!selectedIds.length) {
				frappe.show_alert({
					message: __("Select at least one Approved Demand."),
					indicator: "orange",
				});
				return;
			}
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($dialog);
			}

			var rows = selectedRows();
			var mode = "one_plan_item";
			var formationReason = "";
			if (rows.length >= 2) {
				mode = formationModeValue() === "combined" ? "combined" : "separate";
				if (mode === "combined") {
					if (!selectionCompatibleForCombine(rows)) {
						frappe.show_alert({
							message: __(
								"These Demands cannot be combined (different Organisation Unit or category)."
							),
							indicator: "orange",
						});
						return;
					}
					formationReason = (
						$dialog.find("[data-kt-pln-formation-reason]").val() || ""
					).trim();
					if (!formationReason) {
						if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
							window.ktFormErrors.show($dialog, {
								formation_reason: __("A reason for combining is required."),
							});
						}
						return;
					}
				}
			}
			call("add_demand_to_plan", {
				plan: plan,
				demand: selectedIds[0],
				demands: JSON.stringify(selectedIds),
				formation_mode: mode,
				formation_reason: formationReason,
				separation_reason: "",
			})
				.then(function (res) {
					if (!res || res.ok === false) {
						if (
							res &&
							res.errors &&
							window.ktFormErrors &&
							typeof window.ktFormErrors.show === "function"
						) {
							window.ktFormErrors.show($dialog, res.errors);
						}
						throw new Error(
							(res &&
								res.errors &&
								(res.errors.formation_reason ||
									res.errors.separation_reason ||
									res.errors.form)) ||
								"Add failed"
						);
					}
					closeDialog();
					frappe.show_alert({
						message: __("Demand added to plan"),
						indicator: "green",
					});
					if (!(res && res.editor_route)) {
						return refresh();
					}
					window.location.href = res.editor_route;
				})
				.catch(function (err) {
					frappe.show_alert({
						message: (err && err.message) || __("Could not add Demand"),
						indicator: "red",
					});
				});
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="continue-item"]', function (e) {
			e.preventDefault();
			var item = $(this).attr("data-plan-item");
			if (item) {
				window.location.href = "/app/procurement-plan-item-editor?plan_item=" + encodeURIComponent(item);
			}
		});
		function closeOverflowMenus() {
			$root.find("[data-kt-pln-overflow-menu]").addClass("hidden").attr("hidden", "hidden");
		}
		function openRemoveDialog(itemId) {
			var dto = lastBuilderDto || {};
			var row = (dto.items || []).filter(function (it) {
				return it.plan_item === itemId;
			})[0];
			if (!row) {
				return;
			}
			removeTargetItem = itemId;
			var variant = "draft";
			if (row.can_propose_removal) {
				variant = "active";
			} else if (row.removal_variant === "finance" || row.finance_effect_kind === "release") {
				variant = "finance";
			}
			$removeDialog.removeClass("hidden").removeAttr("hidden");
			$removeDialog.find("[data-kt-pln-05a-variant]").each(function () {
				var $v = $(this);
				var match = $v.attr("data-kt-pln-05a-variant") === variant;
				if (match) {
					$v.removeClass("hidden").removeAttr("hidden");
				} else {
					$v.addClass("hidden").attr("hidden", "hidden");
				}
			});
			var $visible = $removeDialog.find('[data-kt-pln-05a-variant="' + variant + '"]');
			$visible.find("[data-kt-pln-05a-item]").text(row.title || row.plan_item_code || "");
			$visible.find("[data-kt-pln-05a-ou]").text(row.owner_org_unit_label || row.owner_org_unit || "");
			$visible.find("[data-kt-pln-05a-value]").text(row.amount_display || "");
			$visible.find("[data-kt-pln-05a-sources]").text(row.sources_label || "");
			$visible.find("[data-kt-pln-05a-finance-copy]").text(
				row.finance_effect_copy ||
					__("No funding confirmed; no reservation to release")
			);
			$visible.find("[data-kt-pln-05a-release-amount]").text(row.amount_display || "");
			$visible.find('[data-kt-field="reason"]').val("");
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($visible);
			}
			$visible.find('[data-kt-field="reason"]').trigger("focus");
		}
		function closeRemoveDialog() {
			removeTargetItem = "";
			$removeDialog.addClass("hidden").attr("hidden", "hidden");
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($removeDialog);
			}
		}
		$root.on("click.ktPlnBld", '[data-kt-pln-action="row-overflow"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			var $menu = $(this).closest("[data-kt-pln-row-overflow]").find("[data-kt-pln-overflow-menu]");
			var opening = $menu.hasClass("hidden") || $menu.attr("hidden");
			closeOverflowMenus();
			if (opening) {
				$menu.removeClass("hidden").removeAttr("hidden");
			}
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="remove-from-draft"], [data-kt-pln-action="propose-removal"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			var item = $(this).attr("data-plan-item");
			closeOverflowMenus();
			if (item) {
				openRemoveDialog(item);
			}
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="keep-item"]', function (e) {
			e.preventDefault();
			closeRemoveDialog();
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="open-finance"]', function (e) {
			e.preventDefault();
			var item = $(this).attr("data-plan-item");
			if (item) {
				openFinanceDrawer(item);
			}
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="close-finance"]', function (e) {
			e.preventDefault();
			closeFinanceDrawer();
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="confirm-finance"]', function (e) {
			e.preventDefault();
			if (!financeTargetItem) {
				return;
			}
			var $visible = $financeDrawer.find("[data-kt-pln-07-variant]:not([hidden])").first();
			if ($visible.attr("data-kt-pln-07-variant") === "shortfall") {
				return;
			}
			var note = $visible.find('[data-kt-field="reason"]').val() || "";
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($visible);
			}
			call("confirm_plan_item_funding", { plan_item: financeTargetItem, note: note })
				.then(function (res) {
					if (!res || res.ok === false) {
						if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
							window.ktFormErrors.show($visible, (res && res.errors) || { form: __("Could not confirm") });
						}
						return;
					}
					closeFinanceDrawer();
					frappe.show_alert({ message: __("Funding confirmed"), indicator: "green" });
					return refresh();
				})
				.catch(function () {
					closeFinanceDrawer();
				});
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="return-finance"]', function (e) {
			e.preventDefault();
			if (!financeTargetItem) {
				return;
			}
			var $visible = $financeDrawer.find("[data-kt-pln-07-variant]:not([hidden])").first();
			var reason = ($visible.find('[data-kt-field="reason"]').val() || "").trim();
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($visible);
			}
			if (!reason) {
				if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
					window.ktFormErrors.show($visible, { reason: __("A return reason is required.") });
				}
				return;
			}
			call("return_plan_item_from_finance", { plan_item: financeTargetItem, reason: reason })
				.then(function (res) {
					if (!res || res.ok === false) {
						if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
							window.ktFormErrors.show($visible, (res && res.errors) || { reason: __("Could not return") });
						}
						return;
					}
					closeFinanceDrawer();
					frappe.show_alert({ message: __("Returned to planner"), indicator: "green" });
					return refresh();
				});
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="confirm-remove"]', function (e) {
			e.preventDefault();
			if (!removeTargetItem) {
				return;
			}
			var $visible = $removeDialog.find("[data-kt-pln-05a-variant]:not([hidden])").first();
			var reason = String($visible.find('[data-kt-field="reason"]').val() || "").trim();
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($visible);
			}
			if (!reason) {
				if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
					window.ktFormErrors.show($visible, {
						reason: __("A reason for removal is required."),
					});
				}
				return;
			}
			call("remove_plan_item_from_plan", {
				plan: plan,
				plan_item: removeTargetItem,
				reason: reason,
				concurrency_token: $root.attr("data-kt-pln-concurrency") || undefined,
			})
				.then(function (res) {
					if (!res || res.ok === false) {
						if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
							window.ktFormErrors.show(
								$visible,
								(res && res.errors) || { reason: __("Could not remove item") }
							);
						}
						return;
					}
					closeRemoveDialog();
					return refresh();
				})
				.catch(function (err) {
					if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
						window.ktFormErrors.show($visible, {
							reason: (err && err.message) || __("Could not remove item"),
						});
					}
				});
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="cancel-update"]', function (e) {
			e.preventDefault();
			call("cancel_plan_update", {
				plan: plan,
				concurrency_token: $root.attr("data-kt-pln-concurrency") || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					frappe.show_alert({
						message: (res && res.errors && res.errors.form) || __("Could not cancel update"),
						indicator: "red",
					});
					return;
				}
				return refresh();
			});
		});
		$(document).off("click.ktPlnBldOverflow").on("click.ktPlnBldOverflow", function () {
			closeOverflowMenus();
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="review-issue"]', function (e) {
			e.preventDefault();
			var $first = $root.find('[data-kt-pln-action="continue-item"]').first();
			var item = $first.attr("data-plan-item");
			if (item) {
				window.location.href = "/app/procurement-plan-item-editor?plan_item=" + encodeURIComponent(item);
			}
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="run-validation"]', function (e) {
			e.preventDefault();
			call("validate_plan", { plan: plan }).then(function () {
				return refresh();
			});
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="submit-for-review"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			var token = $root.attr("data-kt-pln-concurrency") || "";
			call("submit_plan_for_review", {
				plan: plan,
				concurrency_token: token || undefined,
			})
				.then(function (res) {
					if (!res || res.ok === false) {
						frappe.show_alert({
							message:
								(res && res.errors && res.errors.form) ||
								__("Could not submit for review"),
							indicator: "red",
						});
						return;
					}
					frappe.show_alert({
						message: __("Plan submitted for review"),
						indicator: "green",
					});
					frappe.set_route("procurement-plan-review", {
						plan: plan,
					});
					window.location.href =
						"/app/procurement-plan-review?plan=" + encodeURIComponent(plan);
				})
				.catch(function (err) {
					frappe.show_alert({
						message: (err && err.message) || __("Could not submit for review"),
						indicator: "red",
					});
				});
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="back-workspace"]', function (e) {
			e.preventDefault();
			frappe.set_route("planning-workspace");
		});

		return refresh().catch(function (err) {
			$root.attr("data-kt-pln-live", "0");
			$root.attr("data-kt-pln-error", "1");
			console.warn("Plan builder load failed", err);
		});
	}

	function bindPlanningItemEditor($root, opts) {
		if (!$root || !$root.length) {
			return;
		}
		opts = opts || {};
		var planItem = opts.plan_item || "";
		if (!planItem) {
			try {
				planItem =
					new URLSearchParams(window.location.search || "").get("plan_item") || "";
			} catch (e) {
				planItem = "";
			}
		}
		if (!planItem) {
			$root.attr("data-kt-pln-error", "1");
			return;
		}

		var plan = "";

		function clearErrors() {
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($root);
			}
		}

		function showErrors(errors) {
			if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
				window.ktFormErrors.show($root, errors || {});
			}
			if (errors && errors.form) {
				$root.find("[data-kt-pln-editor-issue-copy]").text(errors.form);
				setHidden($root.find("[data-kt-pln-editor-issue]"), false);
			}
		}

		function collectFields() {
			var fields = {};
			$root.find("[data-kt-pln-field]").each(function () {
				var name = $(this).attr("data-kt-pln-field");
				if (!name) {
					return;
				}
				if (
					name === "preference_reservation_scheme" ||
					name === "reservation_scope" ||
					name === "planned_reserved_value"
				) {
					return;
				}
				if ($(this).is(":checkbox")) {
					fields[name] = $(this).is(":checked") ? 1 : 0;
				} else if ($(this).is('[type="radio"]')) {
					if ($(this).is(":checked")) {
						fields[name] = $(this).val();
					}
				} else {
					fields[name] = $(this).val();
				}
			});
			return fields;
		}

		function paint(dto) {
			$root.attr("data-kt-pln-live", "1");
			$root.attr("data-kt-pln-plan-item", dto.plan_item || planItem);
			$root.attr("data-kt-pln-plan", dto.plan || plan || "");
			plan = dto.plan || plan;
			var title = dto.requirement_title || "";
			$root.find("[data-kt-pln-editor-title]").text(title);
			$root.find("[data-kt-pln-editor-ou]").text(dto.organisation_unit_label || "—");
			$root.find("[data-kt-pln-editor-amount]").text(dto.amount_display || "");
			$root
				.find("[data-kt-pln-editor-lifecycle]")
				.text(dto.lifecycle_label || dto.baseline_state || "Proposed");
			$root.find("[data-kt-pln-editor-version]").text(dto.version_label || "");
			var banner = cstr(dto.draft_banner || "");
			$root.find("[data-kt-pln-editor-draft-banner]").text(banner);
			setHidden($root.find("[data-kt-pln-editor-draft-banner]"), !banner);
			var f = dto.fields || {};
			var recommended = cstr(f.recommended_method || "Open tender") || "Open tender";
			$root.attr("data-kt-pln-recommended-method", recommended);
			$root.find("[data-kt-pln-editor-regime]").text(f.governing_regime || "PPADA");
			$root.find("[data-kt-pln-editor-recommended-method]").text(recommended);
			$root
				.find("[data-kt-pln-editor-method-basis]")
				.text(f.method_basis || "Preferred competitive method under the applicable regime.");
			Object.keys(f).forEach(function (k) {
				if (
					k === "preference_reservation_scheme" ||
					k === "reservation_scope" ||
					k === "eligible_groups" ||
					k === "planned_reserved_value"
				) {
					return;
				}
				var $el = $root.find('[data-kt-pln-field="' + k + '"]');
				if (!$el.length) {
					return;
				}
				if ($el.is('[type="radio"]')) {
					$el.filter('[value="' + f[k] + '"]').prop("checked", true);
				} else {
					var val = f[k] == null ? "" : f[k];
					if ($el.is("select") && val !== "") {
						var hasOpt = false;
						$el.find("option").each(function () {
							if (String($(this).attr("value")) === String(val)) {
								hasOpt = true;
								return false;
							}
						});
						if (!hasOpt) {
							$el.append(
								$("<option></option>").attr("value", val).text(String(val))
							);
						}
					}
					$el.val(val);
				}
			});
			$root
				.find('[data-kt-pln-field="requirement_description"]')
				.val(dto.requirement_description || f.requirement_description || "");
			var src = dto.approved_source || {};
			var financeLabel = dto.finance_status_label || "Not requested";
			$root.find("[data-kt-pln-source-demand]").text(src.title || src.demand_code || "—");
			$root
				.find("[data-kt-pln-source-need-count]")
				.text(String(src.need_item_count != null ? src.need_item_count : "—"));
			$root.find("[data-kt-pln-source-owner]").text(src.owner_org_unit_label || "—");
			$root
				.find("[data-kt-pln-source-approved-value]")
				.text(src.approved_value_display || src.reserved_value_display || dto.amount_display || "—");
			$root
				.find("[data-kt-pln-source-funding-line]")
				.text(
					src.funding_line_label &&
						!/^[a-z0-9]{8,}$/.test(String(src.funding_line_label).trim())
						? src.funding_line_label
						: "—"
				);
			$root.find("[data-kt-pln-source-finance], [data-kt-pln-source-finance-combined]").text(
				financeLabel
			);
			$root
				.find("[data-kt-pln-source-strategy]")
				.text(src.strategy_context || src.strategy_snapshot || "—");
			$root
				.find("[data-kt-pln-source-sidebar]")
				.attr("data-kt-pln-source-summary", dto.source_allocation_summary || "");
			if (dto.demand_route) {
				$root.find('[data-kt-pln-action="view-demand"]').attr("href", dto.demand_route);
			}
			var rows = dto.source_rows || [];
			var combined = !!dto.combined_sources || rows.length > 1;
			setHidden($root.find("[data-kt-pln-single-source]"), combined);
			setHidden($root.find("[data-kt-pln-combined-sources]"), !combined);
			if (combined) {
				var rowHtml = rows
					.map(function (r) {
						return (
							'<div class="flex flex-col gap-2 border border-border-subtle rounded-md p-3">' +
							'<div class="font-body-md text-on-surface">' +
							esc(r.title || r.demand_code || "—") +
							"</div>" +
							'<div class="font-body-sm text-on-surface-variant">' +
							esc(r.owner_org_unit_label || "—") +
							" · " +
							esc(r.approved_value_display || "—") +
							" · " +
							esc(String(r.need_item_count != null ? r.need_item_count : "—")) +
							" Need Items</div>" +
							'<div class="font-body-sm text-on-surface">' +
							esc(r.budget_line_label || "—") +
							"</div>" +
							(r.demand_route
								? '<a class="text-primary font-body-sm hover:underline" href="' +
									esc(r.demand_route) +
									'">View source breakdown</a>'
								: "") +
							"</div>"
						);
					})
					.join("");
				$root.find("[data-kt-pln-combined-rows]").html(rowHtml);
				$root.find("[data-kt-pln-combined-total]").text(dto.amount_display || "");
				$root.find("[data-kt-pln-formation-reason]").text(dto.formation_reason || "—");
			}
			var attention = cstr(dto.attention_message || "");
			$root.find("[data-kt-pln-editor-issue-copy]").text(
				attention ||
					"Confirm all milestone dates before requesting Finance confirmation."
			);
			clearErrors();
			if (dto.field_issues && Object.keys(dto.field_issues).length) {
				showErrors(dto.field_issues);
			}
			if (attention) {
				$root
					.find("[data-kt-pln-editor-issue-copy]")
					.text(attention)
					.removeClass("hidden")
					.removeAttr("hidden");
				setHidden($root.find("[data-kt-pln-editor-issue]"), false);
			} else if (!(dto.field_issues && dto.field_issues.form)) {
				setHidden($root.find("[data-kt-pln-editor-issue]"), true);
			}
			var showOverride =
				cstr(f.procurement_method || "") &&
				cstr(f.procurement_method) !== recommended;
			setHidden($root.find("[data-kt-pln-method-override]"), !showOverride);
			var lotted = cstr(f.lotting_decision || "") === "Multiple lots";
			setHidden($root.find("[data-kt-pln-lotting-details]"), !lotted);
			setHidden(
				$root.find(
					'[data-kt-pln-action="save-draft"], [data-kt-pln-action="request-finance"]'
				),
				!dto.can_edit
			);
			$root.find("[data-kt-pln-field]").prop("disabled", !dto.can_edit);
		}

		function cstr(v) {
			return String(v == null ? "" : v);
		}

		function save(opts) {
			opts = opts || {};
			var requestFinance = !!opts.requestFinance;
			clearErrors();
			return call("update_plan_item", {
				plan_item: planItem,
				fields: JSON.stringify(collectFields()),
				request_finance: requestFinance ? 1 : 0,
			})
				.then(function (result) {
					if (!result || result.ok === false) {
						showErrors((result && result.errors) || { form: __("Could not save") });
						return;
					}
					if (requestFinance && result.complete) {
						window.location.href =
							result.builder_route ||
							"/app/procurement-plan-builder?plan=" +
								encodeURIComponent($root.attr("data-kt-pln-plan") || "");
						return;
					}
					if (!requestFinance) {
						frappe.show_alert({ message: __("Plan Item saved"), indicator: "green" });
					}
					return call("get_plan_item_editor", { plan_item: planItem }).then(function (dto) {
						paint(dto);
						if (result.field_issues && Object.keys(result.field_issues).length) {
							showErrors(result.field_issues);
						}
						if (requestFinance && !result.complete) {
							var copy =
								result.attention_message ||
								"Confirm all milestone dates before requesting Finance confirmation.";
							$root.find("[data-kt-pln-editor-issue-copy]").text(copy);
							setHidden($root.find("[data-kt-pln-editor-issue]"), false);
						}
					});
				})
				.catch(function (err) {
					var mapped = {};
					if (
						window.ktFormErrors &&
						typeof window.ktFormErrors.fromFrappeError === "function"
					) {
						mapped = window.ktFormErrors.fromFrappeError(err) || {};
					}
					if (!Object.keys(mapped).length) {
						mapped = { form: __("Could not save") };
					}
					if (!mapped.form) {
						mapped.form = __("Could not save");
					}
					showErrors(mapped);
				});
		}

		$root.off(".ktPlnEd");
		$root.on("change.ktPlnEd", '[data-kt-pln-field="procurement_method"]', function () {
			var rec = $root.attr("data-kt-pln-recommended-method") || "Open tender";
			setHidden($root.find("[data-kt-pln-method-override]"), $(this).val() === rec);
		});
		$root.on("change.ktPlnEd", '[name="lotting_decision"]', function () {
			var lotted =
				$root.find('[name="lotting_decision"]:checked').val() === "Multiple lots";
			setHidden($root.find("[data-kt-pln-lotting-details]"), !lotted);
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="save-draft"]', function (e) {
			e.preventDefault();
			save({ requestFinance: false });
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="request-finance"]', function (e) {
			e.preventDefault();
			save({ requestFinance: true });
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="cancel"]', function (e) {
			e.preventDefault();
			call("get_plan_item_editor", { plan_item: planItem }).then(function (dto) {
				window.location.href = dto.builder_route || "/app/planning-workspace";
			});
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="view-source"]', function (e) {
			e.preventDefault();
			var summary =
				$root.find("[data-kt-pln-source-sidebar]").attr("data-kt-pln-source-summary") ||
				__("No source allocation summary.");
			frappe.show_alert({ message: summary, indicator: "blue" });
		});

		return call("get_plan_item_editor", { plan_item: planItem })
			.then(function (dto) {
				$root.attr("data-kt-pln-plan", dto.plan || "");
				paint(dto);
			})
			.catch(function (err) {
				$root.attr("data-kt-pln-error", "1");
				console.warn("Plan item editor load failed", err);
			});
	}

	function bindPlanningReview($root, opts) {
		opts = opts || {};
		var plan = String(opts.plan || $root.attr("data-kt-pln-plan") || "").trim();
		$root.attr("data-kt-pln-live", "0");
		if (!plan) {
			$root.find("h1").first().text(__("Plan not specified"));
			return;
		}
		$root.attr("data-kt-pln-plan", plan);
		var concurrency = "";
		var version = "";
		var railMode = "readonly";

		function paintReview(dto) {
			if (!dto || !dto.ok) {
				return;
			}
			$root.attr("data-kt-pln-live", "1");
			concurrency = dto.concurrency_token || "";
			version = dto.version || "";
			railMode = dto.rail_mode || "readonly";
			$root.find("[data-kt-pln-review-secondary]").text(dto.secondary_line || "");
			$root
				.find("[data-kt-pln-review-lifecycle]")
				.html(
					'<span class="material-symbols-outlined text-[14px] mr-1" aria-hidden="true">pending</span> ' +
						esc(dto.version_status || "In review")
				)
				.attr(
					"class",
					"inline-flex items-center px-3 py-1 rounded-full font-label-caps text-label-caps border " +
						statusPillClasses(lifecycleTone(dto.version_status || "In review"))
				);
			var val = dto.validation_projection || "Not run";
			var valTone = validationTone(val);
			$root
				.find("[data-kt-pln-review-validation-chip]")
				.html(
					'<span class="material-symbols-outlined text-[14px] mr-1" aria-hidden="true">' +
						validationIcon(val, valTone) +
						"</span> " +
						esc(val)
				)
				.attr(
					"class",
					"inline-flex items-center px-3 py-1 rounded-full font-label-caps text-label-caps border " +
						statusPillClasses(valTone)
				);
			$root.find("[data-kt-pln-review-items]").text(String(dto.item_count || 0));
			$root.find("[data-kt-pln-review-total]").text(dto.planned_total_display || "KES 0");
			$root
				.find("[data-kt-pln-review-finance-confirmed]")
				.text(dto.finance_confirmed_label || "0 of 0");
			$root
				.find("[data-kt-pln-review-validation]")
				.html(
					'<span class="material-symbols-outlined text-[14px] mr-1">check_circle</span> ' +
						esc(val)
				)
				.attr(
					"class",
					"inline-flex items-center px-2 py-1 rounded font-label-caps text-label-caps w-fit " +
						(valTone === "available"
							? "bg-status-available/10 text-status-available"
							: valTone === "reserved"
								? "bg-status-reserved/10 text-status-reserved"
								: "bg-surface-container text-on-surface-variant")
				);
			$root.find("[data-kt-pln-review-prepared-by]").text(dto.prepared_by || "—");
			var financeComplete = !!dto.finance_complete;
			$root
				.find("[data-kt-pln-review-finance-rail]")
				.html(
					financeComplete
						? '<span class="material-symbols-outlined text-[16px]">done</span> ' +
							esc(dto.finance_confirmation_label || __("Complete"))
						: esc(dto.finance_confirmation_label || __("Incomplete"))
				)
				.attr(
					"class",
					"font-body-sm text-body-sm font-medium flex items-center gap-1 " +
						(financeComplete ? "text-status-available" : "text-status-reserved")
				);
			$root
				.find("[data-kt-pln-review-validation-run]")
				.text(val)
				.attr(
					"class",
					"font-body-sm text-body-sm font-medium " + statusTextClass(valTone)
				);

			var itemsHtml = (dto.items || [])
				.map(function (it) {
					var iv = it.validation_projection || "Not run";
					var tone = validationTone(iv);
					var fin = it.finance_status_label || it.finance_status || "";
					var finLower = String(fin).toLowerCase();
					var finTone =
						finLower === "confirmed"
							? "text-status-available"
							: finLower === "stale" || finLower === "returned"
								? "text-status-exhausted"
								: "text-status-reserved";
					var finIcon =
						finLower === "confirmed"
							? "verified"
							: finLower === "stale"
								? "sync_problem"
								: "schedule";
					return (
						'<tr class="hover:bg-surface-container-low transition-colors group">' +
						'<td class="py-4 px-4">' +
						'<p class="font-body-sm text-body-sm text-on-surface font-medium whitespace-normal">' +
						esc(it.title || "") +
						"</p>" +
						'<p class="font-data-md text-[12px] text-on-surface-variant mt-1 whitespace-normal">' +
						esc(it.plan_item_code || "") +
						"</p></td>" +
						'<td class="py-4 px-4 font-body-sm text-body-sm text-on-surface whitespace-normal">' +
						esc(it.owner_org_unit_label || it.owner_org_unit || "") +
						"</td>" +
						'<td class="py-4 px-4 font-data-md text-data-md text-on-surface text-right whitespace-nowrap">' +
						esc(it.amount_display || "") +
						"</td>" +
						'<td class="py-4 px-4 font-body-sm text-body-sm text-on-surface">' +
						esc(it.method || "") +
						"</td>" +
						'<td class="py-4 px-4 font-body-sm text-body-sm text-on-surface whitespace-nowrap">' +
						esc(it.completion || "—") +
						"</td>" +
						'<td class="py-4 px-4"><span class="inline-flex items-center gap-1 ' +
						finTone +
						' font-body-sm text-body-sm"><span class="material-symbols-outlined text-[16px]">' +
						finIcon +
						"</span> " +
						esc(fin) +
						"</span></td>" +
						'<td class="py-4 px-4"><span class="inline-flex items-center px-2 py-0.5 rounded font-label-caps text-[10px] ' +
						(tone === "available"
							? "bg-status-available/10 text-status-available"
							: "bg-status-reserved/10 text-status-reserved") +
						'">' +
						esc(iv) +
						"</span></td>" +
						'<td class="py-4 px-4 text-right"><a class="font-body-sm text-body-sm text-primary hover:underline font-medium" href="' +
						esc(it.editor_route || "#") +
						'" data-testid="kt-pln-ui08-view">' +
						__("View") +
						"</a></td></tr>"
					);
				})
				.join("");
			$root.find("[data-kt-pln-review-items-body]").html(itemsHtml || "");

			var coverageRows = dto.statutory_coverage || [];
			setHidden($root.find('[data-testid="kt-pln-ui08-statutory"]'), !coverageRows.length);
			var statHtml = coverageRows
				.map(function (row) {
					var st = row.status || "";
					var stTone =
						st === "Compliant" || st === "Ready"
							? "available"
							: st === "Needs attention"
								? "reserved"
								: "neutral";
					return (
						'<tr class="hover:bg-surface-container-low transition-colors">' +
						'<td class="py-4 px-4 font-body-sm text-body-sm text-on-surface whitespace-normal">' +
						esc(row.obligation || "") +
						"</td>" +
						'<td class="py-4 px-4 font-data-md text-data-md text-on-surface text-right whitespace-nowrap">' +
						esc(row.required_treatment || "") +
						"</td>" +
						'<td class="py-4 px-4 font-data-md text-data-md text-on-surface text-right whitespace-nowrap">' +
						esc(row.planned_treatment || "") +
						"</td>" +
						'<td class="py-4 px-4"><span class="inline-flex items-center px-2 py-0.5 rounded font-label-caps text-[10px] ' +
						(stTone === "available"
							? "bg-status-available/10 text-status-available"
							: stTone === "reserved"
								? "bg-status-reserved/10 text-status-reserved"
								: "bg-surface-container text-on-surface-variant") +
						'">' +
						esc(st) +
						"</span></td></tr>"
					);
				})
				.join("");
			$root.find("[data-kt-pln-review-statutory-body]").html(statHtml);

			var $banner = $root.find("[data-kt-pln-review-issues-banner]");
			$root.find("[data-kt-pln-review-issues-copy]").text(dto.issues_message || "");
			if (dto.issues_ready && financeComplete) {
				$banner.attr(
					"class",
					"bg-status-available/10 border border-status-available/20 rounded-lg p-gutter-md flex items-start gap-3"
				);
			} else {
				$banner.attr(
					"class",
					"bg-status-reserved/10 border border-status-reserved/20 rounded-lg p-gutter-md flex items-start gap-3"
				);
			}

			var $primary = $root.find('[data-kt-pln-action="primary-decision"]');
			var $return = $root.find('[data-kt-pln-action="return-plan"]');
			var surface = dto.surface || "task";
			var isTask = surface === "task";
			var showPrimary =
				isTask &&
				((railMode === "approver" && !!dto.can_approve) ||
					(railMode === "reviewer" && !!dto.can_recommend));
			var showReturn = isTask && !!dto.can_return;
			var showActions = showPrimary || showReturn;
			setHidden($root.find("[data-kt-pln-review-actions]"), !showActions);
			setHidden($root.find("[data-kt-pln-review-comment-block]"), !showActions);
			setHidden($primary, !showPrimary);
			setHidden($return, !showReturn);
			// Never leave disabled primary CTAs on the rail (PLN-FR-083).
			$primary.prop("disabled", false).removeClass("opacity-50 cursor-not-allowed");
			$return.prop("disabled", false);
			if (showPrimary && railMode === "approver") {
				$root
					.find("[data-kt-pln-review-primary-label]")
					.text(dto.primary_cta_label || __("Approve plan"));
			} else if (showPrimary && railMode === "reviewer") {
				$root
					.find("[data-kt-pln-review-primary-label]")
					.text(dto.primary_cta_label || __("Recommend approval"));
			}
			$root.attr("data-kt-pln-surface", surface);
			$root.attr("data-kt-pln-task", isTask ? "1" : "0");

			var trailHtml = (dto.prior_decision_trail || [])
				.map(function (t) {
					return (
						'<div class="relative">' +
						'<div class="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-status-available border-2 border-surface-bright"></div>' +
						'<div class="flex flex-col">' +
						'<span class="font-body-sm text-body-sm text-on-surface font-medium">' +
						esc(t.actor || t.label || "") +
						(t.actor_role
							? ' <span class="text-on-surface-variant font-normal">(' +
								esc(t.actor_role) +
								")</span>"
							: "") +
						"</span>" +
						'<div class="flex items-center gap-2 mt-0.5">' +
						'<span class="font-label-caps text-[10px] bg-status-available/10 text-status-available px-1.5 py-0.5 rounded">' +
						esc(t.label || "") +
						"</span>" +
						'<span class="font-body-sm text-[12px] text-on-surface-variant">' +
						esc(t.date || "") +
						"</span></div></div></div>"
					);
				})
				.join("");
			$root.find("[data-kt-pln-review-trail]").html(trailHtml || "");
		}

		function refresh() {
			return new Promise(function (resolve, reject) {
				frappe.call({
					method: API + ".get_plan_review",
					args: { plan: plan },
					freeze: false,
					callback: function (r) {
						if (r && r.message) {
							resolve(r.message);
							return;
						}
						reject(r || { message: __("Review load failed") });
					},
					error: function (r) {
						reject(r || { message: __("Review load failed") });
					},
				});
			}).then(paintReview);
		}

		function showDenied(err) {
			$root.attr("data-kt-pln-error", "1");
			$root.attr("data-kt-pln-surface", "denied");
			setHidden($root.find("[data-kt-pln-review-actions]"), true);
			setHidden($root.find("[data-kt-pln-review-comment-block]"), true);
			var msg =
				(err && (err.message || err._server_messages || err.exc)) ||
				__("You are not permitted to open this Planning review.");
			if (typeof msg !== "string") {
				msg = __("You are not permitted to open this Planning review.");
			}
			$root.find("h1").first().text(__("Planning review unavailable"));
			$root
				.find("[data-kt-pln-review-secondary]")
				.text(String(msg).replace(/^PLN_[A-Z_]+:\s*/, "").slice(0, 280));
		}

		function commentValue() {
			return String($root.find('[data-kt-field="decision_comment"]').val() || "").trim();
		}

		$root.off(".ktPlnRev");
		$root.on("click.ktPlnRev", '[data-kt-pln-action="primary-decision"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($root);
			}
			if (railMode === "approver") {
				call("approve_plan_version", {
					version: version,
					concurrency_token: concurrency || undefined,
					reason: commentValue() || undefined,
				})
					.then(function (res) {
						if (!res || res.ok === false) {
							frappe.show_alert({
								message:
									(res && res.errors && res.errors.form) ||
									__("Approval failed"),
								indicator: "red",
							});
							return;
						}
						frappe.show_alert({
							message: __("Plan approved"),
							indicator: "green",
						});
						window.location.href = "/app/planning-workspace";
					})
					.catch(function (err) {
						frappe.show_alert({
							message: (err && err.message) || __("Approval failed"),
							indicator: "red",
						});
					});
				return;
			}
			call("record_plan_decision", {
				version: version,
				decision: "recommend",
				comment: commentValue() || undefined,
				concurrency_token: concurrency || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (
						res &&
						res.errors &&
						window.ktFormErrors &&
						typeof window.ktFormErrors.show === "function"
					) {
						window.ktFormErrors.show($root, res.errors);
					}
					return;
				}
				frappe.show_alert({
					message: __("Recommendation recorded"),
					indicator: "green",
				});
				return refresh();
			});
		});
		$root.on("click.ktPlnRev", '[data-kt-pln-action="return-plan"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($root);
			}
			call("record_plan_decision", {
				version: version,
				decision: "return",
				comment: commentValue(),
				concurrency_token: concurrency || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (
						res &&
						res.errors &&
						window.ktFormErrors &&
						typeof window.ktFormErrors.show === "function"
					) {
						window.ktFormErrors.show($root, res.errors);
					} else {
						frappe.show_alert({
							message:
								(res && res.errors && res.errors.decision_comment) ||
								__("Return failed"),
							indicator: "red",
						});
					}
					return;
				}
				frappe.show_alert({
					message: __("Plan returned"),
					indicator: "orange",
				});
				window.location.href =
					"/app/procurement-plan-builder?plan=" + encodeURIComponent(plan);
			});
		});

		return refresh().catch(function (err) {
			showDenied(err);
			console.warn("Plan review load failed", err);
		});
	}

	function bindPlanningApproved($root, opts) {
		opts = opts || {};
		if (!$root || !$root.length) {
			return;
		}
		var plan = String(opts.plan || $root.attr("data-kt-pln-plan") || "").trim();
		if (!plan) {
			try {
				plan = new URLSearchParams(window.location.search || "").get("plan") || "";
			} catch (e) {
				plan = "";
			}
		}
		$root.attr("data-kt-pln-live", "0");
		if (!plan) {
			$root.find("h1").first().text(__("Plan not specified"));
			return;
		}
		$root.attr("data-kt-pln-plan", plan);

		var dialogs = ensureBuilderDialogs($root);
		var $dialog = dialogs.$add;
		var $removeDialog = dialogs.$remove;
		var lastDto = null;
		var selectedIds = [];
		var lastEligRows = [];
		var removeTargetItem = "";
		var filterOu = "";
		var filterStatus = "";

		function findEligRow(demandId) {
			return (lastEligRows || []).find(function (r) {
				return r.demand === demandId;
			});
		}

		function selectedRows() {
			return (selectedIds || []).map(findEligRow).filter(Boolean);
		}

		function formationModeValue() {
			var $checked = $dialog.find("[data-kt-pln-formation-mode]:checked");
			return ($checked.val() || "separate").trim();
		}

		function selectionCompatibleForCombine(rows) {
			if (!rows || rows.length < 2) {
				return false;
			}
			var ou0 = String(rows[0].organisation_unit || "").trim();
			var cat0 = String(rows[0].category || "").trim();
			return rows.every(function (r) {
				return (
					String(r.organisation_unit || "").trim() === ou0 &&
					String(r.category || "").trim() === cat0
				);
			});
		}

		function paintEligSummary() {
			var rows = selectedRows();
			var n = rows.length;
			$dialog
				.find("[data-kt-pln-elig-count-label]")
				.text(
					n === 1
						? __("1 Approved Demand selected")
						: __("{0} Approved Demands selected", [String(n)])
				);
			var showFormation = n >= 2;
			setHidden($dialog.find("[data-kt-pln-formation-wrap]"), !showFormation);
			setHidden($dialog.find("[data-kt-pln-add-mode-footer]"), showFormation);
			var canCombine = selectionCompatibleForCombine(rows);
			var $combine = $dialog.find('[data-kt-pln-formation-mode][value="combined"]');
			$combine.prop("disabled", !canCombine);
			if (!canCombine && formationModeValue() === "combined") {
				$dialog.find('[data-kt-pln-formation-mode][value="separate"]').prop("checked", true);
			}
			var mode = formationModeValue();
			setHidden(
				$dialog.find("[data-kt-pln-formation-reason-wrap]"),
				!(showFormation && mode === "combined" && canCombine)
			);
			$dialog.find('[data-kt-pln-action="elig-add"]').prop("disabled", n === 0);
		}

		function paintElig(rows) {
			lastEligRows = rows || [];
			var body = lastEligRows
				.map(function (r) {
					var isSel = selectedIds.indexOf(r.demand) !== -1;
					var ou = r.organisation_unit_label || r.organisation_unit || "";
					var amt = Number(r.approved_amount || 0).toLocaleString(undefined, {
						maximumFractionDigits: 0,
					});
					return (
						'<tr class="hover:bg-surface-container-low transition-colors cursor-pointer' +
						(isSel ? " bg-surface-container-low/50 is-selected" : "") +
						'" data-kt-pln-elig-row data-demand="' +
						esc(r.demand) +
						'">' +
						'<td class="px-container-padding py-4"><input type="checkbox" class="w-4 h-4 text-primary border-outline rounded"' +
						(isSel ? " checked" : "") +
						' data-kt-pln-elig-check data-demand="' +
						esc(r.demand) +
						'" /></td>' +
						'<td class="px-container-padding py-4"><p class="font-body-md text-on-surface font-medium m-0">' +
						esc(r.title || "") +
						'</p><p class="font-body-sm text-on-surface-variant m-0">' +
						esc(r.demand_code || "") +
						"</p></td>" +
						'<td class="px-container-padding py-4 font-body-sm text-on-surface-variant">' +
						esc(ou) +
						"</td>" +
						'<td class="px-container-padding py-4 text-right font-data-md">' +
						esc((r.currency || "KES") + " " + amt) +
						"</td>" +
						'<td class="px-container-padding py-4 font-body-sm">' +
						esc(r.proposed_budget_line_display || "—") +
						"</td>" +
						'<td class="px-container-padding py-4 font-body-sm">' +
						esc(r.status_label || "Planning Ready") +
						"</td>" +
						'<td class="px-container-padding py-4 font-body-sm">' +
						esc(r.required_by || "—") +
						"</td></tr>"
					);
				})
				.join("");
			if (!body) {
				body =
					'<tr><td class="px-container-padding py-4" colspan="7"><span class="font-body-sm text-on-surface-variant italic">' +
					__("No eligible Demands for this filter.") +
					"</span></td></tr>";
			}
			$dialog.find("[data-kt-pln-elig-body]").html(body);
			paintEligSummary();
		}

		function loadElig() {
			return call("list_eligible_demands", {
				plan: plan,
				search: $dialog.find("[data-kt-pln-elig-search]").val() || "",
				organisation_unit: $dialog.find("[data-kt-pln-elig-ou]").val() || "",
				category: $dialog.find("[data-kt-pln-elig-category]").val() || "",
				remaining_only: $dialog.find("[data-kt-pln-elig-remaining]").is(":checked") ? 1 : 0,
			}).then(function (dto) {
				paintElig((dto && dto.demands) || []);
			});
		}

		function openAddDialog() {
			selectedIds = [];
			$dialog.find("[data-kt-pln-formation-reason]").val("");
			$dialog.find('[data-kt-pln-formation-mode][value="separate"]').prop("checked", true);
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($dialog);
			}
			setHidden($dialog, false);
			$dialog.removeClass("hidden").removeAttr("hidden");
			return loadElig();
		}

		function closeAddDialog() {
			setHidden($dialog, true);
			$dialog.addClass("hidden").attr("hidden", "hidden");
			selectedIds = [];
		}

		function pubDotClass(status) {
			if (status === "Published") {
				return "w-2.5 h-2.5 rounded-full bg-status-available";
			}
			if (status === "Failed") {
				return "w-2.5 h-2.5 rounded-full bg-status-exhausted";
			}
			return "w-2.5 h-2.5 rounded-full bg-outline";
		}

		function paintTable(dto) {
			var items = dto.items || [];
			var showActuals = !!dto.has_downstream_actuals;
			var colCount = showActuals ? 8 : 6;
			var body = items
				.filter(function (it) {
					if (filterOu && String(it.owner_org_unit || "") !== filterOu) {
						return false;
					}
					if (filterStatus && String(it.takeup_label || "") !== filterStatus) {
						return false;
					}
					return true;
				})
				.map(function (it) {
					var takeup =
						'<div class="flex flex-col gap-0.5"><span class="text-on-surface">' +
						esc(it.takeup_label || "Not taken up") +
						"</span>" +
						(it.tender_reference
							? '<span class="text-on-surface-variant text-[12px]">' +
								esc(it.tender_reference) +
								"</span>"
							: "") +
						"</div>";
					var overflow = "";
					if (dto.can_add_item && it.can_propose_removal && !it.tender_reference) {
						overflow =
							'<div class="relative inline-block ml-2" data-kt-pln-row-overflow>' +
							'<button type="button" class="text-on-surface-variant p-1 rounded hover:bg-surface-container" data-kt-pln-action="row-overflow" aria-label="' +
							__("More actions") +
							'"><span class="material-symbols-outlined text-[18px]">more_vert</span></button>' +
							'<div class="hidden absolute right-0 mt-1 z-20 bg-surface border border-subtle rounded shadow-sm min-w-[10rem]" data-kt-pln-overflow-menu hidden>' +
							'<button type="button" class="block w-full text-left px-3 py-2 font-label-caps text-label-caps text-on-surface hover:bg-surface-container-low" data-kt-pln-action="propose-removal" data-plan-item="' +
							esc(it.plan_item) +
							'">' +
							__("Propose removal") +
							"</button></div></div>";
					}
					return (
						'<tr class="hover:bg-surface-container-low transition-colors" data-kt-pln-ui09-row data-plan-item="' +
						esc(it.plan_item) +
						'" data-ou="' +
						esc(it.owner_org_unit || "") +
						'" data-takeup="' +
						esc(it.takeup_label || "") +
						'">' +
						'<td class="px-5 py-4 font-body-sm text-body-sm text-on-surface font-medium" style="white-space:normal">' +
						esc(it.title || it.plan_item_code) +
						"</td>" +
						'<td class="px-5 py-4 font-body-sm text-body-sm text-on-surface-variant" style="white-space:normal">' +
						esc(it.owner_org_unit_label || it.owner_org_unit || "") +
						"</td>" +
						'<td class="px-5 py-4 font-data-md text-data-md text-on-surface text-right">' +
						esc(it.amount_display || "") +
						"</td>" +
						'<td class="px-5 py-4 font-body-sm text-body-sm">' +
						takeup +
						"</td>" +
						'<td class="px-5 py-4 font-body-sm text-body-sm text-on-surface">' +
						esc(it.milestone_label || "") +
						"</td>" +
						(showActuals
							? '<td class="px-5 py-4 font-body-sm text-body-sm text-on-surface" style="white-space:normal">' +
								esc(it.progress_label || "") +
								"</td>" +
								'<td class="px-5 py-4 text-center font-body-sm">' +
								esc(it.variance_label || "") +
								"</td>"
							: "") +
						'<td class="px-5 py-4 text-right whitespace-nowrap">' +
						'<a class="inline-flex items-center gap-1 font-label-caps text-label-caps text-primary" href="' +
						esc(it.view_route || "#") +
						'">' +
						__("View") +
						' <span class="material-symbols-outlined text-[16px]">chevron_right</span></a>' +
						overflow +
						"</td></tr>"
					);
				})
				.join("");
			if (!body) {
				body =
					'<tr><td class="px-5 py-4 font-body-sm text-on-surface-variant" colspan="' +
					colCount +
					'">' +
					__("No Plan Items match these filters.") +
					"</td></tr>";
			}
			$root.find("[data-kt-pln-ui09-items-body]").html(body);
		}

		function paintApproved(dto) {
			if (!dto || !dto.ok) {
				return;
			}
			lastDto = dto;
			$root.attr("data-kt-pln-live", "1");
			$root.attr("data-kt-pln-concurrency", dto.concurrency_token || "");
			$root.find("[data-kt-pln-ui09-title]").text(dto.title || dto.plan_code || "");
			$root.find("[data-kt-pln-ui09-version]").text(dto.version_label || "Approved Version 1");
			$root.find("[data-kt-pln-ui09-total]").text(dto.planned_total_display || "KES 0.00");
			$root.find("[data-kt-pln-ui09-items]").text(String(dto.item_count || 0));
			$root.find("[data-kt-pln-ui09-takeup]").text(dto.takeup_label || "0 of 0");
			setHidden($root.find("[data-kt-pln-ui09-on-schedule-kpi]"), !dto.has_downstream_actuals);
			setHidden($root.find("[data-kt-pln-ui09-progress-col]"), !dto.has_downstream_actuals);
			setHidden($root.find("[data-kt-pln-ui09-variance-col]"), !dto.has_downstream_actuals);
			if (dto.has_downstream_actuals) {
				$root.find("[data-kt-pln-ui09-on-schedule]").text(dto.on_schedule_label || "");
			}
			var pub = dto.publication || {};
			var pubStatus = pub.status || dto.publication_status_label || "Not published";
			$root
				.find("[data-kt-pln-ui09-pub-kpi]")
				.html(
					'<span class="' +
						pubDotClass(pubStatus) +
						'"></span> ' +
						esc(pubStatus)
				);
			$root.find("[data-kt-pln-ui09-pub-dest]").text(pub.destination || "Tender Portal");
			$root.find("[data-kt-pln-ui09-pub-status]").text(pubStatus);
			$root
				.find("[data-kt-pln-ui09-pub-dot]")
				.attr("class", pubDotClass(pubStatus).replace("w-2.5 h-2.5", "w-2 h-2"));
			if (pub.published_at_display) {
				$root.find("[data-kt-pln-ui09-pub-date]").text(pub.published_at_display);
				setHidden($root.find("[data-kt-pln-ui09-pub-date-wrap]"), false);
				setHidden($root.find("[data-kt-pln-ui09-pub-date-sep]"), false);
			} else {
				$root.find("[data-kt-pln-ui09-pub-date]").text("—");
			}
			setHidden($root.find("[data-kt-pln-ui09-pub-link]"), !pub.published);
			setHidden($root.find('[data-testid="kt-pln-ui09-add-item"]'), !dto.can_add_item);
			setHidden($root.find('[data-testid="kt-pln-ui09-export"]'), !dto.can_export);
			$root
				.find('[data-testid="kt-pln-ui09-add-item"]')
				.attr("style", dto.can_add_item ? "" : "display:none !important");
			$root
				.find('[data-testid="kt-pln-ui09-export"]')
				.attr("style", dto.can_export ? "" : "display:none !important");
			var $notice = $root.find('[data-testid="kt-pln-ui09-successor-notice"]');
			if (dto.has_successor) {
				$root
					.find("[data-kt-pln-ui09-successor-copy]")
					.html(esc(dto.successor_copy || dto.successor_label || ""));
				setHidden($notice, false);
				$notice.removeClass("hidden").removeAttr("hidden");
				$notice.css("display", "");
			} else {
				setHidden($notice, true);
				$notice.addClass("hidden").attr("hidden", "hidden");
				$notice.css("display", "none");
			}
			$root.find("[data-kt-pln-ui09-as-at]").html(
				'<span class="material-symbols-outlined text-[16px]" data-icon="calendar_today">calendar_today</span> ' +
					esc(dto.as_at_display || "")
			);
			var $period = $root.find('[data-kt-pln-ui09-filter="period"]');
			if (dto.reporting_period_label) {
				$period.html(
					'<option value="' +
						esc(dto.reporting_period_label) +
						'">' +
						esc(dto.reporting_period_label) +
						"</option>"
				);
			}
			var $ou = $root.find('[data-kt-pln-ui09-filter="ou"]');
			var ouHtml = '<option value="">' + __("All permitted units") + "</option>";
			(dto.ou_options || []).forEach(function (opt) {
				ouHtml +=
					'<option value="' +
					esc(opt.id) +
					'">' +
					esc(opt.label || opt.id) +
					"</option>";
			});
			$ou.html(ouHtml);
			if (filterOu) {
				$ou.val(filterOu);
			}
			paintTable(dto);
		}

		function openRemoveDialog(itemId) {
			var dto = lastDto || {};
			var row = (dto.items || []).filter(function (it) {
				return it.plan_item === itemId;
			})[0];
			if (!row) {
				return;
			}
			removeTargetItem = itemId;
			$removeDialog.removeClass("hidden").removeAttr("hidden");
			$removeDialog.find("[data-kt-pln-05a-variant]").each(function () {
				var match = $(this).attr("data-kt-pln-05a-variant") === "active";
				if (match) {
					$(this).removeClass("hidden").removeAttr("hidden");
				} else {
					$(this).addClass("hidden").attr("hidden", "hidden");
				}
			});
			var $visible = $removeDialog.find('[data-kt-pln-05a-variant="active"]');
			$visible.find("[data-kt-pln-05a-item]").text(row.title || row.plan_item_code || "");
			$visible.find("[data-kt-pln-05a-ou]").text(row.owner_org_unit_label || "");
			$visible.find("[data-kt-pln-05a-value]").text(row.amount_display || "");
			$visible.find("[data-kt-pln-05a-sources]").text(row.sources_label || "");
			$visible
				.find("[data-kt-pln-05a-finance-copy]")
				.text(row.finance_effect_copy || "");
			$visible.find('[data-kt-field="reason"]').val("");
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($visible);
			}
		}

		function closeRemoveDialog() {
			removeTargetItem = "";
			$removeDialog.addClass("hidden").attr("hidden", "hidden");
		}

		function refresh() {
			return call("get_plan_implementation", { plan: plan }).then(function (dto) {
				if (!dto || dto.ok === false) {
					throw dto || { message: __("Could not load approved plan") };
				}
				paintApproved(dto);
				return dto;
			});
		}

		function showDenied(err) {
			$root.attr("data-kt-pln-error", "1");
			var msg =
				(err && (err.message || err._server_messages)) ||
				__("This Approved Plan is not available.");
			$root.find("h1").first().text(__("Approved plan unavailable"));
			$root.find("[data-kt-pln-ui09-secondary]").text(String(msg).slice(0, 280));
		}

		$root.off(".ktPlnUi09");
		$root.on("click.ktPlnUi09", '[data-kt-pln-action="add-demand"]', function (e) {
			e.preventDefault();
			openAddDialog();
		});
		$root.on(
			"click.ktPlnUi09",
			'[data-kt-pln-action="elig-cancel"], [data-kt-pln-action="elig-close"]',
			function (e) {
				e.preventDefault();
				closeAddDialog();
			}
		);
		$root.on("change.ktPlnUi09", "[data-kt-pln-elig-check]", function () {
			var id = $(this).attr("data-demand");
			if (!id) {
				return;
			}
			if ($(this).is(":checked")) {
				if (selectedIds.indexOf(id) === -1) {
					selectedIds.push(id);
				}
			} else {
				selectedIds = selectedIds.filter(function (x) {
					return x !== id;
				});
			}
			paintEligSummary();
		});
		$root.on(
			"input.ktPlnUi09 change.ktPlnUi09",
			"[data-kt-pln-elig-search], [data-kt-pln-elig-ou], [data-kt-pln-elig-category], [data-kt-pln-elig-remaining]",
			function () {
				loadElig();
			}
		);
		$root.on("click.ktPlnUi09", '[data-kt-pln-action="elig-add"]', function (e) {
			e.preventDefault();
			if (!selectedIds.length) {
				return;
			}
			var rows = selectedRows();
			var mode = "one_plan_item";
			var formationReason = "";
			if (rows.length >= 2) {
				mode = formationModeValue() === "combined" ? "combined" : "separate";
				if (mode === "combined") {
					formationReason = ($dialog.find("[data-kt-pln-formation-reason]").val() || "").trim();
					if (!formationReason) {
						if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
							window.ktFormErrors.show($dialog, {
								formation_reason: __("A reason for combining is required."),
							});
						}
						return;
					}
				}
			}
			call("add_demand_to_plan", {
				plan: plan,
				demand: selectedIds[0],
				demands: JSON.stringify(selectedIds),
				formation_mode: mode,
				formation_reason: formationReason,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (res && res.errors && window.ktFormErrors) {
						window.ktFormErrors.show($dialog, res.errors);
					}
					return;
				}
				closeAddDialog();
				frappe.show_alert({ message: __("Demand added to plan"), indicator: "green" });
				if (res.editor_route) {
					window.location.href = res.editor_route;
					return;
				}
				if (res.builder_route) {
					window.location.href = res.builder_route;
					return;
				}
				return refresh();
			});
		});
		$root.on("click.ktPlnUi09", '[data-kt-pln-action="export-approved"]', function (e) {
			e.preventDefault();
			call("publish_approved_plan", { plan: plan }).then(function (res) {
				if (!res || res.ok === false) {
					frappe.show_alert({
						message:
							(res && res.errors && res.errors.form) || __("Export failed"),
						indicator: "red",
					});
					return refresh();
				}
				frappe.show_alert({ message: __("Approved plan exported"), indicator: "green" });
				return refresh();
			});
		});
		$root.on(
			"click.ktPlnUi09",
			'[data-kt-pln-action="continue-update"], [data-kt-pln-action="view-changes"]',
			function (e) {
				e.preventDefault();
				var route = (lastDto && lastDto.update_route) || "/app/procurement-plan-update?plan=" + encodeURIComponent(plan);
				window.location.href = route;
			}
		);
		$root.on("click.ktPlnUi09", '[data-kt-pln-action="row-overflow"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			var $menu = $(this).closest("[data-kt-pln-row-overflow]").find("[data-kt-pln-overflow-menu]");
			var opening = $menu.hasClass("hidden") || $menu.attr("hidden");
			$root.find("[data-kt-pln-overflow-menu]").addClass("hidden").attr("hidden", "hidden");
			if (opening) {
				$menu.removeClass("hidden").removeAttr("hidden");
			}
		});
		$root.on("click.ktPlnUi09", '[data-kt-pln-action="propose-removal"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			var item = $(this).attr("data-plan-item");
			$root.find("[data-kt-pln-overflow-menu]").addClass("hidden").attr("hidden", "hidden");
			if (item) {
				openRemoveDialog(item);
			}
		});
		$root.on("click.ktPlnUi09", '[data-kt-pln-action="keep-item"]', function (e) {
			e.preventDefault();
			closeRemoveDialog();
		});
		$root.on("click.ktPlnUi09", '[data-kt-pln-action="confirm-remove"]', function (e) {
			e.preventDefault();
			if (!removeTargetItem) {
				return;
			}
			var $visible = $removeDialog.find("[data-kt-pln-05a-variant]:not([hidden])").first();
			var reason = String($visible.find('[data-kt-field="reason"]').val() || "").trim();
			if (!reason) {
				if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
					window.ktFormErrors.show($visible, {
						reason: __("A reason for removal is required."),
					});
				}
				return;
			}
			call("remove_plan_item_from_plan", {
				plan: plan,
				plan_item: removeTargetItem,
				reason: reason,
				concurrency_token: $root.attr("data-kt-pln-concurrency") || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
						window.ktFormErrors.show($visible, (res && res.errors) || { form: __("Could not propose removal") });
					}
					return;
				}
				closeRemoveDialog();
				frappe.show_alert({ message: __("Removal proposed"), indicator: "green" });
				window.location.href =
					(lastDto && lastDto.update_route) ||
					"/app/procurement-plan-update?plan=" + encodeURIComponent(plan);
			});
		});
		$root.on("change.ktPlnUi09", '[data-kt-pln-ui09-filter="ou"]', function () {
			filterOu = $(this).val() || "";
			if (lastDto) {
				paintTable(lastDto);
			}
		});
		$root.on("change.ktPlnUi09", '[data-kt-pln-ui09-filter="status"]', function () {
			filterStatus = $(this).val() || "";
			if (lastDto) {
				paintTable(lastDto);
			}
		});

		return refresh().catch(function (err) {
			showDenied(err);
			console.warn("Approved plan load failed", err);
		});
	}

	function bindPlanningUpdate($root, opts) {
		if (!$root || !$root.length) {
			return;
		}
		opts = opts || {};
		$root.attr("data-kt-pln-live", "0");
		var plan = opts.plan || "";
		if (!plan) {
			try {
				plan = new URLSearchParams(window.location.search || "").get("plan") || "";
			} catch (e) {
				plan = "";
			}
		}
		if (!plan) {
			$root.attr("data-kt-pln-error", "1");
			$root.find("h1").first().text(__("Plan not specified"));
			return;
		}

		var $removeDialog = ensureBuilderDialogs($root).$remove;
		var lastDto = null;
		var removeTargetItem = "";
		var unchangedOpen = false;

		function hideCta($el, hide) {
			setHidden($el, hide);
			$el.attr("style", hide ? "display:none !important" : "");
		}

		function financeTone(label) {
			var s = String(label || "").toLowerCase();
			if (s === "confirmed") {
				return "text-status-available";
			}
			if (s === "awaiting confirmation" || s === "stale" || s === "returned") {
				return "text-status-reserved";
			}
			return "text-on-surface-variant";
		}

		function validationToneClass(label) {
			var s = String(label || "").toLowerCase();
			if (s === "ready") {
				return "text-status-available";
			}
			if (s === "blocked") {
				return "text-status-exhausted";
			}
			return "text-status-reserved";
		}

		function overflowHtml(it) {
			if (it.can_remove_from_draft) {
				return (
					'<div class="relative inline-block ml-2" data-kt-pln-row-overflow>' +
					'<button type="button" class="text-on-surface-variant p-1 rounded hover:bg-surface-container" data-kt-pln-action="row-overflow" aria-label="' +
					__("More actions") +
					'"><span class="material-symbols-outlined text-[18px]">more_vert</span></button>' +
					'<div class="hidden absolute right-0 mt-1 z-20 bg-surface border border-subtle rounded shadow-sm min-w-[10rem]" data-kt-pln-overflow-menu hidden>' +
					'<button type="button" class="block w-full text-left px-3 py-2 font-label-caps text-label-caps text-status-exhausted hover:bg-surface-container-low" data-kt-pln-action="remove-from-update" data-plan-item="' +
					esc(it.plan_item) +
					'">' +
					__("Remove from update") +
					"</button></div></div>"
				);
			}
			if (it.can_propose_removal) {
				return (
					'<div class="relative inline-block ml-2" data-kt-pln-row-overflow>' +
					'<button type="button" class="text-on-surface-variant p-1 rounded hover:bg-surface-container" data-kt-pln-action="row-overflow" aria-label="' +
					__("More actions") +
					'"><span class="material-symbols-outlined text-[18px]">more_vert</span></button>' +
					'<div class="hidden absolute right-0 mt-1 z-20 bg-surface border border-subtle rounded shadow-sm min-w-[10rem]" data-kt-pln-overflow-menu hidden>' +
					'<button type="button" class="block w-full text-left px-3 py-2 font-label-caps text-label-caps text-on-surface hover:bg-surface-container-low" data-kt-pln-action="propose-removal" data-plan-item="' +
					esc(it.plan_item) +
					'">' +
					__("Propose removal") +
					"</button></div></div>"
				);
			}
			return "";
		}

		function paintChanged(dto) {
			var rows = dto.changed_items || [];
			var body = rows
				.map(function (it) {
					var chip =
						it.change_label === "Proposed removal"
							? "bg-status-reserved/10 text-status-reserved"
							: "bg-status-available/10 text-status-available";
					return (
						'<tr class="hover:bg-surface-container-low/50 transition-colors border-l-4 border-l-status-available" data-kt-pln-ui10-row data-plan-item="' +
						esc(it.plan_item) +
						'">' +
						'<td class="py-3 px-4"><span class="px-2 py-0.5 rounded-sm ' +
						chip +
						' font-label-caps text-label-caps">' +
						esc(it.change_label || "Added") +
						"</span></td>" +
						'<td class="py-3 px-4 text-on-background font-medium" style="white-space:normal">' +
						esc(it.title || it.plan_item_code) +
						"</td>" +
						'<td class="py-3 px-4 text-on-surface-variant" style="white-space:normal">' +
						esc(it.owner_org_unit_label || "") +
						"</td>" +
						'<td class="py-3 px-4 text-right font-data-md text-data-md text-on-background">' +
						esc(it.amount_display || "") +
						"</td>" +
						'<td class="py-3 px-4"><span class="' +
						financeTone(it.finance_status_label) +
						' flex items-center gap-1.5 text-body-sm font-body-sm font-medium">' +
						esc(it.finance_status_label || "Not requested") +
						"</span></td>" +
						'<td class="py-3 px-4"><span class="' +
						validationToneClass(it.validation_projection) +
						' flex items-center gap-1.5 text-body-sm font-body-sm font-medium">' +
						esc(it.validation_projection || "Not run") +
						"</span></td>" +
						'<td class="py-3 px-4 text-right whitespace-nowrap">' +
						'<a class="text-primary font-medium hover:underline text-body-sm font-body-sm" href="' +
						esc(it.view_route || "#") +
						'">' +
						__("View") +
						"</a>" +
						overflowHtml(it) +
						"</td></tr>"
					);
				})
				.join("");
			$root.find("[data-kt-pln-ui10-changes-body]").html(body || "");
		}

		function paintUnchanged(dto) {
			var rows = dto.unchanged_items || [];
			var body = rows
				.map(function (it) {
					return (
						'<tr data-kt-pln-ui10-unchanged-row data-plan-item="' +
						esc(it.plan_item) +
						'">' +
						'<td class="py-3 px-4 text-on-background font-medium" style="white-space:normal">' +
						esc(it.title || it.plan_item_code) +
						"</td>" +
						'<td class="py-3 px-4 text-on-surface-variant" style="white-space:normal">' +
						esc(it.owner_org_unit_label || "") +
						"</td>" +
						'<td class="py-3 px-4 text-right font-data-md text-data-md">' +
						esc(it.amount_display || "") +
						"</td>" +
						'<td class="py-3 px-4 text-right">' +
						overflowHtml(it) +
						"</td></tr>"
					);
				})
				.join("");
			$root.find("[data-kt-pln-ui10-unchanged-body]").html(body);
			$root
				.find("[data-testid='kt-pln-ui10-view-unchanged']")
				.text(
					dto.unchanged_count === 1
						? __("View unchanged item")
						: __("View unchanged items")
				);
		}

		function rowByItem(item) {
			var list = []
				.concat((lastDto && lastDto.changed_items) || [])
				.concat((lastDto && lastDto.unchanged_items) || []);
			return list.filter(function (it) {
				return it.plan_item === item;
			})[0];
		}

		function openRemoveDialog(item) {
			var row = rowByItem(item);
			if (!row) {
				return;
			}
			removeTargetItem = item;
			var variant = row.can_remove_from_draft ? "draft" : "active";
			setHidden($removeDialog, false);
			$removeDialog.prop("hidden", false);
			$removeDialog.find("[data-kt-pln-05a-variant]").each(function () {
				if ($(this).attr("data-kt-pln-05a-variant") === variant) {
					$(this).removeClass("hidden").removeAttr("hidden");
				} else {
					$(this).addClass("hidden").attr("hidden", "hidden");
				}
			});
			var $visible = $removeDialog.find('[data-kt-pln-05a-variant="' + variant + '"]');
			$visible.find("[data-kt-pln-05a-item]").text(row.title || row.plan_item_code || "");
			$visible.find("[data-kt-pln-05a-ou]").text(row.owner_org_unit_label || "");
			$visible.find("[data-kt-pln-05a-value]").text(row.amount_display || "");
			$visible.find("[data-kt-pln-05a-sources]").text(row.sources_label || "");
			$visible.find("[data-kt-pln-05a-finance-copy]").text(row.finance_effect_copy || "");
			$visible.find('[data-kt-field="reason"]').val("");
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($visible);
			}
		}

		function closeRemoveDialog() {
			removeTargetItem = "";
			$removeDialog.addClass("hidden").attr("hidden", "hidden");
		}

		function paintUpdate(dto) {
			lastDto = dto;
			$root.attr("data-kt-pln-live", "1");
			$root.attr("data-kt-pln-concurrency", dto.concurrency_token || "");
			$root.find("[data-kt-pln-ui10-subtitle]").text(dto.title || dto.plan_code || "");
			$root.find("[data-kt-pln-ui10-status-chip]").text(dto.version_status || "Draft");
			var $attn = $root.find("[data-kt-pln-ui10-attention-chip]");
			if (dto.attention_chip) {
				$attn.text(dto.attention_chip);
				setHidden($attn, false);
			} else {
				setHidden($attn, true);
			}
			$root.find("[data-kt-pln-ui10-banner-copy]").text(dto.banner_copy || "");
			$root.find("[data-kt-pln-ui10-approved-label]").text(dto.approved_version_label || "");
			$root.find("[data-kt-pln-ui10-approved-total]").text(dto.approved_total_display || "");
			$root.find("[data-kt-pln-ui10-draft-label]").text(dto.version_label || "");
			$root.find("[data-kt-pln-ui10-draft-total]").text(dto.draft_total_display || "");
			$root.find("[data-kt-pln-ui10-change-copy]").text(dto.change_display || "");
			$root
				.find("[data-kt-pln-ui10-changed-count]")
				.text(String(dto.changed_count || 0) + " Changed");
			$root
				.find("[data-kt-pln-ui10-unchanged-count]")
				.text(String(dto.unchanged_count || 0) + " Unchanged");
			$root.find("[data-kt-pln-ui10-change-type]").text(dto.change_type_label || "");
			$root.find("[data-kt-field='update_reason']").val(dto.update_reason || "");
			$root
				.find("[data-kt-pln-ui10-initiated]")
				.text(__("Initiated by") + " " + (dto.initiated_by || ""));
			$root
				.find("[data-kt-pln-ui10-created]")
				.text(dto.created_display ? __("Created") + " " + dto.created_display : "");
			$root.find("[data-kt-pln-ui10-unchanged-copy]").text(dto.unchanged_copy || "");
			paintChanged(dto);
			paintUnchanged(dto);
			setHidden($root.find('[data-testid="kt-pln-ui10-unchanged"]'), !dto.unchanged_count);
			setHidden(
				$root.find('[data-testid="kt-pln-ui10-unchanged-table"]'),
				!unchangedOpen || !dto.unchanged_count
			);
			var $issue = $root.find('[data-testid="kt-pln-ui10-issue"]');
			if (dto.issue_message && !dto.no_changes_remain) {
				$root.find("[data-kt-pln-ui10-issue-copy]").text(dto.issue_message);
				setHidden($issue, false);
			} else {
				setHidden($issue, true);
			}
			setHidden($root.find('[data-testid="kt-pln-ui10-no-changes"]'), !dto.no_changes_remain);
			setHidden($root.find('[data-testid="kt-pln-ui10-changes"]'), !!dto.no_changes_remain);
			hideCta($root.find('[data-testid="kt-pln-ui10-validate"]'), !dto.can_validate);
			hideCta($root.find('[data-testid="kt-pln-ui10-save"]'), !dto.can_save || dto.no_changes_remain);
			hideCta($root.find('[data-testid="kt-pln-ui10-cancel"]'), !dto.can_cancel);
			var $submit = $root.find('[data-testid="kt-pln-ui10-submit"]');
			hideCta($submit, !dto.can_save || !!dto.no_changes_remain);
			$submit.prop("disabled", !dto.can_submit);
			if (dto.can_submit) {
				$submit
					.removeClass(
						"bg-on-surface-variant/20 text-on-surface-variant/50 cursor-not-allowed"
					)
					.addClass("bg-primary text-on-primary cursor-pointer");
			} else {
				$submit
					.addClass(
						"bg-on-surface-variant/20 text-on-surface-variant/50 cursor-not-allowed"
					)
					.removeClass("bg-primary text-on-primary cursor-pointer");
			}
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($root);
			}
		}

		function refresh() {
			return call("get_plan_update", { plan: plan }).then(function (dto) {
				if (!dto || dto.ok === false) {
					throw dto || { message: __("Could not load plan update") };
				}
				paintUpdate(dto);
				return dto;
			});
		}

		$root.off(".ktPlnUi10");
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="validate"]', function (e) {
			e.preventDefault();
			call("validate_plan", { plan: plan }).then(function () {
				return refresh();
			});
		});
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="save-update"]', function (e) {
			e.preventDefault();
			var reason = String($root.find("[data-kt-field='update_reason']").val() || "");
			call("save_plan_update", {
				plan: plan,
				update_reason: reason,
				concurrency_token: $root.attr("data-kt-pln-concurrency") || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (res && res.errors && window.ktFormErrors) {
						window.ktFormErrors.show($root, res.errors);
					}
					return;
				}
				frappe.show_alert({ message: __("Draft saved"), indicator: "green" });
				return refresh();
			});
		});
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="submit-update"]', function (e) {
			e.preventDefault();
			call("submit_plan_for_review", {
				plan: plan,
				concurrency_token: $root.attr("data-kt-pln-concurrency") || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (res && res.errors && window.ktFormErrors) {
						window.ktFormErrors.show($root, res.errors);
					} else {
						frappe.show_alert({
							message: (res && res.errors && res.errors.form) || __("Submit failed"),
							indicator: "red",
						});
					}
					return;
				}
				window.location.href =
					(lastDto && lastDto.review_route) ||
					"/app/procurement-plan-review?plan=" + encodeURIComponent(plan);
			});
		});
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="cancel-update"]', function (e) {
			e.preventDefault();
			call("cancel_plan_update", {
				plan: plan,
				concurrency_token: $root.attr("data-kt-pln-concurrency") || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (res && res.errors && window.ktFormErrors) {
						window.ktFormErrors.show($root, res.errors);
					} else {
						frappe.show_alert({
							message:
								(res && res.errors && res.errors.form) ||
								__("This update still has changes."),
							indicator: "orange",
						});
					}
					return;
				}
				window.location.href =
					(lastDto && lastDto.approved_route) ||
					"/app/procurement-plan-approved?plan=" + encodeURIComponent(plan);
			});
		});
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="toggle-unchanged"]', function (e) {
			e.preventDefault();
			unchangedOpen = !unchangedOpen;
			if (lastDto) {
				paintUpdate(lastDto);
			}
		});
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="row-overflow"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			var $menu = $(this).closest("[data-kt-pln-row-overflow]").find("[data-kt-pln-overflow-menu]");
			var opening = $menu.hasClass("hidden") || $menu.attr("hidden");
			$root.find("[data-kt-pln-overflow-menu]").addClass("hidden").attr("hidden", "hidden");
			if (opening) {
				$menu.removeClass("hidden").removeAttr("hidden");
			}
		});
		$root.on(
			"click.ktPlnUi10",
			'[data-kt-pln-action="remove-from-update"], [data-kt-pln-action="propose-removal"]',
			function (e) {
				e.preventDefault();
				e.stopPropagation();
				var item = $(this).attr("data-plan-item");
				$root.find("[data-kt-pln-overflow-menu]").addClass("hidden").attr("hidden", "hidden");
				if (item) {
					openRemoveDialog(item);
				}
			}
		);
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="keep-item"]', function (e) {
			e.preventDefault();
			closeRemoveDialog();
		});
		$root.on("click.ktPlnUi10", '[data-kt-pln-action="confirm-remove"]', function (e) {
			e.preventDefault();
			if (!removeTargetItem) {
				return;
			}
			var $visible = $removeDialog.find("[data-kt-pln-05a-variant]:not([hidden])").first();
			var reason = String($visible.find('[data-kt-field="reason"]').val() || "").trim();
			if (!reason) {
				if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
					window.ktFormErrors.show($visible, {
						reason: __("A reason for removal is required."),
					});
				}
				return;
			}
			call("remove_plan_item_from_plan", {
				plan: plan,
				plan_item: removeTargetItem,
				reason: reason,
				concurrency_token: $root.attr("data-kt-pln-concurrency") || undefined,
			}).then(function (res) {
				if (!res || res.ok === false) {
					if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
						window.ktFormErrors.show($visible, (res && res.errors) || { form: __("Could not remove") });
					}
					return;
				}
				closeRemoveDialog();
				frappe.show_alert({ message: __("Plan Item removed from this update"), indicator: "green" });
				return refresh();
			});
		});

		return refresh().catch(function (err) {
			$root.attr("data-kt-pln-error", "1");
			var msg =
				(err && (err.message || err._server_messages)) ||
				__("This plan update is not available.");
			$root.find("h1").first().text(__("Plan update unavailable"));
			$root.find("[data-kt-pln-ui10-subtitle]").text(String(msg).slice(0, 280));
			console.warn("Plan update load failed", err);
		});
	}

	kentender_procurement.live.bindPlanningWorkspace = bindPlanningWorkspace;
	kentender_procurement.live.bindPlanningRegister = bindPlanningRegister;
	kentender_procurement.live.bindPlanningBuilder = bindPlanningBuilder;
	kentender_procurement.live.bindPlanningItemEditor = bindPlanningItemEditor;
	kentender_procurement.live.bindPlanningReview = bindPlanningReview;
	kentender_procurement.live.bindPlanningApproved = bindPlanningApproved;
	kentender_procurement.live.bindPlanningUpdate = bindPlanningUpdate;
})();
