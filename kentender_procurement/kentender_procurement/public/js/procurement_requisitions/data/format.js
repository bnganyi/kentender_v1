// Shared display formatting for Procurement Requisitions screens. Every
// fixture value in REQ-CHG-001 v1.6 §13 is written to two decimal places
// ("KES 50,000,000.00") — the same rule `read.py::_money()` already applies
// server-side; this is the client-side mirror for values a screen formats
// itself (e.g. a per-row amount not already pre-formatted by the server).
export function formatMoney(amount) {
	const value = Number(amount) || 0;
	return `KES ${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Every fixture date in REQ-CHG-001 v1.6 §13 is written "30 Sep 2027" — a
// fixed three-letter month abbreviation. `Date.toLocaleDateString`'s
// "short" month is ICU-data-dependent and can render "Sept" instead
// (confirmed on this bench's Node/ICU version), so the abbreviation is
// spelled out here rather than left to the runtime's own locale data.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatDate(value) {
	if (!value) return "";
	const d = new Date(value);
	if (Number.isNaN(d.getTime())) return value;
	return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}
