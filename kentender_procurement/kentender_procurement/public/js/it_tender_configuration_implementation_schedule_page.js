// CFG-04 — Implementation Schedule (C2-CFG4 + column-clarity).
// Route: /desk/it-tender-configuration-implementation-schedule/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-04";
	var PAGE_SLUG = "it-tender-configuration-implementation-schedule";
	var GET_API =
		"kentender_procurement.tender_configurations.get_tender_configuration_implementation_schedule";
	var SAVE_API =
		"kentender_procurement.tender_configurations.save_tender_configuration_implementation_schedule";
	var STORAGE_KEY = "kt_cl_cfg04_configuration_id";
	var SUBTITLE =
		"Define the delivery approach, milestones, deliverables, timing, and acceptance checkpoints for this IT tender.";
	var DRAWER_HOST_ID = "kt-cl-cfg04-drawer-host";
	var APPROACH_PHASED = "Phased Delivery";
	var APPROACH_SINGLE = "Single Turnkey Delivery";

	var state = {
		payload: null,
		configurationId: null,
		page: null,
		mounting: false,
		dirty: false,
		saving: false,
		deliveryApproach: APPROACH_PHASED,
		milestones: [],
		singleDelivery: {},
		editingIndex: -1,
		drawerOpen: false,
		drawerRelatedIds: [],
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
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg04-root">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg04-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusChip(label) {
		var key = String(label || "Draft")
			.toLowerCase()
			.replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg04-status kt-cl-cfg04-status--' +
			esc(key) +
			'">' +
			esc(label || "Draft") +
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
				'<div class="kt-cl-cfg04-issues hidden" data-testid="kt-cl-cfg04-blockers" aria-hidden="true"></div>'
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
			'<div class="kt-cl-cfg04-issues' +
			(expanded ? " kt-cl-cfg04-issues--open" : "") +
			'" data-testid="kt-cl-cfg04-blockers" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg04-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg04-issues-toggle" aria-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<span class="kt-cl-cfg04-issues-toggle-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">error</span>' +
			esc(summary) +
			"</span>" +
			'<span class="kt-cl-cfg04-issues-hint">' +
			esc(__("Review details")) +
			'</span><span class="material-symbols-outlined kt-cl-cfg04-issues-chevron" aria-hidden="true">' +
			(expanded ? "expand_less" : "expand_more") +
			"</span></button>" +
			'<div class="kt-cl-cfg04-issues-body' +
			(expanded ? "" : " hidden") +
			'" data-testid="kt-cl-cfg04-issues-list"' +
			(expanded ? "" : ' hidden="hidden"') +
			"><ul>" +
			items +
			"</ul></div></div>"
		);
	}

	function approachHtml() {
		var phased = state.deliveryApproach === APPROACH_PHASED;
		return (
			'<section class="kt-cl-cfg04-approach" data-testid="kt-cl-cfg04-approach">' +
			"<h3>" +
			__("Delivery Approach") +
			"</h3>" +
			'<div class="kt-cl-cfg04-approach-options">' +
			'<label class="kt-cl-cfg04-approach-option' +
			(phased ? " is-active" : "") +
			'">' +
			'<input type="radio" name="kt-cl-cfg04-approach" value="' +
			esc(APPROACH_PHASED) +
			'" data-testid="kt-cl-cfg04-approach-phased"' +
			(phased ? " checked" : "") +
			" />" +
			"<span><strong>" +
			esc(APPROACH_PHASED) +
			"</strong><small>" +
			esc(__("Multiple milestones or phases after award.")) +
			"</small></span></label>" +
			'<label class="kt-cl-cfg04-approach-option' +
			(!phased ? " is-active" : "") +
			'">' +
			'<input type="radio" name="kt-cl-cfg04-approach" value="' +
			esc(APPROACH_SINGLE) +
			'" data-testid="kt-cl-cfg04-approach-single"' +
			(!phased ? " checked" : "") +
			" />" +
			"<span><strong>" +
			esc(APPROACH_SINGLE) +
			"</strong><small>" +
			esc(__("One complete package delivered as a turnkey milestone.")) +
			"</small></span></label></div></section>"
		);
	}

	function tableHtml(milestones) {
		var comp = c();
		var cols = [
			{ label: __("ID") },
			{ label: __("Milestone") },
			{ label: __("Expected Duration") },
			{ label: __("Trigger") },
			{ label: __("Key Deliverable") },
			{ label: __("Acceptance Method") },
			{ label: __("Setup Status") },
			{ label: __("Action") },
		];
		var rows = (milestones || []).map(function (row, idx) {
			var action = row.action_label || "Edit";
			var setup = row.setup_status_label || row.status_label || "Draft";
			return {
				id: row.milestone_id || String(idx),
				cells: [
					{ text: row.milestone_id || "", cls: "kt-cl-cfg04-cell-mono" },
					{ text: row.name || "—" },
					{ text: row.expected_duration || "—" },
					{ text: row.start_trigger || "—" },
					{ text: row.key_deliverable || "—" },
					{
						text:
							row.acceptance_method_display || row.acceptance_method || "—",
					},
					{ html: statusChip(setup) },
					{
						html:
							'<div class="kt-cl-cfg04-row-actions">' +
							'<button type="button" class="kt-cl-cfg04-row-action" data-action="edit-milestone" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg04-row-action-' +
							esc(row.milestone_id || String(idx)) +
							'">' +
							esc(action) +
							"</button>" +
							'<button type="button" class="kt-cl-cfg04-row-delete" data-action="delete-milestone" data-index="' +
							idx +
							'" data-testid="kt-cl-cfg04-row-delete-' +
							esc(row.milestone_id || String(idx)) +
							'" title="' +
							esc(__("Remove")) +
							'" aria-label="' +
							esc(__("Remove")) +
							'"><span class="material-symbols-outlined" aria-hidden="true">delete</span></button></div>',
					},
				],
			};
		});
		var table = comp.queueTable({
			columns: cols,
			rows: rows,
			footerText: __("Total Milestones: {0}", [rows.length]),
			showPageSize: false,
			pagination: null,
		});
		return (
			'<section class="kt-cl-cfg04-table-card" data-testid="kt-cl-cfg04-table-card">' +
			'<div class="kt-cl-cfg04-table-head">' +
			"<h3>" +
			__("Delivery Milestones") +
			"</h3>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="add-milestone" data-testid="kt-cl-cfg04-add">' +
			'<span class="material-symbols-outlined" aria-hidden="true">add</span>' +
			__("Add Milestone") +
			"</button></div>" +
			'<div data-testid="kt-cl-cfg04-table">' +
			table +
			"</div></section>"
		);
	}

	function durationUnitOptions(selected, preferred) {
		var units =
			(state.payload && state.payload.options && state.payload.options.duration_unit) ||
			["days", "weeks", "months"];
		var sel = String(selected || preferred || "weeks").toLowerCase();
		return units
			.map(function (u) {
				var v = String(u || "").toLowerCase();
				return (
					'<option value="' +
					esc(v) +
					'"' +
					(v === sel ? " selected" : "") +
					">" +
					esc(v) +
					"</option>"
				);
			})
			.join("");
	}

	function durationControlsHtml(prefix, value, unit, preferredUnit) {
		return (
			'<div class="kt-cl-cfg04-duration-row">' +
			'<input type="number" min="0" step="1" class="kt-cl-cfg04-input" data-' +
			prefix +
			'-field="expected_duration_value" data-testid="kt-cl-cfg04-' +
			prefix +
			'-duration" value="' +
			esc(value || "") +
			'" placeholder="e.g. 4" />' +
			'<select class="kt-cl-cfg04-select" data-' +
			prefix +
			'-field="expected_duration_unit" data-testid="kt-cl-cfg04-' +
			prefix +
			'-duration-unit">' +
			durationUnitOptions(unit, preferredUnit) +
			"</select></div>"
		);
	}

	function singleFormHtml(row) {
		row = row || {};
		return (
			'<section class="kt-cl-cfg04-single-form" data-testid="kt-cl-cfg04-single-form">' +
			"<h3>" +
			__("Single Delivery Milestone") +
			"</h3>" +
			fieldWrap(
				__("Expected Delivery Duration"),
				durationControlsHtml(
					"single",
					row.expected_duration_value,
					row.expected_duration_unit,
					"months"
				),
				true
			) +
			fieldWrap(
				__("Delivery Trigger"),
				'<input type="text" class="kt-cl-cfg04-input" data-single-field="delivery_trigger" data-testid="kt-cl-cfg04-single-trigger" value="' +
					esc(row.delivery_trigger || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Key Deliverables"),
				'<textarea class="kt-cl-cfg04-textarea" rows="3" data-single-field="key_deliverables" data-testid="kt-cl-cfg04-single-deliverables">' +
					esc(row.key_deliverables || "") +
					"</textarea>",
				true
			) +
			fieldWrap(
				__("Acceptance Method"),
				'<input type="text" class="kt-cl-cfg04-input" list="kt-cl-cfg04-acceptance-methods" data-single-field="acceptance_method" data-testid="kt-cl-cfg04-single-acceptance" value="' +
					esc(row.acceptance_method || "") +
					'" />' +
					acceptanceDatalist(),
				true
			) +
			fieldWrap(
				__("Evidence Expected"),
				'<textarea class="kt-cl-cfg04-textarea" rows="2" data-single-field="evidence_expected" data-testid="kt-cl-cfg04-single-evidence">' +
					esc(row.evidence_expected || "") +
					"</textarea>",
				false
			) +
			fieldWrap(
				__("Notes to Bidders"),
				'<textarea class="kt-cl-cfg04-textarea" rows="2" data-single-field="notes_to_bidders" data-testid="kt-cl-cfg04-single-notes">' +
					esc(row.notes_to_bidders || "") +
					"</textarea>",
				false
			) +
			"</section>"
		);
	}

	function guidanceHtml(data) {
		var g = (data && data.guidance) || {};
		return (
			'<aside class="kt-cl-cfg04-side" data-testid="kt-cl-cfg04-side">' +
			'<section class="kt-cl-cfg04-guidance" data-testid="kt-cl-cfg04-guidance">' +
			'<div class="kt-cl-cfg04-guidance-head">' +
			'<span class="material-symbols-outlined" aria-hidden="true">lightbulb</span>' +
			"<h3>" +
			esc(g.title || __("Implementation Schedule Guidance")) +
			"</h3></div>" +
			'<p class="kt-cl-cfg04-guidance-body">' +
			esc(g.body || "") +
			"</p>" +
			'<dl class="kt-cl-cfg04-guidance-list">' +
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
		var mainBody =
			state.deliveryApproach === APPROACH_SINGLE
				? singleFormHtml(state.singleDelivery)
				: tableHtml(state.milestones);
		return (
			'<div data-testid="kt-cl-cfg04-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			issuesHtml(data) +
			approachHtml() +
			'<div class="kt-cl-cfg04-layout" data-testid="kt-cl-cfg04-layout">' +
			'<div class="kt-cl-cfg04-main" data-testid="kt-cl-cfg04-main">' +
			mainBody +
			"</div>" +
			guidanceHtml(data) +
			"</div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg04-footer",
				backTestid: "kt-cl-cfg04-back",
				saveTestid: "kt-cl-cfg04-save",
				continueTestid: "kt-cl-cfg04-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Schedule"),
				continueLabel: __("Continue to System Inventory & Bidder Background"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg04-run-check",
						variant: "secondary",
					},
				],
			}) +
			"</div>"
		);
	}

	function fieldWrap(label, controlHtml, required) {
		return (
			'<div class="kt-cl-cfg04-field">' +
			"<label>" +
			esc(label) +
			(required ? ' <span class="kt-cl-cfg04-req">*</span>' : "") +
			"</label>" +
			controlHtml +
			"</div>"
		);
	}

	function acceptanceDatalist() {
		var opts =
			(state.payload && state.payload.options && state.payload.options.acceptance_method) ||
			[];
		return (
			'<datalist id="kt-cl-cfg04-acceptance-methods">' +
			opts
				.map(function (o) {
					return '<option value="' + esc(o) + '"></option>';
				})
				.join("") +
			"</datalist>"
		);
	}

	function startTriggerDatalist() {
		var opts =
			(state.payload && state.payload.options && state.payload.options.start_trigger) || [];
		return (
			'<datalist id="kt-cl-cfg04-start-triggers">' +
			opts
				.map(function (o) {
					return '<option value="' + esc(o) + '"></option>';
				})
				.join("") +
			"</datalist>"
		);
	}

	function nextMilestoneId() {
		var maxN = 0;
		(state.milestones || []).forEach(function (r) {
			var m = String((r && r.milestone_id) || "").match(/^MS-(\d+)$/i);
			if (m) {
				maxN = Math.max(maxN, parseInt(m[1], 10));
			}
		});
		var padded = String(maxN + 1);
		while (padded.length < 3) {
			padded = "0" + padded;
		}
		return "MS-" + padded;
	}

	function availableRequirements() {
		return (state.payload && state.payload.available_requirements) || [];
	}

	function requirementById(id) {
		var rid = String(id || "");
		var found = null;
		availableRequirements().forEach(function (r) {
			if (String(r.id || "") === rid) {
				found = r;
			}
		});
		return found;
	}

	function relatedChipsHtml(selectedIds) {
		var chips = (selectedIds || [])
			.map(function (id) {
				var ref = requirementById(id) || { id: id, code: id, name: id };
				var label = ref.code || ref.id;
				var title =
					ref.name && ref.code
						? ref.name + " (" + ref.code + ")"
						: ref.name || ref.code || id;
				return (
					'<span class="kt-cl-cfg04-chip" data-related-id="' +
					esc(ref.id || id) +
					'" title="' +
					esc(title) +
					'">' +
					esc(label) +
					'<button type="button" class="kt-cl-cfg04-chip-remove" data-action="remove-related" data-related-id="' +
					esc(ref.id || id) +
					'" aria-label="' +
					esc(__("Remove")) +
					'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></span>'
				);
			})
			.join("");
		var available = availableRequirements().filter(function (r) {
			return (selectedIds || []).indexOf(String(r.id || "")) < 0;
		});
		var pickOpts =
			'<option value="">' +
			esc(available.length ? __("+ Add Reference") : __("No IT Requirements configured")) +
			"</option>";
		available.forEach(function (r) {
			var primary = r.name || r.code || r.id;
			var secondary = r.code && r.name ? r.code : "";
			pickOpts +=
				'<option value="' +
				esc(r.id) +
				'">' +
				esc(primary) +
				(secondary ? " (" + esc(secondary) + ")" : "") +
				"</option>";
		});
		return (
			'<div class="kt-cl-cfg04-chip-field" data-testid="kt-cl-cfg04-drawer-related">' +
			'<div class="kt-cl-cfg04-chips" data-testid="kt-cl-cfg04-drawer-related-chips">' +
			(chips ||
				'<span class="kt-cl-cfg04-chip-empty">' +
					esc(__("Optional — link configured IT Requirements")) +
					"</span>") +
			"</div>" +
			'<select class="kt-cl-cfg04-select kt-cl-cfg04-related-pick" data-testid="kt-cl-cfg04-drawer-related-pick"' +
			(available.length ? "" : " disabled") +
			">" +
			pickOpts +
			"</select></div>"
		);
	}

	function sectionTitle(n, label) {
		return (
			'<h3 class="kt-cl-cfg04-section-title">' +
			esc(String(n) + ". " + label) +
			"</h3>"
		);
	}

	function drawerHtml(row, isNew) {
		row = row || {};
		var milestoneId = row.milestone_id || (isNew ? nextMilestoneId() : "");
		var relatedIds = (row.related_requirement_ids || []).slice();
		if (!relatedIds.length && row.related_requirement_refs) {
			relatedIds = row.related_requirement_refs.map(function (r) {
				return r.id || r.code;
			});
		}
		state.drawerRelatedIds = relatedIds.slice();
		var refs = row.references || {
			it_requirements: relatedIds.length
				? "Linked to IT Requirements"
				: "No requirement link selected",
			price_schedule: "No price schedule link expected",
			contract_values: "May carry into contract values",
		};
		return (
			'<div class="kt-cl-cfg04-drawer-overlay" data-testid="kt-cl-cfg04-drawer-overlay" role="dialog" aria-modal="true">' +
			'<aside class="kt-cl-cfg04-drawer" data-testid="kt-cl-cfg04-drawer">' +
			'<header class="kt-cl-cfg04-drawer-header">' +
			"<div>" +
			'<h2 data-testid="kt-cl-cfg04-drawer-title">' +
			esc(isNew ? __("Add Milestone") : __("Milestone Detail")) +
			"</h2>" +
			'<p class="kt-cl-cfg04-drawer-eyebrow">' +
			esc(__("CFG-04 IMPLEMENTATION")) +
			"</p></div>" +
			'<button type="button" class="kt-cl-cfg04-drawer-close" data-action="close-drawer" data-testid="kt-cl-cfg04-drawer-close" aria-label="' +
			__("Close") +
			'"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></header>' +
			'<div class="kt-cl-cfg04-drawer-body" data-testid="kt-cl-cfg04-drawer-body">' +
			"<section>" +
			sectionTitle(1, __("Milestone Core Identity")) +
			fieldWrap(
				__("ID"),
				'<p class="kt-cl-cfg04-readonly" data-testid="kt-cl-cfg04-drawer-id" data-milestone-id="' +
					esc(milestoneId) +
					'">' +
					esc(milestoneId) +
					"</p>",
				false
			) +
			fieldWrap(
				__("Milestone Name"),
				'<input type="text" class="kt-cl-cfg04-input" data-drawer-field="name" data-testid="kt-cl-cfg04-drawer-name" placeholder="' +
					esc(__("e.g. Installation & Config")) +
					'" value="' +
					esc(row.name || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Milestone Description"),
				'<textarea class="kt-cl-cfg04-textarea" rows="3" data-drawer-field="description" data-testid="kt-cl-cfg04-drawer-description">' +
					esc(row.description || "") +
					"</textarea>",
				true
			) +
			'<div class="kt-cl-cfg04-grid-2">' +
			fieldWrap(
				__("Sequence"),
				'<input type="number" min="1" class="kt-cl-cfg04-input" data-drawer-field="sequence" data-testid="kt-cl-cfg04-drawer-sequence" value="' +
					esc(row.sequence || (isNew ? String((state.milestones || []).length + 1) : "")) +
					'" />',
				true
			) +
			fieldWrap(
				__("Expected Duration"),
				durationControlsHtml(
					"drawer",
					row.expected_duration_value,
					row.expected_duration_unit,
					"weeks"
				),
				true
			) +
			"</div>" +
			fieldWrap(
				__("Start Trigger"),
				'<input type="text" class="kt-cl-cfg04-input" list="kt-cl-cfg04-start-triggers" data-drawer-field="start_trigger" data-testid="kt-cl-cfg04-drawer-trigger" value="' +
					esc(row.start_trigger || "") +
					'" />' +
					startTriggerDatalist(),
				true
			) +
			"</section>" +
			"<section>" +
			sectionTitle(2, __("Deliverables & Technical Mapping")) +
			fieldWrap(
				__("Key Deliverable"),
				'<input type="text" class="kt-cl-cfg04-input" data-drawer-field="key_deliverable" data-testid="kt-cl-cfg04-drawer-deliverable" value="' +
					esc(row.key_deliverable || "") +
					'" />',
				true
			) +
			fieldWrap(
				__("Deliverable Description"),
				'<textarea class="kt-cl-cfg04-textarea" rows="2" data-drawer-field="deliverable_description" data-testid="kt-cl-cfg04-drawer-deliverable-description">' +
					esc(row.deliverable_description || "") +
					"</textarea>",
				true
			) +
			fieldWrap(__("Related IT Requirements"), relatedChipsHtml(relatedIds), false) +
			"</section>" +
			"<section>" +
			sectionTitle(3, __("Formal Acceptance Framework")) +
			fieldWrap(
				__("Acceptance Method"),
				'<input type="text" class="kt-cl-cfg04-input" list="kt-cl-cfg04-acceptance-methods" data-drawer-field="acceptance_method" data-testid="kt-cl-cfg04-drawer-acceptance" placeholder="' +
					esc(__("e.g. Inspection at delivery")) +
					'" value="' +
					esc(row.acceptance_method || "") +
					'" />' +
					acceptanceDatalist() +
					'<p class="kt-cl-cfg04-field-hint">' +
					esc(
						__(
							"How this milestone will later be accepted — a method, not a setup status."
						)
					) +
					"</p>",
				true
			) +
			fieldWrap(
				__("Evidence Expected"),
				'<textarea class="kt-cl-cfg04-textarea" rows="2" data-drawer-field="evidence_expected" data-testid="kt-cl-cfg04-drawer-evidence">' +
					esc(row.evidence_expected || "") +
					"</textarea>",
				false
			) +
			"</section>" +
			'<section data-testid="kt-cl-cfg04-drawer-references">' +
			sectionTitle(4, __("References (Compact)")) +
			'<ul class="kt-cl-cfg04-refs-compact">' +
			"<li><span class=\"material-symbols-outlined\" aria-hidden=\"true\">link</span>" +
			esc(refs.it_requirements || "") +
			"</li>" +
			"<li><span class=\"material-symbols-outlined\" aria-hidden=\"true\">payments</span>" +
			esc(refs.price_schedule || "") +
			"</li>" +
			"<li><span class=\"material-symbols-outlined\" aria-hidden=\"true\">description</span>" +
			esc(refs.contract_values || "") +
			"</li></ul></section></div>" +
			'<footer class="kt-cl-cfg04-drawer-footer">' +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--primary" data-action="save-milestone" data-testid="kt-cl-cfg04-drawer-save">' +
			__("Save Milestone") +
			"</button>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary" data-action="close-drawer" data-testid="kt-cl-cfg04-drawer-cancel">' +
			__("Cancel") +
			"</button></footer></aside></div>"
		);
	}

	function ensureDrawerHost() {
		var $host = $("#" + DRAWER_HOST_ID);
		if (!$host.length) {
			$host = $('<div id="' + DRAWER_HOST_ID + '"></div>').appendTo(document.body);
		}
		return $host;
	}

	function closeDrawer() {
		state.drawerOpen = false;
		state.editingIndex = -1;
		state.drawerRelatedIds = [];
		ensureDrawerHost().empty().off(".cfg04drawer");
	}

	function refreshRelatedChips($host) {
		var $field = $host.find('[data-testid="kt-cl-cfg04-drawer-related"]');
		if (!$field.length) {
			return;
		}
		$field.replaceWith($(relatedChipsHtml(state.drawerRelatedIds)));
	}

	function openDrawer(index) {
		state.drawerOpen = true;
		state.editingIndex = typeof index === "number" ? index : -1;
		var isNew = state.editingIndex < 0;
		var row = isNew ? {} : state.milestones[state.editingIndex] || {};
		var $host = ensureDrawerHost();
		$host.html(drawerHtml(row, isNew));
		$host.off(".cfg04drawer");
		$host.on("click.cfg04drawer", "[data-action='close-drawer']", function (e) {
			e.preventDefault();
			closeDrawer();
		});
		$host.on("click.cfg04drawer", "[data-testid='kt-cl-cfg04-drawer-overlay']", function (e) {
			if (e.target === this) {
				closeDrawer();
			}
		});
		$host.on("click.cfg04drawer", "[data-action='save-milestone']", function (e) {
			e.preventDefault();
			saveDrawerMilestone($host);
		});
		$host.on("click.cfg04drawer", "[data-action='remove-related']", function (e) {
			e.preventDefault();
			var rid = String($(this).attr("data-related-id") || "");
			state.drawerRelatedIds = (state.drawerRelatedIds || []).filter(function (id) {
				return id !== rid;
			});
			refreshRelatedChips($host);
		});
		$host.on("change.cfg04drawer", "[data-testid='kt-cl-cfg04-drawer-related-pick']", function () {
			var rid = String($(this).val() || "");
			if (!rid) {
				return;
			}
			if ((state.drawerRelatedIds || []).indexOf(rid) < 0) {
				state.drawerRelatedIds = (state.drawerRelatedIds || []).concat([rid]);
			}
			refreshRelatedChips($host);
		});
	}

	function collectDrawer($host) {
		var row = {};
		$host.find("[data-drawer-field]").each(function () {
			var key = String($(this).attr("data-drawer-field") || "");
			row[key] = String($(this).val() || "").trim();
		});
		var previewId = String(
			$host.find('[data-testid="kt-cl-cfg04-drawer-id"]').attr("data-milestone-id") || ""
		).trim();
		if (state.editingIndex >= 0 && state.milestones[state.editingIndex]) {
			row.milestone_id = state.milestones[state.editingIndex].milestone_id || previewId;
		} else {
			row.milestone_id = previewId || nextMilestoneId();
		}
		row.related_requirement_ids = (state.drawerRelatedIds || []).slice();
		return row;
	}

	function collectSingle($root) {
		var row = Object.assign({}, state.singleDelivery || {});
		$root.find("[data-single-field]").each(function () {
			var key = String($(this).attr("data-single-field") || "");
			row[key] = String($(this).val() || "").trim();
		});
		return row;
	}

	function persistablePayload() {
		return {
			delivery_approach: state.deliveryApproach,
			milestones: (state.milestones || []).map(function (r) {
				return {
					milestone_id: r.milestone_id || "",
					name: r.name || "",
					description: r.description || "",
					sequence: r.sequence || "",
					expected_duration_value: r.expected_duration_value || "",
					expected_duration_unit: r.expected_duration_unit || "weeks",
					expected_duration: r.expected_duration || "",
					start_trigger: r.start_trigger || "",
					key_deliverable: r.key_deliverable || "",
					deliverable_description: r.deliverable_description || "",
					related_requirement_ids: r.related_requirement_ids || [],
					acceptance_method: r.acceptance_method || "",
					evidence_expected: r.evidence_expected || "",
				};
			}),
			single_delivery: {
				expected_duration_value: (state.singleDelivery || {}).expected_duration_value || "",
				expected_duration_unit:
					(state.singleDelivery || {}).expected_duration_unit || "months",
				expected_delivery_duration:
					(state.singleDelivery || {}).expected_delivery_duration || "",
				delivery_trigger: (state.singleDelivery || {}).delivery_trigger || "",
				key_deliverables: (state.singleDelivery || {}).key_deliverables || "",
				acceptance_method: (state.singleDelivery || {}).acceptance_method || "",
				evidence_expected: (state.singleDelivery || {}).evidence_expected || "",
				notes_to_bidders: (state.singleDelivery || {}).notes_to_bidders || "",
			},
		};
	}

	function saveDrawerMilestone($host) {
		var row = collectDrawer($host);
		if (state.editingIndex >= 0) {
			state.milestones[state.editingIndex] = Object.assign(
				{},
				state.milestones[state.editingIndex],
				row
			);
		} else {
			state.milestones.push(row);
		}
		state.dirty = true;
		closeDrawer();
		if (state.page) {
			saveSchedule($(state.page.main), state.page, { fromDrawer: true });
		}
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg04-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function refreshContinue($root, canContinue) {
		var can =
			typeof canContinue === "boolean"
				? canContinue
				: !!(state.payload && state.payload.can_continue);
		$root.find('[data-testid="kt-cl-cfg04-continue"]').prop("disabled", !can || state.saving);
	}

	function applyClientFromPayload(data) {
		if (!data) {
			return;
		}
		state.deliveryApproach = data.delivery_approach || APPROACH_PHASED;
		state.milestones = (data.milestones || []).slice();
		state.singleDelivery = Object.assign({}, data.single_delivery || {});
	}

	function remountWithPayload(page, data, opts) {
		opts = opts || {};
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Implementation Schedule"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		if (!opts.keepClientList) {
			applyClientFromPayload(data);
			state.dirty = false;
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? pageHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
		setDirty($(page.main), state.dirty);
		refreshContinue($(page.main), !!(data && data.can_continue) && !state.dirty);
		if (state.dirty) {
			refreshContinue($(page.main), false);
		}
	}

	function saveSchedule($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		if (state.deliveryApproach === APPROACH_SINGLE) {
			state.singleDelivery = collectSingle($root);
		}
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		frappe.call({
			method: SAVE_API,
			args: {
				configuration_id: state.configurationId,
				payload: persistablePayload(),
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
				} else if (opts.fromDelete) {
					frappe.show_alert(
						{
							message: __("Milestone removed"),
							indicator: "green",
						},
						4
					);
				} else if (!opts.thenContinue && !opts.silent) {
					frappe.show_alert(
						{
							message: __("Implementation Schedule saved successfully"),
							indicator: "green",
						},
						5
					);
				}
				if (opts.thenContinue && data.can_continue) {
					frappe.route_options = { configuration_id: state.configurationId };
					frappe.set_route(
						"it-tender-configuration-system-inventory",
						state.configurationId
					);
				}
			},
			error: function () {
				state.saving = false;
				remountWithPayload(page, state.payload || {}, { keepClientList: true });
				setDirty($(page.main), true);
				refreshContinue($(page.main), false);
			},
		});
	}

	function requestApproachChange($root, page, nextApproach) {
		if (nextApproach === state.deliveryApproach) {
			return;
		}
		var switchingToSingle =
			nextApproach === APPROACH_SINGLE && (state.milestones || []).length > 0;
		var apply = function () {
			if (state.deliveryApproach === APPROACH_SINGLE) {
				state.singleDelivery = collectSingle($root);
			}
			state.deliveryApproach = nextApproach;
			state.dirty = true;
			remountWithPayload(page, state.payload || {}, { keepClientList: true });
			setDirty($(page.main), true);
			// Persist approach + both drafts immediately (no toast — avoids racing footer Save)
			saveSchedule($(page.main), page, { silent: true });
		};
		if (switchingToSingle) {
			kentender_core.cl.confirm({
				title: __("Switch to Single Turnkey Delivery?"),
				message: __(
					"This will replace the phased delivery view with one single delivery milestone. Existing milestone details will be kept in draft history and will be restored if you switch back before submission for review."
				),
				confirmLabel: __("Switch approach"),
				cancelLabel: __("Cancel"),
				tone: "primary",
				onConfirm: apply,
				onCancel: function () {
					// Cancel: keep phased selected without remount race against Yes
					state.deliveryApproach = APPROACH_PHASED;
					$root.find('[data-testid="kt-cl-cfg04-approach-phased"]').prop("checked", true);
					$root.find('[data-testid="kt-cl-cfg04-approach-single"]').prop("checked", false);
					$root.find(".kt-cl-cfg04-approach-option").removeClass("is-active");
					$root
						.find('[data-testid="kt-cl-cfg04-approach-phased"]')
						.closest(".kt-cl-cfg04-approach-option")
						.addClass("is-active");
				},
			});
			return;
		}
		apply();
	}

	function bind($root, page) {
		$root.off(".cfg04");
		$root.on("click.cfg04", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg04-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg04-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg04-issues-toggle"]');
			var $chev = $panel.find(".kt-cl-cfg04-issues-chevron");
			$panel.toggleClass("kt-cl-cfg04-issues--open", state.issuesExpanded);
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
		$root.on("change.cfg04", 'input[name="kt-cl-cfg04-approach"]', function () {
			requestApproachChange($root, page, String($(this).val() || APPROACH_PHASED));
		});
		$root.on("input.cfg04 change.cfg04", "[data-single-field]", function () {
			state.dirty = true;
			setDirty($root, true);
			refreshContinue($root, false);
		});
		$root.on("click.cfg04", "[data-action='add-milestone']", function (e) {
			e.preventDefault();
			openDrawer(-1);
		});
		$root.on("click.cfg04", "[data-action='edit-milestone']", function (e) {
			e.preventDefault();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (!isNaN(idx)) {
				openDrawer(idx);
			}
		});
		$root.on("click.cfg04", "[data-action='delete-milestone']", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var idx = parseInt($(this).attr("data-index"), 10);
			if (isNaN(idx) || idx < 0 || idx >= (state.milestones || []).length) {
				return;
			}
			var row = state.milestones[idx] || {};
			var label = row.name || row.milestone_id || __("this milestone");
			kentender_core.cl.confirm({
				title: __("Remove milestone?"),
				message: __("{0} will be removed from this configuration.", [label]),
				confirmLabel: __("Remove"),
				cancelLabel: __("Cancel"),
				tone: "danger",
				onConfirm: function () {
					state.milestones.splice(idx, 1);
					state.dirty = true;
					closeDrawer();
					if (state.page) {
						saveSchedule($(state.page.main), state.page, { fromDelete: true });
					}
				},
			});
		});
		$root.on("click.cfg04", "[data-action='back-home']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route("it-tender-configuration-overview", state.configurationId);
		});
		$root.on("click.cfg04", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveSchedule($root, page, {});
		});
		$root.on("click.cfg04", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveSchedule($root, page, { runCheck: true });
		});
		$root.on("click.cfg04", "[data-action='continue']", function (e) {
			e.preventDefault();
			closeDrawer();
			if (state.dirty) {
				saveSchedule($root, page, { thenContinue: true });
				return;
			}
			if (state.payload && state.payload.can_continue && state.configurationId) {
				frappe.route_options = { configuration_id: state.configurationId };
				frappe.set_route(
					"it-tender-configuration-system-inventory",
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
			title: __("Implementation Schedule"),
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
			title: __("Implementation Schedule"),
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
