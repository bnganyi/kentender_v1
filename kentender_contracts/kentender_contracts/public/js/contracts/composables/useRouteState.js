import { ref, onMounted, onUnmounted, onActivated, onDeactivated } from "vue";

// Thin adapter over kentender_core.desk_page.useRoute for this bundle's own Vue runtime (AGENTS.md §6.6). The app lives on the "contracts" page; a contract is a path segment
// (`/app/contracts/<contract>/<tab>/<subject...>`), so a reload, the browser's Back and Forward and a copied link all land on the same screen.
export function useRouteState(pageSlug) {
	return kentender_core.desk_page.useRoute({ ref, onMounted, onUnmounted, onActivated, onDeactivated }, pageSlug);
}

// ["contracts", "CM-2027-0001", "deliveries", "record-delivery"] -> { contract, tab, subject }
export function parseRoute(route, pageSlug) {
	const rest = (route || []).slice(route && route[0] === pageSlug ? 1 : 0).map((s) => decodeURIComponent(String(s)));
	return { contract: rest[0] || "", tab: rest[1] || "", subject: rest.slice(2) };
}
