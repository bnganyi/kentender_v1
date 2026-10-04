<!-- TPR-DES-05/06/07 review note (§10.6 item 2): one attention notice — the
     count, every note's message and, where the viewer can act on it, the
     note's own link. It never blocks a decision and stays separate from the
     §10.17 guidance. -->
<template>
	<div v-if="notes.length" class="tnd-section tnd-section--plain" data-testid="tnd-review-notes">
		<div class="kt-notice is-attention">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
			<div class="kt-notice-body"><strong>{{ notes.length }} review note{{ notes.length === 1 ? "" : "s" }}.</strong> {{ notes.map((n) => n.message).join(" ") }} <button v-if="linkable && notes[0].link_label" type="button" class="tnd-link-btn" data-testid="tnd-review-note-link" @click="$emit('go', notes[0])">{{ notes[0].link_label }}</button></div>
		</div>
	</div>
</template>

<script setup>
defineProps({ notes: { type: Array, default: () => [] }, linkable: { type: Boolean, default: true } });
defineEmits(["go"]);
</script>
