// BDS-CHG-001 v0.8 §10.10 fixture payloads for BDS-DES-09 as the server sends
// them (`get_bid_task` for the requirements task), and the structural-
// fidelity variants at both frames. The response-drawer artboard draws the
// unchanged page beneath the drawer; the page is what is compared.
import RequirementsTaskScreen from "./RequirementsTaskScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const FIELD = (handle, kind, label, value, extra = {}) => ({ handle, kind, label, help: "", editable: true, visible: true, required: true, value, shown_when: null, issue: null, ...extra });
const FILE = (name, status = "Accepted") => ({ id: `EV-${name}`, name, status, size_bytes: 1000 });
const TECH = [
	["Electrical compatibility", "Suitable for Kenyan mains supply", "Yes — 240 V, 50 Hz adaptor supplied"], ["New and unused equipment", "Yes", "Yes — all units new and unused"], ["Memory", "Minimum 16 GB", "16 GB"],
	["Storage capacity", "Minimum 512 GB", "512 GB"], ["Storage type", "NVMe SSD", "NVMe SSD"], ["Display size", "Minimum 14.0 inches", "14.0 inches"], ["Battery runtime", "Minimum 8 hours", "10 hours"],
	["Processor requirement", "64-bit business-class", "64-bit business-class"], ["Operating-system compatibility", "Approved organisational OS", "Windows 11 Pro compatible"],
	["Network connectivity", "Wi-Fi 6 and Bluetooth", "Wi-Fi 6E and Bluetooth 5.3"], ["Required ports", "USB-C ×2; USB-A ×2; HDMI", "USB-C ×2; USB-A ×2; HDMI"],
];
const WARRANTY = [["Minimum warranty 36 months", "36 months"], ["On-site support required", "Yes"], ["Maximum support response 8 hours", "4 hours"], ["Manufacturer support required", "Yes"], ["Service location within Kenya", "Nairobi service centre"], ["Escalation and warranty contacts", "Supplied"]];
const EVIDENCE = ["Manufacturer authorisation", "Product datasheet", "Warranty and support commitment", "Kenya service-centre details"];

function row(key, label, requirement, response, file, status = "Complete") {
	return { key, label, requirement, response, evidence: file, status, tone: status === "Complete" ? "live" : "attention", facts: [{ label: "Required", value: requirement }], statement: "", fields: [FIELD(`${key}-v`, "short_text", "Offered value", response), FIELD(`${key}-e`, "evidence", "Evidence reference", null, { evidence: { files: [FILE(file)] } })] };
}

/** One requirements-task read for a board variant ("", ATTENTION, ADDENDUM). */
export function requirementsTask(variant = "") {
	const attention = variant === "ATTENTION";
	const guided = workspace(variant === "ADDENDUM" ? "ADDENDUM" : "IN-PROGRESS");
	const technical = TECH.map(([label, req, resp], i) => row(`t${i}`, label, req, resp, "Product datasheet", attention && i !== 1 ? "Needs evidence" : "Complete"));
	const sections = ["Offered goods", "Technical requirements", "Warranty and support", "Experience", "Evidence"].map((label, i) => {
		const bad = (attention && (i === 1 || i === 4)) || (variant === "ADDENDUM" && i === 0);
		return { key: ["goods", "technical", "warranty", "experience", "evidence"][i], label, status: bad ? "Needs attention" : "Complete", tone: bad ? "attention" : "live" };
	});
	return {
		bid: { reference: "BID-MOH-2027-033-001", tender_reference: REF, record_version: 30 },
		page: { title: "Requirements and supporting evidence", description: "State what you are offering and attach the evidence requested by the Tender.", back_href: `/tenders/${REF}/bid` },
		badge: attention || variant === "ADDENDUM" ? { label: "Needs attention", tone: "attention" } : { label: "Complete", tone: "live" },
		sections,
		attention: attention ? { tone: "critical", title: "Fix 1 item", items: [{ key: "ev1", label: "Replace the rejected product datasheet" }] }
			: variant === "ADDENDUM" ? { tone: "warning", title: "Review 1 changed response", items: [{ key: "goods", label: "Confirm current delivery location" }] } : null,
		goods: { key: "goods", fields: [FIELD("g-model", "short_text", "Offered model", "ApexBook Pro 14"), FIELD("g-date", "date", "Delivery date", "2027-09-15")], published: [{ label: "Quantity · published", value: "250 Each" }, { label: "Delivery location · published", value: "Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi" }] },
		technical, warranty: WARRANTY.map(([label, resp], i) => row(`w${i}`, label, "", resp, "Warranty and support commitment")),
		experience: {
			text: "Provide at least 2 comparable contracts completed within the last 5 years.",
			rows: [["Kenyatta National Hospital", "180 business laptops", "30 Nov 2026"], ["Kenya Medical Training College", "220 business laptops", "15 Mar 2027"]].map(([customer, supply, completed], i) => ({ ...row(`x${i}`, `Contract ${i + 1}`, "", "", `contract-${i + 1}.pdf`), customer, supply, completed })),
		},
		acceptance: [],
		evidence: EVIDENCE.map((label, i) => ({ ...row(`ev${i}`, label, "", "", `${label.toLowerCase().replace(/ /g, "-")}.pdf`), file: `${label.toLowerCase().replace(/ /g, "-")}.pdf`, file_status: attention && i === 1 ? "Rejected" : "Accepted", file_tone: attention && i === 1 ? "critical" : "live" })),
		footer: { save_label: "Save and continue", next_href: `/tenders/${REF}/bid/price` },
		next_step: attention
			? { ...guided.next_step, kind: "your_turn_blocked", label: "Your turn, blocked", headline: "Replace the rejected product datasheet before submitting.", blockers: [{ reason_code: "BDS_EVIDENCE_REJECTED", message: "", headline: "", figures: {}, facts: [], fixes: [{ fix_id: "fix_item", label: "Fix item", responsibility: "Supplier user", person: "", kind: "focus", target: "ev1", primary: true }] }], fixes: [] }
			: guided.next_step,
		journey: guided.journey,
	};
}

const VARIANTS = [["BDS-DES-09", ""], ["BDS-DES-09 response drawer", ""], ["BDS-DES-09-ATTENTION", "ATTENTION"], ["BDS-DES-09-ADDENDUM", "ADDENDUM"]];

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	VARIANTS.map(([variant, key]) => ({ name: "RequirementsTaskScreen", variant, frame, component: RequirementsTaskScreen, props: { initial: requirementsTask(key), reference: REF }, path: `/tenders/${REF}/bid/requirements` })),
);
