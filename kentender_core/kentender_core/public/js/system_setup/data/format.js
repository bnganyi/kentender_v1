// Display helpers shared by the System setup tabs (KT-STD-001 §2.2: dates as
// "1 Jul 2027"; blanks as an em dash, never an empty cell).
export function fmtDate(iso) {
	if (!iso) return "—";
	const date = new Date(String(iso).slice(0, 10) + "T00:00:00");
	if (Number.isNaN(date.getTime())) return String(iso);
	return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function fmtDays(value) {
	return value === null || value === undefined || value === "" ? "—" : String(value);
}

export function dash(value) {
	return value === null || value === undefined || value === "" ? "—" : String(value);
}
