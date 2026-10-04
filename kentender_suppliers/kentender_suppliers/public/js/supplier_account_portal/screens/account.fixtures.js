// BDS-CHG-001 v0.8 §10.4–10.5 fixture payloads as the server sends them
// (`GetSupplierAccount` and the `/account/register` first payload, with
// kentender_core's next-step and journey shapes), and the structural-fidelity
// variants for boards BDS-DES-03 and BDS-DES-04 at both frames.
import AccountScreen from "./AccountScreen.vue";
import RegisterScreen from "./RegisterScreen.vue";

const STAGES = [["ACCOUNT_SETUP", "Set up account"], ["CONTACT_VERIFICATION", "Verify email"], ["ACTIVE", "Account ready"]];
const MARKER_LABELS = { done: "Done", current: "Current", blocked: "Blocked", not_started: "Not started" };
const KIND_LABELS = { your_turn: "Your turn", your_turn_blocked: "Your turn, blocked", waiting: "Waiting on someone", done: "Done" };

export function journey(markers, holder = "") {
	const index = markers.findIndex((m) => m === "current" || m === "blocked");
	const at = index >= 0 ? index : markers.length - 1;
	const stages = STAGES.map(([code, label], i) => ({ code, label, marker: markers[i], marker_label: MARKER_LABELS[markers[i]], holder: i === index ? holder : "" }));
	const parts = { prefix: `Stage ${at + 1} of 3: `, label: STAGES[at][1], suffix: index >= 0 && holder ? ` — ${holder}` : "" };
	return { stages, current: STAGES[at][0], reduced_style: "stage_of", reduced: false, reduced_text: parts.prefix + parts.label + parts.suffix, reduced_parts: parts, upstream: null, downstream: null };
}

export function answer(kind, headline, extra = {}) {
	return { kind, label: KIND_LABELS[kind], headline, sentence: "", stage: "", holder: null, since: null, blockers: [], fixes: [], primary_action: "", ...extra };
}

const EDIT_PHONE = { fix_id: "edit_organisation:official_phone", label: "Edit organisation", responsibility: "Supplier user", person: "", kind: "focus", target: "official_phone", primary: true };

export const NEW_ACCOUNT = {
	user: "mary.wanjiku@afyadigital.example",
	user_name: "Mary Wanjiku",
	next_step: answer("your_turn", "Enter the supplier organisation details.", { stage: "ACCOUNT_SETUP", primary_action: "create_account" }),
	journey: journey(["current", "not_started", "not_started"], "Mary Wanjiku"),
};

const ORG = {
	organisation: "ORG-AFYA", legal_name: "Afya Digital Supplies Limited", country: "Kenya", registration_number: "PVT-9X7K2M", tax_identifier: "P051234567X",
	registered_address: "Westlands Business Park, Waiyaki Way, Nairobi", official_email: "tenders@afyadigital.example", official_phone: "+254 709 555 014", account_status: "Active", record_version: 3,
};
const PEOPLE = [
	{ assignment: "ASG-1", person: "David Ouma", responsibility: "Supplier Representative", job_title: "Bid Coordinator", effective_period: "From 18 May 2027", active: true },
	{ assignment: "ASG-2", person: "Mary Wanjiku", responsibility: "Authorised Signatory", job_title: "Managing Director", effective_period: "From 18 May 2027", active: true },
];
const EVIDENCE = [
	{ evidence: "EV-1", label: "Certificate of incorporation", evidence_type: "Certificate of incorporation", reference: "PVT-9X7K2M", valid_until: "—", status: "Available", file_name: "incorporation.pdf" },
	{ evidence: "EV-2", label: "Tax compliance certificate", evidence_type: "Tax compliance certificate", reference: "P051234567X", valid_until: "31 Dec 2027", status: "Available", file_name: "tcc.pdf" },
	{ evidence: "EV-3", label: "Youth reservation evidence", evidence_type: "Reservation evidence", reference: "AGPO-Y-2026-04172", valid_until: "30 Jun 2027", status: "Available", file_name: "agpo.pdf" },
];

const PROFILE_VALUES = {
	business_structure: "Registered company", sole_proprietor_name: "", sole_proprietor_age: "", sole_proprietor_nationality: "", sole_proprietor_country_of_origin: "", sole_proprietor_citizenship: "",
	partners: [], company_type: "Private company", nominal_capital: "5000000.00", issued_capital: "2500000.00",
	directors: [{ name: "Mary Wanjiku", nationality: "Kenyan", citizenship: "Kenyan", shares: "60.00" }, { name: "John Kamau", nationality: "Kenyan", citizenship: "Kenyan", shares: "40.00" }],
	trade_licence_number: "TL-2027-0451", trade_licence_expiry: "2027-12-31", maximum_business_value: "80000000.00", state_owned: "No", year_of_registration: 2014,
};
/** The `business_profile` block of a read: complete by default, or empty with what is missing. */
export function businessProfile(empty = false) {
	if (!empty) return { organisation: ORG.organisation, record_version: 2, values: { ...PROFILE_VALUES, directors: PROFILE_VALUES.directors.map((r) => ({ ...r })) }, missing: [] };
	const values = Object.fromEntries(Object.keys(PROFILE_VALUES).map((k) => [k, ["partners", "directors"].includes(k) ? [] : ""]));
	return { organisation: ORG.organisation, record_version: 0, values, missing: [{ field: "business_structure", text: "Choose the business structure" }] };
}

/** One `GetSupplierAccount` read for a board variant ("", ATTENTION, VERIFY, SUSPENDED). */
export function account(variant = "") {
	const base = {
		outcome: "OK", state: "account", organisations: [{ organisation: ORG.organisation, legal_name: ORG.legal_name }], organisation: { ...ORG }, viewer: { responsibility: "Authorised Signatory" },
		people: PEOPLE.map((p) => ({ ...p })), evidence: EVIDENCE.map((e) => ({ ...e })), notice_contacts: [{ email: ORG.official_email, status: "Verified" }], missing: [],
		allowed_actions: ["edit_organisation", "edit_business_profile", "add_evidence", "add_person"], links: [], status: { label: "Active", tone: "live" }, business_profile: businessProfile(),
		next_step: answer("done", "The supplier account is ready.", { stage: "ACTIVE" }), journey: journey(["done", "done", "done"]),
	};
	if (variant === "ATTENTION") {
		const blocker = { reason_code: "BDS_ACCOUNT_REQUIRED", message: "Enter the official phone number", headline: "Enter the official phone number", figures: {}, fixes: [EDIT_PHONE], facts: [] };
		return {
			...base, organisation: { ...ORG, official_phone: "" }, missing: [{ field: "official_phone", text: "Enter the official phone number" }], status: null,
			next_step: answer("your_turn_blocked", "Add the missing official phone before continuing.", { sentence: "Enter the official phone number.", stage: "ACCOUNT_SETUP", blockers: [blocker], fixes: [EDIT_PHONE], primary_action: "edit_organisation" }),
			journey: journey(["blocked", "not_started", "not_started"], "Mary Wanjiku"),
		};
	}
	if (variant === "VERIFY") {
		const resend = { fix_id: "send_account_verification", label: "Resend verification link", responsibility: "Supplier user", person: "", kind: "command", target: null, primary: true };
		return {
			...base, organisation: { ...ORG, account_status: "Pending verification" }, notice_contacts: [{ email: ORG.official_email, status: "Pending verification" }],
			allowed_actions: ["edit_organisation", "add_evidence", "send_account_verification", "add_person"], status: { label: "Pending verification", tone: "attention" },
			next_step: answer("your_turn", "Verify your email to finish setting up the supplier account.", { sentence: "Verify tenders@afyadigital.example before starting a bid.", stage: "CONTACT_VERIFICATION", fixes: [resend], primary_action: "send_account_verification" }),
			journey: journey(["done", "current", "not_started"], "Mary Wanjiku"),
		};
	}
	if (variant === "SUSPENDED") {
		return {
			...base, organisation: { ...ORG, account_status: "Suspended" }, allowed_actions: ["view_receipts"], status: { label: "Account suspended", tone: "critical" },
			links: [{ key: "view_receipts", label: "View receipts", href: "/account/receipts" }, { key: "supplier_support", label: "Supplier support", href: "mailto:supplier.support@kentender.example" }],
			next_step: answer("waiting", "Supplier Account support officer Amina Yusuf is reviewing suspended access.", { stage: "ACTIVE", holder: { role: "Supplier Account support officer", people: ["Amina Yusuf"], display: "Amina Yusuf (Supplier Account support officer)" }, since: { at: "2027-05-19 08:00:00", display: "19 May 2027, 08:00 EAT" } }),
			journey: journey(["done", "done", "blocked"], "Amina Yusuf (Supplier Account support officer)"),
		};
	}
	return base;
}

/** DES-03-VERIFY is the registration form after Create account: the read that follows it. */
export const REGISTERED = { ok: true, idempotent: false, organisation: "ORG-AFYA", account_status: "Pending verification", record_version: 0, verification_sent_to: "tenders@afyadigital.example" };

export const SCREENS = ["desktop", "narrow"].flatMap((frame) => [
	{ name: "RegisterScreen", variant: "BDS-DES-03", frame, component: RegisterScreen, props: { initial: NEW_ACCOUNT }, path: "/account/register" },
	{ name: "RegisterScreen", variant: "BDS-DES-03-VERIFY", frame, component: RegisterScreen, props: { initial: NEW_ACCOUNT }, path: "/account/register", register: true },
	...["", "-ATTENTION", "-VERIFY", "-SUSPENDED"].map((suffix) => ({ name: "AccountScreen", variant: `BDS-DES-04${suffix}`, frame, component: AccountScreen, props: { initial: account(suffix.slice(1)) }, path: "/account" })),
]);
