// Strategy Alignment MVP-1 — live API binders (Stitch shells + frappe.call).
frappe.provide("kentender_strategy.live");

(function () {
	"use strict";

	var API = "kentender_strategy.api.strategy_api";

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: API + "." + method,
				args: args || {},
				freeze: false,
				callback: function (r) {
					if (r && r.exc) {
						reject(r.exc);
						return;
					}
					resolve(r && r.message);
				},
				error: function (err) {
					reject(err);
				},
			});
		});
	}

	function esc(s) {
		return frappe.utils.escape_html(s == null ? "" : String(s));
	}

	/**
	 * Shared client-side table pager bound to [data-kt-str-table-footer].
	 * Chrome: "Showing X of Y" + Rows per page + numbered pager (1 2 3 … n).
	 * opts.renderPage(pageRows, state) paints the current page into tbody.
	 */
	function attachTablePagination($root, opts) {
		opts = opts || {};
		var existing = $root.data("ktStrPagerApi");
		if (existing && existing._bound) {
			if (typeof opts.renderPage === "function") {
				existing._renderPage = opts.renderPage;
			}
			return existing;
		}
		var $footer = $root.find("[data-kt-str-table-footer]").first();
		var state = {
			page: 1,
			pageSize: 20,
			rows: [],
		};
		$root.data("ktStrPager", state);

		function totalPages() {
			var n = state.rows.length;
			if (!n) {
				return 1;
			}
			return Math.max(1, Math.ceil(n / state.pageSize));
		}

		/** Page tokens: 1 2 3 … n-2 n-1 n (plus neighborhood around current). */
		function pageItems(current, pages) {
			if (pages <= 1) {
				return [1];
			}
			if (pages <= 7) {
				var all = [];
				for (var i = 1; i <= pages; i++) {
					all.push(i);
				}
				return all;
			}
			var show = {};
			function mark(p) {
				if (p >= 1 && p <= pages) {
					show[p] = 1;
				}
			}
			mark(1);
			mark(2);
			mark(3);
			mark(pages - 2);
			mark(pages - 1);
			mark(pages);
			mark(current - 1);
			mark(current);
			mark(current + 1);
			var sorted = Object.keys(show)
				.map(function (k) {
					return parseInt(k, 10);
				})
				.sort(function (a, b) {
					return a - b;
				});
			var out = [];
			for (var j = 0; j < sorted.length; j++) {
				if (j > 0 && sorted[j] - sorted[j - 1] > 1) {
					out.push("ellipsis");
				}
				out.push(sorted[j]);
			}
			return out;
		}

		function paintChrome() {
			if (!$footer.length) {
				return;
			}
			var total = state.rows.length;
			var pages = totalPages();
			if (state.page > pages) {
				state.page = pages;
			}
			if (state.page < 1) {
				state.page = 1;
			}
			var start = total ? (state.page - 1) * state.pageSize + 1 : 0;
			var end = Math.min(state.page * state.pageSize, total);
			var rangeText;
			if (!total) {
				rangeText = __("Showing 0 of 0");
			} else if (start === 1 && end === total) {
				rangeText = __("Showing {0} of {1}", [String(total), String(total)]);
			} else {
				rangeText = __("Showing {0}-{1} of {2}", [String(start), String(end), String(total)]);
			}
			$footer.find("[data-kt-str-footer-range]").text(rangeText);
			$footer.find("[data-kt-str-footer-page-size]").val(String(state.pageSize));
			$footer.find("[data-kt-str-footer-prev]").prop("disabled", state.page <= 1);
			$footer
				.find("[data-kt-str-footer-next]")
				.prop("disabled", !total || state.page >= pages);

			var $pages = $footer.find("[data-kt-str-footer-pages]");
			if ($pages.length) {
				var html = "";
				pageItems(state.page, pages).forEach(function (tok) {
					if (tok === "ellipsis") {
						html +=
							'<span class="kt-str-footer-ellipsis" data-kt-str-footer-ellipsis aria-hidden="true">…</span>';
						return;
					}
					var active = tok === state.page;
					html +=
						'<button type="button" class="kt-str-footer-page-btn' +
						(active ? " is-active" : "") +
						'" data-kt-str-footer-page-num="' +
						tok +
						'" aria-label="' +
						__("Page {0}", [String(tok)]) +
						'"' +
						(active ? ' aria-current="page"' : "") +
						">" +
						tok +
						"</button>";
				});
				$pages.html(html);
			}
		}

		function render() {
			paintChrome();
			var startIdx = (state.page - 1) * state.pageSize;
			var pageRows = state.rows.slice(startIdx, startIdx + state.pageSize);
			if (typeof api._renderPage === "function") {
				api._renderPage(pageRows, state);
			}
		}

		function setRows(rows, resetPage) {
			state.rows = rows || [];
			if (resetPage) {
				state.page = 1;
			}
			render();
		}

		var api = {
			_bound: true,
			_renderPage: opts.renderPage,
			setRows: setRows,
			render: render,
			state: state,
		};
		$root.data("ktStrPagerApi", api);

		if ($footer.length && !$footer.data("ktStrPagerBound")) {
			$footer.data("ktStrPagerBound", 1);
			$footer.on("change.ktStrPager", "[data-kt-str-footer-page-size]", function () {
				state.pageSize = parseInt($(this).val(), 10) || 20;
				state.page = 1;
				render();
			});
			$footer.on("click.ktStrPager", "[data-kt-str-footer-prev]", function (e) {
				e.preventDefault();
				if (state.page > 1) {
					state.page -= 1;
					render();
				}
			});
			$footer.on("click.ktStrPager", "[data-kt-str-footer-next]", function (e) {
				e.preventDefault();
				if (state.page < totalPages()) {
					state.page += 1;
					render();
				}
			});
			$footer.on("click.ktStrPager", "[data-kt-str-footer-page-num]", function (e) {
				e.preventDefault();
				var p = parseInt($(this).attr("data-kt-str-footer-page-num"), 10);
				if (!p || p === state.page || p < 1 || p > totalPages()) {
					return;
				}
				state.page = p;
				render();
			});
		}
		return api;
	}

	/**
	 * Compact period for tables/headers: "01-Jul-2026 - 30-Jun-2030".
	 * Never join locale DD-MM-YYYY strings (reads as a digit dump in mono table cells).
	 */
	function formatPeriod(start, end) {
		var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
		function fmt(d) {
			if (!d) {
				return "";
			}
			var dt = null;
			try {
				dt = frappe.datetime.str_to_obj(d);
			} catch (e) {
				dt = null;
			}
			if (!dt || isNaN(dt.getTime())) {
				var m = String(d).match(/^(\d{4})-(\d{2})-(\d{2})/);
				if (m) {
					return m[3] + "-" + months[parseInt(m[2], 10) - 1] + "-" + m[1];
				}
				return String(d);
			}
			var day = String(dt.getDate()).padStart(2, "0");
			return day + "-" + months[dt.getMonth()] + "-" + dt.getFullYear();
		}
		if (!start && !end) {
			return "—";
		}
		if (start && end) {
			return fmt(start) + " - " + fmt(end);
		}
		return fmt(start || end);
	}

	/** Portfolio period cell: stack start/end so the column stays narrow. */
	function periodCellHtml(label, start, end) {
		var text = label || formatPeriod(start, end);
		if (!text || text === "—") {
			return "—";
		}
		var parts = String(text).split(/\s+-\s+/);
		if (parts.length === 2 && parts[0] && parts[1]) {
			return (
				'<span class="kt-str-period-wrap">' +
				'<span class="kt-str-period-start">' +
				esc(parts[0]) +
				"</span>" +
				'<span class="kt-str-period-sep" aria-hidden="true">–</span>' +
				'<span class="kt-str-period-end">' +
				esc(parts[1]) +
				"</span></span>"
			);
		}
		return esc(text);
	}

	function statusPill(status) {
		var st = status || "";
		var cls = "bg-surface-container text-on-surface-variant";
		if (st === "Active") {
			cls = "bg-status-available/15 text-status-available";
		} else if (st === "Submitted") {
			cls = "bg-status-reserved/15 text-status-reserved";
		} else if (st === "Draft") {
			cls = "bg-surface-container-high text-on-surface-variant";
		}
		return (
			'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ' +
			cls +
			'">' +
			esc(st) +
			"</span>"
		);
	}

	function attentionCell(p) {
		var kind = p.attention_kind || "none";
		if (kind === "none") {
			return '<span class="text-on-surface-variant text-body-md">—</span>';
		}
		var tone =
			kind === "risk" ? "text-error"
			: kind === "due" ? "text-status-committed"
			: "text-on-surface-variant";
		var icon = p.attention_icon || "info";
		return (
			'<div class="flex items-center gap-1.5 ' +
			tone +
			' text-body-md">' +
			'<span class="material-symbols-outlined text-sm">' +
			esc(icon) +
			"</span>" +
			esc(p.attention || "") +
			"</div>"
		);
	}

	function actionLabel(status) {
		return status === "Submitted" ? "Review" : "View";
	}

	function actionClass(status) {
		return status === "Submitted"
			? "text-primary font-bold hover:text-secondary transition-colors text-body-md"
			: "text-secondary font-semibold hover:text-primary transition-colors text-body-md";
	}

	function renderPlanRows(plans) {
		if (!plans || !plans.length) {
			return (
				'<tr data-kt-str-empty="1"><td class="py-6 px-4 text-body-md text-on-surface-variant" colspan="7">' +
				esc(__("No strategic plans match the current filters.")) +
				"</td></tr>"
			);
		}
		return plans
			.map(function (p) {
				return (
					'<tr class="hover:bg-surface-container transition-colors group" data-plan-code="' +
					esc(p.code) +
					'" data-plan-id="' +
					esc(p.id) +
					'" data-plan-status="' +
					esc(p.status) +
					'">' +
					'<td class="py-4 px-4 kt-str-plans-col-plan"><div class="flex flex-col min-w-0">' +
					'<span class="font-data-mono text-data-mono text-secondary mb-0.5">' +
					esc(p.code) +
					"</span>" +
					'<span class="font-body-md text-body-md font-semibold text-primary">' +
					esc(p.name) +
					"</span></div></td>" +
					'<td class="py-4 px-4 text-body-md text-on-surface-variant kt-str-plans-col-type">' +
					esc(p.plan_type || "") +
					"</td>" +
					'<td class="py-4 px-4 text-data-mono text-on-surface-variant kt-str-plans-col-period">' +
					periodCellHtml(p.effective_period_label, p.start_date, p.end_date) +
					"</td>" +
					'<td class="py-4 px-4 text-data-mono text-on-surface-variant text-center kt-str-plans-col-ver">v' +
					esc(p.version_number || 1) +
					"</td>" +
					'<td class="py-4 px-4 kt-str-plans-col-status">' +
					statusPill(p.status) +
					"</td>" +
					'<td class="py-4 px-4 kt-str-plans-col-attention">' +
					attentionCell(p) +
					"</td>" +
					'<td class="py-4 px-4 text-right kt-str-plans-col-action">' +
					'<button type="button" data-kt-str-action="open-plan" class="' +
					actionClass(p.status) +
					'">' +
					esc(actionLabel(p.status)) +
					"</button></td></tr>"
				);
			})
			.join("");
	}

	function renderMyWork(items) {
		if (!items || !items.length) {
			return (
				'<p class="text-body-md text-on-surface-variant px-1 py-2" data-kt-str-my-work-empty="1">' +
				esc(__("No open work items right now.")) +
				"</p>"
			);
		}
		return items
			.map(function (item) {
				var action =
					item.type === "plan_review" ? "review-plan"
					: item.type === "submit_measurement" ? "submit-measurement"
					: item.type === "verify_measurement" ? "verify-measurement"
					: item.type === "resolve_target" ? "resolve-target"
					: "open-plan";
				var route = (item.route || []).join("/");
				return (
					'<a class="group flex items-center justify-between p-3 rounded-lg hover:bg-surface-container transition-all border border-transparent hover:border-outline-variant" href="#" data-kt-str-action="' +
					esc(action) +
					'" data-kt-str-route="' +
					esc(route) +
					'">' +
					'<span class="font-body-md text-body-md text-on-surface-variant group-hover:text-primary">' +
					esc(item.label || "") +
					"</span>" +
					'<span class="material-symbols-outlined text-on-surface-variant group-hover:translate-x-1 transition-transform text-lg">arrow_forward</span></a>'
				);
			})
			.join("");
	}

	function readPortfolioFilters($root) {
		var $f = $root.find('[data-testid="kt-str-pf-filters"]');
		return {
			search: ($f.find('[data-kt-str-filter="search"]').val() || "").trim(),
			plan_type: $f.find('[data-kt-str-filter="plan_type"]').val() || "",
			period: $f.find('[data-kt-str-filter="period"]').val() || "",
			status: $f.find('[data-kt-str-filter="status"]').val() || "",
			procuring_entity: $f.find('[data-kt-str-filter="procuring_entity"]').val() || "",
		};
	}

	function applyPortfolioStrip($root, counts) {
		counts = counts || {};
		$root.find('[data-kt-str-count="active"]').text(String(counts.active || 0));
		$root.find('[data-kt-str-count="submitted"]').text(String(counts.submitted || 0));
		$root.find('[data-kt-str-count="measurements_due"]').text(String(counts.measurements_due || 0));
		$root.find('[data-kt-str-count="measurement_attention"]').text(String(counts.measurement_attention || 0));
	}

	function applyEntityOptions($root, entities) {
		var $sel = $root.find('[data-kt-str-filter="procuring_entity"]');
		if (!$sel.length) {
			return;
		}
		var current = $sel.val();
		var html = '<option value="">Entity</option>';
		(entities || []).forEach(function (e) {
			html +=
				'<option value="' +
				esc(e.id) +
				'">' +
				esc(e.name || e.id) +
				"</option>";
		});
		$sel.html(html);
		if (current) {
			$sel.val(current);
		}
	}

	function renderPortfolioTable($root, plans, totalHint) {
		var pager = attachTablePagination($root, {
			renderPage: function (pageRows) {
				var $tbody = $root.find("[data-kt-str-plans-tbody]");
				if (!$tbody.length) {
					$tbody = $root.find('[data-testid="kt-str-plans-table"] tbody');
				}
				$tbody.html(renderPlanRows(pageRows));
			},
		});
		/* totalHint kept for callers; pager uses full filtered list length. */
		void totalHint;
		pager.setRows(plans || [], true);
	}

	function bindPortfolio($root) {
		var token = Number($root.attr("data-kt-str-bind-token") || 0) + 1;
		$root.attr("data-kt-str-bind-token", String(token));
		$root.attr("data-kt-str-live", "0");

		function reloadTable() {
			var filters = readPortfolioFilters($root);
			return call("list_strategy_plans", filters).then(function (plans) {
				if (String($root.attr("data-kt-str-bind-token")) !== String(token)) {
					return;
				}
				renderPortfolioTable($root, plans || [], ($root.data("ktStrPlanTotal") || (plans || []).length));
			});
		}

		return call("get_strategy_portfolio")
			.then(function (data) {
				if (!data) {
					throw new Error("Empty portfolio payload");
				}
				if (String($root.attr("data-kt-str-bind-token")) !== String(token)) {
					return data;
				}
				$root.attr("data-kt-str-live", "1");
				$root.data("ktStrPlanTotal", (data.plans || []).length);
				$root.data(
					"ktStrDefaultPe",
					((data.entities || [])[0] && (data.entities || [])[0].id) || ""
				);
				applyPortfolioStrip($root, data.counts);
				applyEntityOptions($root, data.entities);
				renderPortfolioTable($root, data.plans || [], (data.plans || []).length);
				$root.find("[data-kt-str-my-work-list]").html(renderMyWork(data.my_work || []));

				var canCreate = !!(data.capabilities && data.capabilities.create_plan);
				var $create = $root.find('[data-kt-str-action="create-plan"]');
				if (!canCreate) {
					$create.addClass("hidden").attr("disabled", "disabled").attr("aria-hidden", "true");
				} else {
					$create.removeClass("hidden").removeAttr("disabled").attr("aria-hidden", "false");
				}

				var debounce = null;
				$root.off(".ktStrPfLive");
				$root.on("input.ktStrPfLive", '[data-kt-str-filter="search"]', function () {
					clearTimeout(debounce);
					debounce = setTimeout(function () {
						reloadTable().catch(function (err) {
							console.warn("Portfolio filter failed", err);
						});
					}, 250);
				});
				$root.on(
					"change.ktStrPfLive",
					'[data-kt-str-filter="plan_type"], [data-kt-str-filter="period"], [data-kt-str-filter="status"], [data-kt-str-filter="procuring_entity"]',
					function () {
						reloadTable().catch(function (err) {
							console.warn("Portfolio filter failed", err);
						});
					}
				);
				$root.on("click.ktStrPfLive", '[data-kt-str-action="clear-filters"]', function (e) {
					e.preventDefault();
					$root.find("[data-kt-str-filter]").each(function () {
						$(this).val("");
					});
					reloadTable().catch(function (err) {
						console.warn("Portfolio clear filters failed", err);
					});
				});
				return data;
			})
			.catch(function (err) {
				$root.attr("data-kt-str-live", "0");
				$root.attr("data-kt-str-error", "1");
				var $tbody = $root.find("[data-kt-str-plans-tbody]");
				$tbody.html(
					'<tr data-kt-str-error-row="1"><td class="py-6 px-4 text-body-md text-error" colspan="7">' +
						esc(__("Could not load strategic plans. Refresh and try again.")) +
						"</td></tr>"
				);
				throw err;
			});
	}

	function clearCreateErrors($root) {
		$root.find("[data-kt-str-error]").addClass("hidden").text("");
		$root.find("[data-kt-str-field]").removeClass("kt-str-field-invalid");
	}

	function showCreateErrors($root, errors) {
		clearCreateErrors($root);
		Object.keys(errors || {}).forEach(function (field) {
			var $err = $root.find('[data-kt-str-error="' + field + '"]');
			$err.text(errors[field] || "").removeClass("hidden");
			$root.find('[data-kt-str-field="' + field + '"]').addClass("kt-str-field-invalid");
		});
	}

	var PLAN_TYPE_BY_STITCH = {
		entity: "Entity Strategic Plan",
		sector: "Sector Strategy",
		programme: "Programme Strategy",
		other: "Other",
	};

	function readCreatePayload($root) {
		var pe =
			($root.find('[data-kt-str-field="procuring_entity_select"]').val() || "").trim() ||
			($root.find('[data-kt-str-field="procuring_entity"]').val() || "").trim();
		var typeKey = $root.find('[data-kt-str-field="plan_type"]').val() || "";
		return {
			plan_code: ($root.find('[data-kt-str-field="plan_code"]').val() || "").trim().toUpperCase(),
			title: ($root.find('[data-kt-str-field="title"]').val() || "").trim(),
			plan_type: PLAN_TYPE_BY_STITCH[typeKey] || typeKey,
			procuring_entity: pe,
			start_date: $root.find('[data-kt-str-field="start_date"]').val() || "",
			end_date: $root.find('[data-kt-str-field="end_date"]').val() || "",
			description: ($root.find('[data-kt-str-field="description"]').val() || "").trim(),
		};
	}

	function initialsFromName(name) {
		var parts = String(name || "")
			.trim()
			.split(/\s+/)
			.filter(Boolean);
		if (!parts.length) {
			return "—";
		}
		if (parts.length === 1) {
			return parts[0].slice(0, 2).toUpperCase();
		}
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	function showCreateToast($root, planName) {
		var $toast = $root.find("#successToast, [data-testid='kt-str-create-toast']");
		if (!$toast.length) {
			return;
		}
		$root
			.find("[data-kt-str-toast-detail]")
			.text(__('Opening Plan Overview for "{0}"...', [planName || __("new plan")]));
		$toast
			.removeClass("translate-y-24 opacity-0")
			.addClass("translate-y-0 opacity-100")
			.attr("aria-hidden", "false");
	}

	function bindCreatePlan($root) {
		$root.attr("data-kt-str-live", "0");
		return call("get_create_plan_context")
			.then(function (ctx) {
				if (!ctx) {
					throw new Error("Empty create context");
				}
				$root.attr("data-kt-str-live", "1");
				var pe = ctx.procuring_entity || {};
				var changeEntity = !!(ctx.capabilities && ctx.capabilities.change_entity);
				var $hidden = $root.find('[data-kt-str-field="procuring_entity"]');
				var $select = $root.find('[data-kt-str-field="procuring_entity_select"]');
				var fullName = frappe.session.user_fullname || frappe.session.user || "";
				$root.find("[data-kt-str-created-by-name]").text(fullName);
				$root.find("[data-kt-str-created-by-initials]").text(initialsFromName(fullName));

				function applyPeOptions(entities) {
					var html = '<option value="">' + esc(__("Select procuring entity")) + "</option>";
					var list = entities || [];
					if (!list.length && pe.id) {
						list = [{ id: pe.id, name: pe.name || pe.id }];
					}
					list.forEach(function (e) {
						html +=
							'<option value="' +
							esc(e.id) +
							'">' +
							esc(e.name || e.id) +
							"</option>";
					});
					$select.html(html);
					if (pe.id) {
						$select.val(pe.id);
						$hidden.val(pe.id);
					}
					if (!changeEntity) {
						$select.prop("disabled", true).attr("aria-readonly", "true");
					} else {
						$select.prop("disabled", false).removeAttr("aria-readonly");
					}
				}

				$select.off("change.ktStrPe").on("change.ktStrPe", function () {
					$hidden.val($select.val() || "");
				});

				return call("get_strategy_portfolio").then(function (pf) {
					applyPeOptions((pf && pf.entities) || []);
					return ctx;
				});
			})
			.then(function (ctx) {
				$root.off(".ktStrCreate");
				$root.on("input.ktStrCreate", '[data-kt-str-field="plan_code"]', function () {
					this.value = String(this.value || "").toUpperCase();
				});
				$root.on("click.ktStrCreate", '[data-kt-str-action="cancel-create"]', function (e) {
					e.preventDefault();
					frappe.set_route("strategy-alignment");
				});
				$root.on("submit.ktStrCreate", "#planForm, [data-testid='kt-str-create-plan-form']", function (e) {
					e.preventDefault();
					clearCreateErrors($root);
					var payload = readCreatePayload($root);
					$root.find('[data-kt-str-field="plan_code"]').val(payload.plan_code);
					var $btn = $root.find('[data-kt-str-action="submit-create"]');
					$btn.prop("disabled", true);
					call("create_plan", { payload: payload })
						.then(function (result) {
							if (!result || !result.ok) {
								showCreateErrors($root, (result && result.errors) || {});
								$btn.prop("disabled", false);
								return;
							}
							showCreateToast($root, result.plan.name || result.plan.code);
							setTimeout(function () {
								frappe.set_route("strategy-plan-overview", result.plan.code);
							}, 600);
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
				return ctx;
			})
			.catch(function (err) {
				$root.attr("data-kt-str-error", "1");
				frappe.msgprint({
					title: __("Not permitted"),
					message: __("Only Strategy Officer or Strategy Manager can create plans."),
					indicator: "red",
				});
				throw err;
			});
	}

	function paintPlanStatusPill($root, status) {
		var st = status || "";
		/* Scope to shared plan chrome only — never paint body status chips. */
		var $chrome = $root.find('[data-testid="kt-str-plan-chrome"], .kt-str-injected-plan-chrome').first();
		var $scope = $chrome.length ? $chrome : $root;
		var $pill = $scope.find("[data-kt-str-plan-status-pill]");
		var $dot = $scope.find("[data-kt-str-plan-status-dot]");
		$pill.removeClass(
			"bg-status-available/10 text-status-available bg-status-reserved/10 text-status-reserved bg-surface-variant text-on-surface-variant"
		);
		$dot.removeClass("bg-status-available bg-status-reserved bg-outline");
		if (st === "Active" || st === "Approved") {
			$pill.addClass("bg-status-available/10 text-status-available");
			$dot.addClass("bg-status-available");
		} else if (st === "Submitted" || st === "Returned") {
			$pill.addClass("bg-status-reserved/10 text-status-reserved");
			$dot.addClass("bg-status-reserved");
		} else {
			$pill.addClass("bg-surface-variant text-on-surface-variant");
			$dot.addClass("bg-outline");
		}
		$scope.find("[data-kt-str-plan-status]").text(st || "—");
	}

	function bindPlanChrome($root, plan) {
		if (!plan) {
			return;
		}
		var $chrome = $root.find('[data-testid="kt-str-plan-chrome"], .kt-str-injected-plan-chrome').first();
		if (!$chrome.length) {
			return;
		}
		$chrome.find("[data-kt-str-plan-title]").first().text(plan.name || "");
		$chrome.find("[data-kt-str-plan-code]").first().text(plan.code || "");
		paintPlanStatusPill($root, plan.status || "");
		var period = "";
		if (plan.effective_period_label) {
			period = "Effective " + plan.effective_period_label;
		} else if (plan.start_date || plan.end_date) {
			period = "Effective " + formatPeriod(plan.start_date, plan.end_date);
		}
		$chrome.find("[data-kt-str-plan-period]").first().text(period);
		/* Canonical label is "Version N" — never compact "vN" in plan chrome. */
		$chrome
			.find("[data-kt-str-plan-version]")
			.first()
			.text(plan.version_number != null ? "Version " + plan.version_number : "");
		/* Seed sibling tabs so soft-nav never flashes placeholder chrome. */
		if (
			kentender_strategy.alignment &&
			typeof kentender_strategy.alignment.rememberPlanChrome === "function"
		) {
			kentender_strategy.alignment.rememberPlanChrome(plan);
		}
	}

	function ensureStartStructureCta($root, plan, counts, capabilities) {
		var $cluster = $root
			.find('[data-testid="kt-str-plan-chrome"] [data-kt-str-chrome-actions]')
			.first();
		if (!$cluster.length) {
			$cluster = $root
				.find('[data-testid="kt-str-plan-chrome"] .flex.flex-wrap.items-center.gap-3')
				.first();
		}
		if (!$cluster.length) {
			return;
		}
		$cluster.find('[data-kt-str-action="start-plan-structure"]').remove();
		var empty = !counts || !counts.programmes;
		var draft = plan && plan.status === "Draft";
		var canStart = capabilities && capabilities.start_structure;
		var canSucc = capabilities && capabilities.create_successor;
		var $succ = $cluster.find('[data-kt-str-action="open-successor-modal"]');
		if (!$succ.length) {
			return;
		}
		if (draft && empty && canStart !== false) {
			$succ.addClass("hidden").attr("aria-hidden", "true");
			$cluster.append(
				'<button type="button" data-kt-str-action="start-plan-structure" data-testid="kt-str-start-plan-structure" class="px-6 py-2.5 bg-primary text-white font-bold text-body-md rounded-lg hover:bg-primary/90 transition-all shadow-sm">' +
					esc(__("Start plan structure")) +
					"</button>"
			);
		} else if (canSucc) {
			$succ.removeClass("hidden").attr("aria-hidden", "false");
		} else {
			$succ.addClass("hidden").attr("aria-hidden", "true");
		}
	}

	function resultToneClass(label) {
		var t = String(label || "").toLowerCase();
		if (t.indexOf("at risk") >= 0 || t.indexOf("off track") >= 0) {
			return "bg-status-reserved/10 text-status-reserved";
		}
		if (t.indexOf("due") >= 0) {
			return "bg-primary-container/10 text-on-primary-container";
		}
		return "bg-surface-container-high text-on-surface-variant";
	}

	function renderAttentionRows(rows) {
		if (!rows || !rows.length) {
			return (
				'<tr data-kt-str-attention-empty="1"><td class="py-6 px-6 text-body-md text-on-surface-variant" colspan="4">' +
				esc(__("No performance items need attention.")) +
				"</td></tr>"
			);
		}
		return rows
			.map(function (row) {
				var tgt = row.target || {};
				var action = row.action || "view-measurement";
				var icon = action === "submit-measurement" ? "add_circle" : "arrow_forward";
				var route = (row.route || []).join("/");
				return (
					'<tr class="hover:bg-surface-container transition-colors" data-kt-str-attention-row="1" data-measurement-id="' +
					esc(row.id || "") +
					'" data-target-code="' +
					esc(tgt.code || "") +
					'">' +
					'<td class="px-6 py-4"><div class="flex flex-col">' +
					'<span class="font-data-mono text-data-mono text-xs text-primary mb-1">' +
					esc(tgt.code || "") +
					"</span>" +
					'<span class="text-body-md font-body-md text-on-surface">' +
					esc(tgt.name || "") +
					"</span></div></td>" +
					'<td class="px-6 py-4 text-body-md text-on-surface-variant">' +
					esc(row.period_label || "—") +
					"</td>" +
					'<td class="px-6 py-4"><span class="inline-flex items-center px-2 py-1 rounded text-[11px] font-bold uppercase ' +
					resultToneClass(row.result_label) +
					'">' +
					esc(row.result_label || "") +
					"</span></td>" +
					'<td class="px-6 py-4 text-right">' +
					'<a class="text-primary font-bold text-body-md hover:underline inline-flex items-center gap-1" href="#" data-kt-str-action="' +
					esc(action) +
					'" data-kt-str-route="' +
					esc(route) +
					'" data-target-code="' +
					esc(tgt.code || "") +
					'">' +
					esc(row.action_label || __("View")) +
					' <span class="material-symbols-outlined text-[16px]">' +
					icon +
					"</span></a></td></tr>"
				);
			})
			.join("");
	}

	function bindOverview($root, planCode) {
		var args = {};
		if (planCode && /^[A-Z0-9-]+$/i.test(planCode) && planCode.indexOf("MOH-") === 0) {
			args.plan_code = planCode;
		} else if (planCode) {
			// May be plan docname (hash) or business code — server resolves both via plan_code arg.
			args.plan_code = planCode;
		}
		return call("get_plan_overview", args).then(function (dto) {
			if (!dto || !dto.plan) {
				return;
			}
			var plan = dto.plan;
			var c = dto.counts || {};
			var caps = dto.capabilities || {};
			$root.attr("data-kt-str-live", "1");
			$root.attr("data-kt-str-plan-id", plan.id || "");
			$root.attr("data-kt-str-bound-code", plan.code || "");
			// Active portfolio links use plan_code; Draft successors use docname so Active is not resolved.
			var routeToken =
				plan.status === "Active" && plan.code
					? plan.code
					: plan.supersedes_plan_version
						? plan.id || planCode
						: plan.code || plan.id || planCode;
			$root.attr("data-kt-str-route-token", routeToken);

			bindPlanChrome($root, plan);
			$root.find('[data-kt-str-detail="plan_type"]').text(plan.plan_type || "—");
			var pe = plan.procuring_entity || {};
			$root
				.find('[data-kt-str-detail="procuring_entity"]')
				.text(pe.name || pe.code || "—");
			$root
				.find('[data-kt-str-detail="effective_period"]')
				.text(plan.effective_period_label || formatPeriod(plan.start_date, plan.end_date));
			$root
				.find('[data-kt-str-detail="version_status"]')
				.html(
					esc(String(plan.version_number != null ? plan.version_number : "—")) +
						' <span class="mx-2 text-outline-variant">•</span> ' +
						esc(plan.status || "")
				);
			var desc = plan.description || "";
			$root
				.find('[data-kt-str-detail="description"]')
				.text(desc ? (desc.charAt(0) === '"' ? desc : '"' + desc + '"') : "—");

			["programmes", "sub_programmes", "outcomes", "indicators", "targets"].forEach(function (k) {
				$root.find('[data-kt-str-count="' + k + '"]').text(String(c[k] || 0));
			});
			var cs = dto.commitments_summary || {};
			$root.find('[data-kt-str-commit-count="total"]').text(String(cs.total || 0));
			$root.find('[data-kt-str-commit-count="required"]').text(String(cs.required || 0));
			$root.find('[data-kt-str-commit-count="recommended"]').text(String(cs.recommended || 0));

			var attn = dto.attention_rows || [];
			var attnCount = dto.attention_count != null ? dto.attention_count : attn.length;
			$root
				.find("[data-kt-str-attention-badge]")
				.text(
					attnCount === 1
						? __("1 Required Action")
						: attnCount + " " + __("Required Actions")
				);
			$root.find("[data-kt-str-attention-tbody]").html(renderAttentionRows(attn));

			var lock = dto.lock || {};
			var $footer = $root.find("[data-kt-str-lock-footer]");
			if (lock.show) {
				$footer.removeClass("hidden").attr("aria-hidden", "false");
				$root.find("[data-kt-str-lock-message]").text(lock.message || "");
			} else {
				$footer.addClass("hidden").attr("aria-hidden", "true");
			}

			var $policy = $root.find("[data-kt-str-policy-note]");
			if (dto.show_policy_note) {
				$policy.removeClass("hidden");
			} else {
				$policy.addClass("hidden");
			}

			var nextVer = (parseInt(plan.version_number, 10) || 1) + 1;
			$root
				.find("[data-kt-str-successor-modal-copy]")
				.text(
					__(
						"This will create an 'In-Progress' draft version (v{0}) while preserving the current active plan.",
						[String(nextVer)]
					)
				);

			ensureStartStructureCta($root, plan, c, caps);

			$root.off("click.ktStrOvLive").on("click.ktStrOvLive", "[data-kt-str-action]", function (e) {
				var $el = $(this);
				var action = $el.attr("data-kt-str-action");
				var token = $root.attr("data-kt-str-route-token") || plan.code || planCode;
				if (action === "view-structure" || action === "start-plan-structure") {
					e.preventDefault();
					frappe.set_route("strategy-plan-structure", token);
					return;
				}
				if (action === "view-commitments") {
					e.preventDefault();
					frappe.set_route("strategy-plan-value-commitments", token);
					return;
				}
				if (
					action === "view-measurement" ||
					action === "submit-measurement" ||
					action === "review-measurement"
				) {
					e.preventDefault();
					var routeAttr = ($el.attr("data-kt-str-route") || "").split("/").filter(Boolean);
					var measPage =
						action === "submit-measurement"
							? "strategy-measurement-submit"
							: "strategy-measurement-verify";
					var tgtCode =
						$el.attr("data-target-code") ||
						kentender_strategy.alignment.FIXTURE_TARGET;
					if (routeAttr.length >= 3) {
						frappe.set_route(routeAttr[0], routeAttr[1], routeAttr[2]);
					} else if (routeAttr.length === 2 && routeAttr[0] === measPage) {
						// Legacy [page, target] → scope with current plan token
						frappe.set_route(measPage, token, routeAttr[1]);
					} else {
						frappe.set_route(measPage, token, tgtCode);
					}
					return;
				}
				if (action === "confirm-successor") {
					e.preventDefault();
					e.stopImmediatePropagation();
					call("create_successor_version", { plan_version: plan.id }).then(function (res) {
						if (!res || !res.ok || !res.plan) {
							frappe.show_alert({
								message: __("Could not create successor version"),
								indicator: "red",
							});
							return;
						}
						$root.find('[data-testid="kt-str-successor-modal"]').attr("hidden", "hidden").addClass("hidden");
						frappe.show_alert({
							message: __("Successor draft v{0} created", [String(res.plan.version_number)]),
							indicator: "green",
						});
						frappe.set_route("strategy-plan-overview", res.plan.id);
					}).catch(function () {
						frappe.show_alert({
							message: __("Could not create successor version"),
							indicator: "red",
						});
					});
				}
			});

			return dto;
		});
	}

	var STRUCTURE_DEPTH_PL = ["", "pl-8", "pl-14", "pl-20", "pl-28"];
	var STRUCTURE_TYPE_META = {
		Programme: { tag: "PROG", label: "Programme", badge: "bg-primary text-on-primary" },
		SubProgramme: { tag: "SUB-P", label: "Sub-programme", badge: "bg-secondary text-on-secondary" },
		StrategicOutcome: { tag: "OUT", label: "Strategic Outcome", badge: "bg-tertiary text-on-tertiary" },
		PerformanceIndicator: {
			tag: "IND",
			label: "Performance Indicator",
			badge: "bg-surface-tint text-on-primary",
		},
		PerformanceTarget: {
			tag: "TGT",
			label: "Performance Target",
			badge: "border border-outline text-outline",
		},
	};
	var STRUCTURE_CHILD_TYPES = {
		Programme: [
			{ type: "SubProgramme", label: "Sub-programme" },
			{ type: "StrategicOutcome", label: "Strategic Outcome" },
		],
		SubProgramme: [{ type: "StrategicOutcome", label: "Strategic Outcome" }],
		StrategicOutcome: [{ type: "PerformanceIndicator", label: "Indicator" }],
		PerformanceIndicator: [{ type: "PerformanceTarget", label: "Performance Target" }],
		PerformanceTarget: [],
	};

	function flattenTree(nodes, out) {
		out = out || [];
		(nodes || []).forEach(function (n) {
			out.push(n);
			flattenTree(n.children, out);
		});
		return out;
	}

	function countTreeWarnings(nodes) {
		var n = 0;
		flattenTree(nodes).forEach(function (node) {
			n += (node.warnings || []).length;
		});
		return n;
	}

	function structureTypeLabel(type) {
		return (STRUCTURE_TYPE_META[type] && STRUCTURE_TYPE_META[type].label) || type || "";
	}

	function renderTreeNodes(nodes, depth, selectedId, collapsed) {
		depth = depth || 0;
		collapsed = collapsed || {};
		var pl = STRUCTURE_DEPTH_PL[Math.min(depth, STRUCTURE_DEPTH_PL.length - 1)] || "";
		return (nodes || [])
			.map(function (n) {
				var meta = STRUCTURE_TYPE_META[n.type] || {
					tag: "?",
					badge: "bg-surface-container text-on-surface-variant",
				};
				var hasKids = (n.children || []).length > 0;
				var isCollapsed = !!collapsed[n.id];
				var selected = selectedId && n.id === selectedId;
				var warnHtml = "";
				if ((n.warnings || []).length) {
					warnHtml =
						'<div class="mt-1 flex items-center gap-1 text-error text-xs font-medium">' +
						'<span class="material-symbols-outlined text-[14px]">warning</span>' +
						esc(n.warnings[0]) +
						"</div>";
				}
				var rowCls =
					"flex items-start gap-2 p-2 rounded cursor-pointer transition-colors group kt-str-tree-node " +
					pl +
					(selected
						? " bg-primary-fixed border-l-2 border-primary"
						: " hover:bg-surface-container") +
					(warnHtml && !selected ? " hover:bg-error-container/20" : "");
				var chevron = hasKids
					? isCollapsed
						? "arrow_right"
						: "arrow_drop_down"
					: "arrow_drop_down";
				var chevronCls = hasKids
					? selected
						? "text-primary"
						: "text-outline"
					: "text-outline opacity-0";
				var codeCls =
					selected || n.type === "Programme" || n.type === "StrategicOutcome"
						? "font-data-mono text-xs text-primary font-bold"
						: "font-data-mono text-xs text-on-surface-variant";
				var titleCls =
					n.type === "Programme" || n.type === "SubProgramme" || n.type === "StrategicOutcome"
						? "font-medium text-sm text-on-surface" + (selected ? " text-primary" : "")
						: "text-sm text-on-surface";
				var html =
					'<div class="' +
					rowCls +
					'" data-node-id="' +
					esc(n.id) +
					'" data-node-type="' +
					esc(n.type) +
					'" data-node-code="' +
					esc(n.code || "") +
					'" data-kt-str-action="select-node" tabindex="0" role="treeitem">' +
					'<span class="material-symbols-outlined ' +
					chevronCls +
					' mt-0.5 text-sm" data-kt-str-action="toggle-node">' +
					chevron +
					"</span>" +
					'<div class="flex-1">' +
					'<div class="flex items-center gap-2 mb-1">' +
					'<span class="' +
					meta.badge +
					' text-[10px] uppercase font-bold px-1.5 py-0.5 rounded tracking-wider">' +
					esc(meta.tag) +
					"</span>" +
					'<span class="' +
					codeCls +
					'">' +
					esc(n.code || "") +
					"</span>" +
					"</div>" +
					'<div class="' +
					titleCls +
					'">' +
					esc(n.name || "") +
					"</div>" +
					warnHtml +
					"</div></div>";
				if (hasKids && !isCollapsed) {
					html += renderTreeNodes(n.children, depth + 1, selectedId, collapsed);
				}
				return html;
			})
			.join("");
	}

	function fieldInput(name, label, value, opts) {
		opts = opts || {};
		var type = opts.type || "text";
		var req = opts.required ? " required" : "";
		var mono = opts.mono ? " font-data-mono" : "";
		var labelHtml =
			'<label class="font-label-caps text-label-caps text-on-surface-variant uppercase">' +
			esc(label) +
			"</label>";
		if (opts.codeDisplay) {
			return (
				'<div class="space-y-1" data-kt-str-drawer-field="' +
				esc(name) +
				'">' +
				labelHtml +
				'<div class="font-data-mono text-data-mono bg-surface-container px-3 py-2 rounded border border-outline-variant text-on-surface-variant">' +
				esc(value || "") +
				"</div>" +
				'<input type="hidden" name="' +
				esc(name) +
				'" value="' +
				esc(value || "") +
				'"/>' +
				"</div>"
			);
		}
		if (type === "textarea") {
			return (
				'<div class="space-y-1" data-kt-str-drawer-field="' +
				esc(name) +
				'">' +
				labelHtml +
				'<textarea name="' +
				esc(name) +
				'" class="w-full border border-outline-variant rounded-lg p-3 text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none min-h-[80px]"' +
				req +
				">" +
				esc(value || "") +
				"</textarea></div>"
			);
		}
		if (type === "select") {
			var optsHtml = (opts.options || [])
				.map(function (o) {
					var v = typeof o === "string" ? o : o.value;
					var lab = typeof o === "string" ? o : o.label;
					return (
						'<option value="' +
						esc(v) +
						'"' +
						(String(value || "") === String(v) ? " selected" : "") +
						">" +
						esc(lab) +
						"</option>"
					);
				})
				.join("");
			return (
				'<div class="space-y-1" data-kt-str-drawer-field="' +
				esc(name) +
				'">' +
				labelHtml +
				'<select name="' +
				esc(name) +
				'" class="w-full border border-outline-variant rounded-lg p-2 text-body-md focus:border-primary outline-none"' +
				req +
				">" +
				optsHtml +
				"</select></div>"
			);
		}
		if (opts.unitSuffix != null) {
			return (
				'<div class="space-y-1" data-kt-str-drawer-field="' +
				esc(name) +
				'">' +
				labelHtml +
				'<div class="flex">' +
				'<input name="' +
				esc(name) +
				'" type="text" class="flex-1 border border-outline-variant rounded-l-lg p-2 text-body-md font-data-mono focus:border-primary outline-none" value="' +
				esc(value == null ? "" : value) +
				'"' +
				req +
				"/>" +
				'<span class="bg-surface-container border border-l-0 border-outline-variant rounded-r-lg px-3 flex items-center text-on-surface-variant font-medium">' +
				esc(opts.unitSuffix) +
				"</span></div></div>"
			);
		}
		return (
			'<div class="space-y-1" data-kt-str-drawer-field="' +
			esc(name) +
			'">' +
			labelHtml +
			'<input name="' +
			esc(name) +
			'" type="' +
			esc(type) +
			'" class="w-full border border-outline-variant rounded-lg p-2 text-body-md' +
			mono +
			' focus:border-primary outline-none" value="' +
			esc(value == null ? "" : value) +
			'"' +
			req +
			(opts.readonly ? " readonly" : "") +
			"/></div>"
		);
	}

	function renderDrawerForm(type, fields, unit, mode) {
		fields = fields || {};
		mode = mode || "add";
		var codeOpts = { required: true, mono: true, codeDisplay: mode === "edit" && !!fields.code };
		if (type === "Programme" || type === "SubProgramme") {
			return (
				fieldInput("code", type === "SubProgramme" ? "Sub-programme code" : "Programme code", fields.code, codeOpts) +
				fieldInput("title", "Title", fields.title, { required: true }) +
				fieldInput("description", "Description", fields.description, { type: "textarea" }) +
				fieldInput("responsible_function", "Responsible function", fields.responsible_function, {
					required: true,
				})
			);
		}
		if (type === "StrategicOutcome") {
			return (
				fieldInput("code", "Outcome code", fields.code, codeOpts) +
				fieldInput("title", "Title", fields.title, { required: true }) +
				fieldInput("description", "Description", fields.description, { type: "textarea" }) +
				fieldInput("responsible_function", "Responsible function", fields.responsible_function, {
					required: true,
				}) +
				fieldInput("executive_owner", "Executive owner", fields.executive_owner)
			);
		}
		if (type === "PerformanceIndicator") {
			return (
				fieldInput("code", "Indicator code", fields.code, codeOpts) +
				fieldInput("title", "Title", fields.title, { required: true }) +
				fieldInput("definition", "Definition", fields.definition, {
					type: "textarea",
					required: true,
				}) +
				'<div class="grid grid-cols-2 gap-4">' +
				fieldInput("measurement_type", "Measurement type", fields.measurement_type || "Percentage", {
					type: "select",
					required: true,
					options: [
						"Numeric",
						"Percentage",
						"Currency",
						"Duration",
						"Count",
						"Milestone",
						"Boolean",
					],
				}) +
				fieldInput("unit", "Unit", fields.unit || unit || "%") +
				"</div>" +
				fieldInput(
					"measurement_frequency",
					"Measurement frequency",
					fields.measurement_frequency || "Monthly",
					{
						type: "select",
						required: true,
						options: ["Monthly", "Quarterly", "Annual", "Due date", "Plan end"],
					}
				) +
				fieldInput("data_source", "Data source", fields.data_source, { required: true }) +
				fieldInput("responsible_function", "Responsible function", fields.responsible_function, {
					required: true,
				})
			);
		}
		// PerformanceTarget — Stitch plan_structure_add_performance_target_drawer
		var unitLabel = unit || fields.unit || "%";
		return (
			fieldInput("code", "Target code", fields.code, codeOpts) +
			fieldInput("title", "Target title", fields.title, { type: "textarea", required: true }) +
			'<div class="grid grid-cols-2 gap-4">' +
			fieldInput(
				"comparison_direction",
				"Comparison direction",
				fields.comparison_direction || "At least",
				{
					type: "select",
					required: true,
					options: [
						"At least",
						"At most",
						"Equal to",
						"Increase to",
						"Reduce to",
						"Achieve by date",
					],
				}
			) +
			fieldInput("target_numeric", "Target value", fields.target_numeric, {
				required: true,
				unitSuffix: unitLabel,
			}) +
			"</div>" +
			'<div class="grid grid-cols-2 gap-4">' +
			fieldInput("baseline_status", "Baseline status", fields.baseline_status || "Known", {
				type: "select",
				required: true,
				options: ["Known", "To be established", "Not applicable"],
			}) +
			fieldInput("baseline_numeric", "Baseline value", fields.baseline_numeric, { mono: true }) +
			"</div>" +
			'<div class="grid grid-cols-2 gap-4">' +
			fieldInput("baseline_as_of", "Baseline as at", fields.baseline_as_of, { type: "date" }) +
			fieldInput("tolerance_value", "Tolerance", fields.tolerance_value, { mono: true }) +
			"</div>" +
			fieldInput("baseline_source", "Baseline source", fields.baseline_source) +
			'<div class="grid grid-cols-2 gap-4">' +
			fieldInput("period_start", "Period start", fields.period_start, {
				type: "date",
				required: true,
			}) +
			fieldInput("period_end", "Period end", fields.period_end, { type: "date", required: true }) +
			"</div>" +
			fieldInput("benefit_owner", "Benefit owner", fields.benefit_owner, { required: true }) +
			fieldInput(
				"measurement_verifier",
				"Measurement verifier",
				fields.measurement_verifier || "Administrator",
				{ required: true }
			)
		);
	}

	function renderStructureDetail(node, editable, linkedNames) {
		if (!node) {
			return (
				'<div class="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm p-card-padding text-on-surface-variant text-sm">' +
				esc(__("Select a structure item to view details.")) +
				"</div>"
			);
		}
		var meta = STRUCTURE_TYPE_META[node.type] || { label: node.type, badge: "" };
		var f = node.fields || {};
		var desc = f.description || node.description || f.definition || "";
		var kids = node.children || [];
		var indCount = 0;
		var tgtCount = 0;
		if (node.type === "StrategicOutcome") {
			indCount = kids.length;
			kids.forEach(function (c) {
				tgtCount += (c.children || []).length;
			});
		} else if (node.type === "PerformanceIndicator") {
			tgtCount = kids.length;
		}
		var childTypes = STRUCTURE_CHILD_TYPES[node.type] || [];
		var addLabel =
			childTypes.length === 1
				? __("Add {0}", [childTypes[0].label])
				: childTypes.length
					? __("Add child")
					: "";
		var actions = "";
		if (editable) {
			actions =
				'<div class="flex gap-2">' +
				'<button type="button" class="p-2 text-on-surface-variant hover:text-primary hover:bg-primary-fixed rounded transition-colors" title="Edit Item" data-kt-str-action="edit-structure-node">' +
				'<span class="material-symbols-outlined">edit</span></button>' +
				'<button type="button" class="p-2 text-on-surface-variant hover:text-error hover:bg-error-container rounded transition-colors" title="Delete Item" data-kt-str-action="delete-structure-node">' +
				'<span class="material-symbols-outlined">delete</span></button></div>';
		}
		var metaGrid = "";
		if (node.type === "StrategicOutcome" || node.type === "Programme" || node.type === "SubProgramme") {
			metaGrid =
				'<div class="grid grid-cols-2 gap-4">' +
				'<div class="bg-surface p-3 rounded-lg border border-surface-variant">' +
				'<h3 class="font-label-caps text-[10px] text-on-surface-variant mb-1 uppercase">Responsible Function</h3>' +
				'<div class="text-sm font-medium text-on-surface">' +
				esc(f.responsible_function || node.responsible_function || "—") +
				"</div></div>" +
				'<div class="bg-surface p-3 rounded-lg border border-surface-variant">' +
				'<h3 class="font-label-caps text-[10px] text-on-surface-variant mb-1 uppercase">Executive Owner</h3>' +
				'<div class="text-sm font-medium text-on-surface">' +
				esc(f.executive_owner || node.executive_owner || "—") +
				"</div></div></div>";
		} else if (node.type === "PerformanceIndicator") {
			metaGrid =
				'<div class="grid grid-cols-2 gap-4">' +
				'<div class="bg-surface p-3 rounded-lg border border-surface-variant">' +
				'<h3 class="font-label-caps text-[10px] text-on-surface-variant mb-1 uppercase">Measurement type</h3>' +
				'<div class="text-sm font-medium text-on-surface">' +
				esc(f.measurement_type || "—") +
				"</div></div>" +
				'<div class="bg-surface p-3 rounded-lg border border-surface-variant">' +
				'<h3 class="font-label-caps text-[10px] text-on-surface-variant mb-1 uppercase">Unit</h3>' +
				'<div class="text-sm font-medium text-on-surface">' +
				esc(f.unit || "—") +
				"</div></div></div>";
		} else if (node.type === "PerformanceTarget") {
			metaGrid =
				'<div class="grid grid-cols-2 gap-4">' +
				'<div class="bg-surface p-3 rounded-lg border border-surface-variant">' +
				'<h3 class="font-label-caps text-[10px] text-on-surface-variant mb-1 uppercase">Target value</h3>' +
				'<div class="text-sm font-medium text-on-surface font-data-mono">' +
				esc(
					f.comparison_direction
						? f.comparison_direction + " " + (f.target_numeric != null ? f.target_numeric : "")
						: f.target_numeric != null
							? f.target_numeric
							: "—"
				) +
				"</div></div>" +
				'<div class="bg-surface p-3 rounded-lg border border-surface-variant">' +
				'<h3 class="font-label-caps text-[10px] text-on-surface-variant mb-1 uppercase">Period</h3>' +
				'<div class="text-sm font-medium text-on-surface">' +
				esc(formatPeriod(f.period_start, f.period_end)) +
				"</div></div></div>";
		}
		var linksHtml = "";
		if (node.type === "StrategicOutcome") {
			var chips =
				(linkedNames || []).length ?
					linkedNames
						.map(function (nm) {
							return (
								'<span class="bg-secondary-fixed text-on-secondary-fixed-variant px-3 py-1.5 rounded-full text-xs font-medium border border-secondary-fixed-dim">' +
								esc(nm) +
								"</span>"
							);
						})
						.join("")
				:	'<span class="text-on-surface-variant text-xs">' + esc(__("No linked commitments")) + "</span>";
			linksHtml =
				'<div><h3 class="font-label-caps text-label-caps text-on-surface-variant mb-2 uppercase">Linked Commitments</h3>' +
				'<div class="flex flex-wrap gap-2">' +
				chips +
				"</div></div><hr class=\"border-outline-variant\"/>";
		}
		var childSummary = "";
		if (node.type === "StrategicOutcome" || node.type === "PerformanceIndicator" || node.type === "Programme") {
			var summaryBits = "";
			if (node.type === "StrategicOutcome") {
				summaryBits =
					'<div class="flex items-center gap-2 text-sm text-on-surface bg-surface-container px-3 py-1 rounded">' +
					'<span class="material-symbols-outlined text-[18px] text-surface-tint">analytics</span>' +
					esc(String(indCount) + (indCount === 1 ? " Indicator" : " Indicators")) +
					"</div>" +
					'<div class="flex items-center gap-2 text-sm text-on-surface bg-surface-container px-3 py-1 rounded">' +
					'<span class="material-symbols-outlined text-[18px] text-outline">track_changes</span>' +
					esc(String(tgtCount) + (tgtCount === 1 ? " Target" : " Targets")) +
					"</div>";
			} else if (node.type === "PerformanceIndicator") {
				summaryBits =
					'<div class="flex items-center gap-2 text-sm text-on-surface bg-surface-container px-3 py-1 rounded">' +
					'<span class="material-symbols-outlined text-[18px] text-outline">track_changes</span>' +
					esc(String(tgtCount) + (tgtCount === 1 ? " Target" : " Targets")) +
					"</div>";
			} else {
				summaryBits =
					'<div class="flex items-center gap-2 text-sm text-on-surface bg-surface-container px-3 py-1 rounded">' +
					esc(String(kids.length) + (kids.length === 1 ? " child" : " children")) +
					"</div>";
			}
			var addBtn =
				editable && addLabel
					? '<button type="button" class="bg-primary text-on-primary px-4 py-2 rounded-lg font-medium hover:bg-primary-container transition-colors flex items-center gap-2 text-sm" data-kt-str-action="add-structure-item" data-kt-str-child-type="' +
						esc(childTypes[0] ? childTypes[0].type : "") +
						'"><span class="material-symbols-outlined text-sm">add</span>' +
						esc(addLabel) +
						"</button>"
					: "";
			childSummary =
				'<div><h3 class="font-label-caps text-label-caps text-on-surface-variant mb-3 uppercase">Child Structure Summary</h3>' +
				'<div class="flex items-center gap-4 mb-4">' +
				summaryBits +
				"</div>" +
				'<div class="flex gap-3 mt-4">' +
				addBtn +
				"</div></div>";
		}
		return (
			'<div class="max-w-3xl mx-auto bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm">' +
			'<div class="p-card-padding border-b border-outline-variant bg-surface-container-low rounded-t-xl flex justify-between items-start">' +
			"<div><div class=\"flex items-center gap-2 mb-2\">" +
			'<span class="' +
			meta.badge +
			' text-[10px] uppercase font-bold px-2 py-1 rounded tracking-wider">' +
			esc(meta.label) +
			"</span>" +
			'<span class="font-data-mono text-sm text-on-surface-variant bg-surface-container px-2 py-1 rounded">' +
			esc(node.code || "") +
			"</span></div>" +
			'<h2 class="font-headline-md text-headline-md text-primary">' +
			esc(node.name || "") +
			"</h2></div>" +
			actions +
			"</div>" +
			'<div class="p-card-padding space-y-6">' +
			(desc
				? "<div><h3 class=\"font-label-caps text-label-caps text-on-surface-variant mb-2 uppercase\">Description</h3>" +
					'<p class="text-body-md text-on-surface bg-surface p-3 rounded-lg border border-surface-variant">' +
					esc(desc) +
					"</p></div>"
				: "") +
			metaGrid +
			linksHtml +
			childSummary +
			"</div></div>"
		);
	}

	function closeStructureDrawerLive($host) {
		$host.find('[data-testid="kt-str-structure-drawer"]').remove();
		$host.find('[data-testid="kt-str-structure-drawer-overlay"]').remove();
	}

	function openStructureDrawerLive($host, opts) {
		opts = opts || {};
		closeStructureDrawerLive($host);
		var fx = kentender_strategy.ui_fixtures || {};
		if (!fx.structure_drawer) {
			return null;
		}
		var $tmp = $("<div/>").html(fx.structure_drawer());
		var $drawer = $tmp.find('[data-testid="kt-str-structure-drawer"]').first();
		var $overlay = $drawer.length
			? $drawer.find('[data-testid="kt-str-structure-drawer-overlay"]').first()
			: $tmp.find('[data-testid="kt-str-structure-drawer-overlay"]').first();
		if (!$overlay.length) {
			return null;
		}
		$overlay.attr("data-dismiss", "explicit-only");
		var typeLabel = structureTypeLabel(opts.type);
		var title =
			opts.type === "PerformanceTarget"
				? opts.mode === "edit"
					? __("Edit performance target")
					: __("Add performance target")
				: opts.mode === "edit"
					? __("Edit {0}", [typeLabel])
					: __("Add {0}", [typeLabel]);
		$overlay.find("[data-kt-str-drawer-title]").text(title);
		$overlay.find("[data-kt-str-drawer-path]").text(opts.path || "");
		$overlay
			.find("[data-kt-str-drawer-form]")
			.html(renderDrawerForm(opts.type, opts.fields || {}, opts.unit, opts.mode || "add"));
		var saveLabel = opts.type === "PerformanceTarget" ? __("Save target") : __("Save");
		$overlay.find("[data-kt-str-drawer-save]").text(saveLabel);
		$overlay.attr("data-kt-str-drawer-type", opts.type || "");
		$overlay.attr("data-kt-str-drawer-mode", opts.mode || "add");
		if (opts.nodeId) {
			$overlay.attr("data-kt-str-drawer-node-id", opts.nodeId);
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
				e.preventDefault();
			}
		});
		return $overlay;
	}

	function readDrawerFields($overlay) {
		var data = {};
		$overlay.find("[data-kt-str-drawer-form] [name]").each(function () {
			var $el = $(this);
			var name = $el.attr("name");
			var val = $el.val();
			if (val !== "" && val != null) {
				data[name] = val;
			}
		});
		return data;
	}

	function bindStructure($root, planCode) {
		var state = {
			treeDto: null,
			selectedId: null,
			collapsed: {},
			commitments: [],
			editable: false,
			routeToken: planCode,
		};
		var $host = $root.closest('[data-testid="kt-cl-page-body"]').length
			? $root.closest('[data-testid="kt-cl-page-body"]')
			: $root.parent();

		function nodeById(id) {
			if (!id || !state.treeDto) {
				return null;
			}
			return (
				flattenTree(state.treeDto.tree).find(function (n) {
					return n.id === id;
				}) || null
			);
		}

		function pathForNode(node) {
			if (!node || !state.treeDto) {
				return "";
			}
			var parts = [];
			function walk(nodes, trail) {
				for (var i = 0; i < (nodes || []).length; i++) {
					var n = nodes[i];
					var next = trail.concat([n.name || n.code]);
					if (n.id === node.id) {
						parts = next;
						return true;
					}
					if (walk(n.children, next)) {
						return true;
					}
				}
				return false;
			}
			walk(state.treeDto.tree, []);
			return parts.slice(0, -1).join(" / ");
		}

		function linkedNamesForOutcome(outcomeId) {
			var names = [];
			(state.commitments || []).forEach(function (c) {
				var links = c.links || [];
				var hit = links.some(function (l) {
					return l.link_type === "Strategic Outcome" && l.linked_outcome === outcomeId;
				});
				if (hit) {
					var obj = c.objective || {};
					names.push(obj.name || obj.code || c.id);
				}
			});
			return names;
		}

		function paint() {
			if (!state.treeDto) {
				return;
			}
			var tree = state.treeDto.tree || [];
			var $treeHost = $root.find("[data-kt-str-structure-tree-host]");
			if (!tree.length) {
				$treeHost.html(
					'<div class="p-4 text-sm text-on-surface-variant" data-kt-str-structure-empty>' +
						esc(__("No structure yet. Add a Programme to begin.")) +
						"</div>"
				);
			} else {
				$treeHost.html(renderTreeNodes(tree, 0, state.selectedId, state.collapsed));
			}
			var selected = nodeById(state.selectedId);
			var links = selected && selected.type === "StrategicOutcome" ? linkedNamesForOutcome(selected.id) : [];
			$root
				.find("[data-kt-str-structure-detail-host]")
				.html(renderStructureDetail(selected, state.editable, links));
			var $addBar = $root.find("[data-kt-str-structure-add-bar]");
			if (state.editable) {
				$addBar.removeClass("hidden");
				var addLabel = !tree.length
					? __("Add Programme")
					: selected && (STRUCTURE_CHILD_TYPES[selected.type] || []).length
						? __("Add Structure Item")
						: __("Add Structure Item");
				$addBar.find("[data-kt-str-action='add-structure-item']").html(
					'<span class="material-symbols-outlined text-sm">add</span>' + esc(addLabel)
				);
			} else {
				$addBar.addClass("hidden");
			}
			var $editPlan = $root.find("[data-kt-str-structure-edit-plan]");
			if (state.editable) {
				$editPlan.removeClass("hidden");
			} else {
				$editPlan.addClass("hidden");
			}
		}

		function paintIssues(issueCount) {
			var count = parseInt(issueCount, 10) || 0;
			var $banner = $root.find("[data-kt-str-structure-issues]");
			if (count > 0) {
				$banner
					.removeClass("hidden")
					.removeAttr("hidden")
					.attr("aria-hidden", "false");
				var label =
					count === 1
						? __("1 structure issue to resolve before submission")
						: __("{0} structure issues to resolve before submission", [String(count)]);
				$banner.find("[data-kt-str-structure-issues-label]").text(label);
			} else {
				$banner
					.addClass("hidden")
					.attr("hidden", "hidden")
					.attr("aria-hidden", "true");
				$banner.find("[data-kt-str-structure-issues-label]").text("");
			}
		}

		function defaultChildType(parent) {
			if (!parent) {
				return "Programme";
			}
			var opts = STRUCTURE_CHILD_TYPES[parent.type] || [];
			return opts.length ? opts[0].type : null;
		}

		function parentLinksFor(type, parent) {
			var links = {};
			if (!parent) {
				return links;
			}
			if (type === "SubProgramme" && parent.type === "Programme") {
				links.programme = parent.id;
			} else if (type === "StrategicOutcome") {
				if (parent.type === "SubProgramme") {
					links.sub_programme = parent.id;
					links.programme = (parent.fields && parent.fields.programme) || null;
				} else if (parent.type === "Programme") {
					links.programme = parent.id;
				}
			} else if (type === "PerformanceIndicator" && parent.type === "StrategicOutcome") {
				links.strategic_outcome = parent.id;
			} else if (type === "PerformanceTarget" && parent.type === "PerformanceIndicator") {
				links.performance_indicator = parent.id;
			}
			return links;
		}

		function openAddDrawer(forcedType) {
			if (!state.editable) {
				return;
			}
			var parent = nodeById(state.selectedId);
			var type = forcedType || defaultChildType(parent);
			if (!type) {
				frappe.show_alert({ message: __("No valid child type for this node"), indicator: "orange" });
				return;
			}
			if (type !== "Programme" && !parent) {
				frappe.show_alert({ message: __("Select a parent node first"), indicator: "orange" });
				return;
			}
			var pathParts = [];
			if (parent) {
				var base = pathForNode(parent);
				if (base) {
					pathParts.push(base);
				}
				pathParts.push(parent.name || parent.code || "");
			}
			openStructureDrawerLive($host, {
				mode: "add",
				type: type,
				path: pathParts.filter(Boolean).join(" / "),
				fields: {},
				unit: parent && parent.fields ? parent.fields.unit : null,
			});
			$host.data("kt-str-drawer-parent", parent);
			$host.data("kt-str-drawer-type", type);
		}

		function openEditDrawer() {
			if (!state.editable) {
				return;
			}
			var node = nodeById(state.selectedId);
			if (!node) {
				return;
			}
			var fields = Object.assign({}, node.fields || {}, { code: node.code, title: node.name });
			openStructureDrawerLive($host, {
				mode: "edit",
				type: node.type,
				nodeId: node.id,
				path: pathForNode(node),
				fields: fields,
				unit: fields.unit || node.unit,
			});
			$host.data("kt-str-drawer-parent", null);
			$host.data("kt-str-drawer-type", node.type);
		}

		function saveDrawer() {
			var $overlay = $host.find('[data-testid="kt-str-structure-drawer-overlay"]');
			if (!$overlay.length) {
				return;
			}
			var type = $overlay.attr("data-kt-str-drawer-type") || $host.data("kt-str-drawer-type");
			var mode = $overlay.attr("data-kt-str-drawer-mode") || "add";
			var fields = readDrawerFields($overlay);
			var plan = state.treeDto.plan;
			var payload = {
				type: type,
				plan_version: plan.id,
				code: fields.code,
				title: fields.title,
			};
			Object.keys(fields).forEach(function (k) {
				if (k !== "code" && k !== "title") {
					payload[k] = fields[k];
				}
			});
			if (mode === "edit") {
				payload.id = $overlay.attr("data-kt-str-drawer-node-id");
			} else {
				var parent = $host.data("kt-str-drawer-parent");
				Object.assign(payload, parentLinksFor(type, parent));
			}
			if (type === "PerformanceTarget" && !payload.status) {
				payload.status = "Active";
			}
			call("upsert_structure_node", { payload: payload })
				.then(function (res) {
					closeStructureDrawerLive($host);
					frappe.show_alert({ message: __("Structure item saved"), indicator: "green" });
					return reload(res && res.id);
				})
				.catch(function () {
					frappe.show_alert({ message: __("Could not save structure item"), indicator: "red" });
				});
		}

		function deleteSelected() {
			if (!state.editable) {
				return;
			}
			var node = nodeById(state.selectedId);
			if (!node) {
				return;
			}
			frappe.confirm(__("Delete {0}?", [node.code || node.name]), function () {
				call("delete_structure_node", { node_type: node.type, name: node.id })
					.then(function () {
						frappe.show_alert({ message: __("Deleted"), indicator: "green" });
						state.selectedId = null;
						return reload(null);
					})
					.catch(function () {
						frappe.show_alert({
							message: __("Could not delete (check children or measurements)"),
							indicator: "red",
						});
					});
			});
		}

		function reload(selectId) {
			var args = { plan_code: state.routeToken || planCode };
			return Promise.all([
				call("get_strategy_tree", args),
				call("list_plan_value_commitments", args).catch(function () {
					return { rows: [] };
				}),
				call("get_plan_readiness_api", args).catch(function () {
					return null;
				}),
			]).then(function (results) {
				var tree = results[0];
				if (!tree || !tree.plan) {
					return;
				}
				state.treeDto = tree;
				var commitmentsDto = results[1] || {};
				state.commitments = Array.isArray(commitmentsDto)
					? commitmentsDto
					: commitmentsDto.rows || [];
				state.editable = !!(tree.capabilities && tree.capabilities.editable);
				var plan = tree.plan;
				$root.attr("data-kt-str-live", "1");
				$root.attr("data-kt-str-plan-id", plan.id || "");
				$root.attr("data-kt-str-bound-code", plan.code || "");
				state.routeToken =
					plan.status === "Active" && plan.code
						? plan.code
						: plan.supersedes_plan_version
							? plan.id || planCode
							: plan.code || plan.id || planCode;
				$root.attr("data-kt-str-route-token", state.routeToken);
				$root.attr("data-kt-str-structure-editable", state.editable ? "1" : "0");
				bindPlanChrome($root, plan);
				if (selectId) {
					state.selectedId = selectId;
				} else if (state.selectedId && !nodeById(state.selectedId)) {
					state.selectedId = null;
				}
				if (!state.selectedId && (tree.tree || []).length) {
					// Prefer first outcome for Stitch-like detail, else first node.
					var flat = flattenTree(tree.tree);
					var outcome = flat.find(function (n) {
						return n.type === "StrategicOutcome";
					});
					state.selectedId = (outcome || flat[0]).id;
				}
				paint();
				var warnCount = countTreeWarnings(tree.tree);
				var ready = results[2];
				var structIssues = 0;
				if (ready && ready.issues) {
					structIssues = ready.issues.filter(function (i) {
						return (
							i.group === "Structure" ||
							(i.edit_location || "").indexOf("structure") >= 0
						);
					}).length;
				}
				paintIssues(Math.max(warnCount, structIssues));
				return tree;
			});
		}

		$root.off("click.ktStrStructLive").on("click.ktStrStructLive", "[data-kt-str-action]", function (e) {
			var $el = $(this);
			var action = $el.attr("data-kt-str-action");
			if (action === "toggle-node") {
				e.preventDefault();
				e.stopPropagation();
				var $row = $el.closest("[data-node-id]");
				var tid = $row.attr("data-node-id");
				if (tid) {
					state.collapsed[tid] = !state.collapsed[tid];
					paint();
				}
				return;
			}
			if (action === "select-node") {
				e.preventDefault();
				var sid = $el.closest("[data-node-id]").attr("data-node-id") || $el.attr("data-node-id");
				if (sid) {
					state.selectedId = sid;
					paint();
				}
				return;
			}
			if (action === "add-structure-item") {
				e.preventDefault();
				openAddDrawer($el.attr("data-kt-str-child-type") || null);
				return;
			}
			if (action === "edit-structure-node") {
				e.preventDefault();
				openEditDrawer();
				return;
			}
			if (action === "delete-structure-node") {
				e.preventDefault();
				deleteSelected();
				return;
			}
			if (action === "expand-all") {
				e.preventDefault();
				state.collapsed = {};
				paint();
				return;
			}
			if (action === "resolve-structure-issues") {
				e.preventDefault();
				frappe.set_route("strategy-plan-review", state.routeToken || planCode);
				return;
			}
			if (action === "edit-plan-details") {
				e.preventDefault();
				frappe.set_route("strategy-plan-overview", state.routeToken || planCode);
				return;
			}
			if (action === "close-drawer") {
				e.preventDefault();
				closeStructureDrawerLive($host);
				return;
			}
			if (action === "save-structure-node") {
				e.preventDefault();
				saveDrawer();
			}
		});

		$root.off("keydown.ktStrStructLive").on("keydown.ktStrStructLive", "[data-node-id]", function (e) {
			var flat = flattenTree((state.treeDto && state.treeDto.tree) || []).filter(function (n) {
				return !state.collapsed[n.id];
			});
			// Visible-ish: skip children of collapsed ancestors
			var visible = [];
			function walk(nodes) {
				(nodes || []).forEach(function (n) {
					visible.push(n);
					if (!state.collapsed[n.id]) {
						walk(n.children);
					}
				});
			}
			walk((state.treeDto && state.treeDto.tree) || []);
			var idx = visible.findIndex(function (n) {
				return n.id === state.selectedId;
			});
			if (e.key === "ArrowDown" && idx < visible.length - 1) {
				e.preventDefault();
				state.selectedId = visible[idx + 1].id;
				paint();
			} else if (e.key === "ArrowUp" && idx > 0) {
				e.preventDefault();
				state.selectedId = visible[idx - 1].id;
				paint();
			} else if (e.key === "Enter") {
				e.preventDefault();
				paint();
			}
		});

		$host.off("click.ktStrDrawerClose").on("click.ktStrDrawerClose", "[data-kt-str-action='close-drawer']", function (e) {
			e.preventDefault();
			closeStructureDrawerLive($host);
		});
		$host.off("click.ktStrDrawerSave").on("click.ktStrDrawerSave", "[data-kt-str-action='save-structure-node']", function (e) {
			e.preventDefault();
			saveDrawer();
		});

		return reload(null);
	}

	function renderPvoCatalogueRows(rows) {
		if (!(rows || []).length) {
			return (
				'<tr data-kt-str-empty="1"><td class="py-6 px-4 text-body-md text-on-surface-variant" colspan="8">' +
				esc(__("No public-value objectives match the current filters.")) +
				"</td></tr>"
			);
		}
		return rows
			.map(function (r) {
				var status = r.status || "Active";
				var active = String(status).toLowerCase() === "active";
				var pillCls = active
					? "bg-status-available/10 text-status-available border border-status-available/20"
					: "bg-status-reserved/10 text-status-reserved border border-status-reserved/20";
				var dotCls = active ? "bg-status-available" : "bg-status-reserved";
				var actionLabel = active ? __("View") : __("Review");
				var actionCls = active
					? "text-primary hover:text-primary-container"
					: "text-secondary hover:text-secondary-container";
				return (
					'<tr class="hover:bg-surface-container/50 transition-colors group" data-pvo-id="' +
					esc(r.id) +
					'" data-pvo-code="' +
					esc(r.code) +
					'">' +
					'<td class="py-3 px-4"><div class="flex flex-col">' +
					'<span class="font-data-mono text-data-mono text-primary font-bold">' +
					esc(r.code) +
					"</span>" +
					'<span class="font-body-md text-on-surface font-medium mt-1">' +
					esc(r.name) +
					"</span></div></td>" +
					'<td class="py-3 px-4"><span class="font-body-md text-[13px] text-on-surface">' +
					esc(r.pillar || "—") +
					"</span></td>" +
					'<td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">' +
					esc(r.source_type || "—") +
					"</td>" +
					'<td class="py-3 px-4 font-body-md text-[13px] text-on-surface">' +
					esc(r.applicability_mode || "—") +
					"</td>" +
					'<td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">—</td>' +
					'<td class="py-3 px-4 font-data-mono text-data-mono text-on-surface-variant">v1</td>' +
					'<td class="py-3 px-4"><span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ' +
					pillCls +
					' font-body-md text-xs font-medium"><span class="w-1.5 h-1.5 rounded-full ' +
					dotCls +
					'"></span>' +
					esc(status) +
					"</span></td>" +
					'<td class="py-3 px-4 text-right"><button type="button" class="' +
					actionCls +
					' font-body-md text-sm font-medium transition-colors" data-kt-str-action="open-pvo" data-pvo-code="' +
					esc(r.code) +
					'">' +
					esc(actionLabel) +
					"</button></td></tr>"
				);
			})
			.join("");
	}

	function bindPvoCatalogue($root) {
		return call("list_public_value_objectives").then(function (rows) {
			$root.attr("data-kt-str-live", "1");
			var pager = attachTablePagination($root, {
				renderPage: function (pageRows) {
					$root.find("[data-kt-str-pvo-tbody]").html(renderPvoCatalogueRows(pageRows));
				},
			});
			pager.setRows(rows || [], true);
			return rows;
		});
	}

	function flattenTreeLinks(nodes, out) {
		out = out || { outcomes: [], targets: [] };
		(nodes || []).forEach(function (n) {
			if (n.type === "StrategicOutcome") {
				out.outcomes.push({ id: n.id, code: n.code, name: n.name });
			}
			if (n.type === "PerformanceTarget") {
				out.targets.push({ id: n.id, code: n.code, name: n.name });
			}
			flattenTreeLinks(n.children, out);
		});
		return out;
	}

	function bindCommitments($root, planCode) {
		var state = {
			dto: null,
			tree: null,
			pvos: [],
			editable: false,
			routeToken: planCode,
			drawerMode: "add",
			editId: null,
			selectedPvoId: null,
			selectedLinks: [],
		};

		function setDrawerOpen(open) {
			var $drawer = $root.find('[data-testid="kt-str-vc-drawer"]').first();
			var $canvas = $root.find('[data-testid="kt-str-vc-canvas"]').first();
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

		function renderProgress() {
			var p = (state.dto && state.dto.progress) || { complete: 0, total: 0 };
			var total = p.total || 0;
			var complete = p.complete || 0;
			var pct = total ? Math.round((complete / total) * 100) : 0;
			$root.find("[data-kt-str-vc-progress-bar]").css("width", pct + "%");
			$root
				.find("[data-kt-str-vc-progress-label]")
				.text(
					String(complete) +
						" OF " +
						String(total) +
						" COMMITMENTS COMPLETE"
				);
		}

		function renderRows() {
			var rows = (state.dto && state.dto.rows) || [];
			var $tbody = $root.find("[data-kt-str-vc-tbody]");
			if (!rows.length) {
				$tbody.html(
					'<tr data-kt-str-vc-empty="1"><td colspan="7" class="py-8 px-4 text-center text-on-surface-variant text-sm">' +
						esc(__("No value commitments yet. Add an Active public-value objective.")) +
						"</td></tr>"
				);
				return;
			}
			$tbody.html(
				rows
					.map(function (r) {
						var obj = r.objective || {};
						var complete = !!r.complete;
						var rowCls = complete
							? "hover:bg-surface-container-lowest transition-colors group"
							: "hover:bg-error-container/10 bg-error-container/5 transition-colors group border-l-2 border-l-status-reserved";
						var linksHtml = "";
						if ((r.links || []).length) {
							linksHtml =
								'<div class="flex flex-col gap-1">' +
								r.links
									.map(function (lnk) {
										return (
											'<span class="font-data-mono text-[12px] bg-secondary-fixed text-on-secondary-fixed px-2 py-0.5 rounded border border-secondary-fixed-dim/50 inline-block w-max">' +
											esc(lnk.code || "—") +
											"</span>"
										);
									})
									.join("") +
								"</div>";
						} else {
							linksHtml =
								'<div class="flex items-center gap-1.5 text-status-reserved text-sm font-medium bg-status-reserved/10 px-2 py-1 rounded">' +
								'<span class="material-symbols-outlined text-[16px]">warning</span>' +
								esc(__("No link selected")) +
								"</div>";
						}
						var statusHtml = complete
							? '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-status-available/10 text-status-available text-xs font-semibold">' +
								'<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span> ' +
								esc(__("Complete")) +
								"</span>"
							: '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-status-reserved/10 text-status-reserved text-xs font-semibold border border-status-reserved/20">' +
								'<span class="w-1.5 h-1.5 rounded-full bg-status-reserved"></span> ' +
								esc(__("Needs attention")) +
								"</span>";
						var actionHtml = complete
							? '<button type="button" class="text-primary hover:text-on-primary-fixed-variant font-medium text-sm transition-colors" data-kt-str-action="review-vc" data-kt-str-vc-id="' +
								esc(r.id) +
								'">' +
								esc(__("Review")) +
								"</button>"
							: '<button type="button" class="text-status-reserved hover:text-status-reserved/80 font-semibold text-sm transition-colors inline-flex items-center justify-end gap-1" data-kt-str-action="review-vc" data-kt-str-vc-id="' +
								esc(r.id) +
								'">' +
								esc(__("Resolve")) +
								' <span class="material-symbols-outlined text-[16px]">arrow_forward</span></button>';
						return (
							'<tr class="' +
							rowCls +
							'" data-kt-str-vc-id="' +
							esc(r.id) +
							'" data-kt-str-vc-code="' +
							esc(obj.code || "") +
							'">' +
							'<td class="py-4 px-4 align-top w-[250px]">' +
							'<div class="font-data-mono text-data-mono text-secondary mb-1">' +
							esc(obj.code || "") +
							"</div>" +
							'<div class="font-medium text-sm leading-tight">' +
							esc(obj.name || "") +
							"</div></td>" +
							'<td class="py-4 px-4 align-top"><span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-container text-on-surface-variant text-xs font-medium border border-outline-variant/30">' +
							esc(r.consideration_level || "") +
							"</span></td>" +
							'<td class="py-4 px-4 align-top text-sm text-on-surface-variant min-w-[200px]">' +
							esc(r.rationale || "") +
							"</td>" +
							'<td class="py-4 px-4 align-top">' +
							linksHtml +
							"</td>" +
							'<td class="py-4 px-4 align-top text-sm">' +
							esc(r.responsible_owner || "—") +
							"</td>" +
							'<td class="py-4 px-4 align-top">' +
							statusHtml +
							"</td>" +
							'<td class="py-4 px-4 align-top text-right">' +
							actionHtml +
							"</td></tr>"
						);
					})
					.join("")
			);
		}

		function committedPvoIds() {
			return ((state.dto && state.dto.rows) || []).map(function (r) {
				return r.objective && r.objective.id;
			});
		}

		function filteredPvos() {
			var q = String($root.find("[data-kt-str-vc-drawer-search]").val() || "")
				.trim()
				.toLowerCase();
			var pillar = $root.find("[data-kt-str-vc-drawer-pillar]").val() || "";
			var source = $root.find("[data-kt-str-vc-drawer-source]").val() || "";
			var taken = {};
			if (state.drawerMode === "add") {
				committedPvoIds().forEach(function (id) {
					if (id) {
						taken[id] = true;
					}
				});
			}
			return (state.pvos || []).filter(function (p) {
				if (taken[p.id] && p.id !== state.selectedPvoId) {
					return false;
				}
				if (pillar && p.pillar !== pillar) {
					return false;
				}
				if (source && p.source_type !== source) {
					return false;
				}
				if (!q) {
					return true;
				}
				return (
					String(p.code || "")
						.toLowerCase()
						.indexOf(q) >= 0 ||
					String(p.name || "")
						.toLowerCase()
						.indexOf(q) >= 0
				);
			});
		}

		function paintPvoList() {
			var list = filteredPvos();
			var $host = $root.find("[data-kt-str-vc-drawer-pvo-list]");
			if (!list.length) {
				$host.html(
					'<div class="text-sm text-on-surface-variant py-2">' +
						esc(__("No matching Active objectives")) +
						"</div>"
				);
				return;
			}
			$host.html(
				list
					.map(function (p) {
						var sel = p.id === state.selectedPvoId;
						return (
							'<button type="button" class="kt-str-vc-pvo-option w-full text-left px-3 py-2 rounded-lg border' +
							(sel ? " is-selected" : "") +
							'" data-kt-str-action="select-pvo" data-kt-str-pvo-id="' +
							esc(p.id) +
							'" data-kt-str-vc-pvo-selected="' +
							(sel ? "1" : "0") +
							'" aria-pressed="' +
							(sel ? "true" : "false") +
							'">' +
							'<div class="flex items-start justify-between gap-2">' +
							"<div>" +
							'<div class="font-data-mono text-xs text-secondary">' +
							esc(p.code || "") +
							"</div>" +
							'<div class="text-sm font-medium text-on-surface">' +
							esc(p.name || "") +
							"</div></div>" +
							(sel
								? '<span class="kt-str-vc-pvo-selected-badge inline-flex items-center gap-1 shrink-0 text-xs font-semibold text-primary" aria-hidden="true">' +
									'<span class="material-symbols-outlined text-[16px]">check_circle</span>' +
									esc(__("Selected")) +
									"</span>"
								: "") +
							"</div></button>"
						);
					})
					.join("")
			);
		}

		function paintPreview() {
			var p = (state.pvos || []).find(function (x) {
				return x.id === state.selectedPvoId;
			});
			var $prev = $root.find("[data-kt-str-vc-drawer-preview]");
			if (!p) {
				$prev.addClass("hidden");
				return;
			}
			$prev.removeClass("hidden");
			$root.find("[data-kt-str-vc-drawer-pvo-code]").text(p.code || "");
			$root.find("[data-kt-str-vc-drawer-pvo-title]").text(p.name || "");
			$root.find("[data-kt-str-vc-drawer-pvo-pillar]").text(p.pillar || "");
		}

		function paintLinkPicker() {
			var flat = flattenTreeLinks((state.tree && state.tree.tree) || []);
			var selected = {};
			(state.selectedLinks || []).forEach(function (l) {
				var key =
					l.link_type +
					":" +
					(l.linked_outcome || l.linked_target || "");
				selected[key] = true;
			});
			var html = "";
			if (!flat.outcomes.length && !flat.targets.length) {
				html =
					'<div class="text-sm text-on-surface-variant text-center py-2">' +
					esc(__("Add plan structure first to link outcomes or targets.")) +
					"</div>";
			} else {
				html +=
					'<div class="text-xs font-semibold text-on-surface-variant uppercase mb-1">' +
					esc(__("Outcomes")) +
					"</div>";
				html += flat.outcomes
					.map(function (o) {
						var key = "Strategic Outcome:" + o.id;
						var checked = selected[key] ? " checked" : "";
						return (
							'<label class="flex items-start gap-2 text-sm cursor-pointer">' +
							'<input type="checkbox" data-kt-str-link-type="Strategic Outcome" data-kt-str-link-id="' +
							esc(o.id) +
							'"' +
							checked +
							"/>" +
							'<span><span class="font-data-mono text-xs text-secondary">' +
							esc(o.code) +
							"</span> " +
							esc(o.name) +
							"</span></label>"
						);
					})
					.join("");
				html +=
					'<div class="text-xs font-semibold text-on-surface-variant uppercase mb-1 mt-3">' +
					esc(__("Targets")) +
					"</div>";
				html += flat.targets
					.map(function (t) {
						var key = "Performance Target:" + t.id;
						var checked = selected[key] ? " checked" : "";
						return (
							'<label class="flex items-start gap-2 text-sm cursor-pointer">' +
							'<input type="checkbox" data-kt-str-link-type="Performance Target" data-kt-str-link-id="' +
							esc(t.id) +
							'"' +
							checked +
							"/>" +
							'<span><span class="font-data-mono text-xs text-secondary">' +
							esc(t.code) +
							"</span> " +
							esc(t.name) +
							"</span></label>"
						);
					})
					.join("");
			}
			$root.find("[data-kt-str-vc-drawer-links]").html(html);
		}

		function fillPillarSourceFilters() {
			var pillars = {};
			var sources = {};
			(state.pvos || []).forEach(function (p) {
				if (p.pillar) {
					pillars[p.pillar] = true;
				}
				if (p.source_type) {
					sources[p.source_type] = true;
				}
			});
			var $pillar = $root.find("[data-kt-str-vc-drawer-pillar]");
			var curP = $pillar.val();
			$pillar.html('<option value="">Pillar: All</option>');
			Object.keys(pillars)
				.sort()
				.forEach(function (p) {
					$pillar.append($("<option/>").val(p).text(p));
				});
			if (curP) {
				$pillar.val(curP);
			}
			var $src = $root.find("[data-kt-str-vc-drawer-source]");
			var curS = $src.val();
			$src.html('<option value="">Source: All</option>');
			Object.keys(sources)
				.sort()
				.forEach(function (s) {
					$src.append($("<option/>").val(s).text(s));
				});
			if (curS) {
				$src.val(curS);
			}
		}

		function openDrawer(mode, row) {
			if (!state.editable && mode === "add") {
				return;
			}
			state.drawerMode = mode;
			state.editId = row ? row.id : null;
			state.selectedPvoId = row && row.objective ? row.objective.id : null;
			state.selectedLinks = row
				? (row.links || []).map(function (l) {
						return {
							link_type: l.link_type,
							linked_outcome: l.linked_outcome || null,
							linked_target: l.linked_target || null,
						};
					})
				: [];
			$root
				.find("[data-kt-str-vc-drawer-title]")
				.text(mode === "edit" ? __("Review Commitment") : __("Add Commitment"));
			$root
				.find("[data-kt-str-vc-drawer-subtitle]")
				.text(
					mode === "edit"
						? __("Update rationale, level, owner, and links")
						: __("Select and configure an objective")
				);
			$root.find("[data-kt-str-vc-drawer-search]").val("");
			$root.find("[data-kt-str-vc-drawer-rationale]").val((row && row.rationale) || "");
			$root
				.find("[data-kt-str-vc-drawer-level]")
				.val((row && row.consideration_level) || "Required consideration");
			$root
				.find("[data-kt-str-vc-drawer-owner]")
				.val((row && row.responsible_owner) || "");
			var $lib = $root.find("[data-kt-str-vc-drawer-library]");
			if (mode === "edit") {
				$lib.addClass("hidden");
			} else {
				$lib.removeClass("hidden");
			}
			var $save = $root.find("[data-kt-str-vc-drawer-save]");
			if (state.editable) {
				$save.removeClass("hidden").prop("disabled", false);
			} else {
				$save.addClass("hidden");
			}
			fillPillarSourceFilters();
			paintPvoList();
			paintPreview();
			paintLinkPicker();
			setDrawerOpen(true);
		}

		function readSelectedLinks() {
			var links = [];
			$root.find("[data-kt-str-vc-drawer-links] input[type='checkbox']:checked").each(function () {
				var $el = $(this);
				var type = $el.attr("data-kt-str-link-type");
				var id = $el.attr("data-kt-str-link-id");
				if (type === "Strategic Outcome") {
					links.push({ link_type: type, linked_outcome: id });
				} else {
					links.push({ link_type: type, linked_target: id });
				}
			});
			return links;
		}

		function saveDrawer() {
			if (!state.editable) {
				return;
			}
			var plan = state.dto && state.dto.plan;
			if (!plan) {
				return;
			}
			var pvoId = state.selectedPvoId;
			if (!pvoId && state.drawerMode === "add") {
				frappe.show_alert({
					message: __("Select an Active public-value objective"),
					indicator: "orange",
				});
				return;
			}
			var rationale = String($root.find("[data-kt-str-vc-drawer-rationale]").val() || "").trim();
			var owner = String($root.find("[data-kt-str-vc-drawer-owner]").val() || "").trim();
			var level = $root.find("[data-kt-str-vc-drawer-level]").val();
			var links = readSelectedLinks();
			if (!rationale || !owner) {
				frappe.show_alert({
					message: __("Rationale and owner are required"),
					indicator: "orange",
				});
				return;
			}
			if (!links.length) {
				frappe.show_alert({
					message: __("Link at least one outcome or target"),
					indicator: "orange",
				});
				return;
			}
			var payload = {
				plan_version: plan.id,
				public_value_objective_version: pvoId,
				rationale: rationale,
				consideration_level: level,
				responsible_owner: owner,
				status: "Draft",
				links: links,
			};
			if (state.drawerMode === "edit" && state.editId) {
				payload.id = state.editId;
			}
			call("upsert_plan_value_commitment", { payload: payload })
				.then(function () {
					setDrawerOpen(false);
					frappe.show_alert({ message: __("Commitment saved"), indicator: "green" });
					return reload();
				})
				.catch(function () {
					frappe.show_alert({
						message: __("Could not save commitment"),
						indicator: "red",
					});
				});
		}

		function paint() {
			if (!state.dto) {
				return;
			}
			var plan = state.dto.plan || {};
			state.editable = !!(state.dto.capabilities && state.dto.capabilities.editable);
			$root.attr("data-kt-str-live", "1");
			$root.attr("data-kt-str-plan-id", plan.id || "");
			$root.attr("data-kt-str-bound-code", plan.code || "");
			state.routeToken =
				plan.status === "Active" && plan.code
					? plan.code
					: plan.supersedes_plan_version
						? plan.id || planCode
						: plan.code || plan.id || planCode;
			$root.attr("data-kt-str-route-token", state.routeToken);
			$root.attr("data-kt-str-vc-editable", state.editable ? "1" : "0");
			$root.attr(
				"data-kt-str-commitment-count",
				String(((state.dto.rows || []).length))
			);
			bindPlanChrome($root, plan);
			renderProgress();
			renderRows();
			var $add = $root.find("[data-kt-str-vc-add]");
			if (state.editable) {
				$add.removeClass("hidden").removeAttr("hidden").attr("aria-hidden", "false");
			} else {
				$add.addClass("hidden").attr("hidden", "hidden").attr("aria-hidden", "true");
			}
		}

		function reload() {
			var args = { plan_code: state.routeToken || planCode };
			return Promise.all([
				call("list_plan_value_commitments", args),
				call("get_strategy_tree", args).catch(function () {
					return null;
				}),
				call("list_public_value_objectives", { status: "Active" }).catch(function () {
					return [];
				}),
			]).then(function (results) {
				state.dto = results[0];
				state.tree = results[1];
				state.pvos = results[2] || [];
				if (!state.dto || !state.dto.plan) {
					return;
				}
				paint();
				return state.dto;
			});
		}

		$root.off("click.ktStrVcLive").on("click.ktStrVcLive", "[data-kt-str-action]", function (e) {
			var $el = $(this);
			var action = $el.attr("data-kt-str-action");
			if (action === "add-vc") {
				e.preventDefault();
				openDrawer("add", null);
				return;
			}
			if (action === "close-vc-drawer") {
				e.preventDefault();
				setDrawerOpen(false);
				return;
			}
			if (action === "save-vc") {
				e.preventDefault();
				saveDrawer();
				return;
			}
			if (action === "review-vc") {
				e.preventDefault();
				var id = $el.attr("data-kt-str-vc-id");
				var row = ((state.dto && state.dto.rows) || []).find(function (r) {
					return r.id === id;
				});
				if (row) {
					openDrawer("edit", row);
				}
				return;
			}
			if (action === "select-pvo") {
				e.preventDefault();
				state.selectedPvoId = $el.attr("data-kt-str-pvo-id");
				paintPvoList();
				paintPreview();
			}
		});

		$root
			.off("input.ktStrVcFilter change.ktStrVcFilter")
			.on(
				"input.ktStrVcFilter change.ktStrVcFilter",
				"[data-kt-str-vc-drawer-search], [data-kt-str-vc-drawer-pillar], [data-kt-str-vc-drawer-source]",
				function () {
					paintPvoList();
				}
			);

		setDrawerOpen(false);
		return reload();
	}

	function measResultPill(status) {
		var s = String(status || "No data");
		var cls =
			"inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-caps text-[11px] font-bold border ";
		var lower = s.toLowerCase();
		if (lower === "on track") {
			cls += "bg-surface-container-highest text-status-available border-status-available/30";
		} else if (lower === "at risk" || lower === "off track") {
			cls += "bg-error-container text-on-error-container border-error/20";
		} else {
			cls += "bg-surface-container text-outline border-outline-variant border-dashed";
		}
		return (
			'<div class="' +
			cls +
			'"><span class="w-1.5 h-1.5 rounded-full bg-current"></span> ' +
			esc(s.toUpperCase()) +
			"</div>"
		);
	}

	function measWorkflowPill(status) {
		var s = String(status || "");
		var cls =
			"inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-caps text-[11px] font-bold border border-outline-variant bg-surface-container-highest text-on-surface";
		var icon = "schedule";
		var lower = s.toLowerCase();
		if (lower === "verified") {
			icon = "verified";
		} else if (lower === "submitted") {
			icon = "send";
			cls =
				"inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-caps text-[11px] font-bold border border-tertiary-fixed-dim bg-tertiary-fixed text-on-tertiary-fixed-variant";
		} else if (lower === "draft" || lower === "returned") {
			icon = "edit";
			cls =
				"inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-caps text-[11px] font-bold border border-status-reserved/30 bg-surface-container-highest text-status-reserved";
		}
		return (
			'<div class="' +
			cls +
			'"><span class="material-symbols-outlined text-[14px]">' +
			icon +
			"</span> " +
			esc(s.toUpperCase()) +
			"</div>"
		);
	}

	function bindMeasurements($root, planCode) {
		var state = {
			dto: null,
			routeToken: planCode,
			filterSearch: "",
			filterPeriod: "",
			filterWorkflow: "",
			filterResult: "",
		};

		function filteredRows() {
			var rows = (state.dto && state.dto.rows) || [];
			var q = String(state.filterSearch || "")
				.trim()
				.toLowerCase();
			return rows.filter(function (r) {
				var tgt = r.target || {};
				if (state.filterPeriod && r.period_label !== state.filterPeriod) {
					return false;
				}
				if (state.filterWorkflow && r.workflow_status !== state.filterWorkflow) {
					return false;
				}
				if (state.filterResult && r.result_status !== state.filterResult) {
					return false;
				}
				if (!q) {
					return true;
				}
				return (
					String(tgt.code || "")
						.toLowerCase()
						.indexOf(q) >= 0 ||
					String(tgt.name || "")
						.toLowerCase()
						.indexOf(q) >= 0
				);
			});
		}

		function paintCounts() {
			var c = (state.dto && state.dto.counts) || {};
			["due", "submitted", "verified", "needs_attention"].forEach(function (k) {
				$root.find('[data-kt-str-meas-count="' + k + '"]').text(String(c[k] != null ? c[k] : 0));
			});
		}

		function paintPeriodFilter() {
			var $sel = $root.find("[data-kt-str-meas-filter-period]");
			var cur = state.filterPeriod;
			var labels = {};
			((state.dto && state.dto.rows) || []).forEach(function (r) {
				if (r.period_label) {
					labels[r.period_label] = true;
				}
			});
			$sel.html('<option value="">Measurement period</option>');
			Object.keys(labels)
				.sort()
				.forEach(function (lab) {
					$sel.append($("<option/>").val(lab).text(lab));
				});
			if (cur) {
				$sel.val(cur);
			}
		}

		function actionButton(r) {
			var code = (r.target && r.target.code) || "";
			var id = r.id || "";
			if (r.next_action === "submit") {
				return (
					'<button type="button" class="bg-surface-container-lowest border border-primary text-primary hover:bg-primary-fixed py-1.5 px-3 rounded text-body-md font-medium transition-colors shadow-sm" data-kt-str-action="submit-measurement" data-kt-str-target-code="' +
					esc(code) +
					'" data-kt-str-measurement-id="' +
					esc(id) +
					'">' +
					esc(__("Submit measurement")) +
					"</button>"
				);
			}
			if (r.next_action === "review") {
				return (
					'<button type="button" class="text-secondary font-medium text-body-md hover:underline px-2 py-1" data-kt-str-action="review-measurement" data-kt-str-target-code="' +
					esc(code) +
					'" data-kt-str-measurement-id="' +
					esc(id) +
					'">' +
					esc(__("Review")) +
					"</button>"
				);
			}
			return (
				'<button type="button" class="text-secondary font-medium text-body-md hover:underline px-2 py-1" data-kt-str-action="view-measurement" data-kt-str-target-code="' +
				esc(code) +
				'" data-kt-str-measurement-id="' +
				esc(id) +
				'">' +
				esc(__("View")) +
				"</button>"
			);
		}

		function paintMeasPageRows(pageRows) {
			var $tbody = $root.find("[data-kt-str-meas-tbody]");
			if (!pageRows.length) {
				$tbody.html(
					'<tr data-kt-str-meas-empty="1"><td colspan="8" class="py-8 px-4 text-center text-on-surface-variant text-sm">' +
						esc(__("No performance measurements for this plan yet.")) +
						"</td></tr>"
				);
				return;
			}
			$tbody.html(
				pageRows
					.map(function (r) {
						var tgt = r.target || {};
						var ca = r.corrective_action_label || "—";
						var caHtml = r.corrective_action_open
							? '<span class="text-secondary font-medium">' + esc(ca) + "</span>"
							: '<span class="text-on-surface-variant' +
								(ca === "None required" ? " italic" : "") +
								'">' +
								esc(ca) +
								"</span>";
						return (
							'<tr class="hover:bg-surface-container transition-colors group" data-kt-str-measurement-id="' +
							esc(r.id) +
							'" data-kt-str-target-code="' +
							esc(tgt.code || "") +
							'">' +
							'<td class="py-4 px-4 align-top min-w-[300px]"><div class="flex flex-col"><span class="font-data-mono text-data-mono text-primary font-bold">' +
							esc(tgt.code || "") +
							'</span><span class="text-body-md text-on-surface-variant">' +
							esc(tgt.name || "") +
							"</span></div></td>" +
							'<td class="py-4 px-4 align-top text-body-md text-on-surface whitespace-nowrap">' +
							esc(r.period_label || "—") +
							"</td>" +
							'<td class="py-4 px-4 align-top font-data-mono text-data-mono text-on-surface text-right whitespace-nowrap">' +
							esc(r.target_value_display || "—") +
							"</td>" +
							'<td class="py-4 px-4 align-top font-data-mono text-data-mono text-on-surface text-right whitespace-nowrap">' +
							esc(r.actual_display || "—") +
							"</td>" +
							'<td class="py-4 px-4 align-top whitespace-nowrap">' +
							measResultPill(r.result_status) +
							"</td>" +
							'<td class="py-4 px-4 align-top whitespace-nowrap">' +
							measWorkflowPill(r.workflow_status) +
							"</td>" +
							'<td class="py-4 px-4 align-top text-body-md">' +
							caHtml +
							"</td>" +
							'<td class="py-4 px-4 align-top text-right whitespace-nowrap">' +
							actionButton(r) +
							"</td></tr>"
						);
					})
					.join("")
			);
		}

		function paintRows(resetPage) {
			var pager = attachTablePagination($root, {
				renderPage: paintMeasPageRows,
			});
			pager.setRows(filteredRows(), !!resetPage);
		}

		function paint() {
			if (!state.dto) {
				return;
			}
			var plan = state.dto.plan || {};
			$root.attr("data-kt-str-live", "1");
			$root.attr("data-kt-str-plan-id", plan.id || "");
			$root.attr("data-kt-str-bound-code", plan.code || "");
			state.routeToken =
				plan.status === "Active" && plan.code
					? plan.code
					: plan.supersedes_plan_version
						? plan.id || planCode
						: plan.code || plan.id || planCode;
			$root.attr("data-kt-str-route-token", state.routeToken);
			$root.attr(
				"data-kt-str-measurement-count",
				String(((state.dto.rows || []).length))
			);
			var defaultTarget = state.dto.default_target_code || "";
			$root.attr("data-kt-str-default-target", defaultTarget);
			$root
				.find("[data-kt-str-meas-submit]")
				.attr("data-kt-str-target-code", defaultTarget);
			bindPlanChrome($root, plan);
			paintCounts();
			paintPeriodFilter();
			paintRows(true);
		}

		function routeToSubmit(targetCode) {
			var plan = state.routeToken || planCode || "";
			var code = targetCode || $root.attr("data-kt-str-default-target") || "";
			if (!plan) {
				frappe.show_alert({
					message: __("Plan context is required to submit a measurement."),
					indicator: "orange",
				});
				return;
			}
			if (!code) {
				frappe.show_alert({
					message: __(
						"This plan has no Active performance targets to measure. Add targets on the Structure tab first."
					),
					indicator: "orange",
				});
				return;
			}
			frappe.set_route("strategy-measurement-submit", plan, code);
		}

		function routeToVerify(targetCode) {
			var plan = state.routeToken || planCode || "";
			var code = targetCode || $root.attr("data-kt-str-default-target") || "";
			if (!plan || !code) {
				frappe.show_alert({
					message: __("Select a measurement row to review."),
					indicator: "orange",
				});
				return;
			}
			frappe.set_route("strategy-measurement-verify", plan, code);
		}

		function reload() {
			return call("list_measurements", { plan_code: state.routeToken || planCode }).then(
				function (dto) {
					state.dto = dto;
					if (!state.dto || !state.dto.plan) {
						return;
					}
					paint();
					return state.dto;
				}
			);
		}

		$root.off("click.ktStrMeasLive").on("click.ktStrMeasLive", "[data-kt-str-action]", function (e) {
			var $el = $(this);
			var action = $el.attr("data-kt-str-action");
			var targetCode = $el.attr("data-kt-str-target-code");
			if (action === "submit-measurement") {
				e.preventDefault();
				routeToSubmit(targetCode);
				return;
			}
			if (action === "view-measurement" || action === "review-measurement") {
				e.preventDefault();
				routeToVerify(targetCode);
				return;
			}
			if (action === "clear-meas-filters") {
				e.preventDefault();
				state.filterSearch = "";
				state.filterPeriod = "";
				state.filterWorkflow = "";
				state.filterResult = "";
				$root.find("[data-kt-str-meas-search]").val("");
				$root.find("[data-kt-str-meas-filter-period]").val("");
				$root.find("[data-kt-str-meas-filter-workflow]").val("");
				$root.find("[data-kt-str-meas-filter-result]").val("");
				paintRows(true);
			}
		});

		$root
			.off("input.ktStrMeasFilter change.ktStrMeasFilter")
			.on(
				"input.ktStrMeasFilter change.ktStrMeasFilter",
				"[data-kt-str-meas-search], [data-kt-str-meas-filter-period], [data-kt-str-meas-filter-workflow], [data-kt-str-meas-filter-result]",
				function () {
					state.filterSearch = $root.find("[data-kt-str-meas-search]").val() || "";
					state.filterPeriod = $root.find("[data-kt-str-meas-filter-period]").val() || "";
					state.filterWorkflow = $root.find("[data-kt-str-meas-filter-workflow]").val() || "";
					state.filterResult = $root.find("[data-kt-str-meas-filter-result]").val() || "";
					paintRows(true);
				}
			);

		return reload();
	}

	function reviewIssueRow(issue) {
		var blocker = (issue.severity || "blocker") === "blocker";
		var sevLabel = blocker ? __("Blocker") : __("Warning");
		var sevCls = blocker ? "text-status-exhausted" : "text-status-reserved";
		var icon = blocker ? "cancel" : "warning";
		var loc = issue.edit_location || "strategy-plan-structure";
		return (
			'<div class="flex flex-col md:flex-row md:items-center justify-between p-4 border-b border-surface-variant last:border-b-0 hover:bg-surface-container/30 transition-colors group" data-kt-str-review-issue>' +
			'<div class="flex gap-4 items-start">' +
			'<span class="material-symbols-outlined ' +
			sevCls +
			' mt-0.5" data-icon="' +
			icon +
			'">' +
			icon +
			"</span>" +
			"<div>" +
			'<div class="flex items-center gap-2 mb-1">' +
			'<span class="text-data-mono font-data-mono text-xs bg-surface-container px-1.5 py-0.5 rounded text-on-surface-variant">' +
			esc(issue.code || "") +
			"</span>" +
			'<span class="text-xs font-bold ' +
			sevCls +
			' uppercase tracking-wider">' +
			esc(sevLabel) +
			"</span>" +
			"</div>" +
			'<p class="text-body-md font-body-md text-on-surface">' +
			esc(issue.message || issue.title || "") +
			"</p>" +
			"</div></div>" +
			'<div class="mt-3 md:mt-0 ml-10 md:ml-0">' +
			'<button type="button" class="text-primary hover:text-primary-container font-semibold text-sm flex items-center gap-1 group-hover:underline" data-kt-str-resolve="' +
			esc(loc) +
			'" data-kt-str-record="' +
			esc(issue.record_id || "") +
			'">' +
			__("Resolve") +
			' <span class="material-symbols-outlined text-[16px]" data-icon="arrow_forward">arrow_forward</span>' +
			"</button></div></div>"
		);
	}

	function setReviewActionVisible($btn, visible) {
		if (!$btn || !$btn.length) {
			return;
		}
		if (visible) {
			$btn.removeClass("hidden").removeAttr("hidden").css("display", "");
		} else {
			$btn.addClass("hidden").attr("hidden", "hidden").css("display", "none");
		}
	}

	function paintReviewStatusPill($root, status) {
		paintPlanStatusPill($root, status);
	}

	function paintReviewActions($root, dto) {
		var actions = dto.allowed_actions || [];
		var canSubmit = actions.indexOf("Submit") >= 0 || actions.indexOf("Resubmit") >= 0;
		var isBlockersCanvas = $root.is('[data-testid="kt-str-review-blockers"]');
		var $submit = $root.find('[data-kt-str-action="submit-for-review"]');
		var $return = $root.find('[data-kt-str-action="return-for-correction"]');
		var $approve = $root.find('[data-kt-str-action="approve-plan"]');
		var $activate = $root.find('[data-kt-str-action="activate-plan"]');

		if (actions.indexOf("Resubmit") >= 0) {
			$root.find("[data-kt-str-submit-label]").text(__("Resubmit for review"));
		} else {
			$root.find("[data-kt-str-submit-label]").text(__("Submit for review"));
		}

		// Primary CTAs only when listed in allowed_actions. Blockers canvas keeps a
		// disabled Submit affordance when not allowed (Stitch parity). Ready canvas
		// never shows Submit unless Submit/Resubmit is allowed.
		if (canSubmit) {
			setReviewActionVisible($submit, true);
			$submit
				.prop("disabled", false)
				.removeClass("bg-surface-variant text-outline cursor-not-allowed")
				.addClass("bg-primary text-on-primary hover:bg-primary-container")
				.removeAttr("title");
		} else if (isBlockersCanvas) {
			setReviewActionVisible($submit, true);
			$submit
				.prop("disabled", true)
				.addClass("bg-surface-variant text-outline cursor-not-allowed")
				.removeClass("bg-primary text-on-primary hover:bg-primary-container")
				.attr("title", __("All blockers must be resolved before submission"));
		} else {
			setReviewActionVisible($submit, false);
			$submit.prop("disabled", true);
		}

		setReviewActionVisible($return, actions.indexOf("Return for correction") >= 0);
		setReviewActionVisible($approve, actions.indexOf("Approve") >= 0);
		setReviewActionVisible($activate, actions.indexOf("Activate") >= 0);
	}

	function paintReviewCanvas($root, dto) {
		var plan = dto.plan || {};
		var status = dto.status || plan.status || "";
		$root.attr("data-kt-str-live", "1");
		$root.attr("data-kt-str-ready", dto.ready ? "1" : "0");
		$root.attr("data-kt-str-blocker-count", String(dto.blocker_count || 0));
		$root.attr("data-kt-str-bound-code", plan.code || "");
		$root.attr("data-kt-str-route-token", plan.code || plan.id || "");
		$root.attr("data-kt-str-plan-id", plan.id || "");
		/* Full shared chrome (period + Version N + status tones) — not code/title-only. */
		bindPlanChrome(
			$root,
			Object.assign({}, plan, {
				status: status,
			})
		);
		paintReviewStatusPill($root, status);

		var blockers = dto.blocker_count || 0;
		var warnings = dto.warning_count || 0;
		$root
			.find("[data-kt-str-blocker-count-label]")
			.text(blockers + (blockers === 1 ? " Blocker" : " Blockers"));
		$root
			.find("[data-kt-str-warning-count-label]")
			.text(warnings + (warnings === 1 ? " Warning" : " Warnings"));

		var reason = dto.return_reason || "";
		var $banner = $root.find("[data-kt-str-return-reason-banner]");
		if (status === "Returned" && reason) {
			$banner.removeClass("hidden");
			$root.find("[data-kt-str-return-reason]").text(reason);
		} else {
			$banner.addClass("hidden");
			$root.find("[data-kt-str-return-reason]").text("");
		}

		if ($root.is('[data-testid="kt-str-review-ready"]')) {
			var title = __("Ready for submission");
			var copy = __(
				"All readiness checks have passed. This version of the strategic plan can now be submitted for official review."
			);
			if (status === "Submitted") {
				title = __("Awaiting review");
				copy = __("Readiness checks have passed. Approve or return this plan according to your authority.");
			} else if (status === "Approved") {
				title = __("Approved — ready to activate");
				copy = __("This plan version is approved. Activate it to make it the live strategy for the entity.");
			} else if (status === "Active") {
				title = __("Plan is Active");
				copy = __("All readiness checks pass for this Active plan version.");
			} else if (status === "Returned") {
				title = __("Ready to resubmit");
				copy = __("Return issues are resolved and readiness checks have passed. Resubmit for review.");
			}
			$root.find("[data-kt-str-review-ready-title]").text(title);
			$root.find("[data-kt-str-review-ready-copy]").text(copy);
		} else {
			var grouped = dto.grouped || {};
			var groups = ["Structure", "Targets", "Value Commitments", "Governance"];
			groups.forEach(function (g) {
				var issues = grouped[g] || [];
				var $card = $root.find('[data-kt-str-review-group="' + g + '"]');
				if (!issues.length) {
					$card.addClass("hidden");
					$card.find("[data-kt-str-review-issues]").empty();
					return;
				}
				$card.removeClass("hidden");
				var blockerN = issues.filter(function (i) {
					return (i.severity || "blocker") === "blocker";
				}).length;
				var warnN = issues.length - blockerN;
				var countLabel =
					blockerN && warnN
						? blockerN + " / " + warnN
						: blockerN
							? blockerN + (blockerN === 1 ? " Blocker" : " Blockers")
							: warnN + (warnN === 1 ? " Warning" : " Warnings");
				$card.find("[data-kt-str-review-group-count]").text(countLabel);
				$card.find("[data-kt-str-review-issues]").html(
					issues
						.map(function (i) {
							return reviewIssueRow(i);
						})
						.join("")
				);
			});
			$root.find("[data-kt-str-review-blocked-banner]").toggleClass("hidden", !!dto.ready);
		}

		paintReviewActions($root, dto);
		// Hide design fixture toggle once live data is bound.
		$root
			.closest('[data-testid="kt-cl-page-body"]')
			.find('[data-testid="kt-str-review-state-toggle"]')
			.addClass("hidden");
	}

	function remountReviewForReadyState(planCode, ready) {
		if (frappe.route_options) {
			delete frappe.route_options.kt_str_review_state;
		}
		frappe.route_options = frappe.route_options || {};
		// Force shell pick via temporary flag then clear — use explicit state matching API.
		frappe.route_options.kt_str_review_state = ready ? "ready" : "blockers";
		frappe.set_route("strategy-plan-review", planCode);
		// Clear after navigation so next live load is API-driven.
		setTimeout(function () {
			if (frappe.route_options) {
				delete frappe.route_options.kt_str_review_state;
			}
		}, 0);
	}

	function bindReview($root, planCode) {
		function reload() {
			return call("get_plan_readiness_api", { plan_code: planCode }).then(function (dto) {
				if (!dto) {
					return dto;
				}
				var isReadyCanvas = $root.is('[data-testid="kt-str-review-ready"]');
				if (!!dto.ready !== isReadyCanvas) {
					remountReviewForReadyState(planCode, !!dto.ready);
					return dto;
				}
				paintReviewCanvas($root, dto);

				$root.off("click.ktStrResolve").on("click.ktStrResolve", "[data-kt-str-resolve]", function (e) {
					e.preventDefault();
					var loc = $(this).attr("data-kt-str-resolve");
					if (loc) {
						frappe.set_route(loc, planCode);
					}
				});

				$root.off("click.ktStrRunReady").on("click.ktStrRunReady", "[data-kt-str-action='run-readiness']", function (e) {
					e.preventDefault();
					frappe.show_alert({ message: __("Running readiness check…"), indicator: "blue" });
					reload();
				});

				function doTransition(action, reason) {
					var args = { plan_version: dto.plan.id, action: action };
					if (reason) {
						args.reason = reason;
					}
					return call("transition_plan", args).then(function (out) {
						frappe.show_alert({
							message: __("Plan updated: {0}", [(out && out.status) || action]),
							indicator: "green",
						});
						return reload();
					});
				}

				$root
					.off("click.ktStrSubmit")
					.on("click.ktStrSubmit", "[data-kt-str-action='submit-for-review']", function (e) {
						e.preventDefault();
						var $btn = $(this);
						if ($btn.prop("disabled") || $btn.hasClass("hidden") || $btn.attr("hidden")) {
							return;
						}
						var action = dto.status === "Returned" ? "Resubmit" : "Submit";
						if ((dto.allowed_actions || []).indexOf(action) < 0) {
							return;
						}
						doTransition(action);
					});

				$root
					.off("click.ktStrReturnPlan")
					.on("click.ktStrReturnPlan", "[data-kt-str-action='return-for-correction']", function (e) {
						e.preventDefault();
						frappe.prompt(
							[
								{
									fieldname: "reason",
									fieldtype: "Small Text",
									label: __("Return reason"),
									reqd: 1,
								},
							],
							function (values) {
								doTransition("Return for correction", values.reason);
							},
							__("Return for correction"),
							__("Return")
						);
					});

				$root
					.off("click.ktStrApprove")
					.on("click.ktStrApprove", "[data-kt-str-action='approve-plan']", function (e) {
						e.preventDefault();
						doTransition("Approve");
					});

				$root
					.off("click.ktStrActivate")
					.on("click.ktStrActivate", "[data-kt-str-action='activate-plan']", function (e) {
						e.preventDefault();
						doTransition("Activate");
					});

				return dto;
			});
		}
		return reload();
	}

	function bindDownstream($root, planCode) {
		return call("get_strategy_usage", { plan_code: planCode }).then(function (usage) {
			$root.attr("data-kt-str-live", "1");
			if (!usage || !usage.plan) {
				return usage;
			}
			var plan = usage.plan;
			$root.attr("data-kt-str-bound-code", plan.code || "");
			$root.attr("data-kt-str-route-token", plan.code || plan.id || planCode || "");
			$root.attr("data-kt-str-plan-id", plan.id || "");
			/* Shared plan chrome — never paint ad-hoc UPPERCASE / vN byline variants. */
			bindPlanChrome($root, plan);

			var counts = usage.counts || {};
			var modules = [
				"Budget",
				"Demand",
				"Planning",
				"Tender",
				"Contract",
				"Asset",
				"Disposal",
			];
			modules.forEach(function (mod) {
				var n = counts[mod] || 0;
				$root.attr("data-kt-str-usage-" + mod.toLowerCase(), String(n));
				$root.find('[data-kt-str-down-count="' + mod + '"]').text(String(n));
				var $chip = $root.find('[data-kt-str-down-chip="' + mod + '"]');
				if (n > 0) {
					$chip.removeClass("opacity-60");
					$chip
						.find(".material-symbols-outlined")
						.removeClass("text-on-surface-variant")
						.addClass("text-primary");
					$chip
						.find(".text-body-md")
						.removeClass("text-on-surface-variant")
						.addClass("text-on-surface");
				} else {
					$chip.addClass("opacity-60");
				}
			});

			var allRows = usage.rows || [];
			$root.data("ktStrDownRows", allRows);

			var targets = {};
			var statuses = {};
			allRows.forEach(function (r) {
				if (r.target && r.target.code) {
					targets[r.target.code] = r.target.name || r.target.code;
				}
				if (r.status) {
					statuses[r.status] = true;
				}
			});
			var $tgt = $root.find("[data-kt-str-down-filter-target]");
			var tgtVal = $tgt.val() || "";
			$tgt.find("option:not(:first)").remove();
			Object.keys(targets)
				.sort()
				.forEach(function (code) {
					$tgt.append(
						$("<option></option>").attr("value", code).text(code + " — " + targets[code])
					);
				});
			$tgt.val(tgtVal);

			var $st = $root.find("[data-kt-str-down-filter-status]");
			var stVal = $st.val() || "";
			$st.find("option:not(:first)").remove();
			Object.keys(statuses)
				.sort()
				.forEach(function (s) {
					$st.append($("<option></option>").attr("value", s).text(s));
				});
			$st.val(stVal);

			function refTypeClass(rt) {
				if (rt === "Primary alignment") {
					return "bg-primary text-on-primary";
				}
				if (rt === "Supporting alignment") {
					return "bg-secondary-fixed text-on-secondary-fixed-variant";
				}
				return "bg-surface-container-highest text-on-surface";
			}

			function formatDownDate(iso) {
				if (!iso) {
					return "—";
				}
				try {
					var d = String(iso).slice(0, 10);
					return frappe.datetime.str_to_user ? frappe.datetime.str_to_user(d) : d;
				} catch (e) {
					return String(iso).slice(0, 10);
				}
			}

			function paintDownRows(rows) {
				var $tb = $root.find("[data-kt-str-down-tbody]");
				$tb.empty();
				if (!rows.length) {
					$tb.append(
						'<tr data-kt-str-down-empty><td colspan="7" class="py-8 px-4 text-center text-on-surface-variant text-body-md">' +
							esc(__("No downstream references match the current filters.")) +
							"</td></tr>"
					);
					return;
				}
				rows.forEach(function (r) {
					var rec = r.record || {};
					var tgt = r.target || {};
					var rt = r.reference_type || "—";
					var tr =
						'<tr class="hover:bg-surface-container transition-colors group" data-kt-str-down-row data-kt-str-down-module="' +
						esc(r.module || "") +
						'" data-kt-str-down-code="' +
						esc(rec.code || "") +
						'">' +
						'<td class="py-4 px-4 align-top"><div class="flex flex-col">' +
						'<span class="font-data-mono text-data-mono text-primary font-bold">' +
						esc(rec.code || "—") +
						"</span>" +
						'<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">' +
						esc(rec.name || "") +
						"</span></div></td>" +
						'<td class="py-4 px-4 align-top text-body-md text-on-surface whitespace-nowrap">' +
						esc(r.module || "") +
						"</td>" +
						'<td class="py-4 px-4 align-top"><div class="flex flex-col">' +
						'<span class="font-data-mono text-data-mono text-on-surface font-medium">' +
						esc(tgt.code || "—") +
						"</span>" +
						(tgt.name
							? '<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">' +
								esc(tgt.name) +
								"</span>"
							: "") +
						"</div></td>" +
						'<td class="py-4 px-4 align-top whitespace-nowrap">' +
						'<span class="inline-flex items-center px-2.5 py-1 rounded-full font-label-caps text-[11px] font-bold ' +
						refTypeClass(rt) +
						'">' +
						esc(rt) +
						"</span></td>" +
						'<td class="py-4 px-4 align-top whitespace-nowrap">' +
						'<div class="inline-flex items-center gap-1.5 text-body-md font-medium text-on-surface">' +
						'<span class="material-symbols-outlined text-[16px]">circle</span> ' +
						esc(r.status || "—") +
						"</div></td>" +
						'<td class="py-4 px-4 align-top font-data-mono text-data-mono text-on-surface whitespace-nowrap">' +
						esc(formatDownDate(r.modified)) +
						"</td>" +
						'<td class="py-4 px-4 align-top text-right whitespace-nowrap">' +
						'<button type="button" class="text-secondary hover:text-primary transition-colors p-1 rounded hover:bg-surface-container" data-kt-str-action="view-downstream" data-kt-str-down-doctype="' +
						esc(r.doctype || "") +
						'" data-kt-str-down-id="' +
						esc(rec.id || "") +
						'" aria-label="' +
						esc(__("View")) +
						'">' +
						'<span class="material-symbols-outlined">visibility</span></button></td></tr>';
					$tb.append(tr);
				});
			}

			function applyDownFilters() {
				var q = String($root.find("[data-kt-str-down-search]").val() || "")
					.trim()
					.toLowerCase();
				var mod = $root.find("[data-kt-str-down-filter-module]").val() || "";
				var tgtCode = $root.find("[data-kt-str-down-filter-target]").val() || "";
				var rt = $root.find("[data-kt-str-down-filter-reftype]").val() || "";
				var st = $root.find("[data-kt-str-down-filter-status]").val() || "";
				var filtered = allRows.filter(function (r) {
					if (mod && r.module !== mod) {
						return false;
					}
					if (tgtCode && (!r.target || r.target.code !== tgtCode)) {
						return false;
					}
					if (rt && r.reference_type !== rt) {
						return false;
					}
					if (st && r.status !== st) {
						return false;
					}
					if (q) {
						var hay = [
							r.module,
							(r.record && r.record.code) || "",
							(r.record && r.record.name) || "",
							(r.target && r.target.code) || "",
							(r.target && r.target.name) || "",
							r.reference_type || "",
							r.status || "",
						]
							.join(" ")
							.toLowerCase();
						if (hay.indexOf(q) < 0) {
							return false;
						}
					}
					return true;
				});
				paintDownRows(filtered);
			}

			paintDownRows(allRows);

			$root
				.off("input.ktStrDown change.ktStrDown")
				.on(
					"input.ktStrDown change.ktStrDown",
					"[data-kt-str-down-search], [data-kt-str-down-filter-module], [data-kt-str-down-filter-target], [data-kt-str-down-filter-reftype], [data-kt-str-down-filter-status]",
					function () {
						applyDownFilters();
					}
				);

			$root.off("click.ktStrDown").on("click.ktStrDown", "[data-kt-str-action]", function (e) {
				var action = $(this).attr("data-kt-str-action");
				if (action === "clear-down-filters") {
					e.preventDefault();
					e.stopPropagation();
					$root.find("[data-kt-str-down-search]").val("");
					$root.find("[data-kt-str-down-filter-module]").val("");
					$root.find("[data-kt-str-down-filter-target]").val("");
					$root.find("[data-kt-str-down-filter-reftype]").val("");
					$root.find("[data-kt-str-down-filter-status]").val("");
					paintDownRows(allRows);
					return;
				}
				if (action === "view-downstream") {
					e.preventDefault();
					e.stopPropagation();
					var dt = $(this).attr("data-kt-str-down-doctype");
					var id = $(this).attr("data-kt-str-down-id");
					if (dt && id) {
						frappe.set_route("Form", dt, id);
					}
				}
			});

			return usage;
		});
	}

	function formatAuditWhen(iso) {
		if (!iso) {
			return "—";
		}
		try {
			if (frappe.datetime && frappe.datetime.str_to_user) {
				return frappe.datetime.str_to_user(iso);
			}
		} catch (e) {
			/* fall through */
		}
		return String(iso).replace("T", " ").slice(0, 16);
	}

	function renderAuditRows(rows) {
		if (!(rows || []).length) {
			return (
				'<tr data-kt-str-empty="1"><td class="py-6 px-4 text-on-surface-variant" colspan="7">' +
				esc(__("No audit events for this plan version yet.")) +
				"</td></tr>"
			);
		}
		return rows
			.map(function (r) {
				var prior = r.prior_state || "";
				var next = r.new_state || "";
				var summary = r.summary || r.event_type || "";
				var stateHtml = "";
				if (prior && next) {
					stateHtml =
						'<span class="text-xs text-on-surface-variant">' +
						esc(prior) +
						'</span><span class="material-symbols-outlined text-[14px] text-outline mx-1">arrow_forward</span><span class="text-xs font-semibold text-status-available">' +
						esc(next) +
						"</span>";
				} else if (summary) {
					stateHtml =
						'<span class="bg-surface-variant px-2 py-0.5 rounded text-xs">' +
						esc(summary) +
						"</span>";
				} else {
					stateHtml = '<span class="text-on-surface-variant">—</span>';
				}
				var record = r.entity_name || r.entity_type || "—";
				return (
					'<tr class="hover:bg-surface-container transition-colors group cursor-pointer" data-kt-str-audit-id="' +
					esc(r.name) +
					'">' +
					'<td class="py-2.5 px-4 text-on-surface-variant">' +
					esc(formatAuditWhen(r.event_at)) +
					"</td>" +
					'<td class="py-2.5 px-4 font-medium text-on-surface">' +
					esc(r.event_type || summary) +
					"</td>" +
					'<td class="py-2.5 px-4 font-data-mono text-xs text-primary">' +
					esc(record) +
					"</td>" +
					'<td class="py-2.5 px-4">' +
					esc(r.actor || "—") +
					"</td>" +
					'<td class="py-2.5 px-4"><div class="flex items-center gap-2 flex-wrap">' +
					stateHtml +
					"</div></td>" +
					'<td class="py-2.5 px-4 text-on-surface-variant">' +
					esc(r.reason || "—") +
					"</td>" +
					'<td class="py-2.5 px-4 text-right"><button type="button" class="text-secondary hover:text-primary font-medium text-xs" data-kt-str-action="view-audit">' +
					esc(__("View")) +
					"</button></td></tr>"
				);
			})
			.join("");
	}

	function bindAudit($root, planCode) {
		return Promise.all([
			call("get_plan_overview", { plan_code: planCode }).catch(function () {
				return null;
			}),
			call("list_audit_events", { plan_code: planCode }),
		]).then(function (parts) {
			var dto = parts[0];
			var rows = parts[1] || [];
			$root.attr("data-kt-str-live", "1");
			$root.attr("data-kt-str-audit-count", String(rows.length));
			if (dto && dto.plan) {
				var plan = dto.plan;
				$root.attr("data-kt-str-bound-code", plan.code || "");
				$root.attr("data-kt-str-route-token", plan.code || plan.id || planCode || "");
				$root.attr("data-kt-str-plan-id", plan.id || "");
				bindPlanChrome($root, plan);
			}
			var pager = attachTablePagination($root, {
				renderPage: function (pageRows) {
					$root.find("[data-kt-str-audit-tbody]").html(renderAuditRows(pageRows));
				},
			});
			pager.setRows(rows, true);
			return rows;
		});
	}

	function bindCorrective($root, planCode) {
		return call("list_corrective_actions", { plan_code: planCode }).then(function (rows) {
			$root.attr("data-kt-str-live", "1");
			$root.attr("data-kt-str-ca-count", String((rows || []).length));
			return rows;
		});
	}

	function bindPvoEditor($root) {
		var route = frappe.get_route() || [];
		var code = route.length > 1 ? route[1] : null;
		if (!code) {
			$root.attr("data-kt-str-live", "1");
			return Promise.resolve(null);
		}
		return call("get_pvo", { objective_code: code }).then(function (pvo) {
			if (!pvo) {
				return;
			}
			$root.attr("data-kt-str-live", "1");
			$root.find("input, textarea").each(function () {
				var $el = $(this);
				var name = ($el.attr("name") || $el.attr("data-field") || "").toLowerCase();
				if (name.indexOf("title") >= 0) {
					$el.val(pvo.name);
				}
				if (name.indexOf("code") >= 0) {
					$el.val(pvo.code);
				}
			});
			return pvo;
		});
	}

	function resultTone(status) {
		var lower = String(status || "")
			.trim()
			.toLowerCase();
		if (lower === "at risk") {
			return "at-risk";
		}
		if (lower === "on track") {
			return "on-track";
		}
		if (lower === "off track") {
			return "off-track";
		}
		return "neutral";
	}

	function workflowIcon(status) {
		var s = String(status || "").toLowerCase();
		if (s === "verified") {
			return "verified";
		}
		if (s === "returned") {
			return "replay";
		}
		if (s === "rejected") {
			return "cancel";
		}
		if (s === "draft") {
			return "edit";
		}
		return "hourglass_empty";
	}

	function resultIcon(status) {
		var s = String(status || "").toLowerCase();
		if (s === "on track") {
			return "check_circle";
		}
		if (s === "off track") {
			return "error";
		}
		if (s === "at risk") {
			return "warning";
		}
		return "info";
	}

	function paintVerifyPills($root, workflowStatus, resultStatus) {
		$root.attr("data-kt-str-workflow-status", workflowStatus || "");
		$root.attr("data-kt-str-result-status", resultStatus || "");
		$root.find("[data-kt-str-meas-workflow-label]").text(
			workflowStatus ? String(workflowStatus).toUpperCase() : "—"
		);
		$root.find("[data-kt-str-meas-workflow-icon]").text(workflowIcon(workflowStatus));
		var tone = resultTone(resultStatus);
		$root.find("[data-kt-str-result]").text(
			resultStatus ? String(resultStatus).toUpperCase() : "—"
		);
		$root.find("[data-kt-str-meas-result-icon]").text(resultIcon(resultStatus));
		$root.find("[data-kt-str-meas-result-pill]").attr("data-kt-str-meas-tone", tone);
		$root.find("[data-kt-str-meas-tone-rail]").attr("data-kt-str-meas-tone", tone);
		$root.find("[data-kt-str-meas-submitted-body]").attr("data-kt-str-meas-tone", tone);
	}

	function paintVerifySurface($root, m, tgt, planCode) {
		paintVerifyPills($root, m.workflow_status, m.result_status);

		if (tgt.baseline_numeric != null) {
			var bl =
				String(tgt.baseline_numeric) +
				"%" +
				(tgt.baseline_as_of
					? " " +
						__("as at") +
						" " +
						(frappe.datetime.str_to_user
							? frappe.datetime.str_to_user(String(tgt.baseline_as_of).slice(0, 10))
							: String(tgt.baseline_as_of).slice(0, 10))
					: "");
			$root.find("[data-kt-str-meas-baseline]").text(bl);
		}
		if (m.measurement_period_start && m.measurement_period_end) {
			$root
				.find("[data-kt-str-meas-period-label]")
				.text(formatPeriod(m.measurement_period_start, m.measurement_period_end));
		} else if (tgt.period_start && tgt.period_end) {
			$root
				.find("[data-kt-str-meas-period-label]")
				.text(formatPeriod(tgt.period_start, tgt.period_end));
		}
		if (m.actual_numeric != null) {
			$root.find("[data-kt-str-actual]").text(String(m.actual_numeric) + "%");
		} else {
			$root.find("[data-kt-str-actual]").text("—");
		}
		if (m.measurement_date) {
			var md = String(m.measurement_date).slice(0, 10);
			$root
				.find("[data-kt-str-meas-date-display]")
				.text(frappe.datetime.str_to_user ? frappe.datetime.str_to_user(md) : md);
		} else {
			$root.find("[data-kt-str-meas-date-display]").text("—");
		}
		$root
			.find("[data-kt-str-meas-evidence-source]")
			.text(m.evidence_source || "—");
		$root
			.find("[data-kt-str-meas-evidence-ref]")
			.text(m.evidence_reference || __("No evidence reference"));
		$root
			.find("[data-kt-str-meas-evidence-meta]")
			.text(m.evidence_source || __("Evidence reference"));
		$root.find("[data-kt-str-meas-submitted-by]").text(m.submitted_by || "—");
		$root
			.find("[data-kt-str-meas-commentary]")
			.text(m.commentary ? '"' + m.commentary + '"' : "—");
		if (m.verification_comment) {
			$root.find("[data-kt-str-meas-verify-comments]").val(m.verification_comment);
		}

		var rs = String(m.result_status || "").toLowerCase();
		var $ca = $root.find("[data-kt-str-meas-ca-box]");
		var $exc = $root.find("[data-kt-str-meas-exception-box]");
		if (rs === "at risk") {
			$ca.removeClass("hidden").show();
			$exc.addClass("hidden").hide();
		} else if (rs === "off track") {
			$ca.addClass("hidden").hide();
			$exc.removeClass("hidden").css("display", "flex");
		} else {
			$ca.addClass("hidden").hide();
			$exc.addClass("hidden").hide();
		}

		$root
			.off("change.ktStrExc")
			.on("change.ktStrExc", "[data-kt-str-meas-exception]", function () {
				var on = $(this).is(":checked");
				$root.find("[data-kt-str-meas-exception-reason]").toggleClass("hidden", !on);
			});

		var canDecide = m.workflow_status === "Submitted" && !!m.id;
		var sameUser =
			m.submitted_by &&
			m.submitted_by === frappe.session.user &&
			frappe.session.user !== "Administrator";
		if (sameUser) {
			canDecide = false;
			$root
				.find("[data-kt-str-meas-sod-text]")
				.text(
					__(
						"You submitted this measurement. Another Performance Verifier must decide."
					)
				);
		} else if (!m.id || m.is_new) {
			$root
				.find("[data-kt-str-meas-sod-text]")
				.text(__("No submitted measurement is available to verify for this target."));
		} else if (m.workflow_status && m.workflow_status !== "Submitted") {
			$root
				.find("[data-kt-str-meas-sod-text]")
				.text(
					__("This measurement is {0}. Decisions are locked.", [
						m.workflow_status,
					])
				);
		}
		$root
			.find(
				"[data-kt-str-action='verify-measurement'], [data-kt-str-action='request-changes'], [data-kt-str-action='reject-measurement']"
			)
			.prop("disabled", !canDecide)
			.toggleClass("opacity-50 cursor-not-allowed", !canDecide);
	}

	function applyVerifyDecision($root, m, tr) {
		if (!tr) {
			return;
		}
		m.workflow_status = tr.workflow_status || m.workflow_status;
		m.result_status = tr.result_status || m.result_status;
		// Stay on verify page — only refresh local state / pills (no set_route).
		paintVerifyPills($root, m.workflow_status, m.result_status);
		$root
			.find(
				"[data-kt-str-action='verify-measurement'], [data-kt-str-action='request-changes'], [data-kt-str-action='reject-measurement']"
			)
			.prop("disabled", true)
			.addClass("opacity-50 cursor-not-allowed");
	}

	function bindMeasurementForm($root, targetCode, mode, planCode) {
		var args = { target_code: targetCode, purpose: mode || "submit" };
		if (planCode) {
			args.plan_code = planCode;
		}
		return call("get_measurement", args)
			.then(function (m) {
				$root.attr("data-kt-str-live", "1");
				$root.attr("data-kt-str-plan-code", planCode || "");
				if (!m || !m.performance_target) {
					frappe.show_alert({
						message: __("Could not load measurement for {0}", [targetCode || ""]),
						indicator: "orange",
					});
					return;
				}
				var tgt = m.performance_target;
				$root.attr("data-kt-str-target-id", tgt.id || "");
				$root.attr("data-kt-str-measurement-id", m.id || "");
				$root.find("[data-kt-str-target-code]").text(tgt.code || targetCode || "");
				$root.find("[data-kt-str-target-title]").text(tgt.name || "");
				if (tgt.target_numeric != null) {
					var dir = tgt.comparison_direction || "";
					var prefix =
						dir === "At least" || dir === "Increase to"
							? "≥ "
							: dir === "At most" || dir === "Reduce to"
								? "≤ "
								: "";
					$root
						.find("[data-kt-str-meas-target-value]")
						.text(prefix + String(tgt.target_numeric) + "%");
				}
				if (tgt.tolerance_value != null) {
					var tolBase = parseFloat(tgt.target_numeric);
					var tol = parseFloat(tgt.tolerance_value);
					if (!isNaN(tolBase) && !isNaN(tol)) {
						$root
							.find("[data-kt-str-meas-tolerance]")
							.text(String(Math.round((tolBase - tol) * 1000) / 1000) + "%");
					}
				}
				if (tgt.baseline_numeric != null) {
					$root
						.find("[data-kt-str-meas-baseline]")
						.text(String(tgt.baseline_numeric) + "%");
				}
				$root
					.find("[data-kt-str-meas-indicator]")
					.text(tgt.indicator_name || "—");
				$root
					.find("[data-kt-str-meas-frequency]")
					.text(tgt.measurement_frequency || "—");
				$root.find("[data-kt-str-meas-data-source]").text(tgt.data_source || "—");

				var $periodStart = $root.find("[data-kt-str-meas-period-start]");
				var $periodEnd = $root.find("[data-kt-str-meas-period-end]");
				var $measDate = $root.find("[data-kt-str-meas-date]");
				if (tgt.period_start) {
					$periodStart.attr("min", tgt.period_start);
					$periodEnd.attr("min", tgt.period_start);
					$measDate.attr("min", tgt.period_start);
				}
				if (tgt.period_end) {
					$periodStart.attr("max", tgt.period_end);
					$periodEnd.attr("max", tgt.period_end);
					$measDate.attr("max", tgt.period_end);
				}
				if (tgt.period_start && tgt.period_end) {
					// Display in site/user date style (dd/mm/yyyy); keep ISO on inputs for type=date.
					var rangeLabel = formatPeriod(tgt.period_start, tgt.period_end).replace(
						/–/g,
						" – "
					);
					var rangeHtml =
						'<span class="kt-str-meas-period-range" data-kt-str-meas-period-range>' +
						esc(rangeLabel) +
						"</span>";
					$root
						.find("[data-kt-str-meas-period-hint]")
						.html(
							__("Target period:") +
								" " +
								rangeHtml +
								". " +
								__(
									"Measurement period must fall within this range unless an authorised final measurement is recorded."
								)
						);
				}

				if (mode === "verify") {
					paintVerifySurface($root, m, tgt, planCode);
				} else if (m.is_new) {
					// Do not keep fixture MOH seed values on a blank submit for this plan/target.
					$root.find("[data-kt-str-actual]").val("");
					$root.find("[data-kt-str-meas-evidence-source]").val("");
					$root.find("[data-kt-str-meas-evidence-ref]").val("");
					$root.find("[data-kt-str-meas-commentary]").val("");
					$periodStart.val("");
					$periodEnd.val("");
					$measDate.val("");
				} else {
					if (m.actual_numeric != null) {
						$root.find("[data-kt-str-actual]").val(m.actual_numeric);
					}
					if (m.evidence_source) {
						$root.find("[data-kt-str-meas-evidence-source]").val(m.evidence_source);
					}
					if (m.evidence_reference) {
						$root.find("[data-kt-str-meas-evidence-ref]").val(m.evidence_reference);
					}
					if (m.commentary) {
						$root.find("[data-kt-str-meas-commentary]").val(m.commentary);
					}
					if (m.measurement_period_start) {
						$periodStart.val(String(m.measurement_period_start).slice(0, 10));
					}
					if (m.measurement_period_end) {
						$periodEnd.val(String(m.measurement_period_end).slice(0, 10));
					}
					if (m.measurement_date) {
						$measDate.val(String(m.measurement_date).slice(0, 10));
					}
				}

				function deriveClient(actualRaw) {
					var actualStr = String(actualRaw == null ? "" : actualRaw).trim();
					if (!actualStr) {
						return { result_status: "", variance: null };
					}
					var actual = parseFloat(actualStr);
					if (isNaN(actual)) {
						return { result_status: "", variance: null };
					}
					var target = parseFloat(tgt.target_numeric);
					if (isNaN(target)) {
						return { result_status: "", variance: null };
					}
					var tol =
						tgt.tolerance_value == null || tgt.tolerance_value === ""
							? null
							: parseFloat(tgt.tolerance_value);
					var direction = tgt.comparison_direction || "";
					var mtype = tgt.measurement_type || "Percentage";
					if (mtype === "Milestone" || mtype === "Boolean") {
						return {
							result_status: actual >= 1 ? "On track" : "Off track",
							variance: null,
						};
					}
					var variance = actual - target;
					var status = "Off track";
					if (direction === "At least" || direction === "Increase to") {
						if (actual >= target) {
							status = "On track";
						} else if (tol != null && !isNaN(tol) && actual >= target - tol) {
							status = "At risk";
						} else {
							status = "Off track";
						}
					} else if (direction === "At most" || direction === "Reduce to") {
						if (actual <= target) {
							status = "On track";
						} else if (tol != null && !isNaN(tol) && actual <= target + tol) {
							status = "At risk";
						} else {
							status = "Off track";
						}
					} else if (direction === "Equal to") {
						if (tol != null && !isNaN(tol)) {
							status = Math.abs(actual - target) <= tol ? "On track" : "Off track";
						} else {
							status = actual === target ? "On track" : "Off track";
						}
					} else {
						status = actual >= target ? "On track" : "Off track";
					}
					return { result_status: status, variance: variance };
				}

				function paintDerived(status, variance) {
					status = String(status || "").trim();
					var tone = "neutral";
					var lower = status.toLowerCase();
					if (lower === "at risk") {
						tone = "at-risk";
					} else if (lower === "on track") {
						tone = "on-track";
					} else if (lower === "off track") {
						tone = "off-track";
					} else if (lower === "no data") {
						tone = "neutral";
						status = "";
					}
					$root.find("[data-kt-str-meas-derived]").attr("data-kt-str-meas-tone", tone);
					$root
						.find("[data-kt-str-result]")
						.text(status ? status.toUpperCase() : "—");

					var targetNum = parseFloat(tgt.target_numeric);
					var tolNum = parseFloat(tgt.tolerance_value);
					var explain = "";
					if (lower === "on track") {
						explain = __("Actual meets or exceeds the target.");
					} else if (lower === "at risk" && !isNaN(targetNum) && !isNaN(tolNum)) {
						explain = __(
							"Actual is below the {0}% target but remains within the {1}% tolerance.",
							[String(targetNum), String(Math.round((targetNum - tolNum) * 1000) / 1000)]
						);
					} else if (lower === "off track" && !isNaN(targetNum)) {
						explain = __("Actual is outside the {0}% target and tolerance band.", [
							String(targetNum),
						]);
					} else {
						explain = __("Enter an actual value to derive the result.");
					}
					$root.find("[data-kt-str-meas-result-explain]").text(explain);

					if (variance != null && variance !== "") {
						var v = parseFloat(variance);
						var rounded = Math.round(v * 100) / 100;
						var vLabel =
							(rounded > 0 ? "+" : rounded < 0 ? "−" : "") +
							String(Math.abs(rounded)) +
							" pp";
						$root
							.find("[data-kt-str-meas-variance]")
							.html(
								'<span class="material-symbols-outlined text-sm">' +
									(v < 0 ? "trending_down" : v > 0 ? "trending_up" : "trending_flat") +
									'</span> <span data-kt-str-meas-variance-text>' +
									esc(vLabel) +
									"</span>"
							);
					} else {
						$root
							.find("[data-kt-str-meas-variance]")
							.html(
								'<span class="material-symbols-outlined text-sm">trending_flat</span> <span data-kt-str-meas-variance-text>—</span>'
							);
					}
				}

				paintDerived(m.result_status, m.variance);
				$root
					.off("input.ktStrMeasDerive change.ktStrMeasDerive")
					.on("input.ktStrMeasDerive change.ktStrMeasDerive", "[data-kt-str-actual]", function () {
						var preview = deriveClient($(this).val());
						paintDerived(preview.result_status, preview.variance);
					});

				$root.off("click.ktStrMeasSave").on("click.ktStrMeasSave", "[data-kt-str-action]", function (e) {
					var action = $(this).attr("data-kt-str-action");
					if (action === "cancel") {
						e.preventDefault();
						var backPlan =
							planCode ||
							$root.attr("data-kt-str-plan-code") ||
							kentender_strategy.alignment.FIXTURE_PLAN;
						frappe.set_route("strategy-plan-measurements", backPlan);
						return;
					}
					function collectMeasPayload() {
						var periodStart = $root.find("[data-kt-str-meas-period-start]").val();
						var periodEnd = $root.find("[data-kt-str-meas-period-end]").val();
						var measDate = $root.find("[data-kt-str-meas-date]").val();
						var actualVal = $root.find("[data-kt-str-actual]").val();
						if (!periodStart || !periodEnd || !measDate) {
							frappe.show_alert({
								message: __("Period start, period end, and measurement date are required."),
								indicator: "orange",
							});
							return null;
						}
						return {
							id: m.id || undefined,
							performance_target: tgt.id,
							plan_version: m.plan_version,
							measurement_period_start: periodStart,
							measurement_period_end: periodEnd,
							measurement_date: measDate,
							actual_numeric: actualVal || null,
							evidence_reference:
								$root.find("[data-kt-str-meas-evidence-ref]").val() ||
								m.evidence_reference ||
								null,
							evidence_source:
								$root.find("[data-kt-str-meas-evidence-source]").val() ||
								m.evidence_source ||
								null,
							commentary: $root.find("[data-kt-str-meas-commentary]").val() || null,
						};
					}

					function applySaveResult(res) {
						if (res && res.id) {
							m.id = res.id;
							$root.attr("data-kt-str-measurement-id", res.id);
						}
						if (res && res.result_status) {
							paintDerived(res.result_status, res.variance);
						}
						if (res && res.workflow_status) {
							m.workflow_status = res.workflow_status;
							$root.attr("data-kt-str-workflow-status", res.workflow_status);
						}
					}

					if (action === "save-draft") {
						e.preventDefault();
						e.stopPropagation();
						var draftPayload = collectMeasPayload();
						if (!draftPayload) {
							return;
						}
						call("save_measurement_draft", { payload: draftPayload }).then(function (res) {
							applySaveResult(res);
							frappe.show_alert({ message: __("Draft saved"), indicator: "blue" });
						});
					}
					if (action === "submit-measurement" && mode === "submit") {
						e.preventDefault();
						e.stopPropagation();
						var submitPayload = collectMeasPayload();
						if (!submitPayload) {
							return;
						}
						// Persist current fields, then Submit — stay on this page (same as Save draft).
						call("save_measurement_draft", { payload: submitPayload })
							.then(function (res) {
								applySaveResult(res);
								if (!m.id) {
									frappe.show_alert({
										message: __("Could not save measurement before submit"),
										indicator: "red",
									});
									return null;
								}
								return call("transition_measurement", {
									name: m.id,
									action: "Submit",
								});
							})
							.then(function (tr) {
								if (!tr) {
									return;
								}
								m.workflow_status = tr.workflow_status || "Submitted";
								$root.attr("data-kt-str-workflow-status", m.workflow_status);
								if (tr.result_status) {
									paintDerived(tr.result_status, tr.variance);
								}
								frappe.show_alert({
									message: __("Measurement submitted"),
									indicator: "green",
								});
							});
					}
					if (mode === "verify" && action === "view-evidence") {
						e.preventDefault();
						e.stopPropagation();
						var ref = m.evidence_reference || "";
						if (!ref) {
							frappe.show_alert({
								message: __("No evidence reference recorded"),
								indicator: "orange",
							});
							return;
						}
						if (/^https?:\/\//i.test(ref)) {
							window.open(ref, "_blank", "noopener");
						} else {
							frappe.show_alert({
								message: __("Evidence reference: {0}", [ref]),
								indicator: "blue",
							});
						}
						return;
					}
					if (mode === "verify" && (action === "verify-measurement" || action === "request-changes" || action === "reject-measurement")) {
						e.preventDefault();
						e.stopPropagation();
						if (!m.id || m.workflow_status !== "Submitted") {
							frappe.show_alert({
								message: __("No submitted measurement available to decide"),
								indicator: "orange",
							});
							return;
						}
						var comments = (
							$root.find("[data-kt-str-meas-verify-comments]").val() || ""
						).trim();
						if (
							(action === "request-changes" || action === "reject-measurement") &&
							!comments
						) {
							frappe.show_alert({
								message: __("Verification comments are required for Return or Reject"),
								indicator: "orange",
							});
							return;
						}
						var apiAction =
							action === "verify-measurement"
								? "Verify"
								: action === "request-changes"
									? "Return"
									: "Reject";
						var args = { name: m.id, action: apiAction, reason: comments || null };
						if (apiAction === "Verify") {
							var excOn = $root.find("[data-kt-str-meas-exception]").is(":checked");
							var excReason = (
								$root.find("[data-kt-str-meas-exception-reason]").val() || ""
							).trim();
							if (String(m.result_status || "").toLowerCase() === "off track" && excOn) {
								if (!excReason) {
									frappe.show_alert({
										message: __("Exception reason is required"),
										indicator: "orange",
									});
									return;
								}
								args.authorised_exception = 1;
								args.exception_reason = excReason;
							}
						}
						call("transition_measurement", args)
							.then(function (tr) {
								// Apply decision UI immediately and never navigate away.
								applyVerifyDecision($root, m, tr);
								if (apiAction === "Verify") {
									var wantCa =
										String(tr.result_status || m.result_status || "")
											.toLowerCase() === "at risk" &&
										$root.find("[data-kt-str-meas-create-ca]").is(":checked");
									if (wantCa) {
										return call("upsert_corrective_action", {
											payload: {
												performance_measurement: m.id,
												performance_target: tgt.id,
												plan_version: m.plan_version,
												action: "Address at-risk performance",
												owner: m.submitted_by || frappe.session.user,
												due_date: frappe.datetime.add_days(
													frappe.datetime.get_today(),
													30
												),
												expected_result: "Return to On track performance",
												status: "Open",
											},
										})
											.then(function () {
												return tr;
											})
											.catch(function () {
												frappe.show_alert({
													message: __(
														"Measurement verified, but corrective action could not be created"
													),
													indicator: "orange",
												});
												return tr;
											});
									}
								}
								return tr;
							})
							.then(function (tr) {
								if (!tr) {
									return;
								}
								var msg =
									apiAction === "Verify"
										? __("Measurement verified")
										: apiAction === "Return"
											? __("Measurement returned for correction")
											: __("Measurement rejected");
								frappe.show_alert({
									message: msg,
									indicator: apiAction === "Verify" ? "green" : "orange",
								});
							})
							.catch(function (err) {
								console.warn("verify decision failed", err);
								frappe.show_alert({
									message: __("Could not complete verification decision"),
									indicator: "red",
								});
							});
					}
				});
				return m;
			})
			.catch(function (err) {
				$root.attr("data-kt-str-live", "0");
				console.warn("bindMeasurementForm failed", err);
				frappe.show_alert({
					message: __("Could not load measurement for {0}", [targetCode || ""]),
					indicator: "orange",
				});
				throw err;
			});
	}

	function afterMount(pageSlug, $root, planCode, targetCode) {
		var live = kentender_strategy.live;
		if (pageSlug === "strategy-alignment") {
			return live.bindPortfolio($root);
		}
		if (pageSlug === "strategy-plan-create") {
			return live.bindCreatePlan($root);
		}
		if (pageSlug === "strategy-plan-overview") {
			return live.bindOverview($root, planCode);
		}
		if (pageSlug === "strategy-plan-structure") {
			return live.bindStructure($root, planCode);
		}
		if (pageSlug === "strategy-pvo-catalogue") {
			return live.bindPvoCatalogue($root);
		}
		if (pageSlug === "strategy-pvo-editor") {
			return live.bindPvoEditor($root);
		}
		if (pageSlug === "strategy-plan-value-commitments") {
			return live.bindCommitments($root, planCode);
		}
		if (pageSlug === "strategy-plan-measurements") {
			return live.bindMeasurements($root, planCode);
		}
		if (pageSlug === "strategy-measurement-submit") {
			return live.bindMeasurementForm($root, targetCode, "submit", planCode);
		}
		if (pageSlug === "strategy-measurement-verify") {
			return live.bindMeasurementForm($root, targetCode, "verify", planCode);
		}
		if (pageSlug === "strategy-corrective-actions") {
			return live.bindCorrective($root, planCode || kentender_strategy.alignment.FIXTURE_PLAN);
		}
		if (pageSlug === "strategy-plan-review") {
			return live.bindReview($root, planCode);
		}
		if (pageSlug === "strategy-plan-downstream-usage") {
			return live.bindDownstream($root, planCode);
		}
		if (pageSlug === "strategy-plan-audit") {
			return live.bindAudit($root, planCode);
		}
		return Promise.resolve();
	}

	kentender_strategy.live = {
		call: call,
		bindPortfolio: bindPortfolio,
		bindCreatePlan: bindCreatePlan,
		bindOverview: bindOverview,
		bindStructure: bindStructure,
		bindPvoCatalogue: bindPvoCatalogue,
		bindPvoEditor: bindPvoEditor,
		bindCommitments: bindCommitments,
		bindMeasurements: bindMeasurements,
		bindMeasurementForm: bindMeasurementForm,
		bindReview: bindReview,
		bindDownstream: bindDownstream,
		bindAudit: bindAudit,
		bindCorrective: bindCorrective,
		afterMount: afterMount,
	};
})();
