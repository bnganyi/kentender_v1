// Display helpers the browser genuinely needs (the server formats every
// business value; these cover controls the user is still editing).
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function dateLabel(iso) {
	const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || "");
	if (!m) return "";
	return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
}

export function money(text) {
	const m = /^(\d+)(?:\.(\d{1,2}))?$/.exec(String(text || "").trim());
	if (!m) return "";
	const whole = m[1].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	return `KES ${whole}.${(m[2] || "").padEnd(2, "0")}`;
}

export function key() {
	return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}
