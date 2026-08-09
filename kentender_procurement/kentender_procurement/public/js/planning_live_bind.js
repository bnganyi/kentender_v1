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
		};

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

			var label =
				(dto.procuring_entity_label || "Procuring Entity") +
				" | " +
				(dto.financial_year || state.fy);
			$root.find("[data-kt-pln-context-label]").text(label);
			if (dto.helper_text) {
				$root.find("[data-kt-pln-filter-helper]").text(dto.helper_text);
			}

			var blocked = dto.selection_mode === "blocked";
			setHidden($root.find("[data-kt-pln-blocked]"), !blocked);
			if (blocked) {
				$root
					.find("[data-kt-pln-blocked-msg]")
					.text(dto.blocked_reason || __("An authorised Procuring Entity assignment is required."));
			}

			// Operational CTAs — create / mutate stay blocked for support viewers.
			setHidden($root.find('[data-kt-pln-action="register"]'), readOnly || !dto.can_create_plan);
			$root
				.find('[data-kt-pln-action="open-plan"], [data-kt-pln-action="continue-plan"]')
				.prop("disabled", false)
				.attr("aria-disabled", "false");
			if (readOnly) {
				$root.find("[data-kt-pln-read-only-banner]").removeClass("hidden").removeAttr("hidden");
			} else {
				$root.find("[data-kt-pln-read-only-banner]").addClass("hidden").attr("hidden", "hidden");
			}

			var plan = dto.current_plan;
			var $noPlan = $root.find("[data-kt-pln-no-plan]");
			if (plan) {
				setHidden($noPlan, true);
				$root.find("[data-kt-pln-plan-title]").text(plan.title || plan.plan_code || plan.plan);
				$root.find("[data-kt-pln-plan-lifecycle]").text(plan.lifecycle_state || "—");
				$root.find("[data-kt-pln-plan-items]").text(String(plan.item_count || 0));
				$root.find("[data-kt-pln-plan-total]").text(plan.planned_total_display || "KES 0");
				$root
					.find("[data-kt-pln-plan-contributions], [data-kt-pln-plan-version]")
					.text(
						plan.contributions_display ||
							plan.version_label ||
							"0 of 1 submitted"
					);
				$root.find("[data-kt-pln-plan-validation]").text(plan.validation_projection || "Not run");
				$root.attr("data-kt-pln-plan", plan.plan || "");
				$root.attr("data-kt-pln-builder-route", plan.builder_route || "");
			} else {
				setHidden($noPlan, blocked || dto.selection_mode === "multi" && !dto.procuring_entity);
				$root.find("[data-kt-pln-plan-title]").text(__("No annual plan for this context"));
				$root.find("[data-kt-pln-plan-lifecycle]").text("—");
				$root.find("[data-kt-pln-plan-items]").text("0");
				$root.find("[data-kt-pln-plan-total]").text("KES 0");
				$root
					.find("[data-kt-pln-plan-contributions], [data-kt-pln-plan-version]")
					.text("—");
				$root.find("[data-kt-pln-plan-validation]").text("Not run");
				$root.removeAttr("data-kt-pln-plan");
				$root.removeAttr("data-kt-pln-builder-route");
				if (!blocked && dto.can_create_plan && dto.procuring_entity) {
					setHidden($noPlan, false);
				}
			}

			var rows = dto.work_queue || [];
			var body = rows
				.map(function (r) {
					var status = String(r.status || "Ready");
					var pillTone = "available";
					if (/return/i.test(status)) {
						pillTone = "exhausted";
					} else if (/attention|pending/i.test(status)) {
						pillTone = "reserved";
					}
					return (
						'<tr class="hover:bg-surface-container-lowest transition-colors group" data-kt-pln-queue-row>' +
						'<td class="p-4"><p class="font-body-sm text-body-sm font-medium text-on-surface">' +
						esc(r.title || "") +
						"</p>" +
						(r.demand_code
							? '<p class="font-body-sm text-body-sm text-on-surface-variant font-data-mono">' +
							  esc(r.demand_code) +
							  "</p>"
							: "") +
						"</td>" +
						'<td class="p-4"><p class="font-body-sm text-body-sm text-on-surface-variant">' +
						esc(r.organisation_unit_label || r.organisation_unit || "") +
						"</p></td>" +
						'<td class="p-4 text-right"><p class="font-data-md text-data-md text-on-surface">' +
						esc(r.amount_display || "") +
						"</p></td>" +
						'<td class="p-4"><p class="font-body-sm text-body-sm text-on-surface-variant">' +
						esc(r.reason || "") +
						"</p></td>" +
						'<td class="p-4"><span class="inline-flex items-center gap-1 bg-status-' +
						pillTone +
						"/10 text-status-" +
						pillTone +
						' px-2 py-1 rounded-full font-label-caps text-label-caps border border-status-' +
						pillTone +
						'/20">' +
						esc(status) +
						"</span></td>" +
						'<td class="p-4 text-right"><button type="button" class="font-body-sm text-body-sm text-primary font-medium hover:underline inline-flex items-center gap-1" data-kt-pln-queue-action="' +
						esc(r.action || "view") +
						'">' +
						esc(r.action_label || "View") +
						' <span class="material-symbols-outlined text-[16px]" aria-hidden="true">arrow_forward</span></button></td></tr>'
					);
				})
				.join("");
			if (!body && !blocked) {
				body =
					'<tr><td colspan="6" class="p-4 font-body-md text-body-md text-on-surface-variant">' +
					__("No work items for this filter.") +
					"</td></tr>";
			}
			$root.find("[data-kt-pln-queue-body]").html(body);

			$root.find("[data-kt-pln-work-filter]").each(function () {
				var $el = $(this);
				var active = $el.attr("data-kt-pln-work-filter") === (state.workFilter || "all");
				$el.toggleClass("is-active", active);
				$el.toggleClass("text-primary border-b-2 border-primary", active);
				$el.toggleClass("text-on-surface-variant", !active);
			});
		}

		function refresh() {
			return call("get_planning_workspace", {
				procuring_entity: state.pe || null,
				financial_year: state.fy || "2027/28",
				work_filter: state.workFilter || "all",
			})
				.then(paint)
				.catch(function (err) {
					// Soft-deny: still mark live so blocked chrome is testable (Admin alone / no USA).
					$root.attr("data-kt-pln-live", "1");
					$root.attr("data-kt-pln-error", "1");
					$root.attr("data-kt-pln-mode", "blocked");
					setHidden($root.find("[data-kt-pln-blocked]"), false);
					$root
						.find("[data-kt-pln-blocked-msg]")
						.text(
							__("An authorised Procuring Entity assignment is required.")
						);
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
			refresh();
		});
		$root.on("click.ktPlnWs", "[data-kt-pln-work-filter]", function (e) {
			e.preventDefault();
			state.workFilter = $(this).attr("data-kt-pln-work-filter") || "all";
			$root.attr("data-kt-pln-work-filter", state.workFilter);
			refresh();
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
				} else if (plan) {
					frappe.set_route("procurement-plan-builder", { plan: plan });
				} else if ($root.attr("data-kt-pln-mode") !== "blocked") {
					frappe.set_route("procurement-plan-register");
				}
			}
		);

		return refresh();
	}

	function bindPlanningRegister($root) {
		if (!$root || !$root.length) {
			return;
		}
		$root.attr("data-kt-pln-live", "0");
		var titleDefault = "";

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
				.text("Plan period: " + periodStart + " – " + periodEnd);
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
			var $btn = $root.find('[data-testid="kt-pln-ui02-submit"]');
			$btn.prop("disabled", true);
			call("create_procurement_plan", {
				procuring_entity: pe,
				financial_year: fy,
				title: title,
				currency: "KES",
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

		return call("get_plan_builder", { plan: plan })
			.then(function (dto) {
				$root.attr("data-kt-pln-live", "1");
				$root.attr("data-kt-pln-plan", dto.plan || plan);
				$root
					.find("[data-kt-pln-builder-pe-crumb]")
					.text(dto.procuring_entity_label || dto.procuring_entity || "—");
				$root.find("[data-kt-pln-builder-fy-crumb]").text(dto.financial_year || "—");
				$root.find("[data-kt-pln-builder-title]").text(dto.title || dto.plan_code || "Plan builder");
				$root.find("[data-kt-pln-builder-lifecycle]").text(dto.lifecycle_state || "Draft");
				$root
					.find("[data-kt-pln-builder-version]")
					.text(dto.version_label || "Version 1");
				if (dto.period_start && dto.period_end) {
					$root
						.find("[data-kt-pln-builder-period]")
						.text(
							"Planning period " + dto.period_start + " to " + dto.period_end
						);
				}
				$root.find("[data-kt-pln-builder-items]").text(String(dto.item_count || 0));
				$root.find("[data-kt-pln-builder-total]").text(dto.planned_total_display || "KES 0");
				$root
					.find("[data-kt-pln-builder-org-units]")
					.text(String(dto.org_unit_count != null ? dto.org_unit_count : 0));
				$root
					.find("[data-kt-pln-builder-contributions]")
					.text(dto.contributions_display || "0 submitted");

				var empty = !!dto.empty;
				setHidden($root.find("[data-kt-pln-empty-state]"), !empty);
				setHidden($root.find("[data-kt-pln-items-table]"), empty);
				if (!empty) {
					var body = (dto.items || [])
						.map(function (it) {
							return (
								'<tr class="hover:bg-surface-container-lowest transition-colors">' +
								'<td class="p-4"><p class="font-body-sm text-body-sm font-medium text-on-surface">' +
								esc(it.title || it.plan_item_code) +
								"</p></td>" +
								'<td class="p-4"><p class="font-body-sm text-body-sm text-on-surface-variant">' +
								esc(it.category || "") +
								"</p></td>" +
								'<td class="p-4 text-right"><p class="font-data-md text-data-md text-on-surface">' +
								esc(it.amount_display || "") +
								"</p></td>" +
								'<td class="p-4"><p class="font-body-sm text-body-sm text-on-surface-variant">' +
								esc(it.baseline_state || "") +
								"</p></td></tr>"
							);
						})
						.join("");
					$root.find("[data-kt-pln-items-body]").html(body);
				}

				$root.off(".ktPlnBld");
				$root.on("click.ktPlnBld", '[data-kt-pln-action="add-demand"]', function (e) {
					e.preventDefault();
					// Gate 04 — modal deferred; CTA remains visible.
					frappe.show_alert({
						message: __("Demand selection opens in a later gate."),
						indicator: "blue",
					});
				});
			})
			.catch(function (err) {
				$root.attr("data-kt-pln-live", "0");
				$root.attr("data-kt-pln-error", "1");
				console.warn("Plan builder load failed", err);
			});
	}

	kentender_procurement.live.bindPlanningWorkspace = bindPlanningWorkspace;
	kentender_procurement.live.bindPlanningRegister = bindPlanningRegister;
	kentender_procurement.live.bindPlanningBuilder = bindPlanningBuilder;
})();
