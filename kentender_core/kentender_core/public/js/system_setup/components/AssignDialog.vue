<script setup>
// The guided assign dialog, ported from C06 #auth-des-04 (Permanent),
// #auth-des-05 (Acting, office already held) and #auth-edit-scheduled (the
// same dialog prefilled, AUTH v1.9 §13.7). Fields appear only as the selected
// registry role's scope and appointment require: a Site-wide role hides the
// Organisation Unit control entirely, Permanent hides Effective to and
// Authority reference. There is no Procuring Entity control (§13.1).
//
// Responsibility is the board's select ("Role · Scope"); the Organisation
// Unit is the board's read-only path field that opens a list of units (a
// tree select), over the same server-supplied options.
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
	// The scheduled assignment being changed (the detail projection), or
	// null to assign a new one. Owner decision 21 Sep 2026: an assignment
	// that has not started yet may be changed in any field, through this
	// same dialog; the server refuses once it is in force.
	editing: { type: Object, default: null },
});
const emit = defineEmits(["submit", "cancel"]);

const isEdit = computed(() => !!props.editing);
// The inputs are date-only; a stored instant arrives as "2026-12-01 00:00:00".
function dateOnly(value) {
	return value ? String(value).slice(0, 10) : "";
}
const form = ref(
	props.editing
		? {
				user: props.editing.user,
				business_role: props.editing.business_role,
				organisation_unit: props.editing.organisation_unit || "",
				appointment_type: props.editing.appointment_type || "Permanent",
				effective_from: dateOnly(props.editing.effective_from),
				effective_to: dateOnly(props.editing.effective_to),
				authority_reference: props.editing.authority_reference || "",
			}
		: {
				user: "",
				business_role: "",
				organisation_unit: "",
				appointment_type: "Permanent",
				effective_from: "",
				effective_to: "",
				authority_reference: "",
			}
);
const userQuery = ref("");
const userMatches = ref([]);
const userLabel = ref(props.editing ? props.editing.user_full_name || props.editing.user : "");
const roleOpen = ref(false);
const ouOpen = ref(false);
const preview = ref(null);
const previewing = ref(false);
const firstField = ref(null);
const titleId = computed(() => (props.editing ? "kt-assign-edit-title" : "kt-assign-title"));

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
	if (isEdit.value) refreshPreview();
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

// The field shows the chosen user as "Name · login", or what is being typed;
// typing over a choice drops it (the input is bound to the user's own
// selection, never to a server echo).
const userText = computed(() => (form.value.user ? `${userLabel.value} · ${form.value.user}` : userQuery.value));
function onUserInput(event) {
	userQuery.value = event.target.value;
	if (form.value.user) {
		form.value.user = "";
		userLabel.value = "";
		refreshPreview();
	}
	searchUsers();
}

function onRoleChange(event) {
	const role = props.responsibilities.find((r) => r.business_role === event.target.value);
	if (role) pickRole(role);
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
		const result = await responsibilityApi.preview({
			...form.value,
			// The record being changed is left out of the overlap checks.
			...(props.editing ? { assignment: props.editing.assignment } : {}),
		});
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
	// Esc closes the open unit list first; a second Esc closes the dialog.
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
	<div class="dialog-backdrop">
		<div
			class="dialog kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-labelledby="titleId"
			data-testid="kt-ura-assign"
			@keydown.esc.stop="onEscape"
		>
			<h2 :id="titleId" class="dialog-title">{{ isEdit ? __("Edit scheduled assignment") : __("Assign responsibility") }}</h2>

			<div class="dialog-body kt-assign-body">
				<div v-if="isEdit" class="kt-notice is-info" style="align-items:flex-start" data-testid="kt-ura-edit-notice">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v5h1" /></svg>
					<div class="kt-notice-body"><em>{{ __("This assignment has not started yet, so any of its details can still be changed. Clear Effective from to bring it into force now.") }}</em></div>
				</div>

				<!-- User: a person search showing "Name · login" once chosen -->
				<div class="field">
					<label for="kt-assign-user">{{ __("User") }}</label>
					<div class="kt-input-icon">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
						<input
							id="kt-assign-user"
							ref="firstField"
							class="input"
							type="text"
							autocomplete="off"
							:value="userText"
							:placeholder="__('Search by name or login')"
							:aria-invalid="problemFor('user') ? 'true' : 'false'"
							:data-testid="form.user ? 'kt-ura-user-picked' : 'kt-ura-user'"
							@input="onUserInput"
						>
					</div>
					<ul v-if="!form.user && userMatches.length" class="kt-matches">
						<li v-for="match in userMatches" :key="match.id">
							<button type="button" @click="pickUser(match)">
								<span>{{ match.label }}</span>
								<span class="kt-muted">{{ match.id }}</span>
							</button>
						</li>
					</ul>
					<p v-if="problemFor('user')" class="kt-field-error">{{ problemFor("user") }}</p>
				</div>

				<!-- Responsibility: "Role · Scope", as the board's select -->
				<div class="field">
					<label for="kt-assign-role">{{ __("Responsibility") }}</label>
					<select
						id="kt-assign-role"
						class="input"
						:value="form.business_role"
						:aria-invalid="problemFor('business_role') ? 'true' : 'false'"
						data-testid="kt-ura-role"
						@change="onRoleChange"
					>
						<option value="" disabled>{{ __("Select a responsibility") }}</option>
						<option v-for="role in responsibilities" :key="role.business_role" :value="role.business_role">
							{{ role.business_role }} · {{ role.scope_type }}
						</option>
					</select>
					<p v-if="problemFor('business_role')" class="kt-field-error">{{ problemFor("business_role") }}</p>
				</div>

				<!-- Organisation Unit: OU-scoped roles only; its full path, opening
				     the list of active units -->
				<div v-if="needsUnit" class="field" data-testid="kt-ura-ou">
					<label for="kt-assign-ou">{{ __("Organisation Unit") }}</label>
					<div class="kt-input-icon is-trailing">
						<input
							id="kt-assign-ou"
							class="input"
							type="text"
							readonly
							role="combobox"
							aria-haspopup="listbox"
							:aria-expanded="ouOpen ? 'true' : 'false'"
							:value="selectedUnit ? selectedUnit.path_label || selectedUnit.label : ''"
							:placeholder="__('Select an Organisation Unit')"
							data-testid="kt-ura-ou-toggle"
							@click="ouOpen = !ouOpen"
							@keydown.enter.prevent="ouOpen = !ouOpen"
							@keydown.space.prevent="ouOpen = !ouOpen"
						>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M3 6h6" /><path d="M3 12h10" /><path d="M3 18h10" /><path d="M17 9v9" /><path d="m14 15 3 3 3-3" /></svg>
					</div>
					<ul v-if="ouOpen" class="kt-matches" role="listbox" :aria-label="__('Organisation units')">
						<li v-for="unit in organisationUnits" :key="unit.id">
							<button
								type="button"
								role="option"
								:aria-selected="unit.id === form.organisation_unit ? 'true' : 'false'"
								:data-testid="'kt-ura-ou-option-' + unit.id"
								@click="pickUnit(unit)"
							>{{ unit.path_label || unit.label }}</button>
						</li>
					</ul>
					<p v-if="problemFor('organisation_unit')" class="kt-field-error">{{ problemFor("organisation_unit") }}</p>
				</div>

				<div class="field">
					<label id="kt-assign-appointment">{{ __("Appointment") }}</label>
					<div class="kt-seg kt-seg-inline" role="radiogroup" aria-labelledby="kt-assign-appointment" style="align-self:flex-start">
						<label v-for="kind in ['Permanent', 'Acting']" :key="kind" class="seg-opt">
							<input
								v-model="form.appointment_type"
								type="radio"
								name="kt-appointment"
								:value="kind"
								:data-testid="'kt-ura-appointment-' + kind.toLowerCase()"
								@change="onAppointmentChange"
							>{{ kind === "Permanent" ? __("Permanent") : __("Acting") }}
						</label>
					</div>
				</div>

				<!-- Permanent: one optional start; Acting: the period side by side -->
				<div v-if="!isActing" class="field">
						<label for="kt-assign-from">{{ __("Effective from") }} <span class="text-muted" style="font-weight:400">{{ __("(optional)") }}</span></label>
						<div class="kt-date-field" :class="{ 'is-empty': !form.effective_from }">
							<input id="kt-assign-from" v-model="form.effective_from" class="input" type="date" data-testid="kt-ura-from">
							<span class="kt-date-placeholder">{{ __("Leave blank to start immediately") }}</span>
						</div>
					<p v-if="problemFor('effective_from')" class="kt-field-error">{{ problemFor("effective_from") }}</p>
				</div>
				<div v-if="isActing" style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
					<div class="field">
						<label for="kt-assign-from-acting">{{ __("Effective from") }}</label>
						<input id="kt-assign-from-acting" v-model="form.effective_from" class="input" type="date" data-testid="kt-ura-from">
						<p v-if="problemFor('effective_from')" class="kt-field-error">{{ problemFor("effective_from") }}</p>
					</div>
					<div class="field">
						<label for="kt-assign-to">{{ __("Effective to") }}</label>
						<input id="kt-assign-to" v-model="form.effective_to" class="input" type="date" data-testid="kt-ura-to">
						<p v-if="problemFor('effective_to')" class="kt-field-error">{{ problemFor("effective_to") }}</p>
					</div>
				</div>

				<div v-if="isActing" class="field">
					<label for="kt-assign-authority">{{ __("Authority reference") }}</label>
					<input
						id="kt-assign-authority"
						v-model="form.authority_reference"
						class="input"
						:aria-invalid="problemFor('authority_reference') ? 'true' : 'false'"
						:placeholder="__('Required for Acting assignments')"
						data-testid="kt-ura-authority"
					>
					<p v-if="problemFor('authority_reference')" class="kt-field-error">{{ problemFor("authority_reference") }}</p>
				</div>

				<!-- The server's summary sentence, and the descendant note -->
				<div v-if="preview && preview.summary" class="kt-group" style="margin-top:4px" data-testid="kt-ura-summary">
					<div class="kt-label" style="margin-bottom:4px">{{ __("Responsibility summary") }}</div>
					<p style="margin:0">{{ preview.summary }}</p>
					<p v-if="preview.descendant_count" style="margin:6px 0 0">
						{{ preview.descendant_count === 1
							? __("This includes 1 subordinate organisation unit.")
							: __("This includes {0} subordinate organisation units.", [preview.descendant_count]) }}
					</p>
				</div>

				<!-- The server-detected exclusive office; never an invented client rule -->
				<div v-if="preview && preview.conflict" class="kt-notice is-warning" role="alert" style="align-items:flex-start" data-testid="kt-ura-conflict">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
					<div class="kt-notice-body">
						<strong v-if="preview.conflict.heading" style="display:block;margin-bottom:2px">{{ preview.conflict.heading }}</strong>{{ preview.conflict.message }}
					</div>
				</div>

				<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="kt-ura-assign-error">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ error }}</div>
				</div>
			</div>

			<div class="dialog-actions">
				<span v-if="blockedReason" class="kt-blocked" data-testid="kt-ura-blocked">{{ blockedReason }}</span>
				<button type="button" class="btn btn-secondary" :disabled="busy" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="btn btn-primary"
					:disabled="!canSubmit"
					data-testid="kt-ura-assign-confirm"
					@click="emit('submit', { ...form })"
				>{{ isEdit ? __("Save changes") : __("Assign responsibility") }}</button>
			</div>
		</div>
	</div>
</template>
