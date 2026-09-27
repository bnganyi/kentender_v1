<script setup>
// BDS-CHG-001 v0.8 §10.5 People › View: one person's assignment as the
// Account read states it. Assignments are immutable, so there is nothing to
// edit here; a change is a new assignment (Add person).
import { nextTick, onMounted, ref } from "vue";

defineProps({ person: { type: Object, required: true } });
const emit = defineEmits(["close"]);
const close = ref(null);
onMounted(() => nextTick(() => close.value && close.value.focus()));
</script>

<template>
	<div class="kt-dialog-backdrop" data-testid="acc-view-person" @keydown.esc.stop="emit('close')">
		<div class="kt-dialog acc-dialog" role="dialog" aria-modal="true" aria-labelledby="acc-view-person-title">
			<div id="acc-view-person-title" class="kt-dialog-title">{{ person.person }}</div>
			<div class="acc-dialog-facts">
				<div class="acc-fact"><span class="kt-label">{{ __("Responsibility") }}</span><span>{{ person.responsibility }}</span></div>
				<div class="acc-fact"><span class="kt-label">{{ __("Job title") }}</span><span>{{ person.job_title || "—" }}</span></div>
				<div class="acc-fact"><span class="kt-label">{{ __("Effective period") }}</span><span>{{ person.effective_period }}</span></div>
				<div class="acc-fact"><span class="kt-label">{{ __("Status") }}</span><span>{{ person.active ? __("In effect") : __("Not yet in effect") }}</span></div>
			</div>
			<div class="kt-dialog-actions">
				<button ref="close" type="button" class="kt-btn kt-btn-secondary" @click="emit('close')">{{ __("Close") }}</button>
			</div>
		</div>
	</div>
</template>
