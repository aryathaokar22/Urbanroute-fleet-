(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { ports: [], chargers: [], reservations: [], waitlist: [] };

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  function localIso(value) {
    const date = new Date(value);
    const offset = -date.getTimezoneOffset();
    const sign = offset >= 0 ? "+" : "-";
    const hours = String(Math.floor(Math.abs(offset) / 60)).padStart(2, "0");
    const minutes = String(Math.abs(offset) % 60).padStart(2, "0");
    return `${value}:00${sign}${hours}:${minutes}`;
  }

  function displayDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value || "—";
    return date.toLocaleString([], {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
  }

  async function api(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) }
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "The request could not be completed.");
    return data;
  }

  function setMessage(id, message, isError = false) {
    const element = $(id);
    element.textContent = message;
    element.classList.toggle("is-error", isError);
  }

  function populatePortSelect() {
    const vehicle = $("vehicleId").selectedOptions[0];
    const connector = vehicle?.dataset.connector || "";
    const select = $("portId");
    const compatible = state.ports.filter((port) =>
      port.connector_type.toUpperCase() === connector.toUpperCase()
      && port.available
    );

    select.innerHTML = '<option value="">Choose an available port</option>' +
      compatible.map((port) =>
        `<option value="${port.port_id}">${escapeHtml(port.charger_name)} · Port ${escapeHtml(port.port_number)} · ${escapeHtml(port.max_power_kw)} kW</option>`
      ).join("");

    $("connectorHint").textContent = vehicle
      ? `Vehicle connector: ${connector || "Not specified"}. Showing operational compatible ports.`
      : "Select a vehicle to check connector compatibility.";

    if (vehicle && compatible.length === 0) {
      $("connectorHint").textContent = `No operational ports match ${connector || "this vehicle's connector"}.`;
    }
    updateCapacity();
  }

  function updateCapacity() {
    const port = state.ports.find((item) => String(item.port_id) === $("portId").value);
    const start = $("startAt").value;
    const end = $("endAt").value;

    if (!port || !start || !end) {
      $("capacityEstimate").textContent = "Select a charging port and time window to see estimated charging capacity.";
      return;
    }

    const hours = (new Date(end) - new Date(start)) / 3600000;
    if (hours <= 0) {
      $("capacityEstimate").textContent = "End time must be after start time.";
      return;
    }

    const capacity = hours * Number(port.max_power_kw);
    $("capacityEstimate").textContent =
      `Estimated maximum energy: ${capacity.toFixed(1)} kWh · ${hours.toFixed(2)} hours at ${port.max_power_kw} kW.`;
  }

  function renderPorts() {
    $("portInventory").innerHTML = state.ports.map((port) => {
      const available = port.available;
      return `
        <article class="port-item">
          <div class="port-symbol">ϟ</div>
          <div class="port-details">
            <strong>${escapeHtml(port.charger_name)} · ${escapeHtml(port.port_number)}</strong>
            <small>${escapeHtml(port.location)} · ${escapeHtml(port.connector_type)} · ${escapeHtml(port.max_power_kw)} kW</small>
          </div>
          <span class="port-state ${available ? "available" : "unavailable"}">${available ? "Operational" : escapeHtml(port.port_status)}</span>
        </article>`;
    }).join("") || '<p class="reservation-empty">No charging ports have been configured.</p>';

    $("availablePorts").textContent = state.ports.filter((port) => port.available).length;
  }

  function renderReservations() {
    const rows = state.reservations;
    const active = rows.filter((row) => ["confirmed", "checked_in", "charging"].includes(row.status));
    $("activeCount").textContent = active.length;

    $("reservationRows").innerHTML = rows.map((row) => {
      const activeStatus = ["confirmed", "checked_in"].includes(row.status);
      return `<tr>
        <td><strong>${escapeHtml(row.vehicle_name)}</strong></td>
        <td>${escapeHtml(row.charger_name)}</td>
        <td>${escapeHtml(row.port_number)}</td>
        <td>${escapeHtml(displayDate(row.start_at))}</td>
        <td>${escapeHtml(displayDate(row.end_at))}</td>
        <td>${Number(row.energy_target_kwh).toFixed(1)} kWh</td>
        <td><span class="reservation-state ${escapeHtml(row.status)}">${escapeHtml(row.status.replaceAll("_", " "))}</span></td>
        <td>${activeStatus
          ? `<button class="table-action" data-action="reschedule" data-id="${row.id}">Reschedule</button><button class="table-action cancel" data-action="cancel" data-id="${row.id}">Cancel</button>`
          : "—"}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="8" class="reservation-empty">No reservations yet. Create your first booking above.</td></tr>';
  }

  function renderWaitlist() {
    const waiting = state.waitlist.filter((entry) => entry.status === "waiting");
    $("waitingCount").textContent = waiting.length;

    $("waitlistRows").innerHTML = waiting.map((entry, index) => `
      <article class="waitlist-item">
        <span class="queue-rank">${String(index + 1).padStart(2, "0")}</span>
        <div><strong>${escapeHtml(entry.vehicle_name)}</strong><small>${escapeHtml(entry.charger_name)} · ${Number(entry.vehicle_soc).toFixed(0)}% battery</small></div>
        <span class="priority-score">${Number(entry.priority_score).toFixed(0)} pts</span>
      </article>
    `).join("") || '<p class="reservation-empty">The charging waiting list is empty.</p>';
  }

  async function loadAll() {
    const [ports, reservations, waitlist] = await Promise.all([
      api("/api/charging-ports"),
      api("/api/reservations"),
      api("/api/waitlist")
    ]);

    state.ports = ports.ports || [];
    state.reservations = reservations.reservations || [];
    state.waitlist = waitlist.waitlist || [];

    renderPorts();
    renderReservations();
    renderWaitlist();
    populatePortSelect();
  }

  async function loadChargers() {
    const data = await api("/api/charging-ports");
    const seen = new Map();

    data.ports.forEach((port) => {
      seen.set(port.charger_id, {
        id: port.charger_id,
        name: port.charger_name,
        location: port.location
      });
    });

    state.chargers = Array.from(seen.values());
    $("waitChargerId").innerHTML = '<option value="">Choose a station</option>' +
      state.chargers.map((charger) =>
        `<option value="${charger.id}">${escapeHtml(charger.name)} · ${escapeHtml(charger.location)}</option>`
      ).join("");
  }

  $("vehicleId").addEventListener("change", populatePortSelect);
  ["portId", "startAt", "endAt"].forEach((id) =>
    $(id).addEventListener("change", updateCapacity)
  );

  $("reservationForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage("bookingMessage", "");

    const button = $("reserveButton");
    button.disabled = true;

    try {
      const payload = {
        vehicle_id: Number($("vehicleId").value),
        port_id: Number($("portId").value),
        start_at: localIso($("startAt").value),
        end_at: localIso($("endAt").value),
        energy_target_kwh: Number($("energyTarget").value),
        estimated_cost: Number($("estimatedCost").value || 0),
        notes: $("bookingNotes").value
      };

      const result = await api("/api/reservations", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      setMessage("bookingMessage", result.message || "Reservation created.");
      $("reservationForm").reset();
      $("energyTarget").value = "20";
      $("estimatedCost").value = "0";
      await loadAll();
    } catch (error) {
      setMessage("bookingMessage", error.message, true);
    } finally {
      button.disabled = false;
    }
  });

  $("reservationRows").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const id = button.dataset.id;
    const action = button.dataset.action;

    try {
      if (action === "cancel") {
        if (!window.confirm("Cancel this reservation?")) return;
        const result = await api(`/api/reservations/${id}`, { method: "DELETE" });
        window.alert(result.message);
      } else if (action === "reschedule") {
        const current = state.reservations.find((row) => String(row.id) === id);
        const startValue = window.prompt("New start time (ISO 8601 with timezone):", current.start_at);
        if (!startValue) return;
        const endValue = window.prompt("New end time (ISO 8601 with timezone):", current.end_at);
        if (!endValue) return;

        const result = await api(`/api/reservations/${id}`, {
          method: "PUT",
          body: JSON.stringify({ start_at: startValue, end_at: endValue })
        });
        window.alert(result.message);
      }
      await loadAll();
    } catch (error) {
      window.alert(error.message);
    }
  });

  $("waitlistForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage("waitlistMessage", "");

    try {
      const result = await api("/api/waitlist", {
        method: "POST",
        body: JSON.stringify({
          vehicle_id: Number($("waitVehicleId").value),
          charger_id: Number($("waitChargerId").value),
          requested_energy_kwh: Number($("waitEnergy").value)
        })
      });

      setMessage("waitlistMessage", `${result.message} Priority score: ${result.priority_score}.`);
      $("waitlistForm").reset();
      $("waitEnergy").value = "20";
      await loadAll();
    } catch (error) {
      setMessage("waitlistMessage", error.message, true);
    }
  });

  $("refreshReservations").addEventListener("click", async () => {
    try {
      await loadAll();
    } catch (error) {
      window.alert(error.message);
    }
  });

  function setDefaultTimes() {
    const start = new Date(Date.now() + 60 * 60 * 1000);
    start.setMinutes(0, 0, 0);
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    const toLocalInput = (date) => {
      const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
      return local.toISOString().slice(0, 16);
    };
    $("startAt").value = toLocalInput(start);
    $("endAt").value = toLocalInput(end);
  }

  async function init() {
    setDefaultTimes();
    try {
      await Promise.all([loadAll(), loadChargers()]);
    } catch (error) {
      setMessage("bookingMessage", `Could not load reservation data: ${error.message}`, true);
    }
  }

  init();
})();
