import { ref, onMounted, onUnmounted, onActivated, onDeactivated } from "vue";

// Thin adapter over kentender_core.desk_page.useRoute for this bundle's own Vue
// runtime (AGENTS.md §6.6). The app lives on the "tenders" page.
export function useRouteState(pageSlug) {
	return kentender_core.desk_page.useRoute({ ref, onMounted, onUnmounted, onActivated, onDeactivated }, pageSlug);
}
