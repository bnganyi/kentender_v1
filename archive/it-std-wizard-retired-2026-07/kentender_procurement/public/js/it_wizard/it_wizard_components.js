(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.components");

	function escape_html(value) {
		return String(value == null ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function icon(name, cls) {
		return (
			'<span class="material-symbols-outlined kt-itw-ico' +
			(cls ? " " + cls : "") +
			'" aria-hidden="true">' +
			name +
			"</span>"
		);
	}

	function initials(name) {
		var parts = String(name || "").trim().split(/\s+/).filter(Boolean);
		if (!parts.length) return "U";
		if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	function appbar(options) {
		options = options || {};
		var user = options.user || "User";
		var title = options.title || "IT Tender Configurations";
		var entity = options.entity || "Ministry of Finance";
		return (
			'<header class="kt-itw-appbar" data-itw-appbar="1">' +
			'<div class="kt-itw-appbar-brand">' +
			'<button type="button" class="kt-itw-brand-tile" data-itw-back="1" title="Back to Procurement" aria-label="Back to Procurement">' +
			icon("account_balance") +
			"</button>" +
			'<h1 class="kt-itw-appbar-title">' +
			escape_html(title) +
			"</h1>" +
			"</div>" +
			'<div class="kt-itw-appbar-actions">' +
			'<button type="button" class="kt-itw-bell" data-itw-notifications="1" aria-label="Notifications">' +
			icon("notifications") +
			'<span class="kt-itw-bell-dot"></span>' +
			"</button>" +
			'<div class="kt-itw-user">' +
			'<div class="kt-itw-user-text">' +
			'<p class="kt-itw-user-entity">' +
			escape_html(entity) +
			"</p>" +
			'<p class="kt-itw-user-name">' +
			escape_html(user) +
			"</p>" +
			"</div>" +
			'<div class="kt-itw-avatar" aria-hidden="true">' +
			escape_html(initials(user)) +
			"</div>" +
			"</div>" +
			"</div>" +
			"</header>"
		);
	}

	function footer(actions) {
		actions = actions || [
			{ key: "export", icon: "file_download", label: "Export Report" },
			{ key: "audit", icon: "history", label: "Audit Logs" },
		];
		return (
			'<footer class="kt-itw-footer" data-itw-footer="1">' +
			'<div class="kt-itw-footer-actions">' +
			actions
				.map(function (action) {
					return (
						'<button type="button" class="kt-itw-footer-btn" data-itw-footer-action="' +
						escape_html(action.key) +
						'">' +
						icon(action.icon, "kt-itw-ico--sm") +
						escape_html(action.label) +
						"</button>"
					);
				})
				.join("") +
			"</div>" +
			"</footer>"
		);
	}

	function page_header(options) {
		options = options || {};
		var actions = options.actions || [];
		return (
			'<section class="kt-itw-home-header" data-itw-home-header="1">' +
			'<div class="kt-itw-page-head">' +
			'<div class="kt-itw-page-head-text">' +
			'<h2 class="kt-itw-page-title">' +
			escape_html(options.title || "") +
			"</h2>" +
			(options.subtitle
				? '<p class="kt-itw-page-sub">' + escape_html(options.subtitle) + "</p>"
				: "") +
			"</div>" +
			(actions.length
				? '<div class="kt-itw-page-head-actions">' +
					actions
						.map(function (action) {
							var stub = action.stub ? ' data-itw-home-stub-action="1" disabled' : "";
							return (
								'<button type="button" class="kt-itw-btn kt-itw-btn--' +
								(action.variant || "outline") +
								'"' +
								stub +
								">" +
								escape_html(action.label) +
								"</button>"
							);
						})
						.join("") +
					"</div>"
				: "") +
			"</div>" +
			"</section>"
		);
	}

	function context_strip(fields) {
		fields = fields || [];
		var parts = [];
		fields.forEach(function (field, index) {
			var valueClass = "kt-itw-context-value";
			if (field.mono) {
				valueClass += " kt-itw-mono";
			}
			if (field.tone === "state") {
				valueClass += " kt-itw-context-value--state";
			} else if (field.tone === "danger") {
				valueClass += " kt-itw-context-value--danger";
			} else if (field.tone === "warn") {
				valueClass += " kt-itw-context-value--warn";
			}
			parts.push(
				'<div class="kt-itw-context-cell">' +
					'<span class="kt-itw-context-label">' +
					escape_html(field.label) +
					"</span>" +
					'<span class="' +
					valueClass +
					'">' +
					escape_html(field.value || "—") +
					"</span>" +
					"</div>",
			);
			if (index < fields.length - 1) {
				parts.push('<div class="kt-itw-context-divider" aria-hidden="true"></div>');
			}
		});
		return (
			'<section class="kt-itw-context-strip" data-itw-home-context="1">' + parts.join("") + "</section>"
		);
	}

	function hero_panel(next) {
		next = next || {};
		var heroIcon = next.icon || "memory";
		return (
			'<section class="kt-itw-hero-panel" data-itw-next-action="1">' +
			'<div class="kt-itw-hero-main">' +
			'<div class="kt-itw-hero-icon" aria-hidden="true">' +
			icon(heroIcon) +
			"</div>" +
			'<div class="kt-itw-hero-copy">' +
			'<h2 class="kt-itw-hero-title">' +
			escape_html(__("Next step: {0}", [next.label || ""])) +
			"</h2>" +
			'<p class="kt-itw-hero-reason">' +
			escape_html(__("Reason: {0}", [next.reason || ""])) +
			"</p>" +
			"</div></div>" +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-next-action-route="' +
			escape_html(next.route || "") +
			'">' +
			escape_html(next.button_label || __("Continue")) +
			"</button>" +
			"</section>"
		);
	}

	var STATUS_TONE = {
		Complete: "success",
		"In progress": "info",
		"Needs attention": "danger",
		"Not started": "muted",
		"Available later": "muted",
	};

	function status_chip(status, options) {
		options = options || {};
		var tone = STATUS_TONE[status] || "muted";
		var label = status === "Available later" ? "Available Later" : status || "Not started";
		var lock =
			status === "Available later"
				? icon("lock", "kt-itw-ico--sm") + " "
				: "";
		var pill = options.pill ? " kt-itw-status-chip--pill" : "";
		return (
			'<span class="kt-itw-status-chip kt-itw-status-chip--' +
			tone +
			pill +
			'">' +
			lock +
			escape_html(label) +
			"</span>"
		);
	}

	function format_issue_line(step) {
		var blockers = step.blocker_count || 0;
		var warnings = step.warning_count || 0;
		if (!blockers && !warnings) {
			return "";
		}
		var parts = [];
		if (blockers) {
			parts.push(blockers + " " + (blockers === 1 ? __("Blocker") : __("Blockers")));
		}
		if (warnings) {
			parts.push(warnings + " " + (warnings === 1 ? __("Warning") : __("Warnings")));
		}
		return parts.join(" / ");
	}

	function format_card_issue_line(step) {
		var blockers = step.blocker_count || 0;
		var warnings = step.warning_count || 0;
		var total = blockers + warnings;
		if (!total) {
			return "";
		}
		return total + " " + (total === 1 ? __("Issue") : __("Issues"));
	}

	function step_card(step) {
		var status = step.status_label || "Not started";
		var isCurrent = step.is_current ? "1" : "0";
		var isAvailableLater = status === "Available later";
		var isInProgress = status === "In progress";
		var stepNum = String(step.step_number || 0).padStart(2, "0");
		var issueLine = format_card_issue_line(step);
		var cardClass =
			"kt-itw-step-card" +
			(isInProgress ? " kt-itw-step-card--current" : "") +
			(isAvailableLater ? " kt-itw-step-card--locked" : "");
		var actionBtn = isAvailableLater
			? ""
			: '<button type="button" class="kt-itw-btn kt-itw-btn--sm ' +
				(isInProgress ? "kt-itw-btn--primary" : "kt-itw-btn--outline") +
				'" data-itw-step-action="1">' +
				escape_html(step.action_label || "Start") +
				"</button>";
		var prereqHtml = "";
		if (isAvailableLater && step.availability_reason) {
			prereqHtml =
				'<div class="kt-itw-step-prereq">' +
				escape_html(String(step.availability_reason).toUpperCase()) +
				"</div>";
		}
		return (
			'<div class="' +
			cardClass +
			'" data-itw-step-card="1" data-itw-step-code="' +
			escape_html(step.step_code || "") +
			'" data-itw-step-route="' +
			escape_html(step.route || "") +
			'" data-itw-step-current="' +
			isCurrent +
			'" role="button" tabindex="0" aria-label="' +
			escape_html(__("View {0} details", [step.step_label || "step"])) +
			'">' +
			'<div class="kt-itw-step-card-head">' +
			'<span class="kt-itw-step-num">STEP ' +
			stepNum +
			"</span>" +
			'<div class="kt-itw-step-title-row">' +
			'<h4 class="kt-itw-step-title">' +
			escape_html(step.step_label || "") +
			"</h4>" +
			status_chip(status) +
			"</div></div>" +
			'<p class="kt-itw-step-desc">' +
			escape_html(step.card_description || "") +
			"</p>" +
			(issueLine
				? '<div class="kt-itw-step-issues">' +
					icon("error", "kt-itw-ico--sm") +
					escape_html(issueLine) +
					"</div>"
				: "") +
			actionBtn +
			prereqHtml +
			"</div>"
		);
	}

	function step_grid(steps) {
		if (!steps || !steps.length) {
			return (
				'<div class="kt-itw-step-grid" data-itw-step-grid="1">' +
				'<div class="kt-itw-step-empty">' +
				escape_html(__("No configuration steps found.")) +
				"</div></div>"
			);
		}
		return (
			'<div class="kt-itw-step-grid" data-itw-step-grid="1">' +
			steps.map(step_card).join("") +
			"</div>"
		);
	}

	function step_drawer_shell() {
		return (
			'<div class="kt-itw-drawer-host">' +
			'<div class="kt-itw-drawer-backdrop kt-itw-drawer-backdrop--home" data-itw-home-drawer-overlay="1" hidden></div>' +
			'<aside class="kt-itw-drawer-panel kt-itw-drawer-panel--home" data-itw-home-drawer="1" hidden>' +
			'<div class="kt-itw-drawer-head">' +
			'<div>' +
			'<p class="kt-itw-step-num" data-itw-drawer-step-num="1"></p>' +
			'<h2 class="kt-itw-drawer-title" data-itw-drawer-title="1"></h2>' +
			"</div>" +
			'<button type="button" class="kt-itw-icon-btn kt-itw-icon-btn--round" data-itw-drawer-close="1" aria-label="Close">' +
			icon("close") +
			"</button>" +
			"</div>" +
			'<div class="kt-itw-drawer-body" data-itw-drawer-body="1"></div>' +
			'<div class="kt-itw-drawer-foot">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-drawer-route="1">' +
			escape_html(__("Continue Configuration")) +
			"</button>" +
			'<button type="button" class="kt-itw-btn kt-itw-btn--outline" data-itw-drawer-fix="1" hidden>' +
			escape_html(__("Fix Issues")) +
			"</button>" +
			"</div>" +
			"</aside></div>"
		);
	}

	kentender.it_wizard.components.escape_html = escape_html;
	kentender.it_wizard.components.icon = icon;
	kentender.it_wizard.components.appbar = appbar;
	kentender.it_wizard.components.footer = footer;
	kentender.it_wizard.components.page_header = page_header;
	kentender.it_wizard.components.context_strip = context_strip;
	kentender.it_wizard.components.hero_panel = hero_panel;
	kentender.it_wizard.components.status_chip = status_chip;
	kentender.it_wizard.components.step_grid = step_grid;
	kentender.it_wizard.components.step_drawer_shell = step_drawer_shell;
	kentender.it_wizard.components.format_issue_line = format_issue_line;
	kentender.it_wizard.components.format_card_issue_line = format_card_issue_line;

	var REQ_V2_CATEGORIES = [
		"Business Need",
		"Functional Requirement",
		"Technical Requirement",
		"Security & Compliance",
		"Integration",
		"Implementation & Training",
		"Support & Warranty",
	];

	var REQ_TREATMENTS = ["Mandatory", "Evaluation-linked", "Informational"];

	var REQ_RESPONSE_FORMATS = [
		"Yes/No confirmation",
		"Narrative response",
		"Compliance statement",
		"Completed table",
		"Uploaded document",
		"Not required",
	];

	var REQ_EVIDENCE_LEVELS = ["Evidence required", "Evidence optional", "No evidence required"];

	var REQ_ACCEPTANCE_LEVELS = ["Acceptance defined", "Not applicable"];

	function select_options(values, selected) {
		return values
			.map(function (value) {
				var sel = value === selected ? " selected" : "";
				return "<option" + sel + ">" + escape_html(value) + "</option>";
			})
			.join("");
	}

	function requirements_toolbar() {
		return (
			'<section class="kt-itw-req-toolbar" data-itw-req-toolbar="1">' +
			'<div class="kt-itw-req-search-wrap">' +
			icon("search", "kt-itw-req-search-ico") +
			'<input type="search" class="kt-itw-req-search" data-itw-req-search="1" placeholder="' +
			escape_html(__("Search Requirement ID / Title…")) +
			'">' +
			"</div>" +
			'<button type="button" class="kt-itw-btn kt-itw-btn--outline kt-itw-btn--sm" disabled data-itw-req-stub="1">' +
			icon("filter_list", "kt-itw-ico--sm") +
			escape_html(__("Filters")) +
			"</button>" +
			"</section>"
		);
	}

	function requirements_table_row(row) {
		row = row || {};
		var code = row.display_id || row.requirement_code || "";
		var title = row.title || "";
		var summary = row.description ? row.description.slice(0, 80) : "";
		if (row.description && row.description.length > 80) {
			summary += "…";
		}
		var status = row.status_label_v2 || row.status_label || "";
		return (
			'<tr class="kt-itw-req-row" data-itw-req-row="1" data-itw-req-code="' +
			escape_html(code) +
			'">' +
			'<td class="kt-itw-mono">' +
			escape_html(code) +
			"</td>" +
			"<td><div class=\"kt-itw-req-title\">" +
			escape_html(title) +
			"</div>" +
			(summary ? '<div class="kt-itw-req-summary">' + escape_html(summary) + "</div>" : "") +
			"</td>" +
			"<td>" +
			escape_html(row.v2_category || row.category || "") +
			"</td>" +
			"<td><span class=\"kt-itw-req-pill kt-itw-req-pill--treatment\">" +
			escape_html(row.treatment || row.treatment_label || "") +
			"</span></td>" +
			"<td>" +
			escape_html(row.bidder_response_format || row.response_format_label || "") +
			"</td>" +
			"<td><span class=\"kt-itw-req-pill\">" +
			escape_html(row.evidence_status_label || row.evidence_level_label || "") +
			"</span></td>" +
			"<td><span class=\"kt-itw-req-pill\">" +
			escape_html(row.acceptance_status_label || row.acceptance_label || "") +
			"</span></td>" +
			'<td><span class="kt-itw-req-status ' +
			(status === "Complete" ? "kt-itw-req-status--complete" : "kt-itw-req-status--attention") +
			'">' +
			escape_html(status) +
			"</span></td>" +
			'<td class="kt-itw-req-actions-cell">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--sm kt-itw-btn--ghost" data-itw-req-action="edit">' +
			escape_html(__("Edit")) +
			"</button>" +
			"</td>" +
			"</tr>"
		);
	}

	function requirements_table(rows) {
		rows = rows || [];
		return (
			'<div class="kt-itw-req-table-wrap" data-itw-req-table-host="1">' +
			'<table class="kt-itw-req-table" data-itw-req-table="1">' +
			"<thead><tr>" +
			["ID", "Requirement", "Category", "Treatment", "Bidder Response", "Evidence", "Acceptance", "Status", "Actions"]
				.map(function (label) {
					return "<th>" + escape_html(label) + "</th>";
				})
				.join("") +
			"</tr></thead>" +
			"<tbody>" +
			(rows.length
				? rows.map(requirements_table_row).join("")
				: '<tr><td colspan="9" class="kt-itw-req-empty">' +
					escape_html(__("No requirements found.")) +
					"</td></tr>") +
			"</tbody></table></div>"
		);
	}

	function requirements_guidance(summary, completion) {
		summary = summary || {};
		completion = completion || {};
		var percent = completion.percent || 0;
		var gapLines = [];
		if (summary.mandatory_missing_details_count) {
			gapLines.push(
				String(summary.mandatory_missing_details_count) +
					" " +
					__("Mandatory requirements missing details"),
			);
		}
		if (summary.missing_evidence_instruction_count) {
			gapLines.push(
				String(summary.missing_evidence_instruction_count) +
					" " +
					__("Requirements missing evidence instruction"),
			);
		}
		if (summary.missing_acceptance_expectation_count) {
			gapLines.push(
				String(summary.missing_acceptance_expectation_count) +
					" " +
					__("Requirements missing acceptance expectation"),
			);
		}
		if (summary.missing_bidder_response_instruction_count) {
			gapLines.push(
				String(summary.missing_bidder_response_instruction_count) +
					" " +
					__("Requirements missing bidder response instruction"),
			);
		}
		return (
			'<aside class="kt-itw-req-guidance" data-itw-req-guidance="1">' +
			'<div class="kt-itw-req-guidance-card">' +
			'<div class="kt-itw-req-guidance-head">' +
			icon("info", "kt-itw-ico--sm") +
			"<h3>" +
			escape_html(__("Requirements Guidance")) +
			"</h3></div>" +
			'<p class="kt-itw-req-guidance-copy">' +
			escape_html(
				__(
					"Focus on what bidders must supply, deliver, integrate, support, or prove. Evaluation scores, price lines, submission checklist items, and contract values are configured in later steps.",
				),
			) +
			"</p>" +
			'<div class="kt-itw-req-guidance-progress">' +
			'<div class="kt-itw-req-guidance-progress-label">' +
			"<span>" +
			escape_html(__("Completion")) +
			"</span>" +
			'<span data-itw-req-guidance-completion="1">' +
			String(percent) +
			"%</span></div>" +
			'<div class="kt-itw-req-progress-track"><div class="kt-itw-req-progress-bar" style="width:' +
			String(percent) +
			'%"></div></div></div>' +
			'<ul class="kt-itw-req-guidance-gaps" data-itw-req-guidance-gaps="1">' +
			gapLines
				.map(function (line) {
					return "<li>" + escape_html(line) + "</li>";
				})
				.join("") +
			"</ul>" +
			'<p class="kt-itw-req-guidance-next" data-itw-req-guidance-next="1">' +
			escape_html(__("Implementation Schedule")) +
			"</p></div></aside>"
		);
	}

	function requirements_drawer_shell() {
		return (
			'<div class="kt-itw-req-drawer-backdrop" data-itw-req-drawer-backdrop="1" hidden></div>' +
			'<aside class="kt-itw-req-drawer" data-itw-req-drawer="1" data-itw-req-drawer-hidden="1">' +
			'<header class="kt-itw-req-drawer-head">' +
			'<div><p class="kt-itw-req-drawer-kicker">' +
			escape_html(__("Edit IT Requirement")) +
			'</p><h2 class="kt-itw-req-drawer-title" data-itw-req-drawer-title="1"></h2></div>' +
			'<button type="button" class="kt-itw-icon-btn kt-itw-icon-btn--round" data-itw-req-drawer-close="1" aria-label="Close">' +
			icon("close") +
			"</button></header>" +
			'<div class="kt-itw-req-drawer-body" data-itw-req-drawer-body="1"></div>' +
			'<footer class="kt-itw-req-drawer-foot">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--outline" data-itw-req-drawer-cancel="1">' +
			escape_html(__("Cancel")) +
			"</button>" +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-req-drawer-save="1">' +
			escape_html(__("Update Requirement")) +
			"</button></footer></aside>"
		);
	}

	function requirements_drawer_fields(item) {
		item = item || {};
		return (
			'<section class="kt-itw-req-drawer-section"><h3>Section A — Requirement</h3>' +
			'<label class="kt-itw-field-label">Requirement ID</label>' +
			'<div class="kt-itw-field-readonly" data-itw-field="requirement_code">' +
			escape_html(item.requirement_code || item.display_id || "—") +
			"</div>" +
			'<label class="kt-itw-field-label">Requirement Title</label>' +
			'<input class="kt-itw-field-input" data-itw-field="title" value="' +
			escape_html(item.title || "") +
			'">' +
			'<label class="kt-itw-field-label">Requirement Description</label>' +
			'<textarea class="kt-itw-field-input" data-itw-field="description" rows="4">' +
			escape_html(item.description || "") +
			"</textarea>" +
			'<label class="kt-itw-field-label">Category</label>' +
			'<select class="kt-itw-field-input" data-itw-field="category">' +
			select_options(REQ_V2_CATEGORIES, item.v2_category || item.category) +
			"</select>" +
			'<label class="kt-itw-field-label">Treatment</label>' +
			'<select class="kt-itw-field-input" data-itw-field="treatment">' +
			select_options(REQ_TREATMENTS, item.treatment) +
			"</select></section>" +
			'<section class="kt-itw-req-drawer-section"><h3>Section B — Bidder Response</h3>' +
			'<label class="kt-itw-field-label">Bidder Response Format</label>' +
			'<select class="kt-itw-field-input" data-itw-field="response_format">' +
			select_options(REQ_RESPONSE_FORMATS, item.bidder_response_format) +
			"</select>" +
			'<label class="kt-itw-field-label">Bidder Response Instruction</label>' +
			'<textarea class="kt-itw-field-input" data-itw-field="bidder_instruction" rows="3">' +
			escape_html(item.bidder_response_instruction || item.bidder_instruction || "") +
			"</textarea></section>" +
			'<section class="kt-itw-req-drawer-section"><h3>Section C — Evidence</h3>' +
			'<label class="kt-itw-field-label">Evidence Requirement</label>' +
			'<select class="kt-itw-field-input" data-itw-field="evidence_level">' +
			select_options(REQ_EVIDENCE_LEVELS, item.evidence_requirement || item.evidence_status_label) +
			"</select>" +
			'<label class="kt-itw-field-label">Evidence Instruction</label>' +
			'<textarea class="kt-itw-field-input" data-itw-field="evidence_instruction" rows="3">' +
			escape_html(item.evidence_instruction || "") +
			"</textarea></section>" +
			'<section class="kt-itw-req-drawer-section"><h3>Section D — Acceptance</h3>' +
			'<label class="kt-itw-field-label">Acceptance Expectation</label>' +
			'<select class="kt-itw-field-input" data-itw-field="acceptance_expectation">' +
			select_options(REQ_ACCEPTANCE_LEVELS, item.acceptance_expectation || item.acceptance_status_label) +
			"</select>" +
			'<label class="kt-itw-field-label">Acceptance Description</label>' +
			'<textarea class="kt-itw-field-input" data-itw-field="acceptance_criteria" rows="3">' +
			escape_html(item.acceptance_description || item.acceptance_criteria || "") +
			"</textarea></section>" +
			'<section class="kt-itw-req-drawer-section"><h3>References</h3>' +
			'<div class="kt-itw-req-ref-panel">' +
			'<p data-itw-field="evaluation_reference">' +
			escape_html(__("Evaluation Setup")) +
			": <strong>" +
			escape_html(item.evaluation_reference_label || "—") +
			"</strong></p>" +
			'<p data-itw-field="forms_evidence_reference">' +
			escape_html(__("Forms & Evidence")) +
			": <strong>" +
			escape_html(item.forms_evidence_reference_label || "—") +
			"</strong></p>" +
			'<p data-itw-field="contract_values_reference">' +
			escape_html(__("Contract Values")) +
			": <strong>" +
			escape_html(item.contract_values_reference_label || "—") +
			"</strong></p></div></section>"
		);
	}

	function requirements_action_bar(options) {
		options = options || {};
		var continueDisabled = options.continue_disabled ? " disabled" : "";
		return (
			'<footer class="kt-itw-req-actions" data-itw-req-actions="1">' +
			'<div class="kt-itw-req-actions-inner">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--outline" data-itw-req-save-all="1">' +
			escape_html(__("Save Requirements")) +
			"</button>" +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-req-continue="1"' +
			continueDisabled +
			">" +
			escape_html(__("Continue to Implementation Schedule")) +
			icon("arrow_forward", "kt-itw-ico--sm") +
			"</button></div></footer>"
		);
	}

	kentender.it_wizard.components.requirements_toolbar = requirements_toolbar;
	kentender.it_wizard.components.requirements_table = requirements_table;
	kentender.it_wizard.components.requirements_guidance = requirements_guidance;
	kentender.it_wizard.components.requirements_drawer_shell = requirements_drawer_shell;
	kentender.it_wizard.components.requirements_drawer_fields = requirements_drawer_fields;
	kentender.it_wizard.components.requirements_action_bar = requirements_action_bar;
})();
