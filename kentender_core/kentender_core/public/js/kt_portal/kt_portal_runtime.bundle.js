// The public portal runtime bundle (BDS-CHG-001 v0.8 plan OD-B). Loaded by
// templates/kt_portal/base.html after frappe-web.bundle.js and before the
// surface's own bundle, which registers through
// kentender_core.portal_page.register(...). See ./runtime.js for the contract.
import { createPortalRuntime } from "./runtime.js";

window.kentender_core = window.kentender_core || {};
window.kentender_core.portal_page = window.kentender_core.portal_page || createPortalRuntime(window);
