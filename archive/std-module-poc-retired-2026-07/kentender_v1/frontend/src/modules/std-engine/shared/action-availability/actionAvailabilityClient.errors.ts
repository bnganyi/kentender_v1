import type { ActionAvailabilityApiErrorEnvelope } from "./actionAvailability.types";

/** Thrown when SEC-0410 returns `success: false` or the client cannot parse the envelope. */
export class ActionAvailabilityClientError extends Error {
	readonly envelope: ActionAvailabilityApiErrorEnvelope;

	constructor(envelope: ActionAvailabilityApiErrorEnvelope) {
		super(envelope.message);
		this.name = "ActionAvailabilityClientError";
		this.envelope = envelope;
	}
}
