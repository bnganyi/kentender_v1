// CFG-03 — IT Requirements (C2-CFG3).
// Route contract: /desk/it-tender-configuration-it-requirements/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-03";
	var PAGE_SLUG = "it-tender-configuration-it-requirements";
	var GET_API =
		"kentender_procurement.tender_configurations.get_tender_configuration_requirements";
	var SAVE_API =
		"kentender_procurement.tender_configurations.save_tender_configuration_requirements";
	var STORAGE_KEY = "kt_cl_cfg03_configuration_id";
	var SUBTITLE =
		"Define what bidders must supply, deliver, integrate, support, or prove.";
	var DRAWER_HOST_ID = "kt-cl-cfg03-drawer-host";

	var state = {
		payload: null,
		configurationId: null,
		page: null,
		mounting: false,
		dirty: false,
		saving: false,
		requirements: [],
		editingIndex: -1,
		drawerOpen: false,
		showIssuesPanel: false,
		issuesExpanded: false,
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

	function emptyHtml() {
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg03-root">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg03-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusChip(label) {
		var key = String(label || "Not started")
			.toLowerCase()
			.replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg03-status kt-cl-cfg03-status--' +
			esc(key) +
			'">' +
			esc(label || "Not started") +
			"</span>"
		);
	}

	function issuesHtml(data) {
		var blockers = data.blockers || [];
		var warnings = data.warnings || [];
		var hasProgress = !!(data && data.has_progress);
		var showPanel = blockers.length > 0 && (hasProgress || state.showIssuesPanel);
		if (!blockers.length || !showPanel) {
			return (
				'<div class="kt-cl-cfg03-issues hidden" data-testid="kt-cl-cfg03-blockers" aria-hidden="true"></div>'
			);
		}
		var n = blockers.length;
		var warnN = warnings.length;
		var summary =
			n === 1
				? __("1 item needs attention")
				: __("{0} items need attention", [n]);
		if (warnN > 0) {
			summary +=
				" · " +
				(warnN === 1 ? __("1 warning") : __("{0} warnings", [warnN]));
		}
		var items = blockers
			.map(function (b) {
				return "<li>" + esc(b.message || "") + "</li>";
			})
			.join("");
		var expanded = !!state.issuesExpanded;
		return (
			'<div class="kt-cl-cfg03-issues' +
			(expanded ? " kt-cl-cfg03-issues--open" : "") +
			'" data-testid="kt-cl-cfg03-blockers" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg03-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg03-issues-toggle" aria-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<span class="kt-cl-cfg03-issues-toggle-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">error</span>' +
			'<span data-testid="kt-cl-cfg03-issues-summary">' +
			esc(summary) +
			"</span>" +
			'<span class="kt-cl-cfg03-issues-hint">' +
			esc(__("Review details")) +
			"</span></span>" +
			'<span class="material-symbols-outlined kt-cl-cfg03-issues-chevron" aria-hidden="true">' +
			(expanded ? "expand_less" : "expand_more") +
			"</span></button>" +
			'<div class="kt-cl-cfg03-issues-body' +
			(expanded ? "" : " hidden") +
			'" data-testid="kt-cl-cfg03-issues-list"' +
			(expanded ? "" : " hidden") +
			"><ul>" +
			items +
			"</ul></div></div>"
		);
	}

	function tableHtml(requirements) {
		var comp = c();
		var cols = [
			{ label: __("ID") },
			{ label: __("Requirement") },
			{ label: __("Category") },
			{ label: __("Treatment") },
			{ label: __("Bidder Response Instruction") },
			{ label: __("Evidence Instruction") },
			{ label: __("Delivery Confirmation Method") },
			{ label: __("Setup Status") },
			{ label: __("Action") },
		];
		var rows = (requirements || []).map(function (row, idx) {
			var action = row.action_label || "Edit";
			var setup = row.setup_status_label || row.status_label || "Draft";
			return {
				id: row.requirement_id || String(idx),
				cells: [
					{ text: row.requirement_id || "", cls: "kt-cl-cfg03-cell-mono" },
					{ text: row.title || "—" },
					{ text: row.category_label || "—" },
					{ text: row.treatment_label || "—" },
					{
						text:
							row.bidder_response_instruction_display ||
							row.bidder_response_instruction ||
							"—",
					},
					{
						text:
							row.evidence_instruction_display || row.evidence_instruction || "—",
					},
					{
						text:
							row.delivery_confirmation_method_display ||
							row.delivery_confirmation_method ||
							"—",
					},
					{ html: statusChip(setup) },
					{
						html:
							'<button type="button" class="kt-cl-cfg03-row-action" data-action="edit-requirement" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg03-row-action-' +
							esc(row.requirement_id || String(idx)) +
							'">' +
							esc(action) +
							"</button>",
					},
				],
			};
		});
		var table = comp.queueTable({
			columns: cols,
			rows: rows,
			footerText: __("Total Requirements: {0}", [rows.length]),
			showPageSize: false,
			pagination: null,
		});
		return (
			'<section class="kt-cl-cfg03-table-card" data-testid="kt-cl-cfg03-table-card">' +
			'<div class="kt-cl-cfg03-table-head">' +
			"<h3>" +
			__("Requirements Specification") +
			"</h3>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="add-requirement" data-testid="kt-cl-cfg03-add">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Requirement") +
			"</button></div>" +
			'<div data-testid="kt-cl-cfg03-table">' +
			table +
			"</div></section>"
		);
	}

	function guidanceHtml(data) {
		var g = (data && data.guidance) || {};
		return (
			'<aside class="kt-cl-cfg03-side" data-testid="kt-cl-cfg03-side">' +
			'<section class="kt-cl-cfg03-guidance" data-testid="kt-cl-cfg03-guidance">' +
			'<div class="kt-cl-cfg03-guidance-head">' +
			'<span class="material-symbols-outlined" aria-hidden="true">lightbulb</span>' +
			"<h3>" +
			esc(g.title || __("IT Requirements Guidance")) +
			"</h3></div>" +
			'<p class="kt-cl-cfg03-guidance-body">' +
			esc(g.body || "") +
			"</p>" +
			'<dl class="kt-cl-cfg03-guidance-list">' +
			"<div><dt>" +
			__("What this affects") +
			"</dt><dd>" +
			esc(g.what_this_affects || "") +
			"</dd></div>" +
			"<div><dt>" +
			__("Used later by") +
			"</dt><dd>" +
			esc(g.used_later_by || "") +
			"</dd></div>" +
			"<div><dt>" +
			__("Not configured here") +
			"</dt><dd>" +
			esc(g.not_configured_here || "") +
			"</dd></div></dl></section></aside>"
		);
	}

	function pageHtml(data) {
		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-cfg03-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			issuesHtml(data) +
			'<div class="kt-cl-cfg03-layout" data-testid="kt-cl-cfg03-layout">' +
			'<div class="kt-cl-cfg03-main" data-testid="kt-cl-cfg03-main">' +
			tableHtml(state.requirements) +
			"</div>" +
			guidanceHtml(data) +
			"</div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg03-footer",
				backTestid: "kt-cl-cfg03-back",
				saveTestid: "kt-cl-cfg03-save",
				continueTestid: "kt-cl-cfg03-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Requirements"),
				continueLabel: __("Continue to Implementation Schedule"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg03-run-check",
						variant: "outline",
					},
				],
			}) +
			"</div>"
		);
	}

	function optionsFor(key) {
		var opts = (state.payload && state.payload.options && state.payload.options[key]) || [];
		return opts;
	}

	function selectOpts(options, selected) {
		return (
			'<option value="">' +
			esc(__("Select…")) +
			"</option>" +
			(options || [])
				.map(function (o) {
					return (
						'<option value="' +
						esc(o) +
						'"' +
						(selected === o ? " selected" : "") +
						">" +
						esc(o) +
						"</option>"
					);
				})
				.join("")
		);
	}

	function fieldWrap(label, controlHtml, required) {
		return (
			'<div class="kt-cl-cfg03-field">' +
			"<label>" +
			esc(label) +
			(required ? ' <span class="kt-cl-cfg03-req">*</span>' : "") +
			"</label>" +
			controlHtml +
			"</div>"
		);
	}

	function drawerHtml(row, isNew) {
		row = row || {};
		var refs = row.references || {
			evaluation_setup: "Not linked to evaluation",
			forms_and_evidence: "No evidence item required",
			contract_values: "No contract carry-forward expected",
		};
		return (
			'<div class="kt-cl-cfg03-drawer-overlay" data-testid="kt-cl-cfg03-drawer-overlay" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-cfg03-drawer" data-testid="kt-cl-cfg03-drawer">' +
			'<header class="kt-cl-cfg03-drawer-header">' +
			"<h2 data-testid=\"kt-cl-cfg03-drawer-title\">" +
			esc(isNew ? __("Add Requirement") : __("Edit Requirement")) +
			"</h2>" +
			'<button type="button" class="kt-cl-cfg03-drawer-close" data-action="close-drawer" data-testid="kt-cl-cfg03-drawer-close" aria-label="' +
			__("Close") +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></header>' +
			'<div class="kt-cl-cfg03-drawer-body" data-testid="kt-cl-cfg03-drawer-body">' +
			'<section><h3>' +
			__("Requirement") +
			"</h3>" +
			// Labels align with table columns: ID + Requirement (title is not the ID)
			fieldWrap(
				__("ID"),
				'<p class="kt-cl-cfg03-readonly" data-testid="kt-cl-cfg03-drawer-id">' +
					esc(
						row.requirement_id
							? row.requirement_id
							: __("Assigned on save")
					) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Requirement"),
				'<input type="text" class="kt-cl-cfg03-input" data-drawer-field="title" data-testid="kt-cl-cfg03-drawer-title-input" placeholder="' +
					esc(__("e.g. Compute Node Performance")) +
					'" value="' +
					esc(row.title || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Description"),
				'<textarea class="kt-cl-cfg03-textarea" rows="3" data-drawer-field="description" data-testid="kt-cl-cfg03-drawer-description" placeholder="' +
					esc(__("Optional detail for bidders and reviewers")) +
					'">' +
					esc(row.description || "") +
					"</textarea>",
				false
			) +
			fieldWrap(
				__("Category"),
				'<select class="kt-cl-cfg03-select" data-drawer-field="category_label" data-testid="kt-cl-cfg03-drawer-category">' +
					selectOpts(optionsFor("category_label"), row.category_label || "") +
					"</select>",
				true
			) +
			fieldWrap(
				__("Treatment"),
				'<select class="kt-cl-cfg03-select" data-drawer-field="treatment_label" data-testid="kt-cl-cfg03-drawer-treatment">' +
					selectOpts(optionsFor("treatment_label"), row.treatment_label || "") +
					"</select>",
				true
			) +
			"</section>" +
			"<section><h3>" +
			__("Bidder Response") +
			"</h3>" +
			fieldWrap(
				__("Bidder Response Format"),
				'<select class="kt-cl-cfg03-select" data-drawer-field="bidder_response_format" data-testid="kt-cl-cfg03-drawer-response-format">' +
					selectOpts(
						optionsFor("bidder_response_format"),
						row.bidder_response_format || ""
					) +
					"</select>",
				true
			) +
			fieldWrap(
				__("Bidder Response Instruction"),
				'<textarea class="kt-cl-cfg03-textarea" rows="2" data-drawer-field="bidder_response_instruction" data-testid="kt-cl-cfg03-drawer-response-instruction">' +
					esc(row.bidder_response_instruction || "") +
					"</textarea>",
				false
			) +
			"</section>" +
			"<section><h3>" +
			__("Evidence") +
			"</h3>" +
			fieldWrap(
				__("Evidence Requirement"),
				'<select class="kt-cl-cfg03-select" data-drawer-field="evidence_requirement" data-testid="kt-cl-cfg03-drawer-evidence-requirement">' +
					selectOpts(
						optionsFor("evidence_requirement"),
						row.evidence_requirement || ""
					) +
					"</select>",
				true
			) +
			fieldWrap(
				__("Evidence Instruction"),
				'<textarea class="kt-cl-cfg03-textarea" rows="2" data-drawer-field="evidence_instruction" data-testid="kt-cl-cfg03-drawer-evidence-instruction">' +
					esc(row.evidence_instruction || "") +
					"</textarea>",
				false
			) +
			"</section>" +
			"<section><h3>" +
			__("Delivery Confirmation") +
			"</h3>" +
			fieldWrap(
				__("Delivery Confirmation Method"),
				'<input type="text" class="kt-cl-cfg03-input" list="kt-cl-cfg03-delivery-methods" data-drawer-field="delivery_confirmation_method" data-testid="kt-cl-cfg03-drawer-delivery-method" placeholder="' +
					esc(__("e.g. Inspection at delivery")) +
					'" value="' +
					esc(row.delivery_confirmation_method || "") +
					'" />' +
					'<datalist id="kt-cl-cfg03-delivery-methods">' +
					(optionsFor("delivery_confirmation_method") || [])
						.map(function (o) {
							return '<option value="' + esc(o) + '"></option>';
						})
						.join("") +
					"</datalist>" +
					'<p class="kt-cl-cfg03-field-hint">' +
					esc(
						__(
							"How delivery will later be confirmed — a method, not a setup status."
						)
					) +
					"</p>",
				true
			) +
			"</section>" +
			'<section data-testid="kt-cl-cfg03-drawer-references"><h3>' +
			__("References") +
			"</h3>" +
			"<dl class=\"kt-cl-cfg03-refs\">" +
			"<div><dt>" +
			__("Evaluation Setup") +
			"</dt><dd>" +
			esc(refs.evaluation_setup || "") +
			"</dd></div>" +
			"<div><dt>" +
			__("Forms & Evidence") +
			"</dt><dd>" +
			esc(refs.forms_and_evidence || "") +
			"</dd></div>" +
			"<div><dt>" +
			__("Contract Values") +
			"</dt><dd>" +
			esc(refs.contract_values || "") +
			"</dd></div></dl></section></div>" +
			'<footer class="kt-cl-cfg03-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-drawer" data-testid="kt-cl-cfg03-drawer-cancel">' +
			__("Cancel") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-requirement" data-testid="kt-cl-cfg03-drawer-save">' +
			__("Save Requirement") +
			"</button></footer></aside></div>"
		);
	}

	function ensureDrawerHost() {
		var host = document.getElementById(DRAWER_HOST_ID);
		if (!host) {
			host = document.createElement("div");
			host.id = DRAWER_HOST_ID;
			document.body.appendChild(host);
		}
		return $(host);
	}

	function closeDrawer() {
		state.drawerOpen = false;
		state.editingIndex = -1;
		var $host = ensureDrawerHost();
		$host.empty().off(".cfg03drawer");
	}

	function openDrawer(index) {
		state.drawerOpen = true;
		state.editingIndex = typeof index === "number" ? index : -1;
		var isNew = state.editingIndex < 0;
		var row = isNew ? {} : state.requirements[state.editingIndex] || {};
		var $host = ensureDrawerHost();
		$host.html(drawerHtml(row, isNew));
		$host.off(".cfg03drawer");
		$host.on("click.cfg03drawer", "[data-action='close-drawer']", function (e) {
			e.preventDefault();
			closeDrawer();
		});
		$host.on("click.cfg03drawer", "[data-testid='kt-cl-cfg03-drawer-overlay']", function (e) {
			if (e.target === this) {
				closeDrawer();
			}
		});
		$host.on("click.cfg03drawer", "[data-action='save-requirement']", function (e) {
			e.preventDefault();
			saveDrawerRequirement($host);
		});
	}

	function collectDrawer($host) {
		var row = {};
		$host.find("[data-drawer-field]").each(function () {
			var key = String($(this).attr("data-drawer-field") || "");
			row[key] = String($(this).val() || "").trim();
		});
		if (state.editingIndex >= 0 && state.requirements[state.editingIndex]) {
			row.requirement_id = state.requirements[state.editingIndex].requirement_id || "";
		}
		return row;
	}

	function persistableRequirements() {
		return (state.requirements || []).map(function (r) {
			return {
				requirement_id: r.requirement_id || "",
				title: r.title || "",
				description: r.description || "",
				category_label: r.category_label || "",
				treatment_label: r.treatment_label || "",
				bidder_response_format: r.bidder_response_format || "",
				bidder_response_instruction: r.bidder_response_instruction || "",
				evidence_requirement: r.evidence_requirement || "",
				evidence_instruction: r.evidence_instruction || "",
				delivery_confirmation_method: r.delivery_confirmation_method || "",
			};
		});
	}

	function saveDrawerRequirement($host) {
		var row = collectDrawer($host);
		if (state.editingIndex >= 0) {
			state.requirements[state.editingIndex] = Object.assign(
				{},
				state.requirements[state.editingIndex],
				row
			);
		} else {
			state.requirements.push(row);
		}
		state.dirty = true;
		closeDrawer();
		// Persist immediately so Setup Status / issues / Continue refresh
		// without a second footer "Save Requirements" click.
		if (state.page) {
			saveRequirements($(state.page.main), state.page, { fromDrawer: true });
		}
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg03-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function refreshContinue($root, canContinue) {
		var can =
			typeof canContinue === "boolean"
				? canContinue
				: !!(state.payload && state.payload.can_continue);
		$root.find('[data-testid="kt-cl-cfg03-continue"]').prop("disabled", !can || state.saving);
	}

	function remountWithPayload(page, data, opts) {
		opts = opts || {};
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("IT Requirements"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		if (!opts.keepClientList) {
			state.requirements = (data && data.requirements ? data.requirements : []).slice();
			state.dirty = false;
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? pageHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
		setDirty($(page.main), state.dirty);
		refreshContinue($(page.main), !!(data && data.can_continue) && !state.dirty);
		// If dirty after drawer edit, continue stays disabled until save
		if (state.dirty) {
			refreshContinue($(page.main), false);
		}
	}

	function saveRequirements($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		frappe.call({
			method: SAVE_API,
			args: {
				configuration_id: state.configurationId,
				payload: { requirements: persistableRequirements() },
			},
			callback: function (r) {
				state.saving = false;
				var data = r.message || null;
				if (!data) {
					remountWithPayload(page, state.payload || {}, { keepClientList: true });
					setDirty($(page.main), true);
					refreshContinue($(page.main), false);
					return;
				}
				var blockerCount = data.blocker_count || 0;
				if (opts.runCheck) {
					state.showIssuesPanel = blockerCount > 0;
					state.issuesExpanded = false;
				} else if (blockerCount > 0 && data.has_progress) {
					// Drawer or footer save: keep issues in sync with server validation
					state.showIssuesPanel = true;
				} else {
					state.showIssuesPanel = false;
					state.issuesExpanded = false;
				}
				remountWithPayload(page, data);
				if (opts.runCheck) {
					var warnings = data.warning_count || 0;
					frappe.show_alert(
						{
							message:
								blockerCount === 0
									? __("Check complete: no blockers ({0} warnings).", [warnings])
									: __(
											"Check complete: {0} blocker(s), {1} warning(s).",
											[blockerCount, warnings]
									  ),
							indicator: blockerCount === 0 ? "green" : "orange",
						},
						6
					);
				} else if (!opts.thenContinue) {
					frappe.show_alert(
						{
							message: __("IT Requirements saved successfully"),
							indicator: "green",
						},
						5
					);
				}
				if (opts.thenContinue && data.can_continue) {
					frappe.route_options = { configuration_id: state.configurationId };
					frappe.set_route(
						"it-tender-configuration-implementation-schedule",
						state.configurationId
					);
				}
			},
			error: function () {
				state.saving = false;
				// Keep drawer edits in the table so the user does not lose work
				remountWithPayload(page, state.payload || {}, { keepClientList: true });
				setDirty($(page.main), true);
				refreshContinue($(page.main), false);
			},
		});
	}

	function bind($root, page) {
		$root.off(".cfg03");
		$root.on("click.cfg03", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg03-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg03-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg03-issues-toggle"]');
			var $chev = $panel.find(".kt-cl-cfg03-issues-chevron");
			$panel.toggleClass("kt-cl-cfg03-issues--open", state.issuesExpanded);
			$panel.attr("data-expanded", state.issuesExpanded ? "true" : "false");
			$btn.attr("aria-expanded", state.issuesExpanded ? "true" : "false");
			$list.toggleClass("hidden", !state.issuesExpanded);
			if (state.issuesExpanded) {
				$list.removeAttr("hidden");
			} else {
				$list.attr("hidden", "hidden");
			}
			$chev.text(state.issuesExpanded ? "expand_less" : "expand_more");
		});
		$root.on("click.cfg03", "[data-action='add-requirement']", function (e) {
			e.preventDefault();
			openDrawer(-1);
		});
		$root.on("click.cfg03", "[data-action='edit-requirement']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (!isNaN(idx)) {
				openDrawer(idx);
			}
		});
		$root.on("click.cfg03", "[data-action='back-home']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route("it-tender-configuration-overview", state.configurationId);
		});
		$root.on("click.cfg03", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveRequirements($root, page, {});
		});
		$root.on("click.cfg03", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveRequirements($root, page, { runCheck: true });
		});
		$root.on("click.cfg03", "[data-action='continue']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (state.dirty) {
				saveRequirements($root, page, { thenContinue: true });
				return;
			}
			if (state.payload && state.payload.can_continue && state.configurationId) {
				frappe.route_options = { configuration_id: state.configurationId };
				frappe.set_route(
					"it-tender-configuration-implementation-schedule",
					state.configurationId
				);
			}
		});
	}

	function mount(page) {
		if (state.mounting) {
			return;
		}
		state.page = page;
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		var pageHeader = {
			title: __("IT Requirements"),
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
			title: __("IT Requirements"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			frappe.pages[PAGE_SLUG].page = wrapper.page;
			mount(wrapper.page);
		}
	};
})();
