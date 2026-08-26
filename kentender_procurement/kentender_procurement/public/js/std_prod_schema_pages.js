(function () {
	"use strict";

	var PAGE_CONFIGS = {
		"std-parameter-dictionary": {
			page: "std-parameter-dictionary",
			title: __("Parameter Dictionary"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_parameter_dictionary.html",
			screen: "parameters",
			shell_class: "std-prod-std-parameter-dictionary-shell",
			root_class: "std-prod-std-parameter-dictionary-root",
			iframe_class: "std-prod-std-parameter-dictionary-iframe",
			testid: "std-prod-std-parameter-dictionary",
		},
		"std-parameter-detail": {
			page: "std-parameter-detail",
			title: __("Parameter Detail"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_parameter_detail.html",
			screen: "parameter",
			shell_class: "std-prod-std-parameter-detail-shell",
			root_class: "std-prod-std-parameter-detail-root",
			iframe_class: "std-prod-std-parameter-detail-iframe",
			testid: "std-prod-std-parameter-detail",
		},
		"std-rule-dictionary": {
			page: "std-rule-dictionary",
			title: __("Rule Dictionary"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_rule_dictionary.html",
			screen: "rules",
			shell_class: "std-prod-std-rule-dictionary-shell",
			root_class: "std-prod-std-rule-dictionary-root",
			iframe_class: "std-prod-std-rule-dictionary-iframe",
			testid: "std-prod-std-rule-dictionary",
		},
		"std-rule-detail": {
			page: "std-rule-detail",
			title: __("Rule Detail"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_rule_detail.html",
			screen: "rule",
			shell_class: "std-prod-std-rule-detail-shell",
			root_class: "std-prod-std-rule-detail-root",
			iframe_class: "std-prod-std-rule-detail-iframe",
			testid: "std-prod-std-rule-detail",
		},
		"std-form-schema-manager": {
			page: "std-form-schema-manager",
			title: __("Form Schema Manager"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_form_schema_manager.html",
			screen: "forms",
			shell_class: "std-prod-std-form-schema-manager-shell",
			root_class: "std-prod-std-form-schema-manager-root",
			iframe_class: "std-prod-std-form-schema-manager-iframe",
			testid: "std-prod-std-form-schema-manager",
		},
		"std-form-detail-field-builder": {
			page: "std-form-detail-field-builder",
			title: __("Form Detail Field Builder"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_form_detail_field_builder.html",
			screen: "form",
			shell_class: "std-prod-std-form-detail-field-builder-shell",
			root_class: "std-prod-std-form-detail-field-builder-root",
			iframe_class: "std-prod-std-form-detail-field-builder-iframe",
			testid: "std-prod-std-form-detail-field-builder",
		},
		"std-requirement-schema-manager": {
			page: "std-requirement-schema-manager",
			title: __("Requirement Schema Manager"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_requirement_schema_manager.html",
			screen: "requirements",
			shell_class: "std-prod-std-requirement-schema-manager-shell",
			root_class: "std-prod-std-requirement-schema-manager-root",
			iframe_class: "std-prod-std-requirement-schema-manager-iframe",
			testid: "std-prod-std-requirement-schema-manager",
		},
		"std-price-schedule-schema": {
			page: "std-price-schedule-schema",
			title: __("Price Schedule Schema"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_price_schedule_schema.html",
			screen: "priceSchedules",
			shell_class: "std-prod-std-price-schedule-schema-shell",
			root_class: "std-prod-std-price-schedule-schema-root",
			iframe_class: "std-prod-std-price-schedule-iframe",
			testid: "std-prod-std-price-schedule-schema",
		},
		"std-evaluation-schema": {
			page: "std-evaluation-schema",
			title: __("Evaluation Schema"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_evaluation_schema.html",
			screen: "evaluation",
			shell_class: "std-prod-std-evaluation-schema-shell",
			root_class: "std-prod-std-evaluation-schema-root",
			iframe_class: "std-prod-std-evaluation-schema-iframe",
			testid: "std-prod-std-evaluation-schema",
		},
		"std-render-blocks": {
			page: "std-render-blocks",
			title: __("Render Blocks"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_render_blocks.html",
			screen: "renderBlocks",
			shell_class: "std-prod-std-render-blocks-shell",
			root_class: "std-prod-std-render-blocks-root",
			iframe_class: "std-prod-std-render-blocks-iframe",
			testid: "std-prod-std-render-blocks",
		},
	};

	Object.keys(PAGE_CONFIGS).forEach(function (page_name) {
		if (!frappe.pages[page_name]) {
			return;
		}
		var config = PAGE_CONFIGS[page_name];
		frappe.pages[page_name].on_page_load = function (wrapper) {
			frappe.require("/assets/kentender_procurement/js/std_prod_engine.js", function () {
				kentender.std_prod.mount_page(wrapper, config);
			});
		};
	});
})();
