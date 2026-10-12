// Tender-security intake duty adapter — one function per whitelisted endpoint
// (kentender_procurement.bid_submission.api). The Head of Procurement Function
// sees officers and assignments only; nothing here returns an intake, a
// supplier or a bid. A refusal arrives as { outcome: "FORBIDDEN" }.
import { frappeCall } from "./call.js";

const M = "kentender_procurement.bid_submission.api.";

export const getDuty = (tender) => frappeCall(M + "get_tender_security_duty", { tender_reference: tender }, "GET");
export const assignOfficer = (values) => frappeCall(M + "assign_tender_security_intake_officer", values);
export const revokeOfficer = (values) => frappeCall(M + "revoke_tender_security_intake_officer", values);
export const listConflicts = () => frappeCall(M + "list_tender_security_duty_conflicts", { status: "Open" }, "GET");
