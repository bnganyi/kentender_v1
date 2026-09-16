<script setup>
// CFG-CHG-002 v0.11 §10.3/§11.3 (C02 "forms") / CFG11-CHG-004 — one focused
// form per action (open, close, change closing time) across all three
// intake activities, ported from the artboard's Open/Close/Deadline-edit
// cards into the existing modal shell (the artboard itself renders "disable"
// and "add-year" as `.dialog`s; the forms grid uses `.card` only for the
// side-by-side documentation layout, not to mandate inline chrome).
// Title, close-instant hint, reason and cross-year "stays as they are" text
// are all composed from one activity-label vocabulary (§8: "activity labels
// are Departmental needs, Departmental plan and Disposal plan; the composed
// messages append 'submissions'") — never bespoke per-purpose prose, which
// is exactly what CFG11-CHG-004 retires.
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
	// The year currently open elsewhere, when opening would replace it.
	replaces: { type: Object, default: null },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel", "refresh"]);

const closesAt = ref(props.mode === "deadline" ? (props.row.closes_at_local || "") : "");
const reason = ref("");
const field = ref(null);

const activity = computed(() => ACTIVITY_LABELS[props.purpose] || ACTIVITY_LABELS.needs);
const activityLower = computed(() => {
	const label = activity.value;
	return label.charAt(0).toLowerCase() + label.slice(1);
});

const copy = computed(() => {
	const others = Object.entries(ACTIVITY_LABELS)
		.filter(([key]) => key !== props.purpose)
		.map(([, label]) => label)
		.join(" and ");
	const closeNote = {
		needs: __("Existing needs remain available under the Departmental Needs rules."),
		plan: __("Existing submissions and permitted updates remain available."),
		disposal_plan: __("Existing records remain available under the Disposal rules."),
	}[props.purpose];
	return {
		openTitle: __("Open {0} submissions", [activityLower.value]),
		closeTitle: __("Close {0} submissions", [activityLower.value]),
		closeNote,
		replaces: props.replaces
			? __("This will close {0} submissions for {1}. {2} submissions will stay as they are.", [
					activityLower.value,
					props.replaces.label,
					others,
				])
			: "",
	};
});

const title = computed(() => {
	if (props.mode === "open") return copy.value.openTitle;
	if (props.mode === "close") return copy.value.closeTitle;
	return __("Change closing time");
});
const confirmLabel = computed(() => {
	if (props.mode === "open") return __("Open submissions");
	if (props.mode === "close") return __("Close submissions");
	return __("Save closing time");
});

// CFG-UX-AC-08 — a stale control token is its own distinguishable notice
// with a recovery link, never folded into the generic error paragraph.
const stale = computed(() => props.error === CFG_VERSION_CONFLICT_MESSAGE);

onMounted(async () => {
	await nextTick();
	field.value?.focus();
});

function confirm() {
	emit("confirm", {
		closes_at: props.mode === "close" ? "" : closesAt.value,
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
			:aria-label="title"
			data-testid="kt-fy-intake"
			:data-purpose="purpose"
			:data-mode="mode"
			@keydown.esc="emit('cancel')"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<div class="kt-dialog-fields">
				<div class="kt-meta-row" style="margin-bottom:8px">
					<div><span class="kt-label">{{ __("Year") }}</span><span class="kt-meta-value">{{ row.label }}</span></div>
					<div v-if="mode === 'deadline'"><span class="kt-label">{{ __("Activity") }}</span><span class="kt-meta-value">{{ activity }}</span></div>
				</div>
				<div v-if="mode !== 'close'" class="kt-field">
					<label for="kt-intake-closes">{{ __("Close automatically on (EAT)") }}</label>
					<input
						id="kt-intake-closes"
						ref="field"
						v-model="closesAt"
						class="kt-input"
						type="datetime-local"
						data-testid="kt-fy-intake-closes"
					>
					<p class="kt-hint">{{ __("Leave blank to keep submissions open until you close them.") }}</p>
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
				<!-- cross-year replacement notice — only when another year is open,
				     naming that exact year and what stays untouched (§11.3) -->
				<div v-if="mode === 'open' && replaces" class="kt-setup-notice" data-testid="kt-fy-intake-replaces">
					<h3>{{ __("This will close {0}", [replaces.label]) }}</h3>
					<p>{{ copy.replaces }}</p>
				</div>
				<p v-if="mode === 'close'" class="kt-muted" data-testid="kt-fy-intake-close-note">{{ copy.closeNote }}</p>
				<div
					v-if="stale"
					class="kt-notice is-warning"
					style="flex-direction:column;align-items:flex-start"
					data-testid="kt-fy-intake-stale"
				>
					<div class="kt-notice-body"><strong>{{ __("Stale.") }}</strong> {{ __("These submission settings have changed since you opened them.") }}</div>
					<a href="#" style="margin-left:0;font-size:13px" @click.prevent="emit('refresh')">{{ __("Review latest settings") }}</a>
				</div>
				<p v-else-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
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
				>{{ confirmLabel }}</button>
			</div>
		</div>
	</div>
</template>
