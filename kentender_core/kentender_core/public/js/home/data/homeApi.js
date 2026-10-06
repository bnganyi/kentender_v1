// Thin wrapper over kentender_core.api.home. Every authority check, count, order,
// window, label and phrase is made server-side (HOME §16); this module only shapes
// the call. `regions` limits the read (a retry, or Show more with a cursor).
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.home.";

export const homeApi = {
	load: (regions, cursors) =>
		frappeCall(PREFIX + "get_home_workspace", {
			...(regions ? { regions: JSON.stringify(regions) } : {}),
			...(cursors ? { cursors: JSON.stringify(cursors) } : {}),
		}),
};
