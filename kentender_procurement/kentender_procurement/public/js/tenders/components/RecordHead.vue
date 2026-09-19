<!-- The record header every TPR-DES-03..12 board opens with: h1 + status
     pill, the reference line, an optional lede, and an optional right-hand
     control (TPR-DES-09's "View public Tender"). -->
<template>
	<div class="tnd-head" :class="{ 'tnd-head--split': $slots.aside }">
		<div>
			<div class="tnd-title-row">
				<h1 class="tnd-h1" data-testid="tnd-record-title">{{ title }}</h1>
				<span v-if="badge" class="kt-status" :class="badgeClass" data-testid="tnd-record-badge">{{ badge }}</span>
			</div>
			<p class="tnd-refs" :class="{ 'tnd-refs--last': !lede }" data-testid="tnd-record-refs">{{ refs }}</p>
			<p v-if="lede" class="tnd-lede">{{ lede }}</p>
		</div>
		<slot name="aside" />
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	title: { type: String, default: "" },
	badge: { type: String, default: "" },
	badgeTone: { type: String, default: "" },
	refs: { type: String, default: "" },
	lede: { type: String, default: "" },
});

// Badge tone from the server's own status vocabulary (§11.7).
const TONES = [
	[/^draft/i, "is-draft"],
	[/awaiting|required|ready to issue|needs attention/i, "is-attention"],
	[/published|complete|issued|answered|open/i, "is-live"],
	[/cancelled|correction requested|late/i, "is-critical"],
	[/ended|not started|selected/i, "is-pending"],
];
const badgeClass = computed(() => {
	if (props.badgeTone) return props.badgeTone;
	const hit = TONES.find(([re]) => re.test(props.badge));
	return hit ? hit[1] : "is-draft";
});
</script>
