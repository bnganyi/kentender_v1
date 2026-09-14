<script setup>
// STR-DES-03 (Approval details) / STR-DES-06 (Submission authority) /
// STR-DES-09 (Submission and history) — the v1.8 .kt-timeline component:
// one row per event, newest first, readable event label, actor and instant.
// Stored actions stay verbatim in the row's data attribute (§4.7).
defineProps({
	events: { type: Array, required: true },
	// Show the recorded reason under an event that carries one (Return).
	showReason: { type: Boolean, default: true },
});
</script>

<template>
	<div class="kt-timeline" style="border: none; padding: 0" data-testid="str-timeline">
		<div v-for="(event, index) in events" :key="index" class="kt-timeline-row" data-testid="str-history-row" :data-event="event.event">
			<div class="kt-timeline-dot-col">
				<div class="kt-timeline-dot" :class="event.tone || 'is-draft'"></div>
				<div v-if="index < events.length - 1" class="kt-timeline-line"></div>
			</div>
			<div class="kt-timeline-item" :style="index === events.length - 1 ? 'padding-bottom: 0' : ''">
				<div class="kt-timeline-item-title">{{ event.event_label || event.event }}</div>
				<div class="kt-timeline-item-meta">{{ event.at_label || event.at }}<template v-if="event.actor_name || event.actor"> &middot; {{ event.actor_name || event.actor }}</template></div>
				<div v-if="showReason && event.reason" style="font-size: 13px; margin-top: 4px" data-testid="str-history-reason">{{ event.reason }}</div>
			</div>
		</div>
		<p v-if="!events.length" class="kt-muted" style="margin: 0">{{ __("No events recorded yet.") }}</p>
	</div>
</template>
