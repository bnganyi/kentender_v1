import { ref, onMounted, onUnmounted, onActivated, onDeactivated } from "vue";

// Thin adapter over kentender_core.desk_page.useRoute with the URL fragment
// followed as well (filters, section, open disclosures — STD-TPL-001 v0.10
// §11.4). All routing behaviour lives in kentender_core (AGENTS.md §6.4).
export function useRouteState(pageSlug) {
	return kentender_core.desk_page.useRoute({ ref, onMounted, onUnmounted, onActivated, onDeactivated }, pageSlug, { hash: true });
}
