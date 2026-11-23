
document.addEventListener("DOMContentLoaded", () => {

    // =====================================
    // ENERGY CALCULATOR
    // =====================================

    const energyForm = document.getElementById("energyForm");

    if (energyForm) {
        energyForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const distance = document.getElementById("distance").value;
            const consumption = document.getElementById("consumption").value;
            const result = document.getElementById("energyResult");

            result.textContent = "Calculating energy requirement...";

            try {
                const response = await fetch("/api/energy", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        distance: distance,
                        consumption: consumption
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Calculation failed.");
                }

                result.innerHTML = `
                    <strong>Energy Required</strong>
                    <h2>${data.energy_required_kwh} kWh</h2>
                    <span>For a journey of ${data.distance_km} km</span>
                `;

            } catch (error) {
                result.textContent = error.message;
            }
        });
    }


    // =====================================
    // VEHICLE RANGE ESTIMATOR
    // =====================================

    const rangeForm = document.getElementById("rangeForm");

    if (rangeForm) {
        rangeForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const battery = document.getElementById("battery").value;
            const level = document.getElementById("level").value;
            const consumption = document.getElementById("rangeConsumption").value;
            const result = document.getElementById("rangeResult");

            result.textContent = "Estimating vehicle range...";

            try {
                const response = await fetch("/api/range", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        battery: battery,
                        level: level,
                        consumption: consumption
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Range calculation failed.");
                }

                result.innerHTML = `
                    <strong>Estimated Driving Range</strong>
                    <h2>${data.estimated_range_km} km</h2>
                    <span>Based on the entered battery and consumption values</span>
                `;

            } catch (error) {
                result.textContent = error.message;
            }
        });
    }


    // =====================================
    // DISRUPTION RECOVERY SIMULATOR
    // =====================================

    const disruptionForm = document.getElementById("disruptionForm");

    if (disruptionForm) {
        disruptionForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const type = document.getElementById("disruptionType").value;
            const target = document.getElementById("targetVehicle").value;
            const result = document.getElementById("disruptionResult");

            if (!target) {
                result.textContent = "No vehicle is available to select.";
                return;
            }

            result.textContent = "Analysing disruption and checking replacement vehicles...";

            try {
                const response = await fetch("/api/disruption", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        type: type,
                        target: target
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Simulation failed.");
                }

                if (data.vehicle) {
                    result.innerHTML = `
                        <strong>Recovery Candidate Found</strong>
                        <h2>${data.vehicle}</h2>
                        <p>Battery Level: ${data.battery}%</p>
                        <p>${data.message}</p>
                    `;
                } else {
                    result.innerHTML = `
                        <strong>${data.status}</strong>
                        <p>${data.message}</p>
                    `;
                }

            } catch (error) {
                result.textContent = error.message;
            }
        });
    }

});
