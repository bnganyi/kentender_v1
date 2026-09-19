<!-- TPR-DES-03 "Authorised requisition" drawer (440px, right): the internal
     policy context (§4.3 — internal readers only; the server omits it for
     everyone else) and the authorised requirements carried in full. -->
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
			<table class="kt-table tnd-xs" data-testid="tnd-drawer-items">
				<thead><tr><th>Item</th><th style="text-align: right">Quantity</th></tr></thead>
				<tbody>
					<tr v-for="item in inherited.items || []" :key="item.requisition_item_id"><td>{{ item.item_name }}</td><td class="is-num">{{ item.quantity }} {{ item.unit }}</td></tr>
				</tbody>
			</table>
			<p class="tnd-xs tnd-muted" style="margin-top: 8px">{{ countsLine }}</p>
			<template v-if="full">
				<h4>Technical requirements</h4>
				<table class="kt-table tnd-xs"><thead><tr><th>Requirement</th><th>Required value</th></tr></thead><tbody><tr v-for="t in inherited.technical_requirements || []" :key="t.technical_requirement_id"><td>{{ t.label }}</td><td>{{ t.required_value }} {{ t.unit }}</td></tr></tbody></table>
				<h4>Warranty and support</h4>
				<div class="tnd-fact-list">
					<div><span class="kt-label">Minimum warranty</span> {{ (inherited.warranty_support || {}).minimum_warranty_months }} months</div>
					<div><span class="kt-label">On-site support</span> {{ (inherited.warranty_support || {}).onsite_support_required ? "Required" : "Not required" }}</div>
					<div><span class="kt-label">Maximum response</span> {{ (inherited.warranty_support || {}).maximum_support_response_hours }} hours</div>
				</div>
				<h4>Acceptance checks</h4>
				<table class="kt-table tnd-xs"><thead><tr><th>Check</th><th>Pass condition</th></tr></thead><tbody><tr v-for="a in inherited.acceptance_requirements || []" :key="a.acceptance_requirement_id"><td>{{ a.check_type }}</td><td>{{ a.pass_condition }}</td></tr></tbody></table>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";

const props = defineProps({
	inherited: { type: Object, default: () => ({}) },
	templateLabel: { type: String, default: "" },
	openingLabel: { type: String, default: "" },
	full: { type: Boolean, default: false },
});
defineEmits(["close"]);

const closeEl = ref(null);
const context = computed(() => props.inherited.context || {});
const internal = computed(() => props.inherited.internal || null);
const countsLine = computed(() => {
	const c = props.inherited.counts || {};
	const warranty = Object.keys(props.inherited.warranty_support || {}).length;
	return `${c.technical_requirements || 0} technical requirements · ${warranty} warranty/support facts · ${c.acceptance_requirements || 0} acceptance checks carried in full.`;
});
onMounted(() => nextTick(() => closeEl.value && closeEl.value.focus()));
</script>
