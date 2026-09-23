<!-- PLN-CHG-001 v1.24 §10.16 — several C03/C04 panels at once (one purchase
     missing both its method and schedule rule, or several purchases each
     missing one) have no literal board of their own: every drawn C03/C04
     section shows exactly one. Stacking N of them full-size was never that
     board's choice to begin with, and it does not scale — found live 23 Sep
     2026, two panels already read as a wall of amber before a plan with
     several affected purchases could ever reach this screen. A single panel
     stays exactly as C03/C04 draw it; two or more collapse to one summary
     line, open on request, so the page states how many settings are missing
     without drawing all of them by default. -->
<template>
	<template v-if="panels.length <= 1">
		<MissingSettingPanel v-for="(panel, index) in panels" :key="index" :panel="panel" />
	</template>
	<details v-else class="kt-disclosure pln-missing-settings-group" data-testid="pln-missing-settings-group" @toggle="open = $event.target.open">
		<summary class="kt-disclosure-head">
			<div class="kt-disclosure-title-row">
				<span class="kt-disclosure-title">{{ panels.length }} settings need administrator attention</span>
			</div>
			<svg class="kt-disclosure-chevron" :class="{ 'is-open': open }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M6 9l6 6 6-6"></path>
			</svg>
		</summary>
		<div class="kt-disclosure-body pln-missing-settings-body">
			<MissingSettingPanel v-for="(panel, index) in panels" :key="index" :panel="panel" />
		</div>
	</details>
</template>

<script setup>
import { ref } from "vue";
import MissingSettingPanel from "./MissingSettingPanel.vue";

defineProps({
	panels: { type: Array, default: () => [] },
});

const open = ref(false);
</script>
