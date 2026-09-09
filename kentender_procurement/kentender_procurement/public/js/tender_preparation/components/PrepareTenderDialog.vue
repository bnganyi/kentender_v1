<!-- TPR-DES-02 Start Tender (§13.4): "Prepare IT-equipment Tender" over the
     dimmed workspace, 560 px per the artboard. Read-only Requisition,
     requirement, package counts, method, template version and PPRA Goods
     STD source; the fixed notice; Cancel / Prepare Tender. No template,
     package, schema, manifest or configuration control. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tpr-start-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog tpr-start-dialog kt-blueprint" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-dialog-title">Prepare IT-equipment Tender</div>
			<div v-if="loading" class="tpr-dialog-body"><div class="kt-skel" style="width: 60%"></div><div class="kt-skel" style="width: 80%"></div></div>
			<div v-else-if="detail.outcome && detail.outcome !== 'OK'" class="tpr-dialog-body" data-testid="tpr-start-blocked">
				<p class="tpr-card-body">{{ detail.message }}</p>
				<a v-if="detail.outcome === 'HANDOFF_CONSUMED' && detail.can_view" href="#" class="tpr-inline-link" @click.prevent="$emit('navigate', ['tender-preparation', detail.tender])">View Tender</a>
			</div>
			<div v-else class="tpr-dialog-body">
				<div class="tpr-ro-field"><span class="kt-label">Requisition</span><span class="tpr-ro-val">{{ detail.requisition_reference }} — Authorised · Version 1</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Requirement</span><span class="tpr-ro-val">{{ detail.requirement_title }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Package</span><span class="tpr-ro-val">{{ packageLine }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Method</span><span class="tpr-ro-val">{{ detail.planned_method }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Template</span><span class="tpr-ro-val">{{ (detail.template || {}).label }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Official source</span><span class="tpr-ro-val">{{ (detail.template || {}).official_source }}</span></div>
				<p class="tpr-muted" style="font-size: 12px; margin: 0">{{ detail.notice }}</p>
				<p v-if="error" class="tpr-field-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button v-if="detail.outcome === 'OK'" type="button" class="kt-btn kt-btn-primary" :disabled="pending || !detail.can_prepare" data-testid="tpr-start-confirm" @click="$emit('prepare', detail.handoff)">Prepare Tender</button>
				<button v-else-if="!loading" type="button" class="kt-btn kt-btn-primary" @click="$emit('cancel')">Return to workspace</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";

const props = defineProps({ detail: { type: Object, default: () => ({}) }, loading: Boolean, pending: Boolean, error: { type: String, default: "" } });
defineEmits(["cancel", "prepare", "navigate"]);
const dialogEl = ref(null);
const packageLine = computed(() => {
	const c = props.detail.counts || {};
	const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
	return `${plural(c.items || 0, "item")} · ${plural(c.related_services || 0, "related service")} · ${plural(c.acceptance_requirements || 0, "acceptance requirement")}`;
});
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
