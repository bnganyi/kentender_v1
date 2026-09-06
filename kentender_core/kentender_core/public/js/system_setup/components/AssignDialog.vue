<script setup>
// AUTH-ADR-001 v1.6 §13.5/§13.6/§14.3 — the guided assign dialog, ported
// from AUTH-DES-04/05. Fields 3–7 appear only as the selected registry
// role's scope and appointment require: a Site-wide role hides the
// Organisation Unit control entirely, Permanent hides Effective to and
// Authority reference. There is no Procuring Entity control (§13.1).
//
// The Responsibility and Organisation Unit controls are drawn as the
// artboard draws them — the role beside its scope tag, the unit as its full
// path — which a native <select> cannot render, so both are lightweight
// in-dialog listboxes over the same server-supplied options.
//
// The dialog computes nothing it could get wrong: required fields, the exact
// scope description, descendant counts, exclusive-office findings and the
// human summary all come from the server's preview, and the primary button
// stays disabled with a visible reason until that preview says ok.
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { responsibilityApi } from "../data/responsibilityApi.js";

const props = defineProps({
	responsibilities: { type: Array, required: true },
	organisationUnits: { type: Array, required: true },
	busy: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
const emit = defineEmits(["submit", "cancel"]);

const form = ref({
	user: "",
	business_role: "",
	organisation_unit: "",
	appointment_type: "Permanent",
	effective_from: "",
	effective_to: "",
	authority_reference: "",
});
const userQuery = ref("");
const userMatches = ref([]);
const userLabel = ref("");
const roleOpen = ref(false);
const ouOpen = ref(false);
const preview = ref(null);
const previewing = ref(false);
const firstField = ref(null);

const registryEntry = computed(() =>
	props.responsibilities.find((r) => r.business_role === form.value.business_role) || null
);
const needsUnit = computed(() => !!registryEntry.value?.requires_organisation_unit);
const isActing = computed(() => form.value.appointment_type === "Acting");
const selectedUnit = computed(() =>
	props.organisationUnits.find((u) => u.id === form.value.organisation_unit) || null
);

onMounted(async () => {
	await nextTick();
	firstField.value?.focus();
	userMatches.value = await responsibilityApi.searchUsers("");
});

let searchToken = 0;
async function searchUsers() {
	const token = ++searchToken;
	const rows = await responsibilityApi.searchUsers(userQuery.value);
	if (token === searchToken) userMatches.value = rows;
}

function pickUser(match) {
	form.value.user = match.id;
	userLabel.value = match.label;
	userQuery.value = "";
	userMatches.value = [];
	refreshPreview();
}

function clearUser() {
	form.value.user = "";
	refreshPreview();
}

function pickRole(role) {
	form.value.business_role = role.business_role;
	roleOpen.value = false;
	// The registry decides whether a unit exists on this assignment; clear a
	// stale value so it is never sent for a Site-wide role.
	if (!role.requires_organisation_unit) form.value.organisation_unit = "";
	refreshPreview();
}

function pickUnit(unit) {
	form.value.organisation_unit = unit.id;
	ouOpen.value = false;
	refreshPreview();
}

function onAppointmentChange() {
	if (!isActing.value) {
		form.value.effective_to = "";
		form.value.authority_reference = "";
	}
	refreshPreview();
}

let previewToken = 0;
async function refreshPreview() {
	const token = ++previewToken;
	previewing.value = true;
	try {
		const result = await responsibilityApi.preview({ ...form.value });
		if (token === previewToken) preview.value = result;
	} catch (e) {
		if (token === previewToken) preview.value = { ok: false, problems: [], conflict: null, summary: "" };
	} finally {
		if (token === previewToken) previewing.value = false;
	}
}
watch(
	() => [form.value.effective_from, form.value.effective_to, form.value.authority_reference],
	refreshPreview
);

function problemFor(field) {
	return (preview.value?.problems || []).find((p) => p.field === field)?.message || "";
}

function onEscape() {
	// Esc closes an open listbox first; a second Esc closes the dialog.
	if (roleOpen.value || ouOpen.value) {
		roleOpen.value = false;
		ouOpen.value = false;
		return;
	}
	emit("cancel");
}

const canSubmit = computed(() => !props.busy && !previewing.value && !!preview.value?.ok);
const blockedReason = computed(() => {
	if (preview.value?.conflict) return __("Resolve the conflicting assignment to continue");
	if (!preview.value?.ok) return __("Complete every required field to continue");
	return "";
});
</script>

<template>
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div
			class="kt-dialog kt-blueprint kt-assign"
			role="dialog"
			aria-modal="true"
			:aria-label="__('Assign responsibility')"
			data-testid="kt-ura-assign"
			@keydown.esc="onEscape"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">{{ __("Assign responsibility") }}</h2>

			<div class="kt-assign-body">
				<!-- 1 User — AUTH-DES-04's stacked name and login -->
				<div class="kt-field">
					<label for="kt-assign-user">{{ __("User") }}</label>
					<button
						v-if="form.user"
						type="button"
						class="kt-input kt-picked-user"
						data-testid="kt-ura-user-picked"
						@click="clearUser"
					>
						<span class="kt-picked-id">
							<span>{{ userLabel }}</span>
							<span>{{ form.user }}</span>
						</span>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
					</button>
					<template v-else>
						<input
							id="kt-assign-user"
							ref="firstField"
							v-model="userQuery"
							class="kt-input"
							type="search"
							:placeholder="__('Search by name or login')"
							data-testid="kt-ura-user"
							@input="searchUsers"
						>
						<ul v-if="userMatches.length" class="kt-matches">
							<li v-for="match in userMatches" :key="match.id">
								<button type="button" @click="pickUser(match)">
									<span>{{ match.label }}</span>
									<span class="kt-muted">{{ match.id }}</span>
								</button>
							</li>
						</ul>
					</template>
					<p v-if="problemFor('user')" class="kt-inline-error">{{ problemFor("user") }}</p>
				</div>

				<!-- 2 Responsibility — the role beside its scope tag (AUTH-DES-04) -->
				<div class="kt-field kt-select-wrap">
					<label id="kt-assign-role-label">{{ __("Responsibility") }}</label>
					<button
						type="button"
						class="kt-input kt-select"
						aria-haspopup="listbox"
						:aria-expanded="roleOpen"
						aria-labelledby="kt-assign-role-label"
						data-testid="kt-ura-role"
						@click="roleOpen = !roleOpen; ouOpen = false"
					>
						<span v-if="registryEntry" class="kt-select-value">
							<span>{{ registryEntry.business_role }}</span>
							<span class="kt-tag kt-tag-accent">{{ registryEntry.scope_type }}</span>
						</span>
						<span v-else class="kt-select-placeholder">{{ __("Select a responsibility") }}</span>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6" /></svg>
					</button>
					<ul v-if="roleOpen" class="kt-matches" role="listbox">
						<li v-for="role in responsibilities" :key="role.business_role">
							<button
								type="button"
								role="option"
								:aria-selected="role.business_role === form.business_role"
								:data-testid="'kt-ura-role-option-' + role.business_role"
								@click="pickRole(role)"
							>
								<span>{{ role.business_role }}</span>
								<span class="kt-tag kt-tag-accent">{{ role.scope_type }}</span>
							</button>
						</li>
					</ul>
					<p v-if="problemFor('business_role')" class="kt-inline-error">{{ problemFor("business_role") }}</p>
				</div>

				<!-- 3 Organisation Unit — OU-scoped roles only; shown as its full
				     path, active units only -->
				<div v-if="needsUnit" class="kt-field kt-select-wrap" data-testid="kt-ura-ou">
					<label id="kt-assign-ou-label">{{ __("Organisation Unit") }}</label>
					<button
						type="button"
						class="kt-input kt-select"
						aria-haspopup="listbox"
						:aria-expanded="ouOpen"
						aria-labelledby="kt-assign-ou-label"
						data-testid="kt-ura-ou-toggle"
						@click="ouOpen = !ouOpen; roleOpen = false"
					>
						<span v-if="selectedUnit" class="kt-select-value">
							<span>{{ selectedUnit.path_label || selectedUnit.label }}</span>
						</span>
						<span v-else class="kt-select-placeholder">{{ __("Select an Organisation Unit") }}</span>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 6h6" /><path d="M3 12h10" /><path d="M3 18h10" /><path d="M17 9v9" /><path d="m14 15 3 3 3-3" /></svg>
					</button>
					<ul v-if="ouOpen" class="kt-matches" role="listbox">
						<li v-for="unit in organisationUnits" :key="unit.id">
							<button
								type="button"
								role="option"
								:aria-selected="unit.id === form.organisation_unit"
								:data-testid="'kt-ura-ou-option-' + unit.id"
								@click="pickUnit(unit)"
							>
								<span>{{ unit.path_label || unit.label }}</span>
							</button>
						</li>
					</ul>
					<p v-if="problemFor('organisation_unit')" class="kt-inline-error">{{ problemFor("organisation_unit") }}</p>
				</div>

				<!-- 4 Appointment -->
				<fieldset class="kt-field kt-fieldset">
					<legend>{{ __("Appointment") }}</legend>
					<div class="kt-seg">
						<label
							v-for="kind in ['Permanent', 'Acting']"
							:key="kind"
							class="kt-seg-opt"
							:class="{ 'is-selected': form.appointment_type === kind }"
						>
							<input
								v-model="form.appointment_type"
								type="radio"
								name="kt-appointment"
								:value="kind"
								:data-testid="'kt-ura-appointment-' + kind.toLowerCase()"
								@change="onAppointmentChange"
							>
							<span>{{ kind === "Permanent" ? __("Permanent") : __("Acting") }}</span>
						</label>
					</div>
				</fieldset>

				<!-- 5/6 Effective period — the artboard's empty date field reads
				     "Leave blank to start immediately" -->
				<div class="kt-dates" :class="{ 'is-single': !isActing }">
					<div class="kt-field">
						<label for="kt-assign-from">{{ __("Effective from") }}</label>
						<div class="kt-date-field" :class="{ 'is-empty': !form.effective_from }">
							<input
								id="kt-assign-from"
								v-model="form.effective_from"
								class="kt-input"
								type="date"
								data-testid="kt-ura-from"
							>
							<span class="kt-date-placeholder">{{ __("Leave blank to start immediately") }}</span>
						</div>
						<p v-if="problemFor('effective_from')" class="kt-inline-error">{{ problemFor("effective_from") }}</p>
					</div>
					<div v-if="isActing" class="kt-field">
						<label for="kt-assign-to">{{ __("Effective to") }}</label>
						<input id="kt-assign-to" v-model="form.effective_to" class="kt-input" type="date" data-testid="kt-ura-to">
						<p v-if="problemFor('effective_to')" class="kt-inline-error">{{ problemFor("effective_to") }}</p>
					</div>
				</div>

				<!-- 7 Authority reference — Acting only -->
				<div v-if="isActing" class="kt-field">
					<label for="kt-assign-authority" :class="{ 'is-error': problemFor('authority_reference') }">
						{{ __("Authority reference") }}
					</label>
					<input
						id="kt-assign-authority"
						v-model="form.authority_reference"
						class="kt-input"
						:class="{ 'is-error': problemFor('authority_reference') }"
						:placeholder="__('Required for Acting assignments')"
						data-testid="kt-ura-authority"
					>
					<p v-if="problemFor('authority_reference')" class="kt-inline-error">{{ problemFor("authority_reference") }}</p>
				</div>

				<!-- AUTH-DES-04's "Responsibility summary" box: the server's words,
				     with the role and scope emphasised; the descendant note per
				     §13.6 -->
				<div v-if="preview && preview.summary" class="kt-summary" data-testid="kt-ura-summary">
					<span class="kt-label">{{ __("Responsibility summary") }}</span>
					<p>
						<template v-if="preview.summary_parts">
							{{ preview.summary_parts.user }} {{ __("will be") }}
							<strong>{{ preview.summary_parts.role }}</strong> {{ __("for") }}
							<strong>{{ preview.summary_parts.scope }}</strong>
							{{ preview.summary_parts.period }}.
						</template>
						<template v-else>{{ preview.summary }}</template>
						<template v-if="preview.descendant_count">
							{{ preview.descendant_count === 1
								? __("This includes 1 subordinate organisation unit.")
								: __("This includes {0} subordinate organisation units.", [preview.descendant_count]) }}
						</template>
					</p>
				</div>

				<!-- Server-detected conflict — the exclusive-office notice carries the
				     AUTH-DES-05 heading; never resolved by an invented client rule -->
				<div v-if="preview && preview.conflict" class="kt-conflict" role="alert" data-testid="kt-ura-conflict">
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
					<span>
						<strong v-if="preview.conflict.heading" class="kt-conflict-heading">{{ preview.conflict.heading }}</strong>
						{{ preview.conflict.message }}
					</span>
				</div>

				<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
			</div>

			<div class="kt-dialog-actions kt-assign-actions">
				<div v-if="blockedReason" class="kt-blocked">{{ blockedReason }}</div>
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="!canSubmit"
					data-testid="kt-ura-assign-confirm"
					@click="emit('submit', { ...form })"
				>{{ __("Assign responsibility") }}</button>
			</div>
		</div>
	</div>
</template>
