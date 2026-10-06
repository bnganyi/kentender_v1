// The bench runtime supplies window.__ (translation), window.frappe and kentender_core.desk_page;
// the SFCs and composables use all three, so the test environment defines the same globals.
import { ref } from "vue";

globalThis.__ = (text, args) =>
	String(text).replace(/\{(\d+)\}/g, (_, index) => (args ? String(args[Number(index)]) : ""));
globalThis.frappe = { set_route: () => {}, route_options: null };
// `epoch` ticks when the page is shown again on the same route; a test bumps it.
globalThis.__homeEpoch = ref(0);
globalThis.kentender_core = {
	desk_page: { useRoute: () => ({ route: ref(["home"]), epoch: globalThis.__homeEpoch }) },
};
if (!globalThis.CSS) globalThis.CSS = {};
if (!globalThis.CSS.escape) globalThis.CSS.escape = (value) => String(value).replace(/([^\w-])/g, "\\$1");
