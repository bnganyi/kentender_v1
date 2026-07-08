/* global frappe */
// STD-CFG-0230 — frappe.call facade for STD Version Configurator APIs.
frappe.provide("kentender_procurement.std_configurator_api");

(function () {
	"use strict";

	const API = "kentender_procurement.tender_management.api.std_configurator";
	const api = kentender_procurement.std_configurator_api;

	function _call(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: API + "." + method,
				args: args || {},
				callback: function (r) {
					resolve((r && r.message) || {});
				},
				error: function (err) {
					reject(err);
				},
			});
		});
	}

	api.getContext = function (templateCode) {
		return _call("get_std_configurator_context", { template_code: templateCode });
	};

	api.getSection = function (templateCode, section) {
		return _call("get_std_configurator_section", {
			template_code: templateCode,
			section: section,
		});
	};

	api.saveSection = function (templateCode, section, data) {
		return _call("save_std_configurator_section", {
			template_code: templateCode,
			section: section,
			data: data,
		});
	};

	api.getTechnicalJson = function (templateCode) {
		return _call("get_std_configurator_technical_json", { template_code: templateCode });
	};

	api.saveTechnicalJson = function (templateCode, packageJson) {
		return _call("save_std_configurator_technical_json", {
			template_code: templateCode,
			package_json: packageJson,
		});
	};

	api.getPreview = function (templateCode, mode) {
		return _call("get_std_configurator_preview", {
			template_code: templateCode,
			mode: mode || "summary",
		});
	};

	api.runValidation = function (templateCode) {
		return _call("run_std_configurator_validation", { template_code: templateCode });
	};

	api.runApplicabilityTest = function (templateCode, testCase) {
		return _call("run_std_configurator_applicability_test", {
			template_code: templateCode,
			test_case: testCase || null,
		});
	};

	api.submitForReview = function (templateCode, comment) {
		return _call("submit_std_configurator_for_review", {
			template_code: templateCode,
			comment: comment || "",
		});
	};

	api.activateVersion = function (templateCode, reason, options) {
		const opts = options || {};
		return _call("activate_std_configurator_version", {
			template_code: templateCode,
			reason: reason,
			active_from: opts.active_from || null,
			active_until: opts.active_until || null,
			is_default_active_version: opts.is_default_active_version == null ? 1 : opts.is_default_active_version,
		});
	};
})();
