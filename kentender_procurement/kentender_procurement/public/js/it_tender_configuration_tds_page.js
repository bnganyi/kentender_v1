// CFG-02 — Tender Data Sheet (C2-CFG2).
// Route contract: /desk/it-tender-configuration-tds/<configuration_id>
(function () {
	"use strict";

	var SURFACE_ID = "CFG-02";
	var PAGE_SLUG = "it-tender-configuration-tds";
	var GET_API = "kentender_procurement.tender_configurations.get_tender_configuration_tds";
	var SAVE_API = "kentender_procurement.tender_configurations.save_tender_configuration_tds";
	var STORAGE_KEY = "kt_cl_cfg02_configuration_id";
	var SUBTITLE =
		"Set the tender-specific instructions, dates, submission rules, and allowed options for this IT tender.";

	var state = {
		payload: null,
		configurationId: null,
		mounting: false,
		dirty: false,
		saving: false,
		values: {},
		/** Show issues panel after Run Check even if empty form. */
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
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-cfg02-root">' +
			'<p class="text-body-md text-on-surface-variant">' +
			__("Select a tender configuration from Configuration Home.") +
			"</p>" +
			'<button type="button" class="kt-cl-wizard-btn kt-cl-wizard-btn--secondary mt-4" data-action="back-home" data-testid="kt-cl-cfg02-back">' +
			__("Back to Configuration Home") +
			"</button></div>"
		);
	}

	function statusChip(label) {
		var key = String(label || "Not started").toLowerCase().replace(/\s+/g, "-");
		return (
			'<span class="kt-cl-cfg02-status kt-cl-cfg02-status--' +
			esc(key) +
			'" data-testid="kt-cl-cfg02-status">' +
			'<span class="kt-cl-cfg02-status-dot" aria-hidden="true"></span>' +
			esc(label || "Not started") +
			"</span>"
		);
	}

	function groupMeta(data, groupKey) {
		var groups = (data && data.tds_groups) || [];
		for (var i = 0; i < groups.length; i += 1) {
			if (groups[i].group_key === groupKey) {
				return groups[i];
			}
		}
		return { status_label: "Not started", group_label: groupKey };
	}

	function optionsFor(data, key) {
		var opts = (data && data.options && data.options[key]) || [];
		return opts;
	}

	function val(values, key) {
		return values && values[key] != null ? String(values[key]) : "";
	}

	function fieldLabel(text, required) {
		return (
			'<label class="kt-cl-cfg02-label">' +
			esc(text) +
			(required ? ' <span class="kt-cl-cfg02-req">*</span>' : "") +
			"</label>"
		);
	}

	function textField(key, label, values, opts) {
		opts = opts || {};
		var type = opts.type || "text";
		return (
			'<div class="kt-cl-cfg02-field' +
			(opts.wide ? " kt-cl-cfg02-field--wide" : "") +
			(opts.hidden ? " hidden" : "") +
			'" data-field-wrap="' +
			esc(key) +
			'">' +
			fieldLabel(label, opts.required) +
			'<input type="' +
			esc(type) +
			'" class="kt-cl-cfg02-input" data-field="' +
			esc(key) +
			'" data-testid="kt-cl-cfg02-' +
			esc(key) +
			'" value="' +
			esc(val(values, key)) +
			'"' +
			(opts.readonly ? " readonly" : "") +
			(opts.placeholder ? ' placeholder="' + esc(opts.placeholder) + '"' : "") +
			" /></div>"
		);
	}

	function textareaField(key, label, values, opts) {
		opts = opts || {};
		return (
			'<div class="kt-cl-cfg02-field kt-cl-cfg02-field--wide' +
			(opts.hidden ? " hidden" : "") +
			'" data-field-wrap="' +
			esc(key) +
			'">' +
			fieldLabel(label, opts.required) +
			'<textarea class="kt-cl-cfg02-textarea" rows="3" data-field="' +
			esc(key) +
			'" data-testid="kt-cl-cfg02-' +
			esc(key) +
			'"' +
			(opts.placeholder ? ' placeholder="' + esc(opts.placeholder) + '"' : "") +
			">" +
			esc(val(values, key)) +
			"</textarea></div>"
		);
	}

	function selectField(key, label, values, options, opts) {
		opts = opts || {};
		var cur = val(values, key);
		var optsHtml =
			'<option value="">' +
			esc(__("Select…")) +
			"</option>" +
			(options || [])
				.map(function (o) {
					return (
						'<option value="' +
						esc(o) +
						'"' +
						(cur === o ? " selected" : "") +
						">" +
						esc(o) +
						"</option>"
					);
				})
				.join("");
		return (
			'<div class="kt-cl-cfg02-field' +
			(opts.wide ? " kt-cl-cfg02-field--wide" : "") +
			(opts.hidden ? " hidden" : "") +
			'" data-field-wrap="' +
			esc(key) +
			'">' +
			fieldLabel(label, opts.required) +
			'<select class="kt-cl-cfg02-select" data-field="' +
			esc(key) +
			'" data-testid="kt-cl-cfg02-' +
			esc(key) +
			'">' +
			optsHtml +
			"</select></div>"
		);
	}

	function ynField(key, label, values, opts) {
		opts = opts || {};
		var cur = val(values, key);
		return (
			'<div class="kt-cl-cfg02-field' +
			(opts.hidden ? " hidden" : "") +
			'" data-field-wrap="' +
			esc(key) +
			'">' +
			fieldLabel(label, opts.required) +
			'<div class="kt-cl-cfg02-yn" data-testid="kt-cl-cfg02-' +
			esc(key) +
			'">' +
			'<label class="kt-cl-cfg02-yn-opt"><input type="radio" name="kt-cl-cfg02-' +
			esc(key) +
			'" data-field="' +
			esc(key) +
			'" value="Yes"' +
			(cur === "Yes" ? " checked" : "") +
			" /> " +
			__("Yes") +
			"</label>" +
			'<label class="kt-cl-cfg02-yn-opt"><input type="radio" name="kt-cl-cfg02-' +
			esc(key) +
			'" data-field="' +
			esc(key) +
			'" value="No"' +
			(cur === "No" ? " checked" : "") +
			" /> " +
			__("No") +
			"</label></div></div>"
		);
	}

	function numberUnitField(numKey, unitKey, label, values, units, opts) {
		opts = opts || {};
		var unit = val(values, unitKey) || "days";
		var unitOpts = (units || ["days", "weeks", "months"])
			.map(function (u) {
				return (
					'<option value="' +
					esc(u) +
					'"' +
					(unit === u ? " selected" : "") +
					">" +
					esc(u.charAt(0).toUpperCase() + u.slice(1)) +
					"</option>"
				);
			})
			.join("");
		return (
			'<div class="kt-cl-cfg02-field' +
			(opts.hidden ? " hidden" : "") +
			'" data-field-wrap="' +
			esc(numKey) +
			'">' +
			fieldLabel(label, opts.required) +
			'<div class="kt-cl-cfg02-num-unit">' +
			'<input type="number" min="0" class="kt-cl-cfg02-input" data-field="' +
			esc(numKey) +
			'" data-testid="kt-cl-cfg02-' +
			esc(numKey) +
			'" value="' +
			esc(val(values, numKey)) +
			'" />' +
			'<select class="kt-cl-cfg02-select kt-cl-cfg02-select--unit" data-field="' +
			esc(unitKey) +
			'" data-testid="kt-cl-cfg02-' +
			esc(unitKey) +
			'">' +
			unitOpts +
			"</select></div></div>"
		);
	}

	function sectionCard(data, groupKey, title, bodyHtml) {
		var meta = groupMeta(data, groupKey);
		return (
			'<section class="kt-cl-cfg02-card" data-testid="kt-cl-cfg02-section-' +
			esc(groupKey) +
			'" data-group="' +
			esc(groupKey) +
			'">' +
			'<div class="kt-cl-cfg02-card-head">' +
			"<h3>" +
			esc(title) +
			"</h3>" +
			statusChip(meta.status_label) +
			"</div>" +
			'<div class="kt-cl-cfg02-card-body">' +
			bodyHtml +
			"</div></section>"
		);
	}

	function blockersHtml(data) {
		var blockers = data.blockers || [];
		var warnings = data.warnings || [];
		var hasProgress = !!(data && data.has_progress);
		var showPanel =
			blockers.length > 0 && (hasProgress || state.showIssuesPanel);
		if (!blockers.length || !showPanel) {
			return (
				'<div class="kt-cl-cfg02-issues hidden" data-testid="kt-cl-cfg02-blockers" data-mode="deferred" aria-hidden="true"></div>'
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
				(warnN === 1
					? __("1 warning")
					: __("{0} warnings", [warnN]));
		}
		var items = blockers
			.map(function (b) {
				return "<li>" + esc(b.message || "") + "</li>";
			})
			.join("");
		var expanded = !!state.issuesExpanded;
		return (
			'<div class="kt-cl-cfg02-issues' +
			(expanded ? " kt-cl-cfg02-issues--open" : "") +
			'" data-testid="kt-cl-cfg02-blockers" data-mode="collapsible" data-expanded="' +
			(expanded ? "true" : "false") +
			'">' +
			'<button type="button" class="kt-cl-cfg02-issues-toggle" data-action="toggle-issues" data-testid="kt-cl-cfg02-issues-toggle" aria-expanded="' +
			(expanded ? "true" : "false") +
			'" aria-controls="kt-cl-cfg02-issues-list">' +
			'<span class="kt-cl-cfg02-issues-toggle-main">' +
			'<span class="material-symbols-outlined kt-cl-cfg02-issues-icon" aria-hidden="true">error</span>' +
			'<span class="kt-cl-cfg02-issues-summary" data-testid="kt-cl-cfg02-issues-summary">' +
			esc(summary) +
			"</span>" +
			'<span class="kt-cl-cfg02-issues-hint">' +
			esc(__("Review details")) +
			"</span></span>" +
			'<span class="material-symbols-outlined kt-cl-cfg02-issues-chevron" aria-hidden="true">' +
			(expanded ? "expand_less" : "expand_more") +
			"</span></button>" +
			'<div id="kt-cl-cfg02-issues-list" class="kt-cl-cfg02-issues-body' +
			(expanded ? "" : " hidden") +
			'" data-testid="kt-cl-cfg02-issues-list" role="region"' +
			(expanded ? "" : ' hidden') +
			">" +
			'<p class="kt-cl-cfg02-issues-intro">' +
			esc(
				__(
					"Complete the sections below. Section status chips show which groups still need work."
				)
			) +
			"</p>" +
			"<ul>" +
			items +
			"</ul></div></div>"
		);
	}

	function formHtml(data) {
		var values = data.tds_values || {};
		var g = data.guidance || {};
		var meetingYes = val(values, "pre_tender_meeting") === "Yes";
		var methodSet = !!val(values, "clarification_submission_method");
		var reservedYes = val(values, "reserved_procurement") === "Yes";
		var securityYes = val(values, "tender_security_required") === "Yes";
		var prefYes = val(values, "margin_of_preference_applies") === "Yes";

		var communication =
			textField("contact_officer", __("Contact Officer"), values, { required: true }) +
			textField("contact_email", __("Contact Email"), values, {
				type: "email",
				required: true,
			}) +
			selectField(
				"clarification_submission_method",
				__("Clarification Submission Method"),
				values,
				optionsFor(data, "clarification_submission_method"),
				{ required: true }
			) +
			textField("clarification_deadline", __("Clarification Deadline"), values, {
				type: "datetime-local",
				required: true,
				hidden: !methodSet,
			}) +
			ynField("pre_tender_meeting", __("Pre-tender Meeting"), values, { required: true }) +
			textareaField("pre_tender_meeting_details", __("Pre-tender Meeting Details"), values, {
				required: true,
				hidden: !meetingYes,
				placeholder: __("Enter meeting location, link, or instructions..."),
			});

		var keyDates =
			'<div class="kt-cl-cfg02-field" data-field-wrap="tender_publication_date">' +
			fieldLabel(__("Tender Publication Date") + " (" + __("Read-only") + ")", false) +
			'<input type="text" class="kt-cl-cfg02-input kt-cl-cfg02-input--readonly" readonly data-testid="kt-cl-cfg02-tender_publication_date" value="' +
			esc(val(values, "tender_publication_date") || "—") +
			'" /></div>' +
			textField("tender_submission_deadline", __("Tender Submission Deadline"), values, {
				type: "datetime-local",
				required: true,
			}) +
			textField("tender_opening_datetime", __("Tender Opening Date and Time"), values, {
				type: "datetime-local",
				required: true,
			}) +
			numberUnitField(
				"bid_validity_period",
				"bid_validity_unit",
				__("Bid Validity Period"),
				values,
				optionsFor(data, "bid_validity_unit"),
				{ required: true }
			);

		var submission =
			selectField(
				"submission_channel",
				__("Submission Channel"),
				values,
				optionsFor(data, "submission_channel"),
				{ required: true }
			) +
			selectField(
				"submission_language",
				__("Submission Language"),
				values,
				optionsFor(data, "submission_language"),
				{ required: true }
			) +
			selectField(
				"tender_currency",
				__("Tender Currency"),
				values,
				optionsFor(data, "tender_currency"),
				{ required: true }
			) +
			ynField("alternative_tenders_allowed", __("Alternative Tenders Allowed"), values, {
				required: true,
			}) +
			'<div class="kt-cl-cfg02-field" data-field-wrap="lots_allowed">' +
			fieldLabel(__("Lots Allowed"), false) +
			'<input type="text" class="kt-cl-cfg02-input kt-cl-cfg02-input--readonly" readonly data-testid="kt-cl-cfg02-lots_allowed" value="' +
			esc(val(values, "lots_allowed") || "No") +
			'" />' +
			'<p class="kt-cl-cfg02-helper">' +
			__("Read from Tender Profile; edit lot structure there.") +
			"</p></div>" +
			ynField("joint_ventures_allowed", __("Joint Ventures Allowed"), values, {
				required: true,
			});

		var eligibility =
			selectField(
				"eligible_tenderers",
				__("Eligible Tenderers"),
				values,
				optionsFor(data, "eligible_tenderers"),
				{ required: true }
			) +
			ynField("reserved_procurement", __("Reserved Procurement"), values, { required: true }) +
			selectField(
				"reservation_category",
				__("Reservation Category"),
				values,
				optionsFor(data, "reservation_category"),
				{ required: true, hidden: !reservedYes }
			) +
			textareaField(
				"local_participation_requirement",
				__("Local Participation Requirement"),
				values,
				{ placeholder: __("Enter requirements...") }
			);

		var security =
			ynField("tender_security_required", __("Tender Security Required"), values, {
				required: true,
			}) +
			selectField(
				"tender_security_type",
				__("Tender Security Type"),
				values,
				optionsFor(data, "tender_security_type"),
				{ required: true, hidden: !securityYes }
			) +
			textField("tender_security_amount", __("Tender Security Amount"), values, {
				required: true,
				hidden: !securityYes,
			}) +
			numberUnitField(
				"tender_security_validity_period",
				"tender_security_validity_unit",
				__("Tender Security Validity Period"),
				values,
				optionsFor(data, "tender_security_validity_unit"),
				{ required: true, hidden: !securityYes }
			);

		var preferences =
			ynField("margin_of_preference_applies", __("Margin of Preference Applies"), values, {
				required: true,
			}) +
			selectField(
				"preference_basis",
				__("Preference Basis"),
				values,
				optionsFor(data, "preference_basis"),
				{ required: true, hidden: !prefYes }
			) +
			textareaField("preference_evidence_required", __("Preference Evidence Required"), values, {
				required: true,
				hidden: !prefYes,
			});

		var bidOpening =
			selectField(
				"opening_method",
				__("Opening Method"),
				values,
				optionsFor(data, "opening_method"),
				{ required: true }
			) +
			textField("opening_location", __("Opening Location / Portal"), values, {
				required: true,
			}) +
			ynField("opening_attendance_allowed", __("Opening Attendance Allowed"), values, {
				required: true,
			}) +
			textareaField("opening_notes", __("Opening Notes"), values, {});

		var guidance =
			'<aside class="kt-cl-cfg02-side" data-testid="kt-cl-cfg02-side">' +
			'<section class="kt-cl-cfg02-guidance" data-testid="kt-cl-cfg02-guidance">' +
			"<h3>" +
			esc(g.title || __("Tender Data Sheet Guidance")) +
			"</h3>" +
			'<p class="kt-cl-cfg02-guidance-body">' +
			esc(g.body || "") +
			"</p>" +
			'<dl class="kt-cl-cfg02-guidance-list">' +
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
			"</dd></div></dl></section></aside>";

		var comp = c();
		var ctx = data.context || data;
		return (
			'<div data-testid="kt-cl-cfg02-root" data-configuration-id="' +
			esc(data.configuration_id || "") +
			'">' +
			comp.configurationContextStrip(ctx) +
			blockersHtml(data) +
			'<div class="kt-cl-cfg02-layout" data-testid="kt-cl-cfg02-layout">' +
			'<div class="kt-cl-cfg02-main" data-testid="kt-cl-cfg02-main">' +
			sectionCard(data, "communication", "1. " + __("Tender Communication"), communication) +
			sectionCard(data, "key_dates", "2. " + __("Key Dates"), keyDates) +
			sectionCard(data, "submission", "3. " + __("Submission Rules"), submission) +
			sectionCard(
				data,
				"eligibility",
				"4. " + __("Eligibility and Participation"),
				eligibility
			) +
			sectionCard(data, "security", "5. " + __("Tender Security"), security) +
			sectionCard(
				data,
				"preferences",
				"6. " + __("Preferences and Reservations"),
				preferences
			) +
			sectionCard(data, "bid_opening", "7. " + __("Bid Opening"), bidOpening) +
			"</div>" +
			guidance +
			"</div>" +
			comp.wizardStepFooter({
				testid: "kt-cl-cfg02-footer",
				backTestid: "kt-cl-cfg02-back",
				saveTestid: "kt-cl-cfg02-save",
				continueTestid: "kt-cl-cfg02-continue",
				backLabel: __("Back to Configuration Home"),
				saveLabel: __("Save Tender Data Sheet"),
				continueLabel: __("Continue to IT Requirements"),
				saveDisabled: true,
				continueDisabled: !data.can_continue,
				extraEndActions: [
					{
						label: __("Run Check"),
						action: "run-check",
						testid: "kt-cl-cfg02-run-check",
						variant: "outline",
					},
				],
			}) +
			"</div>"
		);
	}

	function collectValues($root) {
		var values = {};
		$root.find("[data-field]").each(function () {
			var $el = $(this);
			var key = String($el.attr("data-field") || "");
			if (!key) {
				return;
			}
			if ($el.is(':radio')) {
				if ($el.is(":checked")) {
					values[key] = String($el.val() || "").trim();
				}
				return;
			}
			values[key] = String($el.val() || "").trim();
		});
		return values;
	}

	function setDirty($root, dirty) {
		state.dirty = !!dirty;
		$root.find('[data-testid="kt-cl-cfg02-save"]').prop("disabled", !state.dirty || state.saving);
	}

	function refreshContinue($root, canContinue) {
		var can =
			typeof canContinue === "boolean"
				? canContinue
				: !!(state.payload && state.payload.can_continue);
		$root.find('[data-testid="kt-cl-cfg02-continue"]').prop("disabled", !can || state.saving);
	}

	function syncConditionals($root) {
		var values = collectValues($root);
		var methodSet = !!values.clarification_submission_method;
		var meetingYes = values.pre_tender_meeting === "Yes";
		var reservedYes = values.reserved_procurement === "Yes";
		var securityYes = values.tender_security_required === "Yes";
		var prefYes = values.margin_of_preference_applies === "Yes";

		function show(key, visible) {
			$root.find('[data-field-wrap="' + key + '"]').toggleClass("hidden", !visible);
		}
		show("clarification_deadline", methodSet);
		show("pre_tender_meeting_details", meetingYes);
		show("reservation_category", reservedYes);
		show("tender_security_type", securityYes);
		show("tender_security_amount", securityYes);
		show("tender_security_validity_period", securityYes);
		show("preference_basis", prefYes);
		show("preference_evidence_required", prefYes);
	}

	function remountWithPayload(page, data) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		var pageHeader = {
			title: __("Tender Data Sheet"),
			subtitle: __(SUBTITLE),
			hideBreadcrumbs: true,
		};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		state.payload = data;
		state.values = (data && data.tds_values) || {};
		state.dirty = false;
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: data ? formHtml(data) : emptyHtml(),
		});
		bind($(page.main), page);
		setDirty($(page.main), false);
		refreshContinue($(page.main), !!(data && data.can_continue));
		syncConditionals($(page.main));
	}

	function saveTds($root, page, opts) {
		opts = opts || {};
		if (state.saving || !state.configurationId) {
			return;
		}
		var values = collectValues($root);
		state.saving = true;
		setDirty($root, state.dirty);
		refreshContinue($root);
		frappe.call({
			method: SAVE_API,
			args: {
				configuration_id: state.configurationId,
				payload: { tds_values: values },
			},
			callback: function (r) {
				state.saving = false;
				var data = r.message || null;
				if (!data) {
					setDirty($root, true);
					refreshContinue($root);
					return;
				}
				if (opts.runCheck) {
					state.showIssuesPanel = (data.blocker_count || 0) > 0;
					state.issuesExpanded = false;
				} else if (data.has_progress && (data.blocker_count || 0) > 0) {
					state.showIssuesPanel = true;
				} else if (data.can_continue) {
					state.showIssuesPanel = false;
					state.issuesExpanded = false;
				}
				remountWithPayload(page, data);
				if (opts.runCheck) {
					var blockers = data.blocker_count || 0;
					var warnings = data.warning_count || 0;
					var ok = blockers === 0;
					frappe.show_alert(
						{
							message: ok
								? __(
										"Check complete: no blockers ({0} warnings).",
										[warnings]
								  )
								: __(
										"Check complete: {0} blocker(s), {1} warning(s).",
										[blockers, warnings]
								  ),
							indicator: ok ? "green" : "orange",
						},
						6
					);
				} else if (!opts.thenContinue) {
					frappe.show_alert(
						{
							message: __("Tender Data Sheet saved successfully"),
							indicator: "green",
						},
						5
					);
				}
				if (opts.thenContinue && data.can_continue) {
					frappe.route_options = { configuration_id: state.configurationId };
					frappe.set_route(
						"it-tender-configuration-it-requirements",
						state.configurationId
					);
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
		$root.off(".cfg02");
		$root.on("input.cfg02 change.cfg02", "[data-field]", function () {
			setDirty($root, true);
			syncConditionals($root);
			// Continue stays gated by last server can_continue until save
			refreshContinue($root);
		});
		$root.on("click.cfg02", "[data-action='toggle-issues']", function (e) {
			e.preventDefault();
			state.issuesExpanded = !state.issuesExpanded;
			var $panel = $root.find('[data-testid="kt-cl-cfg02-blockers"]');
			var $list = $root.find('[data-testid="kt-cl-cfg02-issues-list"]');
			var $btn = $root.find('[data-testid="kt-cl-cfg02-issues-toggle"]');
			var $chev = $panel.find(".kt-cl-cfg02-issues-chevron");
			$panel.toggleClass("kt-cl-cfg02-issues--open", state.issuesExpanded);
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
		$root.on("click.cfg02", "[data-action='back-home']", function (e) {
			e.preventDefault();
			if (!state.configurationId) {
				frappe.set_route("it-tender-configuration-dashboard");
				return;
			}
			frappe.route_options = { configuration_id: state.configurationId };
			frappe.set_route("it-tender-configuration-overview", state.configurationId);
		});
		$root.on("click.cfg02", "[data-action='save']", function (e) {
			e.preventDefault();
			if (!state.dirty || state.saving) {
				return;
			}
			saveTds($root, page, {});
		});
		$root.on("click.cfg02", "[data-action='run-check']", function (e) {
			e.preventDefault();
			if (state.saving) {
				return;
			}
			saveTds($root, page, { runCheck: true });
		});
		$root.on("click.cfg02", "[data-action='continue']", function (e) {
			e.preventDefault();
			if (state.dirty) {
				saveTds($root, page, { thenContinue: true });
				return;
			}
			if (state.payload && state.payload.can_continue && state.configurationId) {
				frappe.route_options = { configuration_id: state.configurationId };
				frappe.set_route(
					"it-tender-configuration-it-requirements",
					state.configurationId
				);
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
			title: __("Tender Data Sheet"),
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
			title: __("Tender Data Sheet"),
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
