// System setup's route state (AGENTS.md §6.4): the one place the page reads
// its URL. Listening, pausing while the page is hidden and resuming live in
// kentender_core.desk_page.useRoute; this maps the fragment onto the
// CFG-CHG-002 v0.14 §9 link grammar (data/routes.js).
import { computed, inject, onActivated, onDeactivated, onMounted, onUnmounted, provide, ref, watch } from "vue";
import { buildSetupHash, parseSetupHash } from "../data/routes.js";

const PAGE_SLUG = "system-setup";
const EPOCH_KEY = Symbol("system-setup-epoch");

/** For the root only: the parsed route, navigation, and the resume epoch
 *  the tabs revalidate on. */
export function useRouteState() {
	const { hash, goHash, epoch, isShown } = kentender_core.desk_page.useRoute(
		{ ref, onMounted, onUnmounted, onActivated, onDeactivated },
		PAGE_SLUG,
		{ hash: true }
	);
	const state = computed(() => parseSetupHash(hash.value));
	provide(EPOCH_KEY, epoch);

	/** Navigate to a §9 route object; `replace` for corrections that must not
	 *  add a Back step (a defaulted or refused tab). */
	function go(route, { replace = false } = {}) {
		goHash(buildSetupHash(route), { replace });
	}

	return { state, go, epoch, isShown };
}

/**
 * For a tab that loads its own data: re-read quietly (in place, no skeleton)
 * when the page resumes on the same route or the kept-alive tab is shown
 * again — never on first mount, which the tab's own load already covers.
 */
export function onSetupRevalidate(reload) {
	const epoch = inject(EPOCH_KEY, null);
	if (epoch) watch(epoch, () => reload({ quiet: true }));
	let mountedOnce = false;
	onMounted(() => {
		mountedOnce = true;
	});
	let seenActivation = false;
	onActivated(() => {
		// The first activation follows the first mount; only a later one is a
		// return to an already-rendered tab.
		if (seenActivation && mountedOnce) reload({ quiet: true });
		seenActivation = true;
	});
}
