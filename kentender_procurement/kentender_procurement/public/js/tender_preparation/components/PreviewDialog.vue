<!-- §14 "Preview always renders from the server's current canonical
     projection; browser HTML is never authoritative": the server's HTML in
     a sandboxed frame, with its digest. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tpr-preview-dialog" @keydown.esc="$emit('close')">
		<div class="kt-dialog tpr-preview-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">{{ preview.output === "invitation" ? "Invitation preview" : "Complete Tender preview" }}</div>
			<p class="tpr-muted" style="margin: 0 0 8px">Rendered by the server from the current canonical projection · digest {{ shortDigest(preview.digest) }}</p>
			<div v-if="loading" class="kt-skel" style="height: 40vh"></div>
			<iframe v-else class="tpr-preview-frame" sandbox="" :srcdoc="preview.html" title="Tender preview"></iframe>
			<div class="kt-dialog-actions"><button type="button" class="kt-btn kt-btn-secondary" @click="$emit('close')">Close</button></div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";
import { shortDigest } from "../data/format.js";

defineProps({ preview: { type: Object, default: () => ({}) }, loading: Boolean });
defineEmits(["close"]);
const dialogEl = ref(null);
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
