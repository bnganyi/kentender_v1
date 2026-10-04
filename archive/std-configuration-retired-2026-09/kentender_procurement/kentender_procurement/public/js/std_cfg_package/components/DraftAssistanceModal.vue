<script setup>
// STD-UI-M02 — Prepare Draft assistance (§15.6, first half). "Prior configured
// data" is wired to the real Phase 10 reuse-transformation engine
// (run_std_reuse_transformation over the checked-in IT_STD_Config_Control_Pack
// bundle) — the only real proposal-generating mechanism this build has.
// "AI-assisted draft" has no calling adapter yet (tracker STD-802) and is
// shown disabled rather than faked as working.
import { ref, watch } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	saving: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
const emit = defineEmits(["confirm", "cancel"]);

const choice = ref("prior");
watch(
	() => props.open,
	(isOpen) => {
		if (isOpen) choice.value = "prior";
	}
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" @keydown="onKeydown" tabindex="-1">
		<div class="kt-dialog kt-blueprint" style="width: 560px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h2 class="kt-dialog-title">{{ __("Prepare Draft assistance") }}</h2>
			<p class="kt-muted" style="font-size: 14px; margin: 0 0 16px">
				{{ __("Use reviewed prior configuration or AI assistance to prepare proposals. Nothing changes until you review and accept individual items.") }}
			</p>

			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px">
				<div
					class="kt-card"
					:style="{ padding: '14px', cursor: 'pointer', borderColor: choice === 'prior' ? 'var(--kt-color-accent)' : undefined }"
					@click="choice = 'prior'"
				>
					<strong>{{ __("Prior configured data") }}</strong>
					<p class="kt-muted" style="font-size: 13px; margin: 6px 0 0">{{ __("Use an earlier reviewed IT STD configuration dataset.") }}</p>
				</div>
				<div class="kt-card" style="padding: 14px; opacity: 0.5; cursor: not-allowed">
					<strong>{{ __("AI-assisted draft") }}</strong>
					<p class="kt-muted" style="font-size: 13px; margin: 6px 0 0">{{ __("Prepare proposals from the official source and existing Draft.") }}</p>
					<p class="kt-muted" style="font-size: 12px; margin: 6px 0 0">{{ __("Not yet available") }}</p>
				</div>
			</div>

			<div v-if="choice === 'prior'" class="kt-field" style="margin: 0 0 16px">
				<label>{{ __("Configuration file") }}</label>
				<div class="kt-muted" style="font-size: 13px">
					{{ __("Uses this package's reviewed prior configuration bundle (IT_STD_Config_Control_Pack).") }}
				</div>
			</div>

			<p v-if="error" class="kt-status is-critical" style="display: inline-block">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" @click="$emit('confirm')">
					{{ __("Prepare proposals") }}
				</button>
			</div>
		</div>
	</div>
</template>
