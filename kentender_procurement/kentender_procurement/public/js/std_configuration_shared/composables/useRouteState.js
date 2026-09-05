import { ref, onMounted, onUnmounted, onActivated, onDeactivated } from "vue";

// Thin adapter over kentender_core.desk_page.useRoute — this repo's shared
// esbuild config does not mark "vue" external, so every bundle carries its
// own Vue runtime and core cannot hand this bundle a ref it can track
// (AGENTS.md §6.6). All routing behaviour lives in kentender_core; this file
// only supplies the local Vue primitives.
export function useRouteState(pageSlug) {
	return kentender_core.desk_page.useRoute(
		{ ref, onMounted, onUnmounted, onActivated, onDeactivated },
		pageSlug
	);
}
