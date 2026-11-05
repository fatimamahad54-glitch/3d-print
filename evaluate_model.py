import json
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from backend.database import get_connection

def evaluate_regression(y_true, y_pred) -> Dict[str, Any]:
    """
    Xisaabi dhammaan metrics-ka muhiimka ah ee regression-ka:
    - MAE (Mean Absolute Error)
    - RMSE (Root Mean Squared Error)
    - R² Score
    - Mean Percentage Error (MAPE)
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))

    # MAPE (filter zeros)
    non_zero = y_true != 0
    mape = float(np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100) if np.any(non_zero) else 0.0

    # Qiimaynta xaaladda saxnaanta (Evaluation Status)
    if r2 >= 0.85:
        accuracy_label = "Aad u Sareysa (Excellent)"
    elif r2 >= 0.70:
        accuracy_label = "Wanaagsan (Good)"
    elif r2 >= 0.50:
        accuracy_label = "Dhexdhexaad (Moderate)"
    else:
        accuracy_label = "Liidata (Low - Xog badan ayaa loo baahan yahay)"

    return {
        "mae": round(mae, 2),
        "mse": round(mse, 2),
        "rmse": round(rmse, 2),
        "r2_score": round(r2, 4),
        "mape_percent": round(mape, 2),
        "accuracy_quality": accuracy_label,
        "is_reliable": r2 >= 0.65
    }

def evaluate_classification(y_true, y_pred, y_prob=None) -> Dict[str, Any]:
    """
    Xisaabi dhammaan metrics-ka muhiimka ah ee classification-ka:
    - Accuracy
    - Precision
    - Recall
    - F1 Score
    - Confusion Matrix [[TN, FP], [FN, TP]]
    """
    y_true = np.array(y_true, dtype=int)
    y_pred = np.array(y_pred, dtype=int)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    cm = confusion_matrix(y_true, y_pred).tolist()

    if acc >= 0.85:
        quality_label = "Aad u Fiican (High Precision)"
    elif acc >= 0.70:
        quality_label = "Wanaagsan (Satisfactory)"
    else:
        quality_label = "Liidata (Needs more training data)"

    return {
        "accuracy": round(acc, 4),
        "accuracy_percent": round(acc * 100, 1),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": cm,
        "quality_label": quality_label,
        "is_reliable": acc >= 0.75
    }

def generate_metrics(model, X_test, y_test, task_type: str = "regression") -> Dict[str, Any]:
    """
    U samee metrics dhammaystiran model la tijaabinayo.
    """
    preds = model.predict(X_test)
    if task_type == "regression":
        metrics = evaluate_regression(y_test, preds)
    else:
        probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
        metrics = evaluate_classification(y_test, preds, probs)

    metrics["sample_count"] = len(y_test)
    return metrics

def compare_predictions(y_true, y_pred, max_samples: int = 10) -> List[Dict[str, Any]]:
    """
    Isbarbardhig toos ah oo u dhexeeya waxa dhabta ah iyo waxa la saadaaliyay.
    """
    y_true_list = list(y_true)[:max_samples]
    y_pred_list = list(y_pred)[:max_samples]

    comparisons = []
    for actual, pred in zip(y_true_list, y_pred_list):
        act_val = round(float(actual), 2)
        pred_val = round(float(pred), 2)
        diff = round(abs(act_val - pred_val), 2)
        pct_err = round((diff / act_val * 100), 1) if act_val > 0 else 0.0

        comparisons.append({
            "actual": act_val,
            "predicted": pred_val,
            "absolute_error": diff,
            "error_percentage": pct_err
        })
    return comparisons

def save_evaluation_results(model_name: str, model_type: str, metrics: Dict[str, Any], samples_count: int, notes: str = "") -> int:
    """
    Kaydi natiijada qiimaynta miiska database-ka ee MLEvaluation.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
    INSERT INTO MLEvaluation (model_name, model_type, evaluation_metrics, test_samples_count, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    '''
    now = datetime.now().isoformat()
    cursor.execute(query, (
        model_name,
        model_type,
        json.dumps(metrics, ensure_ascii=False),
        samples_count,
        notes,
        now
    ))
    eval_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return eval_id

def get_latest_evaluations() -> List[Dict[str, Any]]:
    """
    Soo celi qiimayntii ugu dambaysay ee model kasta.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MLEvaluation ORDER BY id DESC LIMIT 10")
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["metrics"] = json.loads(d["evaluation_metrics"])
        except Exception:
            d["metrics"] = {}
        rows.append(d)
    conn.close()
    return rows
