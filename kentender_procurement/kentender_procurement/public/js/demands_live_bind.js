// DEM-UI-01 — live bind for Stitch Demands workspace canvas.
frappe.provide("kentender_procurement.live");

(function () {
	"use strict";

	var API = "kentender_procurement.demands.api.list_demands_workspace";

	function esc(v) {
		return frappe.utils.escape_html(String(v == null ? "" : v));
	}

	function call(args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: API,
				args: args || {},
				callback: function (r) {
					if (r.exc) {
						reject(r.exc);
						return;
					}
					resolve(r.message || {});
				},
				error: function (err) {
					reject(err);
				},
			});
		});
	}

	function statusPill(status) {
		var s = String(status || "");
		var lower = s.toLowerCase();
		var cls =
			"inline-flex items-center px-2 py-0.5 rounded-full font-label-caps text-[11px] whitespace-nowrap ";
		if (lower.indexOf("return") >= 0) {
			cls += "bg-status-exhausted/10 text-status-exhausted";
		} else if (lower.indexOf("review") >= 0) {
			cls += "bg-status-reserved/10 text-status-reserved";
		} else if (lower.indexOf("approved") >= 0 || lower.indexOf("complete") >= 0) {
			cls += "bg-status-available/10 text-status-available";
		} else {
			cls += "bg-surface-container-high text-on-surface-variant";
		}
		return '<span class="' + cls + '">' + esc(s || "—") + "</span>";
	}

	function rowHtml(row) {
		return (
			'<tr class="hover:bg-surface-container transition-colors group" data-demand-id="' +
			esc(row.name) +
			'">' +
			'<td class="py-3 px-4 align-top">' +
			'<div class="font-body-md text-body-md font-medium text-on-surface mb-0.5 line-clamp-2">' +
			esc(row.title || "—") +
			"</div>" +
			'<div class="font-data-mono text-data-mono text-on-surface-variant text-[12px]">' +
			esc(row.demand_code || row.name || "") +
			"</div></td>" +
			'<td class="py-3 px-4 align-top font-body-md text-body-md text-on-surface-variant">' +
			esc(row.owning_unit_label || "—") +
			"</td>" +
			'<td class="py-3 px-4 align-top font-body-md text-body-md text-on-surface-variant whitespace-nowrap">' +
			esc(row.required_by_display || "—") +
			"</td>" +
			'<td class="py-3 px-4 align-top font-data-mono text-data-mono text-on-surface text-right whitespace-nowrap">' +
			esc(row.estimate_display || "—") +
			"</td>" +
			'<td class="py-3 px-4 align-top">' +
			statusPill(row.status) +
			"</td>" +
			'<td class="py-3 px-4 align-top font-body-md text-body-md text-on-surface-variant">' +
			esc(row.current_stage || "—") +
			"</td>" +
			'<td class="py-3 px-4 align-top font-body-md text-body-md text-on-surface-variant">' +
			esc(row.current_owner || "—") +
			"</td>" +
			'<td class="py-3 px-4 align-top text-right">' +
			'<button type="button" class="font-body-md text-body-md text-primary font-medium hover:underline whitespace-nowrap" data-kt-dem-action="open-demand" data-demand-id="' +
			esc(row.name) +
			'" data-route="' +
			esc(row.action_route || "demand-detail") +
			'" data-testid="kt-dem-ui01-row-action">' +
			esc(row.action_label || __("Open")) +
			"</button></td></tr>"
		);
	}

	function showEmpty($root, on) {
		var $wrap = $root.find("[data-kt-dem-table-wrap]");
		var $empty = $root.find("[data-kt-dem-empty]");
		if (on) {
			$wrap.addClass("hidden");
			$empty.removeClass("hidden").addClass("flex");
		} else {
			$wrap.removeClass("hidden");
			$empty.addClass("hidden").removeClass("flex");
		}
	}

	function applySummary($root, summary) {
		var s = summary || {};
		["my_drafts", "returned_to_me", "my_approvals", "budget_confirmations"].forEach(function (k) {
			$root.find('[data-kt-dem-count="' + k + '"]').text(String(s[k] != null ? s[k] : 0));
		});
	}

	function paintEntityOptions($root, entities, selected) {
		var $sel = $root.find('[data-kt-dem-filter="entity"]');
		if (!$sel.length) {
			return;
		}
		var cur = selected != null ? selected : $sel.val() || "";
		var html = '<option value="">' + esc(__("All entities")) + "</option>";
		(entities || []).forEach(function (e) {
			html +=
				'<option value="' +
				esc(e.id) +
				'">' +
				esc(e.name || e.code || e.id) +
				"</option>";
		});
		$sel.html(html);
		if (cur) {
			$sel.val(cur);
		}
	}

	function renderRows($tbody, rows) {
		if (!rows || !rows.length) {
			$tbody.html("");
			return;
		}
		$tbody.html(rows.map(rowHtml).join(""));
	}

	function paintTable($root, rows) {
		var $tbody = $root.find("[data-kt-dem-tbody]");
		if (!rows || !rows.length) {
			showEmpty($root, true);
			$tbody.html("");
			if (
				window.kentender_core &&
				kentender_core.table &&
				typeof kentender_core.table.attachPagination === "function"
			) {
				kentender_core.table
					.attachPagination($root, {
						renderPage: function () {
							$tbody.html("");
						},
					})
					.setRows([], true);
			}
			return;
		}
		showEmpty($root, false);
		if (
			window.kentender_core &&
			kentender_core.table &&
			typeof kentender_core.table.attachPagination === "function"
		) {
			kentender_core.table
				.attachPagination($root, {
					renderPage: function (pageRows) {
						renderRows($tbody, pageRows);
					},
				})
				.setRows(rows, true);
		} else {
			renderRows($tbody, rows);
		}
	}

	function readFilters($root) {
		return {
			queue: $root.attr("data-kt-dem-active-queue") || null,
			search: ($root.find('[data-kt-dem-filter="search"]').val() || "").trim() || null,
			status: ($root.find('[data-kt-dem-filter="status"]').val() || "").trim() || null,
			stage: ($root.find('[data-kt-dem-filter="stage"]').val() || "").trim() || null,
			procuring_entity: ($root.find('[data-kt-dem-filter="entity"]').val() || "").trim() || null,
			page: 1,
			page_size: 500,
		};
	}

	function setActiveQueue($root, queue) {
		var q = queue || "";
		$root.attr("data-kt-dem-active-queue", q);
		$root.find("[data-kt-dem-queue]").removeClass("is-active");
		if (q) {
			$root.find('[data-kt-dem-queue="' + q + '"]').addClass("is-active");
		}
	}

	function clearFilters($root) {
		setActiveQueue($root, "");
		$root.find('[data-kt-dem-filter="search"]').val("");
		$root.find('[data-kt-dem-filter="status"]').val("");
		$root.find('[data-kt-dem-filter="stage"]').val("");
		$root.find('[data-kt-dem-filter="entity"]').val("");
	}

	function bindWorkspace($root) {
		var token = Number($root.attr("data-kt-dem-bind-token") || 0) + 1;
		$root.attr("data-kt-dem-bind-token", String(token));
		$root.attr("data-kt-dem-live", "0");

		function reload() {
			var args = readFilters($root);
			if (!args.queue) {
				args.queue = null;
			}
			return call(args).then(function (data) {
				if (String($root.attr("data-kt-dem-bind-token")) !== String(token)) {
					return;
				}
				$root.attr("data-kt-dem-live", "1");
				applySummary($root, data.summary);
				paintEntityOptions($root, data.entities || [], args.procuring_entity);
				paintTable($root, data.rows || []);
				return data;
			});
		}

		$root.off(".ktDemWs");
		$root.on("click.ktDemWs", "[data-kt-dem-queue]", function (e) {
			e.preventDefault();
			var key = $(this).attr("data-kt-dem-queue") || "";
			var cur = $root.attr("data-kt-dem-active-queue") || "";
			setActiveQueue($root, cur === key ? "" : key);
			reload().catch(function (err) {
				console.warn("Demands queue filter failed", err);
			});
		});
		var debounce = null;
		$root.on("input.ktDemWs", '[data-kt-dem-filter="search"]', function () {
			clearTimeout(debounce);
			debounce = setTimeout(function () {
				reload().catch(function (err) {
					console.warn("Demands search failed", err);
				});
			}, 250);
		});
		$root.on(
			"change.ktDemWs",
			'[data-kt-dem-filter="status"], [data-kt-dem-filter="stage"], [data-kt-dem-filter="entity"]',
			function () {
				reload().catch(function (err) {
					console.warn("Demands filter failed", err);
				});
			}
		);
		$root.on("click.ktDemWs", '[data-kt-dem-action="clear-filters"]', function (e) {
			e.preventDefault();
			clearFilters($root);
			reload().catch(function (err) {
				console.warn("Demands clear filters failed", err);
			});
		});
		$root.on("click.ktDemWs", '[data-kt-dem-action="create"]', function (e) {
			e.preventDefault();
			frappe.set_route("demand-form");
		});
		$root.on("click.ktDemWs", '[data-kt-dem-action="open-demand"]', function (e) {
			e.preventDefault();
			var id = $(this).attr("data-demand-id");
			var route = $(this).attr("data-route") || "demand-detail";
			if (id) {
				frappe.set_route(route, id);
			}
		});

		return reload().catch(function (err) {
			$root.attr("data-kt-dem-live", "0");
			$root.attr("data-kt-dem-error", "1");
			$root.find("[data-kt-dem-tbody]").html(
				'<tr data-kt-dem-error-row="1"><td class="py-6 px-4 font-body-md text-body-md text-error" colspan="8">' +
					esc(__("Could not load demands. Refresh and try again.")) +
					"</td></tr>"
			);
			console.warn("Demands workspace bind failed", err);
		});
	}

	kentender_procurement.live.bindDemandsWorkspace = bindWorkspace;

	/* ---------- DEM-UI-02 / DEM-UI-03 demand form ---------- */

	var FORM_GET = "kentender_procurement.demands.api.get_demand_form";
	var FORM_SAVE = "kentender_procurement.demands.api.save_demand_form";
	var FORM_SUBMIT = "kentender_procurement.demands.api.submit_demand_form";

	function callMethod(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: method,
				args: args || {},
				callback: function (r) {
					if (r.exc) {
						reject(r.exc);
						return;
					}
					resolve(r.message || {});
				},
				error: function (err) {
					reject(err);
				},
			});
		});
	}

	function parseMoney(raw) {
		var s = String(raw == null ? "" : raw).replace(/[^\d.-]/g, "");
		if (!s) {
			return 0;
		}
		var n = parseFloat(s);
		return isNaN(n) ? 0 : n;
	}

	function formatMoney(n) {
		var v = Number(n) || 0;
		try {
			return v.toLocaleString("en-KE", {
				minimumFractionDigits: 0,
				maximumFractionDigits: 2,
			});
		} catch (e) {
			return String(Math.round(v));
		}
	}

	function setLabel($root, key, text) {
		$root.find('[data-kt-dem-label="' + key + '"]').text(text == null ? "" : String(text));
	}

	function setField($root, key, value) {
		var $el = $root.find('[data-kt-dem-field="' + key + '"]');
		if ($el.length) {
			$el.val(value == null ? "" : value);
		}
		if (key === "required_by_date") {
			syncRequiredByDisplay($root, value);
		}
	}

	function formatRequiredByDisplay(iso) {
		if (!iso) {
			return "";
		}
		var s = String(iso).slice(0, 10);
		var parts = s.split("-");
		if (parts.length !== 3) {
			return s;
		}
		// Stitch shows "30 September 2027"; keep concise locale for Desk.
		try {
			var d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
			return d.toLocaleDateString("en-GB", {
				day: "numeric",
				month: "long",
				year: "numeric",
			});
		} catch (e) {
			return s;
		}
	}

	function syncRequiredByDisplay($root, iso) {
		$root.find("[data-kt-dem-date-display]").val(formatRequiredByDisplay(iso || fieldVal($root, "required_by_date")));
	}

	function fieldVal($root, key) {
		return ($root.find('[data-kt-dem-field="' + key + '"]').val() || "").trim();
	}

	function itemRowHtml($root, item) {
		var tpl = $root.find("[data-kt-dem-item-template]")[0];
		if (!tpl) {
			return "";
		}
		var $row = $(tpl.content.cloneNode(true)).find("[data-kt-dem-item-row]");
		item = item || {};
		$row.find('[data-kt-dem-item="description"]').val(item.description || "");
		$row.find('[data-kt-dem-item="quantity"]').val(item.quantity != null ? item.quantity : 1);
		$row.find('[data-kt-dem-item="uom"]').val(item.uom || "Lot");
		var est =
			item.requester_estimate_display ||
			(item.requester_estimate ? formatMoney(item.requester_estimate) : "");
		$row.find('[data-kt-dem-item="requester_estimate"]').val(est);
		var cur = fieldVal($root, "currency") || $root.find('[data-kt-dem-label="currency"]').first().text() || "KES";
		$row.find("[data-kt-dem-currency-prefix]").text(cur);
		return $row;
	}

	function addItemRow($root, item) {
		var $tbody = $root.find("[data-kt-dem-items-tbody]");
		var $row = itemRowHtml($root, item);
		if ($row && $row.length) {
			$tbody.append($row);
		}
	}

	function recalcEstimate($root) {
		var total = 0;
		$root.find("[data-kt-dem-item-row]").each(function () {
			total += parseMoney($(this).find('[data-kt-dem-item="requester_estimate"]').val());
		});
		setLabel($root, "requester_estimate", formatMoney(total));
		return total;
	}

	function collectItems($root) {
		var items = [];
		$root.find("[data-kt-dem-item-row]").each(function () {
			var $r = $(this);
			var desc = ($r.find('[data-kt-dem-item="description"]').val() || "").trim();
			if (!desc) {
				return;
			}
			items.push({
				description: desc,
				quantity: parseMoney($r.find('[data-kt-dem-item="quantity"]').val()) || 1,
				uom: ($r.find('[data-kt-dem-item="uom"]').val() || "Lot").trim(),
				requester_estimate: parseMoney($r.find('[data-kt-dem-item="requester_estimate"]').val()),
			});
		});
		return items;
	}

	function collectValues($root) {
		return {
			procuring_entity: fieldVal($root, "procuring_entity"),
			owner_org_unit: fieldVal($root, "owner_org_unit"),
			title: fieldVal($root, "title"),
			need_statement: fieldVal($root, "need_statement"),
			need_rationale: fieldVal($root, "need_rationale"),
			expected_outcome: fieldVal($root, "expected_outcome"),
			beneficiaries: fieldVal($root, "beneficiaries"),
			delivery_location: fieldVal($root, "delivery_location"),
			required_by_date: fieldVal($root, "required_by_date"),
			demand_route: fieldVal($root, "demand_route") || "Standard",
			route_justification: fieldVal($root, "route_justification"),
			technical_contact: fieldVal($root, "technical_contact"),
			estimate_confidence: fieldVal($root, "estimate_confidence") || "Medium",
			estimate_basis: fieldVal($root, "estimate_basis"),
			requester_estimate: recalcEstimate($root),
			currency: $root.find('[data-kt-dem-label="currency"]').first().text() || "KES",
			urgency: "Medium",
		};
	}

	function toggleRouteJustification($root) {
		var route = fieldVal($root, "demand_route");
		var $wrap = $root.find("[data-kt-dem-route-emergency]");
		if (route === "Emergency") {
			$wrap.removeClass("hidden");
		} else {
			$wrap.addClass("hidden");
		}
	}

	function applyMode($root, demand) {
		var returned = demand && demand.status === "Returned";
		var editing = !!(demand && demand.name);
		$root.toggleClass("kt-dem-form-returned", returned);
		$root.find("[data-kt-dem-returned-only]").toggleClass("hidden", !returned);
		$root.find("[data-kt-dem-edit-only]").toggleClass("hidden", !editing);
		if (returned) {
			setLabel($root, "page_title", demand.title || __("Demand"));
			setLabel(
				$root,
				"page_subtitle",
				__("Current stage:") + " " + (demand.current_stage || __("Request preparation"))
			);
			setLabel($root, "submit_label", __("Resubmit"));
			$root.find('[data-kt-dem-action="save"]').text(__("Save changes"));
			$root.find('[data-kt-dem-action="cancel"]').text(__("Cancel demand"));
			var notice = demand.return_notice || {};
			setLabel($root, "returned_by", notice.returned_by || "—");
			setLabel($root, "returned_at", notice.returned_at_display || "—");
			setLabel($root, "return_reason", notice.reason || "—");
		} else if (editing) {
			setLabel($root, "page_title", __("Edit demand"));
			setLabel(
				$root,
				"page_subtitle",
				__("Describe what is needed, why it is needed and when it is required.")
			);
			setLabel($root, "submit_label", __("Submit for business review"));
			$root.find('[data-kt-dem-action="save"]').text(__("Save draft"));
			$root.find('[data-kt-dem-action="cancel"]').text(__("Cancel"));
		} else {
			setLabel($root, "page_title", __("Create demand"));
			setLabel(
				$root,
				"page_subtitle",
				__("Describe what is needed, why it is needed and when it is required.")
			);
			setLabel($root, "submit_label", __("Submit for business review"));
			$root.find('[data-kt-dem-action="save"]').text(__("Save draft"));
			$root.find('[data-kt-dem-action="cancel"]').text(__("Cancel"));
		}
	}

	function applyContext($root, ctx) {
		ctx = ctx || {};
		setField($root, "procuring_entity", ctx.procuring_entity || "");
		setField($root, "owner_org_unit", ctx.owner_org_unit || "");
		setLabel($root, "procuring_entity", ctx.procuring_entity_label || ctx.procuring_entity || "—");
		setLabel($root, "owner_org_unit", ctx.owner_org_unit_label || ctx.owner_org_unit || "—");
		setLabel($root, "currency", ctx.currency || "KES");
		var $contact = $root.find('[data-kt-dem-field="technical_contact"]');
		var contacts = ctx.contacts || [];
		var html =
			'<option disabled value="">' +
			esc(__("Select internal contact")) +
			"</option>";
		contacts.forEach(function (c) {
			html +=
				'<option value="' + esc(c.id) + '">' + esc(c.name || c.id) + "</option>";
		});
		$contact.html(html);
		$contact.find("option").first().prop("selected", true).prop("disabled", true);
	}

	function applyDemand($root, demand) {
		if (!demand) {
			setField($root, "demand_name", "");
			setField($root, "required_by_date", "");
			$root.find("[data-kt-dem-items-tbody]").empty();
			addItemRow($root, {});
			recalcEstimate($root);
			applyMode($root, null);
			toggleRouteJustification($root);
			syncRequiredByDisplay($root, "");
			return;
		}
		setField($root, "demand_name", demand.name || "");
		setField($root, "procuring_entity", demand.procuring_entity || "");
		setField($root, "owner_org_unit", demand.owner_org_unit || "");
		setLabel(
			$root,
			"procuring_entity",
			demand.procuring_entity_label || demand.procuring_entity || "—"
		);
		setLabel(
			$root,
			"owner_org_unit",
			demand.owner_org_unit_label || demand.owner_org_unit || "—"
		);
		setLabel($root, "demand_code", demand.demand_code || "");
		setLabel($root, "currency", demand.currency || "KES");
		[
			"title",
			"need_statement",
			"need_rationale",
			"expected_outcome",
			"beneficiaries",
			"delivery_location",
			"required_by_date",
			"demand_route",
			"route_justification",
			"technical_contact",
			"estimate_confidence",
			"estimate_basis",
		].forEach(function (k) {
			setField($root, k, demand[k] || "");
		});
		$root.find("[data-kt-dem-items-tbody]").empty();
		var items = demand.items || [];
		if (!items.length) {
			addItemRow($root, {});
		} else {
			items.forEach(function (it) {
				addItemRow($root, it);
			});
		}
		recalcEstimate($root);
		applyMode($root, demand);
		toggleRouteJustification($root);
	}

	function bindDemandForm($root, demandId) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var token = Number($root.attr("data-kt-dem-bind-token") || 0) + 1;
		$root.attr("data-kt-dem-bind-token", String(token));
		$root.attr("data-kt-dem-live", "0");
		$root.attr("data-kt-dem-error", "0");

		$root.off(".ktDemForm");
		$root.on("click.ktDemForm", '[data-kt-dem-action="add-item"]', function (e) {
			e.preventDefault();
			addItemRow($root, {});
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="remove-item"]', function (e) {
			e.preventDefault();
			var $rows = $root.find("[data-kt-dem-item-row]");
			if ($rows.length <= 1) {
				$(this).closest("[data-kt-dem-item-row]").find("input, select").val("");
				$(this).closest("[data-kt-dem-item-row]").find('[data-kt-dem-item="quantity"]').val(1);
				recalcEstimate($root);
				return;
			}
			$(this).closest("[data-kt-dem-item-row]").remove();
			recalcEstimate($root);
		});
		$root.on(
			"input.ktDemForm change.ktDemForm",
			'[data-kt-dem-item="requester_estimate"], [data-kt-dem-item="quantity"]',
			function () {
				recalcEstimate($root);
			}
		);
		$root.on("blur.ktDemForm", '[data-kt-dem-item="requester_estimate"]', function () {
			var $inp = $(this);
			var n = parseMoney($inp.val());
			$inp.val(n ? formatMoney(n) : "");
			recalcEstimate($root);
		});
		$root.on("change.ktDemForm", '[data-kt-dem-field="demand_route"]', function () {
			toggleRouteJustification($root);
		});
		$root.on("change.ktDemForm input.ktDemForm", '[data-kt-dem-field="required_by_date"]', function () {
			syncRequiredByDisplay($root, $(this).val());
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="cancel"]', function (e) {
			e.preventDefault();
			frappe.set_route("demands-workspace");
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="save"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			$btn.prop("disabled", true);
			var name = fieldVal($root, "demand_name") || null;
			callMethod(FORM_SAVE, {
				demand: name,
				values: collectValues($root),
				items: collectItems($root),
			})
				.then(function (res) {
					if (!res || !res.ok || !res.demand) {
						throw new Error("Save failed");
					}
					applyDemand($root, res.demand);
					frappe.show_alert({ message: __("Draft saved"), indicator: "green" });
					if (!name && res.demand.name) {
						frappe.set_route("demand-form", res.demand.name);
					}
				})
				.catch(function (err) {
					console.warn("save_demand_form failed", err);
					frappe.show_alert({
						message: __("Could not save demand draft"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="submit"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			$btn.prop("disabled", true);
			var name = fieldVal($root, "demand_name") || null;
			callMethod(FORM_SUBMIT, {
				demand: name,
				values: collectValues($root),
				items: collectItems($root),
			})
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Submit failed");
					}
					frappe.show_alert({
						message: __("Submitted for business review"),
						indicator: "green",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("submit_demand_form failed", err);
					var msg = __("Could not submit demand");
					if (err && err.message) {
						msg = String(err.message).replace(/^.*?:/, "").trim() || msg;
					}
					frappe.show_alert({ message: msg, indicator: "red" });
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});

		return callMethod(FORM_GET, { demand: demandId || null })
			.then(function (payload) {
				if (String($root.attr("data-kt-dem-bind-token")) !== String(token)) {
					return payload;
				}
				if (!payload || !payload.ok) {
					throw new Error("Empty form payload");
				}
				applyContext($root, payload.context || {});
				applyDemand($root, payload.demand || null);
				$root.attr("data-kt-dem-live", "1");
				return payload;
			})
			.catch(function (err) {
				$root.attr("data-kt-dem-live", "0");
				$root.attr("data-kt-dem-error", "1");
				console.warn("Demand form bind failed", err);
				frappe.show_alert({
					message: __("Could not load demand form"),
					indicator: "red",
				});
			});
	}

	kentender_procurement.live.bindDemandForm = bindDemandForm;
})();
