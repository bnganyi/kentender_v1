<!-- NDS-UI-08 intake window (§12.7) — NDS-DES-10. The page exposes only the
     two instants: no manual status command and no approval lifecycle. -->
<template>
	<div style="padding-bottom: 24px">
		<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px">
			<h1 class="kt-record-title">Intake window</h1>
			<StatusPill :label="window.state || 'Not configured'" />
		</div>
		<div class="kt-page-kicker" style="margin-bottom: 6px">
			DEPARTMENTAL NEEDS CONFIGURATION
		</div>
		<p class="kt-page-lede" style="margin: 0 0 24px">
			Set when departments may create and initially submit needs for this Financial Year.
		</p>

		<div v-if="errorSummary" ref="errorEl" class="kt-error-summary" role="alert" tabindex="-1">
			{{ errorSummary }}
		</div>

		<ContextCard :items="contextItems" />

		<div class="kt-card kt-blueprint" style="padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 16px">Window</div>
			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
				<div class="kt-field" style="margin: 0">
					<label for="nds-opens-at">Opens at</label>
					<input id="nds-opens-at" class="kt-input" type="datetime-local" v-model="form.opens_at" />
				</div>
				<div class="kt-field" style="margin: 0">
					<label for="nds-closes-at">Closes at</label>
					<input id="nds-closes-at" class="kt-input" type="datetime-local" v-model="form.closes_at" />
					<div style="font-size: 12.5px; color: var(--color-neutral-600); margin-top: 6px">
						The closing instant is inclusive.
					</div>
				</div>
			</div>
		</div>

		<div class="kt-page-footer" style="justify-content: flex-end">
			<button class="kt-btn kt-btn-primary" :disabled="pending" @click="$emit('save', form)">
				Save window
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
import ContextCard from "./ContextCard.vue";
import StatusPill from "./StatusPill.vue";

const props = defineProps({
	window: { type: Object, default: () => ({}) },
	context: { type: Object, default: () => ({}) },
	errorSummary: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["save"]);

const errorEl = ref(null);
const form = reactive({ opens_at: "", closes_at: "" });

watch(
	() => props.window,
	(value) => {
		form.opens_at = toLocalInput(value?.opens_at);
		form.closes_at = toLocalInput(value?.closes_at);
	},
	{ immediate: true, deep: true }
);

watch(
	() => props.errorSummary,
	async (message) => {
		if (!message) return;
		await nextTick();
		errorEl.value?.focus();
	}
);

// The server stores site-local instants; <input type="datetime-local"> wants
// `YYYY-MM-DDTHH:MM`, so only the separator and seconds differ.
function toLocalInput(value) {
	if (!value) return "";
	return String(value).slice(0, 16).replace(" ", "T");
}

const contextItems = computed(() => [
	{ label: "Procuring Entity", value: props.context.procuring_entity_label || props.context.procuring_entity || "" },
	{ label: "Financial Year", value: props.context.financial_year_label || props.context.financial_year || "" },
]);
</script>
