// Route-fragment state (filters, selected section, open disclosures) so
// refresh and browser Back preserve them (STD-TPL-001 v0.10 §11.4). Read and
// written only through core's useRoute({ hash: true }) — never a page-owned
// hashchange listener (AGENTS.md §6.4).
export function parseHash(hash) {
	const out = {};
	String(hash || "")
		.split("&")
		.filter(Boolean)
		.forEach((pair) => {
			const [k, v = ""] = pair.split("=");
			try {
				out[decodeURIComponent(k)] = decodeURIComponent(v);
			} catch (e) {
				out[k] = v;
			}
		});
	return out;
}

export function buildHash(state) {
	return Object.keys(state)
		.filter((k) => state[k] !== "" && state[k] !== undefined && state[k] !== null && state[k] !== false)
		.sort()
		.map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(state[k] === true ? "1" : state[k])}`)
		.join("&");
}
