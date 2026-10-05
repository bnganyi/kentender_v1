import { ref, onMounted, onUnmounted, onActivated, onDeactivated } from "vue";

const PAGE_SLUG = "home";

// Home keeps nothing in the URL (no record id, tab or filter), so there is no route
// to read. The adapter exists for the one thing the page runtime gives a live app:
// `epoch` ticks when the page is shown again on the same route, and Home revalidates
// in place then (AGENTS.md §6.1, §6.4) so work done elsewhere is not shown stale.
export function useRouteState() {
	const { epoch } = kentender_core.desk_page.useRoute(
		{ ref, onMounted, onUnmounted, onActivated, onDeactivated },
		PAGE_SLUG
	);
	return { epoch };
}
