// Client-side mirrors of the server's own display rules (serializer.fmt_*):
// used only for values a screen formats itself; every server projection is
// already labelled.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatMoney(amount) {
	const value = Number(amount) || 0;
	return `KES ${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatDate(value) {
	if (!value) return "";
	const d = new Date(String(value).replace(" ", "T"));
	if (Number.isNaN(d.getTime())) return String(value);
	return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

// Site time is EAT (UTC+3); the server stores naive site-local instants and
// labels them itself. Local input values keep the server's own text form.
export function toInputDate(value) {
	if (!value) return "";
	return String(value).slice(0, 10);
}

export function toInputDateTime(value) {
	if (!value) return "";
	const text = String(value).replace(" ", "T");
	return text.length >= 16 ? text.slice(0, 16) : text;
}

export function fromInputDateTime(value) {
	if (!value) return "";
	return `${String(value).replace("T", " ")}${String(value).length === 16 ? ":00" : ""}`;
}

export function pad(n) {
	return String(n).padStart(2, "0");
}

export function fileSize(bytes) {
	const n = Number(bytes) || 0;
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
	return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}
