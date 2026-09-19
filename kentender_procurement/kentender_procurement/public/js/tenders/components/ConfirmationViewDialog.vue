<!-- "View confirmation" (TPR-DES-08/09): the recorded confirmation facts —
     channel, available at, reference, URL, evidence file (name, format,
     verification), notes, attestation text and who attested when. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tnd-confirmation-view" @keydown.esc="$emit('close')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog" role="dialog" aria-modal="true" aria-labelledby="tnd-cv-title" tabindex="-1">
			<div id="tnd-cv-title" class="kt-dialog-title">{{ row.channel_label }} confirmation</div>
			<div class="tnd-dialog-body">
				<div class="tnd-grid-2" style="gap: 12px">
					<div class="tnd-fact"><div class="kt-label">Result</div><div class="tnd-fact-value"><span class="kt-status is-live">{{ row.result_label }}</span></div></div>
					<div class="tnd-fact"><div class="kt-label">Available at</div><div class="tnd-fact-value">{{ row.available_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Publication reference</div><div class="tnd-fact-value">{{ row.evidence_reference }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Public URL</div><div class="tnd-fact-value"><a v-if="row.public_url" :href="row.public_url" target="_blank" rel="noopener">{{ row.public_url }}</a><span v-else>{{ row.url_not_applicable_reason || "—" }}</span></div></div>
					<div class="tnd-fact"><div class="kt-label">Evidence file</div><div class="tnd-fact-value"><a v-if="row.evidence_file_url" :href="row.evidence_file_url" target="_blank" rel="noopener" data-testid="tnd-cv-file">{{ row.evidence_file_name }}</a><span v-else>{{ row.evidence_file_name || "—" }}</span><div class="tnd-sub">{{ row.evidence_check_result }}</div></div></div>
					<div class="tnd-fact"><div class="kt-label">Attested by</div><div class="tnd-fact-value">{{ row.attested_by_name }}<div class="tnd-sub">{{ row.attested_at_label }}</div></div></div>
				</div>
				<p v-if="row.evidence_notes" class="tnd-small tnd-muted-700" style="margin: 12px 0 0">{{ row.evidence_notes }}</p>
				<p class="tnd-xs tnd-muted" style="margin: 12px 0 0">{{ row.attestation_text }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-primary" data-testid="tnd-cv-close" @click="$emit('close')">Close</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

defineProps({ row: { type: Object, required: true } });
defineEmits(["close"]);
const dialogEl = ref(null);
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
