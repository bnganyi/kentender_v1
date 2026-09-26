<!-- TPR-DES-03 "Authorised requisition" drawer (440px, right): the internal
     policy context (§4.3 — internal readers only; the server omits it for
     everyone else) and every authorised requirement in full (§10.4). -->
<template>
	<div>
		<div class="tnd-drawer-backdrop" data-testid="tnd-drawer-backdrop" @click="$emit('close')"></div>
		<div class="tnd-drawer" role="dialog" aria-modal="true" aria-labelledby="tnd-drawer-title" data-testid="tnd-drawer" @keydown.esc="$emit('close')">
			<div class="tnd-drawer-head">
				<h3 id="tnd-drawer-title" class="kt-card-title" style="margin: 0">Authorised requisition</h3>
				<button ref="closeEl" type="button" class="tnd-btn-icon" aria-label="Close" data-testid="tnd-drawer-close" @click="$emit('close')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
			</div>
			<template v-if="internal">
				<h4>Approved purchase and policy context</h4>
				<p class="tnd-xs tnd-muted" style="margin: 0 0 12px">{{ internal.note }}</p>
				<div class="tnd-fact-list" data-testid="tnd-drawer-context">
					<div><span class="kt-label">Plan Item</span> {{ context.plan_item_id }}</div>
					<div><span class="kt-label">Requisition</span> {{ context.requisition_reference }}</div>
					<div><span class="kt-label">Authorised value</span> {{ internal.authorised_value }}</div>
					<div><span class="kt-label">Reservation</span> {{ context.reservation_category }}</div>
					<div><span class="kt-label">Lotting</span> {{ context.lotting }}</div>
					<div><span class="kt-label">Strategic objective</span> {{ internal.strategic_objective }}</div>
					<div><span class="kt-label">Plan horizon</span> {{ internal.plan_horizon }}</div>
					<div><span class="kt-label">Template</span> {{ templateLabel }}</div>
					<div><span class="kt-label">Opening date/time</span> {{ openingLabel }}</div>
				</div>
			</template>
			<h4>Authorised requirements</h4>
			<RequirementTables :tables="inherited.requirement_tables || []" data-testid="tnd-drawer-items" />
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import RequirementTables from "./RequirementTables.vue";

const props = defineProps({
	inherited: { type: Object, default: () => ({}) },
	templateLabel: { type: String, default: "" },
	openingLabel: { type: String, default: "" },
});
defineEmits(["close"]);

const closeEl = ref(null);
const context = computed(() => props.inherited.context || {});
const internal = computed(() => props.inherited.internal || null);
onMounted(() => nextTick(() => closeEl.value && closeEl.value.focus()));
</script>
