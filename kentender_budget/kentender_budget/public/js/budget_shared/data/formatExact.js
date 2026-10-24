// Exact money from the server, as text. The Budget never rounds money for display: a server amount arrives as a
// decimal string ("500000.00") and is grouped here without a floating-point step, so a figure with cents keeps them
// and a whole figure drops a ".00" it does not need (BUD-CHG-001 v1.16 §11.22 shows "KES 500,000").
export function formatExact(text, currency) {
	if (text === null || text === undefined || text === "") return "";
	const value = String(text).trim();
	const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value);
	if (!match) return `${currency || "KES"} ${value}`;
	const [, sign, whole, fraction = ""] = match;
	const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	const decimals = /^0*$/.test(fraction) ? "" : `.${fraction}`;
	return `${sign ? "−" : ""}${currency || "KES"} ${grouped}${decimals}`;
}

// The sum of exact money strings, in minor units, so a total never drifts: "300000.00" + "199999.99" is "499999.99".
export function sumExact(values, scale = 2) {
	const factor = 10 ** scale;
	const minor = values.reduce((total, v) => total + toMinor(v, scale), 0);
	return fromMinor(minor, factor, scale);
}

export function toMinor(text, scale = 2) {
	const match = /^(-?)(\d*)(?:\.(\d*))?$/.exec(String(text ?? "").trim());
	if (!match || (match[2] === "" && !match[3])) return 0;
	const [, sign, whole = "", fraction = ""] = match;
	const padded = (fraction + "0".repeat(scale)).slice(0, scale);
	const minor = parseInt(whole || "0", 10) * 10 ** scale + parseInt(padded || "0", 10);
	return sign ? -minor : minor;
}

export function fromMinor(minor, factor, scale = 2) {
	const negative = minor < 0;
	const abs = Math.abs(minor);
	const whole = Math.floor(abs / factor);
	const fraction = String(abs % factor).padStart(scale, "0");
	return `${negative ? "-" : ""}${whole}.${fraction}`;
}
