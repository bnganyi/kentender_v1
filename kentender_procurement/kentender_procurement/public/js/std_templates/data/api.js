// STD Templates data adapter — one function per whitelisted endpoint
// (kentender_procurement.std_templates.api). Reads return outcome data
// (OK / FORBIDDEN / NOT_FOUND); nothing here reconstructs a projection.
import { frappeCall } from "../../tnd_shared/frappeCall.js";

const M = "kentender_procurement.std_templates.api.";

export const getAccess = () => frappeCall(M + "get_std_templates_access", {});
export const getReleases = ({ search, status }) => frappeCall(M + "get_std_templates", { search: search || "", status: status || "" });
export const getRelease = (releaseId) => frappeCall(M + "get_std_template", { release_id: releaseId });
export const getCoverage = (releaseId, { search, treatment, page }) =>
	frappeCall(M + "get_std_template_coverage", { release_id: releaseId, search: search || "", treatment: treatment || "", page: page || 1, page_length: 25 });
export const getChanges = (releaseId, { category, page }) =>
	frappeCall(M + "get_std_template_changes", { release_id: releaseId, category: category || "", page: page || 1, page_length: 25 });
export const reportConcern = (releaseId, values) => frappeCall(M + "report_std_template_concern", { release_id: releaseId, concern_values: JSON.stringify(values) });

export function previewUrl(releaseId, outputId) {
	return `/api/method/${M}preview_std_template_document?release_id=${encodeURIComponent(releaseId)}&output_id=${encodeURIComponent(outputId)}`;
}
export function reviewPackUrl(releaseId) {
	return `/api/method/${M}download_std_template_review_pack?release_id=${encodeURIComponent(releaseId)}`;
}

export async function uploadEvidence(file) {
	const data = new FormData();
	data.append("file", file, file.name);
	data.append("is_private", "1");
	data.append("folder", "Home/Attachments");
	const response = await fetch("/api/method/upload_file", { method: "POST", body: data, headers: { "X-Frappe-CSRF-Token": window.frappe.csrf_token } });
	const body = await response.json().catch(() => ({}));
	if (!response.ok || !body.message || !body.message.name) throw new Error("The file could not be uploaded. Try again.");
	return body.message.name;
}
