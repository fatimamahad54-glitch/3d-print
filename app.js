const API_BASE = "";

// Global state
let currentTab = "tab-ml-dashboard";
let globalStepsData = null;

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    loadDashboard();
});

// 1. Navigation handling
function initNavigation() {
    const navLinks = document.querySelectorAll(".sidebar-nav a");
    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove("active"));
            link.classList.add("active");

            const targetId = link.getAttribute("data-target");
            switchTab(targetId);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    const target = document.getElementById(tabId);
    if (target) {
        target.classList.add("active");
        currentTab = tabId;
        
        // Refresh specific tab data
        if (tabId === "tab-ml-dashboard") loadDashboard();
        else if (tabId === "tab-ml-data") loadDataTab();
        else if (tabId === "tab-ml-clean") loadCleanTab();
        else if (tabId === "tab-ml-selection") loadSelectionTab();
        else if (tabId === "tab-ml-training") loadTrainingTab();
        else if (tabId === "tab-ml-evaluation") loadEvaluationTab();
        else if (tabId === "tab-ml-prediction") loadPredictionTab();
        else if (tabId === "tab-ml-monitoring") loadMonitoringTab();
        else if (tabId === "tab-printers") loadPrintersTab();
        else if (tabId === "tab-jobs") loadJobsTab();
        else if (tabId === "tab-models") loadModelsTab();
        else if (tabId === "tab-filaments") loadFilamentsTab();
    }
}

// Helper: Badge renderer for steps status
function getStatusBadge(status) {
    switch (status) {
        case "Dhammaaday":
            return `<span class="badge badge-success">✓ Dhammaaday</span>`;
        case "Socda":
            return `<span class="badge badge-info">⌛ Socda</span>`;
        case "Xog ayaa maqan":
            return `<span class="badge badge-warning">⚠ Xog ayaa maqan</span>`;
        case "Error":
            return `<span class="badge badge-danger">✖ Khalad (Error)</span>`;
        default:
            return `<span class="badge badge-secondary">○ Lama bilaabin</span>`;
    }
}

// 2. Tab: ML Dashboard (7-da Talaabo)
async function loadDashboard() {
    try {
        const [stepsRes, statsRes] = await Promise.all([
            fetch(`${API_BASE}/api/ml/steps-status`).then(r => r.json()),
            fetch(`${API_BASE}/api/ml/data/statistics`).then(r => r.json())
        ]);

        globalStepsData = stepsRes;

        // Progress bar
        document.getElementById("dash-progress-pct").innerText = `${stepsRes.progress_percentage}%`;
        document.getElementById("dash-progress-fill").style.width = `${stepsRes.progress_percentage}%`;
        document.getElementById("dash-progress-text").innerText = `${stepsRes.completed_steps} ka mid ah 7 talaabo ayaa dhammaatay`;

        // Statistics cards
        document.getElementById("stat-total-data").innerText = statsRes.total_records;
        document.getElementById("stat-real-data").innerText = statsRes.real_records;
        document.getElementById("stat-demo-data").innerText = statsRes.demo_records;
        document.getElementById("stat-active-models").innerText = stepsRes.active_models_count;
        document.getElementById("stat-success-rate").innerText = `${statsRes.success_rate_percent}%`;

        // Render 7 steps list
        const stepsContainer = document.getElementById("dash-steps-list");
        stepsContainer.innerHTML = stepsRes.steps.map(step => `
            <div class="step-card">
                <div class="step-left">
                    <div class="step-badge-num">${step.step_number}</div>
                    <div class="step-info">
                        <h4>${step.name}</h4>
                        <p>${step.description}</p>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap: 14px;">
                    ${getStatusBadge(step.status)}
                    <button class="btn btn-outline btn-sm" onclick="navigateToStep(${step.step_number})">Fur Qaybta →</button>
                </div>
            </div>
        `).join("");

    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

function navigateToStep(stepNum) {
    const tabMap = {
        1: "tab-ml-data",
        2: "tab-ml-clean",
        3: "tab-ml-selection",
        4: "tab-ml-training",
        5: "tab-ml-evaluation",
        6: "tab-ml-prediction",
        7: "tab-ml-monitoring"
    };
    const tab = tabMap[stepNum];
    if (tab) {
        const link = document.querySelector(`.sidebar-nav a[data-target="${tab}"]`);
        if (link) link.click();
        else switchTab(tab);
    }
}

// 3. Tab: Xogta ML (Dataset)
async function loadDataTab() {
    try {
        const stats = await fetch(`${API_BASE}/api/ml/data/statistics`).then(r => r.json());
        document.getElementById("dataset-total-count").innerText = stats.total_records;
        document.getElementById("dataset-real-count").innerText = stats.real_records;
        document.getElementById("dataset-demo-count").innerText = stats.demo_records;
        document.getElementById("dataset-status-badge").innerText = stats.data_readiness;

        const dataRes = await fetch(`${API_BASE}/api/ml/data?limit=50`).then(r => r.json());
        const tbody = document.getElementById("dataset-table-body");
        tbody.innerHTML = dataRes.data.map(row => `
            <tr>
                <td><strong>#${row.id}</strong></td>
                <td>${row.is_demo ? '<span class="badge badge-warning">DEMO</span>' : '<span class="badge badge-success">DHAB</span>'}</td>
                <td>${row.printer_model || '-'}</td>
                <td>${row.filament_type}</td>
                <td>${row.model_volume} cm³</td>
                <td>${row.print_speed} mm/s</td>
                <td>${row.layer_height} mm</td>
                <td>${row.infill_percentage}%</td>
                <td>${row.estimated_print_time} min</td>
                <td>${row.actual_print_time ? row.actual_print_time + ' min' : '<span class="badge badge-secondary">Lama hayo</span>'}</td>
                <td>${row.filament_used ? row.filament_used + ' g' : '-'}</td>
                <td>${row.print_status === 'completed' ? '<span class="badge badge-success">Guul</span>' : '<span class="badge badge-danger">Fashil</span>'}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Data tab error:", e);
    }
}

// Seed Demo Data button action
async function triggerSeedDemo() {
    if (!confirm("Ma rabtaa inaad ku darto 45 tusaale oo DEMO ah? Tani waxay u saamaxaysaa in aad tijaabiso dhammaan 7-da talaabo.")) return;
    try {
        const res = await fetch(`${API_BASE}/api/ml/data/seed-demo`, { method: "POST" }).then(r => r.json());
        alert(res.message || "Xogta demo-ga waa lagu daray!");
        loadDataTab();
        loadDashboard();
    } catch (e) {
        alert("Khalad: " + e.message);
    }
}

// Modal open/close helpers
function openModal(id) { document.getElementById(id).classList.add("active"); }
function closeModal(id) { document.getElementById(id).classList.remove("active"); }

// Submit manual record
async function submitManualRecord(event) {
    event.preventDefault();
    const form = event.target;
    const payload = {
        printer_model: form.printer_model.value,
        model_volume: parseFloat(form.model_volume.value),
        model_weight: parseFloat(form.model_weight.value),
        filament_type: form.filament_type.value,
        print_speed: parseFloat(form.print_speed.value),
        layer_height: parseFloat(form.layer_height.value),
        infill_percentage: parseFloat(form.infill_percentage.value),
        nozzle_temperature: parseFloat(form.nozzle_temperature.value),
        bed_temperature: parseFloat(form.bed_temperature.value),
        support_enabled: form.support_enabled.checked,
        estimated_print_time: parseFloat(form.estimated_print_time.value),
        actual_print_time: form.actual_print_time.value ? parseFloat(form.actual_print_time.value) : null,
        filament_used: form.filament_used.value ? parseFloat(form.filament_used.value) : null,
        print_status: form.print_status.value,
        is_demo: false
    };

    try {
        const res = await fetch(`${API_BASE}/api/ml/data`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(r => r.json());

        if (res.success) {
            alert(res.message);
            closeModal("modal-add-data");
            form.reset();
            loadDataTab();
            loadDashboard();
        } else {
            alert("Khalad: " + JSON.stringify(res));
        }
    } catch (e) {
        alert("Khalad: " + e.message);
    }
}

// CSV Import
async function submitCsvImport(event) {
    event.preventDefault();
    const fileInput = document.getElementById("csv-file-input");
    if (!fileInput.files.length) {
        alert("Fadlan dooro CSV file");
        return;
    }
    const isDemo = document.getElementById("csv-is-demo").checked;
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("is_demo", isDemo);

    try {
        const res = await fetch(`${API_BASE}/api/ml/data/import`, {
            method: "POST",
            body: formData
        }).then(r => r.json());

        alert(res.message);
        closeModal("modal-import-csv");
        loadDataTab();
        loadDashboard();
    } catch (e) {
        alert("Khalad markii CSV la soo rariyay: " + e.message);
    }
}

// 4. Tab: Nadiifinta Xogta (Data Cleaning)
async function loadCleanTab() {
    // Show current state
}

async function triggerDataCleaning() {
    const btn = document.getElementById("btn-run-clean");
    btn.disabled = true;
    btn.innerText = "Nadiifintu way socotaa...";

    try {
        const res = await fetch(`${API_BASE}/api/ml/clean`, { method: "POST" }).then(r => r.json());
        btn.disabled = false;
        btn.innerText = "Nadiifi Xogta Hadda (Run Cleaning)";

        const resultBox = document.getElementById("clean-results-box");
        resultBox.style.display = "block";

        if (res.success) {
            document.getElementById("clean-result-summary").innerHTML = `
                <div class="alert alert-success">
                    <strong>✓ Nadiifintu way guulaysatay!</strong> ${res.message}
                </div>
                <div class="grid-cols-4">
                    <div class="card"><div class="stat-info"><h4>Xogta Bilowga</h4><div class="stat-number">${res.report.initial_count}</div></div></div>
                    <div class="card"><div class="stat-info"><h4>Nuqullada Laba-laabmay</h4><div class="stat-number text-danger">${res.report.duplicates_removed}</div></div></div>
                    <div class="card"><div class="stat-info"><h4>Xogta Xadka Ka Baxsan</h4><div class="stat-number text-danger">${res.report.out_of_bounds_dropped}</div></div></div>
                    <div class="card"><div class="stat-info"><h4>Xogta Ansaxday</h4><div class="stat-number text-success">${res.report.valid_count}</div></div></div>
                </div>
            `;
            loadDashboard();
        } else {
            document.getElementById("clean-result-summary").innerHTML = `
                <div class="alert alert-danger">${res.message}</div>
            `;
        }
    } catch (e) {
        btn.disabled = false;
        btn.innerText = "Nadiifi Xogta Hadda (Run Cleaning)";
        alert("Khalad: " + e.message);
    }
}

// 5. Tab: Xulashada Model-ka (Model Selection)
async function loadSelectionTab() {}

async function triggerModelSelection() {
    const task = document.getElementById("select-task-type").value;
    const btn = document.getElementById("btn-run-selection");
    btn.disabled = true;
    btn.innerText = "Isbarbardhiggu wuu socdaa...";

    try {
        const res = await fetch(`${API_BASE}/api/ml/select-model?task_type=${task}`, { method: "POST" }).then(r => r.json());
        btn.disabled = false;
        btn.innerText = "Bilow Isbarbardhigga (Compare Models)";

        const box = document.getElementById("selection-results-box");
        box.style.display = "block";

        let metricsHtml = "";
        if (task === "regression") {
            metricsHtml = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>Model / Algorithm</th>
                            <th>MAE (Daqiiqado)</th>
                            <th>RMSE</th>
                            <th>R² Score</th>
                            <th>Qiimaynta Xulashada</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(res.models_evaluated).map(([name, m]) => `
                            <tr style="${name === res.best_model_name ? 'background: #dcfce7; font-weight: bold;' : ''}">
                                <td>${name} ${name === res.best_model_name ? '<span class="badge badge-success">Ugu Fiican ★</span>' : ''}</td>
                                <td>${m.mae}</td>
                                <td>${m.rmse}</td>
                                <td>${m.r2_score}</td>
                                <td>${m.selection_score}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } else {
            metricsHtml = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>Model / Algorithm</th>
                            <th>Accuracy</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>F1 Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(res.models_evaluated).map(([name, m]) => `
                            <tr style="${name === res.best_model_name ? 'background: #dcfce7; font-weight: bold;' : ''}">
                                <td>${name} ${name === res.best_model_name ? '<span class="badge badge-success">Ugu Fiican ★</span>' : ''}</td>
                                <td>${(m.accuracy * 100).toFixed(1)}%</td>
                                <td>${m.precision}</td>
                                <td>${m.recall}</td>
                                <td>${m.f1_score}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        }

        document.getElementById("selection-results-content").innerHTML = `
            <div class="alert alert-info">
                <strong>Sababta Xulashada:</strong> ${res.reason}
            </div>
            ${metricsHtml}
        `;
        loadDashboard();
    } catch (e) {
        btn.disabled = false;
        btn.innerText = "Bilow Isbarbardhigga (Compare Models)";
        alert("Khalad: " + e.message);
    }
}

// 6. Tab: Tababarka Model-ka (Model Training)
async function loadTrainingTab() {
    try {
        const modelsRes = await fetch(`${API_BASE}/api/ml/model-status`).then(r => r.json());
        const tbody = document.getElementById("trained-models-tbody");
        if (!modelsRes.models.length) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--muted);">Weli ma jiro moodal la tababaray.</td></tr>`;
            return;
        }
        tbody.innerHTML = modelsRes.models.map(m => `
            <tr>
                <td><strong>${m.model_name}</strong></td>
                <td>${m.algorithm}</td>
                <td><span class="badge badge-info">${m.model_version}</span></td>
                <td>${m.target_variable}</td>
                <td>${m.dataset_size}</td>
                <td>${m.is_active ? '<span class="badge badge-success">Firfircoon (Active)</span>' : '<span class="badge badge-secondary">Hore</span>'}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Training tab error:", e);
    }
}

async function triggerTraining(modelType) {
    const btn = document.getElementById("btn-train-" + modelType);
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Tababarku wuu socdaa...";
    }

    try {
        const res = await fetch(`${API_BASE}/api/ml/train`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model_type: modelType, include_demo: true })
        }).then(r => r.json());

        if (btn) {
            btn.disabled = false;
            btn.innerText = btn.getAttribute("data-original-text") || "Tababar";
        }

        const alertBox = document.getElementById("training-feedback-box");
        alertBox.style.display = "block";

        if (res.success) {
            alertBox.className = "alert alert-success";
            alertBox.innerHTML = `<strong>✓ Guul!</strong> ${res.message}`;
            loadTrainingTab();
            loadDashboard();
        } else {
            alertBox.className = "alert alert-warning";
            alertBox.innerHTML = `<strong>⚠ Digniin:</strong> ${res.message}`;
        }
    } catch (e) {
        if (btn) {
            btn.disabled = false;
            btn.innerText = btn.getAttribute("data-original-text") || "Tababar";
        }
        alert("Khalad: " + e.message);
    }
}

// 7. Tab: Tijaabinta & Qiimaynta (Model Evaluation)
async function loadEvaluationTab() {
    try {
        const res = await fetch(`${API_BASE}/api/ml/model-metrics`).then(r => r.json());
        const container = document.getElementById("evaluations-container");
        if (!res.evaluations.length) {
            container.innerHTML = `<div class="alert alert-info">Weli ma jirto qiimayn la sameeyay. Marka hore tababar model-yada.</div>`;
            return;
        }

        container.innerHTML = res.evaluations.map(ev => {
            const m = ev.metrics || {};
            let details = "";
            if (ev.model_type === "Regression") {
                details = `
                    <div class="grid-cols-4" style="margin-top: 12px;">
                        <div class="card"><div class="stat-info"><h4>MAE (Average Error)</h4><div class="stat-number">${m.mae || 0} min</div></div></div>
                        <div class="card"><div class="stat-info"><h4>RMSE</h4><div class="stat-number">${m.rmse || 0}</div></div></div>
                        <div class="card"><div class="stat-info"><h4>R² Score</h4><div class="stat-number text-success">${m.r2_score || 0}</div></div></div>
                        <div class="card"><div class="stat-info"><h4>Tayada Saxnaanta</h4><div style="font-weight: bold; margin-top: 6px;">${m.accuracy_quality || 'Diyaar'}</div></div></div>
                    </div>
                `;
            } else {
                details = `
                    <div class="grid-cols-4" style="margin-top: 12px;">
                        <div class="card"><div class="stat-info"><h4>Accuracy</h4><div class="stat-number text-success">${m.accuracy_percent || 0}%</div></div></div>
                        <div class="card"><div class="stat-info"><h4>Precision</h4><div class="stat-number">${m.precision || 0}</div></div></div>
                        <div class="card"><div class="stat-info"><h4>Recall</h4><div class="stat-number">${m.recall || 0}</div></div></div>
                        <div class="card"><div class="stat-info"><h4>F1 Score</h4><div class="stat-number">${m.f1_score || 0}</div></div></div>
                    </div>
                    ${m.confusion_matrix ? `
                        <div style="margin-top: 10px; font-size: 0.86rem;">
                            <strong>Confusion Matrix:</strong> [[TN: ${m.confusion_matrix[0][0]}, FP: ${m.confusion_matrix[0][1]}], [FN: ${m.confusion_matrix[1][0]}, TP: ${m.confusion_matrix[1][1]}]]
                        </div>
                    ` : ''}
                `;
            }

            return `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h3>${ev.model_name} <span class="badge badge-info">${ev.model_type}</span></h3>
                            <small class="text-muted">Taariikhda Tijaabada: ${ev.created_at} | Tijaabooyinka: ${ev.test_samples_count} tusaale</small>
                        </div>
                    </div>
                    ${details}
                </div>
            `;
        }).join("");
    } catch (e) {
        console.error("Evaluation tab error:", e);
    }
}

// 8. Tab: Saadaasha ML (Live Interactive Predictions)
async function loadPredictionTab() {
    // Fill printers & filaments dropdown
    try {
        const [printers, filaments] = await Promise.all([
            fetch(`${API_BASE}/api/printers`).then(r => r.json()),
            fetch(`${API_BASE}/api/filaments`).then(r => r.json())
        ]);
        const pSelect = document.getElementById("pred-printer");
        pSelect.innerHTML = printers.map(p => `<option value="${p.model}">${p.name} (${p.model})</option>`).join("");
    } catch (e) {}
}

async function triggerLivePrediction(event) {
    event.preventDefault();
    const form = event.target;
    const payload = {
        model_volume: parseFloat(form.volume.value),
        model_weight: parseFloat(form.weight.value),
        filament_type: form.filament_type.value,
        printer_model: form.printer_model.value,
        print_speed: parseFloat(form.print_speed.value),
        layer_height: parseFloat(form.layer_height.value),
        infill_percentage: parseFloat(form.infill.value),
        nozzle_temperature: parseFloat(form.nozzle_temp.value),
        bed_temperature: parseFloat(form.bed_temp.value),
        support_enabled: form.support_enabled.checked
    };

    const btn = document.getElementById("btn-predict-now");
    btn.disabled = true;
    btn.innerText = "Saadaashu way socotaa...";

    try {
        const res = await fetch(`${API_BASE}/api/ml/predict-all`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(r => r.json());

        btn.disabled = false;
        btn.innerText = "Xisaabi Saadaasha ML (Predict)";

        const resultBox = document.getElementById("live-prediction-results");
        resultBox.style.display = "block";

        const timeData = res.print_time;
        const filData = res.filament;
        const failData = res.failure_risk;

        document.getElementById("pred-time-output").innerHTML = timeData.success ? `
            <div style="font-size: 1.4rem; font-weight: bold; color: var(--primary);">${timeData.predicted_time_minutes} daqiiqo</div>
            <div style="font-size: 0.85rem; color: var(--muted);">${timeData.formatted_time}</div>
            <div style="font-size: 0.8rem; margin-top: 4px;">Xadka Hubanti La'aanta: <strong>${timeData.confidence_range}</strong></div>
            <small style="color: var(--muted); display: block; margin-top: 6px;">${timeData.disclaimer}</small>
        ` : `<div class="text-danger">${timeData.error}</div>`;

        document.getElementById("pred-filament-output").innerHTML = filData.success ? `
            <div style="font-size: 1.4rem; font-weight: bold; color: var(--success);">${filData.predicted_filament_grams} grams</div>
            <div style="font-size: 0.8rem; margin-top: 4px;">Xadka Hubanti La'aanta: <strong>${filData.confidence_range}</strong></div>
            <small style="color: var(--muted); display: block; margin-top: 6px;">${filData.disclaimer}</small>
        ` : `<div class="text-danger">${filData.error}</div>`;

        document.getElementById("pred-failure-output").innerHTML = failData.success ? `
            <div style="font-size: 1.4rem; font-weight: bold; color: ${failData.risk_color === 'danger' ? '#dc2626' : (failData.risk_color === 'warning' ? '#d97706' : '#16a34a')};">
                ${failData.risk_percentage}% - ${failData.risk_level}
            </div>
            <div style="margin-top: 8px;">
                <strong>Talooyinka Badbaadada:</strong>
                <ul style="padding-left: 20px; font-size: 0.82rem; margin-top: 4px;">
                    ${failData.recommendations.map(r => `<li>${r}</li>`).join("")}
                </ul>
            </div>
            <small style="color: var(--muted); display: block; margin-top: 6px;">${failData.disclaimer}</small>
        ` : `<div class="text-danger">${failData.error}</div>`;

        loadDashboard();
    } catch (e) {
        btn.disabled = false;
        btn.innerText = "Xisaabi Saadaasha ML (Predict)";
        alert("Khalad: " + e.message);
    }
}

// 9. Tab: Model Monitoring
async function loadMonitoringTab() {
    try {
        const report = await fetch(`${API_BASE}/api/ml/monitoring-report`).then(r => r.json());
        
        // Retraining card
        const retrain = report.retraining_assessment;
        document.getElementById("mon-retrain-status").innerHTML = `
            <div class="alert ${retrain.needs_retraining ? 'alert-warning' : 'alert-success'}">
                <strong>Xaaladda Dib u Tababarka:</strong> ${retrain.action_required}
            </div>
            <ul style="padding-left: 20px; font-size: 0.85rem;">
                ${retrain.reasons.map(r => `<li>${r}</li>`).join("")}
            </ul>
        `;

        // Drift card
        const drift = report.drift_assessment;
        document.getElementById("mon-drift-status").innerHTML = `
            <div class="alert ${drift.drift_detected ? 'alert-warning' : 'alert-info'}">
                <strong>Data Drift:</strong> ${drift.status}
            </div>
            <p style="font-size: 0.84rem; color: var(--muted);">${drift.recommendation}</p>
        `;

        // Recent predictions table
        const tbody = document.getElementById("mon-predictions-tbody");
        if (!report.recent_predictions.length) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--muted);">Weli ma jiro saadaal la diiwaangeliyay.</td></tr>`;
            return;
        }

        tbody.innerHTML = report.recent_predictions.map(p => `
            <tr>
                <td>#${p.id}</td>
                <td><strong>${p.prediction_type}</strong></td>
                <td>${p.prediction_output}</td>
                <td>${p.actual_value !== null ? p.actual_value : '<span class="badge badge-secondary">Weli lama gelin</span>'}</td>
                <td>${p.prediction_error !== null ? p.prediction_error : '-'}</td>
                <td>${p.created_at.substring(0, 19).replace('T', ' ')}</td>
                <td>
                    ${p.actual_value === null ? `
                        <button class="btn btn-outline btn-sm" onclick="promptActualValue(${p.id})">Geli Qiimaha Dhabta ah</button>
                    ` : '<span class="badge badge-success">La Hubiyay</span>'}
                </td>
            </tr>
        `).join("");

    } catch (e) {
        console.error("Monitoring tab error:", e);
    }
}

async function promptActualValue(predId) {
    const val = prompt("Fadlan geli qiimaha dhabta ah ee laga helay daabacaadda (Actual Value):");
    if (!val || isNaN(val)) return;

    try {
        const res = await fetch(`${API_BASE}/api/ml/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prediction_id: predId, actual_value: parseFloat(val) })
        }).then(r => r.json());

        alert("Xogta dhabta ah waa la kaydiyay, waxaana la xisaabiyay khaladka saadaasha!");
        loadMonitoringTab();
        loadDashboard();
    } catch (e) {
        alert("Khalad: " + e.message);
    }
}

// 10. Core 3D Printing Tabs (Printers, Jobs, Models, Filaments)
async function loadPrintersTab() {
    try {
        const printers = await fetch(`${API_BASE}/api/printers`).then(r => r.json());
        const grid = document.getElementById("printers-grid");
        grid.innerHTML = printers.map(p => `
            <div class="card">
                <div class="card-header">
                    <h3>${p.name}</h3>
                    <span class="badge ${p.status === 'printing' ? 'badge-info' : (p.status === 'idle' ? 'badge-success' : 'badge-warning')}">${p.status}</span>
                </div>
                <div style="font-size: 0.88rem; color: var(--slate); line-height: 1.6;">
                    <div><strong>Moodalka:</strong> ${p.model}</div>
                    <div><strong>Nozzle Temp:</strong> ${p.nozzle_temp}°C</div>
                    <div><strong>Bed Temp:</strong> ${p.bed_temp}°C</div>
                    <div><strong>Bed Size:</strong> ${p.bed_width}x${p.bed_depth}x${p.bed_height} mm</div>
                    <div><strong>IP:</strong> ${p.ip_address}</div>
                </div>
            </div>
        `).join("");
    } catch (e) {}
}

async function loadJobsTab() {
    try {
        const jobs = await fetch(`${API_BASE}/api/jobs`).then(r => r.json());
        const tbody = document.getElementById("jobs-tbody");
        if (!jobs.length) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--muted);">Weli ma jirto shaqo daabacaad ah.</td></tr>`;
            return;
        }

        tbody.innerHTML = jobs.map(j => `
            <tr>
                <td><strong>#${j.id}</strong></td>
                <td>${j.job_name}</td>
                <td>${j.printer_name || j.printer_model || '-'}</td>
                <td><span class="badge ${j.status === 'completed' ? 'badge-success' : (j.status === 'printing' ? 'badge-info' : (j.status === 'failed' ? 'badge-danger' : 'badge-secondary'))}">${j.status}</span></td>
                <td>Est: ${j.estimated_time_minutes}m | Act: ${j.actual_time_minutes || '-'}m</td>
                <td>Est: ${j.estimated_filament_g}g | Act: ${j.actual_filament_g || '-'}g</td>
                <td>${j.created_at ? j.created_at.substring(0, 19).replace('T', ' ') : '-'}</td>
                <td>
                    ${j.status === 'pending' ? `
                        <button class="btn btn-primary btn-sm" onclick="startJob(${j.id})">Bilaab</button>
                    ` : ''}
                    ${j.status === 'printing' ? `
                        <button class="btn btn-success btn-sm" onclick="completeJobPrompt(${j.id})">Dhammee</button>
                        <button class="btn btn-danger btn-sm" onclick="failJobPrompt(${j.id})">Fashil</button>
                    ` : ''}
                </td>
            </tr>
        `).join("");
    } catch (e) {}
}

async function startJob(jobId) {
    await fetch(`${API_BASE}/api/jobs/${jobId}/start`, { method: "POST" });
    loadJobsTab();
}

async function completeJobPrompt(jobId) {
    const actTime = prompt("Geli waqtiga dhabta ah ee daabacaaddu qaadatay (daqiiqado):", "65");
    if (!actTime) return;
    const actFil = prompt("Geli miisaanka dhabta ah ee filament-ka la isticmaalay (grams):", "26.5");
    if (!actFil) return;

    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ actual_time_minutes: parseFloat(actTime), actual_filament_g: parseFloat(actFil) })
    }).then(r => r.json());

    alert(res.message);
    loadJobsTab();
    loadDashboard();
}

async function failJobPrompt(jobId) {
    const actTime = prompt("Geli daqiiqadihii ay socotay intaanay fashilmin:", "20");
    if (!actTime) return;
    const reason = prompt("Sababta fashilka (tusaale: Bed Adhesion, Filament clog):", "Bed Adhesion");
    if (!reason) return;

    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/fail`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ actual_time_minutes: parseFloat(actTime), failure_reason: reason })
    }).then(r => r.json());

    alert(res.message);
    loadJobsTab();
    loadDashboard();
}

async function loadModelsTab() {
    try {
        const models = await fetch(`${API_BASE}/api/models`).then(r => r.json());
        const grid = document.getElementById("models-grid");
        grid.innerHTML = models.map(m => `
            <div class="card">
                <div class="card-header">
                    <h3>${m.name}</h3>
                    <span class="badge badge-info">${m.file_name}</span>
                </div>
                <div style="font-size: 0.88rem; color: var(--slate); line-height: 1.6;">
                    <div><strong>Volume:</strong> ${m.volume_cm3} cm³</div>
                    <div><strong>Weight:</strong> ${m.weight_g} g</div>
                    <div><strong>Dimensions:</strong> ${m.dimensions_xyz}</div>
                    <div><strong>Default Infill:</strong> ${m.default_infill}%</div>
                </div>
            </div>
        `).join("");
    } catch (e) {}
}

async function loadFilamentsTab() {
    try {
        const fils = await fetch(`${API_BASE}/api/filaments`).then(r => r.json());
        const grid = document.getElementById("filaments-grid");
        grid.innerHTML = fils.map(f => `
            <div class="card">
                <div class="card-header">
                    <h3>${f.brand} (${f.material})</h3>
                    <span class="badge badge-success">${f.color}</span>
                </div>
                <div style="font-size: 0.88rem; color: var(--slate); line-height: 1.6;">
                    <div><strong>Haray (Remaining):</strong> ${f.remaining_weight_g} / ${f.spool_weight_g} g</div>
                    <div><strong>Heerkulka Nozzle:</strong> ${f.temp_nozzle_min}°C - ${f.temp_nozzle_max}°C</div>
                    <div><strong>Heerkulka Bed:</strong> ${f.temp_bed}°C</div>
                    <div class="progress-bar-wrap" style="margin-top: 10px;">
                        <div class="progress-bar-fill" style="width: ${(f.remaining_weight_g / f.spool_weight_g * 100).toFixed(0)}%;"></div>
                    </div>
                </div>
            </div>
        `).join("");
    } catch (e) {}
}
