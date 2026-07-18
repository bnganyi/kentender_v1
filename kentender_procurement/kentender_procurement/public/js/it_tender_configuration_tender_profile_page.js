// CFG-01 — Tender Profile (C2-CFG1).
// Route contract: /desk/it-tender-configuration-tender-profile/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-01";
	var PAGE_SLUG = "it-tender-configuration-tender-profile";
	var GET_API = "kentender_procurement.tender_configurations.get_tender_configuration_profile";
	var SAVE_API = "kentender_procurement.tender_configurations.save_tender_configuration_profile";
	var STORAGE_KEY = "kt_cl_cfg01_configuration_id";
	var LOT_SINGLE = "Single lot";
	var LOT_MULTIPLE = "Multiple lots";
	var LOT_NA = "Not applicable";
	var SUBTITLE =
		"Confirm the tender identity, procurement context, lot structure, and applicable standard tender document.";

	var state = {
		payload: null,
		configurationId: null,
		mounting: false,
		dirty: false,
		lots: [],
		saving: false,
	};

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function c() {
		return kentender_core.cl_components || kentender_core.cl.components;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
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

	function helper(key, fallback) {
		var h = (state.payload && state.payload.helpers) || {};
		return h[key] || fallback || "";
	}

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg01-root">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-cfg01-btn kt-cl-cfg01-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg01-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function lotStructureValue(data) {
		return data.lot_structure || "";
	}

	function radioClass(selected, value) {
		return selected === value
			? "kt-cl-cfg01-radio kt-cl-cfg01-radio--selected"
			: "kt-cl-cfg01-radio";
	}

	function lotsTableHtml(lots, show) {
		if (!show) {
			return (
				'<div class="kt-cl-cfg01-lots hidden" data-testid="kt-cl-cfg01-lots" aria-hidden="true"></div>'
			);
		}
		var rows = (lots || [])
			.map(function (row, idx) {
				return (
					"<tr data-lot-index=\"" +
					idx +
					'">' +
					'<td><input type="text" class="kt-cl-cfg01-input" data-lot-field="lot_no" value="' +
					esc(row.lot_no || "Lot " + (idx + 1)) +
					'" /></td>' +
					'<td><input type="text" class="kt-cl-cfg01-input" data-lot-field="lot_title" value="' +
					esc(row.lot_title || "") +
					'" /></td>' +
					'<td><input type="text" class="kt-cl-cfg01-input" data-lot-field="short_description" value="' +
					esc(row.short_description || "") +
					'" /></td>' +
					"<td class=\"kt-cl-cfg01-lot-actions\">" +
					'<button type="button" class="kt-cl-cfg01-icon-btn" data-action="remove-lot" data-lot-index="' +
					idx +
					'" aria-label="' +
					__("Remove lot") +
					'">' +
					'<span class="material-symbols-outlined" aria-hidden="true">delete</span></button></td></tr>'
				);
			})
			.join("");
		return (
			'<div class="kt-cl-cfg01-lots" data-testid="kt-cl-cfg01-lots">' +
			'<div class="kt-cl-cfg01-lots-head">' +
			'<h4 class="kt-cl-cfg01-lots-title">' +
			__("Lot Summary") +
			"</h4>" +
			'<button type="button" class="kt-cl-cfg01-btn kt-cl-cfg01-btn--outline kt-cl-cfg01-btn--sm" data-action="add-lot" data-testid="kt-cl-cfg01-add-lot">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Lot") +
			"</button></div>" +
			'<div class="kt-cl-cfg01-lots-table-wrap">' +
			'<table class="kt-cl-cfg01-lots-table" data-testid="kt-cl-cfg01-lots-table">' +
			"<thead><tr>" +
			"<th>" +
			__("Lot No.") +
			"</th><th>" +
			__("Lot Title") +
			"</th><th>" +
			__("Short Description") +
			"</th><th>" +
			__("Actions") +
			"</th></tr></thead><tbody>" +
			rows +
			"</tbody></table></div></div>"
		);
	}

	function blockersHtml(data) {
		var blockers = data.blockers || [];
		if (!blockers.length) {
			return '<div class="kt-cl-cfg01-blockers hidden" data-testid="kt-cl-cfg01-blockers"></div>';
		}
		var items = blockers
			.map(function (b) {
				return "<li>" + esc(b.message || "") + "</li>";
			})
			.join("");
		return (
			'<div class="kt-cl-cfg01-blockers" data-testid="kt-cl-cfg01-blockers" role="status">' +
			"<ul>" +
			items +
			"</ul></div>"
		);
	}

	function profileHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		var lot = lotStructureValue(data);
		var lots = state.lots.length ? state.lots : data.lots || [];
		state.lots = lots.slice();
		var helpers = data.helpers || {};
		return (
			'<div data-testid="kt-cl-cfg01-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			blockersHtml(data) +
			'<div class="kt-cl-cfg01-layout" data-testid="kt-cl-cfg01-layout">' +
			'<div class="kt-cl-cfg01-main" data-testid="kt-cl-cfg01-main">' +
			'<section class="kt-cl-cfg01-card kt-cl-cfg01-card--identity" data-testid="kt-cl-cfg01-section-identity">' +
			'<div class="kt-cl-cfg01-card-accent" aria-hidden="true"></div>' +
			"<h3>" +
			__("1. Tender Identity") +
			"</h3>" +
			'<div class="kt-cl-cfg01-field">' +
			'<label for="kt-cl-cfg01-title">' +
			__("Tender Title") +
			' <span class="kt-cl-cfg01-req">*</span></label>' +
			'<input id="kt-cl-cfg01-title" type="text" class="kt-cl-cfg01-input" data-field="tender_title" data-testid="kt-cl-cfg01-title" value="' +
			esc(data.tender_title || "") +
			'" />' +
			'<p class="kt-cl-cfg01-helper">' +
			esc(helpers.tender_title || helper("tender_title", "Use a clear public-facing title for the tender.")) +
			"</p></div>" +
			'<div class="kt-cl-cfg01-field">' +
			'<label for="kt-cl-cfg01-scope">' +
			__("Short Scope Summary") +
			' <span class="kt-cl-cfg01-req">*</span></label>' +
			'<textarea id="kt-cl-cfg01-scope" class="kt-cl-cfg01-textarea" rows="3" data-field="short_scope_summary" data-testid="kt-cl-cfg01-scope">' +
			esc(data.short_scope_summary || "") +
			"</textarea>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(
				helpers.short_scope_summary ||
					"Summarize what is being procured in one or two sentences."
			) +
			"</p></div>" +
			'<div class="kt-cl-cfg01-readonly-grid">' +
			'<div class="kt-cl-cfg01-field">' +
			"<label>" +
			__("Procuring Entity") +
			"</label>" +
			'<div class="kt-cl-cfg01-readonly" data-testid="kt-cl-cfg01-entity">' +
			esc(data.procuring_entity_name || ctx.procuring_entity_name || "") +
			"</div>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(helpers.procuring_entity || "Taken from the approved procurement package.") +
			"</p></div>" +
			'<div class="kt-cl-cfg01-field">' +
			"<label>" +
			__("Procurement Method") +
			"</label>" +
			'<div class="kt-cl-cfg01-readonly" data-testid="kt-cl-cfg01-method">' +
			esc(data.procurement_method_label || ctx.procurement_method_label || "") +
			"</div>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(helpers.procurement_method || "Taken from the approved procurement package.") +
			"</p></div></div></section>" +
			'<section class="kt-cl-cfg01-card kt-cl-cfg01-card--lots" data-testid="kt-cl-cfg01-section-lots">' +
			'<div class="kt-cl-cfg01-card-accent" aria-hidden="true"></div>' +
			"<h3>" +
			__("2. Lot Structure") +
			"</h3>" +
			'<fieldset class="kt-cl-cfg01-lot-radios" data-testid="kt-cl-cfg01-lot-structure">' +
			'<legend class="sr-only">' +
			__("Select Lot Structure") +
			"</legend>" +
			'<label class="' +
			radioClass(lot, LOT_SINGLE) +
			'">' +
			'<input type="radio" name="kt-cl-cfg01-lot" value="' +
			esc(LOT_SINGLE) +
			'" ' +
			(lot === LOT_SINGLE ? "checked " : "") +
			'data-testid="kt-cl-cfg01-lot-single" />' +
			"<span>" +
			__(LOT_SINGLE) +
			"</span></label>" +
			'<label class="' +
			radioClass(lot, LOT_MULTIPLE) +
			'">' +
			'<input type="radio" name="kt-cl-cfg01-lot" value="' +
			esc(LOT_MULTIPLE) +
			'" ' +
			(lot === LOT_MULTIPLE ? "checked " : "") +
			'data-testid="kt-cl-cfg01-lot-multiple" />' +
			"<span>" +
			__(LOT_MULTIPLE) +
			"</span></label>" +
			'<label class="' +
			radioClass(lot, LOT_NA) +
			'">' +
			'<input type="radio" name="kt-cl-cfg01-lot" value="' +
			esc(LOT_NA) +
			'" ' +
			(lot === LOT_NA ? "checked " : "") +
			'data-testid="kt-cl-cfg01-lot-na" />' +
			"<span>" +
			__(LOT_NA) +
			"</span></label></fieldset>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(helpers.lot_structure || "Confirm whether this tender has one lot or multiple lots.") +
			"</p>" +
			lotsTableHtml(lots, lot === LOT_MULTIPLE) +
			"</section></div>" +
			'<aside class="kt-cl-cfg01-side" data-testid="kt-cl-cfg01-side">' +
			'<section class="kt-cl-cfg01-card kt-cl-cfg01-card--std" data-testid="kt-cl-cfg01-section-std">' +
			'<div class="kt-cl-cfg01-card-accent" aria-hidden="true"></div>' +
			"<h3>" +
			__("3. STD Context") +
			"</h3>" +
			'<div class="kt-cl-cfg01-field">' +
			"<label>" +
			__("STD Family") +
			"</label>" +
			'<div class="kt-cl-cfg01-readonly kt-cl-cfg01-readonly--icon" data-testid="kt-cl-cfg01-std-family">' +
			'<span class="material-symbols-outlined" aria-hidden="true">folder</span>' +
			"<span>" +
			esc(data.std_family || ctx.std_family_label || "") +
			"</span></div>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(helpers.std_family || "The STD family determines which configuration steps and rules apply.") +
			"</p></div>" +
			'<div class="kt-cl-cfg01-field">' +
			"<label>" +
			__("Standard Tender Document") +
			"</label>" +
			'<div class="kt-cl-cfg01-readonly kt-cl-cfg01-readonly--icon" data-testid="kt-cl-cfg01-std-document">' +
			'<span class="material-symbols-outlined" aria-hidden="true">description</span>' +
			"<span>" +
			esc(data.standard_tender_document_label || "") +
			"</span></div>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(
				helpers.standard_tender_document ||
					"The tender will be configured using this standard tender document."
			) +
			"</p></div>" +
			'<div class="kt-cl-cfg01-field">' +
			"<label>" +
			__("STD Version Label") +
			"</label>" +
			'<div class="kt-cl-cfg01-version" data-testid="kt-cl-cfg01-std-version">' +
			esc(data.std_version_label || "") +
			"</div>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(
				helpers.std_version_label ||
					"Shown for traceability; users do not edit the STD master here."
			) +
			"</p></div></section>" +
			'<section class="kt-cl-cfg01-card kt-cl-cfg01-card--notes" data-testid="kt-cl-cfg01-section-notes">' +
			'<div class="kt-cl-cfg01-card-accent" aria-hidden="true"></div>' +
			"<h3>" +
			'<span class="material-symbols-outlined" aria-hidden="true">edit_note</span>' +
			__("Notes") +
			"</h3>" +
			'<label class="sr-only" for="kt-cl-cfg01-note">' +
			__("Configuration Note") +
			"</label>" +
			'<textarea id="kt-cl-cfg01-note" class="kt-cl-cfg01-textarea kt-cl-cfg01-textarea--notes" data-field="configuration_note" data-testid="kt-cl-cfg01-note" placeholder="' +
			esc(__("Add an internal note regarding this configuration...")) +
			'">' +
			esc(data.configuration_note || "") +
			"</textarea>" +
			'<p class="kt-cl-cfg01-helper">' +
			esc(
				helpers.configuration_note ||
					"Add a short internal note for officers working on this configuration. Do not include bidder-facing requirements here."
			) +
			"</p></section></aside></div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg01-footer",
				backTestid: "kt-cl-cfg01-back",
				saveTestid: "kt-cl-cfg01-save",
				continueTestid: "kt-cl-cfg01-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Profile"),
				continueLabel: __("Continue to Tender Data Sheet"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
			}) +
			"</div>"
		);
	}

	function readLotsFromDom($root) {
		var lots = [];
		$root.find("[data-lot-index]").each(function () {
			var $tr = $(this);
			if (!$tr.is("tr")) {
				return;
			}
			lots.push({
				lot_no: String($tr.find('[data-lot-field="lot_no"]').val() || "").trim(),
				lot_title: String($tr.find('[data-lot-field="lot_title"]').val() || "").trim(),
				short_description: String(
					$tr.find('[data-lot-field="short_description"]').val() || ""
				).trim(),
			});
		});
		return lots;
	}

	function collectPayload($root) {
		var lot =
			String($root.find('input[name="kt-cl-cfg01-lot"]:checked').val() || "").trim() || "";
		var lots = lot === LOT_MULTIPLE ? readLotsFromDom($root) : [];
		return {
			tender_title: String($root.find('[data-field="tender_title"]').val() || "").trim(),
			short_scope_summary: String(
				$root.find('[data-field="short_scope_summary"]').val() || ""
			).trim(),
			lot_structure: lot,
			lots: lots,
			configuration_note: String(
				$root.find('[data-field="configuration_note"]').val() || ""
			).trim(),
		};
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		var $save = $root.find('[data-testid="kt-cl-cfg01-save"]');
		$save.prop("disabled", !state.dirty || state.saving);
	}

	function clientCanContinue($root) {
		var p = collectPayload($root);
		var data = state.payload || {};
		if (!p.tender_title || !p.short_scope_summary || !p.lot_structure) {
			return false;
		}
		if (p.lot_structure === LOT_MULTIPLE) {
			var usable = (p.lots || []).some(function (row) {
				return !!(row.lot_title || "").trim();
			});
			if (!usable) {
				return false;
			}
		}
		var family = data.std_family || (data.context && data.context.std_family_label) || "";
		var stdDoc = data.standard_tender_document_label || "";
		return !!(family && stdDoc);
	}

	function refreshContinue($root) {
		var can = clientCanContinue($root);
		$root.find('[data-testid="kt-cl-cfg01-continue"]').prop("disabled", !can || state.saving);
	}

	function syncRadioStyles($root) {
		var val = String($root.find('input[name="kt-cl-cfg01-lot"]:checked').val() || "");
		$root.find(".kt-cl-cfg01-radio").each(function () {
			var $lab = $(this);
			var v = String($lab.find("input").val() || "");
			$lab.toggleClass("kt-cl-cfg01-radio--selected", v === val);
		});
	}

	function rerenderLots($root) {
		var lot = String($root.find('input[name="kt-cl-cfg01-lot"]:checked').val() || "");
		var html = lotsTableHtml(state.lots, lot === LOT_MULTIPLE);
		var $existing = $root.find('[data-testid="kt-cl-cfg01-lots"]');
		if ($existing.length) {
			$existing.replaceWith(html);
		} else {
			$root.find('[data-testid="kt-cl-cfg01-section-lots"]').append(html);
		}
	}

	function remountWithPayload(page, data) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Tender Profile"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		state.lots = (data && data.lots ? data.lots : []).slice();
		state.dirty = false;
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? profileHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
		setDirty($(page.main), false);
		refreshContinue($(page.main));
	}

	function saveProfile($root, page, thenContinue) {
		if (state.saving || !state.configurationId) {
			return;
		}
		var payload = collectPayload($root);
		state.lots = payload.lots;
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		frappe.call({
			method: SAVE_API,
			args: {
				configuration_id: state.configurationId,
				payload: payload,
			},
			callback: function (r) {
				state.saving = false;
				var data = r.message || null;
				if (!data) {
					setDirty($root, true);
					refreshContinue($root);
					return;
				}
				remountWithPayload(page, data);
				if (!thenContinue) {
					frappe.show_alert(
						{
							message: __("Tender Profile saved successfully"),
							indicator: "green",
						},
						5
					);
				}
				if (thenContinue && data.can_continue) {
					frappe.route_options = { configuration_id: state.configurationId };
					frappe.set_route("it-tender-configuration-tds", state.configurationId);
				}
			},
			error: function () {
				state.saving = false;
				setDirty($root, true);
				refreshContinue($root);
			},
		});
	}

	function bind($root, page) {
		$root.off(".cfg01");
		$root.on("input.cfg01 change.cfg01", "[data-field], [data-lot-field]", function () {
			setDirty($root, true);
			refreshContinue($root);
		});
		$root.on("change.cfg01", 'input[name="kt-cl-cfg01-lot"]', function () {
			var lot = String($(this).val() || "");
			if (lot === LOT_MULTIPLE && !state.lots.length) {
				state.lots = [
					{ lot_no: "Lot 1", lot_title: "", short_description: "" },
				];
			}
			if (lot !== LOT_MULTIPLE) {
				state.lots = [];
			}
			syncRadioStyles($root);
			rerenderLots($root);
			setDirty($root, true);
			refreshContinue($root);
		});
		$root.on("click.cfg01", "[data-action='add-lot']", function (e) {
			e.preventDefault();
			state.lots = readLotsFromDom($root);
			state.lots.push({
				lot_no: "Lot " + (state.lots.length + 1),
				lot_title: "",
				short_description: "",
			});
			rerenderLots($root);
			setDirty($root, true);
			refreshContinue($root);
		});
		$root.on("click.cfg01", "[data-action='remove-lot']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-lot-index"), 10);
			state.lots = readLotsFromDom($root);
			if (!isNaN(idx)) {
				state.lots.splice(idx, 1);
			}
			rerenderLots($root);
			setDirty($root, true);
			refreshContinue($root);
		});
		$root.on("click.cfg01", "[data-action='back-home']", function (e) {
			e.preventDefault();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route("it-tender-configuration-overview", state.configurationId);
		});
		$root.on("click.cfg01", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveProfile($root, page, false);
		});
		$root.on("click.cfg01", "[data-action='continue']", function (e) {
			e.preventDefault();
			if (state.dirty) {
				saveProfile($root, page, true);
				return;
			}
			if (state.payload && state.payload.can_continue && state.configurationId) {
				frappe.route_options = { configuration_id: state.configurationId };
				frappe.set_route("it-tender-configuration-tds", state.configurationId);
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
			title: __("Tender Profile"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}

		var id = configurationId();
		state.configurationId = id;
		if (!id) {
			sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
			bind($(page.main), page);
			return;
		}

		var route = frappe.get_route() || [];
		if (!(route[0] === PAGE_SLUG && route[1] === id)) {
			state.mounting = true;
			frappe.set_route(PAGE_SLUG, id);
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
			method: GET_API,
			args: { configuration_id: id },
			callback: function (r) {
				remountWithPayload(page, r.message || null);
			},
			error: function () {
				sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: emptyHtml() });
				bind($(page.main), page);
			},
		});
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Tender Profile"),
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
