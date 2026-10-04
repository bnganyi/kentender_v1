// BDS-CHG-001 v0.8 §10.8 fixture payloads for BDS-DES-07 as the server sends
// them (`get_bid_task` for the documents task), and the structural-fidelity
// variants at both frames. The two dialog artboards draw the unchanged page
// beneath the Ask-a-question dialog; the page is what is compared.
import DocumentsTaskScreen from "./DocumentsTaskScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const DOC = (key, label) => ({ key, label, published: "15 May 2027", view_href: `/api/method/x?key=${key}&inline=1`, download_href: `/api/method/x?key=${key}` });
const ACK_LABEL = "I have reviewed ADD-MOH-2027-033-001 and understand that the delivery point and submission deadline changed.";
const ANSWER = { key: "ANS-1", question: "May the two comparable contracts be from different customers?", answer: "Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer.", answered: "Answered 26 May 2027, 11:00 EAT", notice: { status: "Delivered", tone: "live" } };
const NOTICES = {
	Queued: { status: "Queued", tone: "pending", text: "This notice is waiting to be sent. You can read the current Tender information here now.", destination: "Notice to tenders@afyadigital.example", can_update_contact: false },
	Sent: { status: "Sent", tone: "pending", text: "Delivery has not been confirmed. You can read the current Tender information here now.", destination: "Notice to tenders@afyadigital.example", can_update_contact: false },
	Failed: { status: "Delivery problem", tone: "attention", text: "The notice could not be delivered to your selected Tender notice email. The current Tender information remains available here.", destination: "Notice to tenders@afyadigital.example", can_update_contact: true },
};

function addendum({ acknowledged = false, notice = null } = {}) {
	return {
		reference: "ADD-MOH-2027-033-001", summary: "Delivery point clarified", label: "ADD-MOH-2027-033-001 · Delivery point clarified", issued: "31 May 2027, 09:00 EAT", revised_deadline: "12 Jun 2027, 11:00 EAT",
		view_href: "/api/method/x?key=ADD&inline=1", download_href: "/api/method/x?key=ADD", notice,
		acknowledgement: { handle: "h-ack-1", label: ACK_LABEL, value: acknowledged, acknowledged_text: acknowledged ? "Acknowledged by David Ouma on 1 Jun 2027, 12:10 EAT" : "", moves_bid: false },
	};
}

/** One documents-task read for a board variant. */
export function documentsTask(variant = "") {
	const guided = workspace(["", "COMPLETE"].includes(variant) || variant.startsWith("NOTICE") ? "ADDENDUM" : "IN-PROGRESS");
	const nextStep = ["COMPLETE", "OPEN", "CLOSED"].includes(variant)
		? { ...guided.next_step, kind: "your_turn", label: "Your turn", headline: "Continue the requirements and evidence task.", sentence: "", blockers: [], fixes: [] }
		: guided.next_step;
	const base = {
		bid: { reference: "BID-MOH-2027-033-001", tender_reference: REF, record_version: 12 }, tender: { reference: REF, title: "Supply and delivery of business laptops" },
		page: { title: "Tender documents, clarifications and addenda", description: "Review the current Tender, ask questions before the clarification deadline and acknowledge issued addenda.", back_href: `/tenders/${REF}/bid` },
		badge: { label: "Needs attention", tone: "attention" }, documents: [DOC("invitation", "Invitation to Tender"), DOC("complete", "Complete Tender")],
		addenda: [addendum()], answers: [ANSWER], clarification: { can_ask: false, deadline: "27 May 2027, 17:00 EAT", closed_text: "Clarifications closed 27 May 2027, 17:00 EAT." },
		organisation: { id: "ORG-AFYA", legal_name: "Afya Digital Supplies Limited" },
		footer: { save_label: "Save and continue", next_href: `/tenders/${REF}/bid/company`, blocked_text: "Acknowledge the addendum to continue." },
		notice_contact: { arrangement: "ARR-MOH-2027-033-001", record_version: 3, current: "C1", email: "tenders@afyadigital.example", options: [{ contact_id: "C1", value: "tenders@afyadigital.example" }, { contact_id: "C2", value: "bids@afyadigital.example" }] },
		next_step: nextStep, journey: guided.journey,
	};
	switch (variant) {
		case "COMPLETE":
			return { ...base, badge: { label: "Complete", tone: "live" }, addenda: [addendum({ acknowledged: true })], footer: { ...base.footer, blocked_text: "" } };
		case "OPEN":
			return { ...base, badge: null, addenda: [], answers: [], clarification: { can_ask: true, deadline: "27 May 2027, 17:00 EAT", closed_text: "" }, footer: { ...base.footer, blocked_text: "" } };
		case "CLOSED":
			return { ...base, badge: null, addenda: [], footer: { ...base.footer, blocked_text: "" } };
		case "NOTICE-QUEUED":
			return { ...base, addenda: [addendum({ notice: NOTICES.Queued })] };
		case "NOTICE-SENT":
			return { ...base, addenda: [addendum({ notice: NOTICES.Sent })] };
		case "NOTICE-FAILED":
			return { ...base, addenda: [addendum({ notice: NOTICES.Failed })] };
		default:
			return base;
	}
}

const VARIANTS = [
	["BDS-DES-07", ""], ["BDS-DES-07-COMPLETE", "COMPLETE"], ["BDS-DES-07-QUESTION-OPEN / BDS-DES-07-NONE", "OPEN"], ["BDS-DES-07-QUESTION-OPEN-DIALOG", "OPEN"],
	["BDS-DES-07-QUESTION-OPEN-DIALOG · success", "OPEN"], ["BDS-DES-07-CLOSED", "CLOSED"], ["BDS-DES-07 notice pending · Queued", "NOTICE-QUEUED"],
	["BDS-DES-07 notice pending · Sent", "NOTICE-SENT"], ["BDS-DES-07-NOTICE", "NOTICE-FAILED"],
];
export const DOCUMENTS_VARIANTS = VARIANTS.map(([label]) => label);

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	VARIANTS.map(([variant, key]) => ({ name: "DocumentsTaskScreen", variant, frame, component: DocumentsTaskScreen, props: { initial: documentsTask(key), reference: REF }, path: `/tenders/${REF}/bid/documents` })),
);
