/**
 * KenTender Desk field-error helper.
 *
 * Contract: write APIs return { ok: false, errors: { field: message } } for
 * user-correctable validation. Callers apply errors inline — never frappe.msgprint
 * for missing/invalid fields.
 *
 * Global: window.ktFormErrors (also kentender.formErrors when kentender exists).
 */
(function (window, $) {
	"use strict";

	var DEFAULTS = {
		errorAttr: "data-kt-field-error",
		/** Strategy alias supported when present */
		errorAttrAliases: ["data-kt-str-error"],
		invalidClass: "kt-field-invalid",
		invalidClassAliases: ["kt-str-field-invalid"],
		fieldAttr: "data-kt-field",
		fieldAttrAliases: ["data-kt-str-field", "name"],
	};

	function _opts(opts) {
		return Object.assign({}, DEFAULTS, opts || {});
	}

	function _errorSelectors(o) {
		var attrs = [o.errorAttr].concat(o.errorAttrAliases || []);
		return attrs.map(function (a) {
			return "[" + a + "]";
		});
	}

	function _findErrorSlot($root, field, o) {
		var attrs = [o.errorAttr].concat(o.errorAttrAliases || []);
		for (var i = 0; i < attrs.length; i++) {
			var $slot = $root.find("[" + attrs[i] + '="' + field + '"]');
			if ($slot.length) {
				return $slot.first();
			}
		}
		return $();
	}

	function _findFieldControl($root, field, o) {
		var attrs = [o.fieldAttr].concat(o.fieldAttrAliases || []);
		for (var i = 0; i < attrs.length; i++) {
			var $el = $root.find("[" + attrs[i] + '="' + field + '"]');
			if ($el.length) {
				return $el.first();
			}
		}
		// Drawer fields often use name= on the control inside data-kt-str-drawer-field
		var $drawer = $root.find('[data-kt-str-drawer-field="' + field + '"]');
		if ($drawer.length) {
			var $ctrl = $drawer.find("input, select, textarea").first();
			if ($ctrl.length) {
				return $ctrl;
			}
		}
		return $();
	}

	function _clearAria($ctrl) {
		var id = $ctrl.attr("data-kt-error-describedby");
		if (id) {
			var parts = ($ctrl.attr("aria-describedby") || "")
				.split(/\s+/)
				.filter(function (p) {
					return p && p !== id;
				});
			if (parts.length) {
				$ctrl.attr("aria-describedby", parts.join(" "));
			} else {
				$ctrl.removeAttr("aria-describedby");
			}
			$ctrl.removeAttr("data-kt-error-describedby");
		}
		$ctrl.removeAttr("aria-invalid");
	}

	function clear($root, opts) {
		if (!$root || !$root.length) {
			return;
		}
		var o = _opts(opts);
		_errorSelectors(o).forEach(function (sel) {
			$root.find(sel).addClass("hidden").attr("hidden", "hidden").text("");
		});
		var classes = [o.invalidClass].concat(o.invalidClassAliases || []).join(" ");
		var $ctrls = $root
			.find("input, select, textarea, [" + o.fieldAttr + "]")
			.add($root.find("[data-kt-str-field], [data-kt-str-drawer-field] :is(input, select, textarea)"));
		$ctrls.removeClass(classes);
		$root.find("[aria-invalid='true'], [data-kt-error-describedby]").each(function () {
			_clearAria($(this));
		});
	}

	function show($root, errors, opts) {
		if (!$root || !$root.length) {
			return;
		}
		var o = _opts(opts);
		clear($root, o);
		var map = errors || {};
		var firstFocus = null;
		Object.keys(map).forEach(function (field) {
			var msg = map[field] || "";
			var $slot = _findErrorSlot($root, field, o);
			var slotId = "";
			if ($slot.length) {
				$slot.text(msg).removeClass("hidden").removeAttr("hidden");
				slotId = $slot.attr("id") || "kt-field-error-" + field;
				$slot.attr("id", slotId);
			}
			var $ctrl = _findFieldControl($root, field, o);
			if ($ctrl.length) {
				var classes = [o.invalidClass].concat(o.invalidClassAliases || []);
				$ctrl.addClass(classes.join(" "));
				$ctrl.attr("aria-invalid", "true");
				if (slotId) {
					var described = ($ctrl.attr("aria-describedby") || "")
						.split(/\s+/)
						.filter(Boolean);
					if (described.indexOf(slotId) === -1) {
						described.push(slotId);
					}
					$ctrl.attr("aria-describedby", described.join(" "));
					$ctrl.attr("data-kt-error-describedby", slotId);
				}
				if (!firstFocus) {
					firstFocus = $ctrl;
				}
			}
		});
		if (firstFocus && firstFocus.length) {
			try {
				var el = firstFocus.get(0);
				if (el && typeof el.scrollIntoView === "function") {
					el.scrollIntoView({ block: "nearest", behavior: "smooth" });
				}
				firstFocus.trigger("focus");
			} catch (e) {
				/* ignore focus failures */
			}
		}
	}

	/**
	 * Best-effort parse of Frappe throw / MandatoryError into a field map.
	 * Prefer structured {ok:false, errors} from the API; this is a fallback only.
	 */
	function fromFrappeError(err) {
		var out = {};
		if (!err) {
			return out;
		}
		var messages = [];
		try {
			if (err._server_messages) {
				var raw = err._server_messages;
				if (typeof raw === "string") {
					raw = JSON.parse(raw);
				}
				(raw || []).forEach(function (m) {
					var obj = typeof m === "string" ? JSON.parse(m) : m;
					if (obj && obj.message) {
						messages.push(String(obj.message));
					}
				});
			}
		} catch (e) {
			/* ignore */
		}
		if (err.message) {
			messages.push(String(err.message));
		}
		if (typeof err === "string") {
			messages.push(err);
		}
		messages.forEach(function (msg) {
			// "Value missing for Performance Target: Benefit Owner"
			var m = msg.match(/Value missing for [^:]+:\s*(.+)$/i);
			if (m) {
				var label = m[1].trim();
				var field = label
					.toLowerCase()
					.replace(/[^a-z0-9]+/g, "_")
					.replace(/^_|_$/g, "");
				if (field) {
					out[field] = __(label) + " " + __("is required");
				}
			}
		});
		return out;
	}

	var api = { clear: clear, show: show, fromFrappeError: fromFrappeError };
	window.ktFormErrors = api;
	window.kentender = window.kentender || {};
	window.kentender.formErrors = api;
})(window, window.jQuery);