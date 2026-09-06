// Shared harness for the System setup component specs. The SFC templates
// compile `__("…")` into a globalProperties lookup, so every mount supplies
// the translation shim and a minimal frappe object.
export function globalMocks() {
	const __ = (text, args) =>
		String(text).replace(/\{(\d+)\}/g, (_, index) => (args ? String(args[Number(index)]) : ""));
	return {
		mocks: { __, frappe: { set_route: () => {} } },
	};
}
