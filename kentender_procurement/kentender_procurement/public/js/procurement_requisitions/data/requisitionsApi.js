// REQ-CHG-001 v1.11 — the browser's only door to the server (§10). Every
// command carries an idempotency key and expected record version; business
// rules stay on the server.
import { frappeCall } from "../../req_shared/frappeCall.js";

const API = "kentender_procurement.procurement_requisitions.api";
const call = (method, args) => frappeCall(`${API}.${method}`, args || {});
const json = (value) => JSON.stringify(value === undefined ? null : value);

// §10.1 reads
export const getWorkspace = (filters) => call("get_requisition_workspace", { workspace_filters: json(filters || {}) });
export const getStartPreview = (planItemId) => call("get_start_preview", { plan_item_id: planItemId });
export const getRecord = (requisition, version) => call("get_requisition_record", { requisition, version: version || "" });
export const getDepartmentTask = (task) => call("get_department_approval_task", { task });
export const getProcurementTask = (task) => call("get_procurement_authorisation_task", { task });
export const getHistory = (requisition) => call("get_requisition_history", { requisition });

// §10.2 Draft commands
export const prepare = (a) => call("prepare_it_equipment_requisition", a);
export const saveSummary = (a) => call("save_requisition_summary", { ...a, summary_values: json(a.summary_values) });
export const addSameSpecificationItems = (a) => call("add_same_specification_items", { ...a, shared_values: json(a.shared_values), item_rows: json(a.item_rows) });
export const updateSharedItemDetails = (a) => call("update_shared_item_details", { ...a, shared_values: json(a.shared_values), requisition_item_ids: json(a.requisition_item_ids) });
export const updateItem = (a) => call("update_requisition_item", { ...a, item_values: json(a.item_values) });
export const removeItem = (a) => call("remove_requisition_item", a);
export const saveProposalDraft = (a) => call("save_requirement_proposal_draft", { ...a, technical_rows: json(a.technical_rows), acceptance_rows: json(a.acceptance_rows), support_values: json(a.support_values) });
export const applyPackage = (a) => call("apply_selected_requirement_package", { ...a, technical_rows: json(a.technical_rows), acceptance_rows: json(a.acceptance_rows), support_values: json(a.support_values) });
export const resetStandardValues = (a) => call("reset_standard_values", a);
export const saveWarrantyAndSupport = (a) => call("save_warranty_and_support", { ...a, warranty_values: json(a.warranty_values) });
export const addTechnical = (a) => call("add_technical_requirement", { ...a, technical_requirement_values: json(a.values) });
export const updateTechnical = (a) => call("update_technical_requirement", { ...a, technical_requirement_values: json(a.values) });
export const removeTechnical = (a) => call("remove_technical_requirement", a);
export const addService = (a) => call("add_related_service", { ...a, service_values: json(a.values) });
export const updateService = (a) => call("update_related_service", { ...a, service_values: json(a.values) });
export const removeService = (a) => call("remove_related_service", a);
export const addAcceptance = (a) => call("add_acceptance_requirement", { ...a, acceptance_values: json(a.values) });
export const updateAcceptance = (a) => call("update_acceptance_requirement", { ...a, acceptance_values: json(a.values) });
export const removeAcceptance = (a) => call("remove_acceptance_requirement", a);
export const addMaterial = (a) => call("add_supporting_material", { ...a, material_values: json(a.values) });
export const removeMaterial = (a) => call("remove_supporting_material", a);

// §10.2 lifecycle
export const sendForDepartmentApproval = (a) => call("send_for_department_approval", a);
export const submitToProcurement = (a) => call("submit_requisition_to_procurement", a);
export const returnToAuthor = (a) => call("return_to_department_author", a);
export const returnToDepartment = (a) => call("return_requisition_to_department", a);
export const changeLeadDepartment = (a) => call("change_requisition_lead_department", a);
export const withdraw = (a) => call("withdraw_requisition", a);
export const requestPlanningCorrection = (a) => call("request_upstream_plan_correction", a);
export const authorise = (a) => call("authorise_requisition", a);
export const revoke = (a) => call("revoke_unconsumed_authorisation", a);
export const prepareAfterCorrection = (a) => call("prepare_requisition_after_plan_correction", a);
export const createCorrectionDraft = (a) => call("create_requisition_correction_draft", a);
export const exportRequisition = (requisition, version) => call("export_requisition", { requisition, version: version || "" });
