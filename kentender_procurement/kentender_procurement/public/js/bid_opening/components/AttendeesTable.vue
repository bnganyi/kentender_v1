<!-- "Attendees" (boards c1–c4): who joined and whom they say they represent.
     In session (c4) each row is present or left, and the recorder can correct it. -->
<template>
	<div class="kt-region" :class="{ 'is-secondary': secondary }"><h2>Attendees</h2>
		<table class="kt-table" data-testid="bop-attendees"><thead><tr><th>Attendee</th><th>Says they represent</th><th>Joined</th><template v-if="inSession"><th>In session</th><th></th></template></tr></thead><tbody>
			<tr v-for="(a, i) in attendees" :key="i"><td>{{ a.person_name }}</td><td>{{ a.represents || "No one (public observer)" }}</td><td>{{ a.joined_label }}</td>
				<template v-if="inSession"><td><span class="kt-status is-live">Present</span></td><td><button v-if="canCorrect" type="button" class="kt-btn kt-btn-ghost" :data-testid="`bop-attendee-correct-${i}`" @click="$emit('correct', a)">Correct</button></td></template></tr>
		</tbody></table>
		<p v-if="!attendees.length" style="margin:10px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty" data-testid="bop-attendees-none">No attendees have joined.</p>
		<p v-if="note" style="margin:10px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ note }}</p>
	</div>
</template>

<script setup>
defineProps({ attendees: { type: Array, default: () => [] }, secondary: Boolean, inSession: Boolean, canCorrect: Boolean, note: { type: String, default: "" } });
defineEmits(["correct"]);
</script>
