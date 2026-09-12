// The bench runtime supplies window.__ (translation) and window.frappe; the
// SFCs use both from template scope AND from <script setup> computeds, so the
// test environment defines the same globals.
globalThis.__ = (text, args) =>
	String(text).replace(/\{(\d+)\}/g, (_, index) => (args ? String(args[Number(index)]) : ""));
globalThis.frappe = globalThis.frappe || { set_route: () => {} };
