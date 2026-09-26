<script setup>
// STD-WF-02 Return dialog (§15.17). Same kt-dialog shell as the other STD
// Configuration dialogs — Escape-to-cancel, no category/assignee/due
// date/attachment/optional-note per the spec's own exclusion list.
import { reactive, watch, nextTick, ref } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	saving: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
const emit = defineEmits(["confirm", "cancel"]);

const form = reactive({ correction_required: "" });
const inputEl = ref(null);

watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		form.correction_required = "";
		await nextTick();
		inputEl.value?.focus();
	}
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" @keydown="onKeydown" tabindex="-1">
		<div class="kt-dialog kt-blueprint" style="width: 520px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h2 class="kt-dialog-title">{{ __("Return package for correction?") }}</h2>
			<p class="kt-muted" style="font-size: 14px; margin: 0 0 16px">
				{{ __("The submitted package will remain unchanged. State the exact correction required.") }}
			</p>
			<div class="kt-field" style="margin: 0 0 16px">
				<label for="kt-return-correction">{{ __("Correction required") }}</label>
				<textarea id="kt-return-correction" ref="inputEl" v-model="form.correction_required" class="kt-input" rows="3"></textarea>
			</div>
			<p v-if="error" class="kt-status is-critical" style="display: inline-block">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="saving || !form.correction_required"
					@click="$emit('confirm', form.correction_required)"
				>
					{{ __("Return for correction") }}
				</button>
			</div>
		</div>
	</div>
</template>
