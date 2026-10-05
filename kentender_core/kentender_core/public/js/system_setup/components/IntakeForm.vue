<script setup>
// CFG-CHG-002 v0.14 §10.4 (C02 #forms, #form-states; tracker CFG14-5B) — one
// focused form per action (open, close, change closing time) across the
// three activities, ported from the board's form cards as an inline panel
// inside the year's Submission periods (decision D18: the board draws them
// as cards in the detail, not as modals; the add-year and disable boards are
// the dialogs). The "Open · …" kickers on the board annotate the specimen
// grid and are not drawn.
//
// Copy is the spec's: activity labels Departmental needs / Departmental plan
// / Disposal plan, the composed titles append "submissions" (§8), and the
// cross-year consequence names the displaced year and what stays as it is.
import { computed, nextTick, onMounted, ref } from "vue";
import { CFG_VERSION_CONFLICT_MESSAGE } from "../data/format.js";

const ACTIVITY_LABELS = {
	needs: "Departmental needs",
	plan: "Departmental plan",
	disposal_plan: "Disposal plan",
};

const props = defineProps({
	mode: { type: String, required: true }, // "open" | "close" | "deadline"
	purpose: { type: String, default: "needs" }, // "needs" | "plan" | "disposal_plan"
	row: { type: Object, required: true },
	// The year currently open elsewhere for this activity, when opening replaces it.
	replaces: { type: Object, default: null },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel", "refresh"]);

const closesAt = ref(props.mode === "deadline" ? props.row.closes_at_local || "" : "");
const reason = ref("");
const firstField = ref(null);

const activity = computed(() => ACTIVITY_LABELS[props.purpose] || ACTIVITY_LABELS.needs);
const lower = (text) => text.charAt(0).toLowerCase() + text.slice(1);

const title = computed(() => {
	if (props.mode === "open") return __("Open {0} submissions", [lower(activity.value)]);
	if (props.mode === "close") return __("Close {0} submissions", [lower(activity.value)]);
	return __("Change closing time");
});
const confirmLabel = computed(() => {
	if (props.mode === "open") return __("Open submissions");
	if (props.mode === "close") return __("Close submissions");
	return __("Save closing time");
});
const closeNote = computed(
	() =>
		({
			needs: __("Existing needs remain available under the Departmental Needs rules."),
			plan: __("Existing submissions and permitted updates remain available."),
			disposal_plan: __("Existing records remain available under the Disposal rules."),
		})[props.purpose]
);
// §10.4 CONFIG-SWAP: "This will close departmental plan submissions for FY
// 2026/27. Departmental needs and disposal plan submissions will stay as
// they are."
const replacement = computed(() => {
	if (!props.replaces) return "";
	const others = Object.entries(ACTIVITY_LABELS)
		.filter(([key]) => key !== props.purpose)
		.map(([, label], index) => (index === 0 ? label : lower(label)));
	return __("This will close {0} submissions for {1}. {2} and {3} submissions will stay as they are.", [
		lower(activity.value),
		props.replaces.label,
		others[0],
		others[1],
	]);
});

// §10.4 form states: a past closing time, an expiry and a stale control token
// are each their own notice; any other refusal is shown as the server said it.
const deadlineError = computed(() => /later than the current time/i.test(props.error || ""));
const expired = computed(() => /submissions closed at/i.test(props.error || ""));
const stale = computed(() => props.error === CFG_VERSION_CONFLICT_MESSAGE);

onMounted(async () => {
	await nextTick();
	firstField.value?.focus();
});

function confirm() {
	emit("confirm", { closes_at: props.mode === "close" ? "" : closesAt.value, reason: reason.value.trim() });
}
</script>

<template>
	<div
		class="card kt-intake-form"
		role="group"
		:aria-label="title"
		data-testid="kt-fy-intake"
		:data-purpose="purpose"
		:data-mode="mode"
		@keydown.esc="emit('cancel')"
	>
		<div class="kt-intake-title">{{ title }}</div>
		<div class="kt-meta-row" style="margin:8px 0">
			<div><span class="kt-label">{{ __("Year") }}</span><span class="kt-meta-value">{{ row.label }}</span></div>
			<div v-if="mode === 'deadline'"><span class="kt-label">{{ __("Activity") }}</span><span class="kt-meta-value">{{ activity }}</span></div>
		</div>
		<template v-if="mode !== 'close'">
			<div class="field">
				<label for="kt-intake-closes">{{ __("Close automatically on (EAT)") }}</label>
				<input
					id="kt-intake-closes"
					ref="firstField"
					v-model="closesAt"
					class="input"
					type="datetime-local"
					:aria-invalid="deadlineError ? 'true' : 'false'"
					data-testid="kt-fy-intake-closes"
				>
			</div>
			<p v-if="mode === 'open'" class="text-muted" style="font-size:12px">
				{{ __("Leave the closing date blank to keep submissions open until you close them.") }}
			</p>
		</template>
		<div class="field">
			<label for="kt-intake-reason">{{ __("Reason") }}</label>
			<textarea
				id="kt-intake-reason"
				:ref="mode === 'close' ? 'firstField' : undefined"
				v-model="reason"
				class="input"
				rows="2"
				data-testid="kt-fy-intake-reason"
			/>
		</div>
		<p v-if="mode === 'close'" class="text-muted" style="font-size:12px" data-testid="kt-fy-intake-close-note">{{ closeNote }}</p>
		<div v-if="mode === 'open' && replaces" class="kt-notice is-warning" style="margin:8px 0" data-testid="kt-fy-intake-replaces">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
			<div class="kt-notice-body">{{ replacement }}</div>
		</div>

		<div v-if="deadlineError" class="kt-notice is-critical" role="alert" data-testid="kt-fy-intake-deadline-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("Deadline error.") }}</strong> {{ error }}</div>
		</div>
		<div v-else-if="expired" class="kt-notice is-warning" role="alert" data-testid="kt-fy-intake-expired">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" /></svg>
			<div class="kt-notice-body"><strong>{{ __("Expired.") }}</strong> {{ error }}</div>
		</div>
		<div
			v-else-if="stale"
			class="kt-notice is-warning"
			role="alert"
			style="flex-direction:column;align-items:flex-start"
			data-testid="kt-fy-intake-stale"
		>
			<div style="display:flex;gap:12px;align-items:flex-start">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.64-6.36" /><path d="M21 3v6h-6" /></svg>
				<div class="kt-notice-body"><strong>{{ __("Stale.") }}</strong> {{ __("These submission settings have changed since you opened them.") }}</div>
			</div>
			<a href="#" style="margin-left:30px;font-size:13px" data-testid="kt-fy-intake-review" @click.prevent="emit('refresh')">{{ __("Review latest settings") }}</a>
		</div>
		<div v-else-if="error" class="kt-notice is-critical" role="alert" data-testid="kt-fy-intake-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body">{{ error }}</div>
		</div>

		<div style="display:flex;gap:8px;justify-content:flex-end">
			<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="kt-fy-intake-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
			<button type="button" class="btn btn-primary" :disabled="busy" data-testid="kt-fy-intake-confirm" @click="confirm">{{ confirmLabel }}</button>
		</div>
	</div>
</template>
