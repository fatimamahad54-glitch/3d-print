import os
import json
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

from backend.database import get_connection

def calculate_prediction_error(actual: float, predicted: float) -> Dict[str, float]:
    """
    Xisaabi khaladka saadaasha (MAE iyo Error Percentage).
    """
    abs_err = abs(actual - predicted)
    pct_err = (abs_err / actual * 100.0) if actual > 0 else 0.0
    return {
        "absolute_error": round(abs_err, 2),
        "percentage_error": round(pct_err, 2)
    }

def monitor_predictions(prediction_id: int, actual_value: float) -> Dict[str, Any]:
    """
    Kala saar oo la soco saadaashii la sameeyay marka shaqada la dhammeeyo
    oo la helo qiimaha dhabta ah.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM MLPrediction WHERE id = ?", (prediction_id,))
    pred_row = cursor.fetchone()
    if not pred_row:
        conn.close()
        raise ValueError(f"Saadaasha id-keedu yahay {prediction_id} lama helin.")

    predicted_val = pred_row["prediction_output"]
    err = calculate_prediction_error(actual_value, predicted_val)

    cursor.execute('''
    UPDATE MLPrediction
    SET actual_value = ?, prediction_error = ?
    WHERE id = ?
    ''', (actual_value, err["absolute_error"], prediction_id))

    conn.commit()
    conn.close()

    # Track overall performance
    track_model_performance(pred_row["prediction_type"], err["absolute_error"])

    return {
        "prediction_id": prediction_id,
        "predicted": predicted_val,
        "actual": actual_value,
        "errors": err
    }

def track_model_performance(metric_name: str, current_error: float):
    """
    Ku kaydi xogta kormeerka (monitoring) miiska MLMonitoring.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM MachineLearningDataset")
    ds_size = cursor.fetchone()[0]

    cursor.execute('''
    INSERT INTO MLMonitoring (metric_name, metric_value, dataset_size, details_json, created_at)
    VALUES (?, ?, ?, ?, ?)
    ''', (
        metric_name,
        round(current_error, 2),
        ds_size,
        json.dumps({"error": current_error}),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def detect_data_drift() -> Dict[str, Any]:
    """
    Baar haddii ay jirto data drift (isbeddel ku yimid xogta cusub marka la barbar dhigo xogta hore).
    Tusaale: heerkul cusub, qalab cusub, xawaare aad u sarreeya.
    """
    conn = get_connection()
    df = pd.read_sql_query("SELECT print_speed, layer_height, infill_percentage, nozzle_temperature FROM MachineLearningDataset ORDER BY id DESC LIMIT 50", conn)
    conn.close()

    if len(df) < 15:
        return {
            "drift_detected": False,
            "status": "Xog kooban (drift lama ogaan karo weli)",
            "details": "Waxaa loo baahan yahay ugu yaraan 15 shaqo oo cusub."
        }

    # Compare first 25 vs latest 25
    half = len(df) // 2
    recent = df.iloc[:half]
    older = df.iloc[half:]

    speed_change = abs(recent["print_speed"].mean() - older["print_speed"].mean())
    temp_change = abs(recent["nozzle_temperature"].mean() - older["nozzle_temperature"].mean())

    drift_found = bool((speed_change > 15.0) or (temp_change > 10.0))

    return {
        "drift_detected": drift_found,
        "speed_difference": float(round(speed_change, 2)),
        "temperature_difference": float(round(temp_change, 2)),
        "status": "Isbeddel weyn ayaa ka dhacay xogta daabacaadda (Data Drift)" if drift_found else "Xogtu waa deggan tahay (Stable)",
        "recommendation": "Dib u tababar model-ka si uu ula qabsado goobaha iyo heerkulka cusub." if drift_found else "Dib u tababar looma baahna hadda."
    }

def check_retraining_conditions() -> Dict[str, Any]:
    """
    Hubi 3-da shuruudood ee dib u tababarka:
    1. Xog cusub oo ku filan ma timid? (> 10 shaqo cusub tan iyo tababarkii hore)
    2. Model performance-ku ma liicay? (Celceliska khaladka hadda > 15%)
    3. User codsi manual ah miyuu sameeyay?
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT dataset_size, created_at FROM MLTrainingRun WHERE training_status = 'Completed' ORDER BY id DESC LIMIT 1")
    last_run = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM MachineLearningDataset")
    current_dataset_size = cursor.fetchone()[0]

    last_size = last_run["dataset_size"] if last_run else 0
    new_samples_added = max(0, current_dataset_size - last_size)

    # Average error in recent predictions
    cursor.execute("SELECT AVG(prediction_error) FROM MLPrediction WHERE prediction_error IS NOT NULL ORDER BY id DESC LIMIT 20")
    avg_err_row = cursor.fetchone()
    avg_recent_error = round(avg_err_row[0], 2) if avg_err_row and avg_err_row[0] else 0.0

    conn.close()

    drift = detect_data_drift()

    needs_retraining = False
    reasons = []

    if new_samples_added >= 10:
        needs_retraining = True
        reasons.append(f"{new_samples_added} xog cusub ayaa lagu daray database-ka.")

    if avg_recent_error > 20.0:
        needs_retraining = True
        reasons.append(f"Khaladka celceliska ah ee saadaasha ayaa gaaray {avg_recent_error} min.")

    if drift["drift_detected"]:
        needs_retraining = True
        reasons.append(drift["status"])

    return {
        "needs_retraining": bool(needs_retraining),
        "current_dataset_size": int(current_dataset_size),
        "last_trained_size": int(last_size),
        "new_samples_since_training": int(new_samples_added),
        "avg_recent_error": float(avg_recent_error),
        "reasons": reasons if reasons else ["Model-ku wuxuu ku shaqaynayaa heerkii loogu talagalay."],
        "action_required": "Fadlan guji 'Dib u Tababar Model-ka' si aad u hesho saadaal ka sii saxan." if needs_retraining else "Xaaladdu waa hagaag, dib u tababar looma baahna hadda."
    }

def generate_monitoring_report() -> Dict[str, Any]:
    """
    Soo celi warbixinta buuxda ee kormeerka ML Dashboard-ka.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Recent predictions vs actuals
    cursor.execute('''
    SELECT id, prediction_type, model_version, prediction_output, actual_value, prediction_error, created_at
    FROM MLPrediction
    ORDER BY id DESC LIMIT 15
    ''')
    recent_predictions = [dict(r) for r in cursor.fetchall()]

    # Training runs history
    cursor.execute("SELECT * FROM MLTrainingRun ORDER BY id DESC LIMIT 5")
    training_runs = [dict(r) for r in cursor.fetchall()]

    # Failure trend in dataset
    cursor.execute('''
    SELECT print_status, COUNT(*) as count
    FROM MachineLearningDataset
    GROUP BY print_status
    ''')
    status_counts = {r["print_status"]: r["count"] for r in cursor.fetchall()}

    conn.close()

    retraining_info = check_retraining_conditions()
    drift_info = detect_data_drift()

    return {
        "recent_predictions": recent_predictions,
        "training_runs": training_runs,
        "status_distribution": status_counts,
        "retraining_assessment": retraining_info,
        "drift_assessment": drift_info,
        "generated_at": datetime.now().isoformat()
    }
