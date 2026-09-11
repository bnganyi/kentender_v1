// Display helpers for Tender Preparation screens. Server payloads arrive
// pre-formatted where the spec fixes a form ("27 May 2027, 17:00 EAT"); these
// cover the few values a screen formats itself.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatDate(value) {
	if (!value) return "";
	const d = new Date(value);
	if (Number.isNaN(d.getTime())) return value;
	return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

export function shortDigest(hex) {
	if (!hex) return "";
	return `sha256:${hex.slice(0, 4)}…${hex.slice(-4)}`;
}

// Native <input type="date"|"datetime-local"> values <-> the server's
// "YYYY-MM-DD" / "YYYY-MM-DD HH:MM:SS" forms (EAT wall-clock, never converted).
export function toInputDate(value) {
	return value ? String(value).slice(0, 10) : "";
}
export function toInputDateTime(value) {
	if (!value) return "";
	const text = String(value).replace(" ", "T");
	return text.slice(0, 16);
}
export function fromInputDateTime(value) {
	if (!value) return null;
	const text = String(value).replace("T", " ");
	return text.length === 16 ? `${text}:00` : text;
}
