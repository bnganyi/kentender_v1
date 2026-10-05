// The payload each Home board is mounted on (HOME-CHG-001 v0.6 §10B; design/Home/Home.dc.html).
//
// The boards are illustrative fixtures (HOME §18: "not runtime events or changes to the canonical seed"), so unlike
// Analytics there is no captured server answer for most of them: the canonical seed world does not hold Charles's
// 18 June morning. These payloads are written by hand in the shape `get_home_workspace` returns, with the board's own
// names and counts, and the page makes no phrase of its own (every sentence below is one the server sends; the Python
// suites `test_home_workspace`, `test_home_time` and the owner provider tests prove the server makes them). What this
// file lets the fidelity spec prove is the page's structure; what the Playwright specs prove is the live data.

const dest = (route, route_options = {}) => ({ route, route_options });

function entry(over = {}) {
	return {
		key: "tenders|TND-1|a", owner: "tenders", module: "Tenders", title: "Supply of UPS units", reference: "", action: "Do the thing",
		reason: "", blocked: false, holder: "", fact: "", link: null, sentence: "", destination: dest(["tenders", "TND-1"]), primary: false,
		timing: "", due: "", badge: "", exact: "", ...over,
	};
}

function region(entries, over = {}) {
	return {
		applicable: true, coverage: "complete", count: entries.length, label: "", total: entries.length, next_count: 0,
		entries, shown: entries.length, remaining: 0, paged: false, next_cursor: null, ...over,
	};
}

const NA = () => region([], { applicable: false, coverage: "not_applicable", count: null, total: null });
const ANALYTICS = { allowed: true, label: "Procurement Analytics", see_all: "See all in Procurement Analytics", route: ["analytics"] };

function base(first, line, over = {}) {
	return {
		state: "ready", empty: false, summary_visible: true, providers: { configured: 9, failed: 0 },
		viewer: { greeting: "Good morning", first_name: first, technical: false, responsibilities: { items: [], line } },
		updated: "18 June 2027, 10:00 EAT", analytics: ANALYTICS,
		regions: { my_work: NA(), coming_up: NA(), waiting: NA(), oversight: NA(), completed: NA() },
		...over,
	};
}

const work = (n, title, over = {}) => entry({ key: `w${n}`, title, action: "Do the work", timing: "Received 2 days ago (16 June, 11:00)", primary: n === 1, ...over });
const rail = (key, title, over = {}) => entry({ key, title, action: "Something is outstanding", timing: "Outstanding 2 days (since 16 June, 09:00)", ...over });
const done = (key, title) => entry({ key, title, sentence: "You did it on 16 June 2027, 15:30 EAT." });

// HOME-DES-21 and 21N (the board at 1024 px, Frappe sidebar collapsed), 28C's base
function charles() {
	return base("Charles", "Head of Procurement Function, site-wide", {
		regions: {
			my_work: region([
				work(1, "Clinic equipment requisition", { owner: "requisitions", module: "Requisitions", action: "Authorise requisition" }),
				work(2, "Supply of printers", { owner: "award", module: "Award", reference: "TND-MOH-2027-044", action: "Prepare professional opinion" }),
				work(3, "Supply of monitors", { owner: "award", module: "Award", reference: "TND-MOH-2027-045", action: "Resolve notice delivery", reason: "A required notice is not yet confirmed." }),
			], { label: "actions for you" }),
			coming_up: region([
				entry({ key: "start", owner: "bid_opening", module: "Bid opening", title: "Supply of network switches", reference: "TND-MOH-2027-042", action: "Start opening", badge: "In 7 days", exact: "25 June, 11:00" }),
				entry({ key: "deadline", owner: "evaluation", module: "Evaluation", title: "Supply of office desks", reference: "TND-MOH-2027-043", action: "Evaluation deadline", badge: "In 13 days", exact: "1 July" }),
			], { count: 2 }),
			waiting: region([entry({ key: "wait", title: "Supply of UPS units", action: "Waiting for Amina Hassan to decide publication", holder: "Accounting Officer", timing: "Waiting 2 days (since 16 June, 15:30)" })], { label: "item you're waiting on" }),
			oversight: region([rail("o1", "Supply of office desks", { owner: "evaluation", module: "Evaluation" }), rail("o2", "Supply of IT peripherals")], { label: "records with outstanding matters" }),
			completed: region([done("d1", "Supply of UPS units")], { count: 1 }),
		},
	});
}

// HOME-DES-29 (Amina, Accounting Officer)
function amina() {
	return base("Amina", "Accounting Officer, site-wide", {
		regions: {
			my_work: region([work(1, "Clinic equipment requisition"), work(2, "Supply of printers"), work(3, "Supply of monitors"), work(4, "Supply of desktop computers")], { label: "actions for you" }),
			coming_up: region([entry({ key: "start", owner: "bid_opening", module: "Bid opening", title: "Supply of network switches", action: "Start opening", badge: "In 7 days", exact: "25 June, 11:00" })], { count: 1 }),
			waiting: region([entry({ key: "wait", title: "Supply of hospital beds", action: "Waiting for Charles Mutiso", holder: "Head of Procurement Function", timing: "Waiting 1 day (since 17 June, 10:00)" })], { label: "item you're waiting on" }),
			oversight: region([rail("o1", "Supply of printers"), rail("o2", "Supply of monitors"), rail("o3", "Supply of office desks")], { label: "records with outstanding matters" }),
			completed: region([done("d1", "Supply of monitors")], { count: 1 }),
		},
	});
}

// HOME-DES-22 (Brian)
function brian() {
	return base("Brian", "Procurement Officer, site-wide", {
		regions: {
			my_work: region([work(1, "Supply of hospital beds", { action: "Record cancellation notices and PPRA report" }), work(2, "Supply of clinic peripherals", { action: "Respond to clarification" })], { label: "actions for you" }),
			coming_up: NA(),
			waiting: region([entry({ key: "wait", title: "Supply of field laptops", action: "Waiting for Amina Hassan to consider cancellation", holder: "Accounting Officer", timing: "Waiting 1 day (since 16 June, 14:00)" })], { label: "item you're waiting on" }),
			oversight: NA(),
			completed: region([done("d1", "Supply of desktop computers")], { count: 1 }),
		},
	});
}

// HOME-DES-23 (Amina, nothing pending, one record with a delivered report)
function aminaOversightOnly() {
	return base("Amina", "Accounting Officer, site-wide", {
		viewer: { greeting: "Good afternoon", first_name: "Amina", technical: false, responsibilities: { items: [], line: "Accounting Officer, site-wide" } },
		regions: {
			my_work: region([], { count: 0, total: 0, label: "actions for you" }),
			coming_up: NA(),
			waiting: region([], { count: 0, total: 0, label: "items you're waiting on" }),
			oversight: region([
				rail("o1", "Supply and delivery of business laptops", {
					owner: "award", module: "Award", reference: "TND-MOH-2027-033", action: "Award: awaiting professional opinion by Charles Mutiso",
					timing: "Outstanding today (since 16 June, 14:07)", fact: "Evaluation report delivered 16 June, 14:07",
					link: { label: "View report", destination: dest(["tenders", "TND-MOH-2027-033", "evaluation", "report"]) },
				}),
			], { label: "record with outstanding matters" }),
			completed: NA(),
		},
	});
}

// HOME-DES-24 (Peter, Head of User Department)
function peter() {
	return base("Peter", "Head of User Department, Human Resources Management and Development", {
		regions: {
			my_work: region([work(1, "Digital health workforce certification programme", { owner: "needs", module: "Needs" })], { label: "action for you" }),
			coming_up: NA(),
			waiting: region([], { count: 0, total: 0, label: "items you're waiting on" }),
			oversight: region([rail("o1", "Supply of office desks"), rail("o2", "Supply of IT peripherals")], { label: "records with outstanding matters" }),
			completed: NA(),
		},
	});
}

// HOME-DES-25 (Brian, blocked response)
function brianBlocked() {
	return base("Brian", "Procurement Officer, site-wide", {
		regions: {
			my_work: region([work(1, "Supply of clinic peripherals", { reference: "TND-MOH-2027-040", action: "Respond to clarification", blocked: true, reason: "Issue an addendum before sending this answer.", timing: "" })], { label: "action for you" }),
			coming_up: NA(),
			waiting: region([], { count: 0, total: 0, label: "items you're waiting on" }),
			oversight: NA(),
			completed: NA(),
		},
	});
}

// HOME-DES-26 (Brian, six actions, five shown) and 26B (after Show 1 more)
function brianSix(shown) {
	const rows = [1, 2, 3, 4, 5, 6].map((n) => work(n, `Supply ${n}`));
	const many = shown === 6;
	return base("Brian", "Procurement Officer, site-wide", {
		regions: {
			my_work: region(rows.slice(0, shown), { count: 6, total: 6, label: "actions for you", shown, remaining: 6 - shown, paged: true, next_cursor: many ? null : "CUR1", next_count: many ? 0 : 1 }),
			coming_up: NA(),
			waiting: region([], { count: 0, total: 0, label: "items you're waiting on" }),
			oversight: NA(),
			completed: NA(),
		},
	});
}

// HOME-DES-27 (Daniel, Technical Operator) and 28A (Brian, a successful read with nothing in it)
const technical = () => base("Daniel", "Technical Operator, site-wide", { empty: true, summary_visible: false, viewer: { greeting: "Good morning", first_name: "Daniel", technical: true, responsibilities: { items: [], line: "Technical Operator, site-wide" } } });
const empty = () => base("Brian", "Procurement Officer, site-wide", { empty: true, summary_visible: false });

// HOME-DES-28B (Waiting on others could not be read) and 28C (Coming up could not be read)
function waitingFailed() {
	const data = brian();
	data.regions.waiting = region([], { coverage: "unavailable", count: null, total: null, label: "items you're waiting on" });
	return data;
}
function comingUpFailed() {
	const data = charles();
	data.regions.coming_up = region([], { coverage: "unavailable", count: null, total: null });
	return data;
}

/** Each board's page state: the payload `homeApi.load` answers with, or `pending` for the loading board. */
export const BOARD_STATES = {
	"HOME-DES-21": () => ({ payload: charles() }),
	"HOME-DES-21N": () => ({ payload: charles() }),
	"HOME-DES-29": () => ({ payload: amina() }),
	"HOME-DES-22": () => ({ payload: brian() }),
	"HOME-DES-23": () => ({ payload: aminaOversightOnly() }),
	"HOME-DES-24": () => ({ payload: peter() }),
	"HOME-DES-25": () => ({ payload: brianBlocked() }),
	"HOME-DES-26": () => ({ payload: brianSix(5) }),
	"HOME-DES-26B": () => ({ payload: brianSix(6) }),
	"HOME-DES-27": () => ({ payload: technical() }),
	"HOME-DES-28A": () => ({ payload: empty() }),
	"HOME-DES-28B": () => ({ payload: waitingFailed() }),
	"HOME-DES-28C": () => ({ payload: comingUpFailed() }),
	"HOME-DES-28D": () => ({ payload: base("Brian", "", { state: "failed" }) }),
	"HOME-DES-28E": () => ({ pending: true }),
	"HOME-DES-28F": () => ({ payload: { state: "denied" } }),
};
