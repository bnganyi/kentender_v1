(function () {
	"use strict";

	frappe.provide("kentender.it_wizard");

	var API = "kentender_procurement.it_tender_wizard.api.instance_api";
	var PROCUREMENT_SIDEBAR_KEY = "Procurement";

	function call_api(method, args) {
		return frappe.call({
			method: API + "." + method,
			args: args || {},
		});
	}

	function preserve_procurement_sidebar() {
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup(PROCUREMENT_SIDEBAR_KEY);
		}
	}

	function read_route_context() {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		var opts = root.frappe.route_options || {};
		var params = new URLSearchParams(root.location && root.location.search ? root.location.search : "");
		function pick(key) {
			return (opts[key] || params.get(key) || "").trim();
		}
		return {
			configuration_id: pick("configuration_id"),
			procurement_package_id: pick("procurement_package_id"),
			tender_id: pick("tender_id"),
			std_version_id: pick("std_version_id"),
			plan_item_id: pick("plan_item_id"),
			procurement_entity_id: pick("procurement_entity_id"),
		};
	}

	function set_route_context(ctx) {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		root.frappe.route_options = Object.assign({}, root.frappe.route_options || {}, ctx || {});
	}

	var ITW_REGISTERED_ROUTES = [
		"it-tender-configuration-dashboard",
		"it-tender-configuration-overview",
		"it-tender-configuration-tender-profile",
		"it-tender-configuration-tds",
		"it-tender-configuration-it-requirements",
		"it-tender-configuration-implementation-schedule",
		"it-tender-configuration-system-inventory",
		"it-tender-configuration-price-schedule",
		"it-tender-configuration-evaluation-setup",
		"it-tender-configuration-forms-and-evidence",
		"it-tender-configuration-scc",
		"it-tender-configuration-validation-report",
		"it-tender-configuration-review-and-approval",
		"it-tender-configuration-render-preview",
		"it-tender-configuration-publication-readiness",
	];

	var STEP_ROUTE_MAP = {
		TENDER_PROFILE: "it-tender-configuration-tender-profile",
		TDS: "it-tender-configuration-tds",
		IT_REQUIREMENTS: "it-tender-configuration-it-requirements",
		IMPLEMENTATION_SCHEDULE: "it-tender-configuration-implementation-schedule",
		SYSTEM_INVENTORY: "it-tender-configuration-system-inventory",
		PRICE_SCHEDULE: "it-tender-configuration-price-schedule",
		EVALUATION_SETUP: "it-tender-configuration-evaluation-setup",
		FORMS_AND_EVIDENCE: "it-tender-configuration-forms-and-evidence",
		SCC: "it-tender-configuration-scc",
		VALIDATION_REPORT: "it-tender-configuration-validation-report",
		REVIEW_AND_APPROVAL: "it-tender-configuration-review-and-approval",
		RENDER_PREVIEW: "it-tender-configuration-render-preview",
		PUBLICATION_READINESS: "it-tender-configuration-publication-readiness",
	};

	var CONFIGURATION_CONTEXT_ROUTES = {
		"it-tender-configuration-overview": 1,
		"it-tender-configuration-tender-profile": 1,
		"it-tender-configuration-tds": 1,
		"it-tender-configuration-it-requirements": 1,
		"it-tender-configuration-implementation-schedule": 1,
		"it-tender-configuration-system-inventory": 1,
		"it-tender-configuration-price-schedule": 1,
		"it-tender-configuration-evaluation-setup": 1,
		"it-tender-configuration-forms-and-evidence": 1,
		"it-tender-configuration-scc": 1,
		"it-tender-configuration-validation-report": 1,
		"it-tender-configuration-review-and-approval": 1,
		"it-tender-configuration-render-preview": 1,
		"it-tender-configuration-publication-readiness": 1,
	};

	var DOWNSTREAM_FETCHERS = {};

	var configRedirectInFlight = false;

	function desk_root_window() {
		return window.parent && window.parent.frappe ? window.parent : window;
	}

	function sync_configuration_id_to_url(configuration_id) {
		var root = desk_root_window();
		if (!configuration_id || !root.location) {
			return;
		}
		var url = new URL(root.location.href);
		if (url.searchParams.get("configuration_id") === configuration_id) {
			return;
		}
		url.searchParams.set("configuration_id", configuration_id);
		root.history.replaceState({}, "", url.toString());
	}

	function clear_configuration_id_from_url() {
		var root = desk_root_window();
		if (!root.location) {
			return;
		}
		var url = new URL(root.location.href);
		if (!url.searchParams.has("configuration_id")) {
			return;
		}
		url.searchParams.delete("configuration_id");
		var next = url.pathname + url.search + url.hash;
		root.history.replaceState({}, "", next);
	}

	function navigate(route, ctx) {
		var normalized = String(route || "").trim();
		if (ITW_REGISTERED_ROUTES.indexOf(normalized) === -1) {
			frappe.msgprint({
				title: __("Navigation failed"),
				indicator: "red",
				message: __("Unknown IT Wizard page route: {0}", [route || ""]),
			});
			return;
		}
		var root = desk_root_window();
		if (ctx) {
			set_route_context(ctx);
		}
		if (normalized === "it-tender-configuration-dashboard") {
			configRedirectInFlight = false;
			clear_configuration_id_from_url();
		}
		root.frappe.set_route(normalized);
		if (CONFIGURATION_CONTEXT_ROUTES[normalized] && ctx && ctx.configuration_id) {
			setTimeout(function () {
				sync_configuration_id_to_url(ctx.configuration_id);
			}, 0);
		}
	}

	function prepare_iframe_frame(iframe) {
		if (!iframe) {
			return;
		}
		iframe.style.opacity = "0";
		iframe.style.transition = "opacity 120ms ease-in";
	}

	function reveal_iframe_frame(doc) {
		var frame = doc && doc.defaultView && doc.defaultView.frameElement;
		if (frame) {
			frame.style.opacity = "1";
		}
	}

	function unfix_layout_chrome(node) {
		if (!node || !node.classList) {
			return;
		}
		node.classList.remove(
			"fixed",
			"sticky",
			"top-0",
			"top-14",
			"top-16",
			"left-0",
			"right-0",
			"z-40",
			"z-50",
		);
		node.classList.add("relative", "w-full");
	}

	function install_hydration_gate(doc) {
		if (!doc || !doc.head || doc.getElementById("it-wizard-hydration-gate")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "it-wizard-hydration-gate";
		// Only reveal main after successful hydrate — never on error (avoids fixture leak).
		style.textContent =
			'body:not([data-it-wizard-hydrated="1"]) > main,' +
			'body:not([data-it-wizard-hydrated="1"]) main {' +
			"visibility: hidden !important;" +
			"}" +
			"#it-wizard-hydration-error {" +
			"padding: 24px;" +
			"margin: 16px;" +
			"border: 1px solid #f0c0c0;" +
			"background: #fff5f5;" +
			"color: #5c1a1a;" +
			"border-radius: 8px;" +
			"font: 14px/1.4 system-ui,sans-serif;" +
			"}";
		doc.head.appendChild(style);
	}

	function normalize_page_layout(doc, screen) {
		if (!doc || !doc.body) {
			return;
		}
		if (screen === "std_config_overview") {
			if (kentender.it_wizard.overview && kentender.it_wizard.overview.prepare) {
				kentender.it_wizard.overview.prepare(doc);
			}
			return;
		}
		if (screen === "tender_profile") {
			harmonize_tender_profile_page_layout(doc);
			return;
		}
		if (screen === "tds") {
			harmonize_tds_page_layout(doc);
			return;
		}
		if (screen === "it_requirements") {
			harmonize_it_requirements_page_layout(doc);
			return;
		}
		if (screen === "implementation_schedule") {
			harmonize_it_schedule_page_layout(doc);
			return;
		}
		if (screen === "system_inventory") {
			harmonize_system_inventory_page_layout(doc);
			return;
		}
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		doc.querySelectorAll("body > nav").forEach(unfix_layout_chrome);
	}










	function mark_hydrated(doc) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.setAttribute("data-it-wizard-hydrated", "1");
		reveal_iframe_frame(doc);
	}

	function mark_hydration_error(doc) {
		if (!doc || !doc.body) {
			return;
		}
		// Never downgrade a document that already hydrated successfully. Redundant
		// triggers (readystate-complete + load event) can race, and a wasted second
		// fetch must not wipe a good render with an error banner.
		if (doc.body.getAttribute("data-it-wizard-hydrated") === "1") {
			return;
		}
		// Keep main hidden (gate CSS). Do not reveal fixture-laden markup.
		doc.body.setAttribute("data-it-wizard-hydrated", "error");
		if (!doc.getElementById("it-wizard-hydration-error")) {
			var banner = doc.createElement("div");
			banner.id = "it-wizard-hydration-error";
			banner.setAttribute("role", "alert");
			banner.textContent = __(
				"Unable to load configuration data for this screen. Magical/fixture values are withheld until a successful load.",
			);
			doc.body.insertBefore(banner, doc.body.firstChild);
		}
		reveal_iframe_frame(doc);
	}
































	function harmonize_tender_profile_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_tender_profile_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-profile-root");
		}
		doc.body.classList.add("it-wizard-profile-layout");
		doc.body.classList.remove("overflow-x-hidden");
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		doc.querySelectorAll("main").forEach(function (main) {
			main.classList.remove("mt-16", "pb-24");
			main.setAttribute("data-itw-profile-main", "1");
		});
		var footer = doc.querySelector("footer.fixed");
		if (footer) {
			unfix_layout_chrome(footer);
			footer.classList.remove("fixed", "bottom-0", "left-0", "right-0");
			footer.setAttribute("data-itw-profile-actions", "1");
		}
		enhance_tender_profile_layout(doc);
	}

	function enhance_tender_profile_layout(doc) {
		var context = doc.querySelector("main > section.bg-surface-container");
		if (context) {
			context.setAttribute("data-itw-profile-context", "1");
		}
		doc.querySelectorAll("h3").forEach(function (heading) {
			var text = (heading.textContent || "").trim();
			if (text.indexOf("Main Tender Profile") >= 0) {
				var card = heading.closest(".bg-surface-container-lowest");
				if (card) {
					card.setAttribute("data-itw-profile-form", "1");
				}
			}
		});
		var aside = doc.querySelector("aside");
		if (aside) {
			aside.setAttribute("data-itw-profile-sidebar", "1");
		}
		var footer = doc.querySelector("[data-itw-profile-actions]");
		if (!footer) {
			footer = doc.querySelector("footer");
		}
		if (footer) {
			footer.setAttribute("data-itw-profile-actions", "1");
		}
		tag_profile_field(
			doc,
			"Tender Display Title",
			"input",
			"tender_name",
		);
		tag_profile_field(
			doc,
			"Tender Description",
			"textarea",
			"contract_description",
		);
		tag_profile_field(doc, "Lot Structure", "select", "lotting_strategy");
		tag_profile_field(doc, "Reserved Procurement", "select", "reservation_setting");
		tag_profile_field(doc, "Tender Security", "input,select", "tender_security_applicability");
		tag_profile_field(doc, "Clarification Contact Email", "input", "clarification_contact_email");
		tag_profile_field(doc, "Submission Language", "input", "language_code");
		tag_profile_field(doc, "Currency", "input", "currency_code");
		strip_profile_fixture_scripts(doc);
		var toggleWrap = doc.querySelector("[data-itw-profile-form] .grid.grid-cols-1.md\\:grid-cols-3");
		if (toggleWrap) {
			var toggles = toggleWrap.querySelectorAll('[role="switch"]');
			var toggleKeys = [
				"alternative_tenders_allowed",
				"jv_allowed",
				"pre_tender_meeting_required",
			];
			toggles.forEach(function (toggle, index) {
				toggle = reset_profile_toggle_node(toggle);
				if (toggleKeys[index]) {
					toggle.setAttribute("data-itw-field", toggleKeys[index]);
					toggle.setAttribute("data-itw-toggle", "1");
				}
			});
		}
	}

	function reset_profile_toggle_node(toggle) {
		if (!toggle || toggle.getAttribute("data-itw-toggle-reset") === "1") {
			return toggle;
		}
		var clone = toggle.cloneNode(true);
		if (toggle.parentNode) {
			toggle.parentNode.replaceChild(clone, toggle);
		}
		clone.setAttribute("data-itw-toggle-reset", "1");
		return clone;
	}

	function strip_profile_fixture_scripts(doc) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-profile-scripts-stripped") === "1") {
			return;
		}
		doc.querySelectorAll("body > script").forEach(function (script) {
			if ((script.textContent || "").indexOf('[role="switch"]') >= 0) {
				script.remove();
			}
		});
		doc.body.setAttribute("data-itw-profile-scripts-stripped", "1");
	}

	function tag_profile_field(doc, labelText, selector, fieldKey) {
		doc.querySelectorAll("label").forEach(function (label) {
			if ((label.textContent || "").indexOf(labelText) < 0) {
				return;
			}
			var control = label.parentElement && label.parentElement.querySelector(selector);
			if (control) {
				control.setAttribute("data-itw-field", fieldKey);
			}
		});
	}

	function requirements_treatment_display_label(item) {
		if (item && item.treatment_label) {
			return item.treatment_label;
		}
		var raw = (item && item.treatment) || "";
		if (raw === "SCORED") {
			return "Evaluation-linked";
		}
		if (raw === "MANDATORY") {
			return "Mandatory";
		}
		if (raw === "INFORMATIONAL") {
			return "Informational";
		}
		return raw || "—";
	}

	function set_select_option_by_value(select, value, labelMap) {
		if (!select) {
			return;
		}
		var targetLabel = labelMap[value] || value || "";
		var matched = false;
		Array.prototype.forEach.call(select.options || [], function (option) {
			if (
				option.value === value ||
				(option.textContent || "").trim() === targetLabel
			) {
				select.value = option.value;
				matched = true;
			}
		});
		if (!matched && targetLabel) {
			Array.prototype.forEach.call(select.options || [], function (option) {
				if ((option.textContent || "").indexOf(targetLabel) >= 0) {
					select.value = option.value;
				}
			});
		}
	}

	function set_toggle_state(toggle, enabled) {
		if (!toggle) {
			return;
		}
		var dot = toggle.querySelector("span");
		if (!dot) {
			return;
		}
		if (enabled) {
			dot.classList.remove("translate-x-0");
			dot.classList.add("translate-x-5");
			toggle.classList.remove("bg-surface-container-highest");
			toggle.classList.add("bg-secondary");
		} else {
			dot.classList.remove("translate-x-5");
			dot.classList.add("translate-x-0");
			toggle.classList.remove("bg-secondary");
			toggle.classList.add("bg-surface-container-highest");
		}
		toggle.setAttribute("aria-checked", enabled ? "true" : "false");
	}

	function read_toggle_state(toggle) {
		if (!toggle) {
			return false;
		}
		var dot = toggle.querySelector("span");
		return !!(dot && dot.classList.contains("translate-x-5"));
	}

	function read_reservation_setting(select) {
		var label = "";
		if (select && select.selectedIndex >= 0) {
			label = (select.options[select.selectedIndex].textContent || "").trim();
		}
		if (label.indexOf("AGPO") >= 0) {
			return { reservation_applies: 1, reserved_group_code: "AGPO" };
		}
		return { reservation_applies: 0, reserved_group_code: "NONE" };
	}

	function read_lotting_strategy(select) {
		if (!select || select.selectedIndex < 0) {
			return "";
		}
		var label = (select.options[select.selectedIndex].textContent || "").trim();
		if (label.indexOf("Multiple") >= 0) {
			return "MULTIPLE_LOTS";
		}
		if (label.indexOf("Bulk") >= 0) {
			return "BULK";
		}
		return "SINGLE_LOT";
	}

	function read_tender_security(select) {
		if (!select || select.selectedIndex < 0) {
			return "";
		}
		var label = (select.options[select.selectedIndex].textContent || "").trim();
		if (label.indexOf("Bank Guarantee") >= 0) {
			return "BANK_GUARANTEE";
		}
		if (label.indexOf("Cash Deposit") >= 0) {
			return "CASH_DEPOSIT";
		}
		if (label.indexOf("None Required") >= 0) {
			return "NONE";
		}
		if (label.indexOf("Declaration") >= 0) {
			return "TENDER_SECURING_DECLARATION";
		}
		return "";
	}

	function collect_profile_form_values(doc) {
		var values = {};
		var tdsOwnedKeys = {
			tender_security_applicability: 1,
			clarification_contact_email: 1,
			language_code: 1,
			currency_code: 1,
		};
		doc.querySelectorAll("[data-itw-field]").forEach(function (node) {
			var key = node.getAttribute("data-itw-field");
			if (!key) {
				return;
			}
			if (node.getAttribute("data-itw-owned-elsewhere") === "1" || tdsOwnedKeys[key]) {
				// Owned by TDS — never persist from Profile.
				return;
			}
			if (node.getAttribute("data-itw-toggle") === "1") {
				values[key] = read_toggle_state(node) ? 1 : 0;
				return;
			}
			if (node.tagName === "SELECT") {
				if (key === "reservation_setting") {
					Object.assign(values, read_reservation_setting(node));
					return;
				}
				if (key === "lotting_strategy") {
					values[key] = read_lotting_strategy(node);
					return;
				}
				values[key] = (node.value || "").trim();
				return;
			}
			values[key] = (node.value || "").trim();
		});
		return values;
	}

	function unwrap_envelope_data(source) {
		var envelope = (source && source.message) || source || {};
		if (envelope.data !== undefined) {
			return envelope.data || {};
		}
		return envelope || {};
	}

	function profile_payload_data(source) {
		return unwrap_envelope_data(source);
	}

	function apply_profile_payload(doc, data) {
		data = data || {};
		hydrate_profile_context(doc, data);
		hydrate_profile_form(doc, data.profile || {});
		hydrate_profile_sidebar(doc, data);
		hydrate_profile_std_panel(doc, data);
	}

	function next_hydration_token(iframe) {
		if (!iframe) {
			return 0;
		}
		var token = (iframe.__itwHydrationToken || 0) + 1;
		iframe.__itwHydrationToken = token;
		return token;
	}

	function hydration_token_active(iframe, token) {
		return !!(iframe && token === iframe.__itwHydrationToken);
	}

	function live_iframe_document(iframe) {
		return iframe && iframe.contentDocument ? iframe.contentDocument : null;
	}

	function hydrate_profile_context(doc, data) {
		var panel = doc.querySelector("[data-itw-profile-context]");
		if (!panel) {
			return;
		}
		var planning = data.planning_package || {};
		var entity = data.procuring_entity || {};
		var method = data.method || {};
		var validation = data.validation || {};
		var cells = panel.querySelectorAll(":scope > div");
		var values = [
			data.configuration_id || "—",
			data.title || "—",
			planning.code || planning.name || "—",
			(entity.name || "").trim() || "—",
			format_method_reference(method),
			data.state_label || "—",
			String(validation.blockers || 0) +
				" " +
				(validation.blockers === 1 ? __("Blocker") : __("Blockers")) +
				" / " +
				String(validation.warnings || 0) +
				" " +
				(validation.warnings === 1 ? __("Warning") : __("Warnings")),
		];
		cells.forEach(function (cell, index) {
			var valueNode = cell.querySelector(".font-bold");
			if (valueNode) {
				valueNode.textContent = values[index] || "—";
			}
		});
	}

	function hydrate_profile_form(doc, profile) {
		profile = profile || {};
		set_control_value(doc, "tender_name", profile.tender_name || "");
		set_control_value(doc, "contract_description", profile.contract_description || "");
		set_select_option_by_value(
			find_profile_control(doc, "lotting_strategy"),
			profile.lotting_strategy || "",
			LOTTING_STRATEGY_OPTIONS,
		);
		var reservationSelect = find_profile_control(doc, "reservation_setting");
		if (profile.reservation_applies) {
			set_select_option_by_value(reservationSelect, "AGPO", RESERVATION_OPTIONS);
		} else {
			set_select_option_by_value(reservationSelect, "NONE", RESERVATION_OPTIONS);
		}
		mark_profile_field_owned_elsewhere(
			doc,
			"tender_security_applicability",
			profile.tender_security_applicability
				? TENDER_SECURITY_OPTIONS[profile.tender_security_applicability] ||
					profile.tender_security_applicability
				: __("Not configured"),
			__("Tender Data Sheet"),
		);
		mark_profile_field_owned_elsewhere(
			doc,
			"clarification_contact_email",
			profile.clarification_contact_email || __("Not configured"),
			__("Tender Data Sheet"),
		);
		mark_profile_field_owned_elsewhere(
			doc,
			"language_code",
			profile.language_code === "en"
				? "English"
				: profile.language_code || __("Not configured"),
			__("Tender Data Sheet"),
		);
		mark_profile_field_owned_elsewhere(
			doc,
			"currency_code",
			profile.currency_code || __("Not configured"),
			__("Tender Data Sheet"),
		);
		set_toggle_state(
			find_profile_control(doc, "alternative_tenders_allowed"),
			!!profile.alternative_tenders_allowed,
		);
		set_toggle_state(find_profile_control(doc, "jv_allowed"), !!profile.jv_allowed);
		set_toggle_state(
			find_profile_control(doc, "pre_tender_meeting_required"),
			!!profile.pre_tender_meeting_required,
		);
	}

	function mark_profile_field_owned_elsewhere(doc, fieldKey, displayValue, ownerScreen) {
		var control = find_profile_control(doc, fieldKey);
		if (!control) {
			return;
		}
		control.disabled = true;
		control.setAttribute("aria-readonly", "true");
		control.setAttribute("data-itw-owned-elsewhere", "1");
		control.setAttribute("data-itw-owner-screen", "it-tender-configuration-tds");
		if (control.tagName === "SELECT") {
			var optionValue = displayValue || __("Not configured");
			if (!Array.from(control.options).some(function (option) { return option.value === optionValue || option.textContent === optionValue; })) {
				control.add(new Option(optionValue, optionValue));
			}
			control.value = optionValue;
		} else {
			control.value = displayValue || __("Not configured");
		}
		var host = control.parentElement;
		if (!host) {
			return;
		}
		var source = host.querySelector("[data-itw-owned-elsewhere-source]");
		if (!source) {
			source = doc.createElement("p");
			source.className = "text-[10px] text-on-surface-variant italic mt-1";
			source.setAttribute("data-itw-owned-elsewhere-source", "1");
			host.appendChild(source);
		}
		source.textContent = __("Source: {0}", [ownerScreen]);
		var edit = host.querySelector("[data-itw-edit-in-owner]");
		if (!edit) {
			edit = doc.createElement("button");
			edit.type = "button";
			edit.className = "text-primary font-body-md text-[12px] hover:underline mt-1";
			edit.setAttribute("data-itw-edit-in-owner", "it-tender-configuration-tds");
			edit.textContent = __("Edit in Tender Data Sheet");
			host.appendChild(edit);
		} else {
			edit.setAttribute("data-itw-edit-in-owner", "it-tender-configuration-tds");
		}
	}

	function find_profile_control(doc, fieldKey) {
		return doc.querySelector('[data-itw-field="' + fieldKey + '"]');
	}

	function set_control_value(doc, fieldKey, value) {
		var control = find_profile_control(doc, fieldKey);
		if (!control) {
			return;
		}
		if (control.getAttribute("data-itw-toggle") === "1") {
			set_toggle_state(control, !!value);
			return;
		}
		control.value = value;
	}

	function hydrate_profile_sidebar(doc, data) {
		var panel = doc.querySelector("[data-itw-profile-sidebar]");
		if (!panel) {
			return;
		}
		var completion = data.completion || {};
		var validation = data.validation || {};
		var countNode = panel.querySelector(".font-data-mono.font-bold.text-primary");
		if (countNode) {
			countNode.textContent =
				String(completion.completed || 0) + "/" + String(completion.total || 11);
		}
		var progress = panel.querySelector(".bg-primary.h-full");
		if (progress) {
			progress.style.width = String(completion.percent || 0) + "%";
		}
		var missingList = panel.querySelector("ul.space-y-2");
		if (missingList) {
			var missing = completion.missing_fields || [];
			if (!missing.length) {
				missingList.innerHTML =
					'<li class="flex items-center gap-2 text-body-md text-on-surface-variant">' +
					'<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span>' +
					frappe.utils.escape_html(__("All required fields complete")) +
					"</li>";
			} else {
				missingList.innerHTML = missing
					.map(function (label) {
						return (
							'<li class="flex items-center gap-2 text-body-md text-on-surface-variant">' +
							'<span class="w-1.5 h-1.5 rounded-full bg-status-reserved"></span>' +
							frappe.utils.escape_html(label) +
							"</li>"
						);
					})
					.join("");
			}
		}
		panel.querySelectorAll(".flex.items-center.justify-between.p-3").forEach(function (row) {
			var text = (row.textContent || "").trim();
			var valueNode = row.querySelector(".font-bold");
			if (!valueNode) {
				return;
			}
			if (text.indexOf("Blocker") >= 0) {
				valueNode.textContent = String(validation.blockers || 0);
			}
			if (text.indexOf("Warning") >= 0) {
				valueNode.textContent = String(validation.warnings || 0);
			}
		});
	}

	function hydrate_profile_std_panel(doc, data) {
		doc.querySelectorAll("h4").forEach(function (heading) {
			if ((heading.textContent || "").indexOf("Standard Tender Document Binding") < 0) {
				return;
			}
			var panel = heading.closest(".bg-secondary-fixed");
			if (!panel) {
				return;
			}
			panel.querySelectorAll("p").forEach(function (node) {
				var text = node.textContent || "";
				if (text.indexOf("STD Package") >= 0) {
					node.innerHTML =
						"<strong>STD Package:</strong> " +
						frappe.utils.escape_html(
							data.std_template_version_label || data.std_template_version_id || "—",
						);
				}
			});
		});
	}

	function disable_profile_stub_actions(doc) {
		var actionBar = doc.querySelector("[data-itw-profile-actions]");
		if (!actionBar) {
			return;
		}
		actionBar.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (
				text.indexOf("Run Validation") >= 0 ||
				text.indexOf("Proceed Now") >= 0 ||
				text.indexOf("View Audit") >= 0
			) {
				btn.disabled = true;
				btn.style.opacity = "0.55";
				btn.style.pointerEvents = "none";
				btn.setAttribute("aria-disabled", "true");
			}
		});
	}

	function wire_profile_interactions(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-profile-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-profile-wired", "1");

		doc.querySelectorAll('[data-itw-toggle="1"]').forEach(function (toggle) {
			toggle.addEventListener("click", function (event) {
				event.preventDefault();
				event.stopImmediatePropagation();
				set_toggle_state(toggle, !read_toggle_state(toggle));
			});
		});

		doc.addEventListener(
			"click",
			function (event) {
				var btn = event.target && event.target.closest ? event.target.closest("button") : null;
				if (!btn) {
					return;
				}
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Save Profile") >= 0) {
					event.preventDefault();
					var values = collect_profile_form_values(doc);
					call_api("save_tender_profile_api", {
						configuration_id: ctx.configuration_id,
						profile_json: JSON.stringify(values),
					})
						.then(function (result) {
							frappe.show_alert({
								message: __("Profile saved"),
								indicator: "green",
							});
							apply_profile_payload(doc, profile_payload_data(result));
						})
						.catch(function (err) {
							frappe.show_alert({
								indicator: "red",
								message: (err && err.message) || __("Unable to save profile."),
							});
						});
					return;
				}
				if (
					text.indexOf("Continue to Tender Data Sheet") >= 0 ||
					text.indexOf("Proceed Now") >= 0 ||
					btn.getAttribute("data-itw-edit-in-owner") === "it-tender-configuration-tds"
				) {
					event.preventDefault();
					navigate("it-tender-configuration-tds", {
						configuration_id: ctx.configuration_id,
					});
				}
			},
			true,
		);
	}

	function fetch_tender_profile_data(ctx) {
		return call_api("get_tender_profile_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				profile: (result && result.message) || {},
			};
		});
	}

	var LOCAL_SOURCING_OPTIONS = {
		MARGIN_15: "Apply 15% Margin of Preference",
		NONE: "No Local Preference",
	};

	var ISSUER_TYPE_OPTIONS = {
		COMMERCIAL_BANK: "Commercial Bank",
		INSURANCE_COMPANY: "Insurance Company",
		SACCO_SOCIETY: "Sacco Society",
	};

	function install_tds_layout_styles(doc) {
		if (!doc || doc.getElementById("itw-tds-layout-style")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "itw-tds-layout-style";
		style.textContent =
			"html.it-wizard-tds-root, body.it-wizard-tds-layout {" +
			"height: 100%; margin: 0; overflow: hidden;" +
			"}" +
			"body.it-wizard-tds-layout {" +
			"display: flex; flex-direction: column; min-height: 100vh;" +
			"}" +
			"body.it-wizard-tds-layout > header {" +
			"flex-shrink: 0; position: relative !important; top: auto !important;" +
			"}" +
			"body.it-wizard-tds-layout [data-itw-tds-main] {" +
			"flex: 1 1 auto; overflow-y: auto; min-height: 0;" +
			"max-width: none !important;" +
			"width: 100% !important;" +
			"margin-left: 0 !important;" +
			"margin-right: 0 !important;" +
			"padding: 0 !important;" +
			"}" +
			"body.it-wizard-tds-layout [data-itw-tds-shell] {" +
			"max-width: 1600px;" +
			"margin-left: auto;" +
			"margin-right: auto;" +
			"width: 100%;" +
			"box-sizing: border-box;" +
			"}" +
			"body.it-wizard-tds-layout [data-itw-tds-actions] {" +
			"flex-shrink: 0; position: relative !important; bottom: auto !important;" +
			"}";
		doc.head.appendChild(style);
	}

	function wrap_tds_content_shell(doc) {
		var main = doc.querySelector("[data-itw-tds-main]");
		if (!main || main.getAttribute("data-itw-tds-shell-wrapped") === "1") {
			return;
		}
		var formColumn = main.querySelector(":scope > .flex-grow");
		var aside = main.querySelector(":scope > aside");
		if (!formColumn) {
			return;
		}
		var shell = doc.createElement("div");
		shell.setAttribute("data-itw-tds-shell", "1");
		shell.className =
			"p-6 grid grid-cols-12 gap-section-gap max-w-[1600px] mx-auto w-full box-border";
		formColumn.classList.remove("flex-grow", "pr-gutter", "py-section-gap");
		formColumn.classList.add("col-span-12", "lg:col-span-9");
		if (aside) {
			aside.classList.remove(
				"w-80",
				"flex-shrink-0",
				"border-l",
				"border-border-subtle",
				"pl-gutter",
				"py-section-gap",
				"hidden",
				"lg:block",
			);
			aside.classList.add("col-span-12", "lg:col-span-3", "space-y-6");
		}
		main.classList.remove(
			"max-w-7xl",
			"mx-auto",
			"px-container-padding",
			"pb-24",
			"min-h-[calc(100vh-120px)]",
		);
		shell.appendChild(formColumn);
		if (aside) {
			shell.appendChild(aside);
		}
		main.appendChild(shell);
		main.setAttribute("data-itw-tds-shell-wrapped", "1");
	}

	function harmonize_tds_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_tds_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-tds-root");
		}
		doc.body.classList.add("it-wizard-tds-layout");
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		var main = doc.querySelector("main");
		if (main) {
			main.classList.remove("pb-24");
			main.setAttribute("data-itw-tds-main", "1");
		}
		var footer = doc.querySelector("footer");
		if (footer) {
			footer.classList.remove("fixed");
			footer.setAttribute("data-itw-tds-actions", "1");
		}
		wrap_tds_content_shell(doc);
		enhance_tds_layout(doc);
	}

	function enhance_tds_layout(doc) {
		var context = doc.querySelector("header section.bg-surface-container");
		if (context) {
			context.setAttribute("data-itw-tds-context", "1");
		}
		var main = doc.querySelector("[data-itw-tds-main]");
		if (main) {
			var formWrap = main.querySelector(".space-y-6");
			if (formWrap) {
				formWrap.setAttribute("data-itw-tds-form", "1");
			}
		}
		var aside = doc.querySelector("aside");
		if (aside) {
			aside.setAttribute("data-itw-tds-sidebar", "1");
		}
		var footer = doc.querySelector("[data-itw-tds-actions]");
		if (footer) {
			footer.setAttribute("data-itw-tds-actions", "1");
		}
		tag_tds_field(doc, "Procuring Entity Address", "input", "procuring_entity_address");
		tag_tds_field(doc, "Tender Ref", "input", "tender_number");
		tag_tds_field(doc, "Tender Name", "input", "tender_name");
		tag_tds_field(doc, "JV Members Cap", "input", "jv_max_members");
		tag_tds_field(doc, "Local Sourcing Preference", "select", "local_sourcing_preference");
		tag_tds_field(doc, "Submission Deadline", "input", "submission_deadline_at");
		tag_tds_field(doc, "Opening Date/Time", "input", "opening_at");
		tag_tds_field(doc, "Clarification Contact", "input", "clarification_contact_email");
		tag_tds_field(doc, "Envelope Marking", "input", "envelope_marking");
		tag_tds_field(doc, "Security Amount", "input", "tender_security_amount");
		tag_tds_field(doc, "Validity", "input", "tender_validity_days");
		tag_tds_field(doc, "Issuer Type", "select", "security_issuer_type");
		var altSelect = doc.querySelector("[data-itw-tds-form] select");
		if (altSelect && !altSelect.getAttribute("data-itw-field")) {
			altSelect.setAttribute("data-itw-field", "alternative_tenders_allowed");
		}
		var electronicCheckbox = doc.querySelector(
			'[data-itw-tds-form] input[type="checkbox"]:not([disabled])',
		);
		if (electronicCheckbox) {
			electronicCheckbox.setAttribute("data-itw-field", "electronic_tenders_allowed");
		}
		strip_tds_fixture_scripts(doc);
		normalize_tds_fixture_field_styles(doc);
	}

	function strip_tds_fixture_scripts(doc) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-tds-scripts-stripped") === "1") {
			return;
		}
		doc.querySelectorAll("body > script").forEach(function (node) {
			node.parentNode.removeChild(node);
		});
		doc.body.setAttribute("data-itw-tds-scripts-stripped", "1");
	}

	function tag_tds_field(doc, labelText, selector, fieldKey) {
		var labels = doc.querySelectorAll("label");
		labels.forEach(function (label) {
			if ((label.textContent || "").indexOf(labelText) < 0) {
				return;
			}
			var container = label.closest(".space-y-1") || label.parentElement;
			if (!container) {
				return;
			}
			var control = container.querySelector(selector);
			if (control) {
				control.setAttribute("data-itw-field", fieldKey);
			}
		});
	}

	function format_datetime_local(value) {
		if (!value) {
			return "";
		}
		return String(value).replace(" ", "T").slice(0, 16);
	}

	function parse_datetime_local(value) {
		if (!value) {
			return "";
		}
		if (value.indexOf("T") >= 0) {
			return value.replace("T", " ") + ":00";
		}
		return value;
	}

	function find_tds_control(doc, fieldKey) {
		return doc.querySelector('[data-itw-field="' + fieldKey + '"]');
	}

	function collect_tds_form_values(doc) {
		var values = {};
		doc.querySelectorAll("[data-itw-field]").forEach(function (node) {
			var key = node.getAttribute("data-itw-field");
			if (!key) {
				return;
			}
			if (node.type === "checkbox") {
				values[key] = node.checked ? 1 : 0;
				return;
			}
			if (node.type === "datetime-local") {
				values[key] = parse_datetime_local(node.value || "");
				return;
			}
			if (node.tagName === "SELECT") {
				var raw = (node.value || "").trim();
				if (key === "alternative_tenders_allowed") {
					values[key] = raw.toLowerCase() === "yes" ? "YES" : "NO";
					return;
				}
				if (key === "local_sourcing_preference") {
					Object.keys(LOCAL_SOURCING_OPTIONS).forEach(function (code) {
						if (LOCAL_SOURCING_OPTIONS[code] === raw) {
							values[key] = code;
						}
					});
					if (!values[key]) {
						values[key] = raw;
					}
					return;
				}
				if (key === "security_issuer_type") {
					Object.keys(ISSUER_TYPE_OPTIONS).forEach(function (code) {
						if (ISSUER_TYPE_OPTIONS[code] === raw) {
							values[key] = code;
						}
					});
					if (!values[key]) {
						values[key] = raw;
					}
					return;
				}
				values[key] = raw;
				return;
			}
			if (key === "jv_max_members" || key === "tender_validity_days") {
				var numeric = (node.value || "").trim();
				values[key] = numeric === "" ? null : parseInt(numeric, 10);
				return;
			}
			if (key === "tender_security_amount") {
				var amount = (node.value || "").replace(/,/g, "").trim();
				values[key] = amount === "" ? null : parseFloat(amount);
				return;
			}
			values[key] = (node.value || "").trim();
		});
		return values;
	}

	function tds_payload_data(source) {
		return unwrap_envelope_data(source);
	}

	function apply_tds_payload(doc, data) {
		data = data || {};
		hydrate_tds_context(doc, data);
		hydrate_tds_form(doc, data.values || {});
		hydrate_tds_sidebar(doc, data);
	}

	function hydrate_tds_context(doc, data) {
		var panel = doc.querySelector("[data-itw-tds-context]");
		if (!panel) {
			return;
		}
		var values = data.values || {};
		var planning = data.planning_package || {};
		var entity = data.procuring_entity || {};
		var method = data.method || {};
		var validation = data.validation || {};
		var cells = panel.querySelectorAll(":scope > div");
		var contextValues = [
			values.tender_number || data.configuration_id || "—",
			data.title || values.tender_name || "—",
			planning.code || planning.name || "—",
			(entity.name || "").trim() || "—",
			format_method_reference(method),
			data.state_label || "—",
			String(validation.blockers || 0) +
				" " +
				(validation.blockers === 1 ? __("Blocker") : __("Blockers")) +
				" / " +
				String(validation.warnings || 0) +
				" " +
				(validation.warnings === 1 ? __("Warning") : __("Warnings")),
		];
		cells.forEach(function (cell, index) {
			var valueNode = cell.querySelector(".font-bold");
			if (valueNode) {
				valueNode.textContent = contextValues[index] || "—";
			}
		});
	}

	function normalize_tds_fixture_field_styles(doc) {
		var standardDatetimeClasses =
			"w-full bg-surface-container-lowest border-outline-variant rounded-md p-2 font-data-mono text-data-mono form-input-focus";
		var submission = find_tds_control(doc, "submission_deadline_at");
		if (submission) {
			submission.className = standardDatetimeClasses;
		}
	}

	function hydrate_tds_form(doc, values) {
		values = values || {};
		set_control_value(doc, "procuring_entity_address", values.procuring_entity_address || "");
		set_control_value(doc, "tender_number", values.tender_number || "");
		set_control_value(doc, "tender_name", values.tender_name || "");
		var altSelect = find_tds_control(doc, "alternative_tenders_allowed");
		if (altSelect) {
			altSelect.value = values.alternative_tenders_allowed === "YES" ? "Yes" : "No";
		}
		set_control_value(doc, "jv_max_members", values.jv_max_members == null ? "" : String(values.jv_max_members));
		set_select_option_by_value(
			find_tds_control(doc, "local_sourcing_preference"),
			values.local_sourcing_preference || "",
			LOCAL_SOURCING_OPTIONS,
		);
		set_control_value(doc, "submission_deadline_at", format_datetime_local(values.submission_deadline_at));
		set_control_value(doc, "opening_at", format_datetime_local(values.opening_at));
		set_control_value(doc, "clarification_contact_email", values.clarification_contact_email || "");
		var electronic = find_tds_control(doc, "electronic_tenders_allowed");
		if (electronic) {
			electronic.checked = !!values.electronic_tenders_allowed;
		}
		set_control_value(doc, "envelope_marking", values.envelope_marking || "");
		set_control_value(
			doc,
			"tender_security_amount",
			values.tender_security_amount == null ? "" : String(values.tender_security_amount),
		);
		set_control_value(
			doc,
			"tender_validity_days",
			values.tender_validity_days == null ? "" : String(values.tender_validity_days),
		);
		set_select_option_by_value(
			find_tds_control(doc, "security_issuer_type"),
			values.security_issuer_type || "",
			ISSUER_TYPE_OPTIONS,
		);
		normalize_tds_fixture_field_styles(doc);
	}

	function hydrate_tds_sidebar(doc, data) {
		var panel = doc.querySelector("[data-itw-tds-sidebar]");
		if (!panel) {
			return;
		}
		var completion = data.completion || {};
		var completed = completion.completed || 0;
		var total = completion.total || 15;
		var percent = completion.percent || 0;
		var progress = panel.querySelector(".bg-primary.h-2\\.5, .bg-primary.h-2_5, .bg-primary");
		if (progress) {
			progress.style.width = String(percent) + "%";
		}
		panel.querySelectorAll("p").forEach(function (node) {
			if ((node.textContent || "").indexOf("/") >= 0 && (node.textContent || "").indexOf("fields complete") >= 0) {
				node.textContent = completed + "/" + total + " fields complete";
			}
		});
		var list = panel.querySelector("ul");
		if (list) {
			list.innerHTML = "";
			(completion.missing_fields || []).forEach(function (label) {
				var li = doc.createElement("li");
				li.className = "flex items-start gap-2";
				li.innerHTML =
					'<span class="material-symbols-outlined text-[16px] text-error mt-0.5">error</span>' +
					"<span>" +
					frappe.utils.escape_html(label) +
					"</span>";
				list.appendChild(li);
			});
			if (!(completion.missing_fields || []).length) {
				var empty = doc.createElement("li");
				empty.className = "text-on-surface-variant";
				empty.textContent = __("All required fields complete.");
				list.appendChild(empty);
			}
		}
	}

	function disable_tds_stub_actions(doc) {
		var actionBar = doc.querySelector("[data-itw-tds-actions]");
		if (actionBar) {
			actionBar.querySelectorAll("button").forEach(function (btn) {
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Continue to IT Requirements") >= 0) {
					btn.disabled = false;
					btn.removeAttribute("aria-disabled");
					btn.style.opacity = "";
					btn.style.pointerEvents = "";
					btn.classList.remove("cursor-not-allowed", "opacity-70");
					return;
				}
				if (
					text.indexOf("Run Validation") >= 0 ||
					text.indexOf("View Details") >= 0
				) {
					btn.disabled = true;
					btn.style.opacity = "0.55";
					btn.style.pointerEvents = "none";
					btn.setAttribute("aria-disabled", "true");
				}
			});
		}
		doc.querySelectorAll("[data-itw-tds-sidebar] button, [data-itw-tds-form] button.group").forEach(
			function (btn) {
				btn.disabled = true;
				btn.style.opacity = "0.55";
				btn.style.pointerEvents = "none";
				btn.setAttribute("aria-disabled", "true");
			},
		);
	}

	function wire_tds_interactions(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-tds-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-tds-wired", "1");

		var electronic = find_tds_control(doc, "electronic_tenders_allowed");
		if (electronic) {
			electronic.addEventListener("click", function (event) {
				event.stopImmediatePropagation();
			});
		}

		doc.addEventListener(
			"click",
			function (event) {
				var btn = event.target && event.target.closest ? event.target.closest("button") : null;
				if (!btn) {
					return;
				}
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Save TDS") >= 0) {
					event.preventDefault();
					var values = collect_tds_form_values(doc);
					call_api("save_tds_api", {
						configuration_id: ctx.configuration_id,
						tds_json: JSON.stringify(values),
					})
						.then(function (result) {
							frappe.show_alert({
								message: __("TDS saved"),
								indicator: "green",
							});
							apply_tds_payload(doc, tds_payload_data(result));
						})
						.catch(function (err) {
							frappe.show_alert({
								indicator: "red",
								message: (err && err.message) || __("Unable to save TDS."),
							});
						});
					}
				if (text.indexOf("Continue to IT Requirements") >= 0) {
					event.preventDefault();
					navigate("it-tender-configuration-it-requirements", {
						configuration_id: ctx.configuration_id,
					});
				}
			},
			true,
		);
	}

	function fetch_tds_data(ctx) {
		return call_api("get_tds_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				tds: (result && result.message) || {},
			};
		});
	}

	var REQ_RESPONSE_FORMAT_MAP = {
		YES_NO: "Yes/No",
		NUMERIC: "Numeric Value",
		DOCUMENT_EVIDENCE: "Document Upload",
		UPLOAD: "Document Upload",
		NARRATIVE: "Narrative",
		COMPLIANCE_MATRIX: "Compliance Matrix",
		NOT_REQUIRED: "Not Required",
	};

	var REQ_RESPONSE_FORMAT_REVERSE = {
		"Yes/No": "YES_NO",
		"Numeric Value": "NUMERIC",
		"Numeric": "NUMERIC",
		"Document Upload": "DOCUMENT_EVIDENCE",
		"Upload": "UPLOAD",
		"Narrative": "NARRATIVE",
		"Compliance Matrix": "COMPLIANCE_MATRIX",
		"Not Required": "NOT_REQUIRED",
	};

	// Storage enum remains SCORED for DocType compatibility; UI never labels it "Scored" / "%".
	var REQ_TREATMENT_REVERSE = {
		Mandatory: "MANDATORY",
		"Evaluation-linked": "SCORED",
		Informational: "INFORMATIONAL",
	};

	var REQ_EVIDENCE_LEVEL_REVERSE = {
		"Evidence Required": "REQUIRED",
		"Evidence Optional": "OPTIONAL",
		"No Evidence Required": "NOT_REQUIRED",
	};

	// @deprecated — iframe hydrator; Screen 03 uses native screens/it_requirements.js
	function install_it_requirements_layout_styles(doc) {
		if (!doc || doc.getElementById("itw-req-layout-style")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "itw-req-layout-style";
		style.textContent =
			"html.it-wizard-it-requirements-root, body.it-wizard-it-requirements-layout {" +
			"height: 100%; margin: 0; overflow: hidden;" +
			"}" +
			"body.it-wizard-it-requirements-layout {" +
			"display: flex; flex-direction: column; min-height: 0; max-height: 100%;" +
			"}" +
			"body.it-wizard-it-requirements-layout > header {" +
			"flex-shrink: 0; position: relative !important; top: auto !important;" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-context] {" +
			"flex-shrink: 0;" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-main] {" +
			"flex: 1 1 0; min-height: 0; overflow: hidden;" +
			"display: flex; flex-direction: row;" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-composer] {" +
			"display: flex; flex-direction: column; flex: 1 1 0; min-height: 0;" +
			"overflow: hidden !important; position: relative;" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-table-host] {" +
			"flex: 1 1 0; min-height: 0; overflow-y: auto; -webkit-overflow-scrolling: touch;" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-actions] {" +
			"flex-shrink: 0; position: relative !important; bottom: auto !important;" +
			"left: auto !important; right: auto !important; width: 100%; z-index: 30;" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-drawer] {" +
			"transform: translateX(100%); z-index: 60;" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-drawer][data-itw-req-drawer-open='1'] {" +
			"transform: translateX(0);" +
			"}" +
			"body.it-wizard-it-requirements-layout [data-itw-req-guidance] {" +
			"display: flex !important; flex-direction: column; min-height: 0; max-height: 100%;" +
			"}";
		doc.head.appendChild(style);
	}

	function harmonize_it_requirements_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_it_requirements_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-it-requirements-root");
		}
		doc.body.classList.add("it-wizard-it-requirements-layout");
		doc.body.classList.remove("min-h-screen");
		doc.body.classList.add("h-full", "overflow-hidden");
		if (doc.documentElement) {
			doc.documentElement.classList.add("h-full");
		}
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		var main = doc.querySelector("main");
		if (main) {
			main.classList.add("min-h-0");
			main.setAttribute("data-itw-req-main", "1");
		}
		var footer = doc.querySelector("footer[data-itw-req-actions], [data-itw-req-actions]");
		if (footer) {
			footer.classList.remove("fixed", "absolute", "bottom-0", "left-0", "right-0");
		}
		enhance_it_requirements_layout(doc);
	}

	function enhance_it_requirements_layout(doc) {
		var context = doc.querySelector("[data-itw-req-context]");
		if (!context) {
			context = doc.querySelector("body > header + div");
			if (context) {
				context.setAttribute("data-itw-req-context", "1");
			}
		}
		var main = doc.querySelector("[data-itw-req-main]");
		if (main) {
			var composer = main.querySelector("[data-itw-req-composer]");
			if (!composer) {
				composer = main.querySelector(":scope > .flex-1.flex.flex-col");
				if (composer) {
					composer.setAttribute("data-itw-req-composer", "1");
				}
			}
			if (composer) {
				composer.classList.add("min-h-0");
				composer.classList.remove("overflow-y-auto");
				composer.classList.add("overflow-hidden");
			}
			var tableHost = doc.querySelector("[data-itw-req-table-host]");
			if (tableHost) {
				tableHost.classList.add("min-h-0");
				tableHost.classList.remove("pb-20");
			}
			var actions = doc.querySelector("[data-itw-req-actions]");
			if (actions) {
				actions.classList.remove("absolute", "bottom-0", "left-0", "right-0");
				if (actions.parentElement && actions.parentElement.getAttribute("data-itw-req-composer") === "1") {
					var footer = doc.createElement("footer");
					footer.setAttribute("data-itw-req-actions", "1");
					footer.className = actions.className;
					while (actions.firstChild) {
						footer.appendChild(actions.firstChild);
					}
					actions.parentElement.removeChild(actions);
					var mainEl = doc.querySelector("[data-itw-req-main]");
					if (mainEl && mainEl.parentNode) {
						mainEl.parentNode.insertBefore(footer, mainEl.nextSibling);
					} else {
						doc.body.appendChild(footer);
					}
				}
			}
		}
		var guidance = doc.querySelector("[data-itw-req-guidance]");
		if (guidance) {
			guidance.classList.remove("hidden");
			guidance.classList.add("flex");
		}
		var drawer = doc.querySelector("[data-itw-req-drawer]");
		if (drawer) {
			drawer.setAttribute("data-itw-req-drawer-hidden", "1");
			drawer.removeAttribute("data-itw-req-drawer-open");
		}
		strip_it_requirements_fixture_scripts(doc);
	}

	function strip_it_requirements_fixture_scripts(doc) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-req-scripts-stripped") === "1") {
			return;
		}
		doc.querySelectorAll("body > script").forEach(function (node) {
			node.parentNode.removeChild(node);
		});
		doc.body.setAttribute("data-itw-req-scripts-stripped", "1");
	}

	function find_req_control(doc, fieldKey) {
		return doc.querySelector('[data-itw-field="' + fieldKey + '"]');
	}

	function requirements_payload_data(source) {
		return unwrap_envelope_data(source);
	}

	function open_it_requirements_drawer(doc) {
		var drawer = doc.querySelector("[data-itw-req-drawer]");
		if (!drawer) {
			return;
		}
		drawer.setAttribute("data-itw-req-drawer-open", "1");
		drawer.removeAttribute("data-itw-req-drawer-hidden");
	}

	function close_it_requirements_drawer(doc) {
		var drawer = doc.querySelector("[data-itw-req-drawer]");
		if (!drawer) {
			return;
		}
		drawer.removeAttribute("data-itw-req-drawer-open");
		drawer.setAttribute("data-itw-req-drawer-hidden", "1");
	}

	function plain_label_html(text, tone) {
		var cls =
			tone === "warning"
				? "text-status-reserved"
				: tone === "muted"
					? "text-on-surface-variant"
					: "text-on-surface";
		return (
			'<span class="font-body-md text-[13px] ' +
			cls +
			'">' +
			frappe.utils.escape_html(text || "—") +
			"</span>"
		);
	}

	function build_requirements_row_html(item) {
		var rowClass = "border-b border-subtle hover:bg-surface-container-low transition-colors group";
		var treatment = requirements_treatment_display_label(item);
		var treatmentHtml = plain_label_html(treatment);
		if (item.evaluation_linked_label) {
			treatmentHtml +=
				' <span class="inline-flex items-center px-2 py-0.5 rounded bg-surface-container text-on-surface-variant text-[11px] font-medium ml-1">' +
				frappe.utils.escape_html(item.evaluation_linked_label) +
				"</span>";
		}
		var summary = item.summary || item.description || "";
		return (
			'<tr class="' +
			rowClass +
			'" data-itw-req-row="1" data-itw-req-code="' +
			frappe.utils.escape_html(item.requirement_code) +
			'">' +
			'<td class="py-3 px-4 font-data-mono text-on-surface-variant">' +
			frappe.utils.escape_html(item.requirement_code) +
			"</td>" +
			'<td class="py-3 px-4 text-on-surface">' +
			'<div class="font-medium">' +
			frappe.utils.escape_html(item.title) +
			"</div>" +
			(summary
				? '<div class="text-[12px] text-on-surface-variant mt-0.5">' +
					frappe.utils.escape_html(summary) +
					"</div>"
				: "") +
			"</td>" +
			'<td class="py-3 px-4">' +
			plain_label_html(item.category || "—") +
			"</td>" +
			'<td class="py-3 px-4">' +
			treatmentHtml +
			"</td>" +
			'<td class="py-3 px-4">' +
			plain_label_html(item.response_format_label || "—") +
			"</td>" +
			'<td class="py-3 px-4">' +
			plain_label_html(item.evidence_level_label || "—", item.evidence_level_label === "Missing Evidence Instruction" ? "warning" : "") +
			"</td>" +
			'<td class="py-3 px-4">' +
			plain_label_html(item.acceptance_label || "—", item.acceptance_label === "Missing Criteria" ? "warning" : "") +
			"</td>" +
			'<td class="py-3 px-4">' +
			plain_label_html(item.status_label || "—", item.status_label === "Warning" ? "warning" : "") +
			"</td>" +
			'<td class="py-3 px-4 text-right"><div class="flex justify-end gap-2">' +
			'<button type="button" class="text-primary font-body-md text-[12px] font-medium hover:underline" data-itw-req-action="edit">Edit</button>' +
			'<button type="button" class="text-on-surface-variant font-body-md text-[12px] font-medium hover:underline" data-itw-req-action="view">View</button>' +
			'<button type="button" class="text-on-surface-variant font-body-md text-[12px] font-medium hover:underline" data-itw-req-action="review">Review</button>' +
			"</div></td></tr>"
		);
	}

	function hydrate_it_requirements_context(doc, data) {
		var panel = doc.querySelector("[data-itw-req-context]");
		if (!panel) {
			return;
		}
		var planning = data.planning_package || {};
		var entity = data.procuring_entity || {};
		var method = data.method || {};
		var validation = data.validation || {};
		var entityName = (entity.name || "").trim() || "—";
		var cells = panel.querySelectorAll(":scope .flex.flex-col");
		var values = [
			data.configuration_id || "—",
			data.title || "—",
			planning.code || planning.name || "—",
			entityName,
			format_method_reference(method),
			data.state_label || "—",
			String(validation.blockers || 0) +
				" Blockers / " +
				String(validation.warnings || 0) +
				" Warnings",
		];
		cells.forEach(function (cell, index) {
			if (index >= values.length) {
				return;
			}
			var valueNode = cell.querySelector(".font-data-mono, .font-body-md, .inline-flex, span");
			if (valueNode) {
				valueNode.textContent = values[index] || "—";
			}
		});
	}

	function hydrate_it_requirements_table(doc, data) {
		var host = doc.querySelector("[data-itw-req-table-host]");
		if (!host) {
			return;
		}
		var sections = data.sections || [];
		sections.forEach(function (section) {
			var heading = Array.prototype.find.call(host.querySelectorAll("h3"), function (node) {
				return (node.textContent || "").indexOf(section.title) >= 0;
			});
			if (!heading) {
				return;
			}
			var sectionWrap = heading.closest(".bg-surface-container-lowest");
			if (!sectionWrap) {
				return;
			}
			var countBadge = sectionWrap.querySelector("span.rounded-full");
			if (countBadge) {
				countBadge.textContent = String(section.item_count || 0) + " Items";
			}
			var tableWrap = sectionWrap.querySelector(".overflow-x-auto");
			var tbody = sectionWrap.querySelector("tbody");
			if (!tbody) {
				return;
			}
			if ((section.items || []).length) {
				if (tableWrap) {
					tableWrap.classList.remove("hidden");
				}
				tbody.innerHTML = (section.items || []).map(build_requirements_row_html).join("");
			} else {
				tbody.innerHTML = "";
				if (tableWrap) {
					tableWrap.classList.add("hidden");
				}
			}
		});
	}

	function set_req_control_value(doc, fieldKey, value) {
		var node = find_req_control(doc, fieldKey);
		if (!node) {
			return;
		}
		if (node.tagName === "TEXTAREA" || node.tagName === "SELECT" || node.tagName === "INPUT") {
			node.value = value || "";
		} else {
			node.textContent = value || "—";
		}
	}

	function hydrate_it_requirements_drawer(doc, data, options) {
		options = options || {};
		var drawer = doc.querySelector("[data-itw-req-drawer]");
		if (!drawer) {
			return;
		}
		var selected = null;
		(data.sections || []).some(function (section) {
			return (section.items || []).some(function (item) {
				if (item.requirement_code === data.selected_item_id) {
					selected = item;
					return true;
				}
				return false;
			});
		});
		if (!selected) {
			if (!options.keep_open) {
				close_it_requirements_drawer(doc);
			}
			return;
		}
		if (options.open !== false) {
			open_it_requirements_drawer(doc);
		}
		set_req_control_value(doc, "requirement_code", selected.requirement_code);
		set_req_control_value(doc, "title", selected.title);
		set_req_control_value(doc, "description", selected.description);
		set_req_control_value(doc, "category", selected.category || "");
		set_req_control_value(doc, "treatment", selected.treatment_label || selected.treatment || "Mandatory");
		set_req_control_value(
			doc,
			"response_format",
			REQ_RESPONSE_FORMAT_MAP[selected.response_format] || selected.response_format_label || "Yes/No",
		);
		set_req_control_value(doc, "bidder_instruction", selected.bidder_instruction || "");
		set_req_control_value(doc, "evidence_level", selected.evidence_level_label || "Evidence Required");
		set_req_control_value(doc, "evidence_instruction", selected.evidence_instruction || "");
		set_req_control_value(doc, "acceptance_criteria", selected.acceptance_criteria || "");
		set_req_control_value(
			doc,
			"evaluation_linked",
			selected.evaluation_linked ? "Linked to Evaluation: Yes" : "Linked to Evaluation: No",
		);
		set_req_control_value(
			doc,
			"evaluation_criterion",
			"Related Evaluation Criterion: " + (selected.evaluation_criterion_label || "—"),
		);
		set_req_control_value(
			doc,
			"contract_carry_forward_summary",
			"Carry Forward to Contract: " + (selected.contract_carry_forward_summary || "To Be Decided"),
		);
		var warningsList = drawer.querySelector("[data-itw-req-warnings-list]");
		if (warningsList) {
			warningsList.innerHTML = (selected.warnings || [])
				.map(function (warning) {
					return (
						'<li class="font-body-md text-[12px] text-on-surface-variant">' +
						frappe.utils.escape_html(warning) +
						"</li>"
					);
				})
				.join("");
		}
	}

	function hydrate_it_requirements_guidance(doc, data) {
		var panel = doc.querySelector("[data-itw-req-guidance]");
		if (!panel) {
			return;
		}
		var completion = data.completion || {};
		var gaps = completion.gaps || {};
		var completionNode = panel.querySelector("[data-itw-req-guidance-completion]");
		if (completionNode) {
			completionNode.textContent =
				String(completion.completed || 0) + "/" + String(completion.total || 0);
		}
		var progress = panel.querySelector(".bg-primary.h-2");
		if (progress) {
			progress.style.width = String(completion.percent || 0) + "%";
		}
		var gapList = panel.querySelector("[data-itw-req-guidance-gaps]");
		if (gapList) {
			gapList.innerHTML = "";
			if (gaps.missing_mandatory) {
				gapList.innerHTML +=
					'<li class="font-body-md text-[12px] text-on-surface-variant">Missing Mandatory Requirements: ' +
					gaps.missing_mandatory +
					"</li>";
			}
			if (gaps.missing_evidence_instructions) {
				gapList.innerHTML +=
					'<li class="font-body-md text-[12px] text-on-surface-variant">Missing Evidence Instructions: ' +
					gaps.missing_evidence_instructions +
					"</li>";
			}
			if (gaps.missing_acceptance_criteria) {
				gapList.innerHTML +=
					'<li class="font-body-md text-[12px] text-on-surface-variant">Missing Acceptance Criteria: ' +
					gaps.missing_acceptance_criteria +
					"</li>";
			}
			if (gaps.vendor_neutrality_warnings) {
				gapList.innerHTML +=
					'<li class="font-body-md text-[12px] text-on-surface-variant">Vendor-Neutrality Warnings: ' +
					gaps.vendor_neutrality_warnings +
					"</li>";
			}
		}
	}

	function hydrate_it_requirements_footer(doc, data) {
		var validation = data.validation || {};
		var warningsNode = doc.querySelector("[data-itw-req-warnings-remain]");
		var continueBtn = doc.querySelector("[data-itw-req-actions] button");
		if (warningsNode) {
			if ((validation.warnings || 0) > 0 && !(validation.blockers || 0)) {
				warningsNode.classList.remove("hidden");
			} else {
				warningsNode.classList.add("hidden");
			}
		}
		doc.querySelectorAll("[data-itw-req-actions] button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (text.indexOf("Continue to Implementation Schedule") >= 0) {
				if (validation.blockers > 0) {
					btn.disabled = true;
					btn.style.opacity = "0.55";
					btn.style.pointerEvents = "none";
					btn.setAttribute("aria-disabled", "true");
				} else {
					btn.disabled = false;
					btn.removeAttribute("aria-disabled");
					btn.style.opacity = "";
					btn.style.pointerEvents = "";
				}
			}
		});
	}

	function apply_it_requirements_payload(doc, data, options) {
		data = data || {};
		options = options || {};
		hydrate_it_requirements_context(doc, data);
		hydrate_it_requirements_table(doc, data);
		hydrate_it_requirements_guidance(doc, data);
		hydrate_it_requirements_footer(doc, data);
		if (data.selected_item_id && options.open_drawer) {
			hydrate_it_requirements_drawer(doc, data, { open: true });
		} else if (!options.keep_drawer_open) {
			close_it_requirements_drawer(doc);
		}
	}

	function collect_requirements_drawer_values(doc) {
		var values = {};
		var codeNode = find_req_control(doc, "requirement_code");
		if (codeNode) {
			values.requirement_code = (codeNode.textContent || "").trim();
		}
		var titleNode = find_req_control(doc, "title");
		if (titleNode) {
			values.title = (titleNode.textContent || titleNode.value || "").trim();
		}
		var description = find_req_control(doc, "description");
		if (description) {
			values.description = (description.value || "").trim();
		}
		var category = find_req_control(doc, "category");
		if (category) {
			values.category = (category.value || "").trim();
		}
		var treatment = find_req_control(doc, "treatment");
		if (treatment) {
			var treatmentLabel = (treatment.value || "").trim();
			values.treatment = treatmentLabel;
			values.priority = REQ_TREATMENT_REVERSE[treatmentLabel] || "MANDATORY";
		}
		var responseFormat = find_req_control(doc, "response_format");
		if (responseFormat) {
			var raw = (responseFormat.value || "").trim();
			values.response_format = REQ_RESPONSE_FORMAT_REVERSE[raw] || raw;
			values.response_format_label = raw;
		}
		var bidderInstruction = find_req_control(doc, "bidder_instruction");
		if (bidderInstruction) {
			values.bidder_instruction = (bidderInstruction.value || "").trim();
		}
		var evidenceLevel = find_req_control(doc, "evidence_level");
		if (evidenceLevel) {
			var evidenceLabel = (evidenceLevel.value || "").trim();
			values.evidence_level_label = evidenceLabel;
			values.evidence_level = REQ_EVIDENCE_LEVEL_REVERSE[evidenceLabel] || "REQUIRED";
			values.evidence_required = values.evidence_level === "NOT_REQUIRED" ? 0 : 1;
		}
		var evidenceInstruction = find_req_control(doc, "evidence_instruction");
		if (evidenceInstruction) {
			values.evidence_instruction = (evidenceInstruction.value || "").trim();
		}
		var acceptanceCriteria = find_req_control(doc, "acceptance_criteria");
		if (acceptanceCriteria) {
			values.acceptance_criteria = (acceptanceCriteria.value || "").trim();
		}
		return values;
	}

	function disable_it_requirements_stub_actions(doc) {
		doc.querySelectorAll("[data-itw-req-composer] button, [data-itw-req-actions] button, [data-itw-req-drawer] button").forEach(
			function (btn) {
				var text = (btn.textContent || "").trim();
				if (
					text.indexOf("Import Template") >= 0 ||
					text.indexOf("Add Requirement") >= 0 ||
					text.indexOf("Run Validation") >= 0 ||
					text.indexOf("Edit in Evaluation Setup") >= 0 ||
					text.indexOf("Edit in SCC") >= 0
				) {
					btn.disabled = true;
					btn.style.opacity = "0.55";
					btn.style.pointerEvents = "none";
					btn.setAttribute("aria-disabled", "true");
				}
			},
		);
	}

	function wire_it_requirements_interactions(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-req-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-req-wired", "1");

		function load_item(code, openDrawer) {
			call_api("get_it_requirements_api", {
				configuration_id: ctx.configuration_id,
			}).then(function (result) {
				var data = requirements_payload_data(result);
				data.selected_item_id = code;
				apply_it_requirements_payload(doc, data, { open_drawer: !!openDrawer });
			});
		}

		function save_requirements() {
			var drawerValues = collect_requirements_drawer_values(doc);
			call_api("save_it_requirements_api", {
				configuration_id: ctx.configuration_id,
				requirements_json: JSON.stringify({
					selected_item_id: drawerValues.requirement_code,
					selected_item: drawerValues,
				}),
			})
				.then(function (result) {
					frappe.show_alert({
						message: __("Requirements saved"),
						indicator: "green",
					});
					var data = requirements_payload_data(result);
					apply_it_requirements_payload(doc, data, {
						open_drawer: true,
						keep_drawer_open: true,
					});
				})
				.catch(function (err) {
					frappe.show_alert({
						indicator: "red",
						message: (err && err.message) || __("Unable to save requirements."),
					});
				});
		}

		doc.addEventListener(
			"click",
			function (event) {
				var row = event.target && event.target.closest ? event.target.closest("[data-itw-req-row]") : null;
				if (row) {
					event.preventDefault();
					var code = row.getAttribute("data-itw-req-code");
					var actionBtn = event.target.closest("[data-itw-req-action]");
					var action = actionBtn ? actionBtn.getAttribute("data-itw-req-action") : "edit";
					load_item(code, action === "edit" || action === "review");
					return;
				}
				var closeBtn = event.target && event.target.closest ? event.target.closest("[data-itw-req-drawer-close], [data-itw-req-drawer-cancel]") : null;
				if (closeBtn) {
					event.preventDefault();
					close_it_requirements_drawer(doc);
					return;
				}
				var btn = event.target && event.target.closest ? event.target.closest("button") : null;
				if (!btn) {
					return;
				}
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Save Requirements") >= 0 || text.indexOf("Update Requirement") >= 0) {
					event.preventDefault();
					save_requirements();
				}
				if (text.indexOf("Continue to Implementation Schedule") >= 0) {
					event.preventDefault();
					navigate("it-tender-configuration-implementation-schedule", {
						configuration_id: ctx.configuration_id,
					});
				}
			},
			true,
		);
	}

	function fetch_it_requirements_data(ctx) {
		return call_api("get_it_requirements_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				it_requirements: (result && result.message) || {},
			};
		});
	}

	var it_schedule_cache = {};

	function install_it_schedule_layout_styles(doc) {
		if (!doc || doc.getElementById("itw-sched-layout-style")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "itw-sched-layout-style";
		style.textContent =
			"html.it-wizard-implementation-schedule-root, body.it-wizard-implementation-schedule-layout {" +
			"height: 100%; margin: 0; overflow: hidden;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout {" +
			"display: flex; flex-direction: column; min-height: 0; max-height: 100%;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout > header {" +
			"flex-shrink: 0; position: relative !important; top: auto !important;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-context] {" +
			"flex-shrink: 0;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-main] {" +
			"flex: 1 1 0; min-height: 0; overflow: hidden;" +
			"display: flex; flex-direction: row;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-composer] {" +
			"display: flex; flex-direction: column; flex: 1 1 0; min-height: 0;" +
			"overflow: hidden !important; position: relative;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-table-host] {" +
			"flex: 1 1 0; min-height: 0; overflow-y: auto; -webkit-overflow-scrolling: touch;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-actions] {" +
			"flex-shrink: 0; position: relative !important; bottom: auto !important;" +
			"left: auto !important; right: auto !important; width: 100%; z-index: 30;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-drawer] {" +
			"transform: translateX(100%); z-index: 60;" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-drawer][data-itw-sched-drawer-open='1'] {" +
			"transform: translateX(0);" +
			"}" +
			"body.it-wizard-implementation-schedule-layout [data-itw-sched-guidance] {" +
			"display: flex !important; flex-direction: column; min-height: 0; max-height: 100%;" +
			"}";
		doc.head.appendChild(style);
	}

	function harmonize_it_schedule_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_it_schedule_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-implementation-schedule-root");
		}
		doc.body.classList.add("it-wizard-implementation-schedule-layout");
		doc.body.classList.remove("min-h-screen");
		doc.body.classList.add("h-full", "overflow-hidden");
		if (doc.documentElement) {
			doc.documentElement.classList.add("h-full");
		}
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		var main = doc.querySelector("main");
		if (main) {
			main.classList.add("min-h-0");
			main.setAttribute("data-itw-sched-main", "1");
		}
		var footer = doc.querySelector("footer[data-itw-sched-actions], [data-itw-sched-actions]");
		if (footer) {
			footer.classList.remove("fixed", "absolute", "bottom-0", "left-0", "right-0");
		}
		enhance_it_schedule_layout(doc);
	}

	function enhance_it_schedule_layout(doc) {
		var context = doc.querySelector("[data-itw-sched-context]");
		if (!context) {
			context = doc.querySelector("body > header + div");
			if (context) {
				context.setAttribute("data-itw-sched-context", "1");
			}
		}
		var main = doc.querySelector("[data-itw-sched-main]");
		if (main) {
			var composer = main.querySelector("[data-itw-sched-composer]");
			if (!composer) {
				composer = main.querySelector(":scope > .flex-1.flex.flex-col");
				if (composer) {
					composer.setAttribute("data-itw-sched-composer", "1");
				}
			}
			if (composer) {
				composer.classList.add("min-h-0");
				composer.classList.remove("overflow-y-auto");
				composer.classList.add("overflow-hidden");
			}
			var tableHost = doc.querySelector("[data-itw-sched-table-host]");
			if (tableHost) {
				tableHost.classList.add("min-h-0");
			}
		}
		var guidance = doc.querySelector("[data-itw-sched-guidance]");
		if (guidance) {
			guidance.classList.remove("hidden");
			guidance.classList.add("flex");
		}
		var drawer = doc.querySelector("[data-itw-sched-drawer]");
		if (drawer) {
			drawer.setAttribute("data-itw-sched-drawer-hidden", "1");
			drawer.removeAttribute("data-itw-sched-drawer-open");
		}
		strip_it_schedule_fixture_scripts(doc);
	}

	function strip_it_schedule_fixture_scripts(doc) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-sched-scripts-stripped") === "1") {
			return;
		}
		doc.querySelectorAll("body > script").forEach(function (node) {
			node.parentNode.removeChild(node);
		});
		doc.body.setAttribute("data-itw-sched-scripts-stripped", "1");
	}

	function find_sched_control(doc, fieldKey) {
		return doc.querySelector('[data-itw-field="' + fieldKey + '"]');
	}

	function schedule_payload_data(source) {
		return unwrap_envelope_data(source);
	}

	function open_it_schedule_drawer(doc) {
		var drawer = doc.querySelector("[data-itw-sched-drawer]");
		if (!drawer) {
			return;
		}
		drawer.setAttribute("data-itw-sched-drawer-open", "1");
		drawer.removeAttribute("data-itw-sched-drawer-hidden");
	}

	function close_it_schedule_drawer(doc) {
		var drawer = doc.querySelector("[data-itw-sched-drawer]");
		if (!drawer) {
			return;
		}
		drawer.removeAttribute("data-itw-sched-drawer-open");
		drawer.setAttribute("data-itw-sched-drawer-hidden", "1");
	}

	function schedule_status_badge_html(status, label) {
		var cls = "bg-surface-container text-on-surface-variant";
		if (status === "COMPLETE") {
			cls = "bg-status-available/10 text-status-available";
		} else if (status === "IN_PROGRESS") {
			cls = "bg-status-reserved/10 text-status-reserved";
		} else if (status === "INCOMPLETE") {
			cls = "bg-error-container text-on-error-container";
		}
		return (
			'<span class="inline-flex items-center px-2 py-0.5 rounded-full font-label-caps text-[11px] ' +
			cls +
			'">' +
			frappe.utils.escape_html(label || status || "—") +
			"</span>"
		);
	}

	function build_schedule_row_html(phase) {
		var rowClass = "border-b border-subtle hover:bg-surface-container-low transition-colors group";
		if (phase.status === "INCOMPLETE") {
			rowClass += " bg-error-container/5";
		}
		return (
			'<tr class="' +
			rowClass +
			'" data-itw-sched-row="1" data-itw-sched-code="' +
			frappe.utils.escape_html(phase.phase_code || "") +
			'">' +
			'<td class="p-4 text-center font-data-mono text-on-surface-variant">' +
			frappe.utils.escape_html(String(phase.display_order || "—")) +
			"</td>" +
			'<td class="p-4 font-body-md text-on-surface font-medium">' +
			frappe.utils.escape_html(phase.title || "—") +
			"</td>" +
			'<td class="p-4 font-body-md text-on-surface-variant">' +
			frappe.utils.escape_html(phase.duration_label || "—") +
			"</td>" +
			'<td class="p-4 font-body-md text-on-surface-variant">' +
			frappe.utils.escape_html(phase.start_trigger || "—") +
			"</td>" +
			'<td class="p-4 font-body-md text-on-surface-variant max-w-[220px] truncate">' +
			frappe.utils.escape_html(phase.key_deliverable_summary || "—") +
			"</td>" +
			'<td class="p-4 font-body-md text-on-surface-variant">' +
			frappe.utils.escape_html(phase.acceptance_label || "—") +
			"</td>" +
			'<td class="p-4">' +
			schedule_status_badge_html(phase.status, phase.status_label) +
			"</td>" +
			'<td class="p-4 text-right whitespace-nowrap">' +
			'<button class="text-primary font-body-md text-[13px] hover:underline mr-3" data-itw-sched-action="edit" type="button">Edit</button>' +
			'<button class="text-on-surface-variant font-body-md text-[13px] hover:underline" data-itw-sched-action="view" type="button">View</button>' +
			"</td></tr>"
		);
	}

	function hydrate_it_schedule_context(doc, data) {
		var panel = doc.querySelector("[data-itw-sched-context]");
		if (!panel) {
			return;
		}
		var planning = data.planning_package || {};
		var entity = data.procuring_entity || {};
		var method = data.method || {};
		var validation = data.validation || {};
		var entityName = (entity.name || "").trim() || "—";
		var cells = panel.querySelectorAll(":scope .flex.flex-col");
		var values = [
			data.tender_number || data.configuration_id || "—",
			data.title || "—",
			planning.code || planning.name || "—",
			entityName,
			format_method_reference(method),
			data.state_label || "—",
			String(validation.blockers || 0) +
				" Blockers / " +
				String(validation.warnings || 0) +
				" Warnings",
		];
		cells.forEach(function (cell, index) {
			if (index >= values.length) {
				return;
			}
			// The first span is the muted label; the value span is the last span.
			var spans = cell.querySelectorAll("span");
			var valueNode = spans.length ? spans[spans.length - 1] : null;
			if (valueNode) {
				valueNode.textContent = values[index] || "—";
			}
		});
	}

	function hydrate_it_schedule_table(doc, data) {
		var phases = data.phases || [];
		var countNode = doc.querySelector("[data-itw-sched-phase-count]");
		if (countNode) {
			countNode.textContent = __("Defined Phases ({0})", [phases.length]);
		}
		var durationNode = doc.querySelector("[data-itw-sched-total-duration]");
		if (durationNode) {
			durationNode.textContent = data.total_duration_label || "—";
		}
		var tbody = doc.querySelector("[data-itw-sched-table] tbody");
		if (tbody) {
			tbody.innerHTML = phases.map(build_schedule_row_html).join("");
		}
		var model = (data.implementation_model || "PHASED").trim();
		doc.querySelectorAll('[data-itw-field="implementation_model"]').forEach(function (input) {
			input.checked = (input.value || "").trim() === model;
			var label = input.closest("label");
			if (label) {
				label.classList.toggle("border-2", input.checked);
				label.classList.toggle("border-primary", input.checked);
				label.classList.toggle("bg-primary-fixed/10", input.checked);
				label.classList.toggle("border", !input.checked);
				label.classList.toggle("border-subtle", !input.checked);
			}
		});
		hydrate_it_schedule_mode(doc, data);
	}

	function find_turnkey_control(doc, fieldKey) {
		return doc.querySelector('[data-itw-turnkey-field="' + fieldKey + '"]');
	}

	function hydrate_it_schedule_mode(doc, data) {
		var model = (data.implementation_model || "PHASED").trim();
		var isTurnkey = model === "SINGLE_TURNKEY";
		doc.querySelectorAll("[data-itw-sched-mode-host]").forEach(function (host) {
			var hostMode = host.getAttribute("data-itw-sched-mode-host");
			host.classList.toggle("hidden", isTurnkey ? hostMode !== "single-turnkey" : hostMode !== "phased");
		});
		var addPhase = doc.querySelector("[data-itw-sched-add-phase]");
		if (addPhase) {
			addPhase.classList.toggle("hidden", isTurnkey);
		}
		var turnkey = data.single_turnkey || {};
		Object.keys(turnkey).forEach(function (fieldKey) {
			var control = find_turnkey_control(doc, fieldKey);
			if (control) {
				control.value = turnkey[fieldKey] == null ? "" : String(turnkey[fieldKey]);
			}
		});
		var subtitle = doc.querySelector("[data-itw-sched-subtitle]");
		if (subtitle) {
			subtitle.textContent = isTurnkey
				? __("Define one unified delivery milestone, acceptance threshold, and contract obligation.")
				: __("Define delivery phases, milestones, deliverables, and acceptance checkpoints.");
		}
	}

	function collect_single_turnkey_values(doc) {
		var values = {};
		doc.querySelectorAll("[data-itw-turnkey-field]").forEach(function (control) {
			values[control.getAttribute("data-itw-turnkey-field")] = (control.value || "").trim();
		});
		return values;
	}

	function primary_schedule_milestone(phase) {
		var milestones = phase.milestones || [];
		return (
			milestones.find(function (row) {
				return row.milestone_type === "OPERATIONAL_ACCEPTANCE";
			}) ||
			milestones.find(function (row) {
				return int(row.acceptance_required);
			}) ||
			milestones[0] ||
			null
		);
	}

	function int(value) {
		return parseInt(value, 10) || 0;
	}

	function hydrate_it_schedule_guidance(doc, data) {
		var panel = doc.querySelector("[data-itw-sched-guidance]");
		if (!panel) {
			return;
		}
		var completion = data.completion || {};
		var completed = completion.completed_phases || 0;
		var total = completion.total_phases || 0;
		var percent = completion.percent || 0;
		var completionNode = doc.querySelector("[data-itw-sched-guidance-completion]");
		if (completionNode) {
			completionNode.textContent = completed + "/" + total;
		}
		var progress = panel.querySelector(".bg-primary.h-2");
		if (progress) {
			progress.style.width = String(percent) + "%";
		}
		var gapList = doc.querySelector("[data-itw-sched-guidance-gaps]");
		if (gapList) {
			gapList.innerHTML = "";
			var gaps = completion.gaps || {};
			if (gaps.incomplete_phases) {
				gapList.innerHTML +=
					'<li class="font-body-md text-[12px] text-on-surface-variant">Incomplete Phases: ' +
					gaps.incomplete_phases +
					"</li>";
			}
			if (gaps.missing_acceptance_criteria) {
				gapList.innerHTML +=
					'<li class="font-body-md text-[12px] text-on-surface-variant">Missing Acceptance Criteria: ' +
					gaps.missing_acceptance_criteria +
					"</li>";
			}
			if (gaps.missing_phase_milestones) {
				gapList.innerHTML +=
					'<li class="font-body-md text-[12px] text-on-surface-variant">Missing Phase Milestones: ' +
					gaps.missing_phase_milestones +
					"</li>";
			}
			if (!gapList.innerHTML) {
				gapList.innerHTML =
					'<li class="font-body-md text-[12px] text-on-surface-variant">' +
					__("All required schedule fields complete.") +
					"</li>";
			}
		}
		var nextNode = doc.querySelector("[data-itw-sched-guidance-next]");
		if (nextNode) {
			var missing = completion.missing_fields || [];
			nextNode.textContent = missing.length
				? missing.join("; ")
				: data.implementation_model === "SINGLE_TURNKEY"
					? __("Review the unified delivery and acceptance criteria before continuing.")
					: __("Review each phase and confirm acceptance criteria before continuing.");
		}
	}

	function set_sched_control_value(doc, fieldKey, value) {
		var node = find_sched_control(doc, fieldKey);
		if (!node) {
			return;
		}
		if (node.tagName === "TEXTAREA" || node.tagName === "INPUT") {
			if (node.type === "checkbox") {
				node.checked = !!value;
			} else {
				node.value = value == null ? "" : String(value);
			}
		} else {
			node.textContent = value == null ? "—" : String(value);
		}
	}

	function schedule_source_text(meta) {
		meta = meta || {};
		if (meta.locked) {
			return __("Source: {0}. Locked: cannot be edited here.", [meta.source_label || __("System")]);
		}
		return __("Source: {0}", [meta.source_label || __("User-entered")]);
	}

	var SCHEDULE_TEMPLATE_DEFAULTS = {
		PHASE_1: {
			duration_label: "3 Months",
			start_trigger: "Contract signing and notice to proceed",
			key_deliverable_summary:
				"Approved project plan, configured core modules, and signed requirements baseline.",
		},
		PHASE_2: {
			duration_label: "6 Months",
			start_trigger: "Phase 1 operational acceptance certificate",
			key_deliverable_summary: "Integrated solution with signed SIT/UAT evidence.",
		},
		PHASE_3: {
			duration_label: "9 Months",
			start_trigger: "Phase 2 UAT sign-off",
			key_deliverable_summary: "Production deployment with signed operational acceptance certificate.",
		},
	};

	var TURNKEY_TEMPLATE_DEFAULTS = {
		expected_delivery_duration: "12 Months",
		delivery_trigger: "Contract signing and notice to proceed",
		key_deliverables:
			"Configured solution, migrated data, integrated interfaces, trained users, and signed operational acceptance.",
		unified_acceptance_criteria:
			"All contracted deliverables accepted under one operational acceptance certificate.",
		evidence_required: "Signed OAC, go-live evidence, and hypercare completion report.",
		carry_forward_decision: "YES",
	};

	function schedule_field_sources_for_phase(phase) {
		var sources = (phase && phase.field_sources) || {};
		if (Object.keys(sources).length) {
			return sources;
		}
		phase = phase || {};
		var code = (phase.phase_code || "").trim();
		var template = SCHEDULE_TEMPLATE_DEFAULTS[code] || {};
		var deliverable = (phase.key_deliverable_summary || "").trim();
		var templateDeliverable = (template.key_deliverable_summary || "").trim();
		return {
			phase_code: {
				source_type: "SYSTEM",
				source_label: "System-generated phase identifier",
				template_value: code,
				editable: false,
				locked: true,
			},
			duration_label: {
				source_type: "TEMPLATE",
				source_label: "Standard IT Schedule Template",
				template_value: template.duration_label || phase.duration_label || "",
				editable: true,
				locked: false,
			},
			start_trigger: {
				source_type: "DERIVED",
				source_label: "Derived from phase sequence",
				template_value: template.start_trigger || phase.start_trigger || "",
				editable: true,
				locked: false,
			},
			deliverables: {
				source_type: deliverable && deliverable !== templateDeliverable ? "USER_ENTERED" : "TEMPLATE",
				source_label: deliverable && deliverable !== templateDeliverable ? "User-entered" : "Template + user configuration",
				template_value: templateDeliverable,
				editable: true,
				locked: false,
			},
			acceptance_criteria: {
				source_type: "USER_ENTERED",
				source_label: "User configuration",
				template_value: "",
				editable: true,
				locked: false,
			},
			evidence_required: {
				source_type: "TEMPLATE",
				source_label: "Template + user configuration",
				template_value: "",
				editable: true,
				locked: false,
			},
			carry_forward_to_contract: {
				source_type: "DEFAULT",
				source_label: "Schedule defaults (editable)",
				template_value: "1",
				editable: true,
				locked: false,
			},
		};
	}

	function hydrate_it_schedule_field_sources(doc, phase) {
		var sources = schedule_field_sources_for_phase(phase);
		Object.keys(sources).forEach(function (fieldKey) {
			var meta = sources[fieldKey] || {};
			var sourceNode = doc.querySelector('[data-itw-sched-source="' + fieldKey + '"]');
			if (sourceNode) {
				sourceNode.textContent = schedule_source_text(meta);
			}
			var control = find_sched_control(doc, fieldKey);
			if (!control) {
				return;
			}
			if (meta.locked) {
				control.setAttribute("readonly", "readonly");
				control.setAttribute("aria-readonly", "true");
				if (control.tagName === "INPUT" || control.tagName === "TEXTAREA") {
					control.classList.add("bg-surface-container-low", "cursor-not-allowed");
				}
			} else {
				control.removeAttribute("readonly");
				control.removeAttribute("aria-readonly");
				if (control.tagName === "INPUT" || control.tagName === "TEXTAREA") {
					control.classList.remove("cursor-not-allowed");
					if (!control.classList.contains("bg-surface-container-lowest")) {
						control.classList.remove("bg-surface-container-low");
					}
				}
			}
			var fieldWrap = doc.querySelector('[data-itw-sched-field="' + fieldKey + '"]');
			if (!fieldWrap) {
				return;
			}
			fieldWrap.querySelectorAll("[data-itw-sched-field-action]").forEach(function (btn) {
				var action = btn.getAttribute("data-itw-sched-field-action") || "";
				var show = !meta.locked;
				if (action === "reset") {
					show = show && !!(meta.template_value || "").length;
					if (show) {
						btn.setAttribute("data-itw-sched-reset-value", String(meta.template_value));
					}
				}
				btn.style.display = show ? "" : "none";
			});
			if (meta.template_value !== undefined && meta.template_value !== null) {
				fieldWrap.setAttribute("data-itw-sched-template-value", String(meta.template_value));
			}
		});
	}

	function focus_sched_field(doc, fieldKey) {
		var node = find_sched_control(doc, fieldKey);
		if (!node || node.getAttribute("readonly") === "readonly") {
			return;
		}
		node.focus();
		if (typeof node.select === "function") {
			node.select();
		}
	}

	function handle_it_schedule_field_action(doc, fieldActionBtn) {
		if (!fieldActionBtn) {
			return false;
		}
		var fieldKey = fieldActionBtn.getAttribute("data-itw-sched-field-key") || "";
		var action = fieldActionBtn.getAttribute("data-itw-sched-field-action") || "";
		if (!fieldKey || !action) {
			return false;
		}
		if (action === "edit" || action === "override") {
			focus_sched_field(doc, fieldKey);
			return true;
		}
		if (action === "reset") {
			reset_sched_field_to_template(doc, null, fieldKey);
			return true;
		}
		return false;
	}

	function handle_it_turnkey_field_action(doc, fieldActionBtn) {
		if (!fieldActionBtn) {
			return false;
		}
		var fieldKey = fieldActionBtn.getAttribute("data-itw-turnkey-field-key") || "";
		var action = fieldActionBtn.getAttribute("data-itw-turnkey-field-action") || "";
		if (!fieldKey || !action) {
			return false;
		}
		var control = doc.querySelector('[data-itw-turnkey-field="' + fieldKey + '"]');
		if (!control) {
			return false;
		}
		if (action === "edit") {
			control.focus();
			return true;
		}
		if (action === "reset") {
			var templateValue = TURNKEY_TEMPLATE_DEFAULTS[fieldKey];
			if (templateValue === undefined) {
				return true;
			}
			control.value = templateValue;
			var source = doc.querySelector('[data-itw-turnkey-source="' + fieldKey + '"]');
			if (source) {
				source.textContent = __("Source: Standard IT Schedule Template");
			}
			return true;
		}
		return false;
	}

	function reset_sched_field_to_template(doc, phase, fieldKey) {
		var resetBtn = doc.querySelector(
			'[data-itw-sched-field-action="reset"][data-itw-sched-field-key="' + fieldKey + '"]',
		);
		var fieldWrap = doc.querySelector('[data-itw-sched-field="' + fieldKey + '"]');
		var codeNode = find_sched_control(doc, "phase_code");
		var phaseCode = codeNode ? (codeNode.textContent || "").trim() : "";
		var sources = schedule_field_sources_for_phase(phase || { phase_code: phaseCode });
		var meta = sources[fieldKey] || {};
		var templateValue =
			(resetBtn && resetBtn.getAttribute("data-itw-sched-reset-value")) ||
			(fieldWrap && fieldWrap.getAttribute("data-itw-sched-template-value")) ||
			meta.template_value ||
			"";
		if (!templateValue) {
			return;
		}
		set_sched_control_value(doc, fieldKey, templateValue);
		focus_sched_field(doc, fieldKey);
	}

	function wire_it_schedule_field_actions(doc) {
		// Field actions are handled via capture delegation in wire_it_schedule_interactions.
	}

	function hydrate_it_schedule_drawer(doc, data, options) {
		options = options || {};
		var phaseCode = data.selected_phase_id || data.selected_phase_code || "";
		var phase = (data.phases || []).find(function (row) {
			return row.phase_code === phaseCode;
		});
		if (!phase) {
			if (options.open) {
				close_it_schedule_drawer(doc);
			}
			return;
		}
		var milestone = primary_schedule_milestone(phase);
		set_sched_control_value(doc, "phase_seq", phase.display_order || "—");
		set_sched_control_value(doc, "title", phase.title || "");
		set_sched_control_value(doc, "phase_code", phase.phase_code || "—");
		set_sched_control_value(doc, "duration_label", phase.duration_label || "");
		set_sched_control_value(doc, "start_trigger", phase.start_trigger || "");
		var deliverables = (phase.key_deliverable_summary || "").trim();
		if (!deliverables && milestone && (milestone.deliverables || []).length) {
			deliverables = (milestone.deliverables || []).join("\n");
		}
		set_sched_control_value(doc, "deliverables", deliverables);
		var acceptance = milestone ? milestone.acceptance_criteria_text || "" : "";
		set_sched_control_value(doc, "acceptance_criteria", acceptance);
		var evidence = milestone && (milestone.evidence_required || []).length ? milestone.evidence_required.join("\n") : "";
		set_sched_control_value(doc, "evidence_required", evidence);
		set_sched_control_value(doc, "carry_forward_to_contract", int(phase.carry_forward_to_contract));
		hydrate_it_schedule_field_sources(doc, phase);
		wire_it_schedule_field_actions(doc);
		if (options.open) {
			open_it_schedule_drawer(doc);
		}
	}

	function hydrate_it_schedule_footer(doc, data) {
		var validation = data.validation || {};
		var warningsNode = doc.querySelector("[data-itw-sched-warnings-remain]");
		if (warningsNode) {
			if ((validation.warnings || 0) > 0 && !(validation.blockers || 0)) {
				warningsNode.classList.remove("hidden");
			} else {
				warningsNode.classList.add("hidden");
			}
		}
		doc.querySelectorAll("[data-itw-sched-actions] button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (text.indexOf("Continue to System Inventory") >= 0) {
				var completion = data.completion || {};
				var gaps = completion.gaps || {};
				var blockers = validation.blockers || 0;
				var incomplete =
					blockers > 0 ||
					(completion.completed_phases || 0) < (completion.total_phases || 0) ||
					(gaps.missing_acceptance_criteria || 0) > 0;
				if (incomplete) {
					btn.disabled = true;
					btn.style.opacity = "0.55";
					btn.style.pointerEvents = "none";
					btn.setAttribute("aria-disabled", "true");
				} else {
					btn.disabled = false;
					btn.removeAttribute("aria-disabled");
					btn.style.opacity = "";
					btn.style.pointerEvents = "";
				}
			}
		});
	}

	function apply_it_schedule_payload(doc, data, options) {
		data = data || {};
		options = options || {};
		it_schedule_cache = data;
		hydrate_it_schedule_context(doc, data);
		hydrate_it_schedule_table(doc, data);
		hydrate_it_schedule_guidance(doc, data);
		hydrate_it_schedule_footer(doc, data);
		if (data.selected_phase_id && options.open_drawer) {
			hydrate_it_schedule_drawer(doc, data, { open: true });
		} else if (!options.keep_drawer_open) {
			close_it_schedule_drawer(doc);
		}
	}

	function collect_schedule_drawer_values(doc) {
		var codeNode = find_sched_control(doc, "phase_code");
		var code = codeNode ? (codeNode.textContent || "").trim() : "";
		var phase = (it_schedule_cache.phases || []).find(function (row) {
			return row.phase_code === code;
		});
		if (!phase) {
			phase = { phase_code: code, milestones: [] };
		}
		phase = JSON.parse(JSON.stringify(phase));
		var titleNode = find_sched_control(doc, "title");
		if (titleNode) {
			phase.title = (titleNode.textContent || titleNode.value || "").trim();
		}
		var durationNode = find_sched_control(doc, "duration_label");
		if (durationNode) {
			phase.duration_label = (durationNode.textContent || durationNode.value || "").trim();
		}
		var triggerNode = find_sched_control(doc, "start_trigger");
		if (triggerNode) {
			phase.start_trigger = (triggerNode.textContent || triggerNode.value || "").trim();
		}
		var deliverablesNode = find_sched_control(doc, "deliverables");
		if (deliverablesNode) {
			var deliverablesText = (deliverablesNode.value || "").trim();
			phase.key_deliverable_summary = deliverablesText;
		}
		var acceptanceNode = find_sched_control(doc, "acceptance_criteria");
		var evidenceNode = find_sched_control(doc, "evidence_required");
		var carryNode = find_sched_control(doc, "carry_forward_to_contract");
		if (carryNode) {
			phase.carry_forward_to_contract = carryNode.checked ? 1 : 0;
		}
		var milestone = primary_schedule_milestone(phase);
		if (!milestone) {
			milestone = {
				phase_code: phase.phase_code,
				milestone_code: phase.phase_code + "-OA",
				milestone_type: "OPERATIONAL_ACCEPTANCE",
				title: "Operational Acceptance",
				display_order: 99,
				acceptance_required: 1,
				deliverables: [],
				evidence_required: [],
			};
			phase.milestones = phase.milestones || [];
			phase.milestones.push(milestone);
		}
		if (deliverablesNode) {
			milestone.deliverables = (deliverablesNode.value || "")
				.split("\n")
				.map(function (line) {
					return line.trim();
				})
				.filter(Boolean);
		}
		if (acceptanceNode) {
			milestone.acceptance_criteria_text = (acceptanceNode.value || "").trim();
			milestone.acceptance_required = milestone.acceptance_criteria_text ? 1 : milestone.acceptance_required;
		}
		if (evidenceNode) {
			milestone.evidence_required = (evidenceNode.value || "")
				.split("\n")
				.map(function (line) {
					return line.trim();
				})
				.filter(Boolean);
		}
		return phase;
	}

	function disable_it_schedule_stub_actions(doc) {
		doc.querySelectorAll("[data-itw-sched-composer] button, [data-itw-sched-actions] button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (text.indexOf("Use Standard IT Schedule Template") >= 0) {
				btn.hidden = true;
				btn.disabled = true;
				btn.setAttribute("aria-disabled", "true");
				btn.setAttribute(
					"title",
					__("Template apply is not yet wired; use Reset to Template on individual fields."),
				);
				return;
			}
			if (text.indexOf("Add Phase") >= 0 || text.indexOf("Run Validation") >= 0) {
				btn.disabled = true;
				btn.style.opacity = "0.55";
				btn.style.pointerEvents = "none";
				btn.setAttribute("aria-disabled", "true");
			}
		});
	}

	function confirm_single_turnkey_switch(onConfirm, onCancel) {
		var dialog = new frappe.ui.Dialog({
			title: __("Switch to Single Turnkey Delivery?"),
			primary_action_label: __("Switch to Single Delivery"),
			primary_action: function () {
				dialog.hide();
				onConfirm();
			},
			secondary_action_label: __("Cancel"),
			secondary_action: function () {
				dialog.hide();
				onCancel();
			},
		});
		dialog.$body.append(
			'<p class="mb-3">' +
				__("This will replace the phased schedule with one unified delivery milestone.") +
				"</p>" +
				'<p class="text-muted">' +
				__("Existing phase details will be retained and restored if you switch back to Phased Delivery.") +
				"</p>",
		);
		dialog.show();
	}

	function wire_it_schedule_interactions(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		if (doc.body.getAttribute("data-itw-sched-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-sched-wired", "1");

		function load_phase(code, openDrawer) {
			call_api("get_implementation_schedule_api", {
				configuration_id: ctx.configuration_id,
			}).then(function (result) {
				var data = schedule_payload_data(result);
				data.selected_phase_id = code;
				apply_it_schedule_payload(doc, data, { open_drawer: !!openDrawer });
			});
		}

		function save_schedule(openDrawer) {
			var modelInput = doc.querySelector('[data-itw-field="implementation_model"]:checked');
			var model = modelInput ? modelInput.value : (it_schedule_cache.implementation_model || "PHASED");
			var phase = null;
			var schedulePayload = { implementation_model: model };
			if (model === "SINGLE_TURNKEY") {
				schedulePayload.single_turnkey = collect_single_turnkey_values(doc);
			} else if (openDrawer) {
				phase = collect_schedule_drawer_values(doc);
				schedulePayload.selected_phase_id = phase.phase_code;
				schedulePayload.selected_phase = phase;
			}
			call_api("save_implementation_schedule_api", {
				configuration_id: ctx.configuration_id,
				schedule_json: JSON.stringify(schedulePayload),
			})
				.then(function (result) {
					frappe.show_alert({
						message: __("Schedule saved"),
						indicator: "green",
					});
					var data = schedule_payload_data(result);
					if (phase) {
						data.selected_phase_id = phase.phase_code;
					}
					apply_it_schedule_payload(doc, data, {
						open_drawer: !!openDrawer && !!phase,
						keep_drawer_open: !!openDrawer && !!phase,
					});
				})
				.catch(function (err) {
					frappe.show_alert({
						indicator: "red",
						message: (err && err.message) || __("Unable to save schedule."),
					});
				});
		}

		doc.addEventListener("change", function (event) {
			var modelInput =
				event.target && event.target.matches
					? event.target.matches('[data-itw-field="implementation_model"]')
						? event.target
						: null
					: null;
			if (!modelInput) {
				return;
			}
			var nextModel = (modelInput.value || "").trim();
			var currentModel = (it_schedule_cache.implementation_model || "PHASED").trim();
			if (nextModel === currentModel) {
				return;
			}
			function applyModel() {
				var nextData = Object.assign({}, it_schedule_cache, {
					implementation_model: nextModel,
				});
				apply_it_schedule_payload(doc, nextData, { keep_drawer_open: false });
				save_schedule(false);
			}
			function restoreCurrentModel() {
				doc.querySelectorAll('[data-itw-field="implementation_model"]').forEach(function (input) {
					input.checked = (input.value || "").trim() === currentModel;
				});
				hydrate_it_schedule_mode(doc, it_schedule_cache);
			}
			if (nextModel === "SINGLE_TURNKEY" && (it_schedule_cache.phases || []).length) {
				confirm_single_turnkey_switch(applyModel, restoreCurrentModel);
				return;
			}
			applyModel();
		});

		doc.addEventListener(
			"click",
			function (event) {
				var fieldActionBtn =
					event.target && event.target.closest
						? event.target.closest("[data-itw-sched-field-action]")
						: null;
				if (fieldActionBtn && handle_it_schedule_field_action(doc, fieldActionBtn)) {
					event.preventDefault();
					event.stopPropagation();
					return;
				}
				var turnkeyActionBtn =
					event.target && event.target.closest
						? event.target.closest("[data-itw-turnkey-field-action]")
						: null;
				if (turnkeyActionBtn && handle_it_turnkey_field_action(doc, turnkeyActionBtn)) {
					event.preventDefault();
					event.stopPropagation();
					return;
				}
				var row = event.target && event.target.closest ? event.target.closest("[data-itw-sched-row]") : null;
				if (row) {
					event.preventDefault();
					var code = row.getAttribute("data-itw-sched-code");
					var actionBtn = event.target.closest("[data-itw-sched-action]");
					var action = actionBtn ? actionBtn.getAttribute("data-itw-sched-action") : "edit";
					load_phase(code, action === "edit" || action === "view");
					return;
				}
				var closeBtn =
					event.target && event.target.closest
						? event.target.closest("[data-itw-sched-drawer-close], [data-itw-sched-drawer-cancel]")
						: null;
				if (closeBtn) {
					event.preventDefault();
					close_it_schedule_drawer(doc);
					return;
				}
				var btn = event.target && event.target.closest ? event.target.closest("button") : null;
				if (!btn) {
					return;
				}
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Save Schedule") >= 0 || text.indexOf("Save Changes") >= 0) {
					event.preventDefault();
					save_schedule(text.indexOf("Save Changes") >= 0);
					return;
				}
				if (text.indexOf("Continue to System Inventory") >= 0 && !btn.disabled) {
					event.preventDefault();
					navigate("it-tender-configuration-system-inventory", {
						configuration_id: ctx.configuration_id,
					});
				}
			},
			true,
		);
	}

	var SYSTEM_INVENTORY_CATEGORIES = [
		"SYSTEMS_IN_SCOPE",
		"INFRASTRUCTURE_ENVIRONMENT",
		"USER_LOCATION_SCOPE",
		"INTEGRATION_POINTS",
		"DATA_MIGRATION_SCOPE",
		"LICENSING_SUPPORT_CONTEXT",
		"SECURITY_ACCESS_CONTEXT",
		"OUT_OF_SCOPE_ITEMS",
	];
	var SYSTEM_INVENTORY_PRICE_LINKS = {
		REQUIRED: "Required",
		OPTIONAL: "Optional",
		PRICE_REQUIRED: "Required",
		PRICE_OPTIONAL: "Optional",
		NOT_PRICED: "Not Priced",
	};
	var system_inventory_cache = {};
	var system_inventory_active_category = "SYSTEMS_IN_SCOPE";
	var system_inventory_selected_item = "";
	var system_inventory_creating_item = false;

	function install_system_inventory_layout_styles(doc) {
		if (!doc || !doc.head || doc.getElementById("it-wizard-system-inventory-layout-styles")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "it-wizard-system-inventory-layout-styles";
		style.textContent =
			"html.it-wizard-system-inventory-root, body.it-wizard-system-inventory-layout { height: 100%; overflow: hidden; }" +
			"body.it-wizard-system-inventory-layout { display: flex; flex-direction: column; min-height: 0 !important; }" +
			"body.it-wizard-system-inventory-layout > header { position: relative !important; top: auto !important; flex: 0 0 auto; }" +
			"body.it-wizard-system-inventory-layout > [data-itw-inv-context] { margin-top: 0 !important; flex: 0 0 auto; }" +
			"body.it-wizard-system-inventory-layout > main { flex: 1 1 auto; min-height: 0; }" +
			"body.it-wizard-system-inventory-layout > footer { position: relative !important; bottom: auto !important; flex: 0 0 auto; }" +
			"[data-itw-inv-drawer][data-itw-inv-drawer-hidden='1'] { transform: translateX(100%); pointer-events: none; }" +
			"[data-itw-inv-drawer][data-itw-inv-drawer-open='1'] { transform: translateX(0); pointer-events: auto; }";
		doc.head.appendChild(style);
	}

	function harmonize_system_inventory_page_layout(doc) {
		if (!doc || !doc.body) {
			return;
		}
		install_system_inventory_layout_styles(doc);
		if (doc.documentElement) {
			doc.documentElement.classList.add("it-wizard-system-inventory-root", "h-full");
		}
		doc.body.classList.add("it-wizard-system-inventory-layout", "h-full", "overflow-hidden");
		doc.body.classList.remove("min-h-screen");
		doc.querySelectorAll("header.fixed, header.sticky").forEach(unfix_layout_chrome);
		var footer = doc.querySelector("[data-itw-inv-actions]");
		if (footer) {
			footer.classList.remove("fixed", "absolute", "bottom-0");
		}
	}

	function system_inventory_payload_data(payload) {
		return unwrap_envelope_data(payload || {});
	}

	function system_inventory_item_key(item) {
		return String(item.item_code || item.inventory_item_code || item.code || item.id || "");
	}

	function system_inventory_price_link(item) {
		var code = String(
			item.pricing_policy || item.price_schedule_link || item.price_link || "NOT_PRICED",
		).toUpperCase();
		return {
			code: SYSTEM_INVENTORY_PRICE_LINKS[code] ? code : "NOT_PRICED",
			label: SYSTEM_INVENTORY_PRICE_LINKS[code] || SYSTEM_INVENTORY_PRICE_LINKS.NOT_PRICED,
		};
	}

	function system_inventory_reference_label(reference) {
		reference = reference || {};
		var name = String(reference.name || "").trim();
		var code = String(reference.code || "").trim();
		return name && code ? name + " (" + code + ")" : name || code || "—";
	}

	function normalize_system_inventory_payload(data) {
		data = Object.assign({}, data || {});
		if (!Array.isArray(data.items)) {
			data.items = (data.categories || []).reduce(function (items, group) {
				return items.concat(group.items || []);
			}, []);
		}
		return data;
	}

	function hydrate_system_inventory_context(doc, data) {
		var values = [
			data.tender_number || data.configuration_id || "—",
			data.title || data.tender_title || "—",
			system_inventory_reference_label(data.planning_package),
			system_inventory_reference_label(data.procuring_entity),
			system_inventory_reference_label(data.method),
			data.state_label || data.state || "—",
		];
		var fields = doc.querySelectorAll("[data-itw-inv-context] > div");
		values.forEach(function (value, index) {
			var spans = fields[index] ? fields[index].querySelectorAll("span") : [];
			if (spans.length) {
				spans[spans.length - 1].textContent = value;
			}
		});
		var validation = data.validation || {};
		var validationSpans = fields[6] ? fields[6].querySelectorAll("span") : [];
		if (validationSpans.length >= 3) {
			validationSpans[1].innerHTML =
				'<span class="material-symbols-outlined text-sm">check_circle</span> ' +
				frappe.utils.escape_html(String(validation.blockers || 0) + " Blockers");
			validationSpans[2].innerHTML =
				'<span class="material-symbols-outlined text-sm">warning</span> ' +
				frappe.utils.escape_html(String(validation.warnings || 0) + " Warnings");
		}
	}

	function system_inventory_visible_items(data) {
		var queryNode = data.doc && data.doc.querySelector ? data.doc.querySelector("[data-itw-inv-search]") : null;
		var query = queryNode ? String(queryNode.value || "").trim().toLowerCase() : "";
		return (data.items || []).filter(function (item) {
			var category = String(item.category || "SYSTEMS_IN_SCOPE");
			if (category !== system_inventory_active_category) {
				return false;
			}
			if (!query) {
				return true;
			}
			return [
				item.title,
				item.item_code,
				(item.requirement_refs || []).join(" "),
				(item.schedule_refs || []).join(" "),
			]
				.join(" ")
				.toLowerCase()
				.indexOf(query) >= 0;
		});
	}

	function hydrate_system_inventory_table(doc, data) {
		var body = doc.querySelector("[data-itw-inv-table-body]");
		if (!body) {
			return;
		}
		data.doc = doc;
		var items = system_inventory_visible_items(data);
		body.innerHTML = items
			.map(function (item) {
				var key = system_inventory_item_key(item);
				var priceLink = system_inventory_price_link(item);
				var requirementLabel = (item.requirement_refs || []).join(", ") || __("Not linked");
				var phaseLabel = (item.schedule_refs || []).join(", ") || __("Not linked");
				return (
					'<tr class="hover:bg-surface-container-low transition-colors" data-itw-inv-row="1" data-itw-inv-code="' +
					frappe.utils.escape_html(key) +
					'"><td class="px-4 py-4"><p class="font-body-md font-semibold text-on-surface">' +
					frappe.utils.escape_html(item.title || __("Untitled inventory item")) +
					'</p><p class="text-xs text-on-surface-variant">' +
					frappe.utils.escape_html(requirementLabel) +
					"</p></td><td class=\"px-4 py-4\">" +
					frappe.utils.escape_html(item.category_label || item.category || "—") +
					'</td><td class="px-4 py-4">' +
					frappe.utils.escape_html(
						String(item.scope_status || "—").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, function (letter) {
							return letter.toUpperCase();
						}),
					) +
					'</td><td class="px-4 py-4"><p class="font-medium">' +
					frappe.utils.escape_html(item.required_action_label || item.required_action || "—") +
					'</p><p class="text-xs text-on-surface-variant">' +
					frappe.utils.escape_html(phaseLabel) +
					'</p></td><td class="px-4 py-4 max-w-xs">' +
					frappe.utils.escape_html(item.bidder_consideration || "—") +
					'</td><td class="px-4 py-4"><span class="font-semibold" data-itw-inv-price-link-code="' +
					priceLink.code +
					'">' +
					frappe.utils.escape_html(priceLink.label) +
					'</span></td><td class="px-4 py-4">' +
					frappe.utils.escape_html(
						String(item.review_status || "—").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, function (letter) {
							return letter.toUpperCase();
						}),
					) +
					'</td><td class="px-4 py-4 text-right"><button class="p-2 text-on-surface-variant hover:text-primary" data-itw-inv-action="edit" type="button"><span class="material-symbols-outlined">edit</span></button></td></tr>'
				);
			})
			.join("");
		if (!items.length) {
			body.innerHTML =
				'<tr><td class="px-4 py-8 text-center text-on-surface-variant" colspan="8">' +
				__("No inventory items in this category.") +
				"</td></tr>";
		}
	}

	function hydrate_system_inventory_categories(doc) {
		doc.querySelectorAll("[data-itw-inv-category]").forEach(function (button) {
			var active = button.getAttribute("data-itw-inv-category") === system_inventory_active_category;
			button.classList.toggle("bg-primary", active);
			button.classList.toggle("text-white", active);
			button.classList.toggle("text-on-surface-variant", !active);
			button.setAttribute("aria-pressed", active ? "true" : "false");
		});
	}

	function hydrate_system_inventory_guidance(doc, data) {
		var guidance = doc.querySelector("[data-itw-inv-guidance]");
		if (!guidance) {
			return;
		}
		var completion = data.completion || {};
		var gaps = completion.gaps || {};
		var count = (data.items || []).length;
		var complete = completion.completed == null ? 0 : completion.completed;
		var completionNode =
			guidance.querySelector("[data-itw-inv-completion-label]") ||
			guidance.querySelector(".font-data-mono");
		if (completionNode) {
			completionNode.textContent = complete + "/" + count + " Items";
		}
		var bar =
			guidance.querySelector("[data-itw-inv-completion-bar]") ||
			guidance.querySelector(".bg-primary.h-full");
		if (bar) {
			bar.style.width = (count ? Math.round((complete / count) * 100) : 0) + "%";
		}
		var migrationGaps = (data.items || []).filter(function (item) {
			return item.category === "DATA_MIGRATION_SCOPE" && item.review_status !== "APPROVED";
		}).length;
		var integrationGaps = (data.items || []).filter(function (item) {
			return item.category === "INTEGRATION_POINTS" && item.review_status !== "APPROVED";
		}).length;
		var gapMap = {
			needs_review: (gaps.needs_review || 0) + " Pending",
			migration: migrationGaps + " Identified",
			integration: integrationGaps + " Required",
			sensitive: (gaps.sensitive_disclosure_pending || 0) + " Warning",
		};
		Object.keys(gapMap).forEach(function (key) {
			var node = guidance.querySelector('[data-itw-inv-gap="' + key + '"]');
			if (node) {
				node.textContent = gapMap[key];
			}
		});
	}

	function hydrate_system_inventory_summaries(doc, data) {
		var locationItems = (data.items || []).filter(function (item) {
			return item.category === "USER_LOCATION_SCOPE";
		});
		var cardsHost = doc.querySelector("[data-itw-inv-summary-cards]");
		if (cardsHost) {
			if (!locationItems.length) {
				cardsHost.innerHTML =
					'<div class="p-3 bg-surface-container rounded-lg border border-border-subtle" data-itw-inv-summary-card="1">' +
					'<p class="font-label-caps text-[10px] text-on-surface-variant mb-1">' +
					__("User & Location Scope") +
					"</p>" +
					'<p class="font-body-md font-bold" data-itw-inv-summary-value="1">' +
					__("Not configured") +
					"</p>" +
					'<p class="text-[10px] text-on-surface-variant mt-2" data-itw-inv-source="1">' +
					__("Source: Not configured") +
					"</p>" +
					'<button class="mt-2 text-[10px] font-bold uppercase tracking-widest text-primary" data-itw-inv-edit-source="USER_LOCATION_SCOPE" type="button">' +
					__("Edit") +
					"</button></div>";
			} else {
				// Honest inventory cards: title + bidder context fields only (no fake KPI metrics).
				cardsHost.innerHTML = locationItems
					.map(function (item) {
						var code = system_inventory_item_key(item);
						var contextBits = [];
						if (item.description) {
							contextBits.push(item.description);
						}
						if (item.bidder_consideration) {
							contextBits.push(item.bidder_consideration);
						}
						var contextText = contextBits.join(" — ") || __("Not configured");
						return (
							'<div class="p-3 bg-surface-container rounded-lg border border-border-subtle" data-itw-inv-summary-card="1" data-itw-inv-code="' +
							frappe.utils.escape_html(code) +
							'">' +
							'<p class="font-label-caps text-[10px] text-on-surface-variant mb-1">' +
							frappe.utils.escape_html(item.title || code) +
							"</p>" +
							'<p class="font-body-md font-bold" data-itw-inv-summary-value="1">' +
							frappe.utils.escape_html(contextText) +
							"</p>" +
							'<p class="text-[10px] text-on-surface-variant mt-2" data-itw-inv-source="1">' +
							__("Source: User & Location Scope inventory item") +
							" (" +
							frappe.utils.escape_html(code) +
							")</p>" +
							'<button class="mt-2 text-[10px] font-bold uppercase tracking-widest text-primary" data-itw-inv-edit-source="USER_LOCATION_SCOPE" data-itw-inv-code="' +
							frappe.utils.escape_html(code) +
							'" type="button">' +
							__("Edit") +
							"</button></div>"
						);
					})
					.join("");
			}
		}
		var securityItems = (data.items || []).filter(function (item) {
			return item.category === "SECURITY_ACCESS_CONTEXT";
		});
		var securityHost = doc.querySelector("[data-itw-inv-security-host]");
		if (securityHost) {
			var security = securityItems[0];
			var titleNode = securityHost.querySelector('[data-itw-inv-security-value="title"]');
			var classification = securityHost.querySelector('[data-itw-inv-security-value="classification"]');
			var requiredAction = securityHost.querySelector('[data-itw-inv-security-value="required_action"]');
			var bidderConsideration = securityHost.querySelector(
				'[data-itw-inv-security-value="bidder_consideration"]',
			);
			var source = securityHost.querySelector("[data-itw-inv-source]");
			var editBtn = securityHost.querySelector("[data-itw-inv-edit-source]");
			if (!security) {
				if (titleNode) {
					titleNode.textContent = __("Not configured");
				}
				if (classification) {
					classification.textContent = __("Not configured");
				}
				if (requiredAction) {
					requiredAction.textContent = __("Not configured");
				}
				if (bidderConsideration) {
					bidderConsideration.textContent = __("Not configured");
				}
				if (source) {
					source.textContent = __("Source: Not configured");
				}
				if (editBtn) {
					editBtn.removeAttribute("data-itw-inv-code");
				}
			} else {
				var secCode = system_inventory_item_key(security);
				if (titleNode) {
					titleNode.textContent = security.title || secCode || __("Not configured");
				}
				if (classification) {
					classification.textContent = security.confidentiality_level || __("Not configured");
				}
				if (requiredAction) {
					requiredAction.textContent = security.required_action || __("Not configured");
				}
				if (bidderConsideration) {
					bidderConsideration.textContent =
						security.bidder_consideration || security.description || __("Not configured");
				}
				if (source) {
					source.textContent =
						__("Source: Security & Access Context inventory item") + " (" + secCode + ")";
				}
				if (editBtn) {
					editBtn.setAttribute("data-itw-inv-code", secCode);
				}
			}
		}
	}

	function set_system_inventory_field(doc, key, value) {
		var field = doc.querySelector('[data-itw-inv-field="' + key + '"]');
		if (!field) {
			return;
		}
		if (field.tagName === "SELECT") {
			var stringValue = value == null ? "" : String(value);
			if (stringValue && !Array.from(field.options).some(function (option) { return option.value === stringValue; })) {
				field.add(new Option(stringValue, stringValue));
			}
			field.value = stringValue;
			return;
		}
		field.value = value == null ? "" : String(value);
	}

	function hydrate_system_inventory_reference_options(doc, data) {
		[
			{ field: "requirement_ref", options: data.requirement_options || [] },
			{ field: "schedule_ref", options: data.schedule_options || [] },
		].forEach(function (config) {
			var select = doc.querySelector('[data-itw-inv-field="' + config.field + '"]');
			if (!select) {
				return;
			}
			var current = select.value;
			select.innerHTML = '<option value="">' + __("Not linked") + "</option>";
			config.options.forEach(function (reference) {
				var option = doc.createElement("option");
				option.value = String(reference.code || "");
				option.textContent = system_inventory_reference_label(reference);
				select.appendChild(option);
			});
			select.value = current;
		});
	}

	function hydrate_system_inventory_drawer(doc, item) {
		item = item || {};
		[
			"title",
			"category",
			"scope_status",
			"required_action",
			"data_volume",
			"integration_requirement",
			"confidentiality_level",
			"bidder_consideration",
		].forEach(function (key) {
			set_system_inventory_field(doc, key, item[key]);
		});
		set_system_inventory_field(doc, "requirement_ref", (item.requirement_refs || [])[0] || "");
		set_system_inventory_field(doc, "schedule_ref", (item.schedule_refs || [])[0] || "");
		set_system_inventory_field(doc, "contract_carry_forward", item.contract_carry_forward ? "1" : "0");
		var priceLink = system_inventory_price_link(item);
		var priceNode = doc.querySelector("[data-itw-inv-price-link]");
		if (priceNode) {
			priceNode.textContent = priceLink.label;
			priceNode.setAttribute("data-itw-inv-price-link-code", priceLink.code);
			priceNode.setAttribute("aria-readonly", "true");
		}
	}

	function open_system_inventory_drawer(doc) {
		var drawer = doc.querySelector("[data-itw-inv-drawer]");
		if (!drawer) {
			return;
		}
		drawer.removeAttribute("data-itw-inv-drawer-hidden");
		drawer.setAttribute("data-itw-inv-drawer-open", "1");
		drawer.setAttribute("aria-hidden", "false");
	}

	function close_system_inventory_drawer(doc) {
		var drawer = doc.querySelector("[data-itw-inv-drawer]");
		if (!drawer) {
			return;
		}
		drawer.removeAttribute("data-itw-inv-drawer-open");
		drawer.setAttribute("data-itw-inv-drawer-hidden", "1");
		drawer.setAttribute("aria-hidden", "true");
	}

	function collect_system_inventory_item(doc) {
		var current = (system_inventory_cache.items || []).find(function (item) {
			return system_inventory_item_key(item) === system_inventory_selected_item;
		}) || {};
		var next = Object.assign({}, current);
		doc.querySelectorAll("[data-itw-inv-field]").forEach(function (field) {
			var key = field.getAttribute("data-itw-inv-field");
			if (key === "requirement_ref") {
				var currentRequirements = next.requirement_refs || [];
				if (field.value !== (currentRequirements[0] || "")) {
					next.requirement_refs = field.value ? [field.value] : [];
				}
			} else if (key === "schedule_ref") {
				var currentSchedule = next.schedule_refs || [];
				if (field.value !== (currentSchedule[0] || "")) {
					next.schedule_refs = field.value ? [field.value] : [];
				}
			} else if (key === "contract_carry_forward") {
				next.contract_carry_forward = field.value === "1" ? 1 : 0;
			} else {
				next[key] = field.value;
			}
		});
		if (!next.description) {
			next.description = next.bidder_consideration || next.title || "";
		}
		next.pricing_policy = next.pricing_policy || "NOT_PRICED";
		next.review_status = next.review_status || "DRAFT";
		return next;
	}

	function apply_system_inventory_payload(doc, data) {
		data = normalize_system_inventory_payload(data);
		system_inventory_cache = data;
		hydrate_system_inventory_context(doc, data);
		hydrate_system_inventory_categories(doc);
		hydrate_system_inventory_reference_options(doc, data);
		hydrate_system_inventory_table(doc, data);
		hydrate_system_inventory_summaries(doc, data);
		hydrate_system_inventory_guidance(doc, data);
		var continueButton = doc.querySelector("[data-itw-inv-continue]");
		if (continueButton) {
			continueButton.disabled = false;
			continueButton.removeAttribute("aria-disabled");
			continueButton.classList.remove("opacity-55", "cursor-not-allowed");
			continueButton.style.opacity = "";
			continueButton.style.pointerEvents = "";
		}
	}

	function wire_system_inventory_interactions(doc, ctx) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-inv-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-inv-wired", "1");
		var searchTimer = null;
		doc.addEventListener("input", function (event) {
			if (!event.target.matches("[data-itw-inv-search]")) {
				return;
			}
			clearTimeout(searchTimer);
			searchTimer = setTimeout(function () {
				apply_system_inventory_payload(doc, system_inventory_cache);
			}, 200);
		});
		doc.addEventListener("click", function (event) {
			var categoryButton = event.target.closest("[data-itw-inv-category]");
			if (categoryButton) {
				system_inventory_active_category = categoryButton.getAttribute("data-itw-inv-category");
				apply_system_inventory_payload(doc, system_inventory_cache);
				return;
			}
			var sourceEdit = event.target.closest("[data-itw-inv-edit-source]");
			if (sourceEdit) {
				var sourceCategory = sourceEdit.getAttribute("data-itw-inv-edit-source");
				var sourceCode = sourceEdit.getAttribute("data-itw-inv-code") || "";
				if (sourceCategory) {
					system_inventory_active_category = sourceCategory;
					apply_system_inventory_payload(doc, system_inventory_cache);
				}
				if (sourceCode) {
					system_inventory_selected_item = sourceCode;
					system_inventory_creating_item = false;
					var sourceItem = (system_inventory_cache.items || []).find(function (candidate) {
						return system_inventory_item_key(candidate) === sourceCode;
					});
					hydrate_system_inventory_drawer(doc, sourceItem || {});
					open_system_inventory_drawer(doc);
				} else {
					// Not configured → open create drawer on owning category.
					system_inventory_selected_item = "";
					system_inventory_creating_item = true;
					hydrate_system_inventory_drawer(doc, {
						category: sourceCategory || system_inventory_active_category,
						scope_status: "IN_SCOPE",
						required_action: "DISCLOSE",
						integration_requirement: "NONE",
						confidentiality_level: "INTERNAL",
						contract_carry_forward: 0,
						pricing_policy: "NOT_PRICED",
					});
					open_system_inventory_drawer(doc);
				}
				return;
			}
			var editButton = event.target.closest("[data-itw-inv-action='edit']");
			if (editButton) {
				system_inventory_creating_item = false;
				var row = editButton.closest("[data-itw-inv-row]");
				system_inventory_selected_item = row ? row.getAttribute("data-itw-inv-code") : "";
				var item = (system_inventory_cache.items || []).find(function (candidate) {
					return system_inventory_item_key(candidate) === system_inventory_selected_item;
				});
				hydrate_system_inventory_drawer(doc, item || {});
				open_system_inventory_drawer(doc);
				return;
			}
			if (event.target.closest("[data-itw-inv-add]")) {
				system_inventory_selected_item = "";
				system_inventory_creating_item = true;
				hydrate_system_inventory_drawer(doc, {
					category: system_inventory_active_category,
					scope_status: "IN_SCOPE",
					required_action: "DISCLOSE",
					integration_requirement: "NONE",
					confidentiality_level: "INTERNAL",
					contract_carry_forward: 0,
					pricing_policy: "NOT_PRICED",
				});
				open_system_inventory_drawer(doc);
				return;
			}
			if (event.target.closest("[data-itw-inv-drawer-close], [data-itw-inv-drawer-cancel]")) {
				close_system_inventory_drawer(doc);
				return;
			}
			if (event.target.closest("[data-itw-inv-update], [data-itw-inv-save]")) {
				var itemPayload =
					system_inventory_selected_item || system_inventory_creating_item
						? collect_system_inventory_item(doc)
						: null;
				call_api("save_system_inventory_api", {
					configuration_id: ctx.configuration_id,
					inventory_json: JSON.stringify(
						itemPayload
							? {
								selected_item_id: system_inventory_selected_item || undefined,
								selected_item: itemPayload,
							}
							: { items: system_inventory_cache.items || [] },
					),
				}).then(function (result) {
					var data = system_inventory_payload_data((result && result.message) || {});
					apply_system_inventory_payload(doc, data);
					system_inventory_creating_item = false;
					close_system_inventory_drawer(doc);
					frappe.show_alert({ message: __("Inventory saved"), indicator: "green" });
				});
				return;
			}
			if (event.target.closest("[data-itw-inv-continue]")) {
				event.preventDefault();
				navigate("it-tender-configuration-price-schedule", {
					configuration_id: ctx.configuration_id,
				});
			}
		});
	}

	function fetch_system_inventory_data(ctx) {
		return call_api("get_system_inventory_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return { system_inventory: (result && result.message) || {} };
		});
	}

	function fetch_implementation_schedule_data(ctx) {
		return call_api("get_implementation_schedule_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				implementation_schedule: (result && result.message) || {},
			};
		});
	}

	function fetch_overview_data(ctx) {
		if (kentender.it_wizard.overview && kentender.it_wizard.overview.fetch) {
			return kentender.it_wizard.overview.fetch(ctx);
		}
		return Promise.resolve({ overview: {} });
	}

	function fetch_screen_data(screen, ctx, filters) {
		if (screen === "std_config_overview") {
			return fetch_overview_data(ctx);
		}
		if (screen === "tender_profile") {
			return fetch_tender_profile_data(ctx);
		}
		if (screen === "tds") {
			return fetch_tds_data(ctx);
		}
		if (screen === "it_requirements") {
			return fetch_it_requirements_data(ctx);
		}
		if (screen === "implementation_schedule") {
			return fetch_implementation_schedule_data(ctx);
		}
		if (screen === "system_inventory") {
			return fetch_system_inventory_data(ctx);
		}
		if (DOWNSTREAM_FETCHERS[screen]) {
			return DOWNSTREAM_FETCHERS[screen](ctx);
		}
		return Promise.resolve({});
	}

	var HYDRATORS = {
		std_config_overview: function (doc, payload, ctx) {
			if (kentender.it_wizard.overview && kentender.it_wizard.overview.hydrate) {
				kentender.it_wizard.overview.hydrate(doc, payload, ctx);
			}
		},
		tender_profile: function (doc, payload, ctx) {
			apply_profile_payload(doc, profile_payload_data(payload.profile || {}));
			disable_profile_stub_actions(doc);
			wire_profile_interactions(doc, ctx);
		},
		tds: function (doc, payload, ctx) {
			apply_tds_payload(doc, tds_payload_data(payload.tds || {}));
			disable_tds_stub_actions(doc);
			wire_tds_interactions(doc, ctx);
		},
		it_requirements: function (doc, payload, ctx) {
			apply_it_requirements_payload(doc, requirements_payload_data(payload.it_requirements || {}));
			disable_it_requirements_stub_actions(doc);
			wire_it_requirements_interactions(doc, ctx);
		},
		implementation_schedule: function (doc, payload, ctx) {
			apply_it_schedule_payload(doc, schedule_payload_data(payload.implementation_schedule || {}));
			disable_it_schedule_stub_actions(doc);
			wire_it_schedule_interactions(doc, ctx);
		},
		system_inventory: function (doc, payload, ctx) {
			apply_system_inventory_payload(
				doc,
				system_inventory_payload_data(payload.system_inventory || {}),
			);
			wire_system_inventory_interactions(doc, ctx);
		},
	};

	function register_downstream(api) {
		api = api || {};
		(api.routes || []).forEach(function (route) {
			if (ITW_REGISTERED_ROUTES.indexOf(route) === -1) {
				ITW_REGISTERED_ROUTES.push(route);
			}
		});
		Object.keys(api.step_route_map || {}).forEach(function (key) {
			STEP_ROUTE_MAP[key] = api.step_route_map[key];
		});
		(api.context_routes || []).forEach(function (route) {
			CONFIGURATION_CONTEXT_ROUTES[route] = 1;
		});
		Object.keys(api.fetchers || {}).forEach(function (screen) {
			DOWNSTREAM_FETCHERS[screen] = api.fetchers[screen];
		});
		Object.keys(api.hydrators || {}).forEach(function (screen) {
			HYDRATORS[screen] = api.hydrators[screen];
		});
	}







	function hydrate_iframe(screen, iframe, ctx, page_title) {
		if (!iframe) {
			return;
		}
		var doc = live_iframe_document(iframe);
		if (!doc || !doc.body) {
			return;
		}
		var hydrationToken = next_hydration_token(iframe);
		install_hydration_gate(doc);
		if (
			(screen === "std_config_overview" ||
				screen === "tender_profile" ||
				screen === "tds" ||
				screen === "it_requirements" ||
				screen === "implementation_schedule" ||
				screen === "system_inventory" ||
				screen === "price_schedule" ||
				screen === "evaluation_setup" ||
				screen === "forms_and_evidence" ||
				screen === "scc" ||
				screen === "validation_report" ||
				screen === "review_and_approval" ||
				screen === "render_preview" ||
				screen === "publication_readiness") &&
			!(ctx.configuration_id || "").trim()
		) {
			mark_hydration_error(doc);
			if (!configRedirectInFlight) {
				configRedirectInFlight = true;
				frappe.show_alert({
					message: __("Open a tender configuration from the dashboard to view this screen."),
					indicator: "orange",
				});
			}
			navigate("it-tender-configuration-dashboard");
			return;
		}
		normalize_page_layout(doc, screen);
		var filters = { page: 1, page_size: 25 };
		fetch_screen_data(screen, ctx, filters)
			.then(function (payload) {
				if (!hydration_token_active(iframe, hydrationToken)) {
					return;
				}
				doc = live_iframe_document(iframe);
				if (!doc || !doc.body) {
					return;
				}
				if (HYDRATORS[screen]) {
					HYDRATORS[screen](doc, payload, ctx, filters);
				}
				mark_hydrated(doc);
			})
			.catch(function (err) {
				if (!hydration_token_active(iframe, hydrationToken)) {
					return;
				}
				doc = live_iframe_document(iframe);
				if (!doc || !doc.body) {
					return;
				}
				mark_hydration_error(doc);
				frappe.show_alert({
					indicator: "red",
					message:
						(err && err.message) ||
						(screen === "std_config_overview"
							? __("Unable to load configuration overview.")
							: screen === "tender_profile"
								? __("Unable to load tender profile.")
								: screen === "tds"
									? __("Unable to load tender data sheet.")
									: screen === "it_requirements"
										? __("Unable to load IT requirements.")
										: screen === "implementation_schedule"
											? __("Unable to load implementation schedule.")
											: screen === "system_inventory"
												? __("Unable to load system inventory.")
												: __("Unable to load dashboard data.")),
				});
			});
	}

	function mount_page(wrapper, config) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: config.title,
			single_column: true,
		});
		preserve_procurement_sidebar();
		document.body.classList.add(config.shell_class);

		var root = page.main.get(0);
		if (!root) {
			return;
		}
		root.className = config.root_class;
		root.setAttribute("data-testid", config.testid + "-root");
		root.style.width = "100%";
		root.style.height = "calc(100vh - var(--navbar-height, 48px))";
		root.style.minHeight = "calc(100vh - var(--navbar-height, 48px))";
		root.innerHTML =
			'<section class="' +
			config.shell_class +
			'" data-testid="' +
			config.testid +
			'-shell">' +
			'<iframe class="' +
			config.iframe_class +
			'" data-testid="' +
			config.testid +
			'-iframe" src="' +
			config.asset +
			'" title="' +
			frappe.utils.escape_html(config.title) +
			'"></iframe></section>';

		var shell = root.querySelector("section");
		if (shell) {
			shell.style.width = "100%";
			shell.style.height = "100%";
			shell.style.minHeight = "100%";
		}
		var iframe = root.querySelector("iframe");
		iframe.style.width = "100%";
		iframe.style.height = "100%";
		iframe.style.border = "0";
		iframe.style.display = "block";
		var hydrationRunId = 0;
		function run_hydration(source) {
			hydrationRunId += 1;
			var runId = hydrationRunId;
			setTimeout(function () {
				if (runId !== hydrationRunId) {
					return;
				}
				// Dedupe redundant triggers (readystate-complete + load event fire
				// for the same document): if THIS document is already hydrated, a
				// second fetch is wasted work and its response can spuriously
				// downgrade a good render to an error state.
				var current = null;
				try { current = live_iframe_document(iframe); } catch (e) { current = null; }
				if (
					current &&
					current.body &&
					current.body.getAttribute("data-it-wizard-hydrated") === "1"
				) {
					return;
				}
				var fresh_ctx = read_route_context();
				hydrate_iframe(config.screen, iframe, fresh_ctx, config.title);
			}, 0);
		}
		prepare_iframe_frame(iframe);
		iframe.addEventListener("load", function () { run_hydration("load-event"); });
		try {
			if (iframe.contentDocument && iframe.contentDocument.readyState === "complete") {
				run_hydration("readystate-complete");
			}
		} catch (err) {
			// load event will hydrate when ready
		}

		frappe.pages[config.page].on_page_show = function () {
			document.body.classList.add(config.shell_class);
			preserve_procurement_sidebar();
			if (CONFIGURATION_CONTEXT_ROUTES[config.page]) {
				var ctx = read_route_context();
				if (ctx.configuration_id) {
					sync_configuration_id_to_url(ctx.configuration_id);
				}
			}
			run_hydration("on_page_show");
		};
		frappe.pages[config.page].on_page_hide = function () {
			document.body.classList.remove(config.shell_class);
		};
	}

	kentender.it_wizard.mount_page = mount_page;
	kentender.it_wizard.navigate = navigate;
	kentender.it_wizard.register_downstream = register_downstream;
	kentender.it_wizard.hydrate_iframe = hydrate_iframe;
	kentender.it_wizard.read_route_context = read_route_context;
	kentender.it_wizard.set_route_context = set_route_context;
	kentender.it_wizard.harmonize_tender_profile_page_layout = harmonize_tender_profile_page_layout;
	kentender.it_wizard.hydrate_profile_context = hydrate_profile_context;
	kentender.it_wizard.hydrate_profile_form = hydrate_profile_form;
	kentender.it_wizard.hydrate_profile_sidebar = hydrate_profile_sidebar;
	kentender.it_wizard.unwrap_envelope_data = unwrap_envelope_data;
	kentender.it_wizard.harmonize_tds_page_layout = harmonize_tds_page_layout;
	kentender.it_wizard.hydrate_tds_context = hydrate_tds_context;
	kentender.it_wizard.hydrate_tds_form = hydrate_tds_form;
	kentender.it_wizard.hydrate_tds_sidebar = hydrate_tds_sidebar;
	kentender.it_wizard.strip_tds_fixture_scripts = strip_tds_fixture_scripts;
	kentender.it_wizard.HYDRATORS = HYDRATORS;
	kentender.it_wizard.preserve_procurement_sidebar = preserve_procurement_sidebar;
})();
