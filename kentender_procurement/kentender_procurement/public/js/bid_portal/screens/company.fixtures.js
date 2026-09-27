// BDS-CHG-001 v0.8 §10.9 fixture payloads for BDS-DES-08 as the server sends
// them (`get_bid_task` for the company task), and the structural-fidelity
// variants at both frames.
import CompanyTaskScreen from "./CompanyTaskScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const FIELD = (handle, kind, label, value, extra = {}) => ({ handle, kind, label, help: "", editable: true, visible: true, required: true, value, shown_when: null, issue: null, ...extra });
const DECLARATION_LABELS = ["Tenderer information", "Form of Tender", "Independent tender determination", "Self-declaration — not debarred", "Self-declaration — no corrupt or fraudulent practice", "Code of ethics commitment", "Youth reservation declaration"];

function declarations(done) {
	return DECLARATION_LABELS.map((label, i) => {
		const confirmation = i > 0 && i < 6;
		const status = !done ? "Not started" : confirmation ? "Confirmed" : "Complete";
		return {
			key: `g-decl-${i}`, label, status, tone: done ? "live" : "draft", confirmed_text: done && confirmation ? "Confirmed by David Ouma" : "", statement: "", facts: [],
			fields: [FIELD(`h-decl-${i}`, confirmation ? "confirmation" : "short_text", `${label} response`, done ? (confirmation ? true : "Answered") : null)],
		};
	});
}
function security(entered, recorded) {
	return {
		key: "g-security", entered,
		fields: [
			FIELD("h-sec-form", "single_choice", "Type", entered ? "Demand Bank Guarantee" : null, { options: ["Demand Bank Guarantee", "Insurance Guarantee"] }),
			FIELD("h-sec-issuer", "short_text", "Issuer", entered ? "Kenya Commercial Bank PLC" : null),
			FIELD("h-sec-ref", "short_text", "Reference", entered ? "KCB/TG/2027/8841" : null),
			FIELD("h-sec-valid", "date", "Valid until", entered ? "2027-11-15" : null),
			FIELD("h-sec-proof", "evidence", "Tender security proof", null, { evidence: { type: "", minimum: 1, maximum: 1, mandatory: true, files: entered ? [{ id: "EV-1", name: "tender-security.pdf", status: "Accepted", size_bytes: 1000 }] : [] } }),
		],
		published_facts: [{ label: "Amount · published", value: "KES 500,000.00" }, { label: "Currency · published", value: "KES" }],
		physical: !entered ? null : recorded
			? { tone: "live", title: "Physical original recorded as received", text: "", facts: [{ label: "Receipt", value: "MOH-SEC-2027-033-017" }, { label: "Received at", value: "10 Jun 2027, 10:00 EAT" }] }
			: { tone: "warning", title: "Physical original not yet recorded", text: "Deliver the original bank guarantee to the Ministry of Health procurement office before 12 Jun 2027, 11:00 EAT. You may submit electronically, but failure to deliver the original before closing may disqualify the bid.", facts: [] },
	};
}
const SINGLE = {
	kind: "single", update_account_href: "/account", snapshot_text: "From your Account · copied to this bid on 19 May 2027, 09:20 EAT", current_text: "This bid is using your current Account details.", update: null,
	facts: [{ label: "Legal name", value: "Afya Digital Supplies Limited" }, { label: "Registration number", value: "PVT-9X7K2M" }, { label: "KRA PIN", value: "P051234567X" }, { label: "Address", value: "Westlands Business Park, Waiyaki Way, Nairobi" }, { label: "Arrangement", value: "Single organisation" }],
};

/** One company-task read for a board variant ("", SECURITY, JV, ACCOUNT-UPDATE). */
export function companyTask(variant = "") {
	const guided = workspace(variant === "JV" ? "IN-PROGRESS" : "IN-PROGRESS");
	const base = {
		bid: { reference: "BID-MOH-2027-033-001", tender_reference: REF, record_version: 20 },
		page: { title: "Company, declarations and tender security", description: "Confirm who is bidding and complete the required legal forms.", back_href: `/tenders/${REF}/bid`, refs_line: "" },
		badge: { label: "Complete", tone: "live" }, organisation: SINGLE,
		contact: { assigned: "David Ouma · Bid Coordinator", notice_email: "tenders@afyadigital.example", notice_verified: true, notice_help: "Mandatory clarification, addendum, deadline and cancellation notices are sent here.", email: "david.ouma@afyadigital.example", phone: "+254 709 555 015", note: "These values apply only to this bid.", record_version: 4, notice: { arrangement: "ARR-MOH-2027-033-001", record_version: 4, current: "C1", email: "tenders@afyadigital.example", options: [{ contact_id: "C1", value: "tenders@afyadigital.example" }, { contact_id: "C2", value: "bids@afyadigital.example" }] } },
		declarations: declarations(true), tender_security: security(true, true),
		signatory: { name: "Mary Wanjiku", job_title: "Managing Director", organisation: "", authority_href: "/api/method/x?evidence=1", certificate: { status: "Ready", tone: "live" } },
		footer: { save_label: "Save and continue", next_href: `/tenders/${REF}/bid/requirements` },
		next_step: { ...guided.next_step, headline: "Continue the requirements and evidence task.", sentence: "" }, journey: guided.journey,
	};
	switch (variant) {
		case "SECURITY":
			return { ...base, tender_security: security(true, false) };
		case "JV":
			return {
				...base, badge: { label: "In progress", tone: "draft" },
				organisation: {
					...SINGLE, kind: "joint_venture", current_text: "This bid is using your current Account details.",
					facts: [{ label: "Joint-venture name", value: "Kisiwa–Jua Technology JV" }, { label: "Lead organisation", value: "Kisiwa Digital Limited" }, { label: "Arrangement", value: "Joint venture" }],
					members: [{ name: "Kisiwa Digital Limited", role: "Lead", status: "Active" }, { name: "Jua Technology Limited", role: "Member", status: "Active" }],
				},
				contact: { ...base.contact, assigned: "Peter Mwangi", notice_email: "tenders@kisiwadigital.example" },
				declarations: declarations(false), tender_security: security(false, false),
				signatory: { name: "Grace Njeri", job_title: "", organisation: "Kisiwa Digital Limited (lead)", authority_href: "", certificate: null },
				next_step: { ...base.next_step, headline: "Continue the company, declarations and tender security task." },
			};
		case "ACCOUNT-UPDATE":
			return {
				...base,
				organisation: {
					...SINGLE, current_text: "",
					update: { fact: "Address", rows: [{ label: "This bid", value: "Westlands Business Park, Waiyaki Way, Nairobi" }, { label: "Current Account", value: "Updated registered address, Riverside Drive, Nairobi" }], note: "Neither action edits the Account. Use updated details refreshes only this Draft and revalidates the affected forms.", record_version: 20 },
				},
			};
		default:
			return base;
	}
}

const VARIANTS = [["BDS-DES-08", ""], ["BDS-DES-08-SECURITY", "SECURITY"], ["BDS-DES-08-JV", "JV"], ["BDS-DES-08-ACCOUNT-UPDATE", "ACCOUNT-UPDATE"]];

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	VARIANTS.map(([variant, key]) => ({ name: "CompanyTaskScreen", variant, frame, component: CompanyTaskScreen, props: { initial: companyTask(key), reference: REF }, path: `/tenders/${REF}/bid/company` })),
);
