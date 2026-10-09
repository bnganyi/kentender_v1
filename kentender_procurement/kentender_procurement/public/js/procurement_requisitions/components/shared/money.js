// Reading aid for KES amounts typed into the Estimated total cost field (REQ v1.15).
//
// Formatting is display only and never changes the amount: it works on the digits as text (no
// floating point), adds thousands separators and two decimals, and refuses to touch anything it
// cannot show exactly — three decimals ("1.005"), letters, a second point — so the server's own
// refusal (excess decimals are never rounded) still reads true against what is on screen.
// The comma-free text is always what is compared and saved.

const EXACT = /^\d+(\.\d{0,2})?$/;

export function plainMoneyText(raw) {
	return String(raw === undefined || raw === null ? "" : raw).replace(/[,\s]/g, "");
}

export function formatMoneyText(raw) {
	const text = plainMoneyText(raw);
	if (!text || !EXACT.test(text)) return String(raw === undefined || raw === null ? "" : raw);
	const [whole, fraction = ""] = text.split(".");
	const grouped = whole.replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	return `${grouped}.${fraction.padEnd(2, "0")}`;
}
