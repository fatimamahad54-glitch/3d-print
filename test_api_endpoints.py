import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

def test_steps_status_endpoint():
    res = client.get("/api/ml/steps-status")
    assert res.status_code == 200
    data = res.json()
    assert "steps" in data
    assert len(data["steps"]) == 7
    assert "progress_percentage" in data

def test_data_statistics_endpoint():
    res = client.get("/api/ml/data/statistics")
    assert res.status_code == 200
    assert "total_records" in res.json()

def test_prediction_endpoint():
    payload = {
        "model_volume": 20.0,
        "model_weight": 16.0,
        "filament_type": "PLA",
        "printer_model": "Ender 3 V2",
        "print_speed": 55.0,
        "layer_height": 0.2,
        "infill_percentage": 20.0,
        "nozzle_temperature": 205.0,
        "bed_temperature": 60.0,
        "support_enabled": False
    }
    res = client.post("/api/ml/predict-all", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "print_time" in body
    assert "filament" in body
    assert "failure_risk" in body

def test_monitoring_report_endpoint():
    res = client.get("/api/ml/monitoring-report")
    assert res.status_code == 200
    assert "retraining_assessment" in res.json()

def test_core_3d_printers():
    res = client.get("/api/printers")
    assert res.status_code == 200
    assert len(res.json()) >= 1
