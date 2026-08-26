// STD-CHG-001 v1.3 Phase 11 — PCFG-03..09 share one generic table+form editor
// (StdCfgAreaGeneric.vue) driven by this registry, rather than 7 hand-authored
// bespoke editors. Column/field lists are the real `STD Cfg *` doctype fields
// (kentender_procurement/std_configuration/doctype/*), not invented shapes —
// §15's artboards are static illustrative fixtures; live editing must match
// the real save_std_* contracts in std_configuration_api.py. PCFG-01 and
// PCFG-02 are architecturally distinct (Draft-field save; Section/Content
// Block tree) and are their own dedicated components, not in this registry.

const SELECT = (options) => options.split("\n");

export const AREA_REGISTRY = {
	"PCFG-03": {
		title: __("Tender Parameters"),
		saveMethod: "kentender_procurement.std_configuration.api.std_configuration_api.save_std_parameters",
		savePayloadKey: "parameters",
		groups: [
			{
				doctype: "STD Cfg Parameter Definition",
				label: __("Parameters"),
				columns: [
					{ key: "label", label: __("Parameter") },
					{ key: "value_type", label: __("Type") },
					{ key: "runtime_owner", label: __("Supplied by") },
					{ key: "required", label: __("Required treatment"), boolean: true },
					{ key: "render_binding", label: __("Output") },
				],
				fields: [
					{ key: "parameter_key", label: __("Parameter key"), type: "text", required: true },
					{ key: "label", label: __("Field label"), type: "text", required: true },
					{ key: "value_type", label: __("Value type"), type: "select", options: SELECT("Text\nLong text\nInteger\nDecimal\nDate\nDatetime\nDuration\nMoney\nChoice\nBoolean\nAddress\nContact") },
					{ key: "runtime_owner", label: __("Supplied by"), type: "select", options: SELECT("System derived\nTender Preparation\nTender Management\nContract Formation") },
					{ key: "required", label: __("Required"), type: "checkbox" },
					{ key: "required_when", label: __("Required when (conditional)"), type: "text" },
					{ key: "allowed_values", label: __("Allowed values"), type: "textarea" },
					{ key: "minimum_value", label: __("Minimum value"), type: "text" },
					{ key: "maximum_value", label: __("Maximum value"), type: "text" },
					{ key: "render_binding", label: __("Rendered in"), type: "text" },
					{ key: "downstream_binding", label: __("Used by"), type: "text" },
					{ key: "help_text", label: __("Help text"), type: "textarea" },
				],
			},
		],
	},
	"PCFG-04": {
		title: __("IT Requirements"),
		saveMethod: "kentender_procurement.std_configuration.api.std_configuration_api.save_std_requirement_schema",
		savePayloadKey: "categories",
		groups: [
			{
				doctype: "STD Cfg Requirement Schema",
				label: __("Categories"),
				columns: [
					{ key: "category", label: __("Category") },
					{ key: "allowed_response_types", label: __("Allowed responses") },
					{ key: "evidence_mode", label: __("Evidence required") },
					{ key: "acceptance_mode", label: __("Acceptance condition") },
				],
				fields: [
					{ key: "category", label: __("Category"), type: "select", required: true, options: SELECT("Functional\nArchitecture\nPerformance\nSecurity\nIntegration\nData and migration\nReporting and analytics\nHosting and infrastructure\nTraining and knowledge transfer\nSupport and warranty\nTesting and acceptance\nAccessibility and usability\nBusiness continuity and disaster recovery\nRegulatory compliance") },
					{ key: "display_order", label: __("Order"), type: "int" },
					{ key: "allowed_response_types", label: __("Allowed responses"), type: "textarea" },
					{ key: "evidence_mode", label: __("Evidence required"), type: "text" },
					{ key: "acceptance_mode", label: __("Acceptance condition"), type: "text" },
					{ key: "vendor_neutrality_trigger", label: __("Vendor-neutrality trigger"), type: "checkbox" },
					{ key: "vendor_neutrality_note", label: __("Vendor-neutrality note"), type: "textarea" },
					{ key: "render_binding", label: __("Tender document mapping"), type: "text" },
					{ key: "bidder_response_binding", label: __("Bidder response mapping"), type: "text" },
					{ key: "evaluation_binding", label: __("Evaluation mapping"), type: "text" },
					{ key: "contract_carry_forward_binding", label: __("Contract mapping"), type: "text" },
				],
			},
		],
	},
	"PCFG-05": {
		title: __("Schedule, Inventory and Background"),
		saveMethod: "kentender_procurement.std_configuration.api.std_configuration_api.save_std_schedule_inventory_background",
		groups: [
			{
				doctype: "STD Cfg Schedule Schema",
				label: __("Implementation Schedule"),
				savePayloadKey: "schedule_rows",
				columns: [
					{ key: "title", label: __("Milestone") },
					{ key: "required_deliverable", label: __("Required deliverable") },
					{ key: "completion_rule", label: __("Completion rule") },
					{ key: "dependency_description", label: __("Dependency") },
				],
				fields: [
					{ key: "milestone_key", label: __("Milestone key"), type: "text", required: true },
					{ key: "title", label: __("Milestone"), type: "text", required: true },
					{ key: "display_order", label: __("Order"), type: "int" },
					{ key: "required_deliverable", label: __("Required deliverable"), type: "textarea" },
					{ key: "completion_rule", label: __("Completion rule"), type: "text" },
					{ key: "duration_days", label: __("Duration (days)"), type: "int" },
					{ key: "dependency_description", label: __("Dependency"), type: "text" },
					{ key: "acceptance_checkpoint", label: __("Acceptance checkpoint"), type: "textarea" },
					{ key: "render_binding", label: __("Used in (tender)"), type: "text" },
					{ key: "contract_binding", label: __("Used in (contract)"), type: "text" },
				],
			},
			{
				doctype: "STD Cfg Inventory Schema",
				label: __("System Inventory"),
				savePayloadKey: "inventory_rows",
				columns: [
					{ key: "category", label: __("Category") },
					{ key: "requirement_link", label: __("Requirement link") },
					{ key: "schedule_link", label: __("Schedule link") },
					{ key: "price_schedule_link_policy", label: __("Price Schedule link policy") },
				],
				fields: [
					{ key: "category", label: __("Category"), type: "select", required: true, options: SELECT("Hardware\nSoftware\nLicence\nService\nTraining\nSupport\nHosting\nIntegration") },
					{ key: "price_schedule_link_policy", label: __("Price Schedule link policy"), type: "select", options: SELECT("Required\nOptional") },
					{ key: "requirement_link", label: __("Requirement link"), type: "text" },
					{ key: "schedule_link", label: __("Schedule link"), type: "text" },
					{ key: "render_binding", label: __("Output"), type: "text" },
				],
			},
		],
	},
	"PCFG-06": {
		title: __("Price Schedules"),
		saveMethod: "kentender_procurement.std_configuration.api.std_configuration_api.save_std_price_schemas",
		savePayloadKey: "price_schemas",
		groups: [
			{
				doctype: "STD Cfg Price Schema",
				label: __("Price Schedules"),
				columns: [
					{ key: "family", label: __("Family") },
					{ key: "line_description", label: __("Line description") },
					{ key: "currency_rule", label: __("Currency") },
					{ key: "calculation", label: __("Calculation use") },
				],
				fields: [
					{ key: "family", label: __("Family"), type: "select", required: true, options: SELECT("Software and infrastructure\nImplementation services\nTraining\nRecurrent support") },
					{ key: "line_description", label: __("Line description"), type: "text" },
					{ key: "quantity_unit_source", label: __("Quantity / unit supplied from"), type: "text" },
					{ key: "currency_rule", label: __("Currency"), type: "text" },
					{ key: "tax_treatment", label: __("Tax treatment"), type: "text" },
					{ key: "bidder_price_fields", label: __("Bidder price fields"), type: "textarea" },
					{ key: "calculation", label: __("Calculation"), type: "text" },
					{ key: "evaluated_total_binding", label: __("Evaluated total"), type: "text" },
				],
			},
		],
	},
	"PCFG-07": {
		title: __("Evaluation and Qualification"),
		saveMethod: "kentender_procurement.std_configuration.api.std_configuration_api.save_std_evaluation_schema",
		savePayloadKey: "criteria",
		groups: [
			{
				doctype: "STD Cfg Evaluation Schema",
				label: __("Criteria"),
				columns: [
					{ key: "stage", label: __("Stage") },
					{ key: "criterion_structure", label: __("Criterion structure") },
					{ key: "treatment", label: __("Treatment") },
					{ key: "response_source", label: __("Response source") },
				],
				fields: [
					{ key: "stage", label: __("Stage"), type: "select", required: true, options: SELECT("Preliminary responsiveness\nTechnical evaluation\nFinancial evaluation\nPost-qualification") },
					{ key: "criterion_key", label: __("Criterion key"), type: "text", required: true },
					{ key: "criterion_structure", label: __("Criterion structure"), type: "text" },
					{ key: "display_order", label: __("Order"), type: "int" },
					{ key: "treatment", label: __("Treatment"), type: "select", options: SELECT("Pass/Fail\nScored\nPass/Fail or scored\nCalculated financial result") },
					{ key: "response_source", label: __("Response source"), type: "text" },
					{ key: "evidence_source", label: __("Evidence source"), type: "text" },
					{ key: "weight", label: __("Weight"), type: "text" },
					{ key: "threshold", label: __("Threshold"), type: "text" },
					{ key: "financial_basis", label: __("Financial basis"), type: "text" },
					{ key: "failure_effect", label: __("Failure effect"), type: "text" },
				],
			},
		],
	},
	"PCFG-08": {
		title: __("Forms and Evidence"),
		saveMethod: "kentender_procurement.std_configuration.api.std_configuration_api.save_std_form_schemas",
		savePayloadKey: "forms",
		groups: [
			{
				doctype: "STD Cfg Form Schema",
				label: __("Forms"),
				columns: [
					{ key: "form_name", label: __("Form") },
					{ key: "activation", label: __("Activation") },
					{ key: "response_treatment", label: __("Response treatment") },
				],
				fields: [
					{ key: "form_key", label: __("Form key"), type: "text", required: true },
					{ key: "form_name", label: __("Form"), type: "text", required: true },
					{ key: "activation", label: __("Activation"), type: "select", options: SELECT("Always\nConditional") },
					{ key: "activation_condition", label: __("Activation condition"), type: "text" },
					{ key: "locked_wording", label: __("Locked wording"), type: "textarea" },
					{ key: "response_treatment", label: __("Response treatment"), type: "text" },
					{ key: "evidence_rule", label: __("Evidence rule"), type: "text" },
					{ key: "render_location", label: __("Render location"), type: "text" },
				],
			},
		],
	},
	"PCFG-09": {
		title: __("Contract and Outputs"),
		saveMethod: "kentender_procurement.std_configuration.api.std_configuration_api.save_std_contract_and_outputs",
		groups: [
			{
				doctype: "STD Cfg Contract Schema",
				label: __("Contract values"),
				savePayloadKey: "contract_values",
				columns: [
					{ key: "value_category", label: __("Value") },
					{ key: "supplied_by", label: __("Supplied by") },
					{ key: "required_treatment", label: __("Required treatment") },
					{ key: "contract_binding", label: __("Output") },
				],
				fields: [
					{ key: "value_category", label: __("Value"), type: "select", required: true, options: SELECT("Performance security\nAdvance-payment security\nPayment milestones\nOperational acceptance\nWarranty period\nSupport period\nIntellectual-property treatment\nSoftware licence categories\nConfidentiality\nInsurance\nLiability limit\nDispute resolution") },
					{ key: "supplied_by", label: __("Supplied by"), type: "text" },
					{ key: "required_treatment", label: __("Required treatment"), type: "select", options: SELECT("Required\nConditional") },
					{ key: "condition", label: __("Condition"), type: "text" },
					{ key: "scc_binding", label: __("SCC output"), type: "text" },
					{ key: "contract_binding", label: __("Contract output"), type: "text" },
				],
			},
			{
				doctype: "STD Cfg Output Mapping",
				label: __("Output mappings"),
				savePayloadKey: "output_mappings",
				columns: [
					{ key: "source_binding_key", label: __("Source binding") },
					{ key: "target", label: __("Target") },
					{ key: "required", label: __("Required"), boolean: true },
				],
				fields: [
					{ key: "source_binding_key", label: __("Source binding key"), type: "text", required: true },
					{ key: "target", label: __("Target"), type: "select", required: true, options: SELECT("Render\nRequisition\nTender\nBidder response\nEvaluation\nContract Formation\nContract Management") },
					{ key: "required", label: __("Required"), type: "checkbox" },
				],
				defaults: { owning_area: "PCFG-09" },
			},
		],
	},
};
