// Display formatting for the Departmental Needs screens.
//
// §12.8: all dates display in Africa/Nairobi while service and audit instants
// remain UTC. Frappe's own formatters already render in the site timezone, so
// they are used rather than a second date library with its own opinion.

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** `31 Aug 2027`, matching every NDS-DES artboard. Empty stays empty.
 *
 * Formatted explicitly rather than through frappe.datetime.str_to_user, which
 * follows the site's date-format preference (dd-mm-yyyy here) and so would
 * render a different string from the one the artboards specify. */
export function formatDate(value) {
	if (!value) return "";
	const [year, month, day] = String(value).slice(0, 10).split("-");
	// Validity, not presence. "not-a-date" also splits into three truthy parts,
	// and a presence-only guard let it through as the literal string
	// "NaN undefined not" — rendered straight into the page, with no error to
	// notice it by (caught by format.spec.js).
	const monthName = MONTHS[Number(month) - 1];
	if (!year || !monthName || !Number.isFinite(Number(day))) return String(value);
	return `${Number(day)} ${monthName} ${year}`;
}

/** `24 Nov 2026, 12:20 EAT` — the artboards' instant format. */
export function formatInstant(value) {
	if (!value) return "";
	const date = formatDate(value);
	const time = String(value).slice(11, 16);
	return time ? `${date}, ${time} EAT` : date;
}

/** `1 programme` / `300 each` — quantity beside its governed unit label. */
export function quantityWithUnit(version) {
	if (!version) return "";
	const quantity = Number(version.indicative_quantity || 0);
	if (!quantity) return "";
	const rounded = Number.isInteger(quantity) ? quantity : quantity;
	const unit = version.unit_label || version.unit || "";
	return `${rounded} ${String(unit).toLowerCase()}`.trim();
}

/** `NDS-MOH-2027-0001 · VERSION 1` — the record kicker. */
export function versionKicker(reference, version, prefix = "") {
	const parts = [];
	if (prefix) parts.push(prefix);
	if (reference) parts.push(reference);
	if (version && version.version_number) parts.push(`VERSION ${version.version_number}`);
	return parts.join(" · ").toUpperCase();
}
