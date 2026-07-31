// PUB-A3 — Publication Setup (v7 + A3 mock layout).
// Route: /desk/publication-setup/<publication_id>
(function () {
	"use strict";

	var SURFACE_ID = "PUB-A3";
	var PAGE_SLUG = "publication-setup";
	var GET_API = "kentender_procurement.tender_configurations.get_publication_setup";
	var SAVE_API = "kentender_procurement.tender_configurations.save_publication_setup";
	var PUBLISH_API = "kentender_procurement.tender_configurations.publish_tender";
	var RETURN_API =
		"kentender_procurement.tender_configurations.return_publication_for_correction";
	var STORAGE_KEY = "kt_cl_pub_a3_publication_id";

	var VISIBILITY_OPTIONS = [
		{ value: "", label: __("Select visibility") },
		{ value: "All Registered Bidders", label: __("Public Open Tender") },
		{ value: "Invited Bidders Only", label: __("Restricted Tender (Pre-qualified)") },
		{ value: "Public Notice Only", label: __("Public Notice Only") },
	];

	var state = {
		payload: null,
		publicationId: null,
		mounting: false,
		busy: false,
		form: {},
	};

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function publicationId() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		if (frappe.route_options && frappe.route_options.publication_id) {
			return String(frappe.route_options.publication_id).trim();
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("publication_id")) {
				return String(params.get("publication_id")).trim();
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

	function enterSurface() {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.enterNative !== "function" || !surf) {
			return;
		}
		sh.enterNative({
			sidebarWorkspaceKey: surf.sidebarWorkspaceKey || "procurement",
			toolbar: (surf.chrome && surf.chrome.toolbar) || {},
			chrome: surf.chrome,
		});
	}

	function toInputDt(value) {
		if (!value) {
			return "";
		}
		var s = String(value).replace(" ", "T");
		if (s.length >= 16) {
			return s.slice(0, 16);
		}
		return s;
	}

	function formatDisplayDt(value) {
		if (!value) {
			return "";
		}
		var s = String(value).replace("T", " ");
		if (s.length >= 16) {
			return s.slice(0, 16);
		}
		return s;
	}

	function looksLikeHashId(value) {
		var s = String(value || "").trim();
		if (!s || s.length < 8 || s.length > 12) {
			return false;
		}
		if (s.indexOf("-") >= 0 || s.indexOf("_") >= 0 || s.indexOf(" ") >= 0) {
			return false;
		}
		return /^[a-z0-9]+$/i.test(s) && /[a-z]/i.test(s) && /\d/.test(s);
	}

	function fromInputDt(value) {
		if (!value) {
			return "";
		}
		return String(value).replace("T", " ") + (String(value).length === 16 ? ":00" : "");
	}

	function nowInputDt() {
		var d = new Date();
		var pad = function (n) {
			return String(n).padStart(2, "0");
		};
		return (
			d.getFullYear() +
			"-" +
			pad(d.getMonth() + 1) +
			"-" +
			pad(d.getDate()) +
			"T" +
			pad(d.getHours()) +
			":" +
			pad(d.getMinutes())
		);
	}

	function inferPublicationMode(data) {
		var f = (data && data.fields) || {};
		var explicit = String(f.publication_mode || "").toLowerCase();
		if (explicit === "scheduled" || explicit === "immediate") {
			return explicit;
		}
		// Never infer "scheduled" from a stamped publication_datetime after publish —
		// immediate publish also sets a datetime.
		if ((data && data.status) === "Scheduled") {
			return "scheduled";
		}
		return "immediate";
	}

	function syncFormFromPayload(data) {
		var f = (data && data.fields) || {};
		var mode = inferPublicationMode(data);
		state.form = {
			publication_mode: mode,
			publication_datetime: f.publication_datetime || "",
			tender_notice: f.tender_notice || "",
			clarification_deadline: f.clarification_deadline || "",
			submission_deadline: f.submission_deadline || "",
			opening_datetime: f.opening_datetime || "",
			bidder_visibility: f.bidder_visibility || "",
			activate_bidder_workspace: f.activate_bidder_workspace ? 1 : 0,
		};
	}

	function readForm($root) {
		var mode = $root.find('input[name="publication_mode"]:checked').val() || "immediate";
		var pubDt = fromInputDt($root.find('[name="publication_datetime"]').val());
		if (mode === "immediate" && !pubDt) {
			pubDt = fromInputDt(nowInputDt());
		}
		return {
			publication_mode: mode,
			publication_datetime: pubDt,
			tender_notice: $root.find('[name="tender_notice"]').val() || "",
			clarification_deadline: fromInputDt($root.find('[name="clarification_deadline"]').val()),
			submission_deadline: fromInputDt($root.find('[name="submission_deadline"]').val()),
			opening_datetime: fromInputDt($root.find('[name="opening_datetime"]').val()),
			bidder_visibility: $root.find('[name="bidder_visibility"]').val() || "",
			activate_bidder_workspace: $root.find('[name="activate_bidder_workspace"]').is(":checked")
				? 1
				: 0,
		};
	}

	function computeValidation(form) {
		var checks = [];
		if (!(form.tender_notice || "").trim()) {
			checks.push({
				severity: "blocker",
				message: __("Public notice text is required for website synchronization."),
				status: __("Missing Content"),
			});
		}
		if (!(form.submission_deadline || "").trim()) {
			checks.push({
				severity: "blocker",
				message: __("Set the submission deadline before publishing."),
				status: __("Missing"),
			});
		}
		if (!(form.opening_datetime || "").trim()) {
			checks.push({
				severity: "blocker",
				message: __("Set the opening date and time before publishing."),
				status: __("Missing"),
			});
		}
		if (!(form.bidder_visibility || "").trim()) {
			checks.push({
				severity: "blocker",
				message: __("Select who can view this tender after publication."),
				status: __("Missing"),
			});
		}
		if (!form.activate_bidder_workspace) {
			checks.push({
				severity: "blocker",
				message: __("Activate the electronic bidder workspace before publishing."),
				status: __("Required"),
			});
		}
		if (form.publication_mode === "scheduled" && !(form.publication_datetime || "").trim()) {
			checks.push({
				severity: "blocker",
				message: __("Future publication date/time required."),
				status: __("Missing"),
			});
		}
		// Server publish gates (package integrity + platform electronic STD template approval).
		var serverBlockers = (state.payload && state.payload.publish_blockers) || [];
		for (var i = 0; i < serverBlockers.length; i++) {
			var msg = String(serverBlockers[i] || "").trim();
			if (!msg) {
				continue;
			}
			checks.push({
				severity: "blocker",
				message: __(msg),
				status: __("Blocked"),
			});
		}
		if (!checks.length) {
			checks.push({
				severity: "ok",
				message: __("Publication setup fields pass the current validation checks."),
				status: __("Ready"),
			});
		}
		return checks;
	}

	function emptyHtml() {
		return (
			'<div class="kt-cl-pub-a3-empty" data-testid="kt-cl-pub-a3-root">' +
			"<p>" +
			__("Select a publication from the Publications queue.") +
			"</p>" +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--secondary" data-action="back-queue">' +
			__("Back to Publications") +
			"</button></div>"
		);
	}

	function publicationStrip(data) {
		var ctx = data.publication_context || {};
		var form = state.form || {};
		var pending = computeValidation(form).filter(function (c) {
			return c.severity === "blocker";
		}).length;
		var statusLabel = ctx.status_label || data.status || "—";
		var pubRef = ctx.publication_ref || data.publication_ref || "";
		if (!pubRef || looksLikeHashId(pubRef)) {
			pubRef = data.configuration_ref || "—";
		}
		var pkg = data.confirmed_package || {};
		var pkgRef =
			ctx.doc_package_ref ||
			pkg.package_code ||
			pkg.procurement_package_ref ||
			pkg.configuration_ref ||
			data.configuration_ref ||
			"";
		if (!pkgRef || looksLikeHashId(pkgRef)) {
			pkgRef = data.configuration_ref || "—";
		}
		var cells = [
			{ key: "pub-ref", label: __("Publication Ref"), value: pubRef },
			{
				key: "pkg-ref",
				label: __("Doc Package Ref"),
				value: pkgRef,
			},
			{ key: "pe", label: __("PE"), value: ctx.procuring_entity_name || data.procuring_entity || "—" },
			{
				key: "std",
				label: __("STD"),
				value: ctx.std_label || data.standard_tender_document || "—",
			},
			{ key: "status", label: __("Status"), value: statusLabel, status: true },
			{
				key: "validation",
				label: __("Validation"),
				value: pending ? pending + " " + __("Pending") : __("Ready"),
				alert: pending > 0,
			},
		];
		var html = cells
			.map(function (cell) {
				var valueHtml = cell.status
					? '<div class="kt-cl-pub-a3-strip-status" data-testid="kt-cl-pub-a3-status"><span class="kt-cl-pub-a3-strip-dot" aria-hidden="true"></span><span>' +
						esc(cell.value) +
						"</span></div>"
					: '<p class="kt-cl-pub-a3-strip-value' +
						(cell.alert ? " is-alert" : "") +
						'">' +
						esc(cell.value) +
						"</p>";
				return (
					'<div class="kt-cl-pub-a3-strip-cell" data-testid="kt-cl-pub-a3-strip-' +
					esc(cell.key) +
					'">' +
					'<p class="kt-cl-pub-a3-strip-label">' +
					esc(cell.label) +
					"</p>" +
					valueHtml +
					"</div>"
				);
			})
			.join("");
		return (
			'<section class="kt-cl-pub-a3-strip" data-testid="kt-cl-pub-a3-context-strip">' +
			'<div class="kt-cl-pub-a3-strip-grid">' +
			html +
			"</div></section>"
		);
	}

	function fieldBlock(label, name, type, value, helper, opts) {
		opts = opts || {};
		var disabled = opts.disabled ? " disabled" : "";
		var required = opts.required ? ' <span class="kt-cl-pub-a3-req">*</span>' : "";
		var input;
		if (type === "textarea") {
			input =
				'<textarea class="kt-cl-pub-a3-input" name="' +
				esc(name) +
				'" rows="6" placeholder="' +
				esc(opts.placeholder || "") +
				'" data-testid="kt-cl-pub-a3-field-' +
				esc(name) +
				'"' +
				disabled +
				">" +
				esc(value || "") +
				"</textarea>";
		} else if (type === "select") {
			var options = (opts.options || [])
				.map(function (o) {
					return (
						'<option value="' +
						esc(o.value) +
						'"' +
						(o.value === value ? " selected" : "") +
						">" +
						esc(o.label) +
						"</option>"
					);
				})
				.join("");
			input =
				'<select class="kt-cl-pub-a3-input" name="' +
				esc(name) +
				'" data-testid="kt-cl-pub-a3-field-' +
				esc(name) +
				'"' +
				disabled +
				">" +
				options +
				"</select>";
		} else {
			input =
				'<input class="kt-cl-pub-a3-input" type="' +
				esc(type) +
				'" name="' +
				esc(name) +
				'" value="' +
				esc(value || "") +
				'" data-testid="kt-cl-pub-a3-field-' +
				esc(name) +
				'"' +
				disabled +
				" />";
		}
		return (
			'<div class="kt-cl-pub-a3-field">' +
			'<label class="kt-cl-pub-a3-label">' +
			esc(label) +
			required +
			"</label>" +
			input +
			(helper ? '<p class="kt-cl-pub-a3-helper">' + esc(helper) + "</p>" : "") +
			"</div>"
		);
	}

	function publicationDatetimeBlock(data) {
		var f = state.form || {};
		var locked = !data.editable || data.setup_locked;
		var immediate = f.publication_mode !== "scheduled";
		var stamped = f.publication_datetime || data.published_at || "";
		var showStamp = !!(stamped && (locked || data.status === "Published" || data.status === "Ready to Publish"));
		if (!immediate) {
			return fieldBlock(
				__("Publication Date/Time"),
				"publication_datetime",
				"datetime-local",
				toInputDt(f.publication_datetime),
				__("Set when this tender becomes visible to bidders."),
				{ disabled: locked, required: true }
			);
		}
		var readonlyLabel = showStamp
			? formatDisplayDt(stamped)
			: __("On publish action (Immediate)");
		return (
			'<div class="kt-cl-pub-a3-field"><label class="kt-cl-pub-a3-label">' +
			__("Publication Date/Time") +
			' <span class="kt-cl-pub-a3-req">*</span></label>' +
			'<div class="kt-cl-pub-a3-readonly" data-testid="kt-cl-pub-a3-field-publication_datetime_readonly">' +
			esc(readonlyLabel) +
			"</div>" +
			'<input type="hidden" name="publication_datetime" value="' +
			esc(toInputDt(stamped)) +
			'" data-testid="kt-cl-pub-a3-field-publication_datetime" />' +
			'<p class="kt-cl-pub-a3-helper">' +
			(showStamp
				? __("Effective date and time when this tender became visible to bidders.")
				: __("Set when this tender becomes visible to bidders.")) +
			"</p></div>"
		);
	}

	function formColumn(data) {
		var f = state.form || {};
		var locked = !data.editable || data.setup_locked;
		var immediate = f.publication_mode !== "scheduled";
		return (
			'<div class="kt-cl-pub-a3-main" data-testid="kt-cl-pub-a3-form">' +
			'<section class="kt-cl-pub-a3-card">' +
			'<div class="kt-cl-pub-a3-card-head">' +
			'<span class="material-symbols-outlined">calendar_month</span>' +
			"<h2>" +
			__("Publication Timelines") +
			"</h2></div>" +
			'<div class="kt-cl-pub-a3-mode" data-testid="kt-cl-pub-a3-mode">' +
			'<p class="kt-cl-pub-a3-label">' +
			__("Publication Mode") +
			' <span class="kt-cl-pub-a3-req">*</span></p>' +
			'<div class="kt-cl-pub-a3-mode-row">' +
			'<label class="kt-cl-pub-a3-radio"><input type="radio" name="publication_mode" value="immediate" data-action="toggle-mode"' +
			(immediate ? " checked" : "") +
			(locked ? " disabled" : "") +
			" /><span>" +
			__("Publish immediately") +
			"</span></label>" +
			'<label class="kt-cl-pub-a3-radio"><input type="radio" name="publication_mode" value="scheduled" data-action="toggle-mode"' +
			(!immediate ? " checked" : "") +
			(locked ? " disabled" : "") +
			" /><span>" +
			__("Schedule publication") +
			"</span></label></div></div>" +
			'<div class="kt-cl-pub-a3-field-grid">' +
			publicationDatetimeBlock(data) +
			fieldBlock(
				__("Clarification Deadline"),
				"clarification_deadline",
				"datetime-local",
				toInputDt(f.clarification_deadline),
				__("Last date for bidders to request clarifications."),
				{ disabled: locked }
			) +
			fieldBlock(
				__("Submission Deadline"),
				"submission_deadline",
				"datetime-local",
				toInputDt(f.submission_deadline),
				__("Closing date for receiving electronic bids."),
				{ disabled: locked, required: true }
			) +
			fieldBlock(
				__("Opening Date/Time"),
				"opening_datetime",
				"datetime-local",
				toInputDt(f.opening_datetime),
				__("Set when submitted bids may be opened."),
				{ disabled: locked, required: true }
			) +
			"</div></section>" +
			'<section class="kt-cl-pub-a3-card">' +
			'<div class="kt-cl-pub-a3-card-head">' +
			'<span class="material-symbols-outlined">description</span>' +
			"<h2>" +
			__("Tender Notice & Description") +
			"</h2></div>" +
			fieldBlock(
				__("Public Tender Notice"),
				"tender_notice",
				"textarea",
				f.tender_notice,
				__("This text will appear on the public portal when the tender is published."),
				{
					disabled: locked,
					required: true,
					placeholder: __("Enter the official text that will appear on the public portal..."),
				}
			) +
			"</section>" +
			'<div class="kt-cl-pub-a3-split">' +
			'<section class="kt-cl-pub-a3-card">' +
			'<div class="kt-cl-pub-a3-card-head">' +
			'<span class="material-symbols-outlined">visibility</span>' +
			"<h2>" +
			__("Bidder Visibility") +
			"</h2></div>" +
			fieldBlock(
				__("Visibility Scope"),
				"bidder_visibility",
				"select",
				f.bidder_visibility,
				__("Choose who can view the tender after publication."),
				{ disabled: locked, options: VISIBILITY_OPTIONS, required: true }
			) +
			"</section>" +
			'<section class="kt-cl-pub-a3-card" data-testid="kt-cl-pub-a3-workspace">' +
			'<div class="kt-cl-pub-a3-card-head">' +
			'<span class="material-symbols-outlined">hub</span>' +
			"<h2>" +
			__("Bidder Workspace") +
			"</h2></div>" +
			'<div class="kt-cl-pub-a3-workspace-card">' +
			'<div class="kt-cl-pub-a3-workspace-row">' +
			"<div><p class=\"kt-cl-pub-a3-strip-label\">" +
			__("Bidder Workspace Status") +
			'</p><p class="kt-cl-pub-a3-workspace-ready">' +
			__("Prepared") +
			"</p></div>" +
			"<div><p class=\"kt-cl-pub-a3-strip-label\">" +
			__("Activate Bidder Workspace") +
			'</p><label class="kt-cl-pub-a3-switch">' +
			'<input type="checkbox" name="activate_bidder_workspace" data-testid="kt-cl-pub-a3-field-activate_bidder_workspace"' +
			(f.activate_bidder_workspace ? " checked" : "") +
			(locked ? " disabled" : "") +
			' /><span class="kt-cl-pub-a3-switch-ui"></span></label></div></div>' +
			'<p class="kt-cl-pub-a3-helper">' +
			__(
				"Enable bidders to view the confirmed tender package, complete required forms, upload evidence, enter prices, and submit bids electronically."
			) +
			"</p></div></section></div></div>"
		);
	}

	function assetsRail(data) {
		var links = (data && data.context_links) || {};
		var pkg = (data && data.confirmed_package) || {};
		return (
			'<aside class="kt-cl-pub-a3-rail">' +
			'<section class="kt-cl-pub-a3-card kt-cl-pub-a3-card--rail" data-testid="kt-cl-pub-a3-assets">' +
			'<div class="kt-cl-pub-a3-rail-head">' +
			'<span class="material-symbols-outlined">attachment</span>' +
			"<h3>" +
			__("Referenced Assets") +
			"</h3></div>" +
			'<button type="button" class="kt-cl-pub-a3-asset" data-action="view-package" data-testid="kt-cl-pub-a3-view-package">' +
			'<span class="material-symbols-outlined">inventory_2</span><span>' +
			__("Confirmed Package") +
			'</span><span class="material-symbols-outlined">open_in_new</span></button>' +
			'<button type="button" class="kt-cl-pub-a3-asset" data-action="view-document" data-testid="kt-cl-pub-a3-view-document">' +
			'<span class="material-symbols-outlined">picture_as_pdf</span><span>' +
			__("Official Tender Doc") +
			'</span><span class="material-symbols-outlined">download</span></button>' +
			'<div class="kt-cl-pub-a3-asset is-static"><span class="material-symbols-outlined">schema</span><span>' +
			__("Package hash") +
			"</span><span class=\"kt-cl-pub-a3-hash\">" +
			esc((pkg.document_hash || data.document_hash || "").slice(0, 12) || "—") +
			"</span></div>" +
			'<p class="hidden" data-view-package="' +
			esc(links.view_package_route || "") +
			'" data-view-document="' +
			esc(links.view_document_route || "") +
			'"></p></section>' +
			validationRail() +
			"</aside>"
		);
	}

	function validationRail() {
		var checks = computeValidation(state.form || {});
		var items = checks
			.map(function (c) {
				return (
					'<div class="kt-cl-pub-a3-val-item" data-severity="' +
					esc(c.severity) +
					'">' +
					'<span class="kt-cl-pub-a3-val-dot"></span><div><p>' +
					esc(c.message) +
					'</p><span class="kt-cl-pub-a3-val-status">' +
					esc(__("Status: {0}", [c.status])) +
					"</span></div></div>"
				);
			})
			.join("");
		return (
			'<section class="kt-cl-pub-a3-card kt-cl-pub-a3-card--rail" data-testid="kt-cl-pub-a3-validation">' +
			'<div class="kt-cl-pub-a3-rail-head kt-cl-pub-a3-rail-head--error">' +
			'<span class="material-symbols-outlined">report</span>' +
			"<h3>" +
			__("Validation Checks") +
			"</h3></div>" +
			'<div class="kt-cl-pub-a3-val-list">' +
			items +
			"</div></section>"
		);
	}

	function footerHtml(data) {
		var editable = !!(data && data.editable) && !state.busy;
		var canPublish = !!(data && data.can_publish) && !state.busy;
		var canReturn = !!(data && data.can_return) && !state.busy;
		var published = (data && data.status) === "Published";
		var mode = (state.form && state.form.publication_mode) || "immediate";
		var publishLabel = mode === "scheduled" ? __("Schedule Tender") : __("Publish Tender");
		return (
			'<div class="kt-cl-pub-a3-footer" data-testid="kt-cl-pub-a3-footer">' +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--secondary" data-action="back-queue" data-testid="kt-cl-pub-a3-back-queue">' +
			__("Back to Publications") +
			"</button>" +
			'<div class="kt-cl-pub-a3-footer-end">' +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--secondary" data-action="return-correction" data-testid="kt-cl-pub-a3-return"' +
			(canReturn && !published ? "" : " disabled") +
			">" +
			__("Return for Correction") +
			"</button>" +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--outline" data-action="save-setup" data-testid="kt-cl-pub-a3-save"' +
			(editable ? "" : " disabled") +
			">" +
			__("Save Setup") +
			"</button>" +
			'<button type="button" class="kt-cl-pub-a3-btn kt-cl-pub-a3-btn--primary" data-action="publish-tender" data-testid="kt-cl-pub-a3-publish"' +
			(canPublish ? "" : " disabled") +
			'><span class="material-symbols-outlined">' +
			(mode === "scheduled" ? "event_available" : "send") +
			"</span>" +
			esc(publishLabel) +
			"</button></div></div>"
		);
	}

	function pageHtml(data) {
		return (
			'<div data-testid="kt-cl-pub-a3-root" data-publication-id="' +
			esc(data.publication_id || "") +
			'">' +
			publicationStrip(data) +
			'<div class="kt-cl-pub-a3-layout" data-testid="kt-cl-pub-a3-layout">' +
			formColumn(data) +
			assetsRail(data) +
			"</div>" +
			footerHtml(data) +
			"</div>"
		);
	}

	function saveSetup(page, $root) {
		if (state.busy || !state.publicationId) {
			return;
		}
		var payload = readForm($root);
		state.form = payload;
		state.busy = true;
		remount(page);
		frappe.call({
			method: SAVE_API,
			args: { publication_id: state.publicationId, payload: payload },
			callback: function (r) {
				state.busy = false;
				state.payload = r.message || state.payload;
				syncFormFromPayload(state.payload);
				remount(page);
				frappe.show_alert({ message: __("Publication setup saved"), indicator: "green" }, 4);
			},
			error: function () {
				state.busy = false;
				remount(page);
			},
		});
	}

	function publishTender(page) {
		if (state.busy || !state.publicationId) {
			return;
		}
		kentender_core.cl.confirm({
			title: __("Publish Tender?"),
			message: __(
				"This will make the tender visible to bidders and activate the electronic bidder workspace. " +
					"This action does not open bids, evaluate bids, approve an award, or create a contract."
			),
			confirmLabel: __("Publish Tender"),
			cancelLabel: __("Cancel"),
			onConfirm: function () {
				state.busy = true;
				remount(page);
				frappe.call({
					method: PUBLISH_API,
					args: { publication_id: state.publicationId },
					callback: function (r) {
						state.busy = false;
						if (r && r.exc) {
							// Exception dialog already shown; reload setup so READY is not false-positive.
							frappe.call({
								method: GET_API,
								args: { publication_id: state.publicationId },
								callback: function (gr) {
									if (gr && gr.message) {
										state.payload = gr.message;
										syncFormFromPayload(state.payload);
									}
									remount(page);
								},
								error: function () {
									remount(page);
								},
							});
							return;
						}
						state.payload = r.message || state.payload;
						syncFormFromPayload(state.payload);
						remount(page);
						frappe.show_alert({ message: __("Tender published"), indicator: "green" }, 5);
					},
					error: function () {
						state.busy = false;
						frappe.call({
							method: GET_API,
							args: { publication_id: state.publicationId },
							callback: function (gr) {
								if (gr && gr.message) {
									state.payload = gr.message;
									syncFormFromPayload(state.payload);
								}
								remount(page);
							},
							error: function () {
								remount(page);
							},
						});
					},
				});
			},
		});
	}

	function returnForCorrection(page) {
		if (state.busy || !state.publicationId) {
			return;
		}
		kentender_core.cl.confirm({
			title: __("Return for Correction?"),
			message: __(
				"This will return the tender to Tender Configurations for correction. " +
					"A new readiness check, review approval, electronic tender package review, and package confirmation will be required before publication."
			),
			confirmLabel: __("Return for Correction"),
			cancelLabel: __("Cancel"),
			onConfirm: function () {
				var reason = window.prompt(__("Reason for return"), "") || "";
				if (!reason.trim()) {
					frappe.msgprint(__("A reason for return is required."));
					return;
				}
				state.busy = true;
				remount(page);
				frappe.call({
					method: RETURN_API,
					args: { publication_id: state.publicationId, payload: { reason: reason } },
					callback: function () {
						state.busy = false;
						frappe.show_alert({ message: __("Returned for correction"), indicator: "orange" }, 5);
						frappe.set_route("publications");
					},
					error: function () {
						state.busy = false;
						remount(page);
					},
				});
			},
		});
	}

	function bind($root, page) {
		$root.off(".puba3");
		$root.on("click.puba3", "[data-action='back-queue']", function (e) {
			e.preventDefault();
			frappe.set_route("publications");
		});
		$root.on("click.puba3", "[data-action='view-package']", function (e) {
			e.preventDefault();
			var route = ($root.find("[data-view-package]").attr("data-view-package") || "").split("/");
			if (route.length >= 2) {
				frappe.set_route(route[0], route[1]);
			} else if (state.payload && state.payload.configuration_id) {
				frappe.set_route("it-tender-package-review", state.payload.configuration_id);
			}
		});
		$root.on("click.puba3", "[data-action='view-document']", function (e) {
			e.preventDefault();
			var route = ($root.find("[data-view-document]").attr("data-view-document") || "").split(
				"/"
			);
			if (route.length >= 2) {
				frappe.set_route(route[0], route[1]);
			} else if (state.payload && state.payload.configuration_id) {
				frappe.set_route(
					"it-tender-configuration-render-preview",
					state.payload.configuration_id
				);
			}
		});
		$root.on("change.puba3", "[data-action='toggle-mode']", function () {
			state.form = readForm($root);
			remount(page);
		});
		$root.on("change.puba3 input.puba3", "input, textarea, select", function () {
			state.form = Object.assign(state.form || {}, readForm($root));
		});
		$root.on("click.puba3", "[data-action='save-setup']", function (e) {
			e.preventDefault();
			saveSetup(page, $root);
		});
		$root.on("click.puba3", "[data-action='publish-tender']", function (e) {
			e.preventDefault();
			publishTender(page);
		});
		$root.on("click.puba3", "[data-action='return-correction']", function (e) {
			e.preventDefault();
			returnForCorrection(page);
		});
	}

	function remount(page) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		enterSurface();
		var pageHeader =
			(surf && surf.chrome && surf.chrome.pageHeader) || {
				title: __("Publication Setup"),
				hideBreadcrumbs: true,
			};
		if (surf && surf.chrome && surf.chrome.toolbar && typeof sh.updateChrome === "function") {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}
		sh.mountContent(page.main, {
			pageHeader: pageHeader,
			mainHtml: state.payload ? pageHtml(state.payload) : emptyHtml(),
		});
		bind($(page.main), page);
	}

	function mount(page) {
		if (state.mounting) {
			return;
		}
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		enterSurface();
		var id = publicationId();
		state.publicationId = id;
		if (!id) {
			state.payload = null;
			remount(page);
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
			args: { publication_id: id },
			callback: function (r) {
				state.payload = r.message || null;
				syncFormFromPayload(state.payload);
				remount(page);
			},
			error: function () {
				state.payload = null;
				remount(page);
			},
		});
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Publication Setup"),
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
