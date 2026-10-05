// The bench runtime supplies window.__ (translation) and window.frappe; the Analytics components use them,
// so the test environment defines the same globals. The chart components are plain props-in components with
// no route and no server call, so nothing more is needed (the page, when built, adds its own mocks).
globalThis.__ = (text, args) =>
	String(text).replace(/\{(\d+)\}/g, (_, index) => (args ? String(args[Number(index)]) : ""));
globalThis.frappe = { set_route: () => {}, route_options: null };
if (!globalThis.CSS) globalThis.CSS = {};
if (!globalThis.CSS.escape) globalThis.CSS.escape = (value) => String(value).replace(/([^\w-])/g, "\\$1");
