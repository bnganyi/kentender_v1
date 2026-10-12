/**
 * Structure the design system itself no longer draws, that the module artboards still do.
 *
 * Module artboards are exported once, from the pack of their day, and are re-exported only when a
 * change unit reopens them. When the Project Owner approves a revision of the design system, every
 * board that draws the old form differs from the built screens until it is re-exported, and a
 * per-board entry for each would be hundreds of copies of one decision. A revision is recorded here
 * once instead, with its authority, and applies to every board. Retire an entry when the boards are
 * re-exported: it exists only because they are not.
 *
 * Matching is by the end of the path, so the omission is found wherever the container sits.
 * Only an omission can be recorded here (something the boards draw and the build no longer does);
 * a build addition still needs the module's own registry entry.
 */
export const DESIGN_SYSTEM_OMISSIONS = [
	{
		// A blocked next step is a 3px warning rule over the warning tint with no icon.
		endsWith: "notice+next-step.is-warning > notice-icon",
		because:
			"DS-REV-004 draws the blocked next step as a 3px warning rule over the warning tint, square on the rule side, with no icon; " +
			"the boards drawn before it show a warning notice with an icon.",
		authority: "DS-REV-004, Project Owner approval of 6 October 2026 (\"2e it is. Approved\")",
	},
];
