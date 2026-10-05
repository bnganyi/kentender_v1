<script setup>
// CFG-CHG-002 v0.14 §10.6 (C03BC #version; tracker CFG14-5D) — the top of a
// rule's new-version form, shared by both rule editors: the heading, the
// Unsaved changes tag, the earlier version's facts, the reason, what it
// replaces, the effect of the replacement and its warning. The editable
// fields follow it in each editor.
import { computed } from "vue";
import { fmtDate } from "../data/format.js";

const props = defineProps({
	ruleName: { type: String, required: true },
	current: { type: Object, required: true },
	// The replacement's reason (v-model).
	modelValue: { type: String, default: "" },
	// The dates entered overlap the earlier version, so it is replaced (D16).
	replaces: { type: Boolean, default: true },
});
const emit = defineEmits(["update:modelValue"]);

const n = computed(() => props.current.version_number);
</script>

<template>
	<div class="kt-rule-version-head" data-testid="kt-rule-version-head">
		<h3 style="margin-bottom:4px" data-testid="kt-rule-version-title">{{ __("{0} — new version", [ruleName]) }}</h3>
		<span class="tag tag-neutral" data-testid="kt-rule-unsaved">{{ __("Unsaved changes") }}</span>
		<div class="kt-meta-row" style="margin:12px 0">
			<div><span class="kt-label">{{ __("Earlier version") }}</span><span class="kt-meta-value">{{ n }}</span></div>
			<div><span class="kt-label">{{ __("Applies from") }}</span><span class="kt-meta-value">{{ fmtDate(current.effective_from) }}</span></div>
			<div><span class="kt-label">{{ __("Applies until") }}</span><span class="kt-meta-value">{{ fmtDate(current.effective_until) }}</span></div>
		</div>
		<div class="field">
			<label for="kt-rule-reason">{{ __("Reason for change") }}</label>
			<textarea
				id="kt-rule-reason"
				class="input"
				rows="2"
				:value="modelValue"
				data-testid="kt-rule-reason"
				@input="emit('update:modelValue', $event.target.value)"
			/>
		</div>
		<p class="text-muted" style="font-size:12px;margin:8px 0" data-testid="kt-rule-replaces">
			{{ replaces ? __("Earlier versions this replaces: {0} Version {1}.", [ruleName, n]) : __("These dates do not overlap Version {0}, so it is not replaced.", [n]) }}
		</p>
		<div class="kt-section">
			<h6 class="kt-card-title">{{ __("Effect of this replacement") }}</h6>
			<div class="kt-panel">
				<div class="kt-meta-row">
					<div><span class="kt-label">{{ __("Coverage replaced") }}</span><span class="kt-meta-value">{{ replaces ? __("Version {0}, for matching applicability within the displayed period", [n]) : __("None") }}</span></div>
					<div><span class="kt-label">{{ __("Current readiness") }}</span><span class="kt-meta-value">{{ current.verification_status === "Verified" ? __("Version {0} is marked valid", [n]) : __("Version {0} already needs source checks", [n]) }}</span></div>
					<div><span class="kt-label">{{ __("Historical decisions") }}</span><span class="kt-meta-value">{{ __("Keep the exact evidence used at the time") }}</span></div>
					<div><span class="kt-label">{{ __("Usage") }}</span><span class="kt-meta-value">{{ __("Not recorded yet") }}</span></div>
				</div>
			</div>
		</div>
		<div class="kt-notice is-warning" style="margin-top:12px">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
			<div class="kt-notice-body">{{ __("The replacement will not be usable for affected new decisions until its required details and source checks are complete.") }}</div>
		</div>
		<!-- §10.6 live-data impact: replacing a valid version takes it out of
		     positive use until the new one is checked (the server's own fact). -->
		<div v-if="replaces && current.verification_status === 'Verified'" class="kt-notice is-critical" style="margin-top:8px" data-testid="kt-rule-impact">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body">{{ __("Saving this replacement will block new decisions that use this rule until its sources are verified.") }}</div>
		</div>
	</div>
</template>
