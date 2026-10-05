<!-- "Correct" on an attendee row (board c4): the recorder records that the
     person left, or corrects whom they said they represent. The boards draw
     only the button; this dialog is a registered departure. -->
<template>
	<div class="dialog-backdrop" data-testid="bop-attendance-dialog" @keydown.esc.stop="$emit('cancel')">
		<div ref="dialogEl" class="dialog bop-dialog" role="dialog" aria-modal="true" aria-labelledby="bop-attendance-title" tabindex="-1">
			<div id="bop-attendance-title" class="dialog-title">Correct attendance</div>
			<div class="bop-dialog-body">
				<div class="field"><label for="bop-attendance-name">Attendee</label><input id="bop-attendance-name" v-model="name" class="input"></div>
				<div class="field"><label for="bop-attendance-capacity">Attended as</label>
					<select id="bop-attendance-capacity" v-model="capacity" class="input"><option>Tenderer representative</option><option>Public observer</option></select></div>
				<div v-if="capacity === 'Tenderer representative'" class="field"><label for="bop-attendance-represents">Says they represent</label><input id="bop-attendance-represents" v-model="represents" class="input"></div>
				<div class="field"><label for="bop-attendance-movement">What to record</label>
					<select id="bop-attendance-movement" v-model="movement" class="input" data-testid="bop-attendance-movement"><option value="Departure">They left the opening</option><option value="Arrival">They are present</option></select></div>
				<div class="field"><label for="bop-attendance-at">Time (as you saw it)</label><input id="bop-attendance-at" v-model="at" class="input" placeholder="hh:mm:ss"></div>
			</div>
			<div class="dialog-actions">
				<button type="button" class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="btn btn-primary" :disabled="pending || !name.trim()" data-testid="bop-attendance-confirm" @click="confirm">Record attendance</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

const props = defineProps({ attendee: { type: Object, required: true }, pending: Boolean, day: { type: String, default: "" } });
const emit = defineEmits(["confirm", "cancel"]);
const dialogEl = ref(null);
const name = ref(props.attendee.person_name || "");
const capacity = ref(props.attendee.represents ? "Tenderer representative" : "Public observer");
const represents = ref(props.attendee.represents || "");
const movement = ref("Departure");
const at = ref("");
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
function confirm() {
	emit("confirm", { person_name: name.value.trim(), capacity: capacity.value, movement: movement.value, represented_tenderer: represents.value.trim(), reported_at: at.value.trim() });
}
</script>
