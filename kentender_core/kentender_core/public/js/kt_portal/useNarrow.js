// BDS-CHG-001 v0.8 §10.1 / plan D17 — the portal's 390 × 844 frame: narrow
// screens draw table rows as labelled cards, as the boards do, rather than
// squeezing the table (no horizontal scroll, nothing hidden). The switch is at
// 800 px so a 1440 screen at 200% zoom (720 px) also gets cards (WCAG 1.4.10;
// the widest register, My bids, needs about 760 px).
import { onMounted, onUnmounted, ref } from "vue";

export const NARROW_QUERY = "(max-width: 800px)";

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
