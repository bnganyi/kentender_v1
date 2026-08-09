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
				var cs = data.creation_scope || {};
				var $create = $root.find('[data-testid="kt-dem-ui01-create"]');
				// Keep Create clickable when blocked — form shows the Contract §7.5 banner
				// (a disabled CTA looks like a dead control / "does nothing").
				$create.prop("disabled", false);
				$create.attr(
					"title",
					cs.selection_mode === "blocked"
						? cs.blocked_reason ||
								__("No operational Demand Requester assignment exists.")
						: ""
				);
				$root.attr("data-kt-dem-creation-mode", cs.selection_mode || "");
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
	var FORM_REMOVE_DOC = "kentender_procurement.demands.api.remove_demand_attachment_form";
	var FORM_CTX = "kentender_procurement.demands.api.get_demand_form_context";
	var FORM_SAVE = "kentender_procurement.demands.api.save_demand_form";
	var FORM_SUBMIT = "kentender_procurement.demands.api.submit_demand_form";
	var FORM_CANCEL = "kentender_procurement.demands.api.cancel_demand_form";

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

	function ensureSelectOption($select, value, label) {
		var v = String(value || "").trim();
		if (!v || !$select || !$select.length) {
			return;
		}
		var exists = false;
		$select.find("option").each(function () {
			if (String($(this).attr("value") || "") === v) {
				exists = true;
				return false;
			}
		});
		if (!exists) {
			$select.append(
				$("<option></option>")
					.attr("value", v)
					.text(label || v)
			);
		}
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
		var uom = (item.uom || "Lot").trim() || "Lot";
		var $uom = $row.find('[data-kt-dem-item="uom"]');
		ensureSelectOption($uom, uom, uom);
		$uom.val(uom);
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

	function applyReturnChrome($root, demand) {
		var returned = !!(demand && demand.status === "Returned");
		var notice = (demand && demand.return_notice) || {};
		var hints = returned ? notice.correction_hints || [] : [];
		var $wrap = $root.find("[data-kt-dem-correction-wrap]");
		var $list = $root.find("[data-kt-dem-correction-list]");
		$list.empty();
		if (hints.length) {
			hints.forEach(function (h) {
				var label = (h && (h.label || h.key)) || "";
				if (!label) {
					return;
				}
				$list.append($("<li></li>").text(label));
			});
			$wrap.removeClass("hidden");
		} else {
			$wrap.addClass("hidden");
		}
		$root.find("[data-kt-dem-highlight]").removeClass("kt-dem-correction-highlight");
		if (returned) {
			hints.forEach(function (h) {
				var key = (h && h.key) || "";
				if (!key) {
					return;
				}
				$root
					.find('[data-kt-dem-highlight="' + key + '"]')
					.addClass("kt-dem-correction-highlight");
			});
		}
		var afDisp =
			(demand && demand.available_funding_display) ||
			notice.available_funding_display ||
			"";
		var $af = $root.find("[data-kt-dem-available-funding]");
		if (returned && afDisp) {
			setLabel($root, "available_funding", afDisp);
			$af.removeClass("hidden");
		} else {
			setLabel($root, "available_funding", "—");
			$af.addClass("hidden");
		}
	}

	function formatRoutePill(route) {
		var r = String(route || "").trim();
		if (!r || r === "—") {
			return "";
		}
		return /route$/i.test(r) ? r : r + " Route";
	}

	function formatPeOuDisplay(peLabel, ouLabel) {
		var pe = String(peLabel || "").trim();
		var ou = String(ouLabel || "").trim();
		if ((!pe || pe === "—") && (!ou || ou === "—")) {
			return "—";
		}
		if (pe && pe !== "—" && ou && ou !== "—") {
			return pe + " · " + ou;
		}
		return pe && pe !== "—" ? pe : ou;
	}

	function paintRecordHeaderFields($root, opts) {
		opts = opts || {};
		setLabel($root, "title", opts.title || "—");
		var code = (opts.demand_code || "").trim();
		var hideCode = !code || code === "—";
		setLabel($root, "demand_code", hideCode ? "" : code);
		$root.find("[data-testid='kt-dem-code']").toggleClass("hidden", hideCode);
		var statusDisp = opts.status_display || "";
		setLabel($root, "status_display", statusDisp || "—");
		$root.find("[data-testid='kt-dem-status-pill']").toggleClass("hidden", !statusDisp);
		var routeDisp = formatRoutePill(opts.demand_route);
		setLabel($root, "demand_route_display", routeDisp || "—");
		$root.find("[data-testid='kt-dem-route-pill']").toggleClass("hidden", !routeDisp);
		$root
			.find("[data-testid='kt-dem-record-meta-top']")
			.toggleClass("hidden", hideCode && !statusDisp && !routeDisp);
		var peOu = formatPeOuDisplay(
			opts.procuring_entity_label,
			opts.owner_org_unit_label
		);
		setLabel($root, "pe_ou_display", peOu || "—");
		$root.find("[data-testid='kt-dem-record-pe']").toggleClass("hidden", !peOu || peOu === "—");
		// Stitch DEM-UI-02 lead under Create demand title only.
		$root
			.find("[data-kt-dem-create-lead]")
			.toggleClass("hidden", !opts.show_create_lead);
	}

	function paintFormRecordChrome($root, demand, stageIndicator) {
		var returned = demand && demand.status === "Returned";
		var editing = !!(demand && demand.name);
		var title = __("Create demand");
		if (returned) {
			title = (demand && demand.title) || __("Demand");
		} else if (editing) {
			title = (demand && demand.title) || __("Edit demand");
		}
		var statusDisp =
			(demand && demand.status_display) ||
			(returned ? __("Returned") : editing ? __("Draft") : "");
		var peLabel =
			(demand && demand.procuring_entity_label) ||
			$root.find('[data-kt-dem-label="procuring_entity"]').first().text() ||
			"";
		var ouLabel =
			(demand && demand.owner_org_unit_label) ||
			$root.find('[data-kt-dem-label="owner_org_unit"]').first().text() ||
			"";
		if (!peLabel || peLabel === "—") {
			peLabel = ($root.attr("data-kt-dem-pe-label") || "").trim() || peLabel;
		}
		if (!ouLabel || ouLabel === "—") {
			ouLabel = ($root.attr("data-kt-dem-ou-label") || "").trim() || ouLabel;
		}
		paintRecordHeaderFields($root, {
			title: title,
			demand_code: (demand && demand.demand_code) || "",
			status_display: statusDisp,
			demand_route: (demand && demand.demand_route) || "",
			procuring_entity_label: peLabel,
			owner_org_unit_label: ouLabel,
			show_create_lead: !editing && !returned,
		});
		var stages =
			stageIndicator ||
			(demand && demand.stage_indicator) ||
			[
				{ key: "Request Preparation", label: "Request preparation", state: "Current" },
				{ key: "Business Review", label: "Business review", state: "Not started" },
				{
					key: "Procurement Enrichment",
					label: "Procurement enrichment",
					state: "Not started",
				},
				{ key: "Budget Confirmation", label: "Budget confirmation", state: "Not started" },
				{ key: "Final Approval", label: "Final approval", state: "Not started" },
			];
		paintStageIndicator($root, stages);
	}

	function applyMode($root, demand, stageIndicator) {
		var returned = demand && demand.status === "Returned";
		var editing = !!(demand && demand.name);
		$root.toggleClass("kt-dem-form-returned", returned);
		$root.find("[data-kt-dem-returned-only]").toggleClass("hidden", !returned);
		$root.find("[data-kt-dem-edit-only]").toggleClass("hidden", !editing);
		$root.find("[data-kt-dem-cancel-create]").toggleClass("hidden", !!returned);
		paintFormRecordChrome($root, demand, stageIndicator);
		if (returned) {
			setLabel($root, "submit_label", __("Resubmit"));
			$root.find('[data-kt-dem-action="save"]').text(__("Save changes"));
			var notice = demand.return_notice || {};
			setLabel($root, "returned_by", notice.returned_by || "—");
			setLabel($root, "returned_at", notice.returned_at_display || "—");
			setLabel($root, "return_reason", notice.reason || "—");
			applyReturnChrome($root, demand);
		} else if (editing) {
			setLabel($root, "submit_label", __("Submit for business review"));
			$root.find('[data-kt-dem-action="save"]').text(__("Save draft"));
			$root.find('[data-kt-dem-action="cancel"]').text(__("Cancel"));
			applyReturnChrome($root, null);
		} else {
			setLabel($root, "submit_label", __("Submit for business review"));
			$root.find('[data-kt-dem-action="save"]').text(__("Save draft"));
			$root.find('[data-kt-dem-action="cancel"]').text(__("Cancel"));
			applyReturnChrome($root, null);
		}
	}

	function syncCreateActionsEnabled($root) {
		var mode = $root.attr("data-kt-dem-selection-mode") || "single_readonly";
		var editing = !!(fieldVal($root, "demand_name") || "").trim();
		var blocked = mode === "blocked" && !editing;
		var multiNeedsPair =
			mode === "multi_required" &&
			!editing &&
			(!(fieldVal($root, "procuring_entity") || "").trim() ||
				!(fieldVal($root, "owner_org_unit") || "").trim());
		var disable = blocked || multiNeedsPair || $root.attr("data-kt-dem-can-edit") === "0";
		$root.find('[data-kt-dem-action="save"], [data-kt-dem-action="submit"]').prop(
			"disabled",
			!!disable
		);
		$root.find("[data-testid='kt-dem-ui02-form-canvas']").toggleClass(
			"kt-dem-form-scope-blocked",
			blocked
		);
	}

	function applyCreationScope($root, ctx, demand) {
		ctx = ctx || {};
		var editing = !!(demand && demand.name);
		var mode = editing ? "single_readonly" : ctx.selection_mode || "single_readonly";
		$root.attr("data-kt-dem-selection-mode", mode);
		$root.attr("data-kt-dem-can-edit", ctx.can_edit === false ? "0" : "1");
		var $ctx = $root.find("[data-testid='kt-dem-ui02-context']");
		$ctx.attr("data-kt-dem-scope-mode", mode);
		var $ro = $root.find("[data-kt-dem-scope-ro]");
		var $multi = $root.find("[data-kt-dem-scope-multi]");
		var $blocked = $root.find("[data-kt-dem-scope-blocked]");
		// PE · OU lives under the shared record title — keep RO context hidden.
		$ro.addClass("hidden");
		$multi.toggleClass("hidden", mode !== "multi_required");
		$blocked.toggleClass("hidden", mode !== "blocked");
		$root
			.find("[data-testid='kt-dem-ui02-context']")
			.toggleClass("hidden", mode !== "multi_required" && mode !== "blocked");
		if (mode === "blocked") {
			setLabel(
				$root,
				"blocked_reason",
				ctx.blocked_reason ||
					__("No operational Demand Requester assignment exists.")
			);
			setField($root, "procuring_entity", "");
			setField($root, "owner_org_unit", "");
		}
		if (mode === "multi_required") {
			var pairs = ctx.pairs || [];
			var $sel = $root.find("[data-kt-dem-scope-pair]");
			var html =
				'<option value="" disabled selected>' +
				esc(__("Select owning entity and unit")) +
				"</option>";
			pairs.forEach(function (p) {
				var pe = (p.procuring_entity && p.procuring_entity.id) || "";
				var ou = (p.owner_org_unit && p.owner_org_unit.id) || "";
				var peName =
					(p.procuring_entity && p.procuring_entity.name) || pe;
				var ouName = (p.owner_org_unit && p.owner_org_unit.name) || ou;
				var val = pe + "|" + ou;
				html +=
					'<option value="' +
					esc(val) +
					'">' +
					esc(peName + " · " + ouName) +
					"</option>";
			});
			$sel.html(html);
			// No silent default — leave placeholder selected.
			setField($root, "procuring_entity", "");
			setField($root, "owner_org_unit", "");
		}
		syncCreateActionsEnabled($root);
	}

	function applyContext($root, ctx, demand) {
		ctx = ctx || {};
		applyCreationScope($root, ctx, demand);
		var peLabel = "—";
		var ouLabel = "—";
		if ((ctx.selection_mode || "single_readonly") !== "multi_required" || (demand && demand.name)) {
			setField($root, "procuring_entity", ctx.procuring_entity || (demand && demand.procuring_entity) || "");
			setField($root, "owner_org_unit", ctx.owner_org_unit || (demand && demand.owner_org_unit) || "");
			peLabel =
				ctx.procuring_entity_label ||
				(demand && demand.procuring_entity_label) ||
				ctx.procuring_entity ||
				"—";
			ouLabel =
				ctx.owner_org_unit_label ||
				(demand && demand.owner_org_unit_label) ||
				ctx.owner_org_unit ||
				"—";
			setLabel($root, "procuring_entity", peLabel);
			setLabel($root, "owner_org_unit", ouLabel);
			$root.attr("data-kt-dem-pe-label", peLabel === "—" ? "" : peLabel);
			$root.attr("data-kt-dem-ou-label", ouLabel === "—" ? "" : ouLabel);
		} else {
			setLabel($root, "procuring_entity", "—");
			setLabel($root, "owner_org_unit", "—");
			$root.attr("data-kt-dem-pe-label", "");
			$root.attr("data-kt-dem-ou-label", "");
		}
		setLabel($root, "pe_ou_display", formatPeOuDisplay(peLabel, ouLabel));
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
		syncCreateActionsEnabled($root);
	}

	function paintAttachments($root, attachments) {
		var $list = $root.find("[data-kt-dem-docs-list]");
		if (!$list.length) {
			return;
		}
		$list.empty();
		var rows = attachments || [];
		if (!rows.length) {
			$list.addClass("hidden");
			return;
		}
		$list.removeClass("hidden");
		rows.forEach(function (a) {
			var $li = $('<li class="kt-dem-ui02-doc-chip flex items-center justify-between gap-2 border border-outline-variant rounded-lg px-3 py-2 bg-surface"/>');
			$li.attr("data-testid", "kt-dem-ui02-doc-chip");
			$li.attr("data-file-id", a.id || "");
			$li.append(
				$('<span class="font-body-md text-on-surface truncate"/>').text(a.file_name || "—")
			);
			$li.append(
				$('<button type="button" class="text-error font-label-caps text-label-caps shrink-0"/>')
					.attr("data-kt-dem-action", "remove-doc")
					.attr("data-file-id", a.id || "")
					.attr("data-testid", "kt-dem-ui02-doc-remove")
					.text(__("Remove"))
			);
			$list.append($li);
		});
	}

	function uploadDemandDoc($root, file) {
		if (!file) {
			return Promise.resolve(null);
		}
		var maxBytes = 10 * 1024 * 1024;
		if (file.size > maxBytes) {
			frappe.show_alert({
				message: __("File must be 10MB or smaller"),
				indicator: "orange",
			});
			return Promise.reject(new Error("file too large"));
		}
		var ensureDemand = Promise.resolve(fieldVal($root, "demand_name") || "");
		if (!fieldVal($root, "demand_name")) {
			ensureDemand = callMethod(FORM_SAVE, {
				demand: null,
				values: collectValues($root),
				items: collectItems($root),
			}).then(function (res) {
				if (!res || !res.ok || !res.demand || !res.demand.name) {
					throw new Error("Save failed before upload");
				}
				applyDemand($root, res.demand);
				frappe.set_route("demand-form", res.demand.name);
				return res.demand.name;
			});
		}
		return ensureDemand.then(function (demandName) {
			if (!demandName) {
				throw new Error("Demand name missing");
			}
			return new Promise(function (resolve, reject) {
				var fd = new FormData();
				fd.append("file", file, file.name);
				fd.append("is_private", "1");
				fd.append("folder", "Home/Attachments");
				fd.append("doctype", "Demand");
				fd.append("docname", demandName);
				var xhr = new XMLHttpRequest();
				xhr.open("POST", "/api/method/upload_file", true);
				xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token || "");
				xhr.setRequestHeader("Accept", "application/json");
				xhr.onload = function () {
					var body = null;
					try {
						body = JSON.parse(xhr.responseText || "{}");
					} catch (err) {
						reject(err);
						return;
					}
					if (xhr.status >= 400 || (body && body.exc)) {
						reject(body || new Error("Upload failed"));
						return;
					}
					resolve((body && body.message) || body || {});
				};
				xhr.onerror = function () {
					reject(new Error("Upload network error"));
				};
				xhr.send(fd);
			}).then(function () {
				return callMethod(FORM_GET, { demand: demandName }).then(function (payload) {
					if (payload && payload.ok && payload.demand) {
						applyDemand($root, payload.demand, payload.stage_indicator || null);
					}
					return payload;
				});
			});
		});
	}

	function applyDemand($root, demand, stageIndicator) {
		if (!demand) {
			setField($root, "demand_name", "");
			setField($root, "required_by_date", "");
			$root.find("[data-kt-dem-items-tbody]").empty();
			addItemRow($root, {});
			recalcEstimate($root);
			applyMode($root, null, stageIndicator);
			toggleRouteJustification($root);
			syncRequiredByDisplay($root, "");
			paintAttachments($root, []);
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
		applyMode($root, demand, stageIndicator);
		toggleRouteJustification($root);
		paintAttachments($root, demand.attachments || []);
	}

	function clearCancelDemandModalError($root) {
		$root.find("[data-kt-dem-cancel-error]").addClass("hidden").text("");
		$root.find("[data-kt-dem-cancel-comment]").removeClass("is-invalid");
	}

	function showCancelDemandModalError($root, message) {
		$root
			.find("[data-kt-dem-cancel-error]")
			.text(message || __("Reason is required"))
			.removeClass("hidden");
		$root.find("[data-kt-dem-cancel-comment]").addClass("is-invalid").trigger("focus");
	}

	function closeCancelDemandModal($root) {
		$root
			.find("[data-kt-dem-cancel-modal]")
			.addClass("hidden")
			.attr("hidden", "hidden");
		clearCancelDemandModalError($root);
	}

	function openCancelDemandModal($root) {
		clearCancelDemandModalError($root);
		$root.find("[data-kt-dem-cancel-comment]").val("");
		$root.find("[data-kt-dem-cancel-confirm]").prop("disabled", false);
		$root.find("[data-kt-dem-cancel-modal]").removeClass("hidden").removeAttr("hidden");
		setTimeout(function () {
			$root.find("[data-kt-dem-cancel-comment]").trigger("focus");
		}, 0);
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
		$root.on("change.ktDemForm", "[data-kt-dem-scope-pair]", function () {
			var raw = ($(this).val() || "").trim();
			var parts = raw.split("|");
			var pe = parts[0] || "";
			var ou = parts[1] || "";
			setField($root, "procuring_entity", pe);
			setField($root, "owner_org_unit", ou);
			syncCreateActionsEnabled($root);
			if (pe && ou) {
				callMethod(FORM_CTX, { procuring_entity: pe, owner_org_unit: ou }).then(
					function (ctx) {
						if (!ctx || !ctx.ok) {
							return;
						}
						var $contact = $root.find('[data-kt-dem-field="technical_contact"]');
						var contacts = ctx.contacts || [];
						var html =
							'<option disabled value="">' +
							esc(__("Select internal contact")) +
							"</option>";
						contacts.forEach(function (c) {
							html +=
								'<option value="' +
								esc(c.id) +
								'">' +
								esc(c.name || c.id) +
								"</option>";
						});
						$contact.html(html);
						$contact.find("option").first().prop("selected", true).prop("disabled", true);
					}
				);
			}
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="cancel"]', function (e) {
			e.preventDefault();
			frappe.set_route("demands-workspace");
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="cancel-demand"]', function (e) {
			e.preventDefault();
			var name = fieldVal($root, "demand_name") || "";
			if (!name) {
				return;
			}
			openCancelDemandModal($root);
		});
		$root.on(
			"click.ktDemForm",
			"[data-kt-dem-cancel-close], [data-kt-dem-cancel-dismiss]",
			function (e) {
				e.preventDefault();
				closeCancelDemandModal($root);
			}
		);
		$root.on("click.ktDemForm", "[data-kt-dem-cancel-modal]", function (e) {
			if (e.target === this) {
				closeCancelDemandModal($root);
			}
		});
		$root.on("click.ktDemForm", "[data-kt-dem-cancel-confirm]", function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			var name = fieldVal($root, "demand_name") || "";
			var reason = String($root.find("[data-kt-dem-cancel-comment]").val() || "").trim();
			if (!reason) {
				showCancelDemandModalError($root, __("Reason is required"));
				return;
			}
			clearCancelDemandModalError($root);
			$btn.prop("disabled", true);
			callMethod(FORM_CANCEL, {
				demand: name,
				reason: reason,
			})
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Cancel failed");
					}
					closeCancelDemandModal($root);
					frappe.show_alert({
						message: __("Demand cancelled"),
						indicator: "orange",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("cancel_demand_form failed", err);
					frappe.show_alert({
						message: __("Could not cancel demand"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="pick-docs"]', function (e) {
			if ($(e.target).is("input[type=file]")) {
				return;
			}
			e.preventDefault();
			var $file = $root.find("[data-kt-dem-docs-file]");
			if ($file.length) {
				$file.trigger("click");
			}
		});
		$root.on("keydown.ktDemForm", '[data-kt-dem-action="pick-docs"]', function (e) {
			if (e.key !== "Enter" && e.key !== " ") {
				return;
			}
			e.preventDefault();
			$root.find("[data-kt-dem-docs-file]").trigger("click");
		});
		$root.on("change.ktDemForm", "[data-kt-dem-docs-file]", function () {
			var file = this.files && this.files[0];
			this.value = "";
			if (!file) {
				return;
			}
			uploadDemandDoc($root, file)
				.then(function () {
					frappe.show_alert({
						message: __("Document attached"),
						indicator: "green",
					});
				})
				.catch(function (err) {
					console.warn("Demand document upload failed", err);
					frappe.show_alert({
						message: __("Could not upload supporting document"),
						indicator: "red",
					});
				});
		});
		$root.on("dragover.ktDemForm drop.ktDemForm", '[data-testid="kt-dem-ui02-docs-dropzone"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			if (e.type !== "drop") {
				return;
			}
			var dt = e.originalEvent && e.originalEvent.dataTransfer;
			var file = dt && dt.files && dt.files[0];
			if (!file) {
				return;
			}
			uploadDemandDoc($root, file).catch(function (err) {
				console.warn("Demand document drop upload failed", err);
				frappe.show_alert({
					message: __("Could not upload supporting document"),
					indicator: "red",
				});
			});
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="remove-doc"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			var fileId = $(this).attr("data-file-id") || "";
			var demand = fieldVal($root, "demand_name") || "";
			if (!fileId || !demand) {
				return;
			}
			callMethod(FORM_REMOVE_DOC, { demand: demand, file_id: fileId })
				.then(function (res) {
					if (!res || !res.ok || !res.demand) {
						throw new Error("Remove failed");
					}
					applyDemand($root, res.demand);
				})
				.catch(function (err) {
					console.warn("remove_demand_attachment_form failed", err);
					frappe.show_alert({
						message: __("Could not remove attachment"),
						indicator: "red",
					});
				});
		});
		$root.on("click.ktDemForm", '[data-kt-dem-action="save"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
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
			if ($btn.prop("disabled")) {
				return;
			}
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
				// Budget/Final returns are specialist stages — demand-form cannot save them.
				var dem = payload.demand || null;
				if (
					dem &&
					dem.status === "Returned" &&
					dem.current_stage &&
					dem.current_stage !== "Request Preparation"
				) {
					frappe.show_alert({
						message: __(
							"This Demand was returned for specialist review. Opening the review workspace."
						),
						indicator: "blue",
					});
					frappe.set_route("demand-review", dem.name);
					return payload;
				}
				applyContext($root, payload.context || {}, dem);
				applyDemand(
					$root,
					dem,
					payload.stage_indicator ||
						(payload.context && payload.context.stage_indicator) ||
						null
				);
				syncCreateActionsEnabled($root);
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

	/* ---------- DEM-UIC-002 / DEM-UI-04 demand review ---------- */

	var REVIEW_GET = "kentender_procurement.demands.api.get_demand_review";
	var REVIEW_DECIDE = "kentender_procurement.demands.api.record_business_decision_form";
	var ENRICH_SAVE = "kentender_procurement.demands.api.enrich_demand_form";
	var ENRICH_SUGGEST = "kentender_procurement.demands.api.suggest_strategy_context_form";
	var PROC_DECIDE = "kentender_procurement.demands.api.record_procurement_decision_form";
	var BUDGET_CONFIRM = "kentender_procurement.demands.api.confirm_demand_funding_form";
	var BUDGET_RETURN = "kentender_procurement.demands.api.return_budget_confirmation_form";
	var BUDGET_EXC_RESOLVE = "kentender_procurement.demands.api.resolve_funding_exception_form";
	var BUDGET_EXC_SAVE_NOTE = "kentender_procurement.demands.api.save_funding_exception_note_form";
	var BUDGET_ADJUST = "kentender_procurement.demands.api.adjust_funding_allocation_form";
	var FINAL_APPROVE = "kentender_procurement.demands.api.approve_and_reserve_form";
	var FINAL_DECIDE = "kentender_procurement.demands.api.record_final_decision_form";
	var CORRECTION_HINT_OPTIONS = [
		{ key: "items", label: __("Need items and participant quantities") },
		{ key: "expected_outcome", label: __("Expected outcome for the revised scope") },
		{ key: "requester_estimate", label: __("Requester estimate") },
	];

	function parseMoneyInput(raw) {
		var s = String(raw == null ? "" : raw).replace(/,/g, "").trim();
		if (!s) {
			return 0;
		}
		var n = Number(s);
		return isNaN(n) ? 0 : n;
	}

	function formatMoneyInput(n) {
		var v = Number(n) || 0;
		if (!v) {
			return "";
		}
		return v.toLocaleString("en-US", { maximumFractionDigits: 2 });
	}

	function fillSelect($el, options, selected) {
		$el.empty();
		$el.append($("<option></option>").val("").text("—"));
		(options || []).forEach(function (opt) {
			var val = typeof opt === "string" ? opt : opt.value;
			var label = typeof opt === "string" ? opt : opt.label || opt.value;
			$el.append($("<option></option>").val(val).text(label));
		});
		if (selected) {
			$el.val(selected);
		}
	}

	function showStageHosts($root, stage) {
		var isEnrich = stage === "Procurement Enrichment";
		var isBudget = stage === "Budget Confirmation";
		var isFinal = stage === "Final Approval";
		var $biz = $root.find("[data-kt-dem-business-host]");
		var $enr = $root.find("[data-kt-dem-enrichment-host]");
		var $foot = $root.find("[data-kt-dem-enrichment-footer]");
		var $bud = $root.find("[data-kt-dem-budget-host]");
		var $final = $root.find("[data-kt-dem-final-host]");
		var $viewDetails = $root.find('[data-kt-dem-action="open-details-drawer"]');
		$root.removeClass(
			"kt-dem-enrichment-active kt-dem-budget-active kt-dem-final-active"
		);
		document.body.classList.remove(
			"kt-dem-enrichment-active",
			"kt-dem-budget-active",
			"kt-dem-final-active"
		);
		$enr.addClass("hidden").attr("hidden", "hidden");
		$foot.addClass("hidden").attr("hidden", "hidden");
		$bud.addClass("hidden").attr("hidden", "hidden");
		$final.addClass("hidden").attr("hidden", "hidden");
		if (isEnrich) {
			$biz.addClass("hidden").attr("hidden", "hidden");
			$enr.removeClass("hidden").removeAttr("hidden");
			$foot.removeClass("hidden").removeAttr("hidden");
			$root.addClass("kt-dem-enrichment-active");
			document.body.classList.add("kt-dem-enrichment-active");
			$viewDetails.addClass("hidden").attr("hidden", "hidden");
		} else if (isBudget) {
			$biz.addClass("hidden").attr("hidden", "hidden");
			$bud.removeClass("hidden").removeAttr("hidden");
			$root.addClass("kt-dem-budget-active");
			document.body.classList.add("kt-dem-budget-active");
			$viewDetails.removeClass("hidden").removeAttr("hidden");
		} else if (isFinal) {
			$biz.addClass("hidden").attr("hidden", "hidden");
			$final.removeClass("hidden").removeAttr("hidden");
			$root.addClass("kt-dem-final-active");
			document.body.classList.add("kt-dem-final-active");
			$viewDetails.removeClass("hidden").removeAttr("hidden");
		} else {
			$biz.removeClass("hidden").removeAttr("hidden");
			$viewDetails.addClass("hidden").attr("hidden", "hidden");
		}
	}

	function syncFinalApproveEnabled($root) {
		var can = $root.attr("data-kt-dem-can-final-approve") === "1";
		var ready = $root.attr("data-kt-dem-fa-approve-ready") === "1";
		var checked = !!$root.find('[data-kt-dem-field="fa_approve_checkbox"]').prop("checked");
		var enabled = can && ready && checked;
		var $btn = $root.find('[data-kt-dem-action="final-approve"]');
		$btn.prop("disabled", !enabled);
	}

	function paintFinalApproval($root, fa, canApprove) {
		fa = fa || {};
		var readiness = fa.readiness || {};
		var summary = fa.demand_summary || {};
		var strategy = fa.strategy || {};
		var funding = fa.funding || {};
		var handoff = fa.planning_handoff || {};

		setLabel(
			$root,
			"fa_ready_business",
			(readiness.business_review && readiness.business_review.detail) || "—"
		);
		setLabel(
			$root,
			"fa_ready_enrichment",
			(readiness.procurement_enrichment && readiness.procurement_enrichment.detail) ||
				"—"
		);
		setLabel(
			$root,
			"fa_ready_budget",
			(readiness.budget_confirmation && readiness.budget_confirmation.detail) || "—"
		);
		setLabel(
			$root,
			"fa_blocking_issues",
			readiness.blocking_issues_display || "None"
		);

		setLabel($root, "fa_need", summary.need || "—");
		setLabel(
			$root,
			"fa_owning_unit",
			summary.owning_unit_display || summary.owning_unit || "—"
		);
		setLabel($root, "fa_required_by", summary.required_by_display || "—");
		setLabel($root, "fa_route", summary.demand_route || "Standard");
		setLabel(
			$root,
			"fa_estimate_display",
			summary.confirmed_estimate_display || "—"
		);

		setLabel($root, "fa_primary_target", strategy.primary_target || "—");
		var applicable = Number(strategy.applicable_count) || 0;
		var addressed = Number(strategy.addressed_count) || 0;
		var carried = Number(strategy.carried_count) || 0;
		setLabel($root, "fa_pvc_applicable", String(applicable));
		setLabel($root, "fa_pvc_addressed", addressed + " Addressed");
		setLabel($root, "fa_pvc_carried", carried + " Carried to Planning");
		var aPct = applicable > 0 ? Math.max(0, Math.min(100, (addressed / applicable) * 100)) : 0;
		var cPct = applicable > 0 ? Math.max(0, Math.min(100 - aPct, (carried / applicable) * 100)) : 0;
		$root.find('[data-kt-dem-fa-pvc-bar="addressed"]').css("width", aPct.toFixed(1) + "%");
		$root.find('[data-kt-dem-fa-pvc-bar="carried"]').css("width", cPct.toFixed(1) + "%");

		setLabel(
			$root,
			"fa_budget_line_display",
			(funding && funding.budget_line_display) || "—"
		);
		setLabel(
			$root,
			"fa_alloc_display",
			(funding && funding.confirmed_allocation_display) || "—"
		);
		setLabel($root, "fa_bo_label", (funding && funding.budget_officer_label) || "—");
		setLabel(
			$root,
			"fa_avail_after_display",
			(funding && funding.available_after_display) || "—"
		);
		setLabel(
			$root,
			"fa_recheck_note",
			(funding && funding.recheck_note) ||
				__("Funds will be rechecked on approval.")
		);

		setLabel(
			$root,
			"fa_planning_status",
			handoff.status_on_approval || "Planning Ready"
		);
		setLabel(
			$root,
			"fa_reservation_note",
			handoff.reservation_note ||
				__("Reservation identity carries forward to Planning and Tendering")
		);
		setLabel(
			$root,
			"fa_method_note",
			handoff.method_note || __("Procurement method: Determined in Planning")
		);
		setLabel(
			$root,
			"fa_approve_checkbox_text",
			fa.approve_checkbox_text ||
				__(
					"I approve this Demand for Procurement Planning and authorise the system to reserve funding against the confirmed Budget allocation"
				)
		);

		$root.attr("data-kt-dem-fa-approve-ready", fa.approve_ready ? "1" : "0");
		var $role = $root.find("[data-kt-dem-final-role-banner]");
		if (canApprove) {
			$role.addClass("hidden").attr("hidden", "hidden");
		} else {
			$role.removeClass("hidden").removeAttr("hidden");
		}
		$root
			.find(
				'[data-kt-dem-action="final-return"], [data-kt-dem-action="final-reject"]'
			)
			.prop("disabled", !canApprove);
		$root
			.find('[data-kt-dem-field="fa_approve_checkbox"]')
			.prop("disabled", !canApprove || !fa.approve_ready);
		if (!canApprove || !fa.approve_ready) {
			$root.find('[data-kt-dem-field="fa_approve_checkbox"]').prop("checked", false);
		}
		syncFinalApproveEnabled($root);
	}

	function closeDetailsDrawer($root) {
		$root
			.find("[data-kt-dem-details-drawer]")
			.addClass("hidden")
			.attr("hidden", "hidden");
	}

	function openDetailsDrawer($root) {
		$root
			.find("[data-kt-dem-details-drawer]")
			.removeClass("hidden")
			.removeAttr("hidden");
	}

	function paintDetailsDrawer($root, demand, enrichment) {
		demand = demand || {};
		enrichment = enrichment || {};
		var summary =
			(demand.need_statement || "").trim() ||
			(demand.title || "").trim() ||
			"—";
		setLabel($root, "details_need_summary", summary);
		setLabel($root, "details_beneficiaries", demand.beneficiaries || "—");
		setLabel($root, "details_required_by", demand.required_by_display || "—");
		setLabel(
			$root,
			"details_business_approver",
			(enrichment.business_decision_summary &&
				enrichment.business_decision_summary.actor_label) ||
				"—");
		setLabel($root, "details_delivery_location", demand.delivery_location || "—");
		setLabel(
			$root,
			"details_category",
			demand.procurement_category || "—"
		);
		setLabel($root, "details_demand_route", demand.demand_route || "—");
		setLabel($root, "details_estimate_basis", demand.estimate_basis || "—");
		setLabel(
			$root,
			"details_confirmed_estimate",
			demand.confirmed_estimate_header ||
				demand.estimate_header_display ||
				"—");

		var items = demand.items || [];
		setLabel(
			$root,
			"details_items_count",
			items.length + (items.length === 1 ? " item" : " items")
		);
		var $list = $root.find("[data-kt-dem-details-items]");
		var $itemsEmpty = $root.find("[data-kt-dem-details-items-empty]");
		$list.empty();
		if (!items.length) {
			$itemsEmpty.removeClass("hidden").removeAttr("hidden");
		} else {
			$itemsEmpty.addClass("hidden").attr("hidden", "hidden");
			items.forEach(function (it, idx) {
				var desc = (it.description || "").trim() || "Item " + (idx + 1);
				var qty =
					it.confirmed_quantity != null && it.confirmed_quantity !== ""
						? it.confirmed_quantity
						: it.quantity;
				var uom = (it.confirmed_uom || it.uom || "").trim();
				var qtyDisp =
					qty != null && qty !== ""
						? String(qty) + (uom ? " " + uom : "")
						: uom || "—";
				var est =
					it.confirmed_estimate_display ||
					(it.confirmed_estimate != null && it.confirmed_estimate !== ""
						? formatMoney(it.confirmed_estimate)
						: it.requester_estimate_display ||
							(it.requester_estimate != null
								? formatMoney(it.requester_estimate)
								: "—"));
				$list.append(
					'<li class="kt-dem-details-item">' +
						'<span class="kt-dem-details-item-title">' +
						esc(desc) +
						"</span>" +
						'<span class="kt-dem-details-item-meta">' +
						esc(qtyDisp) +
						" · KES " +
						esc(String(est)) +
						"</span></li>"
				);
			});
		}

		var primary = enrichment.primary_strategy || null;
		var alignment = enrichment.strategy_alignment || (primary ? "Assigned" : "Not assigned");
		setLabel($root, "details_strategy_pill", alignment);
		if (primary) {
			setLabel(
				$root,
				"details_strategy_summary",
				primary.target_name || primary.snapshot_label || "—"
			);
			setLabel(
				$root,
				"details_strategy_path",
				primary.hierarchy_path ||
					primary.plan_display ||
					(primary.target_code ? "(" + primary.target_code + ")" : "")
			);
		} else if (alignment === "No direct alignment") {
			setLabel(
				$root,
				"details_strategy_summary",
				enrichment.strategy_no_alignment_reason ||
					__("No direct Strategy alignment recorded.")
			);
			setLabel($root, "details_strategy_path", "");
		} else {
			setLabel(
				$root,
				"details_strategy_summary",
				__("No Primary Strategy target assigned yet.")
			);
			setLabel($root, "details_strategy_path", "");
		}

		var treatments = enrichment.value_treatments || [];
		var $pvc = $root.find("[data-kt-dem-details-pvc]");
		var $pvcEmpty = $root.find("[data-kt-dem-details-pvc-empty]");
		$pvc.empty();
		if (!treatments.length) {
			$pvcEmpty.removeClass("hidden").removeAttr("hidden");
		} else {
			$pvcEmpty.addClass("hidden").attr("hidden", "hidden");
			treatments.forEach(function (t) {
				$pvc.append(
					'<li class="kt-dem-details-item">' +
						'<span class="kt-dem-details-item-title">' +
						esc(t.commitment_display || t.pvc_snapshot || "—") +
						"</span>" +
						'<span class="kt-dem-details-item-meta">' +
						esc(t.treatment || "—") +
						(t.rationale ? " · " + esc(t.rationale) : "") +
						"</span></li>"
				);
			});
		}
	}

	function syncBudgetConfirmEnabled($root) {
		var canConfirm = $root.attr("data-kt-dem-can-confirm-funding") === "1";
		var ready = $root.attr("data-kt-dem-funding-confirm-ready") === "1";
		var hasExc = $root.attr("data-kt-dem-funding-exception") === "1";
		var checked = !!$root.find('[data-kt-dem-field="funding_confirm_checkbox"]').prop("checked");
		var $btn = $root.find('[data-kt-dem-action="budget-confirm"]');
		var enabled = canConfirm && ready && checked && !hasExc;
		$btn.prop("disabled", !enabled);
		$btn.toggleClass("opacity-50 cursor-not-allowed", !enabled);
		// DEM-UI-07 Confirm is always locked while exception chrome is visible.
		$root.find('[data-kt-dem-action="budget-exc-confirm"]').prop("disabled", true);
	}

	function syncExceptionResolutionUi($root) {
		var canConfirm = $root.attr("data-kt-dem-can-confirm-funding") === "1";
		var hasExc = $root.attr("data-kt-dem-funding-exception") === "1";
		var choice = String(
			$root.find('[data-kt-dem-field="funding_exc_resolution"]:checked').val() || ""
		).trim();
		var note = String($root.find('[data-kt-dem-field="funding_exc_return_note"]').val() || "").trim();
		var $returnBtn = $root.find('[data-kt-dem-action="budget-exc-return"]');
		var returnEnabled = canConfirm && choice === "return" && !!note;
		$returnBtn.prop("disabled", !returnEnabled);
		$root.find('[data-kt-dem-action="budget-exc-save-note"]').prop("disabled", !canConfirm || !note);
		$root.find('[data-kt-dem-action="budget-exc-confirm"]').prop("disabled", true);

		var $adjustPanel = $root.find("[data-kt-dem-funding-adjust-panel]");
		if (hasExc) {
			if (choice === "select_another" && canConfirm) {
				$adjustPanel.removeClass("hidden").removeAttr("hidden");
			} else {
				$adjustPanel.addClass("hidden").attr("hidden", "hidden");
			}
		}
	}

	function paintExceptionChrome($root, funding, canConfirm) {
		var exc = funding.exception || null;
		var rec = funding.recommendation || null;
		var $ui07 = $root.find("[data-kt-dem-ui07-host]");
		var $routine = $root.find("[data-kt-dem-ui06-routine]");
		var $legacyBanner = $root.find("[data-kt-dem-budget-exception]");
		if (!exc) {
			$root.attr("data-kt-dem-funding-exception", "0");
			$ui07.addClass("hidden").attr("hidden", "hidden");
			$routine.removeClass("is-ui07-hidden");
			$legacyBanner.addClass("hidden").attr("hidden", "hidden");
			return;
		}
		$root.attr("data-kt-dem-funding-exception", "1");
		$ui07.removeClass("hidden").removeAttr("hidden");
		$routine.addClass("is-ui07-hidden");
		// Full UI-07 chrome replaces the compact amber banner.
		$legacyBanner.addClass("hidden").attr("hidden", "hidden");

		setLabel(
			$root,
			"funding_exception_title",
			exc.title || exc.type || __("Funding Exception")
		);
		setLabel(
			$root,
			"funding_exception_summary",
			exc.summary ||
				__(
					"Available funding does not cover the confirmed Demand estimate. Funding cannot be confirmed."
				)
		);
		var isMulti = (exc.type || "") === "Multiple Matches";
		$ui07.attr("data-kt-dem-ui07-mode", isMulti ? "multiple_matches" : "insufficient");
		var $tiles = $root.find("[data-testid='kt-dem-ui07-shortfall-tiles']");
		var $targetCard = $root.find("[data-testid='kt-dem-ui07-target-allocation']");
		var $candCard = $root.find("[data-kt-dem-ui07-candidates-card]");
		var $candList = $root.find("[data-kt-dem-ui07-candidates-list]");
		var $help = $root.find(".kt-dem-ui07-resolution-help");

		setLabel($root, "funding_exc_estimate_display", funding.estimate_display || "—");
		setLabel(
			$root,
			"funding_exc_available_display",
			funding.available_funding_display || "—"
		);
		setLabel($root, "funding_exc_shortfall_display", funding.shortfall_display || "—");

		var $excEmpty = $root.find("[data-kt-dem-ui07-rec-empty]");
		var $metaGrid = $root.find(".kt-dem-ui07-meta-grid");
		if (isMulti) {
			$tiles.addClass("hidden").attr("hidden", "hidden");
			$targetCard.addClass("hidden").attr("hidden", "hidden");
			$candCard.removeClass("hidden").removeAttr("hidden");
			$candList.empty();
			(funding.candidates || []).forEach(function (c) {
				var label = c.display || c.name || c.code || "—";
				var avail = c.available_before_display || "";
				var $li = $('<li class="kt-dem-ui07-candidate"/>');
				$li.append($('<span class="kt-dem-ui07-candidate-name"/>').text(label));
				if (c.code && label.indexOf(c.code) < 0) {
					$li.append(
						$('<span class="kt-dem-ui07-candidate-code font-data-mono"/>').text(
							c.code
						)
					);
				}
				if (avail) {
					$li.append(
						$('<span class="kt-dem-ui07-candidate-avail font-data-mono"/>').text(avail)
					);
				}
				$candList.append($li);
			});
			if ($help.length) {
				$help.text(
					__(
						"Select another eligible funding allocation to choose among candidates, or Return to Procurement."
					)
				);
			}
		} else {
			$tiles.removeClass("hidden").removeAttr("hidden");
			$targetCard.removeClass("hidden").removeAttr("hidden");
			$candCard.addClass("hidden").attr("hidden", "hidden");
			$candList.empty();
			if ($help.length) {
				$help.text(__("Select an action to resolve the funding shortfall."));
			}
			if (rec) {
				$metaGrid.removeClass("hidden").removeAttr("hidden");
				$excEmpty.addClass("hidden").attr("hidden", "hidden");
				setLabel($root, "funding_exc_budget_display", rec.budget_display || "—");
				setLabel($root, "funding_exc_line_display", rec.budget_line_display || "—");
				setLabel(
					$root,
					"funding_exc_alloc_status",
					rec.display_status || "Needs attention"
				);
				setLabel($root, "funding_exc_line_status", rec.status || "Active");
				setLabel(
					$root,
					"funding_exc_avail_before_display",
					rec.available_before_full_display ||
						funding.available_funding_display ||
						"—"
				);
				setLabel(
					$root,
					"funding_exc_proposed_display",
					funding.proposed_funded_display ||
						rec.proposed_funded_display ||
						"—"
				);
				setLabel(
					$root,
					"funding_exc_unfunded_display",
					funding.unfunded_amount_display ||
						rec.unfunded_amount_display ||
						"—"
				);
			} else {
				$metaGrid.addClass("hidden").attr("hidden", "hidden");
				$excEmpty.removeClass("hidden").removeAttr("hidden");
				setLabel($root, "funding_exc_alloc_status", "Needs attention");
				setLabel($root, "funding_exc_budget_display", "—");
				setLabel($root, "funding_exc_line_display", "—");
				setLabel($root, "funding_exc_avail_before_display", "—");
				setLabel($root, "funding_exc_proposed_display", "—");
				setLabel(
					$root,
					"funding_exc_unfunded_display",
					funding.unfunded_amount_display || "—"
				);
			}
		}

		var selectEnabled =
			canConfirm &&
			(exc.select_another_enabled ||
				(funding.candidates && funding.candidates.length) ||
				!!rec);
		var $selectLabel = $root.find("[data-kt-dem-ui07-res-select-another]");
		var $selectInput = $selectLabel.find('input[type="radio"]');
		$selectInput.prop("disabled", !selectEnabled);
		$selectLabel.toggleClass("is-disabled", !selectEnabled);

		var $note = $root.find('[data-kt-dem-field="funding_exc_return_note"]');
		if ($note.length && !$note.data("kt-dem-touched")) {
			$note.val(exc.resolution_reason || "");
		}
		$note.prop("disabled", !canConfirm);
		$root
			.find('[data-kt-dem-field="funding_exc_resolution"][value="return"]')
			.prop("disabled", !canConfirm);
		$selectInput.prop("disabled", !selectEnabled);
		syncExceptionResolutionUi($root);
	}

	function paintFunding($root, funding, canConfirm) {
		funding = funding || {};
		var sc = funding.strategy_consistency || {};
		var rec = funding.recommendation || null;
		var exc = funding.exception || null;
		setLabel($root, "funding_estimate_display", funding.estimate_display || "—");
		setLabel($root, "funding_proposed_display", funding.proposed_total_display || "—");
		setLabel($root, "funding_difference_display", funding.difference_display || "—");
		setLabel($root, "funding_condition", funding.condition || "—");
		setLabel($root, "funding_demand_target", sc.demand_target || "—");
		setLabel($root, "funding_budget_line_target", sc.budget_line_target || "—");
		setLabel($root, "funding_strategy_result", sc.result || "—");
		setLabel(
			$root,
			"funding_no_reserve_note",
			funding.no_reserve_disclaimer ||
				__(
					"Confirmation does not reserve funds or approve the Demand. Funding is rechecked and reserved during Final approval."
				)
		);

		var $cond = $root.find("[data-kt-dem-funding-condition]");
		var $condIcon = $root.find("[data-kt-dem-funding-condition-icon]");
		$cond.removeClass("is-sufficient is-attention is-exception");
		if (funding.condition === "Sufficient") {
			$cond.addClass("is-sufficient");
			$condIcon.text("check_circle");
		} else if (funding.condition === "Exception") {
			$cond.addClass("is-exception");
			$condIcon.text("error");
		} else {
			$cond.addClass("is-attention");
			$condIcon.text("warning");
		}

		var $strat = $root.find("[data-kt-dem-funding-strategy-result]");
		var $stratIcon = $root.find("[data-kt-dem-funding-strategy-icon]");
		$strat.removeClass("is-aligned is-attention");
		if (sc.result === "Aligned") {
			$strat.addClass("is-aligned");
			$stratIcon.text("verified_user");
		} else {
			$strat.addClass("is-attention");
			$stratIcon.text("warning");
		}

		var $excBanner = $root.find("[data-kt-dem-budget-exception]");
		var $recBody = $root.find("[data-kt-dem-funding-rec-body]");
		var $recEmpty = $root.find("[data-kt-dem-funding-rec-empty]");
		// Compact banner kept for non-UI07 fallbacks; paintExceptionChrome owns visibility.
		if (exc) {
			setLabel(
				$root,
				"funding_exception_text",
				exc.summary ||
					__(
						"Open funding exception: {0}. Confirm is unavailable — return to Procurement or resolve via exception flow.",
						[exc.type || exc.name || ""]
					)
			);
		} else {
			$excBanner.addClass("hidden").attr("hidden", "hidden");
		}
		paintExceptionChrome($root, funding, canConfirm);

		var $badge = $root.find("[data-kt-dem-funding-alloc-badge]");
		$badge.removeClass("is-active is-attention is-unavailable");
		if (rec) {
			$recBody.removeClass("hidden").removeAttr("hidden");
			$recEmpty.addClass("hidden").attr("hidden", "hidden");
			setLabel($root, "funding_budget_display", rec.budget_display || "—");
			setLabel($root, "funding_ou_display", rec.owning_unit_display || "—");
			setLabel($root, "funding_line_display", rec.budget_line_display || "—");
			setLabel($root, "funding_approved_display", rec.approved_amount_display || "—");
			setLabel($root, "funding_avail_before_display", rec.available_before_display || "—");
			setLabel($root, "funding_allocate_display", rec.allocate_display || "—");
			setLabel($root, "funding_avail_after_display", rec.available_after_display || "—");
			// ACTIVE only when recommendation is sufficient and no open exception.
			var statusLabel =
				rec.display_status ||
				(rec.sufficient && !exc ? "Active" : exc || !rec.sufficient ? "Needs attention" : "Pending");
			setLabel($root, "funding_alloc_status", statusLabel);
			if (String(statusLabel).toLowerCase() === "active") {
				$badge.addClass("is-active");
			} else if (String(statusLabel).toLowerCase().indexOf("unavailable") >= 0) {
				$badge.addClass("is-unavailable");
			} else {
				$badge.addClass("is-attention");
			}
			var approved = Number(rec.approved_amount) || 0;
			var committed = Number(rec.amount_committed) || 0;
			var reserved = Number(rec.amount_reserved) || 0;
			var allocate = Number(rec.allocate) || 0;
			var availBefore = Number(rec.available_before);
			if (isNaN(availBefore)) {
				availBefore = Math.max(0, approved - committed - reserved);
			}
			var denom = approved > 0 ? approved : committed + reserved + allocate + Math.max(0, availBefore);
			var pct = function (n) {
				return denom > 0 ? Math.max(0, Math.min(100, (n / denom) * 100)) : 0;
			};
			var cPct = pct(committed);
			var reservedSeg = Math.min(allocate, Math.max(0, availBefore));
			var rPct = pct(reserved + reservedSeg);
			var aPct = Math.max(0, 100 - cPct - rPct);
			$root.find('[data-kt-dem-funding-bar="committed"]').css("width", cPct.toFixed(1) + "%");
			$root.find('[data-kt-dem-funding-bar="reserved"]').css("width", rPct.toFixed(1) + "%");
			$root.find('[data-kt-dem-funding-bar="available"]').css("width", aPct.toFixed(1) + "%");
			var utilized = denom > 0 ? (((committed + reserved + Math.min(allocate, availBefore)) / denom) * 100) : 0;
			setLabel(
				$root,
				"funding_utilized_display",
				utilized.toFixed(1) + "% Utilized"
			);
			var $amt = $root.find('[data-kt-dem-field="funding_adjust_amount"]');
			if ($amt.length && !$amt.data("kt-dem-touched")) {
				$amt.val(formatMoneyInput(allocate || funding.estimate || 0));
			}
			var $line = $root.find('[data-kt-dem-field="funding_adjust_line"]');
			if ($line.length && rec.budget_line && !$line.data("kt-dem-touched")) {
				$line.val(rec.budget_line);
			}
		} else {
			$recBody.addClass("hidden").attr("hidden", "hidden");
			$recEmpty.removeClass("hidden").removeAttr("hidden");
			setLabel($root, "funding_alloc_status", "Unavailable");
			$badge.addClass("is-unavailable");
			$root.find("[data-kt-dem-funding-bar]").css("width", "0%");
		}

		// Populate Adjust recommendation candidate select (separate section).
		var $sel = $root.find('[data-kt-dem-field="funding_adjust_line"]');
		if ($sel.length) {
			var prev = $sel.val();
			var touched = !!$sel.data("kt-dem-touched");
			var opts = ['<option value="">' + __("Select budget line…") + "</option>"];
			(funding.candidates || []).forEach(function (c) {
				var id = c.id || "";
				var label = c.display || c.name || c.code || id;
				opts.push(
					'<option value="' +
						esc(id) +
						'">' +
						esc(label) +
						"</option>"
				);
			});
			$sel.html(opts.join(""));
			if (touched && prev) {
				$sel.val(prev);
			} else if (rec && rec.budget_line) {
				$sel.val(rec.budget_line);
			} else if (prev) {
				$sel.val(prev);
			}
		}

		var $adjustPanel = $root.find("[data-kt-dem-funding-adjust-panel]");
		if (exc) {
			// Visibility driven by Resolution → Select another.
			syncExceptionResolutionUi($root);
		} else if (canConfirm) {
			$adjustPanel.removeClass("hidden").removeAttr("hidden");
		} else {
			$adjustPanel.addClass("hidden").attr("hidden", "hidden");
		}

		$root.attr(
			"data-kt-dem-funding-confirm-ready",
			funding.confirm_ready && !exc ? "1" : "0"
		);
		var $roleBanner = $root.find("[data-kt-dem-budget-role-banner]");
		if (canConfirm) {
			$roleBanner.addClass("hidden").attr("hidden", "hidden");
		} else {
			$roleBanner.removeClass("hidden").removeAttr("hidden");
		}
		$root
			.find(
				'[data-kt-dem-action="budget-return"], [data-kt-dem-action="budget-adjust"], [data-kt-dem-action="budget-apply-adjust"]'
			)
			.prop("disabled", !canConfirm);
		$root
			.find('[data-kt-dem-field="funding_adjust_line"], [data-kt-dem-field="funding_adjust_amount"]')
			.prop("disabled", !canConfirm);
		// Confirm stays gated; Adjust remains available during exceptions.
		$root
			.find('[data-kt-dem-field="funding_confirm_checkbox"]')
			.prop("disabled", !canConfirm || !funding.confirm_ready || !!exc);
		if (!canConfirm || !funding.confirm_ready || exc) {
			$root.find('[data-kt-dem-field="funding_confirm_checkbox"]').prop("checked", false);
		}
		syncBudgetConfirmEnabled($root);
	}

	function enrichItemQty(it) {
		var cq = Number(it && it.confirmed_quantity);
		if (!isNaN(cq) && cq > 0) {
			return cq;
		}
		var q = Number(it && it.quantity);
		return !isNaN(q) && q > 0 ? q : 1;
	}

	function enrichItemTotal(it) {
		var ce = Number(it && it.confirmed_estimate);
		if (!isNaN(ce) && ce > 0) {
			return ce;
		}
		var re = Number(it && it.requester_estimate);
		return !isNaN(re) && re > 0 ? re : 0;
	}

	function enrichItemUnit(it) {
		var unit = Number(it && it.unit_estimate);
		if (!isNaN(unit) && unit > 0) {
			return unit;
		}
		var qty = enrichItemQty(it);
		var total = enrichItemTotal(it);
		return qty > 0 ? total / qty : total;
	}

	function formatEnrichMoneyDisplay(n) {
		var v = Number(n) || 0;
		var body = v
			? v.toLocaleString("en-US", {
					minimumFractionDigits: 0,
					maximumFractionDigits: 2,
			  })
			: "0";
		return "KES " + body;
	}

	function enrichRowHtml(it) {
		it = it || {};
		var qty = enrichItemQty(it);
		var uom = it.confirmed_uom || it.uom || "Lot";
		var unit = enrichItemUnit(it);
		var total = enrichItemTotal(it);
		if (!(total > 0) && unit > 0) {
			total = unit * qty;
		}
		/*
		 * DIA-FR-046: PAA may refine description, qty, unit, and unit estimate.
		 * Total Est. is computed (qty × unit est). Soft Stitch inputs (no spinner boxes).
		 */
		return (
			'<tr class="kt-dem-ui05-item-row border-b border-outline-variant" data-kt-dem-enrich-item-row data-item-name="' +
			esc(it.name || "") +
			'">' +
			'<td class="p-3 kt-dem-ui05-item-desc-cell"><input class="kt-dem-ui05-item-input kt-dem-ui05-item-desc" type="text" data-kt-dem-enrich-item="description" data-testid="kt-dem-ui05-item-desc" value="' +
			esc(it.description || "") +
			'"/></td>' +
			'<td class="p-3 kt-dem-ui05-item-qty-cell"><input class="kt-dem-ui05-item-input kt-dem-ui05-item-qty font-data-mono text-right" type="text" inputmode="decimal" data-kt-dem-enrich-item="confirmed_quantity" data-testid="kt-dem-ui05-item-qty" value="' +
			esc(String(qty)) +
			'"/></td>' +
			'<td class="p-3 kt-dem-ui05-item-uom-cell"><input class="kt-dem-ui05-item-input kt-dem-ui05-item-uom" type="text" data-kt-dem-enrich-item="confirmed_uom" data-testid="kt-dem-ui05-item-uom" value="' +
			esc(uom) +
			'"/></td>' +
			'<td class="p-3 kt-dem-ui05-item-unit-est-cell">' +
			'<div class="kt-dem-ui05-item-unit-est-wrap">' +
			'<span class="kt-dem-ui05-item-money-cur" aria-hidden="true">KES</span>' +
			'<input class="kt-dem-ui05-item-input kt-dem-ui05-item-unit-est font-data-mono text-right" type="text" inputmode="decimal" data-kt-dem-enrich-item="unit_estimate" data-testid="kt-dem-ui05-item-unit-est" value="' +
			esc(formatMoneyInput(unit)) +
			'"/>' +
			"</div></td>" +
			'<td class="p-3 font-data-mono text-on-surface font-semibold text-right whitespace-nowrap" data-kt-dem-enrich-item-total data-testid="kt-dem-ui05-item-total-est">' +
			esc(formatEnrichMoneyDisplay(total)) +
			"</td>" +
			'<td class="p-3 text-right"><button type="button" class="kt-dem-ui05-item-delete p-2 rounded-full text-on-surface-variant border-0 bg-transparent" data-kt-dem-action="enrich-remove-item" aria-label="Remove item"><span class="material-symbols-outlined text-[20px]">delete</span></button></td>' +
			"</tr>"
		);
	}

	function syncEnrichItemRowTotals($root) {
		var grand = 0;
		$root.find("[data-kt-dem-enrich-item-row]").each(function () {
			var $row = $(this);
			var qty =
				parseMoneyInput($row.find('[data-kt-dem-enrich-item="confirmed_quantity"]').val()) ||
				0;
			var unit = parseMoneyInput(
				$row.find('[data-kt-dem-enrich-item="unit_estimate"]').val()
			);
			var total = qty > 0 ? qty * unit : unit;
			grand += total;
			$row.find("[data-kt-dem-enrich-item-total]").text(formatEnrichMoneyDisplay(total));
		});
		setLabel($root, "enrich_items_total", formatEnrichMoneyDisplay(grand));
		return grand;
	}

	function paintEnrichItems($root, items) {
		var $tbody = $root.find("[data-kt-dem-enrich-items-tbody]");
		$tbody.empty();
		(items || []).forEach(function (it) {
			$tbody.append(enrichRowHtml(it));
		});
		syncEnrichItemRowTotals($root);
	}

	function collectEnrichItems($root) {
		var rows = [];
		$root.find("[data-kt-dem-enrich-item-row]").each(function () {
			var $row = $(this);
			var desc = String($row.find('[data-kt-dem-enrich-item="description"]').val() || "").trim();
			if (!desc) {
				return;
			}
			var qty =
				parseMoneyInput($row.find('[data-kt-dem-enrich-item="confirmed_quantity"]').val()) ||
				1;
			var unit = parseMoneyInput(
				$row.find('[data-kt-dem-enrich-item="unit_estimate"]').val()
			);
			var total = qty > 0 ? qty * unit : unit;
			var uom = String(
				$row.find('[data-kt-dem-enrich-item="confirmed_uom"]').val() || ""
			).trim();
			rows.push({
				name: $row.attr("data-item-name") || "",
				description: desc,
				quantity: qty,
				uom: uom || "Lot",
				confirmed_quantity: qty,
				confirmed_uom: uom || "Lot",
				confirmed_estimate: total,
			});
		});
		return rows;
	}

	function paintStrategyCard($root, enrichment) {
		var primary = (enrichment && enrichment.primary_strategy) || null;
		var alignment =
			(enrichment && enrichment.strategy_alignment) ||
			(primary ? "Assigned" : "Not assigned");
		setLabel($root, "strategy_alignment_pill", alignment);
		var $pill = $root.find('[data-kt-dem-label="strategy_alignment_pill"]');
		$pill.toggleClass(
			"bg-status-available/10 text-status-available",
			alignment === "Assigned" || alignment === "No direct alignment"
		);
		$pill.toggleClass(
			"bg-surface-container-high text-on-surface-variant",
			alignment !== "Assigned" && alignment !== "No direct alignment"
		);
		var $empty = $root.find("[data-kt-dem-strategy-empty]");
		var $assigned = $root.find("[data-kt-dem-strategy-assigned]");
		if (primary) {
			$empty.addClass("hidden").attr("hidden", "hidden");
			$assigned.removeClass("hidden").removeAttr("hidden");
			setLabel($root, "primary_target_name", primary.target_name || "—");
			setLabel(
				$root,
				"primary_target_code",
				primary.target_code ? "(" + primary.target_code + ")" : ""
			);
			// Name (CODE) only — never plan / plan_version_id hashes.
			setLabel(
				$root,
				"primary_plan_label",
				primary.plan_display ||
					(primary.plan_name && primary.plan_code
						? primary.plan_name + " (" + primary.plan_code + ")"
						: primary.plan_name || primary.plan_code || "—")
			);
			setLabel(
				$root,
				"primary_hierarchy_path",
				primary.hierarchy_path || primary.snapshot_label || "—"
			);
		} else {
			$assigned.addClass("hidden").attr("hidden", "hidden");
			$empty.removeClass("hidden").removeAttr("hidden");
			var emptyMsg =
				alignment === "No direct alignment"
					? (enrichment && enrichment.strategy_no_alignment_reason) ||
						__("No direct Strategy alignment recorded.")
					: __("No Primary Strategy target assigned yet.");
			$empty.find("p").first().text(emptyMsg);
		}
	}

	function paintPvc($root, treatments) {
		var rows = treatments || [];
		var $empty = $root.find("[data-kt-dem-pvc-empty]");
		var $table = $root.find("[data-kt-dem-pvc-table]");
		var $tbody = $root.find("[data-kt-dem-pvc-tbody]");
		$tbody.empty();
		if (!rows.length) {
			$empty.removeClass("hidden");
			$table.addClass("hidden").attr("hidden", "hidden");
			return;
		}
		$empty.addClass("hidden");
		$table.removeClass("hidden").removeAttr("hidden");
		rows.forEach(function (t) {
			$tbody.append(
				"<tr class='border-b border-outline-variant'>" +
					'<td class="p-2 font-medium">' +
					esc(t.commitment_display || t.pvc_snapshot || "—") +
					"</td>" +
					'<td class="p-2">' +
					esc(t.treatment || "—") +
					"</td>" +
					'<td class="p-2 text-on-surface-variant">' +
					esc(t.rationale || "") +
					"</td></tr>"
			);
		});
	}

	function closeStrategyDrawer($root) {
		$root
			.find("[data-kt-dem-strategy-drawer]")
			.addClass("hidden")
			.attr("hidden", "hidden");
	}

	function openStrategyDrawer($root, demandId) {
		var $drawer = $root.find("[data-kt-dem-strategy-drawer]");
		$drawer.removeClass("hidden").removeAttr("hidden");
		setField($root, "strategy_search", "");
		setField($root, "strategy_reason", "");
		setField($root, "strategy_plan_filter", "");
		setField($root, "strategy_period_filter", "");
		$root.find("[data-kt-dem-strategy-reason-host]").removeClass("hidden").removeAttr("hidden");
		$root
			.find("[data-kt-dem-strategy-reason-label]")
			.html(
				esc(__("Confirmation reason")) + ' <span class="text-error">*</span>'
			);
		$root
			.find('[data-kt-dem-field="strategy_reason"]')
			.attr("placeholder", __("Why this Primary target fits the Demand"));
		loadStrategySuggestions($root, demandId);
	}

	function strategySuggestQuery($root) {
		return {
			q: fieldVal($root, "strategy_search") || "",
			plan_code: fieldVal($root, "strategy_plan_filter") || "",
			effective_period: fieldVal($root, "strategy_period_filter") || "",
		};
	}

	function paintStrategyFilters($root, filters) {
		var plans = (filters && filters.plans) || [];
		var periods = (filters && filters.effective_periods) || [];
		var $plan = $root.find('[data-kt-dem-field="strategy_plan_filter"]');
		var $period = $root.find('[data-kt-dem-field="strategy_period_filter"]');
		var planVal = $plan.val() || "";
		var periodVal = $period.val() || "";
		$plan.empty().append($("<option></option>").val("").text(__("Strategic plan")));
		plans.forEach(function (p) {
			$plan.append(
				$("<option></option>")
					.val(p.plan_code || p.code || "")
					.text(p.plan_title || p.name || p.plan_code || "")
			);
		});
		$period.empty().append($("<option></option>").val("").text(__("Effective period")));
		periods.forEach(function (per) {
			$period.append($("<option></option>").val(per).text(per));
		});
		if (planVal) {
			$plan.val(planVal);
		}
		if (periodVal) {
			$period.val(periodVal);
		}
	}

	function strategyOptionCardHtml(s, idx) {
		var id = "kt-dem-ui05a-opt-" + idx;
		var payload = encodeURIComponent(JSON.stringify(s));
		var suggested = !!s.is_suggested;
		var borderCls = suggested
			? "kt-dem-strategy-option is-suggested border-2 border-primary"
			: "kt-dem-strategy-option border border-outline-variant";
		var badge = suggested
			? '<span class="kt-dem-strategy-suggested-badge" data-testid="kt-dem-ui05a-suggested-badge-' +
				idx +
				'">' +
				esc(__("Suggested")) +
				"</span>"
			: "";
		var why = s.why_suggested
			? '<div class="kt-dem-strategy-why" data-testid="kt-dem-ui05a-why-' +
				idx +
				'">' +
				esc(s.why_suggested) +
				"</div>"
			: "";
		var titleCls = suggested
			? "font-headline-sm text-on-surface leading-tight mb-0"
			: "font-body-lg font-semibold text-on-surface leading-tight mb-0";
		return (
			'<label class="' +
			borderCls +
			' relative flex flex-col gap-3 p-4 rounded-xl cursor-pointer" for="' +
			id +
			'" data-testid="kt-dem-ui05a-card-' +
			idx +
			'">' +
			'<div class="flex justify-between items-start gap-3">' +
			'<div class="flex-grow pr-2">' +
			badge +
			"<h3 class=\"" +
			titleCls +
			'">' +
			esc(s.display_name || s.target_name || "—") +
			"</h3>" +
			"</div>" +
			'<input id="' +
			id +
			'" class="mt-1" type="radio" name="kt-dem-strategy-target" data-kt-dem-strategy-option="' +
			payload +
			'" data-testid="kt-dem-ui05a-option-' +
			idx +
			'"/>' +
			"</div>" +
			'<div class="text-xs text-on-surface-variant flex flex-col gap-1">' +
			'<p class="mb-0 ' +
			(suggested ? "font-medium" : "") +
			'">' +
			esc(s.hierarchy_path || s.snapshot_label || "") +
			"</p>" +
			why +
			"</div>" +
			'<button type="button" class="kt-dem-strategy-add-supporting hidden mt-1 text-primary text-sm font-medium flex items-center gap-1 border-0 bg-transparent p-0" data-kt-dem-action="add-supporting-target" data-testid="kt-dem-ui05a-add-supporting-' +
			idx +
			'">' +
			'<span class="material-symbols-outlined text-[18px]" aria-hidden="true">add_circle</span>' +
			esc(__("Add supporting target")) +
			"</button>" +
			"</label>"
		);
	}

	function loadStrategySuggestions($root, demandId) {
		var $host = $root.find("[data-kt-dem-strategy-suggestions]");
		var query = strategySuggestQuery($root);
		$host.html(
			'<p class="text-sm text-on-surface-variant p-2">' + esc(__("Loading…")) + "</p>"
		);
		return callMethod(ENRICH_SUGGEST, {
			demand: demandId,
			q: query.q,
			plan_code: query.plan_code,
			effective_period: query.effective_period,
		}).then(function (res) {
			$host.empty();
			paintStrategyFilters($root, (res && res.filters) || {});
			var suggestions = (res && res.suggestions) || [];
			if (!suggestions.length) {
				$host.append(
					'<p class="text-sm text-on-surface-variant p-2">' +
						esc(__("No active Strategy targets found for this entity.")) +
						"</p>"
				);
			} else {
				suggestions.forEach(function (s, idx) {
					$host.append(strategyOptionCardHtml(s, idx));
				});
			}
			$host.append(
				'<label class="kt-dem-strategy-option kt-dem-strategy-none flex items-start gap-3 p-4 rounded-xl border border-outline-variant cursor-pointer" for="kt-dem-ui05a-none" data-testid="kt-dem-ui05a-none">' +
					'<input id="kt-dem-ui05a-none" class="mt-1" type="radio" name="kt-dem-strategy-target" value="__none__" data-kt-dem-strategy-none="1" data-testid="kt-dem-ui05a-option-none"/>' +
					'<div class="flex flex-col gap-2 w-full">' +
					'<span class="font-medium text-on-surface">' +
					esc(__("No direct Strategy alignment")) +
					"</span></div></label>"
			);
			syncStrategyDrawerSelection($root);
			return res;
		});
	}

	function syncStrategyDrawerSelection($root) {
		var $checked = $root.find('input[name="kt-dem-strategy-target"]:checked');
		var isNone = $checked.is("[data-kt-dem-strategy-none]");
		$root.find(".kt-dem-strategy-add-supporting").addClass("hidden");
		if ($checked.length && !isNone) {
			$checked
				.closest("label")
				.find(".kt-dem-strategy-add-supporting")
				.removeClass("hidden");
			$root
				.find("[data-kt-dem-strategy-reason-label]")
				.html(
					esc(__("Confirmation reason")) + ' <span class="text-error">*</span>'
				);
			$root
				.find('[data-kt-dem-field="strategy_reason"]')
				.attr("placeholder", __("Why this Primary target fits the Demand"));
		} else if (isNone) {
			$root
				.find("[data-kt-dem-strategy-reason-label]")
				.html(
					esc(__("Reason for no alignment")) + ' <span class="text-error">*</span>'
				);
			$root
				.find('[data-kt-dem-field="strategy_reason"]')
				.attr("placeholder", __("Provide a reason for no alignment…"));
		}
	}

	function selectedStrategyOption($root) {
		var $checked = $root.find('input[name="kt-dem-strategy-target"]:checked');
		if (!$checked.length) {
			return null;
		}
		if ($checked.is("[data-kt-dem-strategy-none]")) {
			return { none: true };
		}
		try {
			return JSON.parse(decodeURIComponent($checked.attr("data-kt-dem-strategy-option") || ""));
		} catch (e) {
			return null;
		}
	}

	function collectEnrichValues($root) {
		return {
			procurement_category: fieldVal($root, "procurement_category"),
			// Preserve factory/default Standard when the select has not been painted yet.
			demand_route: fieldVal($root, "demand_route") || "Standard",
			estimate_basis: fieldVal($root, "estimate_basis"),
			confirmed_estimate: parseMoneyInput(fieldVal($root, "confirmed_estimate")),
			duplicate_assessment:
				($root.find('[data-kt-dem-label="duplicate_assessment"]').text() || "").trim() ||
				"None found",
			related_demands_note: fieldVal($root, "related_demands_note"),
			aggregation_treatment: fieldVal($root, "aggregation_treatment"),
			aggregation_rationale: fieldVal($root, "aggregation_rationale"),
			strategy_no_alignment_reason: fieldVal($root, "strategy_no_alignment_reason") || "",
		};
	}

	function stageLabelDisplay(key, label) {
		var raw = (label || key || "").trim();
		var map = {
			"Request Preparation": "Request preparation",
			"Business Review": "Business review",
			"Procurement Enrichment": "Procurement enrichment",
			"Budget Confirmation": "Budget confirmation",
			"Final Approval": "Final approval",
		};
		return map[raw] || map[key] || raw;
	}

	function paintStageIndicator($root, stages) {
		var $list = $root.find("[data-kt-dem-stage-list]");
		$list.empty();
		(stages || []).forEach(function (s, idx) {
			var state = s.state || "Not started";
			var key = s.key || s.label || "";
			var icon =
				state === "Complete"
					? "check"
					: state === "Current"
						? key === "Procurement Enrichment"
							? "edit_note"
							: "visibility"
						: String(idx + 1);
			var $item = $(
				'<div data-kt-dem-stage-item data-state="' +
					esc(state) +
					'">' +
					'<div data-kt-dem-stage-dot>' +
					(state === "Not started"
						? esc(String(idx + 1))
						: '<span class="material-symbols-outlined text-[18px]">' +
							esc(icon) +
							"</span>") +
					"</div>" +
					'<div class="flex flex-col">' +
					'<span data-kt-dem-stage-label>' +
					esc(stageLabelDisplay(key, s.label)) +
					"</span>" +
					'<span class="text-xs font-medium">' +
					esc(state === "Not started" ? "Not started" : state) +
					"</span>" +
					"</div></div>"
			);
			$list.append($item);
		});
	}

	function paintReviewItems($root, items) {
		var $tbody = $root.find("[data-kt-dem-items-tbody]");
		$tbody.empty();
		var rows = items || [];
		setLabel($root, "items_count", String(rows.length) + (rows.length === 1 ? " Item" : " Items"));
		if (!rows.length) {
			$tbody.append(
				'<tr><td class="px-4 py-4 text-on-surface-variant" colspan="3">' +
					esc(__("No need items")) +
					"</td></tr>"
			);
			return;
		}
		rows.forEach(function (it) {
			$tbody.append(
				"<tr class='border-b border-outline-variant'>" +
					'<td class="px-4 py-3"><div class="font-medium text-on-surface">' +
					esc(it.description || "") +
					"</div></td>" +
					'<td class="px-4 py-3 font-data-mono text-right text-on-surface">' +
					esc(it.quantity_display || "") +
					"</td>" +
					'<td class="px-4 py-3 font-data-mono text-right text-on-surface">' +
					esc(it.requester_estimate_display || "") +
					"</td></tr>"
			);
		});
	}

	function paintReviewPrompts($root, prompts) {
		var $host = $root.find("[data-kt-dem-review-prompts]");
		$host.empty();
		// Stitch DEM-UI-04: acknowledgement checkboxes (not scored questions).
		(prompts || []).forEach(function (p, idx) {
			var id = "kt-dem-ui04-criterion-" + idx;
			var $label = $(
				'<label class="kt-dem-ui04-criterion flex items-start gap-3 cursor-pointer group" for="' +
					id +
					'">' +
					'<span class="kt-dem-ui04-criterion-box relative flex items-center justify-center mt-0.5 shrink-0">' +
					'<input id="' +
					id +
					'" class="kt-dem-ui04-criterion-input peer" type="checkbox" data-kt-dem-review-criterion="' +
					idx +
					'" data-testid="kt-dem-ui04-criterion-' +
					idx +
					'"/>' +
					'<span class="material-symbols-outlined kt-dem-ui04-criterion-check" aria-hidden="true">check</span>' +
					"</span>" +
					'<span class="text-sm text-on-surface">' +
					esc(p) +
					"</span></label>"
			);
			$host.append($label);
		});
	}

	function applyReviewPayload($root, payload) {
		var demand = (payload && payload.demand) || {};
		var stage = payload.stage || "";
		var enrichment = (payload && payload.enrichment) || null;
		var funding = (payload && payload.funding) || null;
		$root.attr("data-kt-dem-review-stage", stage);
		$root.attr("data-kt-dem-can-decide", payload.can_decide ? "1" : "0");
		$root.attr("data-kt-dem-can-enrich", payload.can_enrich ? "1" : "0");
		$root.attr(
			"data-kt-dem-can-confirm-funding",
			payload.can_confirm_funding ? "1" : "0"
		);
		$root.attr(
			"data-kt-dem-can-final-approve",
			payload.can_final_approve ? "1" : "0"
		);
		showStageHosts($root, stage);
		paintRecordHeaderFields($root, {
			title: demand.title || "—",
			demand_code: demand.demand_code || "—",
			status_display: demand.status_display || "",
			demand_route: demand.demand_route || "",
			procuring_entity_label:
				demand.procuring_entity_label || demand.procuring_entity || "",
			owner_org_unit_label:
				demand.owner_org_unit_label || demand.owner_org_unit || "",
		});
		[
			"need_statement",
			"need_rationale",
			"expected_outcome",
			"beneficiaries",
			"owner_org_unit_label",
			"delivery_location",
			"technical_contact_label",
			"estimate_basis",
			"required_by_display",
			"estimate_header_display",
			"currency",
		].forEach(function (k) {
			setLabel($root, k, demand[k] || "—");
		});
		var baSummary = (enrichment && enrichment.business_decision_summary) || null;
		setLabel(
			$root,
			"business_approver_label",
			(baSummary && baSummary.actor_label) || "—"
		);
		setLabel(
			$root,
			"non_final_disclaimer",
			payload.non_final_disclaimer ||
				__(
					"Business support does not confirm funding or constitute final procurement approval."
				)
		);
		paintStageIndicator($root, payload.stage_indicator || []);
		paintReviewItems($root, demand.items || []);
		paintReviewPrompts($root, payload.review_prompts || []);
		paintDetailsDrawer($root, demand, enrichment || {});
		var can = !!payload.can_decide;
		$root
			.find(
				'[data-kt-dem-action="support"], [data-kt-dem-action="return"], [data-kt-dem-action="reject"]'
			)
			.prop("disabled", !can);
		$root.find("[data-kt-dem-business-decision]").toggleClass("kt-dem-review-readonly", !can);

		if (stage === "Procurement Enrichment" && enrichment) {
			var canEnrich = !!payload.can_enrich;
			var $roleBanner = $root.find("[data-kt-dem-enrich-role-banner]");
			if (canEnrich) {
				$roleBanner.addClass("hidden").attr("hidden", "hidden");
			} else {
				$roleBanner.removeClass("hidden").removeAttr("hidden");
			}
			fillSelect(
				$root.find('[data-kt-dem-field="procurement_category"]'),
				enrichment.categories || [],
				demand.procurement_category || ""
			);
			fillSelect(
				$root.find('[data-kt-dem-field="demand_route"]'),
				enrichment.demand_routes || [],
				demand.demand_route || ""
			);
			fillSelect(
				$root.find('[data-kt-dem-field="aggregation_treatment"]'),
				enrichment.aggregation_treatments || [],
				demand.aggregation_treatment || enrichment.aggregation_treatment || ""
			);
			setField($root, "estimate_basis", demand.estimate_basis || "");
			setField(
				$root,
				"confirmed_estimate",
				formatMoneyInput(demand.confirmed_estimate || demand.requester_estimate)
			);
			setField($root, "related_demands_note", demand.related_demands_note || "");
			setField(
				$root,
				"aggregation_rationale",
				demand.aggregation_rationale || ""
			);
			setLabel(
				$root,
				"duplicate_assessment",
				demand.duplicate_assessment || enrichment.duplicate_assessment || "None found"
			);
			paintEnrichItems($root, demand.items || []);
			paintStrategyCard($root, enrichment);
			paintPvc($root, enrichment.value_treatments || []);
			$root
				.find(
					'[data-kt-dem-action="enrich-save"], [data-kt-dem-action="enrich-return"], [data-kt-dem-action="assign-strategy"], [data-kt-dem-action="change-strategy"], [data-kt-dem-action="remove-strategy"], [data-kt-dem-action="enrich-add-item"]'
				)
				.prop("disabled", !canEnrich);
			$root
				.find('[data-kt-dem-action="enrich-send"]')
				.prop("disabled", !(canEnrich && enrichment.send_ready));
			$root
				.find("[data-kt-dem-enrichment-host]")
				.toggleClass("kt-dem-review-readonly", !canEnrich);
			// Keep Classification / Strategy inputs usable for reading when locked.
			$root
				.find(
					'[data-kt-dem-field="procurement_category"], [data-kt-dem-field="demand_route"], [data-kt-dem-field="estimate_basis"], [data-kt-dem-field="confirmed_estimate"], [data-kt-dem-field="related_demands_note"], [data-kt-dem-field="aggregation_treatment"], [data-kt-dem-field="aggregation_rationale"]'
				)
				.prop("disabled", !canEnrich);
		}

		if (stage === "Budget Confirmation") {
			paintFunding($root, funding, !!payload.can_confirm_funding);
		}

		if (stage === "Final Approval") {
			paintFinalApproval(
				$root,
				(payload && payload.final_approval) || null,
				!!payload.can_final_approve
			);
		}
	}

	function clearReasonModalError($root) {
		$root.find('[data-kt-field-error="reason"]').addClass("hidden").text("");
		$root.find("[data-kt-dem-reason-comment]").removeClass("is-invalid");
	}

	function showReasonModalError($root, message) {
		$root
			.find('[data-kt-field-error="reason"]')
			.text(message || __("Reason is required"))
			.removeClass("hidden");
		$root.find("[data-kt-dem-reason-comment]").addClass("is-invalid").trigger("focus");
	}

	function closeReasonModal($root) {
		$root
			.find("[data-kt-dem-reason-modal]")
			.addClass("hidden")
			.attr("hidden", "hidden")
			.removeAttr("data-kt-dem-reason-decision");
		clearReasonModalError($root);
	}

	function openReasonModal($root, decision) {
		var isReturn = decision === "Return";
		var $m = $root.find("[data-kt-dem-reason-modal]");
		$m.attr("data-kt-dem-reason-decision", decision);
		$root
			.find("[data-kt-dem-reason-title]")
			.text(isReturn ? __("Return for correction") : __("Reject demand"));
		$root
			.find("[data-kt-dem-reason-lead]")
			.text(
				isReturn
					? __(
							"Provide a clear reason so the requester knows what to correct before resubmitting."
						)
					: __("Provide a clear reason for rejecting this demand. This will be recorded on the audit trail.")
			);
		$root.find("[data-kt-dem-reason-comment]").val("");
		$root.find("[data-kt-dem-reason-hint]").prop("checked", false);
		var $hints = $root.find("[data-kt-dem-reason-hints]");
		if (isReturn) {
			$hints.removeAttr("hidden");
		} else {
			$hints.attr("hidden", "hidden");
		}
		var $confirm = $root.find("[data-kt-dem-reason-confirm]");
		$confirm
			.text(isReturn ? __("Confirm return") : __("Confirm reject"))
			.toggleClass("is-return", isReturn)
			.toggleClass("is-reject", !isReturn)
			.prop("disabled", false);
		clearReasonModalError($root);
		$m.removeClass("hidden").removeAttr("hidden");
		setTimeout(function () {
			$root.find("[data-kt-dem-reason-comment]").trigger("focus");
		}, 0);
	}

	function collectReasonModalValues($root) {
		var reason = String($root.find("[data-kt-dem-reason-comment]").val() || "").trim();
		var decision = $root.find("[data-kt-dem-reason-modal]").attr("data-kt-dem-reason-decision");
		var hints = [];
		if (decision === "Return") {
			CORRECTION_HINT_OPTIONS.forEach(function (opt) {
				if ($root.find('[data-kt-dem-reason-hint="' + opt.key + '"]').is(":checked")) {
					hints.push(opt);
				}
			});
		}
		return { reason: reason, correction_hints: hints, decision: decision };
	}

	function bindDemandReview($root, demandId) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var token = Number($root.attr("data-kt-dem-bind-token") || 0) + 1;
		$root.attr("data-kt-dem-bind-token", String(token));
		$root.attr("data-kt-dem-live", "0");
		$root.attr("data-kt-dem-error", "0");

		$root.off(".ktDemReview");
		$root.on("click.ktDemReview", '[data-kt-dem-action="support"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			$btn.prop("disabled", true);
			callMethod(REVIEW_DECIDE, {
				demand: demandId,
				decision: "Support",
				comment: fieldVal($root, "comment") || "",
			})
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Support failed");
					}
					frappe.show_alert({
						message: __("Demand supported — routed to procurement enrichment"),
						indicator: "green",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("record_business_decision_form Support failed", err);
					frappe.show_alert({
						message: __("Could not support demand"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="return"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			openReasonModal($root, "Return");
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="reject"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			openReasonModal($root, "Reject");
		});
		$root.on(
			"click.ktDemReview",
			"[data-kt-dem-reason-close], [data-kt-dem-reason-cancel]",
			function (e) {
				e.preventDefault();
				closeReasonModal($root);
			}
		);
		$root.on("click.ktDemReview", "[data-kt-dem-reason-modal]", function (e) {
			if (e.target === this) {
				closeReasonModal($root);
			}
		});
		$root.on("click.ktDemReview", "[data-kt-dem-reason-confirm]", function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			var vals = collectReasonModalValues($root);
			if (!vals.reason) {
				showReasonModalError($root, __("Reason is required"));
				return;
			}
			clearReasonModalError($root);
			$btn.prop("disabled", true);
			var stage = $root.attr("data-kt-dem-review-stage") || "";
			var isEnrich = stage === "Procurement Enrichment";
			var isBudget = stage === "Budget Confirmation";
			var isFinal = stage === "Final Approval";
			var payload = {
				demand: demandId,
				decision: vals.decision,
				reason: vals.reason,
				comment: fieldVal($root, "comment") || "",
			};
			if (vals.decision === "Return") {
				payload.correction_hints = vals.correction_hints;
			}
			var method = REVIEW_DECIDE;
			if (isFinal) {
				method = FINAL_DECIDE;
				payload = {
					demand: demandId,
					decision: vals.decision,
					reason: vals.reason,
					comment: fieldVal($root, "comment") || "",
				};
			} else if (isBudget && vals.decision === "Return") {
				method = BUDGET_RETURN;
				payload = { demand: demandId, reason: vals.reason };
			} else if (isEnrich) {
				method = PROC_DECIDE;
			}
			callMethod(method, payload)
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error((vals.decision || "Decision") + " failed");
					}
					closeReasonModal($root);
					frappe.show_alert({
						message:
							vals.decision === "Return"
								? __("Demand returned for correction")
								: __("Demand rejected"),
						indicator: vals.decision === "Return" ? "orange" : "red",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("review decision failed", err);
					frappe.show_alert({
						message:
							vals.decision === "Return"
								? __("Could not return demand")
								: __("Could not reject demand"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});

		function reloadReview() {
			return callMethod(REVIEW_GET, { demand: demandId }).then(function (payload) {
				if (String($root.attr("data-kt-dem-bind-token")) !== String(token)) {
					return payload;
				}
				if (!payload || !payload.ok) {
					throw new Error("Empty review payload");
				}
				applyReviewPayload($root, payload);
				$root.attr("data-kt-dem-live", "1");
				return payload;
			});
		}

		function persistEnrichment(sendForBudget) {
			var values = collectEnrichValues($root);
			var items = collectEnrichItems($root);
			// Omit strategy_references so existing Primary/Supporting refs are preserved.
			return callMethod(ENRICH_SAVE, {
				demand: demandId,
				values: values,
				items: items,
				value_treatments: [],
				send_for_budget: sendForBudget ? 1 : 0,
			});
		}

		$root.on("click.ktDemReview", '[data-kt-dem-action="enrich-return"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			openReasonModal($root, "Return");
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="budget-return"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			openReasonModal($root, "Return");
		});
		$root.on(
			"change.ktDemReview",
			'[data-kt-dem-field="funding_confirm_checkbox"]',
			function () {
				syncBudgetConfirmEnabled($root);
			}
		);
		$root.on("click.ktDemReview", '[data-kt-dem-action="open-details-drawer"]', function (e) {
			e.preventDefault();
			openDetailsDrawer($root);
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="close-details-drawer"]', function (e) {
			e.preventDefault();
			closeDetailsDrawer($root);
		});
		$root.on("click.ktDemReview", "[data-kt-dem-details-drawer]", function (e) {
			if (e.target === this) {
				closeDetailsDrawer($root);
			}
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="budget-adjust"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			var panel = $root.find("[data-kt-dem-funding-adjust-panel]")[0];
			if (panel && panel.scrollIntoView) {
				panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
			}
			$root.find('[data-kt-dem-field="funding_adjust_line"]').trigger("focus");
		});
		$root.on(
			"change.ktDemReview",
			'[data-kt-dem-field="funding_exc_resolution"]',
			function () {
				syncExceptionResolutionUi($root);
				if (String($(this).val() || "") === "select_another") {
					var panel = $root.find("[data-kt-dem-funding-adjust-panel]")[0];
					if (panel && panel.scrollIntoView) {
						panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
					}
					$root.find('[data-kt-dem-field="funding_adjust_line"]').trigger("focus");
				}
			}
		);
		$root.on(
			"input.ktDemReview change.ktDemReview",
			'[data-kt-dem-field="funding_exc_return_note"]',
			function () {
				$(this).data("kt-dem-touched", 1);
				syncExceptionResolutionUi($root);
			}
		);
		$root.on("click.ktDemReview", '[data-kt-dem-action="budget-exc-return"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			var note = String(
				$root.find('[data-kt-dem-field="funding_exc_return_note"]').val() || ""
			).trim();
			if (!note) {
				frappe.show_alert({
					message: __("Return note is required"),
					indicator: "orange",
				});
				return;
			}
			$btn.prop("disabled", true);
			callMethod(BUDGET_EXC_RESOLVE, {
				demand: demandId,
				resolution: "Return",
				reason: note,
			})
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Exception return failed");
					}
					frappe.show_alert({
						message: __("Demand returned for correction"),
						indicator: "orange",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("resolve_funding_exception_form failed", err);
					frappe.show_alert({
						message: __("Could not return demand"),
						indicator: "red",
					});
					syncExceptionResolutionUi($root);
				})
				.finally(function () {
					$btn.prop("disabled", false);
					syncExceptionResolutionUi($root);
				});
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="budget-exc-save-note"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			var note = String(
				$root.find('[data-kt-dem-field="funding_exc_return_note"]').val() || ""
			).trim();
			if (!note) {
				frappe.show_alert({
					message: __("Resolution note is required"),
					indicator: "orange",
				});
				return;
			}
			$btn.prop("disabled", true);
			callMethod(BUDGET_EXC_SAVE_NOTE, { demand: demandId, reason: note })
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Save note failed");
					}
					frappe.show_alert({
						message: __("Resolution note saved — funding still cannot be confirmed"),
						indicator: "orange",
					});
					if (res.funding && typeof paintFunding === "function") {
						paintFunding(
							$root,
							res.funding,
							$root.attr("data-kt-dem-can-confirm-funding") === "1"
						);
					}
					return reloadReview();
				})
				.catch(function (err) {
					console.warn("save_funding_exception_note_form failed", err);
					frappe.show_alert({
						message: __("Could not save resolution note"),
						indicator: "red",
					});
				})
				.finally(function () {
					syncExceptionResolutionUi($root);
				});
		});
		$root.on(
			"change.ktDemReview input.ktDemReview",
			'[data-kt-dem-field="funding_adjust_line"], [data-kt-dem-field="funding_adjust_amount"]',
			function () {
				$(this).data("kt-dem-touched", 1);
			}
		);
		$root.on("click.ktDemReview", '[data-kt-dem-action="budget-apply-adjust"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			var line = String($root.find('[data-kt-dem-field="funding_adjust_line"]').val() || "").trim();
			var amount = parseMoneyInput($root.find('[data-kt-dem-field="funding_adjust_amount"]').val());
			if (!line) {
				frappe.show_alert({
					message: __("Select a Budget Line to adjust"),
					indicator: "orange",
				});
				return;
			}
			$btn.prop("disabled", true);
			callMethod(BUDGET_ADJUST, {
				demand: demandId,
				budget_line: line,
				allocation_amount: amount > 0 ? amount : null,
			})
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Adjust failed");
					}
					var funding = res.funding || {};
					var cleared = !funding.exception && funding.confirm_ready;
					frappe.show_alert({
						message: cleared
							? __("Allocation adjusted — funding exception cleared")
							: __("Allocation adjusted"),
						indicator: cleared ? "green" : "orange",
					});
					$root
						.find('[data-kt-dem-field="funding_adjust_line"], [data-kt-dem-field="funding_adjust_amount"]')
						.removeData("kt-dem-touched");
					if (funding && typeof paintFunding === "function") {
						paintFunding($root, funding, $root.attr("data-kt-dem-can-confirm-funding") === "1");
					}
					return reloadReview();
				})
				.catch(function (err) {
					console.warn("adjust_funding_allocation_form failed", err);
					frappe.show_alert({
						message: __("Could not apply allocation adjustment"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
					syncBudgetConfirmEnabled($root);
				});
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="budget-confirm"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			$btn.prop("disabled", true);
			callMethod(BUDGET_CONFIRM, { demand: demandId })
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Confirm failed");
					}
					frappe.show_alert({
						message: __("Funding confirmed — awaiting Final approval (no funds reserved)"),
						indicator: "green",
					});
					$root.attr("data-kt-dem-review-stage", res.stage || "Final Approval");
					return reloadReview();
				})
				.catch(function (err) {
					console.warn("confirm_demand_funding_form failed", err);
					frappe.show_alert({
						message: __("Could not confirm funding"),
						indicator: "red",
					});
				})
				.finally(function () {
					syncBudgetConfirmEnabled($root);
				});
		});
		$root.on(
			"change.ktDemReview",
			'[data-kt-dem-field="fa_approve_checkbox"]',
			function () {
				syncFinalApproveEnabled($root);
			}
		);
		$root.on("click.ktDemReview", '[data-kt-dem-action="final-return"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			openReasonModal($root, "Return");
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="final-reject"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			openReasonModal($root, "Reject");
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="final-approve"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			$btn.prop("disabled", true);
			callMethod(FINAL_APPROVE, { demand: demandId })
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Approve failed");
					}
					frappe.show_alert({
						message: __(
							"Demand approved — funding reserved; ready for Procurement Planning"
						),
						indicator: "green",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("approve_and_reserve_form failed", err);
					frappe.show_alert({
						message: __("Could not approve and reserve funding"),
						indicator: "red",
					});
					syncFinalApproveEnabled($root);
				});
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="enrich-save"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			$btn.prop("disabled", true);
			persistEnrichment(false)
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Save failed");
					}
					frappe.show_alert({
						message: __("Enrichment saved"),
						indicator: "green",
					});
					return reloadReview();
				})
				.catch(function (err) {
					console.warn("enrich_demand_form save failed", err);
					frappe.show_alert({
						message: __("Could not save enrichment"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="enrich-send"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			$btn.prop("disabled", true);
			persistEnrichment(true)
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Send failed");
					}
					frappe.show_alert({
						message: __("Sent for Budget confirmation"),
						indicator: "green",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("enrich_demand_form send failed", err);
					frappe.show_alert({
						message: __("Could not send for Budget confirmation"),
						indicator: "red",
					});
					$btn.prop("disabled", false);
					return reloadReview();
				});
		});
		$root.on(
			"click.ktDemReview",
			'[data-kt-dem-action="assign-strategy"], [data-kt-dem-action="change-strategy"]',
			function (e) {
				e.preventDefault();
				if ($(this).prop("disabled")) {
					return;
				}
				openStrategyDrawer($root, demandId);
			}
		);
		$root.on("click.ktDemReview", '[data-kt-dem-action="remove-strategy"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			callMethod(ENRICH_SAVE, {
				demand: demandId,
				values: collectEnrichValues($root),
				items: collectEnrichItems($root),
				strategy_references: [],
				value_treatments: [],
				send_for_budget: 0,
			})
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Remove failed");
					}
					frappe.show_alert({
						message: __("Strategy assignment removed"),
						indicator: "orange",
					});
					return reloadReview();
				})
				.catch(function (err) {
					console.warn("remove strategy failed", err);
					frappe.show_alert({
						message: __("Could not remove Strategy assignment"),
						indicator: "red",
					});
				});
		});
		$root.on(
			"click.ktDemReview",
			'[data-kt-dem-action="close-strategy-drawer"], [data-kt-dem-action="close-strategy-drawer"]',
			function (e) {
				e.preventDefault();
				closeStrategyDrawer($root);
			}
		);
		$root.on("click.ktDemReview", "[data-kt-dem-strategy-drawer]", function (e) {
			if (e.target === this) {
				closeStrategyDrawer($root);
			}
		});
		var suggestTimer = null;
		function reloadSuggestionsSoon() {
			if (suggestTimer) {
				clearTimeout(suggestTimer);
			}
			suggestTimer = setTimeout(function () {
				loadStrategySuggestions($root, demandId);
			}, 250);
		}
		$root.on("input.ktDemReview", '[data-kt-dem-field="strategy_search"]', reloadSuggestionsSoon);
		$root.on(
			"change.ktDemReview",
			'[data-kt-dem-field="strategy_plan_filter"], [data-kt-dem-field="strategy_period_filter"]',
			function () {
				loadStrategySuggestions($root, demandId);
			}
		);
		$root.on("change.ktDemReview", 'input[name="kt-dem-strategy-target"]', function () {
			syncStrategyDrawerSelection($root);
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="add-supporting-target"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			frappe.show_alert({
				message: __("Select the Primary target first, then Assign. Supporting targets can be added with a reason on a follow-up save."),
				indicator: "blue",
			});
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="confirm-strategy"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled")) {
				return;
			}
			var opt = selectedStrategyOption($root);
			if (!opt) {
				frappe.show_alert({
					message: __("Select a Primary Strategy target"),
					indicator: "orange",
				});
				return;
			}
			var reason = fieldVal($root, "strategy_reason");
			if (!reason) {
				frappe.show_alert({
					message: __("Confirmation reason is required"),
					indicator: "orange",
				});
				return;
			}
			$btn.prop("disabled", true);
			var values = collectEnrichValues($root);
			var refs = [];
			var okMessage = __("Strategy target assigned");
			if (opt.none) {
				values.strategy_no_alignment_reason = reason;
				refs = [];
				okMessage = __("No direct Strategy alignment recorded");
			} else {
				values.strategy_no_alignment_reason = "";
				refs = [
					{
						reference_type: "Primary",
						plan: opt.plan_version_id || opt.plan_code,
						plan_version_id: opt.plan_version_id,
						target_id: opt.target_id,
						target_code: opt.target_code,
						target_name: opt.target_name,
						hierarchy_path: opt.hierarchy_path || opt.snapshot_label,
						snapshot_label: opt.snapshot_label,
						selection_source: opt.is_suggested ? "Suggested" : "Manual",
						confirmation_reason: reason,
					},
				];
			}
			callMethod(ENRICH_SAVE, {
				demand: demandId,
				values: values,
				items: collectEnrichItems($root),
				strategy_references: refs,
				value_treatments: [],
				send_for_budget: 0,
			})
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Assign failed");
					}
					closeStrategyDrawer($root);
					frappe.show_alert({
						message: okMessage,
						indicator: "green",
					});
					return reloadReview();
				})
				.catch(function (err) {
					console.warn("assign strategy failed", err);
					frappe.show_alert({
						message: __("Could not assign Strategy target"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="enrich-add-item"]', function (e) {
			e.preventDefault();
			if ($(this).prop("disabled")) {
				return;
			}
			$root.find("[data-kt-dem-enrich-items-tbody]").append(
				enrichRowHtml({
					description: "",
					quantity: 1,
					uom: "Lot",
					confirmed_quantity: 1,
					confirmed_uom: "Lot",
					confirmed_estimate: 0,
					unit_estimate: 0,
				})
			);
			syncEnrichItemRowTotals($root);
		});
		$root.on("click.ktDemReview", '[data-kt-dem-action="enrich-remove-item"]', function (e) {
			e.preventDefault();
			$(this).closest("[data-kt-dem-enrich-item-row]").remove();
			syncEnrichItemRowTotals($root);
		});
		$root.on(
			"input.ktDemReview change.ktDemReview",
			'[data-kt-dem-enrich-item="confirmed_quantity"], [data-kt-dem-enrich-item="unit_estimate"]',
			function () {
				syncEnrichItemRowTotals($root);
			}
		);

		return reloadReview().catch(function (err) {
			$root.attr("data-kt-dem-live", "0");
			$root.attr("data-kt-dem-error", "1");
			console.warn("Demand review bind failed", err);
			frappe.show_alert({
				message: __("Could not load demand review"),
				indicator: "red",
			});
		});
	}

	kentender_procurement.live.bindDemandReview = bindDemandReview;

	/* ---------- DEM-UI-09 / 09A–D Approved Demand detail ---------- */

	var DETAIL_GET = "kentender_procurement.demands.api.get_demand_detail";
	var DETAIL_CANCEL = "kentender_procurement.demands.api.cancel_remaining_demand_form";

	function selectDetailTab($root, tab) {
		var key = tab || "overview";
		$root.find("[data-kt-dem-detail-tab]").each(function () {
			var t = $(this).attr("data-kt-dem-detail-tab");
			var on = t === key;
			$(this).toggleClass("is-active", on).attr("aria-selected", on ? "true" : "false");
		});
		$root.find("[data-kt-dem-detail-panel]").each(function () {
			var t = $(this).attr("data-kt-dem-detail-panel");
			if (t === key) {
				$(this).removeClass("hidden").removeAttr("hidden");
			} else {
				$(this).addClass("hidden").attr("hidden", "hidden");
			}
		});
		$root.attr("data-kt-dem-detail-tab", key);
	}

	function paintDetailItems($root, items) {
		var $tb = $root.find("[data-kt-dem-detail-items]");
		$tb.empty();
		(items || []).forEach(function (it) {
			$tb.append(
				$("<tr/>")
					.append($("<td/>").text(it.item_description || "—"))
					.append($("<td/>").text(String(it.quantity == null ? "—" : it.quantity)))
					.append($("<td/>").text(it.uom || "—"))
					.append(
						$("<td/>")
							.addClass("font-data-mono")
							.text(it.approved_estimate_display || "—")
					)
			);
		});
	}

	function paintDetailPvc($root, rows) {
		var $tb = $root.find("[data-kt-dem-detail-pvc]");
		$tb.empty();
		if (!(rows || []).length) {
			$tb.append(
				$("<tr/>").append(
					$('<td colspan="3"/>').text(__("No public-value treatments recorded."))
				)
			);
			return;
		}
		rows.forEach(function (r) {
			$tb.append(
				$("<tr/>")
					.append($("<td/>").text(r.commitment || "—"))
					.append($("<td/>").text(r.treatment || "—"))
					.append($("<td/>").text(r.rationale || "—"))
			);
		});
	}

	function paintDetailDownstream($root, rows) {
		var $tb = $root.find("[data-kt-dem-detail-downstream]");
		var $empty = $root.find("[data-kt-dem-detail-downstream-empty]");
		$tb.empty();
		if (!(rows || []).length) {
			$empty.removeClass("hidden").removeAttr("hidden");
			return;
		}
		$empty.addClass("hidden").attr("hidden", "hidden");
		rows.forEach(function (r) {
			var $action = $("<span/>").text(r.action_label || "View");
			if (!r.action_enabled) {
				$action.addClass("text-on-surface-variant");
			}
			$tb.append(
				$("<tr/>")
					.append(
						$("<td/>").text(
							(r.record_type ? r.record_type + " " : "") + (r.record_display || "—")
						)
					)
					.append($("<td/>").addClass("font-data-mono").text(r.value_display || "—"))
					.append($("<td/>").text(r.relationship || "—"))
					.append($("<td/>").text(r.status || "—"))
					.append($("<td/>").append($action))
			);
		});
	}

	function paintDetailDecisions($root, rows) {
		var $ol = $root.find("[data-kt-dem-detail-decisions]");
		$ol.empty();
		(rows || []).forEach(function (d) {
			var meta = [d.actor_label || "", d.decided_at_display || ""]
				.filter(Boolean)
				.join(" — ");
			$ol.append(
				$("<li/>")
					.addClass("kt-dem-ui09-timeline-item")
					.append($('<span class="kt-dem-ui09-timeline-dot" aria-hidden="true"/>'))
					.append(
						$("<div/>")
							.append(
								$('<p class="kt-dem-ui09-timeline-label mb-0"/>').text(
									d.label || d.decision || "—"
								)
							)
							.append($('<p class="kt-dem-ui09-timeline-meta mb-0"/>').text(meta || "—"))
					)
			);
		});
	}

	function paintDetailAudit($root, rows, selector) {
		var $tb = $root.find(selector);
		$tb.empty();
		(rows || []).forEach(function (d) {
			$tb.append(
				$("<tr/>")
					.append($("<td/>").text(d.decided_at_display || d.decided_at || "—"))
					.append($("<td/>").text(d.actor_label || "—"))
					.append($("<td/>").text(d.label || d.decision || "—"))
					.append($("<td/>").text(d.reason || "—"))
			);
		});
	}

	function applyDetailPayload($root, payload) {
		var demand = (payload && payload.demand) || {};
		var ov = (payload && payload.overview) || {};
		var sc = (payload && payload.scope) || {};
		var st = (payload && payload.strategy) || {};
		var fu = (payload && payload.funding) || {};
		var lc = (payload && payload.lifecycle) || {};
		var alloc = (fu && fu.allocation) || {};
		var rsv = (fu && fu.reservation) || {};
		var ctrl = (ov && ov.control_summary) || {};

		setLabel($root, "detail_code", demand.demand_code || "—");
		setLabel(
			$root,
			"detail_status",
			String(demand.status_display || demand.status || "Approved").toUpperCase()
		);
		setLabel($root, "detail_title", demand.title || "—");
		setLabel($root, "detail_route", demand.demand_route || "Standard");
		setLabel($root, "detail_estimate", demand.confirmed_estimate_display || "—");
		setLabel($root, "detail_planning_usage", demand.planning_usage || "—");
		setLabel(
			$root,
			"detail_lock_message",
			payload.lock_message ||
				__(
					"The approved Demand baseline is locked. Material change requires cancellation and a linked replacement Demand."
				)
		);

		setLabel($root, "ov_need", ov.need_summary || "—");
		setLabel($root, "ov_owning_unit", ov.owning_unit_display || "—");
		setLabel($root, "ov_required_by", ov.required_by_display || "—");
		setLabel($root, "ov_amount", ov.approved_amount_display || "—");
		setLabel($root, "ov_funding_status", ov.funding_status_display || "—");
		setLabel($root, "ov_downstream", ov.downstream_summary || "—");
		setLabel($root, "ov_planning", ov.planning_usage || "—");
		setLabel($root, "ov_ctrl_scope", ctrl.scope_detail || "—");
		setLabel($root, "ov_ctrl_strategy", ctrl.strategy_detail || "—");
		setLabel($root, "ov_ctrl_decisions", ctrl.decisions_detail || "—");

		setLabel($root, "sc_what", sc.what_is_needed || "—");
		setLabel($root, "sc_why", sc.why_needed || "—");
		setLabel($root, "sc_outcome", sc.expected_outcome || "—");
		setLabel($root, "sc_beneficiaries", sc.beneficiaries || "—");
		setLabel($root, "sc_owning_unit", sc.owning_unit_display || "—");
		setLabel($root, "sc_required_by", sc.required_by_display || "—");
		setLabel($root, "sc_delivery", sc.delivery_location || "—");
		setLabel($root, "sc_route", sc.demand_route || "—");
		setLabel($root, "sc_category", sc.procurement_category || "—");
		setLabel($root, "sc_estimate", sc.confirmed_estimate_display || "—");
		setLabel($root, "sc_basis", sc.estimate_basis || "—");
		setLabel($root, "sc_total", sc.total_display || "—");
		paintDetailItems($root, sc.items || []);

		setLabel($root, "st_confirmed", st.confirmed_label || __("Confirmed at approval"));
		setLabel($root, "st_plan", st.plan_display || "—");
		setLabel($root, "st_version", st.plan_version || "—");
		setLabel($root, "st_outcome", st.outcome || "—");
		setLabel($root, "st_primary", st.primary_target || "—");
		setLabel($root, "st_supporting", st.supporting_target || "—");
		setLabel($root, "st_reason", st.supporting_reason || "—");
		setLabel($root, "st_disclaimer", st.disclaimer || "");
		paintDetailPvc($root, st.value_treatments || []);

		setLabel($root, "fu_budget", alloc.budget_display || "—");
		setLabel($root, "fu_line", alloc.budget_line_display || "—");
		setLabel($root, "fu_alloc", alloc.confirmed_allocation_display || "—");
		setLabel($root, "fu_bo", alloc.budget_officer_label || "—");
		setLabel($root, "fu_date", alloc.confirmed_on_display || "—");
		setLabel($root, "fu_consistency", alloc.strategy_consistency || "—");
		setLabel($root, "fu_rsv", rsv.reservation_code || "—");
		setLabel($root, "fu_condition", rsv.condition_display || rsv.status || "—");
		setLabel($root, "fu_original", rsv.original_amount_display || "—");
		setLabel($root, "fu_converted", rsv.converted_amount_display || "—");
		setLabel($root, "fu_remaining", rsv.remaining_reserved_display || "—");
		setLabel($root, "fu_equation", rsv.equation_display || "—");
		setLabel(
			$root,
			"fu_note",
			(fu && fu.carry_forward_note) ||
				rsv.carry_forward_note ||
				__(
					"The reservation identity carries forward through Planning and Tendering. Contract and downstream record details are shown under Lifecycle."
				)
		);

		paintDetailDownstream($root, lc.downstream || []);
		paintDetailDecisions($root, lc.decisions || []);
		paintDetailAudit($root, lc.audit || [], "[data-kt-dem-detail-audit]");
		paintDetailAudit($root, lc.audit || [], "[data-kt-dem-detail-audit-full]");

		var $cancel = $root.find('[data-kt-dem-action="detail-cancel"]');
		if (payload.can_cancel) {
			$cancel.removeClass("hidden").removeAttr("hidden");
		} else {
			$cancel.addClass("hidden").attr("hidden", "hidden");
		}
		$root.attr("data-kt-dem-can-cancel", payload.can_cancel ? "1" : "0");
	}

	function bindDemandDetail($root, demandId) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var token = Number($root.attr("data-kt-dem-bind-token") || 0) + 1;
		$root.attr("data-kt-dem-bind-token", String(token));
		$root.attr("data-kt-dem-live", "0");
		$root.attr("data-kt-dem-error", "0");
		$root.off(".ktDemDetail");

		selectDetailTab($root, $root.attr("data-kt-dem-detail-tab") || "overview");

		$root.on("click.ktDemDetail", "[data-kt-dem-detail-tab]", function (e) {
			e.preventDefault();
			selectDetailTab($root, $(this).attr("data-kt-dem-detail-tab"));
		});
		$root.on("click.ktDemDetail", '[data-kt-dem-action="goto-tab"]', function (e) {
			e.preventDefault();
			selectDetailTab($root, $(this).attr("data-kt-dem-tab"));
		});
		$root.on("click.ktDemDetail", '[data-kt-dem-action="detail-print"]', function (e) {
			e.preventDefault();
			window.print();
		});
		$root.on("click.ktDemDetail", '[data-kt-dem-action="open-audit"]', function (e) {
			e.preventDefault();
			$root
				.find("[data-kt-dem-detail-audit-modal]")
				.removeClass("hidden")
				.removeAttr("hidden");
		});
		$root.on("click.ktDemDetail", '[data-kt-dem-action="close-audit"]', function (e) {
			e.preventDefault();
			$root
				.find("[data-kt-dem-detail-audit-modal]")
				.addClass("hidden")
				.attr("hidden", "hidden");
		});
		$root.on("click.ktDemDetail", '[data-kt-dem-action="detail-cancel"]', function (e) {
			e.preventDefault();
			var $btn = $(this);
			if ($btn.prop("disabled") || $btn.is("[hidden]")) {
				return;
			}
			var reason = window.prompt(
				__("Provide a reason for cancelling the remaining Demand"),
				""
			);
			if (reason == null) {
				return;
			}
			reason = String(reason || "").trim();
			if (!reason) {
				frappe.show_alert({
					message: __("A cancellation reason is required"),
					indicator: "orange",
				});
				return;
			}
			$btn.prop("disabled", true);
			callMethod(DETAIL_CANCEL, { demand: demandId, reason: reason })
				.then(function (res) {
					if (!res || !res.ok) {
						throw new Error("Cancel failed");
					}
					frappe.show_alert({
						message: __("Demand cancelled — remaining reservation released"),
						indicator: "orange",
					});
					frappe.set_route("demands-workspace");
				})
				.catch(function (err) {
					console.warn("cancel_remaining_demand_form failed", err);
					frappe.show_alert({
						message: __("Could not cancel remaining Demand"),
						indicator: "red",
					});
				})
				.finally(function () {
					$btn.prop("disabled", false);
				});
		});

		return callMethod(DETAIL_GET, { demand: demandId })
			.then(function (payload) {
				if (String($root.attr("data-kt-dem-bind-token")) !== String(token)) {
					return payload;
				}
				if (!payload || !payload.ok) {
					throw new Error("Empty detail payload");
				}
				applyDetailPayload($root, payload);
				$root.attr("data-kt-dem-live", "1");
				return payload;
			})
			.catch(function (err) {
				$root.attr("data-kt-dem-live", "0");
				$root.attr("data-kt-dem-error", "1");
				console.warn("Demand detail bind failed", err);
				frappe.show_alert({
					message: __("Could not load demand detail"),
					indicator: "red",
				});
			});
	}

	kentender_procurement.live.bindDemandDetail = bindDemandDetail;

	/* —— DEM-UI-10 Demand performance —— */
	var PERF_GET = "kentender_procurement.demands.api.get_demand_performance_form";

	function fillPerfFilterSelect($sel, options, valueKey, labelFn, placeholder) {
		var current = $sel.val() || "";
		$sel.empty();
		$sel.append($("<option/>").attr("value", "").text(placeholder || "—"));
		(options || []).forEach(function (opt) {
			if (typeof opt === "string") {
				$sel.append($("<option/>").attr("value", opt).text(opt));
				return;
			}
			var id = opt[valueKey] || opt.id || opt.code || "";
			var label = labelFn ? labelFn(opt) : opt.name || opt.code || id;
			$sel.append($("<option/>").attr("value", id).text(label));
		});
		if (current) {
			$sel.val(current);
		}
	}

	function readPerfFilters($root) {
		return {
			procuring_entity: $root.find('[data-kt-dem-filter="procuring_entity"]').val() || "",
			owner_org_unit: $root.find('[data-kt-dem-filter="owner_org_unit"]').val() || "",
			demand_route: $root.find('[data-kt-dem-filter="demand_route"]').val() || "",
			status: $root.find('[data-kt-dem-filter="status"]').val() || "",
			current_stage: $root.find('[data-kt-dem-filter="current_stage"]').val() || "",
		};
	}

	function clearPerfFilters($root) {
		$root.find("[data-kt-dem-filter]").val("");
	}

	function openPerfRoute(route, demandName) {
		if (!demandName) {
			return;
		}
		var r = (route || "demand-detail").replace(/^\/?desk\//, "");
		frappe.set_route(r, demandName);
	}

	function paintPerfFlow($root, rows) {
		var $tb = $root.find("[data-kt-dem-perf-flow]");
		$tb.empty();
		(rows || []).forEach(function (row) {
			var oldest =
				row.count && row.oldest_waiting_days
					? String(row.oldest_waiting_days) + " days"
					: "—";
			var $tr = $("<tr/>");
			$tr.append($("<td/>").text(row.stage_display || row.stage || "—"));
			$tr.append(
				$('<td class="text-right font-data-mono"/>').text(
					String(row.count != null ? row.count : 0)
				)
			);
			$tr.append($('<td class="text-right font-data-mono"/>').text(oldest));
			$tr.append($("<td/>").text(row.attention || "—"));
			var $action = $('<td class="text-right"/>');
			if (row.view_demand && row.view_demand.demand) {
				$action.append(
					$('<button type="button" class="kt-dem-ui10-link"/>')
						.text("View")
						.attr("data-kt-dem-action", "perf-view")
						.attr("data-demand", row.view_demand.demand)
						.attr("data-route", row.view_demand.route || "demand-detail")
				);
			} else {
				$action.append($('<span class="font-data-mono text-on-surface-variant"/>').text("—"));
			}
			$tr.append($action);
			$tb.append($tr);
		});
	}

	function paintPerfPlanning($root, rows) {
		var $tb = $root.find("[data-kt-dem-perf-planning]");
		var $empty = $root.find("[data-kt-dem-perf-planning-empty]");
		$tb.empty();
		if (!rows || !rows.length) {
			$empty.removeClass("hidden");
			return;
		}
		$empty.addClass("hidden");
		rows.forEach(function (row) {
			var $tr = $("<tr/>");
			$tr.append(
				$("<td/>").html(
					'<span class="block font-data-mono font-bold text-primary mb-1">' +
						esc(row.demand_code || "") +
						"</span>" +
						'<span class="text-on-surface">' +
						esc(row.title || "—") +
						"</span>"
				)
			);
			$tr.append(
				$("<td/>").html(
					'<span class="text-on-surface-variant text-sm block">Approved</span>' +
						'<span class="font-data-mono">' +
						esc(row.approved_value_display || "—") +
						"</span>"
				)
			);
			$tr.append(
				$("<td/>").append(
					$('<span class="kt-dem-ui10-pill"/>').text(row.planning_usage || "—")
				)
			);
			$tr.append(
				$('<td class="font-data-mono text-sm text-on-surface-variant"/>').text(
					row.plan_item_codes_display || "—"
				)
			);
			$tr.append(
				$('<td class="text-right"/>').append(
					$('<button type="button" class="kt-dem-ui10-link"/>')
						.text("View")
						.attr("data-kt-dem-action", "perf-view")
						.attr("data-demand", row.demand || "")
						.attr("data-route", row.route || "demand-detail")
				)
			);
			$tb.append($tr);
		});
	}

	function paintPerfStrategy($root, rows) {
		var $tb = $root.find("[data-kt-dem-perf-strategy]");
		$tb.empty();
		if (!rows || !rows.length) {
			$tb.append(
				$("<tr/>").append(
					$('<td colspan="5" class="text-on-surface-variant"/>').text(
						__("No Approved Demand strategy coverage in this scope.")
					)
				)
			);
			return;
		}
		rows.forEach(function (row) {
			var $tr = $("<tr/>");
			$tr.append($("<td/>").text(row.strategy_label || "—"));
			$tr.append(
				$('<td class="text-right font-data-mono"/>').text(
					row.approved_value_display || "—"
				)
			);
			$tr.append(
				$('<td class="text-center font-data-mono"/>').text(
					String(row.required_commitments != null ? row.required_commitments : 0)
				)
			);
			$tr.append(
				$('<td class="text-center font-data-mono"/>').text(
					String(row.addressed_count != null ? row.addressed_count : 0)
				)
			);
			$tr.append($('<td class="text-right text-on-surface-variant text-sm"/>').text(
				row.attention || "—"
			));
			$tb.append($tr);
		});
	}

	function applyPerfPayload($root, payload) {
		var header = payload.header || {};
		var summary = payload.summary || {};
		var fund = payload.funding_control || {};
		var opts = payload.filter_options || {};

		var ctxParts = [];
		if (header.pe_label) {
			ctxParts.push(header.pe_label);
		}
		if (header.as_at_display) {
			ctxParts.push("As at " + header.as_at_display);
		}
		$root.find('[data-kt-dem-label="perf_context"]').text(ctxParts.join(" · ") || header.basis || "—");

		$root.find('[data-kt-dem-label="strip_demands"]').text(String(summary.demands_count || 0));
		$root
			.find('[data-kt-dem-label="strip_approved_value"]')
			.text(summary.approved_value_display || "KES 0.00");
		$root.find('[data-kt-dem-label="strip_returned"]').text(String(summary.returned_count || 0));
		$root
			.find('[data-kt-dem-label="strip_awaiting"]')
			.text(String(summary.awaiting_action_count || 0));
		$root
			.find('[data-kt-dem-label="strip_planning"]')
			.text(summary.planning_taken_display || "0 of 0");

		$root.find('[data-kt-dem-label="fund_auto"]').text(String(fund.auto_matches || 0));
		$root.find('[data-kt-dem-label="fund_bo"]').text(String(fund.bo_confirmations || 0));
		$root.find('[data-kt-dem-label="fund_adjusted"]').text(String(fund.adjusted || 0));
		$root.find('[data-kt-dem-label="fund_exceptions"]').text(String(fund.exceptions || 0));
		$root
			.find('[data-kt-dem-label="fund_unfunded"]')
			.text(fund.unfunded_amount_display || "KES 0.00");

		var $exc = $root.find('[data-kt-dem-action="view-funding-exception"]');
		if (fund.exception_demand && fund.exception_demand.demand) {
			$exc
				.removeAttr("hidden")
				.attr("data-demand", fund.exception_demand.demand)
				.attr("data-route", fund.exception_demand.route || "demand-review");
		} else {
			$exc.attr("hidden", "hidden").removeAttr("data-demand");
		}

		fillPerfFilterSelect(
			$root.find('[data-kt-dem-filter="procuring_entity"]'),
			opts.procuring_entities || [],
			"id",
			function (o) {
				return o.name && o.code ? o.name + " (" + o.code + ")" : o.name || o.code || o.id;
			},
			__("All entities")
		);
		fillPerfFilterSelect(
			$root.find('[data-kt-dem-filter="owner_org_unit"]'),
			opts.owner_org_units || [],
			"id",
			function (o) {
				return o.name || o.code || o.id;
			},
			__("Owning unit")
		);
		fillPerfFilterSelect(
			$root.find('[data-kt-dem-filter="demand_route"]'),
			opts.routes || [],
			null,
			null,
			__("Demand route")
		);
		fillPerfFilterSelect(
			$root.find('[data-kt-dem-filter="status"]'),
			opts.statuses || [],
			null,
			null,
			__("Status")
		);
		fillPerfFilterSelect(
			$root.find('[data-kt-dem-filter="current_stage"]'),
			opts.stages || [],
			null,
			null,
			__("Current stage")
		);

		var applied = payload.filters_applied || {};
		Object.keys(applied).forEach(function (k) {
			if (applied[k]) {
				$root.find('[data-kt-dem-filter="' + k + '"]').val(applied[k]);
			}
		});

		paintPerfFlow($root, payload.flow_ageing || []);
		paintPerfPlanning($root, payload.planning_uptake || []);
		paintPerfStrategy($root, payload.strategy_coverage || []);
	}

	function loadPerf($root, token) {
		var filters = readPerfFilters($root);
		return callMethod(PERF_GET, { filters: JSON.stringify(filters) })
			.then(function (payload) {
				if (String($root.attr("data-kt-dem-bind-token")) !== String(token)) {
					return payload;
				}
				if (!payload || !payload.ok) {
					throw new Error("Empty performance payload");
				}
				applyPerfPayload($root, payload);
				$root.attr("data-kt-dem-live", "1");
				return payload;
			})
			.catch(function (err) {
				$root.attr("data-kt-dem-live", "0");
				$root.attr("data-kt-dem-error", "1");
				console.warn("Demand performance bind failed", err);
				frappe.show_alert({
					message: __("Could not load demand performance"),
					indicator: "red",
				});
			});
	}

	function bindDemandPerformance($root) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var token = Number($root.attr("data-kt-dem-bind-token") || 0) + 1;
		$root.attr("data-kt-dem-bind-token", String(token));
		$root.attr("data-kt-dem-live", "0");
		$root.attr("data-kt-dem-error", "0");
		$root.off(".ktDemPerf");

		$root.on("click.ktDemPerf", '[data-kt-dem-action="perf-apply"]', function (e) {
			e.preventDefault();
			var t = Number($root.attr("data-kt-dem-bind-token") || 0) + 1;
			$root.attr("data-kt-dem-bind-token", String(t));
			loadPerf($root, t);
		});
		$root.on("click.ktDemPerf", '[data-kt-dem-action="perf-clear"]', function (e) {
			e.preventDefault();
			clearPerfFilters($root);
			var t = Number($root.attr("data-kt-dem-bind-token") || 0) + 1;
			$root.attr("data-kt-dem-bind-token", String(t));
			loadPerf($root, t);
		});
		$root.on("click.ktDemPerf", '[data-kt-dem-action="perf-view"]', function (e) {
			e.preventDefault();
			openPerfRoute($(this).attr("data-route"), $(this).attr("data-demand"));
		});
		$root.on("click.ktDemPerf", '[data-kt-dem-action="view-funding-exception"]', function (e) {
			e.preventDefault();
			openPerfRoute($(this).attr("data-route") || "demand-review", $(this).attr("data-demand"));
		});

		return loadPerf($root, token);
	}

	kentender_procurement.live.bindDemandPerformance = bindDemandPerformance;
})();
