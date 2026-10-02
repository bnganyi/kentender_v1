<script setup>
// The evidence column of a requirements table: how many files a row holds, as a
// paperclip and a number, with the names only in a hover. File names have no
// fixed length and say little, so they never reach the table's layout. A refused
// file reads as Rejected, beside the count when the row holds others; a row
// with none is a dash.
defineProps({
	count: { type: Number, default: 0 },
	names: { type: Array, default: () => [] },
	rejected: { type: Boolean, default: false },
});
</script>

<template>
	<span v-if="count > 0" class="bds-attachments" data-testid="bds-attachments" :title="names.join(', ')">
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
		<span class="bds-attachment-count">{{ count }}</span>
		<span class="bds-sr-only">{{ __(count === 1 ? "file attached" : "files attached") }}</span>
	</span>
	<span v-if="rejected" class="kt-status is-critical">{{ __("Rejected") }}</span>
	<template v-else-if="count <= 0">—</template>
</template>
