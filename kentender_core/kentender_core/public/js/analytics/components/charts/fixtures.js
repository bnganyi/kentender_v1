// The A1 fixture's chart values as the server sends them (ANL §10A.3 to §10A.7, §10A.9): every label, count,
// value text, tick and caption below is the brief's own wording. Used by the component specs, and a template
// for the page builder's payloads.

export const TENDER_STAGES = [
	{ key: "preparation", label: "Tender preparation and publication", count: 1, valueText: "KES 6,500,000", tone: "cat-1" },
	{ key: "open", label: "Open for bids", count: 1, valueText: "KES 8,000,000", tone: "cat-2" },
	{ key: "evaluation", label: "Evaluation", count: 1, valueText: "KES 3,500,000", tone: "cat-3" },
	{ key: "award", label: "Award", count: 2, valueText: "KES 12,500,000", tone: "cat-4" },
	{ key: "closed", label: "Closed", count: 1, valueText: "KES 25,000,000", tone: "cat-5" },
];

export const REQUISITION_STATES = [
	{ key: "submitted", label: "Submitted to Procurement", count: 1, valueText: "KES 12,000,000 requested", tone: "cat-3" },
	{ key: "authorised", label: "Authorised", count: 6, valueText: "KES 55,500,000 authorised", tone: "cat-1" },
];

export const TENDER_STRIP = [
	{ key: "preparation", label: "Preparation", count: 1, tone: "cat-1" },
	{ key: "open", label: "Open", count: 1, tone: "cat-2" },
	{ key: "evaluation", label: "Evaluation", count: 1, tone: "cat-3" },
	{ key: "award", label: "Award", count: 2, tone: "cat-4" },
	{ key: "closed", label: "Closed", count: 1, tone: "cat-5" },
];

export const PLAN_COVERAGE = [
	{ key: "covered", label: "Covered by authorised requisitions", count: 55500000, text: "KES 55,500,000", tone: "pair-strong" },
	{ key: "uncovered", label: "Not yet covered", count: 13000000, text: "KES 13,000,000", tone: "pair-tint" },
];

export const FUNDING = [
	{ key: "reserved", label: "Reserved for requisitions", count: 55500000, text: "KES 55,500,000", tone: "family-1" },
	{ key: "committed", label: "Committed to contracts", count: 0, text: "KES 0", tone: "family-2" },
	{ key: "available", label: "Available to reserve", count: 94500000, text: "KES 94,500,000", tone: "family-3" },
];

export const WAITING_LEGEND = [
	{ key: "b1", label: "0–7 days", tone: "seq-1" },
	{ key: "b2", label: "8–30 days", tone: "seq-2" },
	{ key: "b3", label: "31–90 days", tone: "seq-3" },
	{ key: "b4", label: "Over 90 days", tone: "seq-4" },
];

export const WAITING_ROWS = [
	{ key: "requisitions", label: "Requisitions", segments: [{ key: "b1", label: "0–7 days", count: 1, tone: "seq-1" }] },
	{
		key: "tenders",
		label: "Tender proceedings",
		segments: [
			{ key: "b1", label: "0–7 days", count: 3, tone: "seq-1" },
			{ key: "b2", label: "8–30 days", count: 1, tone: "seq-2" },
		],
	},
];

export const PLAN_ITEMS = [
	{ key: "servers", label: "Servers", segments: [{ key: "c", label: "Covered", count: 25000, text: "KES 25,000,000", tone: "pair-strong" }] },
	{ key: "clinic", label: "Clinic equipment", segments: [{ key: "n", label: "Not yet covered", count: 12000, text: "KES 12,000,000", tone: "pair-tint", muted: true }] },
	{
		key: "switches",
		label: "Network switches",
		segments: [
			{ key: "c", label: "Covered", count: 8000, text: "KES 8,000,000", tone: "pair-strong" },
			{ key: "n", label: "Not yet covered", count: 1000, text: "KES 1,000,000", tone: "pair-tint", muted: true },
		],
	},
	{ key: "monitors", label: "Monitors", segments: [{ key: "c", label: "Covered", count: 7500, text: "KES 7,500,000", tone: "pair-strong" }] },
	{ key: "peripherals", label: "IT peripherals", segments: [{ key: "c", label: "Covered", count: 6500, text: "KES 6,500,000", tone: "pair-strong" }] },
	{ key: "printers", label: "Printers", segments: [{ key: "c", label: "Covered", count: 5000, text: "KES 5,000,000", tone: "pair-strong" }] },
	{ key: "desks", label: "Office desks", segments: [{ key: "c", label: "Covered", count: 3500, text: "KES 3,500,000", tone: "pair-strong" }] },
];

export const PLAN_LEGEND = [
	{ key: "c", label: "Covered", tone: "pair-strong" },
	{ key: "n", label: "Not yet covered", tone: "pair-tint" },
];

export const DEPARTMENTS = [
	{
		key: "dh",
		label: "Digital Health",
		endLabel: "74%",
		segments: [
			{ key: "c", label: "Covered", count: 34000, text: "KES 34,000,000", tone: "pair-strong" },
			{ key: "n", label: "Not yet covered", count: 12000, text: "KES 12,000,000", tone: "pair-tint", muted: true },
		],
	},
	{
		key: "hrmd",
		label: "Human Resources Management and Development",
		endLabel: "96%",
		segments: [
			{ key: "c", label: "Covered", count: 21500, text: "KES 21,500,000", tone: "pair-strong" },
			{ key: "n", label: "Not yet covered", count: 1000, text: "KES 1,000,000", tone: "pair-tint", muted: true },
		],
	},
];

const MONTHS = [
	["2026-07", "Jul 2026", ["Jul", "2026"]],
	["2026-08", "Aug 2026", ["Aug"]],
	["2026-09", "Sep 2026", ["Sep"]],
	["2026-10", "Oct 2026", ["Oct"]],
	["2026-11", "Nov 2026", ["Nov"]],
	["2026-12", "Dec 2026", ["Dec"]],
	["2027-01", "Jan 2027", ["Jan", "2027"]],
	["2027-02", "Feb 2027", ["Feb"]],
	["2027-03", "Mar 2027", ["Mar"]],
	["2027-04", "Apr 2027", ["Apr"]],
	["2027-05", "May 2027", ["May"]],
	["2027-06", "Jun 2027 (to date)", ["Jun", "(to date)"]],
];

/** The twelve month slots, with `values` keyed by month key: { "2027-04": { published: 4 } }. */
export function monthSlots(values = {}) {
	return MONTHS.map(([key, label, axisLines]) => ({ key, label, axisLines, values: values[key] || {} }));
}

export const TENDER_MONTH_SERIES = [
	{ key: "published", label: "Published", tone: "cat-1" },
	{ key: "cancelled", label: "Cancelled", tone: "cat-5" },
	{ key: "awarded", label: "AO award decisions", tone: "cat-4" },
];
export const TENDER_MONTH_VALUES = {
	"2027-04": { published: 4 },
	"2027-05": { published: 1 },
	"2027-06": { cancelled: 1, awarded: 1 },
};

export const RANGE_COLUMNS = ["Step", "", "Completed", "Median", "Shortest", "Longest"];
export const RANGE_AXIS = {
	max: 60,
	ticks: [0, 10, 20, 30, 40, 50, 60].map((value) => ({ value, label: String(value) })),
};
const span = (key, label, completed, median, shortest, longest) => ({
	key,
	label,
	completed: String(completed),
	median: { value: median[0], text: median[1] },
	shortest: { value: shortest[0], text: shortest[1] },
	longest: { value: longest[0], text: longest[1] },
});
export const RANGE_ROWS = [
	span("t1", "Requisition submitted to authorised", 6, [8.5, "8.5 days"], [6, "6 days"], [14, "14 days"]),
	span("t2", "Requisition authorised to Tender started", 6, [3.5, "3.5 days"], [1, "1 day"], [5, "5 days"]),
	span("t3", "Tender started to published", 5, [26, "26 days"], [21, "21 days"], [56, "56 days"]),
	span("t4", "Bid opening complete to evaluation report sent", 2, [32.5, "32.5 days"], [28, "28 days"], [37, "37 days"]),
	span("t5", "Evaluation report sent to AO decision recorded", 1, [13, "13 days"], [13, "13 days"], [13, "13 days"]),
];

export const INVITATION_TIMING = [
	{ key: "switches", label: "Network switches", value: 25, text: "25 days after approved date" },
	{ key: "desks", label: "Office desks", value: 7, text: "7 days after approved date" },
	{ key: "servers", label: "Servers", value: 7, text: "7 days after approved date" },
	{ key: "monitors", label: "Monitors", value: 0, text: "On the approved date" },
	{ key: "printers", label: "Printers", value: -3, text: "3 days before approved date" },
	{ key: "peripherals", label: "IT peripherals", value: null, text: "No date recorded" },
];
