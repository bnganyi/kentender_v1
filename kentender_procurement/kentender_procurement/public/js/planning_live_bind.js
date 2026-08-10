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

			var blocked = dto.selection_mode === "blocked";
			setHidden($root.find("[data-kt-pln-blocked]"), !blocked);
			if (blocked) {
				$root
					.find("[data-kt-pln-blocked-msg]")
					.text(dto.blocked_reason || __("An authorised Procuring Entity assignment is required."));
			}

			var canCreate = !readOnly && !!dto.can_create_plan;
			$root.attr("data-kt-pln-can-create", canCreate ? "1" : "0");

			// Operational create CTA — never for support viewers / blocked actors.
			setHidden($root.find('[data-kt-pln-action="register"]'), !canCreate);

			var plan = dto.current_plan;
			var $noPlan = $root.find("[data-kt-pln-no-plan]");
			var $open = $root.find('[data-kt-pln-action="open-plan"]');
			var $continue = $root.find('[data-kt-pln-action="continue-plan"]');
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
				setHidden($open, false);
				setHidden($continue, false);
				$open
					.text(__("Open current plan"))
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
				$root.find("[data-kt-pln-plan-items]").text("0");
				$root.find("[data-kt-pln-plan-total]").text("KES 0");
				$root
					.find("[data-kt-pln-plan-contributions], [data-kt-pln-plan-version]")
					.text("—");
				$root.find("[data-kt-pln-plan-validation]").text("Not run");
				$root.removeAttr("data-kt-pln-plan");
				$root.removeAttr("data-kt-pln-builder-route");

				var peChosen =
					!!dto.procuring_entity && dto.procuring_entity !== "__all__";
				var showCreateEmpty = !blocked && canCreate && peChosen;
				var showReadOnlyEmpty = !blocked && !canCreate && peChosen;

				var $headerCreate = $root.find('[data-testid="kt-pln-ui01-header-create"]');
				if (!$headerCreate.length) {
					$headerCreate = $(
						'<button type="button" class="bg-primary text-on-primary font-body-sm text-body-sm font-semibold px-4 py-2 rounded-lg hover:bg-primary-container transition-colors whitespace-nowrap shadow-sm shadow-primary/10" data-kt-pln-action="register" data-testid="kt-pln-ui01-header-create"></button>'
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
					setHidden($noPlan.find('[data-kt-pln-action="register"]'), false);
					// Honest CTA — do not label create as "Open current plan".
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
					setHidden($noPlan.find('[data-kt-pln-action="register"]'), true);
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
							.text(__("Open current plan"))
							.prop("disabled", true)
							.attr("aria-disabled", "true");
					}
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
						'<td class="p-4 text-right"><button type="button" class="font-body-sm text-body-sm text-primary font-medium inline-flex items-center gap-1 no-underline" data-kt-pln-queue-action="' +
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
					return;
				}
				if (plan) {
					frappe.set_route("procurement-plan-builder", { plan: plan });
					return;
				}
				// Never dump users onto register when they cannot create (support viewer),
				// and never call create "Open current plan" — use the explicit create CTA.
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

	function ensureAddDemandDialog($root) {
		var $host = $root.find("[data-kt-pln-dialog-host]");
		if (!$host.length) {
			$host = $('<div data-kt-pln-dialog-host></div>').appendTo($root);
		}
		if ($host.find("[data-kt-pln-add-demand-dialog]").length) {
			return $host.find("[data-kt-pln-add-demand-dialog]");
		}
		var html =
			kentender_procurement.ui_fixtures &&
			typeof kentender_procurement.ui_fixtures.planning_add_demand_dialog === "function"
				? kentender_procurement.ui_fixtures.planning_add_demand_dialog()
				: "";
		if (html) {
			$host.html(html);
		}
		return $host.find("[data-kt-pln-add-demand-dialog]");
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
		var selectedId = "";
		var lastEligRows = [];
		var dialogMode = "add"; // add | aggregate
		var aggregatePlanItem = "";
		var separateIntent = false;

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
				'<div class="font-data-md text-data-md ' +
				(toneClass || "text-on-surface") +
				' whitespace-nowrap">' +
				esc(cur) +
				" " +
				esc(num) +
				"</div>"
			);
		}

		function findEligRow(demandId) {
			return (lastEligRows || []).find(function (r) {
				return r.demand === demandId;
			});
		}

		function selectedRow() {
			return selectedId ? findEligRow(selectedId) : null;
		}

		function paintEligSummary() {
			var row = selectedRow();
			var needCount = row
				? Number(row.need_item_count || (row.need_items || []).length || 0)
				: 0;
			var total = row ? Number(row.available_to_plan || 0) : 0;
			var cur = (row && row.currency) || "KES";
			$dialog
				.find("[data-kt-pln-elig-count-label]")
				.text(
					row
						? __("1 Approved Demand selected")
						: __("0 Approved Demands selected")
				);
			$dialog
				.find("[data-kt-pln-elig-need-count]")
				.text(
					needCount === 1
						? __("1 Need Item")
						: __("{0} Need Items", [String(needCount)])
				);
			$dialog
				.find("[data-kt-pln-elig-amount]")
				.text(__("Total {0}", [formatKes(total, cur)]));
			var showSeparate =
				dialogMode === "add" && !!row && needCount > 1 && !separateIntent;
			setHidden($dialog.find('[data-kt-pln-action="plan-separately"]'), !showSeparate);
			setHidden($dialog.find("[data-kt-pln-add-mode-footer]"), dialogMode !== "add");
			setHidden(
				$dialog.find("[data-kt-pln-separation-wrap]"),
				!(dialogMode === "add" && separateIntent && needCount > 1)
			);
			setHidden(
				$dialog.find("[data-kt-pln-aggregate-reason-wrap]"),
				dialogMode !== "aggregate"
			);
		}

		function applyDialogMode() {
			$dialog.attr("data-kt-pln-dialog-mode", dialogMode);
			if (dialogMode === "aggregate") {
				$dialog
					.find("[data-kt-pln-ui04-title]")
					.text(__("Add another approved Demand to this Plan Item"));
				$dialog
					.find("[data-kt-pln-ui04-subtitle]")
					.text(
						__(
							"Select a compatible Approved Demand to combine into this Proposed Plan Item."
						)
					);
				$dialog.find("[data-kt-pln-ui04-cta-label]").text(__("Add Demand to Plan Item"));
			} else {
				$dialog.find("[data-kt-pln-ui04-title]").text(__("Add approved Demand"));
				$dialog
					.find("[data-kt-pln-ui04-subtitle]")
					.text(__("Select one pre-approved Demand to create a Proposed Plan Item."));
				$dialog
					.find("[data-kt-pln-ui04-cta-label]")
					.text(
						separateIntent
							? __("Create separate Plan Items")
							: __("Add Demand and continue")
					);
			}
			paintEligSummary();
		}

		function paintElig(rows) {
			lastEligRows = rows || [];
			if (selectedId && !findEligRow(selectedId)) {
				selectedId = "";
			}
			var body = lastEligRows
				.map(function (r) {
					var isSel = selectedId === r.demand;
					var checked = isSel ? " checked" : "";
					// Exactly 8 <td>s — never add an absolute <td> for the left bar (shifts columns).
					var rowClass =
						"hover:bg-surface-container-low transition-colors group relative cursor-pointer" +
						(isSel ? " bg-primary/5 is-selected" : "");
					var ou = r.organisation_unit_label || r.organisation_unit || "";
					var funding = r.funding || "—";
					var cur = r.currency || "KES";
					return (
						'<tr class="' +
						rowClass +
						'" data-kt-pln-elig-row data-demand="' +
						esc(r.demand) +
						'" data-available="' +
						esc(String(r.available_to_plan || 0)) +
						'">' +
						'<td class="pl-6 pr-3 py-4 w-10 align-top">' +
						'<input type="checkbox" name="demand-select" class="w-4 h-4 text-primary bg-surface border-outline-variant rounded focus:ring-primary focus:ring-2 mt-1"' +
						checked +
						' data-kt-pln-elig-check data-demand="' +
						esc(r.demand) +
						'" aria-label="' +
						esc(r.title || r.demand_code) +
						'" /></td>' +
						'<td class="px-3 py-4 align-top">' +
						'<div class="font-body-md text-body-md text-on-surface font-semibold leading-tight mb-1 group-hover:text-primary transition-colors" data-kt-pln-elig-title>' +
						esc(r.title || "") +
						"</div>" +
						'<div class="tracking-tight" data-kt-pln-elig-code>' +
						esc(r.demand_code || "") +
						"</div></td>" +
						'<td class="px-3 py-4 align-top">' +
						'<div class="font-body-sm text-body-sm text-on-surface" data-kt-pln-elig-ou-cell>' +
						esc(ou) +
						"</div></td>" +
						'<td class="px-3 py-4 align-top text-right">' +
						moneyCellHtml(r.approved_amount, cur, "text-on-surface") +
						"</td>" +
						'<td class="px-3 py-4 align-top text-right">' +
						moneyCellHtml(r.already_planned, cur, "text-on-surface-variant") +
						"</td>" +
						'<td class="px-3 py-4 align-top text-right">' +
						moneyCellHtml(r.available_to_plan, cur, "text-on-surface font-medium") +
						"</td>" +
						'<td class="px-3 py-4 align-top">' +
						'<div class="font-body-sm text-body-sm text-on-surface whitespace-nowrap">' +
						esc(r.required_by || "—") +
						"</div></td>" +
						'<td class="px-6 py-4 align-top">' +
						'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full font-label-caps text-[11px] font-bold tracking-wide uppercase bg-status-reserved/10 text-status-reserved border border-status-reserved/20">' +
						esc(funding) +
						"</span></td></tr>"
					);
				})
				.join("");
			if (!body) {
				body =
					'<tr class="hover:bg-surface-container-low transition-colors">' +
					'<td class="pl-6 pr-3 py-4 w-10 align-top">' +
					'<input aria-label="Disabled row" class="w-4 h-4 text-on-surface-variant/30 bg-surface border-outline-variant/50 rounded" disabled type="checkbox"/>' +
					"</td>" +
					'<td class="px-3 py-4 text-center" colspan="7">' +
					'<span class="font-body-sm text-on-surface-variant italic">' +
					__("No eligible Demands for this filter.") +
					"</span></td></tr>";
			} else {
				body +=
					'<tr class="hover:bg-surface-container-low transition-colors" data-kt-pln-elig-end>' +
					'<td class="pl-6 pr-3 py-4 w-10 align-top">' +
					'<input aria-label="Disabled row" class="w-4 h-4 text-on-surface-variant/30 bg-surface border-outline-variant/50 rounded" disabled type="checkbox"/>' +
					"</td>" +
					'<td class="px-3 py-4 text-center" colspan="7">' +
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

		function openDialog(mode, planItemForAgg) {
			dialogMode = mode === "aggregate" ? "aggregate" : "add";
			aggregatePlanItem = planItemForAgg || "";
			separateIntent = false;
			selectedId = "";
			$dialog.find("[data-kt-pln-separation-reason]").val("");
			$dialog.find("[data-kt-pln-aggregate-reason]").val("");
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
			aggregatePlanItem = "";
			separateIntent = false;
		}

		// Expose for editor "Add another Demand" CTA (same page host or builder).
		$root.data("ktPlnOpenAddDemand", openDialog);

		function paintBuilder(dto) {
			$root.attr("data-kt-pln-live", "1");
			$root.attr("data-kt-pln-plan", dto.plan || plan);
			$root
				.find("[data-kt-pln-builder-pe-crumb]")
				.text(dto.procuring_entity_label || dto.procuring_entity || "—");
			$root.find("[data-kt-pln-builder-fy-crumb]").text(dto.financial_year || "—");
			$root.find("[data-kt-pln-builder-title]").text(dto.title || dto.plan_code || "Plan builder");
			$root.find("[data-kt-pln-builder-lifecycle]").text(dto.lifecycle_state || "Draft");
			$root.find("[data-kt-pln-builder-version]").text(dto.version_label || "Version 1");
			if (dto.period_start && dto.period_end) {
				$root
					.find("[data-kt-pln-builder-period]")
					.text("Planning period " + dto.period_start + " to " + dto.period_end);
			}
			$root.find("[data-kt-pln-builder-items]").text(String(dto.item_count || 0));
			$root.find("[data-kt-pln-builder-total]").text(dto.planned_total_display || "KES 0");
			$root
				.find("[data-kt-pln-builder-org-units]")
				.text(String(dto.organisation_unit_count != null ? dto.organisation_unit_count : 0));
			$root
				.find("[data-kt-pln-builder-contributions]")
				.text(dto.departmental_contributions_label || "Preparing");
			$root
				.find("[data-kt-pln-builder-validation]")
				.text(dto.validation_projection || "Not run");

			var empty = !!dto.empty;
			setHidden($root.find("[data-kt-pln-empty-state]"), !empty);
			setHidden($root.find("[data-kt-pln-items-table]"), empty);
			// Stitch UI-05 omits filter row + planning-period meta; UI-03 keeps them.
			setHidden($root.find('[data-testid="kt-pln-ui03-filters"]'), !empty);
			setHidden($root.find("[data-kt-pln-builder-period]"), !empty);
			$root.find("[data-kt-pln-builder-period-sep]").toggle(!!empty);
			var showIssues = !empty && (dto.issue_count || 0) > 0;
			setHidden($root.find("[data-kt-pln-issue-strip]"), !showIssues);
			if (showIssues) {
				$root
					.find("[data-kt-pln-issue-copy], [data-kt-pln-issue-summary]")
					.text(dto.issue_summary || __("1 item needs attention before departmental sign-off."));
			}
			setHidden($root.find('[data-kt-pln-action="add-demand"]'), !dto.can_add_demand);

			// Footer: Stitch UI-03 disables both; UI-05 enables Run validation.
			var $run = $root.find('[data-kt-pln-action="run-validation"]');
			$run.prop("disabled", empty);
			if (empty) {
				$run.addClass("opacity-50 cursor-not-allowed");
				$root
					.find('[data-kt-pln-action="submit-dept"]')
					.contents()
					.filter(function () {
						return this.nodeType === 3;
					})
					.first()
					.replaceWith("Submit for departmental sign-off");
			} else {
				$run.removeClass("opacity-50 cursor-not-allowed");
				$root.find('[data-testid="kt-pln-ui05-submit-dept"]').each(function () {
					var $btn = $(this);
					$btn.html(
						__("Submit for sign-off") +
							' <span class="material-symbols-outlined text-sm" aria-hidden="true">lock</span>'
					);
				});
			}

			if (!empty) {
				var body = (dto.items || [])
					.map(function (it) {
						var val = it.validation_projection || "Not run";
						var needs = /attention|needs/i.test(val);
						var pill =
							'<div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-label-caps text-label-caps border whitespace-nowrap ' +
							(needs
								? "bg-status-reserved/10 text-status-reserved border-status-reserved/20"
								: "bg-surface-variant text-on-surface-variant border-outline-variant") +
							'">' +
							(needs
								? '<span class="material-symbols-outlined text-[12px]" aria-hidden="true">error</span>'
								: "") +
							esc(val) +
							"</div>";
						return (
							'<tr class="hover:bg-surface-bright transition-colors group" data-kt-pln-item-row data-plan-item="' +
							esc(it.plan_item) +
							'">' +
							'<td class="p-4 align-top"><div class="font-medium mb-1">' +
							esc(it.title || it.plan_item_code) +
							'</div><div class="text-on-surface-variant text-xs">' +
							esc(it.plan_item_code || "") +
							"</div></td>" +
							'<td class="p-4 align-top">' +
							esc(it.owner_org_unit_label || it.owner_org_unit || "") +
							"</td>" +
							'<td class="p-4 align-top">' +
							esc(it.category || "") +
							"</td>" +
							'<td class="p-4 align-top font-data-md text-data-md text-right whitespace-nowrap">' +
							esc(it.amount_display || "") +
							"</td>" +
							'<td class="p-4 align-top">' +
							esc(it.method || "") +
							"</td>" +
							'<td class="p-4 align-top"><div class="text-on-surface-variant text-xs">' +
							esc(it.schedule || "—") +
							"</div></td>" +
							'<td class="p-4 align-top">' +
							pill +
							"</td>" +
							'<td class="p-4 align-top text-center"><button type="button" class="text-primary hover:text-primary-container font-medium no-underline" data-kt-pln-action="continue-item" data-plan-item="' +
							esc(it.plan_item) +
							'" data-testid="kt-pln-ui05-row-continue"><div class="flex flex-col items-center gap-1"><span>' +
							__("Continue") +
							'</span><span class="material-symbols-outlined text-[18px]" aria-hidden="true">arrow_forward</span></div></button></td></tr>'
						);
					})
					.join("");
				$root.find("[data-kt-pln-items-body]").html(body);
				$root
					.find("[data-kt-pln-builder-table-total], [data-kt-pln-items-total]")
					.text(dto.planned_total_display || "");
			}
		}

		function refresh() {
			return call("get_plan_builder", { plan: plan }).then(paintBuilder);
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
			// Single-select: checking a row replaces any prior selection.
			if ($(this).is(":checked")) {
				selectedId = id;
				$dialog.find("[data-kt-pln-elig-check]").each(function () {
					var other = $(this).attr("data-demand");
					$(this).prop("checked", other === id);
					$(this)
						.closest("[data-kt-pln-elig-row]")
						.toggleClass("bg-primary/5 is-selected", other === id);
				});
			} else if (selectedId === id) {
				selectedId = "";
				$(this).closest("[data-kt-pln-elig-row]").removeClass("bg-primary/5 is-selected");
			}
			separateIntent = false;
			applyDialogMode();
		});
		$root.on("click.ktPlnBld", '[data-kt-pln-action="plan-separately"]', function (e) {
			e.preventDefault();
			var row = selectedRow();
			var needCount = row
				? Number(row.need_item_count || (row.need_items || []).length || 0)
				: 0;
			if (!row || needCount < 2) {
				return;
			}
			separateIntent = true;
			applyDialogMode();
			$dialog.find("[data-kt-pln-separation-reason]").trigger("focus");
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
			if (!selectedId) {
				frappe.show_alert({
					message: __("Select one Approved Demand."),
					indicator: "orange",
				});
				return;
			}
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($dialog);
			}

			if (dialogMode === "aggregate") {
				var aggReason = (
					$dialog.find("[data-kt-pln-aggregate-reason]").val() || ""
				).trim();
				if (!aggReason) {
					if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
						window.ktFormErrors.show($dialog, {
							aggregation_reason: __("A reason for combining is required."),
						});
					}
					return;
				}
				call("aggregate_plan_allocations", {
					plan_item: aggregatePlanItem,
					demand: selectedId,
					aggregation_reason: aggReason,
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
								(res && res.errors && (res.errors.aggregation_reason || res.errors.form)) ||
									"Aggregate failed"
							);
						}
						closeDialog();
						frappe.show_alert({
							message: __("Demand added to Plan Item"),
							indicator: "green",
						});
						window.location.href =
							"/app/procurement-plan-item-editor?plan_item=" +
							encodeURIComponent(aggregatePlanItem);
					})
					.catch(function (err) {
						frappe.show_alert({
							message: (err && err.message) || __("Could not aggregate Demand"),
							indicator: "red",
						});
					});
				return;
			}

			var formationMode = separateIntent
				? "separate_per_need_item"
				: "one_plan_item";
			var sepReason = ($dialog.find("[data-kt-pln-separation-reason]").val() || "").trim();
			if (formationMode === "separate_per_need_item" && !sepReason) {
				if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
					window.ktFormErrors.show($dialog, {
						separation_reason: __("A separation reason is required."),
					});
				}
				return;
			}
			call("add_demand_to_plan", {
				plan: plan,
				demand: selectedId,
				formation_mode: formationMode,
				separation_reason:
					formationMode === "separate_per_need_item" ? sepReason : "",
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
								(res.errors.separation_reason || res.errors.form)) ||
								"Add failed"
						);
					}
					closeDialog();
					frappe.show_alert({
						message: __("Demand added to plan"),
						indicator: "green",
					});
					if (
						formationMode === "separate_per_need_item" ||
						!(res && res.editor_route)
					) {
						// Already on the plan builder — refresh in place (no full navigation).
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
		$root.on("click.ktPlnBld", '[data-kt-pln-action="run-validation"]', function (e) {
			e.preventDefault();
			call("validate_plan", { plan: plan }).then(function () {
				return refresh();
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

		var $dialog = ensureAddDemandDialog($root);
		var selectedId = "";
		var lastEligRows = [];
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
		}

		function collectFields() {
			var fields = {};
			$root.find("[data-kt-pln-field]").each(function () {
				var name = $(this).attr("data-kt-pln-field");
				if (!name) {
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
			plan = dto.plan || plan;
			$root.find("[data-kt-pln-editor-title]").text(dto.requirement_title || "");
			$root
				.find("[data-kt-pln-editor-meta]")
				.text(
					(dto.organisation_unit_label || "") +
						" · " +
						(dto.amount_display || "")
				);
			$root.find("[data-kt-pln-editor-validation]").text(dto.validation_projection || "");
			var f = dto.fields || {};
			Object.keys(f).forEach(function (k) {
				var $el = $root.find('[data-kt-pln-field="' + k + '"]');
				if (!$el.length) {
					return;
				}
				if ($el.is('[type="radio"]')) {
					$el.filter('[value="' + f[k] + '"]').prop("checked", true);
				} else {
					$el.val(f[k] == null ? "" : f[k]);
				}
			});
			$root
				.find("[data-kt-pln-field='requirement_description']")
				.val(dto.requirement_description || f.requirement_description || "");
			var src = dto.approved_source || {};
			$root.find("[data-kt-pln-source-demand]").text(src.title || src.demand_code || "—");
			$root.find("[data-kt-pln-source-funding]").text(src.funding_label || "—");
			$root.find("[data-kt-pln-source-owner]").text(src.owner_org_unit_label || "—");
			$root
				.find("[data-kt-pln-editor-source-allocation]")
				.text(dto.source_allocation_summary || "");
			setHidden(
				$root.find('[data-kt-pln-action="add-another-demand"]'),
				!dto.can_add_another_demand
			);
			var showOverride =
				cstr(f.procurement_method || "") &&
				cstr(f.procurement_method) !== cstr(f.recommended_method || "Open tender");
			setHidden($root.find("[data-kt-pln-method-override]"), !showOverride);
			var multi = cstr(f.arrangement || "") === "Multi-year";
			setHidden($root.find("[data-kt-pln-multi-year]"), !multi);
			setHidden($root.find('[data-kt-pln-action="save-draft"], [data-kt-pln-action="save-return"]'), !dto.can_edit);
		}

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

		function moneyCellHtml(amount, currency, toneClass) {
			var cur = currency || "KES";
			var num = Number(amount || 0).toLocaleString(undefined, {
				maximumFractionDigits: 0,
			});
			return (
				'<div class="font-data-md text-data-md ' +
				(toneClass || "text-on-surface") +
				' whitespace-nowrap">' +
				esc(cur) +
				" " +
				esc(num) +
				"</div>"
			);
		}

		function findEligRow(demandId) {
			return (lastEligRows || []).find(function (r) {
				return r.demand === demandId;
			});
		}

		function paintAggSummary() {
			var row = selectedId ? findEligRow(selectedId) : null;
			var needCount = row
				? Number(row.need_item_count || (row.need_items || []).length || 0)
				: 0;
			var total = row ? Number(row.available_to_plan || 0) : 0;
			var cur = (row && row.currency) || "KES";
			$dialog
				.find("[data-kt-pln-elig-count-label]")
				.text(
					row
						? __("1 Approved Demand selected")
						: __("0 Approved Demands selected")
				);
			$dialog
				.find("[data-kt-pln-elig-need-count]")
				.text(
					needCount === 1
						? __("1 Need Item")
						: __("{0} Need Items", [String(needCount)])
				);
			$dialog
				.find("[data-kt-pln-elig-amount]")
				.text(__("Total {0}", [formatKes(total, cur)]));
			setHidden($dialog.find("[data-kt-pln-add-mode-footer]"), true);
			setHidden($dialog.find("[data-kt-pln-separation-wrap]"), true);
			setHidden($dialog.find("[data-kt-pln-aggregate-reason-wrap]"), false);
		}

		function paintAggElig(rows) {
			lastEligRows = rows || [];
			var body = lastEligRows
				.map(function (r) {
					var isSel = selectedId === r.demand;
					var checked = isSel ? " checked" : "";
					var rowClass =
						"hover:bg-surface-container-low transition-colors group relative cursor-pointer" +
						(isSel ? " bg-primary/5 is-selected" : "");
					var ou = r.organisation_unit_label || r.organisation_unit || "";
					var funding = r.funding || "—";
					var cur = r.currency || "KES";
					return (
						'<tr class="' +
						rowClass +
						'" data-kt-pln-elig-row data-demand="' +
						esc(r.demand) +
						'">' +
						'<td class="pl-6 pr-3 py-4 w-10 align-top">' +
						'<input type="checkbox" name="demand-select" class="w-4 h-4 text-primary bg-surface border-outline-variant rounded focus:ring-primary focus:ring-2 mt-1"' +
						checked +
						' data-kt-pln-elig-check data-demand="' +
						esc(r.demand) +
						'" /></td>' +
						'<td class="px-3 py-4 align-top"><div class="font-body-md text-body-md text-on-surface font-semibold" data-kt-pln-elig-title>' +
						esc(r.title || "") +
						'</div><div data-kt-pln-elig-code>' +
						esc(r.demand_code || "") +
						"</div></td>" +
						'<td class="px-3 py-4 align-top"><div class="font-body-sm" data-kt-pln-elig-ou-cell>' +
						esc(ou) +
						"</div></td>" +
						'<td class="px-3 py-4 align-top text-right">' +
						moneyCellHtml(r.approved_amount, cur) +
						"</td>" +
						'<td class="px-3 py-4 align-top text-right">' +
						moneyCellHtml(r.already_planned, cur, "text-on-surface-variant") +
						"</td>" +
						'<td class="px-3 py-4 align-top text-right">' +
						moneyCellHtml(r.available_to_plan, cur, "text-on-surface font-medium") +
						"</td>" +
						'<td class="px-3 py-4 align-top">' +
						esc(r.required_by || "—") +
						"</td>" +
						'<td class="px-6 py-4 align-top"><span class="inline-flex px-2.5 py-0.5 rounded-full font-label-caps text-[11px] font-bold uppercase bg-status-reserved/10 text-status-reserved border border-status-reserved/20">' +
						esc(funding) +
						"</span></td></tr>"
					);
				})
				.join("");
			if (!body) {
				body =
					'<tr><td colspan="8" class="p-4 text-center text-on-surface-variant">' +
					__("No compatible Demands.") +
					"</td></tr>";
			}
			$dialog.find("[data-kt-pln-elig-body]").html(body);
			paintAggSummary();
		}

		function openAggregateDialog() {
			selectedId = "";
			$dialog.attr("data-kt-pln-dialog-mode", "aggregate");
			$dialog
				.find("[data-kt-pln-ui04-title]")
				.text(__("Add another approved Demand to this Plan Item"));
			$dialog
				.find("[data-kt-pln-ui04-subtitle]")
				.text(
					__(
						"Select a compatible Approved Demand to combine into this Proposed Plan Item."
					)
				);
			$dialog.find("[data-kt-pln-ui04-cta-label]").text(__("Add Demand to Plan Item"));
			$dialog.find("[data-kt-pln-aggregate-reason]").val("");
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($dialog);
			}
			setHidden($dialog, false);
			$dialog.removeClass("hidden").removeAttr("hidden");
			return call("list_eligible_demands", {
				plan: plan,
				remaining_only: 1,
			}).then(function (dto) {
				paintAggElig(dto.demands || []);
			});
		}

		function closeAggregateDialog() {
			setHidden($dialog, true);
			$dialog.addClass("hidden").attr("hidden", "hidden");
		}

		function cstr(v) {
			return String(v == null ? "" : v);
		}

		function save(andReturn) {
			clearErrors();
			return call("update_plan_item", {
				plan_item: planItem,
				fields: JSON.stringify(collectFields()),
			}).then(function (result) {
				if (!result || result.ok === false) {
					showErrors((result && result.errors) || { form: __("Could not save") });
					return;
				}
				frappe.show_alert({ message: __("Plan Item saved"), indicator: "green" });
				if (andReturn && result.validation) {
					window.location.href =
						"/app/procurement-plan-builder?plan=" +
						encodeURIComponent(
							$root.attr("data-kt-pln-plan") ||
								(result.validation && result.validation.plan) ||
								""
						);
					return;
				}
				return call("get_plan_item_editor", { plan_item: planItem }).then(paint);
			});
		}

		$root.off(".ktPlnEd");
		$root.on("change.ktPlnEd", '[data-kt-pln-field="procurement_method"]', function () {
			var rec = $root.find('[data-kt-pln-field="recommended_method"]').val() || "Open tender";
			setHidden($root.find("[data-kt-pln-method-override]"), $(this).val() === rec);
		});
		$root.on("change.ktPlnEd", '[data-kt-pln-field="arrangement"]', function () {
			setHidden($root.find("[data-kt-pln-multi-year]"), $(this).val() !== "Multi-year");
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="save-draft"]', function (e) {
			e.preventDefault();
			save(false);
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="save-return"]', function (e) {
			e.preventDefault();
			save(true);
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="cancel"]', function (e) {
			e.preventDefault();
			call("get_plan_item_editor", { plan_item: planItem }).then(function (dto) {
				window.location.href = dto.builder_route || "/app/planning-workspace";
			});
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="add-another-demand"]', function (e) {
			e.preventDefault();
			openAggregateDialog();
		});
		$root.on(
			"click.ktPlnEd",
			'[data-kt-pln-action="elig-cancel"], [data-kt-pln-action="elig-close"]',
			function (e) {
				e.preventDefault();
				closeAggregateDialog();
			}
		);
		$root.on("change.ktPlnEd", "[data-kt-pln-elig-check]", function () {
			var id = $(this).attr("data-demand");
			if (!id) {
				return;
			}
			if ($(this).is(":checked")) {
				selectedId = id;
				$dialog.find("[data-kt-pln-elig-check]").each(function () {
					var other = $(this).attr("data-demand");
					$(this).prop("checked", other === id);
					$(this)
						.closest("[data-kt-pln-elig-row]")
						.toggleClass("bg-primary/5 is-selected", other === id);
				});
			} else if (selectedId === id) {
				selectedId = "";
				$(this).closest("[data-kt-pln-elig-row]").removeClass("bg-primary/5 is-selected");
			}
			paintAggSummary();
		});
		$root.on("click.ktPlnEd", '[data-kt-pln-action="elig-add"]', function (e) {
			e.preventDefault();
			if ($dialog.attr("data-kt-pln-dialog-mode") !== "aggregate") {
				return;
			}
			if (!selectedId) {
				frappe.show_alert({
					message: __("Select one Approved Demand."),
					indicator: "orange",
				});
				return;
			}
			var aggReason = ($dialog.find("[data-kt-pln-aggregate-reason]").val() || "").trim();
			if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
				window.ktFormErrors.clear($dialog);
			}
			if (!aggReason) {
				if (window.ktFormErrors && typeof window.ktFormErrors.show === "function") {
					window.ktFormErrors.show($dialog, {
						aggregation_reason: __("A reason for combining is required."),
					});
				}
				return;
			}
			call("aggregate_plan_allocations", {
				plan_item: planItem,
				demand: selectedId,
				aggregation_reason: aggReason,
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
							(res && res.errors && (res.errors.aggregation_reason || res.errors.form)) ||
								"Aggregate failed"
						);
					}
					closeAggregateDialog();
					frappe.show_alert({
						message: __("Demand added to Plan Item"),
						indicator: "green",
					});
					return call("get_plan_item_editor", { plan_item: planItem }).then(paint);
				})
				.catch(function (err) {
					frappe.show_alert({
						message: (err && err.message) || __("Could not aggregate Demand"),
						indicator: "red",
					});
				});
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

	kentender_procurement.live.bindPlanningWorkspace = bindPlanningWorkspace;
	kentender_procurement.live.bindPlanningRegister = bindPlanningRegister;
	kentender_procurement.live.bindPlanningBuilder = bindPlanningBuilder;
	kentender_procurement.live.bindPlanningItemEditor = bindPlanningItemEditor;
})();
