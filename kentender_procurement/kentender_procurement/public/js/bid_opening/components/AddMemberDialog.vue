<!-- "Add members" (the record picker board, item 14, approved 14 October 2026): the Accounting Officer finds people in the
     picker on the left, each choice adds the person to "To appoint" on the right without closing anything, each person's role
     is set in that list, and one action appoints them all. It replaces one trip through a dialog per member.

     The page's committee table (boards a1 and a2) still holds what is already drafted: a refused appointment leaves its people
     there, and the dialog treats them as already on the committee. The dialog draws no board of its own (the boards draw only
     the button); it is a registered departure (tests/ui/fidelity/departures/bid-opening.js).

     People are searched on the server (source bid_opening.committee_member). The list cannot depend on one role, because each
     person has their own: a row says whether that person could not be the independent member (`extra.independent_blocker`),
     and the dialog shows it beside the person when that role is chosen. The command checks everyone again. -->
<template>
	<div class="dialog-backdrop" data-testid="bop-add-member-dialog" @keydown.esc.stop="$emit('cancel')">
		<div ref="dialogEl" class="dialog bop-dialog is-wide" role="dialog" aria-modal="true" aria-labelledby="bop-add-member-title" tabindex="-1">
			<div id="bop-add-member-title" class="dialog-title">Add members</div>
			<div class="bop-members-grid">
				<div class="field"><label for="bop-add-member-person">Find people</label>
					<RecordPickerHost
						ref="picker"
						input-id="bop-add-member-person"
						source="bid_opening.committee_member"
						noun="person"
						plural="people"
						placeholder="Search by name, role or department"
						inline
						multiple
						staged-noun="to appoint"
						:context="context"
						:staged="stagedIds"
						@add="onAdd"
					/>
				</div>
				<div class="bop-staged">
					<div class="bop-staged-title" data-testid="bop-staged-title">{{ stagedTitle }}</div>
					<div v-if="!staged.length" class="bop-staged-empty" data-testid="bop-staged-empty">People you choose appear here.</div>
					<div v-else class="bop-staged-rows" data-testid="bop-staged">
						<div v-for="m in staged" :key="m.user" class="bop-staged-row" :data-user="m.user">
							<div class="bop-staged-who">
								<span class="bop-staged-name">{{ m.full_name }}</span>
								<span class="bop-staged-detail">{{ m.detail }}</span>
								<span v-if="problemFor(m)" class="bop-field-error bop-staged-error" role="alert" :data-testid="`bop-staged-error-${m.user}`">{{ problemFor(m) }}</span>
							</div>
							<select v-model="m.committee_role" class="input bop-staged-role" :aria-label="`Role for ${m.full_name}`" :data-testid="`bop-staged-role-${m.user}`">
								<option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
							</select>
							<button type="button" class="btn btn-ghost bop-staged-remove" :aria-label="`Remove ${m.full_name}`" :data-testid="`bop-staged-remove-${m.user}`" @click="remove(m.user)">Remove</button>
						</div>
					</div>
				</div>
			</div>
			<div class="dialog-actions bop-members-actions">
				<span class="bop-members-note" role="status" data-testid="bop-add-members-note" :class="{ 'is-error': !!error }">{{ error || (pending ? "Appointing…" : "") }}</span>
				<button type="button" class="btn btn-secondary" :disabled="pending" data-testid="bop-add-members-cancel" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="btn btn-primary" :disabled="!canAppoint" data-testid="bop-add-member-confirm" @click="appoint">{{ appointLabel }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import RecordPickerHost from "../../record_picker_shared/RecordPickerHost.vue";

const props = defineProps({
	tender: { type: String, required: true },
	// What the page's table already holds (a refused appointment leaves its people there).
	draft: { type: Array, default: () => [] },
	pending: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
const emit = defineEmits(["appoint", "cancel"]);
const roles = ["Chair and recorder", "Chair", "Recorder", "Member", "Independent member"];
const CHAIRS = ["Chair and recorder", "Chair"];
const INDEPENDENT = "Independent member";

const dialogEl = ref(null);
const picker = ref(null);
const staged = ref([]);

const stagedIds = computed(() => staged.value.map((m) => m.user));
const context = computed(() => ({ tender: props.tender, taken: props.draft.map((d) => d.user) }));
const total = computed(() => props.draft.length + staged.value.length);
const stagedTitle = computed(() => (staged.value.length ? `To appoint · ${staged.value.length}` : "To appoint"));
const appointLabel = computed(() => (total.value === 0 ? "Appoint members" : total.value === 1 ? "Appoint 1 member" : `Appoint ${total.value} members`));
const problemFor = (m) => (m.committee_role === INDEPENDENT ? m.independent_blocker : "");
const canAppoint = computed(() => !props.pending && staged.value.length > 0 && !staged.value.some(problemFor));

// A first person is suggested as chair and recorder, and the next as the independent member, until the committee has them.
function suggestedRole() {
	const roleOf = [...props.draft, ...staged.value].map((m) => m.committee_role);
	if (!roleOf.some((r) => CHAIRS.includes(r))) return "Chair and recorder";
	if (!roleOf.includes(INDEPENDENT)) return INDEPENDENT;
	return "Member";
}

function onAdd(row) {
	if (staged.value.some((m) => m.user === row.id)) return;
	const extra = row.extra || {};
	staged.value.push({
		user: row.id,
		full_name: row.label,
		detail: row.detail,
		designation: extra.designation || "",
		independent_blocker: extra.independent_blocker || "",
		committee_role: suggestedRole(),
	});
}
function remove(user) {
	staged.value = staged.value.filter((m) => m.user !== user);
	nextTick(() => picker.value && picker.value.focus());
}
function appoint() {
	// the page's table shows the designation on its own: the source sends it as a fact (`extra`), apart from the text beneath the name
	emit("appoint", staged.value.map((m) => ({ user: m.user, committee_role: m.committee_role, full_name: m.full_name, designation: m.designation })));
}
onMounted(() => nextTick(() => (picker.value ? picker.value.focus() : dialogEl.value && dialogEl.value.focus())));
</script>
