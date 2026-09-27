// BDS-CHG-001 v0.8 §10.1 / §10.3 fixture payloads for BDS-DES-02 as the server
// sends them (`get_tender_overview`), and the structural-fidelity variants.
import TenderOverviewScreen from "./TenderOverviewScreen.vue";

const REF = "TND-MOH-2027-033";
const DOC = (key, label) => ({ key, label, published: "15 May 2027", view_href: `/api/method/x?key=${key}&inline=1`, download_href: `/api/method/x?key=${key}` });
const BEFORE = [
	"Sign in to start or continue a bid.",
	"Bid as one supplier organisation, or as a joint venture where this Tender permits it.",
	"An Authorised Signatory and a valid digital certificate are needed only when submitting.",
];

export function overview(variant = "") {
	const afterAddendum = ["", "SIGNED-OUT", "SUBMITTED"].includes(variant);
	const base = {
		tender: {
			reference: REF, title: "Supply and delivery of business laptops", description: "Ministry of Health · Open Tender · Youth reservation.", availability: "open", status_label: "",
			deadline: afterAddendum ? "12 Jun 2027, 11:00 EAT" : "5 Jun 2027, 11:00 EAT", published: "15 May 2027, 08:00 EAT", clarification_deadline: "27 May 2027, 17:00 EAT",
			clarifications_open: !afterAddendum, clarification_label: afterAddendum ? "Clarifications closed" : "Clarification deadline",
		},
		organisation: variant === "SIGNED-OUT" ? null : { id: "ORG-AFYA", legal_name: "Afya Digital Supplies Limited" },
		facts: {
			quantity: "250 Each", delivery_location: afterAddendum ? "Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi" : "", latest_delivery: "30 Sep 2027",
			currency: "KES", tender_security: "KES 500,000.00", bid_validity: "120 days",
		},
		documents: [DOC("invitation", "Invitation to Tender"), DOC("complete", "Complete Tender")],
		addenda: afterAddendum ? [{ reference: "ADD-MOH-2027-033-001", summary: "Delivery point clarified", issued: "31 May 2027, 09:00 EAT", current_deadline: "12 Jun 2027, 11:00 EAT", view_href: "/api/method/x?key=ADD" }] : [],
		answers: afterAddendum ? [{ question: "May the two comparable contracts be from different customers?", answer: "Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer.", answered: "26 May 2027, 11:00 EAT" }] : [],
		clarification: { can_ask: variant === "CANDIDATE-QUESTION", helper: "", closed_text: afterAddendum ? "Clarifications closed 27 May 2027, 17:00 EAT." : "" },
		notice: null, bid: null, action: { kind: "start_bid", label: "Start bid" }, start: null, before_you_start: BEFORE, cancellation: null, signed_in: variant !== "SIGNED-OUT",
	};
	if (variant === "SIGNED-OUT") base.action = { kind: "sign_in", label: "Sign in to start bid", href: `/login?redirect-to=/tenders/${REF}` };
	if (variant === "DRAFT" || variant === "CANDIDATE-QUESTION") {
		base.bid = { bid_reference: "BID-MOH-2027-033-001", status: "Draft", draft_version: 3, status_text: "Draft · 3 of 5 tasks complete", href: `/tenders/${REF}/bid` };
		base.action = { kind: "continue_bid", label: "Continue bid", href: `/tenders/${REF}/bid` };
	}
	if (variant === "SUBMITTED") {
		base.bid = { bid_reference: "BID-MOH-2027-033-001", status: "Submitted", status_text: "Submitted 10 Jun 2027, 14:32 EAT", receipt_reference: "RCPT-MOH-2027-033-001" };
		base.action = { kind: "view_receipt", label: "View receipt", href: `/tenders/${REF}/bid/receipt/RCPT-MOH-2027-033-001` };
	}
	if (variant === "CANCELLED") {
		base.tender = { ...base.tender, reference: "TND-MOH-2027-034", availability: "cancelled", status_label: "Cancelled" };
		base.action = { kind: "view_notice", label: "View notice", href: "/api/method/x?key=cancellation" };
	}
	if (variant === "JV-START") base.start = { organisation: { id: "ORG-KISIWA", legal_name: "Kisiwa Digital Limited" }, joint_venture_permitted: true, arrangements: ["Single organisation", "Joint venture"], notice_contacts: [{ contact_id: "C1", value: "tenders@kisiwadigital.example" }], notice_contact_help: "Mandatory Tender notices will be sent here. You can change this later to another verified Account email.", signatories: [{ assignment_id: "ASG-G", name: "Grace Njeri" }], agreements: [{ evidence_id: "EVD-JV", title: "kisiwa-jua-jv-agreement.pdf" }] };
	return base;
}

const VARIANTS = ["", "SIGNED-OUT", "JV-START", "DRAFT", "SUBMITTED", "CANDIDATE-QUESTION", "CANCELLED"];

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	VARIANTS.map((v) => ({
		name: "TenderOverviewScreen", variant: `BDS-DES-02${v ? `-${v}` : ""}`, frame, component: TenderOverviewScreen,
		props: { initial: overview(v), reference: v === "CANCELLED" ? "TND-MOH-2027-034" : REF }, path: `/tenders/${REF}`,
	})),
);
