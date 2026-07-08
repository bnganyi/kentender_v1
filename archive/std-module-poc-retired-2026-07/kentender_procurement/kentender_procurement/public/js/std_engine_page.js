// STD-LIB-0001 / STD-LIB-0100 — Desk Page `std-engine`: library shell (default + `/library`);
// `advanced` → Page std-engine-advanced (catalogue). See std_library_shell.js (+ std_library_import_wizard_shell.js).
(function () {
	function segment() {
		const r = frappe.get_route() || [];
		return String(r[1] || "")
			.toLowerCase()
			.trim();
	}
	function subsegment() {
		const r = frappe.get_route() || [];
		return String(r[2] || "")
			.toLowerCase()
			.trim();
	}

	function is_std_engine_route() {
		const r = frappe.get_route() || [];
		return r[0] === "std-engine";
	}

	function should_show_library_shell() {
		if (!is_std_engine_route()) {
			return false;
		}
		const seg = segment();
		if (seg === "advanced") {
			return false;
		}
		return (seg === "" || seg === "library") && subsegment() !== "import";
	}

	function should_show_import_shell() {
		if (!is_std_engine_route()) {
			return false;
		}
		return segment() === "library" && subsegment() === "import";
	}

	function normalize_library_route() {
		if (!is_std_engine_route()) {
			return;
		}
		const seg = segment();
		if (seg === "") {
			frappe.set_route("std-engine", "library");
		}
	}

	function mount_library_shell() {
		const wrap =
			frappe.pages["std-engine"] ||
			document.getElementById("page-std-engine");
		if (!wrap || !kentender_procurement?.std_library_shell?.mountInto) {
			return;
		}
		kentender_procurement.std_library_shell.mountInto(wrap);
	}
	function mount_import_shell() {
		const wrap =
			frappe.pages["std-engine"] ||
			document.getElementById("page-std-engine");
		if (!wrap || !kentender_procurement?.std_library_shell?.mountImportInto) {
			return;
		}
		kentender_procurement.std_library_shell.mountImportInto(wrap);
	}

	function run_std_engine_route() {
		if (!is_std_engine_route()) {
			return;
		}
		const seg = segment();
		if (seg === "advanced") {
			frappe.set_route("std-engine-advanced");
			return;
		}
		if (should_show_import_shell()) {
			frappe.after_ajax(() => mount_import_shell());
			return;
		}
		if (!should_show_library_shell()) {
			return;
		}
		normalize_library_route();
		if (segment() !== "library") {
			return;
		}
		frappe.after_ajax(() => mount_library_shell());
	}

	function bind_page_show() {
		const wrap =
			frappe.pages["std-engine"] ||
			document.getElementById("page-std-engine");
		if (!wrap || wrap._kentender_std_library_show_bound) {
			return;
		}
		wrap._kentender_std_library_show_bound = true;
		$(wrap).on("show", function () {
			if (should_show_import_shell()) {
				frappe.after_ajax(() => mount_import_shell());
				return;
			}
			if (should_show_library_shell() && segment() === "library") {
				frappe.after_ajax(() => mount_library_shell());
			}
		});
	}

	$(document).on("page-change", function () {
		run_std_engine_route();
		bind_page_show();
	});
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", function () {
			run_std_engine_route();
			bind_page_show();
		});
	}
	setTimeout(function () {
		run_std_engine_route();
		bind_page_show();
	}, 0);
})();
