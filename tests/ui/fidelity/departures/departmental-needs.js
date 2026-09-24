/**
 * Structure Departmental Needs builds that its board does not draw.
 *
 * `NDS Artboards.dc.html` is an earlier export than Planning's boards and
 * carries almost none of the container vocabulary — `.kt-page`, `.kt-region`,
 * `.kt-group`, `.kt-field`, `.kt-table` appear nowhere in it, because those
 * names were extracted from this very board afterwards. So the board contract
 * here is thin by nature, and most of this module's structural assurance comes
 * from the shared-vocabulary rules in the spec beside this file.
 *
 * Same shape as the Planning registry: what, why, and who decided.
 */
export const DEPARTURES = {
	"NeedEditorScreen#NDS-DES-04": [
		{
			omits: ["disclosure > disclosure-body"],
			because:
				"The board's static `<details>` is drawn unfolded for illustration; the live " +
				"disclosure is correctly collapsed until asked for, so its body has no counterpart " +
				"until a reader opens it. The same exemption already exists on the landmark gate.",
			authority: "KT-STD-001 §2.6.4 — a disclosure opens on request",
		},
		{
			path: "meta-row.is-tight",
			because:
				"The record's own context — department, financial year, revision — which NDS-DES-04's " +
				"fixture states in its caption rather than in the sheet. NDS-DES-15-SINGLE draws the " +
				"same row for the same editor.",
			authority: "NDS Artboards NDS-DES-15-SINGLE",
		},
		{
			path: "field",
			because:
				"The editor offers the department and financial year as fields in the states where " +
				"the author may still choose them; NDS-DES-04's returned correction has both already " +
				"fixed, so its board draws six fields where the component can render eight.",
			authority: "NDS Artboards NDS-DES-15-MULTIPLE",
		},
	],
};
