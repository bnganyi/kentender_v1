import { ref, onMounted, onUnmounted, onActivated, onDeactivated } from "vue";

// Thin adapter over kentender_core.desk_page.useRoute (AGENTS.md §6.4); the
// Tender-reference filter lives in the URL fragment so refresh and Back keep it.
export function useRouteState(pageSlug) {
	return kentender_core.desk_page.useRoute({ ref, onMounted, onUnmounted, onActivated, onDeactivated }, pageSlug, { hash: true });
}
