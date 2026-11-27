document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("mobileToggle");
  const nav = document.getElementById("mainNav");
  if (toggle && nav) toggle.addEventListener("click", () => nav.classList.toggle("open"));

  const form = document.getElementById("disruptionForm");
  const result = document.getElementById("recoveryResult");
  if (form && result) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(form).entries());
      result.innerHTML = "<p>Evaluating demonstration recovery options…</p>";
      try {
        const response = await fetch("/api/disruptions", {
          method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify(data)
        });
        const proposal = await response.json();
        const checks = proposal.checks.map(item => `<li>${escapeHtml(item)}</li>`).join("");
        result.innerHTML = `<small>RECOVERY PROPOSAL · ${escapeHtml(proposal.status)}</small>
          <h3>${proposal.vehicle ? "Candidate: " + escapeHtml(proposal.vehicle) : "No eligible candidate"}</h3>
          <p>${escapeHtml(proposal.reason)}</p><ul>${checks}</ul>`;
      } catch (_error) {
        result.innerHTML = "<p>Could not reach the local application. Check that Flask is running.</p>";
      }
    });
  }
});
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  })[char]);
}
