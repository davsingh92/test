(() => {
  const form = document.getElementById("ahs-contact-form");
  if (!form) return;
  const status = document.getElementById("ahs-contact-status");
  const button = document.getElementById("ahs-contact-submit");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const apiBase = (window.AHS_BACKEND_API_URL || "").replace(/\/$/, "");
    if (!apiBase || apiBase.includes("YOUR-WORKER") || apiBase.includes("YOUR-SUBDOMAIN")) {
      status.textContent = "The form is not connected yet. Complete the Worker setup in the project README.";
      status.style.color = "#b45309";
      return;
    }
    const data = Object.fromEntries(new FormData(form).entries());
    button.disabled = true;
    button.textContent = "Sending…";
    status.textContent = "";
    try {
      const response = await fetch(`${apiBase}/api/contact`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data)
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Submission failed");
      form.reset();
      status.textContent = result.message || "Thank you. Your enquiry has been received.";
      status.style.color = "#166534";
    } catch (error) {
      status.textContent = error.message || "Could not send your enquiry. Please try again later.";
      status.style.color = "#b91c1c";
    } finally {
      button.disabled = false;
      button.textContent = "Send Enquiry";
    }
  });
})();
