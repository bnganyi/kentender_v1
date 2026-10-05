<script setup>
// Ported from design/Home/Home.dc.html — the main-column work row of HOME-DES-21:
// line 1 the module chip, the title in bold, then the module name and the reference as quiet
// text; line 2 the action and its timing (in Coming up a tinted badge and the exact time);
// a warning callout on its own line for a reason; one action at the right — Continue
// (primary on the first row, standard on the others) in My work, the text link View record
// elsewhere (or the owner's own named link, such as View report, when the entry carries one). "Your turn, blocked" shows only on blocked work (§5.1 item 7).
import HomeIcon from "./HomeIcon.vue";
import { moduleIcon } from "../homeModules.js";
import { followLink, hrefOf, openDestination } from "../composables/openDestination.js";

const props = defineProps({
	entry: { type: Object, required: true },
	region: { type: String, required: true }, // my_work | coming_up | oversight (when promoted to the main column)
});
</script>

<template>
	<div class="kt-home-row" :data-key="props.entry.key" tabindex="-1" data-testid="kt-home-row">
		<span class="kt-icon-chip kt-home-chip-main" :title="entry.module"><HomeIcon :name="moduleIcon(entry.owner)" /></span>
		<div class="kt-home-row-body">
			<div class="kt-home-line">
				<span class="kt-home-row-title">{{ entry.title }}</span>
				<span class="kt-home-quiet">{{ entry.module }}</span>
				<span v-if="entry.reference" class="kt-home-quiet">{{ entry.reference }}</span>
			</div>
			<div class="kt-home-line is-centered">
				<span class="kt-home-action">{{ entry.action }}</span>
				<span v-if="entry.blocked" class="kt-status is-attention">{{ __("Your turn, blocked") }}</span>
				<template v-if="region === 'coming_up'">
					<span class="kt-home-badge">{{ entry.badge }}</span>
					<span class="kt-home-quiet">{{ entry.exact }}</span>
				</template>
				<template v-else>
					<span v-if="entry.timing" class="kt-home-quiet">{{ entry.timing }}</span>
					<span v-if="entry.due" class="kt-home-quiet">{{ entry.due }}</span>
					<span v-if="entry.fact" class="kt-home-quiet" data-testid="kt-home-fact">{{ entry.fact }}</span>
				</template>
			</div>
			<div v-if="entry.reason" class="kt-home-callout" data-testid="kt-home-reason">
				<HomeIcon name="triangle-alert" size="sm" />
				<span>{{ entry.reason }}</span>
			</div>
		</div>
		<div class="kt-home-row-action">
			<button
				v-if="region === 'my_work'"
				type="button"
				class="btn"
				:class="entry.primary ? 'btn-primary' : 'btn-secondary'"
				:aria-label="__('Continue: {0}', [entry.title])"
				data-testid="kt-home-continue"
				@click="openDestination(entry.destination)"
			>
				{{ __("Continue") }}
			</button>
			<a
				v-else
				:href="hrefOf(entry.link ? entry.link.destination : entry.destination)"
				class="kt-home-link"
				:aria-label="(entry.link ? entry.link.label : __('View record')) + ': ' + entry.title"
				data-testid="kt-home-view"
				@click="followLink($event, entry.link ? entry.link.destination : entry.destination)"
			>
				{{ entry.link ? entry.link.label : __("View record") }}<HomeIcon name="arrow-right" size="sm" />
			</a>
		</div>
	</div>
</template>
