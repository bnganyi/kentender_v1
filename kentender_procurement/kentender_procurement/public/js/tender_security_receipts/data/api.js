// Blind intake data adapter — one function per whitelisted endpoint
// (kentender_procurement.bid_submission.api). Reads return outcome data
// (OK / FORBIDDEN); nothing here sees or derives a bid.
import { frappeCall } from "./call.js";

const M = "kentender_procurement.bid_submission.api.";

export const listIntakes = ({ tender }) => frappeCall(M + "list_my_tender_security_intakes", { tender_reference: tender || "" }, "GET");
export const getRequirement = (tender) => frappeCall(M + "get_tender_security_requirement", { tender_reference: tender }, "GET");
export const recordIntake = (values, key) => frappeCall(M + "record_physical_tender_security_receipt", { ...values, idempotency_key: key });
