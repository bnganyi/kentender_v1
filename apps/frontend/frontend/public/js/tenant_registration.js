(() => {
  const form = document.getElementById("tenant-registration-form");
  if (!form) return;
  const button = document.getElementById("submit-button");
  const message = document.getElementById("registration-message");
  const statusBox = document.getElementById("registration-status");
  let statusTimer = null;

  function showMessage(text, kind) {
    message.className = kind === "error" ? "text-danger" : "text-success";
    message.textContent = text;
  }

  async function callApi(method, args) {
    const response = await fetch(`/api/method/${method}`, {
      method: "POST",
      headers: {"Content-Type": "application/json", "Accept": "application/json"},
      credentials: "same-origin",
      body: JSON.stringify(args)
    });
    const data = await response.json();
    if (!response.ok || data.exc) {
      throw new Error(data._server_messages ? JSON.parse(data._server_messages).map(x => {
        try { return JSON.parse(x).message; } catch (_) { return x; }
      }).join(" ") : (data.message || "Registration failed."));
    }
    return data.message;
  }

  async function pollStatus(registrationId) {
    try {
      const result = await callApi("frontend.api.tenant_registration.registration_status", {registration_id: registrationId});
      statusBox.style.display = "block";
      statusBox.textContent = result.message;
      if (result.status === "Active" && result.login_url) {
        statusBox.innerHTML = "";
        const p = document.createElement("p");
        p.textContent = "Your workspace is ready: ";
        const a = document.createElement("a");
        a.href = result.login_url;
        a.textContent = result.login_url;
        a.rel = "noopener";
        p.appendChild(a);
        statusBox.appendChild(p);
        return;
      }
      if (result.status === "Failed") return;
      statusTimer = window.setTimeout(() => pollStatus(registrationId), 6000);
    } catch (_) {
      statusTimer = window.setTimeout(() => pollStatus(registrationId), 10000);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    if (statusTimer) window.clearTimeout(statusTimer);
    button.disabled = true;
    showMessage("Submitting registration…", "success");
    statusBox.style.display = "none";
    const formData = new FormData(form);
    const args = Object.fromEntries(formData.entries());
    try {
      const result = await callApi("frontend.api.tenant_registration.register_tenant", args);
      showMessage(result.message, "success");
      form.reset();
      pollStatus(result.registration_id);
    } catch (error) {
      showMessage(error.message || "Could not submit registration.", "error");
    } finally {
      button.disabled = false;
    }
  });
})();
