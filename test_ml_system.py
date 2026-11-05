import pytest
import os
import json
import numpy as np
import pandas as pd
from backend.database import init_db, get_connection
from ml.data_collection import (
    add_dataset_record,
    get_all_dataset,
    get_dataset_statistics,
    seed_sample_demo_data
)
from ml.data_preprocessing import (
    load_data,
    validate_data,
    clean_data,
    prepare_training_data
)
from ml.model_selection import (
    select_regression_model,
    select_classification_model,
    compare_models
)
from ml.train_model import (
    train_print_time_model,
    train_filament_model,
    train_failure_model,
    train_all_models
)
from ml.evaluate_model import (
    evaluate_regression,
    evaluate_classification
)
from ml.prediction import (
    predict_print_time,
    predict_filament_usage,
    predict_failure_risk,
    predict_all
)
from ml.model_monitoring import (
    calculate_prediction_error,
    detect_data_drift,
    check_retraining_conditions,
    generate_monitoring_report
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Diyaari database-ka iyo xogta tijaabada"""
    init_db()
    seed_sample_demo_data()

# 1. Test Step 1: Collect Data
def test_data_collection():
    rec = {
        "printer_model": "Ender 3 V2",
        "model_volume": 25.0,
        "model_weight": 20.0,
        "filament_type": "PLA",
        "print_speed": 60.0,
        "layer_height": 0.2,
        "infill_percentage": 20.0,
        "nozzle_temperature": 205.0,
        "bed_temperature": 60.0,
        "support_enabled": False,
        "estimated_print_time": 90.0,
        "actual_print_time": 95.0,
        "filament_used": 21.0,
        "print_status": "completed",
        "is_demo": 1
    }
    rec_id = add_dataset_record(rec)
    assert rec_id > 0

    stats = get_dataset_statistics()
    assert stats["total_records"] > 0
    assert "filament_distribution" in stats

# 2. Test Step 2: Data Preprocessing & Validation
def test_data_preprocessing():
    raw_df = load_data(include_demo=True)
    assert not raw_df.empty

    cleaned_df, report = clean_data(raw_df)
    assert report["valid_count"] > 0
    assert report["out_of_bounds_dropped"] >= 0

    prep = prepare_training_data(target="actual_print_time", include_demo=True)
    assert len(prep["X_train"]) > 0
    assert len(prep["X_test"]) > 0
    assert len(prep["y_train"]) == len(prep["X_train"])

# 3. Test Step 3: Model Selection
def test_model_selection():
    prep = prepare_training_data(target="actual_print_time", include_demo=True)
    comp = compare_models(prep["X_train"], prep["X_test"], prep["y_train"], prep["y_test"], task_type="regression")
    assert "best_model_name" in comp
    assert "models_evaluated" in comp
    assert len(comp["models_evaluated"]) == 3

# 4. Test Step 4: Model Training
def test_model_training():
    res = train_all_models(include_demo=True)
    assert res["success"] is True
    assert res["successful_models"] >= 2
    assert "print_time" in res["results"]
    assert res["results"]["print_time"]["success"] is True

# 5. Test Step 5: Model Evaluation
def test_model_evaluation():
    # Regression metrics
    y_true = [100.0, 150.0, 80.0, 200.0]
    y_pred = [105.0, 142.0, 85.0, 195.0]
    reg_eval = evaluate_regression(y_true, y_pred)
    assert reg_eval["mae"] > 0
    assert reg_eval["r2_score"] > 0.8

    # Classification metrics
    c_true = [1, 1, 0, 1, 0, 1]
    c_pred = [1, 1, 0, 1, 1, 1]
    clf_eval = evaluate_classification(c_true, c_pred)
    assert "accuracy" in clf_eval
    assert "confusion_matrix" in clf_eval

# 6. Test Step 6: Prediction API
def test_predictions():
    sample_input = {
        "model_volume": 30.0,
        "model_weight": 24.0,
        "filament_type": "PLA",
        "printer_model": "Ender 3 V2",
        "print_speed": 60.0,
        "layer_height": 0.2,
        "infill_percentage": 20.0,
        "nozzle_temperature": 205.0,
        "bed_temperature": 60.0,
        "support_enabled": False
    }

    t_pred = predict_print_time(sample_input)
    assert t_pred["success"] is True
    assert t_pred["predicted_time_minutes"] > 0
    assert "disclaimer" in t_pred

    f_pred = predict_filament_usage(sample_input)
    assert f_pred["success"] is True
    assert f_pred["predicted_filament_grams"] > 0

    fail_pred = predict_failure_risk(sample_input)
    assert fail_pred["success"] is True
    assert "risk_percentage" in fail_pred

# 7. Test Step 7: Monitoring
def test_monitoring():
    err = calculate_prediction_error(100.0, 110.0)
    assert err["absolute_error"] == 10.0

    drift = detect_data_drift()
    assert "drift_detected" in drift

    retrain = check_retraining_conditions()
    assert "needs_retraining" in retrain

    report = generate_monitoring_report()
    assert "retraining_assessment" in report
