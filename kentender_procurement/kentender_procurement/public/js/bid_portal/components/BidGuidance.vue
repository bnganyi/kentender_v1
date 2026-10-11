<script setup>
// The bid journey and next step on every bid page (BDS-CHG-001 v0.12 §10.19),
// with what a next-step fix does decided once. The server names each fix as a
// route (`target`) or a command (`fix_id`); a route is left to the screen
// (`fix`), because only the screen knows where it already is. The commands a
// bid page can be sent are done here, so a fix works wherever the block is
// drawn and not only on the Submit screen:
//   - check_certificate: a fresh trust-service read; says the result under the
//     block, then asks the screen to re-read (`reload`);
//   - submit_bid: confirming a submission is the Submit screen's own dialog,
//     so it goes there;
//   - contact_support: the support link the page was read with.
// `tracker` is false on a page that already shows where the bidder is among the
// five tasks (the task stepper): the formal journey is not drawn beside it, so
// "Step 3 of 5" and "Stage 2 of 3" never stand in competition. The next step
// still is.
import { computed, inject, onMounted, onUnmounted, ref } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";

const API = "kentender_procurement.bid_submission.api.";
const props = defineProps({
	journey: { type: Object, default: null },
	answer: { type: Object, default: null },
	reference: { type: String, default: "" },
	bidReference: { type: String, default: "" },
	organisation: { type: String, default: "" },
	supportHref: { type: String, default: "" },
	tracker: { type: Boolean, default: true },
});
const emit = defineEmits(["fix", "reload"]);
const portal = inject("portal");
const { route, go } = portal.useRoute({ ref, onMounted, onUnmounted });
const note = ref("");
const busy = ref(false);

const shownJourney = computed(() => (props.tracker ? props.journey : null));

async function onFix(fix) {
	if (fix && fix.fix_id === "check_certificate" && props.bidReference) {
		busy.value = true;
		try {
			const result = await portal.call(API + "check_certificate", { bid_reference: props.bidReference, organisation: props.organisation });
			note.value = (result && result.text) || "";
			emit("reload");
		} finally {
			busy.value = false;
		}
		return;
	}
	if (fix && fix.fix_id === "submit_bid" && props.reference && route.value.path !== `/tenders/${props.reference}/bid/submit`) {
		go(`/tenders/${props.reference}/bid/submit`);
		return;
	}
	if (fix && fix.fix_id === "contact_support" && props.supportHref) {
		window.location.assign(props.supportHref);
		return;
	}
	emit("fix", fix);
}
</script>

<template>
	<PortalGuidance :journey="shownJourney" :answer="answer" :label="__('Bid journey')" :pending="busy" @fix="onFix" />
	<p v-if="note" class="bds-muted" role="status" data-testid="bds-certificate-check">{{ note }}</p>
</template>
