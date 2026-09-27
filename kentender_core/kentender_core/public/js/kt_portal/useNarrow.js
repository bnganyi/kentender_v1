// BDS-CHG-001 v0.8 §10.1 / plan D17 — the portal's 390 × 844 frame: at ≤600 px
// the boards draw table rows as labelled cards, so portal screens render that
// structure rather than squeezing the table (no horizontal scroll, nothing hidden).
import { onMounted, onUnmounted, ref } from "vue";

export const NARROW_QUERY = "(max-width: 600px)";

export function useNarrow() {
	const mql = typeof window !== "undefined" && window.matchMedia ? window.matchMedia(NARROW_QUERY) : null;
	const narrow = ref(!!(mql && mql.matches));
	const update = (event) => {
		narrow.value = event.matches;
	};
	onMounted(() => mql && mql.addEventListener && mql.addEventListener("change", update));
	onUnmounted(() => mql && mql.removeEventListener && mql.removeEventListener("change", update));
	return narrow;
}
