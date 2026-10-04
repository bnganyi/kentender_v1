// REQ-DES-12 "Uncertain decision result" (§13.13): when a decision request
// fails without a definite answer (the connection dropped or the server
// errored), the page must not offer a second decision blindly. It re-reads the
// record: if the decision is now recorded it says so; otherwise it states the
// retry-safe message. A refusal the server did state (a §11 code) is shown as
// that refusal, not as uncertainty.
import { ref } from "vue";

export const CHECKING = "Checking whether your action completed…";
export const RETRY_SAFE = "The result could not be confirmed. Check the current requisition before trying again.";

export function useDecision(ctx) {
	// "" | "checking" | "committed" | "unconfirmed"
	const uncertain = ref("");
	const committedText = ref("");

	function isUncertain(error) {
		if (!error || error.code) return false;
		return !error.httpStatus || error.httpStatus >= 500;
	}

	async function decide(label, fn, { committed, text }) {
		uncertain.value = "";
		const done = await ctx.run(label, fn);
		if (done) return done;
		if (!isUncertain(ctx.commandError.value)) return null;
		uncertain.value = "checking";
		ctx.clearError();
		await ctx.reload();
		if (committed()) {
			committedText.value = text;
			uncertain.value = "committed";
		} else {
			uncertain.value = "unconfirmed";
		}
		return null;
	}

	return { uncertain, committedText, decide };
}
