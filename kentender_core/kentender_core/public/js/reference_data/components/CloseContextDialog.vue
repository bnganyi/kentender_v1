<script setup>
// §12.8 — Close Context dialog: closure reason (required) + explicit acknowledgment
// checkbox that the action removes the context from new-work selectors without
// cancelling existing records. Matches CFG-PEFY-DES-07.
import { reactive, computed } from "vue";

const props = defineProps({
	contextLine: { type: String, required: true },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const form = reactive({ reason: "", acknowledged: false });
const canConfirm = computed(() => form.reason.trim().length > 0 && form.acknowledged);

function confirm() {
	if (!canConfirm.value || props.busy) return;
	emit("confirm", { reason: form.reason.trim() });
}
</script>

<template>
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div class="kt-dialog kt-blueprint">
			<h2 class="kt-dialog-title">{{ __("Close PE/FY context") }}</h2>
			<div style="font-size:14px;color:color-mix(in srgb, var(--kt-color-text) 72%, transparent)">{{ contextLine }}</div>
			<p style="margin:0;font-size:14px;line-height:1.55">
				{{ __("This context will no longer appear in new-work selectors. Existing records will remain available according to their module rules.") }}
			</p>
			<div class="kt-field" style="padding-top:4px;border-top:1px solid var(--kt-color-divider)">
				<label style="padding-top:14px">{{ __("Closure reason") }}</label>
				<textarea class="kt-input" style="height:auto;min-height:70px;padding:10px" v-model="form.reason"></textarea>
			</div>
			<label style="display:flex;gap:12px;align-items:flex-start;font-size:14px;line-height:1.5;cursor:pointer">
				<input type="checkbox" v-model="form.acknowledged" style="width:18px;height:18px;margin:1px 0 0;accent-color:var(--kt-color-accent);flex:none" />
				<span>{{ __("I understand that this removes the context from new-work selectors but does not cancel existing records.") }}</span>
			</label>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="emit('cancel')" :disabled="busy">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary kt-danger" :disabled="!canConfirm || busy" @click="confirm">
					{{ __("Close context") }}
				</button>
			</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
	</div>
</template>
