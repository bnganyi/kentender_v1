<!-- One place for everything a task needs the requester to look at (REQ-CHG-001
     v1.17 §13.4A). Every finding is said once, here, in one warning-toned panel
     at the top of the task; the row, section or field it concerns carries only
     a quiet "Needs attention" marker, and choosing a finding goes to it. The
     same panel is used on Request details, Requirements and Review and submit,
     so an issue looks the same wherever it is found.

     `items` are { message, advisory?, go? }: `advisory` marks a note that does
     not block; `go` is whatever the page needs to take the reader to the place
     (kept opaque here and handed back with the `go` event). `stale` says the
     findings describe the last saved draft, not what is being typed. -->
<template>
	<Notice v-if="items.length" tone="warning">
		<div class="req-attention" data-testid="req-attention" :class="{ 'is-stale': stale }">
			<div class="req-attention-head" data-testid="req-attention-head">{{ heading }}</div>
			<ul class="req-attention-list">
				<li v-for="(item, i) in items" :key="i" data-testid="req-attention-item">
					<span v-if="item.advisory" class="req-attention-tag">Note</span>
					<button v-if="item.go" type="button" class="req-attention-link" @click="$emit('go', item.go)">{{ item.message }}</button>
					<span v-else>{{ item.message }}</span>
				</li>
			</ul>
		</div>
	</Notice>
</template>

<script setup>
import { computed } from "vue";
import Notice from "./Notice.vue";

const props = defineProps({ items: { type: Array, default: () => [] }, stale: { type: Boolean, default: false } });
defineEmits(["go"]);

const heading = computed(() => {
	const blocking = props.items.filter((i) => !i.advisory).length;
	const base = blocking
		? blocking === 1 ? "1 thing needs attention" : `${blocking} things need attention`
		: "For your attention";
	return props.stale ? `${base} in the last saved draft` : base;
});
</script>
