// Shared display formatting for Procurement Planning screens (PLN-CHG-001
// v1.18). The server pre-formats almost every display string itself
// (`_money()`/`_date()`/`_eat()` in `services/plan_read.py` and siblings) —
// these helpers exist only for the values a screen must format itself: a
// live recalculation before save (PLN-DES-09's feasibility check) or an
// interactive input echo, never a re-derivation of a server-supplied
// `*_display` field.

// Every Money value crosses the API boundary as a decimal string
// (`services/money.py`, §4.1) — format it without ever routing it through a
// float first, so a value like "1000000.10" never becomes "1000000.1".
export function formatMoney(amount) {
	const text = String(amount ?? "").trim();
	if (!text) return "KES 0.00";
	const negative = text.startsWith("-");
	const [whole, fraction = ""] = (negative ? text.slice(1) : text).split(".");
	const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	const cents = (fraction + "00").slice(0, 2);
	return `${negative ? "-" : ""}KES ${grouped}.${cents}`;
}

// Every fixture date in this repo's specs is written "30 Sep 2027" — a fixed
// three-letter month abbreviation, spelled out here rather than left to
// `Date.toLocaleDateString`'s ICU-data-dependent "short" month (which can
// render "Sept" — confirmed on this bench's Node/ICU version).
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatDate(value) {
	if (!value) return "";
	const d = new Date(value);
	if (Number.isNaN(d.getTime())) return value;
	return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

// East Africa Time is UTC+3 with no daylight-saving offset — the fixed
// conversion `services/plan_read.py::_eat()` also uses for every governance/
// publication instant.
export function formatEat(value) {
	if (!value) return "";
	const d = new Date(String(value).replace(" ", "T") + (String(value).includes("Z") ? "" : "Z"));
	if (Number.isNaN(d.getTime())) return value;
	const eat = new Date(d.getTime() + 3 * 60 * 60 * 1000);
	const hours = String(eat.getUTCHours()).padStart(2, "0");
	const minutes = String(eat.getUTCMinutes()).padStart(2, "0");
	return `${eat.getUTCDate()} ${MONTHS[eat.getUTCMonth()]} ${eat.getUTCFullYear()}, ${hours}:${minutes} EAT`;
}

// §4.1 quantities carry a governed UOM precision as a decimal string too
// (`services/money.py::quantity_text`) — format without a float round-trip.
export function formatQuantity(value, unit) {
	const text = String(value ?? "").trim();
	if (!text) return unit ? `0 ${unit}` : "0";
	const trimmed = text.replace(/\.0+$/, "").replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
	return unit ? `${trimmed} ${unit}` : trimmed;
}
