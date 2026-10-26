(() => {
	const form = document.getElementById("tenant-registration-form");
	if (!form) return;
	const button = document.getElementById("submit-button");
	const message = document.getElementById("registration-message");
	const statusBox = document.getElementById("registration-status");
	const statusUrl = document.getElementById("registration-workspace-url");
	const otpPanel = document.getElementById("otp-panel");
	const tokenField = document.getElementById("verification_token");
	const emailInput = document.getElementById("email");
	const phoneInput = document.getElementById("phone");
	const workspaceInput = document.getElementById("workspace_name");
	const passwordInput = document.getElementById("password");
	const confirmPasswordInput = document.getElementById("confirm_password");
	const emailCode = document.getElementById("email_otp");
	const smsCode = document.getElementById("sms_otp");
	const emailVerified = document.getElementById("email-verified");
	const smsVerified = document.getElementById("sms-verified");
	let emailOk = false;
	let smsOk = false;
	let statusTimer = null;
	let currentStep = 1;
	const stepPanels = [...document.querySelectorAll("[data-step-panel]")];
	const stepIndicators = [...document.querySelectorAll("[data-step-indicator]")];
	function showMessage(text, kind) {
		message.className = kind === "error" ? "text-danger" : "text-success";
		message.textContent = text;
	}
	function updateSubmit() {
		button.disabled = !(emailOk && smsOk);
	}

	function showStep(step) {
		currentStep = step;
		stepPanels.forEach((panel) => {
			panel.hidden = Number(panel.dataset.stepPanel) !== step;
		});
		stepIndicators.forEach((indicator) => {
			const indicatorStep = Number(indicator.dataset.stepIndicator);
			indicator.classList.toggle("is-active", indicatorStep === step);
			indicator.classList.toggle("is-complete", indicatorStep < step);
			if (indicatorStep === step) indicator.setAttribute("aria-current", "step");
			else indicator.removeAttribute("aria-current");
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

	form.querySelectorAll("[data-next-step]").forEach((nextButton) => {
		nextButton.addEventListener("click", () => {
			if (currentStep === 1) {
				validatePasswordConfirmation();
				const firstStep = document.querySelector('[data-step-panel="1"]');
				const invalidField = [...firstStep.querySelectorAll("input, select")].find(
					(field) => !field.checkValidity(),
				);
				if (invalidField) {
					invalidField.reportValidity();
					return;
				}
			}
			showStep(Number(nextButton.dataset.nextStep));
		});
	});
	form.querySelectorAll("[data-previous-step]").forEach((previousButton) => {
		previousButton.addEventListener("click", () =>
			showStep(Number(previousButton.dataset.previousStep)),
		);
	});
	passwordInput.addEventListener("input", validatePasswordConfirmation);
	confirmPasswordInput.addEventListener("input", validatePasswordConfirmation);
	workspaceInput.addEventListener("input", updateWorkspacePreview);
	emailInput.addEventListener("input", resetVerification);
	phoneInput.addEventListener("input", resetVerification);
	document.getElementById("country").addEventListener("change", (event) => {
		const currencyByCountry = {
			Kenya: "KES",
			Uganda: "UGX",
			Tanzania: "TZS",
			Rwanda: "RWF",
			"United States": "USD",
			"United Kingdom": "GBP",
		};
		const currency = currencyByCountry[event.target.value];
		if (currency) document.getElementById("currency").value = currency;
	});

	async function callApi(method, args) {
		const response = await fetch(`/api/method/${method}`, {
			method: "POST",
			headers: { "Content-Type": "application/json", Accept: "application/json" },
			credentials: "same-origin",
			body: JSON.stringify(args),
		});
		const data = await response.json();
		if (!response.ok || data.exc) {
			let detail = data.message || "Request failed.";
			if (data._server_messages) {
				try {
					detail = JSON.parse(data._server_messages)
						.map((x) => {
							try {
								return JSON.parse(x).message;
							} catch (_) {
								return x;
							}
						})
						.join(" ");
				} catch (_) {}
			}
			throw new Error(detail);
		}
		return data.message;
	}
	document.getElementById("send-otp-button").addEventListener("click", async () => {
		if (!emailInput.reportValidity() || !phoneInput.reportValidity()) return;
		const sendButton = document.getElementById("send-otp-button");
		sendButton.disabled = true;
		try {
			resetVerification();
			const result = await callApi("frontend.api.registration_otp.send_registration_otps", {
				email: emailInput.value,
				phone: phoneInput.value,
			});
			tokenField.value = result.verification_token;
			otpPanel.hidden = false;
			showMessage(result.message, "success");
		} catch (e) {
			showMessage(e.message, "error");
		} finally {
			sendButton.disabled = false;
		}
	});
	document.getElementById("verify-email-button").addEventListener("click", async () => {
		try {
			const r = await callApi("frontend.api.registration_otp.verify_registration_email", {
				token: tokenField.value,
				code: emailCode.value,
			});
			emailOk = true;
			emailVerified.textContent = "Verified";
			showMessage(r.message, "success");
			updateSubmit();
		} catch (e) {
			emailOk = false;
			updateSubmit();
			showMessage(e.message, "error");
		}
	});
	document.getElementById("verify-sms-button").addEventListener("click", async () => {
		try {
			const r = await callApi("frontend.api.registration_otp.verify_registration_sms", {
				token: tokenField.value,
				code: smsCode.value,
			});
			smsOk = true;
			smsVerified.textContent = "Verified";
			showMessage(r.message, "success");
			updateSubmit();
		} catch (e) {
			smsOk = false;
			updateSubmit();
			showMessage(e.message, "error");
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
		if (currentStep !== 3 || !emailOk || !smsOk || !tokenField.value) {
			showMessage("Verify both email and phone first.", "error");
			return;
		}
		if (statusTimer) window.clearTimeout(statusTimer);
		button.disabled = true;
		showMessage("Submitting registration…", "success");
		const args = Object.fromEntries(new FormData(form).entries());
		delete args.confirm_password;
		try {
			const result = await callApi("frontend.api.tenant_registration.register_tenant", args);
			showMessage(result.message, "success");
			showStep(4);
			statusBox.textContent = result.message;
			if (result.status_token) pollStatus(result.status_token);
		} catch (e) {
			showMessage(e.message || "Could not submit registration.", "error");
			updateSubmit();
		}
	});
	updateWorkspacePreview();
	showStep(1);
	updateSubmit();
})();
