import os
import time
import json
import joblib
from datetime import datetime
from typing import Dict, Any, Tuple

from ml.data_preprocessing import prepare_training_data
from ml.model_selection import compare_models
from ml.evaluate_model import generate_metrics, save_evaluation_results
from ml.model_registry import register_model, MODELS_DIR
from backend.database import get_connection

MIN_SAMPLES_REQUIRED = 8

def save_model(model_obj: Any, model_name: str, metadata: dict) -> str:
    """
    Ku kaydi model-ka iyo xogtiisa qaabaysan ml/models/ folder-ka adoo isticmaalaya joblib.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    file_path = os.path.join(MODELS_DIR, f"{model_name}.joblib")
    payload = {
        "model": model_obj,
        "metadata": metadata,
        "saved_at": datetime.now().isoformat()
    }
    joblib.dump(payload, file_path)
    return file_path

def load_model(model_name: str) -> Dict[str, Any]:
    """
    Ka soo akhri model-ka iyo metadata-giisa faylka disk-ga.
    """
    file_path = os.path.join(MODELS_DIR, f"{model_name}.joblib")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Faylka model-ka lama helin: {file_path}")
    return joblib.load(file_path)

def log_training_run(model_name: str, model_type: str, dataset_size: int, status: str, duration: float, metrics: dict = None, error: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO MLTrainingRun (model_name, model_type, dataset_size, training_status, train_duration_seconds, metrics_json, error_message, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        model_name,
        model_type,
        dataset_size,
        status,
        round(duration, 3),
        json.dumps(metrics or {}, ensure_ascii=False),
        error,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def train_print_time_model(include_demo: bool = True) -> Dict[str, Any]:
    """
    Tababar model-ka saadaaliya waqtiga daabacaadda (actual_print_time).
    Regression Task: Isbarbardhig Linear, Random Forest, Gradient Boosting.
    """
    start_time = time.time()
    model_name = "print_time_predictor"

    try:
        data = prepare_training_data(target="actual_print_time", include_demo=include_demo)
    except Exception as e:
        log_training_run(model_name, "Regression", 0, "Failed", 0.0, error=str(e))
        return {
            "success": False,
            "message": f"Xogta kuma filna tababarka model-ka: {str(e)} Fadlan ururi xog dheeraad ah.",
            "insufficient_data": True
        }

    dataset_size = data["dataset_size"]
    if dataset_size < MIN_SAMPLES_REQUIRED:
        msg = f"Dataset-ku wuxuu ka kooban yahay {dataset_size} xabbo oo keliya. Ugu yaraan {MIN_SAMPLES_REQUIRED} xog dhab ah ayaa loo baahan yahay."
        log_training_run(model_name, "Regression", dataset_size, "Insufficient Data", 0.0, error=msg)
        return {
            "success": False,
            "message": msg,
            "insufficient_data": True
        }

    # Compare regression algorithms
    comparison = compare_models(data["X_train"], data["X_test"], data["y_train"], data["y_test"], task_type="regression")
    best_model = comparison["best_model_instance"]
    best_algo_name = comparison["best_model_name"]

    # Re-fit best model on full train set & generate final test metrics
    best_model.fit(data["X_train"], data["y_train"])
    test_metrics = generate_metrics(best_model, data["X_test"], data["y_test"], task_type="regression")

    duration = time.time() - start_time
    version = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Metadata
    metadata = {
        "model_name": model_name,
        "model_type": "Regression",
        "target": "actual_print_time",
        "algorithm": best_algo_name,
        "version": version,
        "features": data["feature_names"],
        "dataset_size": dataset_size,
        "metrics": test_metrics,
        "comparison": comparison["models_evaluated"]
    }

    file_path = save_model(best_model, model_name, metadata)
    register_model(model_name, "Regression", "actual_print_time", version, best_algo_name, file_path, dataset_size)
    save_evaluation_results(model_name, "Regression", test_metrics, len(data["y_test"]), f"Doortay {best_algo_name}")
    log_training_run(model_name, "Regression", dataset_size, "Completed", duration, test_metrics)

    return {
        "success": True,
        "model_name": model_name,
        "algorithm": best_algo_name,
        "version": version,
        "dataset_size": dataset_size,
        "metrics": test_metrics,
        "duration_seconds": round(duration, 2),
        "message": f"Model-ka Waqtiga Daabacaadda ({best_algo_name}) si guul leh ayaa loo tababaray."
    }

def train_filament_model(include_demo: bool = True) -> Dict[str, Any]:
    """
    Tababar model-ka saadaaliya caddadka filament-ka la isticmaali doono (filament_used).
    Regression Task.
    """
    start_time = time.time()
    model_name = "filament_usage_predictor"

    try:
        data = prepare_training_data(target="filament_used", include_demo=include_demo)
    except Exception as e:
        log_training_run(model_name, "Regression", 0, "Failed", 0.0, error=str(e))
        return {
            "success": False,
            "message": f"Xogta kuma filna tababarka model-ka filament-ka: {str(e)}",
            "insufficient_data": True
        }

    dataset_size = data["dataset_size"]
    if dataset_size < MIN_SAMPLES_REQUIRED:
        msg = f"Xogta filament-ku kuma filna tababarka ({dataset_size} xabbo). Fadlan ururi ugu yaraan {MIN_SAMPLES_REQUIRED} xog ah."
        log_training_run(model_name, "Regression", dataset_size, "Insufficient Data", 0.0, error=msg)
        return {"success": False, "message": msg, "insufficient_data": True}

    comparison = compare_models(data["X_train"], data["X_test"], data["y_train"], data["y_test"], task_type="regression")
    best_model = comparison["best_model_instance"]
    best_algo_name = comparison["best_model_name"]

    best_model.fit(data["X_train"], data["y_train"])
    test_metrics = generate_metrics(best_model, data["X_test"], data["y_test"], task_type="regression")

    duration = time.time() - start_time
    version = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    metadata = {
        "model_name": model_name,
        "model_type": "Regression",
        "target": "filament_used",
        "algorithm": best_algo_name,
        "version": version,
        "features": data["feature_names"],
        "dataset_size": dataset_size,
        "metrics": test_metrics,
        "comparison": comparison["models_evaluated"]
    }

    file_path = save_model(best_model, model_name, metadata)
    register_model(model_name, "Regression", "filament_used", version, best_algo_name, file_path, dataset_size)
    save_evaluation_results(model_name, "Regression", test_metrics, len(data["y_test"]), f"Doortay {best_algo_name}")
    log_training_run(model_name, "Regression", dataset_size, "Completed", duration, test_metrics)

    return {
        "success": True,
        "model_name": model_name,
        "algorithm": best_algo_name,
        "version": version,
        "dataset_size": dataset_size,
        "metrics": test_metrics,
        "duration_seconds": round(duration, 2),
        "message": f"Model-ka Isticmaalka Filament-ka ({best_algo_name}) si guul leh ayaa loo tababaray."
    }

def train_failure_model(include_demo: bool = True) -> Dict[str, Any]:
    """
    Tababar classification model saadaaliya khatarta fashilka daabacaadda (print_success: 1=guul, 0=fashil).
    Classification Task: Random Forest Classifier.
    """
    start_time = time.time()
    model_name = "failure_risk_predictor"

    try:
        data = prepare_training_data(target="print_success", include_demo=include_demo)
    except Exception as e:
        log_training_run(model_name, "Classification", 0, "Failed", 0.0, error=str(e))
        return {
            "success": False,
            "message": f"Xogta kuma filna classification-ka: {str(e)}",
            "insufficient_data": True
        }

    dataset_size = data["dataset_size"]
    # Check if we have both classes (0 and 1)
    unique_classes = set(data["y_train"].unique()).union(set(data["y_test"].unique()))
    if len(unique_classes) < 2:
        msg = "Xogtu ma laha labada natiijo ee guul iyo fashil (waxay leedahay 1 natiijo oo keliya). Fadlan xog fashil ah ama guul ah ku dar si model-ku u kala barto."
        log_training_run(model_name, "Classification", dataset_size, "Class Imbalance", 0.0, error=msg)
        return {"success": False, "message": msg, "insufficient_data": True}

    comparison = compare_models(data["X_train"], data["X_test"], data["y_train"], data["y_test"], task_type="classification")
    best_model = comparison["best_model_instance"]
    best_algo_name = comparison["best_model_name"]

    best_model.fit(data["X_train"], data["y_train"])
    test_metrics = generate_metrics(best_model, data["X_test"], data["y_test"], task_type="classification")

    duration = time.time() - start_time
    version = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    metadata = {
        "model_name": model_name,
        "model_type": "Classification",
        "target": "print_success",
        "algorithm": best_algo_name,
        "version": version,
        "features": data["feature_names"],
        "dataset_size": dataset_size,
        "metrics": test_metrics,
        "comparison": comparison["models_evaluated"]
    }

    file_path = save_model(best_model, model_name, metadata)
    register_model(model_name, "Classification", "print_success", version, best_algo_name, file_path, dataset_size)
    save_evaluation_results(model_name, "Classification", test_metrics, len(data["y_test"]), f"Doortay {best_algo_name}")
    log_training_run(model_name, "Classification", dataset_size, "Completed", duration, test_metrics)

    return {
        "success": True,
        "model_name": model_name,
        "algorithm": best_algo_name,
        "version": version,
        "dataset_size": dataset_size,
        "metrics": test_metrics,
        "duration_seconds": round(duration, 2),
        "message": f"Model-ka Khatarta Fashilka ({best_algo_name}) si guul leh ayaa loo tababaray."
    }

def train_all_models(include_demo: bool = True) -> Dict[str, Any]:
    """
    Hal mar tababar dhammaan moodallada (Print Time, Filament, Failure Risk).
    """
    time_res = train_print_time_model(include_demo=include_demo)
    fil_res = train_filament_model(include_demo=include_demo)
    fail_res = train_failure_model(include_demo=include_demo)

    success_count = sum(1 for r in [time_res, fil_res, fail_res] if r.get("success"))

    return {
        "success": success_count > 0,
        "successful_models": success_count,
        "total_attempted": 3,
        "results": {
            "print_time": time_res,
            "filament": fil_res,
            "failure_risk": fail_res
        },
        "message": f"{success_count} ka mid ah 3 moodal ayaa si guul leh loo tababaray."
    }
