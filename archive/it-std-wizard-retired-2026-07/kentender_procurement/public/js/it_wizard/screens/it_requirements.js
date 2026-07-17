/* ── IT Requirements — Screen 03 (native screen module) ───────────────────── */
(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.screens.it_requirements");

	var api = kentender.it_wizard.api;
	var routes = kentender.it_wizard.routes;
	var components = kentender.it_wizard.components;
	var shell = kentender.it_wizard.shell;

	var SCREEN_SHELL = "it-wizard-it-requirements-shell";
	var IMPL_SCHEDULE_ROUTE = "it-tender-configuration-implementation-schedule";

	var TREATMENT_REVERSE = {
		Mandatory: "MANDATORY",
		"Evaluation-linked": "SCORED",
		Informational: "INFORMATIONAL",
	};

	var RESPONSE_REVERSE = {
		"Yes/No confirmation": "YES_NO",
		"Narrative response": "NARRATIVE",
		"Compliance statement": "COMPLIANCE_MATRIX",
		"Completed table": "NUMERIC",
		"Uploaded document": "DOCUMENT_EVIDENCE",
		"Not required": "NOT_REQUIRED",
	};

	var EVIDENCE_REVERSE = {
		"Evidence required": "REQUIRED",
		"Evidence optional": "OPTIONAL",
		"No evidence required": "NOT_REQUIRED",
	};

	var _state = {
		wrapper: null,
		configurationId: "",
		payload: null,
		itemsByCode: {},
		selectedCode: "",
		filterText: "",
		loading: false,
	};

	function _q(sel) {
		return _state.wrapper ? _state.wrapper.querySelector(sel) : null;
	}

	function _payloadData(result) {
		var msg = (result && result.message) || {};
		return msg.data || msg;
	}

	function _contextFields(data) {
		data = data || {};
		var blockers = data.blocker_count != null ? data.blocker_count : (data.validation || {}).blockers || 0;
		var warnings = data.warning_count != null ? data.warning_count : (data.validation || {}).warnings || 0;
		var entity = data.procuring_entity || {};
		var method = data.method || {};
		return [
			{ label: "TENDER REF", value: data.tender_ref || data.configuration_id, mono: true },
			{ label: "TENDER TITLE", value: data.tender_title || data.title },
			{
				label: "PLANNING PKG REF",
				value: data.planning_package_ref || (data.planning_package || {}).code,
				mono: true,
			},
			{ label: "PROCURING ENTITY", value: data.procuring_entity_name || entity.name },
			{ label: "PROCUREMENT METHOD", value: data.procurement_method_label || method.label || method.name },
			{ label: "WIZARD STATE", value: data.wizard_state_label || data.state_label },
			{ label: "ISSUES", value: blockers + " Blockers / " + warnings + " Warnings" },
		];
	}

	function _indexItems(payload) {
		var map = {};
		(payload.sections || []).forEach(function (section) {
			(section.items || []).forEach(function (row) {
				if (row.requirement_code) {
					map[row.requirement_code] = row;
				}
			});
		});
		(payload.requirements || []).forEach(function (row) {
			var code = row.requirement_code || row.display_id;
			if (code) {
				map[code] = Object.assign({}, map[code] || {}, row);
			}
		});
		_state.itemsByCode = map;
	}

	function _filteredRows() {
		var rows = [];
		Object.keys(_state.itemsByCode)
			.sort()
			.forEach(function (code) {
				rows.push(_state.itemsByCode[code]);
			});
		if (!rows.length && _state.payload && _state.payload.requirements) {
			rows = _state.payload.requirements.slice();
		}
		var needle = (_state.filterText || "").trim().toLowerCase();
		if (!needle) {
			return rows;
		}
		return rows.filter(function (row) {
			var hay = [
				row.display_id,
				row.requirement_code,
				row.title,
				row.description,
				row.category,
			]
				.join(" ")
				.toLowerCase();
			return hay.indexOf(needle) >= 0;
		});
	}

	function _shellHtml() {
		var user = (frappe.session && (frappe.session.user_fullname || frappe.session.user)) || "User";
		return (
			'<div class="kt-itw-root kt-itw-root--requirements" data-testid="it-wizard-it-requirements" data-itw-native-loaded="0">' +
			components.appbar({ user: user, title: "IT Requirements" }) +
			'<main class="kt-itw-canvas kt-itw-canvas--requirements">' +
			components.page_header({
				title: "IT Requirements",
				subtitle: "Define what bidders must supply, deliver, integrate, support, or prove.",
				actions: [
					{ label: "Import Requirements Template", variant: "outline", stub: true },
					{ label: "Run Check", variant: "outline", stub: true },
					{ label: "Add Requirement", variant: "primary", stub: true },
				],
			}) +
			'<div data-itw-req-loading="1" class="kt-itw-loading">' +
			components.escape_html(__("Loading IT requirements…")) +
			"</div>" +
			'<div data-itw-req-content="1" hidden>' +
			components.context_strip([]).replace('data-itw-home-context="1"', 'data-itw-req-context="1"') +
			'<div class="kt-itw-req-layout" data-itw-req-main="1">' +
			'<div class="kt-itw-req-main" data-itw-req-composer="1">' +
			components.requirements_toolbar() +
			components.requirements_table([]) +
			"</div>" +
			components.requirements_guidance({}, {}) +
			"</div>" +
			components.requirements_action_bar({ continue_disabled: false }) +
			"</div></main>" +
			components.requirements_drawer_shell() +
			"</div>"
		);
	}

	function _openDrawer(code) {
		var item = _state.itemsByCode[code];
		if (!item) {
			return;
		}
		_state.selectedCode = code;
		var body = _q("[data-itw-req-drawer-body]");
		var title = _q("[data-itw-req-drawer-title]");
		if (title) {
			title.textContent = (item.display_id || item.requirement_code || "") + " | " + (item.title || "");
		}
		if (body) {
			body.innerHTML = components.requirements_drawer_fields(item);
		}
		var drawer = _q("[data-itw-req-drawer]");
		var backdrop = _q("[data-itw-req-drawer-backdrop]");
		if (drawer) {
			drawer.setAttribute("data-itw-req-drawer-hidden", "0");
			drawer.setAttribute("data-itw-req-drawer-open", "1");
		}
		if (backdrop) {
			backdrop.hidden = false;
		}
	}

	function _closeDrawer() {
		var drawer = _q("[data-itw-req-drawer]");
		var backdrop = _q("[data-itw-req-drawer-backdrop]");
		if (drawer) {
			drawer.setAttribute("data-itw-req-drawer-hidden", "1");
			drawer.removeAttribute("data-itw-req-drawer-open");
		}
		if (backdrop) {
			backdrop.hidden = true;
		}
		_state.selectedCode = "";
	}

	function _fieldValue(key) {
		var node = _q('[data-itw-field="' + key + '"]');
		if (!node) {
			return "";
		}
		if (node.tagName === "TEXTAREA" || node.tagName === "SELECT" || node.tagName === "INPUT") {
			return (node.value || "").trim();
		}
		return (node.textContent || "").trim();
	}

	function _collectDrawerPayload() {
		var base = _state.itemsByCode[_state.selectedCode] || {};
		var treatment = _fieldValue("treatment");
		var evidence = _fieldValue("evidence_level");
		var responseLabel = _fieldValue("response_format");
		return Object.assign({}, base, {
			requirement_code: _state.selectedCode,
			title: _fieldValue("title"),
			description: _fieldValue("description"),
			category: _fieldValue("category"),
			treatment: treatment,
			treatment_label: treatment,
			priority: TREATMENT_REVERSE[treatment] || base.priority || "MANDATORY",
			response_format: RESPONSE_REVERSE[responseLabel] || base.response_format || "YES_NO",
			response_format_label: responseLabel,
			bidder_response_format: responseLabel,
			bidder_instruction: _fieldValue("bidder_instruction"),
			evidence_level_label: evidence,
			evidence_level: EVIDENCE_REVERSE[evidence] || base.evidence_level || "REQUIRED",
			evidence_required: EVIDENCE_REVERSE[evidence] === "NOT_REQUIRED" ? 0 : 1,
			evidence_instruction: _fieldValue("evidence_instruction"),
			acceptance_criteria: _fieldValue("acceptance_criteria"),
			acceptance_expectation: _fieldValue("acceptance_expectation"),
			requirement_type: base.requirement_type || "FUNCTIONAL",
			section_key: base.section_key || "",
			evaluation_binding: base.evaluation_binding || "",
			contract_carry_forward: base.contract_carry_forward || 0,
			supplier_response_required: base.supplier_response_required != null ? base.supplier_response_required : 1,
		});
	}

	function _paint(payload) {
		payload = payload || {};
		_state.payload = payload;
		_indexItems(payload);

		var contextHost = _q("[data-itw-req-context]");
		if (contextHost) {
			contextHost.outerHTML = components
				.context_strip(_contextFields(payload))
				.replace('data-itw-home-context="1"', 'data-itw-req-context="1"');
		}

		var tableHost = _q("[data-itw-req-table-host]");
		if (tableHost) {
			tableHost.outerHTML = components.requirements_table(_filteredRows());
		}

		var guidanceHost = _q("[data-itw-req-guidance]");
		if (guidanceHost) {
			guidanceHost.outerHTML = components.requirements_guidance(
				payload.requirements_summary || {},
				payload.completion || {},
			);
		}

		var actionsHost = _q("[data-itw-req-actions]");
		if (actionsHost) {
			var validation = payload.validation || {};
			var blockers = validation.blockers != null ? validation.blockers : payload.blocker_count || 0;
			actionsHost.outerHTML = components.requirements_action_bar({
				continue_disabled: blockers > 0,
			});
		}

		var root = _q('[data-testid="it-wizard-it-requirements"]');
		if (root) {
			root.setAttribute("data-itw-native-loaded", "1");
		}

		if (_state.selectedCode && _state.itemsByCode[_state.selectedCode]) {
			_openDrawer(_state.selectedCode);
		}
	}

	function _fetch() {
		_state.loading = true;
		var loading = _q("[data-itw-req-loading]");
		var content = _q("[data-itw-req-content]");
		if (loading) {
			loading.hidden = false;
		}
		if (content) {
			content.hidden = true;
		}
		return api
			.call("get_it_requirements_api", { configuration_id: _state.configurationId })
			.then(function (result) {
				var data = _payloadData(result);
				_paint(data);
				if (loading) {
					loading.hidden = true;
				}
				if (content) {
					content.hidden = false;
				}
				_state.loading = false;
			})
			.catch(function (err) {
				_state.loading = false;
				frappe.show_alert({
					indicator: "red",
					message: (err && err.message) || __("Unable to load IT requirements."),
				});
			});
	}

	function _saveSelected() {
		if (!_state.selectedCode) {
			return Promise.resolve();
		}
		var selected = _collectDrawerPayload();
		return api
			.call("save_it_requirements_api", {
				configuration_id: _state.configurationId,
				requirements_json: JSON.stringify({
					selected_item_id: _state.selectedCode,
					selected_item: selected,
				}),
			})
			.then(function (result) {
				frappe.show_alert({ message: __("Requirements saved"), indicator: "green" });
				_paint(_payloadData(result));
			})
			.catch(function (err) {
				frappe.show_alert({
					indicator: "red",
					message: (err && err.message) || __("Unable to save requirements."),
				});
			});
	}

	function _requireConfigurationId() {
		var ctx = routes.read_route_context();
		if (!ctx.configuration_id) {
			frappe.show_alert({
				message: __("Open a tender configuration from the dashboard to view this screen."),
				indicator: "orange",
			});
			routes.navigate(routes.ROUTES.DASHBOARD);
			return "";
		}
		return ctx.configuration_id;
	}

	function _bind(wrapper) {
		wrapper.addEventListener("click", function (event) {
			var target = event.target;
			if (target.closest("[data-itw-back]")) {
				event.preventDefault();
				routes.go_back_to_desk();
				return;
			}
			if (target.closest("[data-itw-req-drawer-close], [data-itw-req-drawer-cancel], [data-itw-req-drawer-backdrop]")) {
				event.preventDefault();
				_closeDrawer();
				return;
			}
			var editBtn = target.closest('[data-itw-req-action="edit"]');
			if (editBtn) {
				event.preventDefault();
				var row = editBtn.closest("[data-itw-req-row]");
				if (row) {
					_openDrawer(row.getAttribute("data-itw-req-code"));
				}
				return;
			}
			if (target.closest("[data-itw-req-drawer-save]")) {
				event.preventDefault();
				_saveSelected();
				return;
			}
			if (target.closest("[data-itw-req-save-all]")) {
				event.preventDefault();
				if (_state.selectedCode) {
					_saveSelected();
				} else {
					frappe.show_alert({ message: __("Select a requirement to save changes."), indicator: "blue" });
				}
				return;
			}
			if (target.closest("[data-itw-req-continue]")) {
				event.preventDefault();
				var btn = target.closest("[data-itw-req-continue]");
				if (btn && btn.disabled) {
					return;
				}
				routes.navigate(IMPL_SCHEDULE_ROUTE, { configuration_id: _state.configurationId });
			}
		});

		wrapper.addEventListener("input", function (event) {
			if (event.target && event.target.matches("[data-itw-req-search]")) {
				_state.filterText = event.target.value || "";
				var tableHost = _q("[data-itw-req-table-host]");
				if (tableHost) {
					tableHost.outerHTML = components.requirements_table(_filteredRows());
				}
			}
		});
	}

	function render(wrapper) {
		_state.wrapper = wrapper;
		shell.mount_wrapper(wrapper, _shellHtml());
		_bind(wrapper);
	}

	function show(wrapper) {
		shell.show({ screen_shell_class: SCREEN_SHELL });
		_state.configurationId = _requireConfigurationId();
		if (!_state.configurationId) {
			return Promise.resolve();
		}
		render(wrapper);
		return _fetch();
	}

	kentender.it_wizard.screens.it_requirements = {
		init: function (wrapper) {
			_state.wrapper = wrapper;
			shell.show({ screen_shell_class: SCREEN_SHELL });
		},
		show: show,
	};
})();
