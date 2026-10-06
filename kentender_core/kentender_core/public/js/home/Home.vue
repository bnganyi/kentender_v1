<script setup>
// HOME-CHG-001 v0.6 — Home. Ported from design/Home/Home.dc.html (HOME-DES-21 to 29, 21N, 28A-28F);
// the markup is the build source. A Work workspace: read-only apart from navigation and the
// row actions, no next-step block, no journey tracker. Everything it says is made by the
// server (counts, labels, relative times, order, paging); nothing here computes work.
import { nextTick, onMounted, ref, watch } from "vue";
import HomeHeader from "./components/HomeHeader.vue";
import HomeIcon from "./components/HomeIcon.vue";
import HomeRegion from "./components/HomeRegion.vue";
import StatePanel from "./components/StatePanel.vue";
import SummaryColumn from "./components/SummaryColumn.vue";
import { REGION_IDS, useHomeWorkspace } from "./composables/useHomeWorkspace.js";
import { useRouteState } from "./composables/useRouteState.js";

const { phase, data, busy, failed, moreFailed, focusKey, announcement, layout, load, retry, showMore } = useHomeWorkspace();
const { epoch } = useRouteState();
const root = ref(null);

onMounted(() => load());
// The page was shown again on the same route: revalidate in place, no skeleton (AGENTS.md §6.4).
watch(epoch, () => load({ quiet: true }));

// A summary column moves focus to its region and reads nothing (§5.1 item 2, §11).
function focusRegion(name) {
	const heading = root.value && root.value.querySelector("#" + REGION_IDS[name] + "-heading");
	if (heading) heading.focus();
}

// After Show more, focus goes to the first appended row.
watch(focusKey, async (key) => {
	if (!key) return;
	await nextTick();
	const row = root.value && root.value.querySelector('[data-key="' + CSS.escape(key) + '"]');
	if (row) row.focus();
	focusKey.value = "";
});
</script>

<template>
	<div ref="root" class="kt-industry kt-home" data-testid="kt-home-root">
		<div class="kt-home-frame">
			<main class="kt-home-sheet" :aria-busy="phase === 'loading'">
				<template v-if="phase === 'loading'">
					<h1 class="kt-home-title is-plain">{{ __("Home") }}</h1>
					<p class="kt-home-loading" role="status" data-testid="kt-home-loading">{{ __("Loading your work…") }}</p>
				</template>

				<template v-else-if="phase === 'denied'">
					<h1 class="kt-home-title is-plain">{{ __("Home") }}</h1>
					<StatePanel spot="neutral" icon="lock" :text="__('This page is for internal users.')" data-testid="kt-home-denied" />
				</template>

				<template v-else-if="phase === 'failed'">
					<h1 class="kt-home-title is-plain">{{ __("Home") }}</h1>
					<StatePanel spot="error" icon="circle-x" :text="__('We could not load your work.')" data-testid="kt-home-failed">
						<button type="button" class="btn btn-primary" data-testid="kt-home-retry-all" @click="load()">
							<HomeIcon name="refresh-cw" />{{ __("Try again") }}
						</button>
					</StatePanel>
				</template>

				<template v-else-if="data && layout">
					<HomeHeader :viewer="data.viewer" :updated="data.updated" :analytics="data.analytics" />

					<div v-if="layout.columns.length" class="kt-home-summary" :style="{ '--kt-home-columns': layout.columns.length }" data-testid="kt-home-summary">
						<SummaryColumn v-for="column in layout.columns" :key="column.region" :column="column" @focus-region="focusRegion" />
					</div>

					<StatePanel
						v-if="layout.panel === 'empty'"
						class="kt-home-span"
						spot="success"
						icon="circle-check"
						:text="__('Nothing needs your action right now.')"
						data-testid="kt-home-empty"
					/>
					<div v-else-if="layout.panel === 'technical'" class="kt-home-main is-full" data-testid="kt-home-empty-technical">
						<p class="kt-home-nothing"><HomeIcon name="circle-check" />{{ __("Nothing needs your action right now.") }}</p>
					</div>

					<template v-else>
						<div class="kt-home-main" :class="{ 'is-full': layout.railEmpty }" data-testid="kt-home-main">
							<p v-if="layout.mainEmpty" class="kt-home-nothing" data-testid="kt-home-nothing">
								<HomeIcon name="circle-check" />{{ __("Nothing needs your action right now.") }}
							</p>
							<HomeRegion
								v-for="name in layout.main"
								:key="name"
								:name="name"
								:region="data.regions[name]"
								variant="main"
								:busy="!!busy[name]"
								:retry-failed="!!failed[name]"
								:more-failed="!!moreFailed[name]"
								:analytics="data.analytics"
								@retry="retry"
								@more="showMore"
							/>
						</div>
						<aside v-if="!layout.railEmpty" class="kt-home-rail" :aria-label="__('Other work')" data-testid="kt-home-rail">
							<HomeRegion
								v-for="name in layout.rail"
								:key="name"
								:name="name"
								:region="data.regions[name]"
								variant="rail"
								:busy="!!busy[name]"
								:retry-failed="!!failed[name]"
								:more-failed="!!moreFailed[name]"
								:analytics="data.analytics"
								@retry="retry"
								@more="showMore"
							/>
						</aside>
					</template>
				</template>

				<div class="kt-home-sr" role="status" aria-live="polite" data-testid="kt-home-live">{{ announcement }}</div>
			</main>
		</div>
	</div>
</template>
