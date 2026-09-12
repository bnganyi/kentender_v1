<script setup>
// CFG-DES-05/06 — open (with optional close instant, reason and the
// replacement notice naming the exact other open year) and close (reason,
// destructive). One component, two modes; the server re-validates everything.
// CFG v0.9 §4.2 — the same dialog serves departmental-plan intake
// (`purpose: "plan"`), which is an independent flag with its own copy.
import { computed, nextTick, onMounted, ref } from "vue";

const props = defineProps({
	mode: { type: String, required: true }, // "open" | "close"
	purpose: { type: String, default: "needs" }, // "needs" | "plan"
	row: { type: Object, required: true },
	// The year currently open elsewhere, when opening would replace it.
	replaces: { type: Object, default: null },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const closesAt = ref("");
const reason = ref("");
const field = ref(null);

const copy = computed(() => {
	const label = props.row.label;
	if (props.purpose === "plan") {
		// PLN-CHG-001 v1.18 §10.11 C02 / C02-close — exact dialog copy.
		return {
			openTitle: __("Open departmental-plan intake"),
			closeTitle: __("Close departmental-plan intake"),
			openBody: __("Departments will be able to make their first departmental-plan submission for {0}.", [label]),
			closeBody: __("Existing submissions and governed updates remain available under their Planning rules."),
			replaces: __("Departmental-plan intake can be open for one financial year at a time. Intake for {0} will close when you continue.", [props.replaces?.label]),
			openButton: __("Open departmental-plan intake"),
			closeButton: __("Close intake"),
		};
	}
	return {
		openTitle: __("Open needs submission"),
		closeTitle: __("Close needs submission?"),
		openBody: __("Departments will be able to create and submit needs for {0}.", [label]),
		closeBody: __("Departments will no longer be able to create or submit needs for {0}. Needs already submitted or accepted are unaffected.", [label]),
		replaces: __("Needs submission can be open for one financial year at a time. Submission for {0} will close when you continue.", [props.replaces?.label]),
		openButton: __("Open needs submission"),
		closeButton: __("Close needs submission"),
	};
});

onMounted(async () => {
	await nextTick();
	field.value?.focus();
});

function confirm() {
	emit("confirm", {
		closes_at: props.mode === "open" ? closesAt.value : "",
		reason: reason.value.trim(),
	});
}
</script>

<template>
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div
			class="kt-dialog kt-blueprint kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="mode === 'open' ? copy.openTitle : copy.closeTitle"
			data-testid="kt-fy-intake"
			:data-purpose="purpose"
			@keydown.esc="emit('cancel')"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">
				{{ mode === "open" ? copy.openTitle : copy.closeTitle }}
			</h2>
			<p v-if="!(purpose === 'plan' && mode === 'close')" class="kt-confirm-body">
				{{ mode === "open" ? copy.openBody : copy.closeBody }}
			</p>
			<div class="kt-dialog-fields">
				<!-- C02 — the year is shown read-only on the plan-intake dialog -->
				<div v-if="purpose === 'plan' && mode === 'open'" class="kt-field">
					<label for="kt-intake-year">{{ __("Financial year") }}</label>
					<input id="kt-intake-year" class="kt-input" :value="row.label" disabled data-testid="kt-fy-intake-year">
				</div>
				<div v-if="mode === 'open'" class="kt-field">
					<label for="kt-intake-closes">{{ __("Close automatically on") }}</label>
					<input
						id="kt-intake-closes"
						ref="field"
						v-model="closesAt"
						class="kt-input"
						type="datetime-local"
						data-testid="kt-fy-intake-closes"
					>
					<p class="kt-hint">{{ __("Leave blank to keep submission open until you close it.") }}</p>
				</div>
				<div class="kt-field">
					<label for="kt-intake-reason">{{ __("Reason") }}</label>
					<textarea
						id="kt-intake-reason"
						:ref="mode === 'close' ? 'field' : undefined"
						v-model="reason"
						class="kt-input kt-textarea"
						rows="3"
						data-testid="kt-fy-intake-reason"
					/>
				</div>
				<!-- CFG-DES-05 replacement notice — only when another year is open,
				     naming that exact year (§11.3) -->
				<div v-if="mode === 'open' && replaces" class="kt-setup-notice" data-testid="kt-fy-intake-replaces">
					<h3>{{ __("This will close {0}", [replaces.label]) }}</h3>
					<p>{{ copy.replaces }}</p>
				</div>
				<!-- C02-close — the consequence statement follows the reason -->
				<p v-if="purpose === 'plan' && mode === 'close'" class="kt-confirm-body" data-testid="kt-fy-intake-close-note">{{ copy.closeBody }}</p>
				<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:class="{ 'kt-danger': mode === 'close' }"
					:disabled="busy"
					data-testid="kt-fy-intake-confirm"
					@click="confirm"
				>{{ mode === "open" ? copy.openButton : copy.closeButton }}</button>
			</div>
		</div>
	</div>
</template>
