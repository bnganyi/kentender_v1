<!-- Preview / View Invitation and complete Tender (§11.3, §11.9): the exact
     rendered document in a wide dialog with its name, format and size and a
     Download control when a stored PDF exists. A preview of an unfrozen
     Draft freezes nothing (the server renders read-only). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tnd-document-dialog" @keydown.esc="$emit('close')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog tnd-dialog--doc" role="dialog" aria-modal="true" aria-labelledby="tnd-doc-title" tabindex="-1">
			<div id="tnd-doc-title" class="kt-dialog-title">{{ title }}</div>
			<div class="tnd-doc-meta">
				<span data-testid="tnd-doc-name">{{ fileName }}</span>
				<span>{{ format }}</span>
				<span v-if="size">{{ size }}</span>
				<span v-if="digest" class="tnd-muted">Reference {{ digest.slice(0, 12) }}</span>
			</div>
			<div v-if="loading" class="tnd-doc-frame"><div class="kt-skel" style="width: 60%"></div></div>
			<div v-else-if="error" class="kt-notice is-critical"><div class="kt-notice-body">{{ error }}</div></div>
			<div v-else class="tnd-doc-frame" data-testid="tnd-doc-frame" v-html="html"></div>
			<div class="kt-dialog-actions">
				<a v-if="downloadUrl" class="kt-btn kt-btn-secondary" :href="downloadUrl" target="_blank" rel="noopener" data-testid="tnd-doc-download">Download</a>
				<button type="button" class="kt-btn kt-btn-primary" data-testid="tnd-doc-close" @click="$emit('close')">Close</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";
import { fileSize } from "../data/format.js";

defineProps({
	title: { type: String, default: "Document" },
	fileName: { type: String, default: "" },
	format: { type: String, default: "HTML" },
	size: { type: String, default: "" },
	digest: { type: String, default: "" },
	html: { type: String, default: "" },
	downloadUrl: { type: String, default: "" },
	loading: Boolean,
	error: { type: String, default: "" },
});
defineEmits(["close"]);
const dialogEl = ref(null);
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
defineExpose({ fileSize });
</script>
