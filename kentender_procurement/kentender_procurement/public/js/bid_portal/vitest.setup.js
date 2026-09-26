// Bid portal component tests mount screens outside the portal page: `__`
// is the identity translation and matchMedia reports the width each test
// sets, so a test can render the 1440 table or the 390 cards.
globalThis.__ = (text, args) => (args ? String(text).replace(/\{(\d+)\}/g, (_, i) => args[i]) : text);
globalThis.window.__ = globalThis.__;
globalThis.__narrow = false;
globalThis.window.matchMedia = (query) => ({
	matches: query.includes("max-width") ? globalThis.__narrow : false,
	media: query,
	addEventListener() {},
	removeEventListener() {},
});
