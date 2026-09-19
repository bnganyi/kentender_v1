<!-- TPR-DES-05/06/07 finding notices: every Must fix as a critical notice
     with its route link, then the Review notes as one attention notice
     ("N review note(s)." + messages + link). Copy and routes come from the
     server's review result; the client adds nothing. -->
<template>
	<div v-if="mustFix.length || notes.length">
		<div v-for="f in mustFix" :key="f.finding_code + f.field" class="tnd-section--notice tnd-section" data-testid="tnd-must-fix">
			<div class="kt-notice is-critical">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
				<div class="kt-notice-body"><strong>{{ f.message }}</strong> <button v-if="linkable && f.link_label" type="button" class="tnd-link-btn" @click="$emit('go', f)">{{ f.link_label }}</button></div>
			</div>
		</div>
		<div v-if="notes.length" class="tnd-section--notice tnd-section" data-testid="tnd-review-notes">
			<div class="kt-notice is-attention">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
				<div class="kt-notice-body"><strong>{{ notes.length }} review note{{ notes.length === 1 ? "" : "s" }}.</strong> {{ notes.map((n) => n.message).join(" ") }} <button v-if="linkable && notes[0].link_label" type="button" class="tnd-link-btn" @click="$emit('go', notes[0])">{{ notes[0].link_label }}</button></div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	review: { type: Object, default: () => ({}) },
	linkable: { type: Boolean, default: true },
});
defineEmits(["go"]);
const mustFix = computed(() => props.review.must_fix || []);
const notes = computed(() => props.review.review_notes || []);
</script>
