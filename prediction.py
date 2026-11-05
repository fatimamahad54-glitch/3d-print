import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any

from ml.train_model import load_model
from backend.database import get_connection

def _format_input_features(raw_input: dict, expected_columns: list) -> pd.DataFrame:
    """
    U beddel input-ka dictionary qaab DataFrame oo la mid ah feature-radii lagu tababaray model-ka.
    Xisaabi One-Hot encoding adag oo buuxi wixii tiirar ah oo maqan 0.
    """
    row = {
        "model_volume": float(raw_input.get("model_volume", 15.0)),
        "model_weight": float(raw_input.get("model_weight", 12.0)),
        "print_speed": float(raw_input.get("print_speed", 50.0)),
        "layer_height": float(raw_input.get("layer_height", 0.2)),
        "infill_percentage": float(raw_input.get("infill_percentage", 20.0)),
        "nozzle_temperature": float(raw_input.get("nozzle_temperature", 200.0)),
        "bed_temperature": float(raw_input.get("bed_temperature", 60.0)),
        "support_enabled": 1 if raw_input.get("support_enabled") in (True, 1, "1", "true") else 0,
    }

    filament_type = str(raw_input.get("filament_type", "PLA")).strip()
    printer_model = str(raw_input.get("printer_model", "Ender 3 V2")).strip()

    # Create single-row DataFrame with expected columns initialized to 0.0
    df = pd.DataFrame(0.0, index=[0], columns=expected_columns)

    # Fill numeric columns
    for col, val in row.items():
        if col in df.columns:
            df.at[0, col] = float(val)

    # Fill one-hot dummy columns
    fil_dummy = f"filament_type_{filament_type}"
    if fil_dummy in df.columns:
        df.at[0, fil_dummy] = 1.0

    print_dummy = f"printer_model_{printer_model}"
    if print_dummy in df.columns:
        df.at[0, print_dummy] = 1.0

    return df

def log_prediction_to_db(pred_type: str, model_ver: str, raw_in: dict, pred_val: float, conf_interval: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO MLPrediction (prediction_type, model_version, prediction_input, prediction_output, confidence_interval, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        pred_type,
        model_ver,
        json.dumps(raw_in, ensure_ascii=False),
        round(pred_val, 2),
        conf_interval,
        datetime.now().isoformat()
    ))
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid

def predict_print_time(input_data: dict) -> Dict[str, Any]:
    """
    Saadaali waqtiga daabacaadda (Print Time in minutes).
    """
    try:
        loaded = load_model("print_time_predictor")
        model = loaded["model"]
        meta = loaded["metadata"]
    except Exception as e:
        return {
            "success": False,
            "error": "Model-ka waqtiga weli lama tababarin. Fadlan marka hore tababar model-ka.",
            "details": str(e)
        }

    features = meta["features"]
    X = _format_input_features(input_data, features)
    pred_minutes = float(model.predict(X)[0])
    pred_minutes = max(1.0, round(pred_minutes, 1))

    # Uncertainty estimate (± 8-12%)
    uncertainty_margin = round(pred_minutes * 0.10, 1)
    lower_bound = max(1.0, round(pred_minutes - uncertainty_margin, 1))
    upper_bound = round(pred_minutes + uncertainty_margin, 1)

    conf_str = f"[{lower_bound} min - {upper_bound} min]"
    log_prediction_to_db("Print Time", meta["version"], input_data, pred_minutes, conf_str)

    hours = int(pred_minutes // 60)
    mins = int(pred_minutes % 60)
    time_str = f"{hours} saacadood iyo {mins} daqiiqo" if hours > 0 else f"{mins} daqiiqo"

    return {
        "success": True,
        "predicted_time_minutes": pred_minutes,
        "formatted_time": time_str,
        "confidence_range": conf_str,
        "uncertainty_margin_minutes": uncertainty_margin,
        "model_version": meta["version"],
        "algorithm": meta["algorithm"],
        "disclaimer": "MUHIIM: Waqtigani waa qiyaas (estimate) ku salaysan xogta hore. Daabacaaddu way ka yaraan kartaa ama ka badnaan kartaa sababo la xiriira xaaladaha hardware-ka."
    }

def predict_filament_usage(input_data: dict) -> Dict[str, Any]:
    """
    Saadaali caddadka filament-ka la isticmaali doono (grams).
    """
    try:
        loaded = load_model("filament_usage_predictor")
        model = loaded["model"]
        meta = loaded["metadata"]
    except Exception as e:
        return {
            "success": False,
            "error": "Model-ka filament-ka weli lama tababarin. Fadlan tababar model-ka marka hore.",
            "details": str(e)
        }

    features = meta["features"]
    X = _format_input_features(input_data, features)
    pred_grams = float(model.predict(X)[0])
    pred_grams = max(0.5, round(pred_grams, 2))

    uncertainty_margin = round(pred_grams * 0.08, 2)
    lower_bound = max(0.5, round(pred_grams - uncertainty_margin, 2))
    upper_bound = round(pred_grams + uncertainty_margin, 2)
    conf_str = f"[{lower_bound}g - {upper_bound}g]"

    log_prediction_to_db("Filament Usage", meta["version"], input_data, pred_grams, conf_str)

    return {
        "success": True,
        "predicted_filament_grams": pred_grams,
        "confidence_range": conf_str,
        "uncertainty_margin_grams": uncertainty_margin,
        "model_version": meta["version"],
        "algorithm": meta["algorithm"],
        "disclaimer": "MUHIIM: Isticmaalka filament-ku waa qiyaas. Waxaa ku jiri kara khasaare yar (purging, skirt, supports)."
    }

def predict_failure_risk(input_data: dict) -> Dict[str, Any]:
    """
    Saadaali khatarta fashilka daabacaadda (Print Failure Risk Assessment).
    """
    try:
        loaded = load_model("failure_risk_predictor")
        model = loaded["model"]
        meta = loaded["metadata"]
    except Exception as e:
        return {
            "success": False,
            "error": "Model-ka khatarta fashilka weli lama tababarin. Fadlan tababar model-ka marka hore.",
            "details": str(e)
        }

    features = meta["features"]
    X = _format_input_features(input_data, features)

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        # class 0 = failed, class 1 = success
        classes = list(model.classes_)
        fail_idx = classes.index(0) if 0 in classes else -1
        fail_probability = float(probs[fail_idx]) if fail_idx != -1 else 0.05
    else:
        pred_val = model.predict(X)[0]
        fail_probability = 0.85 if pred_val == 0 else 0.10

    fail_pct = round(fail_probability * 100, 1)

    if fail_pct >= 60:
        risk_level = "Sare (High Risk)"
        risk_color = "danger"
        recommendations = [
            "Hoos u dhig xawaaraha daabacaadda (print speed).",
            "Hubi heerkulka sariirta (bed temperature) iyo nozzle-ka filament-kan.",
            "Kordhi layer height ama isticmaal brim/raft haddii ay warping tahay."
        ]
    elif fail_pct >= 30:
        risk_level = "Dhexdhexaad (Moderate Risk)"
        risk_color = "warning"
        recommendations = [
            "Hubi in sariirta daabacuhu si fiican u leveled tahay.",
            "Hubi adhesion-ka lakabka koowaad (first layer)."
        ]
    else:
        risk_level = "Hoose (Low Risk - Safe)"
        risk_color = "success"
        recommendations = [
            "Settings-ku waxay u muuqdaan kuwo wanaagsan.",
            "Bilaabidda daabacaadda waa badqab."
        ]

    log_prediction_to_db("Failure Risk", meta["version"], input_data, fail_pct, risk_level)

    return {
        "success": True,
        "risk_percentage": fail_pct,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "recommendations": recommendations,
        "model_version": meta["version"],
        "algorithm": meta["algorithm"],
        "disclaimer": "MUHIIM: Saadaashani waxay ku salaysan tahay xogta guulaha iyo fashilaadaha hore. Waxay muujinaysaa heerka khatarta (risk trend), ma aha natiijo 100% go'an."
    }

def predict_all(input_data: dict) -> Dict[str, Any]:
    """
    Wada saadaali Waqtiga, Filament-ka, iyo Khatarta Fashilka hal mar.
    """
    time_pred = predict_print_time(input_data)
    fil_pred = predict_filament_usage(input_data)
    fail_pred = predict_failure_risk(input_data)

    return {
        "print_time": time_pred,
        "filament": fil_pred,
        "failure_risk": fail_pred,
        "input_summary": input_data
    }
