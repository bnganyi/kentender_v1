(() => {
	const form = document.getElementById("tenant-registration-form");
	if (!form) return;

	const button = document.getElementById("submit-button");
	const message = document.getElementById("registration-message");
	const statusBox = document.getElementById("registration-status");
	const statusUrl = document.getElementById("registration-workspace-url");
	const otpPanel = document.getElementById("otp-panel");
	const tokenField = document.getElementById("verification_token");

	const companyInput = document.getElementById("company_name");
	const emailInput = document.getElementById("email");
	const phoneInput = document.getElementById("phone");
	const workspaceInput = document.getElementById("workspace_name");
	const countryInput = document.getElementById("country");
	const passwordInput = document.getElementById("password");
	const confirmPasswordInput = document.getElementById("confirm_password");

	const emailCode = document.getElementById("email_otp");
	const smsCode = document.getElementById("sms_otp");
	const emailVerified = document.getElementById("email-verified");
	const smsVerified = document.getElementById("sms-verified");
	const sendOtpButton = document.getElementById("send-otp-button");
	const continueToSmsButton = document.getElementById("continue-to-sms-button");

	let emailOk = false;
	let smsOk = false;
	let detailsValidated = false;
	let validatedSnapshot = null;
	let validationInProgress = false;
	let statusTimer = null;
	let currentStep = 1;

	const stepPanels = [...document.querySelectorAll("[data-step-panel]")];
	const stepIndicators = [...document.querySelectorAll("[data-step-indicator]")];

	const identityFields = [companyInput, workspaceInput, emailInput, phoneInput, countryInput];

	function showToast(text, kind) {
		let container = document.getElementById("registration-toast-container");
		if (!container) {
			container = document.createElement("div");
			container.id = "registration-toast-container";
			container.setAttribute("role", "region");
			container.setAttribute("aria-label", "Notifications");
			document.body.append(container);
		}

		while (container.children.length >= 4) {
			container.lastElementChild.remove();
		}

		const toast = document.createElement("div");
		toast.className = `registration-toast registration-toast--${kind}`;
		toast.setAttribute("role", kind === "error" ? "alert" : "status");

		const content = document.createElement("span");
		content.textContent = text;

		const closeButton = document.createElement("button");
		closeButton.type = "button";
		closeButton.className = "registration-toast-close";
		closeButton.setAttribute("aria-label", "Dismiss notification");
		closeButton.textContent = "×";
		closeButton.addEventListener("click", () => dismissToast(toast));

		toast.append(content, closeButton);
		container.prepend(toast);
		window.setTimeout(() => dismissToast(toast), 6000);
	}

	function dismissToast(toast) {
		if (toast.classList.contains("is-dismissing")) return;
		toast.classList.add("is-dismissing");
		window.setTimeout(() => toast.remove(), 180);
	}

	function showMessage(text, kind, notify = kind === "error") {
		if (notify && text) {
			message.className = "";
			message.textContent = "";
			showToast(text, kind);
			return;
		}

		message.className = kind === "error" ? "text-danger" : "text-success";
		message.textContent = text || "";
	}

	function updateSubmit() {
		button.disabled = !(emailOk && smsOk && tokenField.value);
		continueToSmsButton.disabled = !(emailOk && tokenField.value);
	}

	function showStep(step) {
		currentStep = step;
		stepPanels.forEach((panel) => {
			panel.hidden = Number(panel.dataset.stepPanel) !== step;
		});
		stepIndicators.forEach((indicator) => {
			const indicatorStep = Number(indicator.dataset.stepIndicator);
			const isFinalComplete = step === 5 && indicatorStep === 5;
			const isActive = indicatorStep === step && !isFinalComplete;
			indicator.classList.toggle("is-active", isActive);
			indicator.classList.toggle("is-complete", indicatorStep < step || isFinalComplete);
			if (isActive) {
				indicator.setAttribute("aria-current", "step");
			} else {
				indicator.removeAttribute("aria-current");
			}
		});
	}

	function validatePasswordConfirmation() {
		confirmPasswordInput.setCustomValidity(
			passwordInput.value === confirmPasswordInput.value ? "" : "Passwords do not match.",
		);
	}

	function updateWorkspacePreview() {
		const slug = workspaceInput.value.trim().toLowerCase();
		document.getElementById("workspace-url-preview").textContent =
			`${slug || "yourname"}.midas.co.ke`;
	}

	function getRegistrationSnapshot() {
		return JSON.stringify({
			company_name: companyInput.value.trim(),
			workspace_name: workspaceInput.value.trim().toLowerCase(),
			email: emailInput.value.trim().toLowerCase(),
			phone: phoneInput.value.trim(),
			country: countryInput.value,
		});
	}

	function clearFieldError(field) {
		const error = document.getElementById(`${field.id}-error`);
		if (error) error.remove();
		field.removeAttribute("aria-invalid");
	}

	function setFieldError(field, text) {
		clearFieldError(field);
		if (!text) return;

		const error = document.createElement("small");
		error.id = `${field.id}-error`;
		error.className = "text-danger";
		error.style.display = "block";
		error.style.marginTop = "4px";
		error.textContent = text;

		field.setAttribute("aria-invalid", "true");
		field.insertAdjacentElement("afterend", error);
	}

	function clearValidationErrors() {
		identityFields.forEach(clearFieldError);
	}

	function displayValidationErrors(errors) {
		const fieldMap = {
			company_name: companyInput,
			workspace_name: workspaceInput,
			email: emailInput,
			phone: phoneInput,
		};

		clearValidationErrors();

		Object.entries(errors || {}).forEach(([name, text]) => {
			const field = fieldMap[name];
			if (field) setFieldError(field, text);
		});
	}

	function invalidateRegistrationDetails() {
		detailsValidated = false;
		validatedSnapshot = null;

		// Changing an identity after OTP delivery invalidates that verification.
		if (emailOk || smsOk || tokenField.value) {
			resetVerification();
		}
	}

	function resetVerification() {
		emailOk = false;
		smsOk = false;
		tokenField.value = "";
		emailCode.value = "";
		smsCode.value = "";
		emailVerified.textContent = "";
		smsVerified.textContent = "";
		otpPanel.hidden = true;
		updateSubmit();
	}

	async function callApi(method, args) {
		const response = await fetch(`/api/method/${method}`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Accept: "application/json",
			},
			credentials: "same-origin",
			body: JSON.stringify(args),
		});

		const data = await response.json();

		if (!response.ok || data.exc || data.exception) {
			let detail = data.message || "Request failed.";

			if (data._server_messages) {
				try {
					detail = JSON.parse(data._server_messages)
						.map((item) => {
							try {
								return JSON.parse(item).message;
							} catch (_) {
								return item;
							}
						})
						.join(" ");
				} catch (_) {
					// Keep the original message if Frappe's message payload is malformed.
				}
			}

			throw new Error(detail);
		}

		return data.message;
	}

	async function validateRegistration(force = false) {
		const snapshot = getRegistrationSnapshot();

		if (!force && detailsValidated && snapshot === validatedSnapshot) {
			return true;
		}

		if (validationInProgress) return false;

		validationInProgress = true;
		clearValidationErrors();
		showMessage("Checking your registration details…", "success");

		const stepOne = document.querySelector('[data-step-panel="1"]');
		const invalidField = [...stepOne.querySelectorAll("input, select")].find(
			(field) => !field.checkValidity(),
		);

		if (invalidField) {
			invalidField.reportValidity();
			validationInProgress = false;
			showMessage("Please complete the required account details.", "error");
			return false;
		}

		try {
			const result = await callApi(
				"frontend.api.tenant_registration.validate_registration",
				{
					company_name: companyInput.value,
					workspace_name: workspaceInput.value,
					email: emailInput.value,
					phone: phoneInput.value,
					country: countryInput.value,
				},
			);

			if (!result || result.available !== true) {
				displayValidationErrors(result?.errors || {});
				detailsValidated = false;
				validatedSnapshot = null;
				showMessage(result?.message || "Please correct the highlighted details.", "error");
				return false;
			}

			detailsValidated = true;
			validatedSnapshot = getRegistrationSnapshot();

			if (result.workspace_url) {
				document.getElementById("workspace-url-preview").textContent =
					result.workspace_url;
			}

			showMessage(result.message || "Registration details are available.", "success", true);
			return true;
		} catch (error) {
			detailsValidated = false;
			validatedSnapshot = null;
			showMessage(error.message || "Unable to validate registration.", "error");
			return false;
		} finally {
			validationInProgress = false;
		}
	}

	// Validate the first step before allowing the user to continue.
	form.querySelectorAll("[data-next-step]").forEach((nextButton) => {
		nextButton.addEventListener("click", async () => {
			if (currentStep === 1) {
				validatePasswordConfirmation();

				const valid = await validateRegistration();
				if (!valid) return;
			}

			showStep(Number(nextButton.dataset.nextStep));
		});
	});

	form.querySelectorAll("[data-previous-step]").forEach((previousButton) => {
		previousButton.addEventListener("click", () => {
			showStep(Number(previousButton.dataset.previousStep));
		});
	});

	passwordInput.addEventListener("input", validatePasswordConfirmation);
	confirmPasswordInput.addEventListener("input", validatePasswordConfirmation);
	workspaceInput.addEventListener("input", updateWorkspacePreview);

	identityFields.forEach((field) => {
		field.addEventListener("input", () => {
			clearFieldError(field);
			invalidateRegistrationDetails();
		});
		field.addEventListener("change", () => {
			clearFieldError(field);
			invalidateRegistrationDetails();
		});
	});

	countryInput.addEventListener("change", (event) => {
		const currencyByCountry = {
			Kenya: "KES",
			Uganda: "UGX",
			Tanzania: "TZS",
			Rwanda: "RWF",
			"United States": "USD",
			"United Kingdom": "GBP",
		};
		const currency = currencyByCountry[event.target.value];
		if (currency) {
			document.getElementById("currency").value = currency;
		}
	});

	sendOtpButton.addEventListener("click", async () => {
		if (!emailInput.reportValidity() || !phoneInput.reportValidity()) return;

		sendOtpButton.disabled = true;
		sendOtpButton.textContent = "Validating details…";

		try {
			// Recheck immediately before OTP delivery, not only at step one.
			const valid = await validateRegistration(true);
			if (!valid) {
				showStep(1);
				return;
			}

			resetVerification();
			sendOtpButton.textContent = "Sending codes…";

			const result = await callApi("frontend.api.registration_otp.send_registration_otps", {
				email: emailInput.value,
				phone: phoneInput.value,
			});

			tokenField.value = result.verification_token;
			otpPanel.hidden = false;
			showMessage(result.message, "success", true);
		} catch (error) {
			showMessage(error.message || "Could not send verification codes.", "error");
		} finally {
			sendOtpButton.disabled = false;
			sendOtpButton.textContent = "Send verification codes";
		}
	});

	document.getElementById("verify-email-button").addEventListener("click", async () => {
		if (!tokenField.value) {
			showMessage("Request verification codes first.", "error");
			return;
		}

		try {
			const result = await callApi(
				"frontend.api.registration_otp.verify_registration_email",
				{
					token: tokenField.value,
					code: emailCode.value,
				},
			);

			emailOk = true;
			emailVerified.textContent = "Verified";
			showMessage(result.message, "success", true);
			updateSubmit();
		} catch (error) {
			emailOk = false;
			updateSubmit();
			showMessage(error.message, "error");
		}
	});

	document.getElementById("verify-sms-button").addEventListener("click", async () => {
		if (!tokenField.value) {
			showMessage("Request verification codes first.", "error");
			return;
		}

		try {
			const result = await callApi("frontend.api.registration_otp.verify_registration_sms", {
				token: tokenField.value,
				code: smsCode.value,
			});

			smsOk = true;
			smsVerified.textContent = "Verified";
			showMessage(result.message, "success", true);
			updateSubmit();
		} catch (error) {
			smsOk = false;
			updateSubmit();
			showMessage(error.message, "error");
		}
	});

	async function pollStatus(statusToken) {
		try {
			const result = await callApi("frontend.api.tenant_registration.registration_status", {
				status_token: statusToken,
			});

			statusBox.textContent = result.message;

			if (result.status === "Active" && result.login_url) {
				statusUrl.hidden = false;
				statusUrl.replaceChildren();

				const link = document.createElement("a");
				link.href = result.login_url;
				link.textContent = result.login_url;
				link.rel = "noopener";
				statusUrl.append("Workspace URL: ", link);
				return;
			}

			if (result.status === "Failed") return;

			statusTimer = window.setTimeout(() => pollStatus(statusToken), 6000);
		} catch (_) {
			statusBox.textContent = "Your request is saved. We’re checking provisioning status…";
			statusTimer = window.setTimeout(() => pollStatus(statusToken), 10000);
		}
	}

	form.addEventListener("submit", async (event) => {
		event.preventDefault();

		if (currentStep !== 4 || !emailOk || !smsOk || !tokenField.value) {
			showMessage("Verify both email and phone first.", "error");
			return;
		}

		// Ensure identities have not changed since the pre-OTP check.
		if (getRegistrationSnapshot() !== validatedSnapshot) {
			detailsValidated = false;
			resetVerification();
			showStep(1);
			showMessage(
				"Your registration details changed. Please validate them and request new OTPs.",
				"error",
			);
			return;
		}

		if (statusTimer) window.clearTimeout(statusTimer);

		button.disabled = true;
		showMessage("Submitting registration…", "success");

		const args = Object.fromEntries(new FormData(form).entries());
		delete args.confirm_password;

		try {
			const result = await callApi("frontend.api.tenant_registration.register_tenant", args);

			showMessage(result.message, "success", true);
			showStep(5);
			statusBox.textContent = result.message;

			if (result.status_token) {
				pollStatus(result.status_token);
			}
		} catch (error) {
			showMessage(error.message || "Could not submit registration.", "error");
			updateSubmit();
		}
	});

	updateWorkspacePreview();
	showStep(1);
	updateSubmit();
})();
