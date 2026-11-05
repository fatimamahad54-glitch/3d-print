import os
import json
import sqlite3
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from sklearn.model_selection import train_test_split
from backend.database import get_connection

CLEANED_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PROCESSED_FILE_PATH = os.path.join(CLEANED_DATA_DIR, "processed_dataset.csv")

FEATURE_COLUMNS = [
    "model_volume",
    "model_weight",
    "print_speed",
    "layer_height",
    "infill_percentage",
    "nozzle_temperature",
    "bed_temperature",
    "support_enabled",
    "filament_type",
    "printer_model"
]

NUMERIC_FEATURES = [
    "model_volume",
    "model_weight",
    "print_speed",
    "layer_height",
    "infill_percentage",
    "nozzle_temperature",
    "bed_temperature",
    "support_enabled"
]

CATEGORICAL_FEATURES = [
    "filament_type",
    "printer_model"
]

VALIDATION_RULES = {
    "print_speed": (1.0, 300.0),          # mm/s
    "layer_height": (0.04, 1.2),          # mm
    "infill_percentage": (0.0, 100.0),    # %
    "model_volume": (0.1, 10000.0),       # cm3
    "model_weight": (0.1, 5000.0),        # grams
    "nozzle_temperature": (150.0, 320.0), # Celsius
    "bed_temperature": (0.0, 150.0),      # Celsius
}

def load_data(include_demo: bool = True) -> pd.DataFrame:
    """
    1. Ka soo akhri xogta ceyriinka ah database-ka MachineLearningDataset.
    """
    conn = get_connection()
    query = "SELECT * FROM MachineLearningDataset"
    if not include_demo:
        query += " WHERE is_demo = 0"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def validate_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    2. Hubi missing values, data types, duplication, iyo validation rules adag.
    Soo celi DataFrame la xaqiijiyay iyo warbixin (report) caddaynaya xogta la helay ama la diiday.
    """
    report = {
        "initial_count": len(df),
        "missing_values_dropped": 0,
        "duplicates_removed": 0,
        "out_of_bounds_dropped": 0,
        "valid_count": 0,
        "validation_errors": []
    }

    if df.empty:
        report["validation_errors"].append("Dataset-ku waa maran yahay.")
        return df, report

    # Duplicate check on core features
    subset_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    dup_mask = df.duplicated(subset=subset_cols, keep='first')
    duplicates_count = int(dup_mask.sum())
    report["duplicates_removed"] = duplicates_count
    df = df[~dup_mask].copy()

    # Required target column check
    if "actual_print_time" in df.columns:
        # For print_time and filament target, check null or negative
        missing_targets = df["actual_print_time"].isnull() | (df["actual_print_time"] <= 0)
        dropped_missing = int(missing_targets.sum())
        report["missing_values_dropped"] += dropped_missing
        df = df[~missing_targets].copy()

    # Range validation rules
    valid_mask = pd.Series(True, index=df.index)
    for col, (min_val, max_val) in VALIDATION_RULES.items():
        if col in df.columns:
            # Check numeric type
            df[col] = pd.to_numeric(df[col], errors='coerce')
            rule_mask = (df[col] >= min_val) & (df[col] <= max_val)
            invalid_in_col = (~rule_mask).sum()
            if invalid_in_col > 0:
                report["validation_errors"].append(
                    f"{col} qiimo aan sax ahayn ({invalid_in_col} xabbo): xadka waa [{min_val} ilaa {max_val}]"
                )
            valid_mask = valid_mask & rule_mask

    dropped_bounds = int((~valid_mask).sum())
    report["out_of_bounds_dropped"] = dropped_bounds
    df = df[valid_mask].copy()

    # Success target column: print_success
    if "print_status" in df.columns:
        df["print_success"] = (df["print_status"].str.lower() == "completed").astype(int)

    report["valid_count"] = len(df)
    return df, report

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    3. Nadiifi xogta: sax formats, buuxi qiimayaasha maqan haddii macquul tahay,
    ka saar tiirarka aan loo baahnayn.
    """
    validated_df, report = validate_data(df)
    if validated_df.empty:
        return validated_df, report

    cleaned = validated_df.copy()

    # Clean categorical text
    for cat_col in CATEGORICAL_FEATURES:
        if cat_col in cleaned.columns:
            cleaned[cat_col] = cleaned[cat_col].fillna("Unknown").astype(str).str.strip()

    # Support enabled boolean
    if "support_enabled" in cleaned.columns:
        cleaned["support_enabled"] = cleaned["support_enabled"].astype(int)

    # Ensure float types on numeric
    for num_col in NUMERIC_FEATURES:
        if num_col in cleaned.columns:
            cleaned[num_col] = cleaned[num_col].astype(float)

    return cleaned, report

def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    8. Encode gareeyo categorical data (One-Hot Encoding) si model-ku u fahmo.
    """
    if df.empty:
        return df

    encoded_df = df.copy()

    # Use pd.get_dummies with prefix
    for col in CATEGORICAL_FEATURES:
        if col in encoded_df.columns:
            dummies = pd.get_dummies(encoded_df[col], prefix=col, drop_first=False)
            encoded_df = pd.concat([encoded_df, dummies], axis=1)

    return encoded_df

def prepare_training_data(
    target: str = "actual_print_time",
    test_size: float = 0.2,
    random_state: int = 42,
    include_demo: bool = True
) -> Dict[str, Any]:
    """
    10. Diyaari dataset-ka training iyo testing oo buuxa:
    - Splits: X_train, X_test, y_train, y_test
    - Metadata: feature names, dataset size
    """
    raw_df = load_data(include_demo=include_demo)
    cleaned_df, report = clean_data(raw_df)

    if len(cleaned_df) < 5:
        raise ValueError(
            f"Xogta saxda ah kuma filna ({len(cleaned_df)} records). "
            f"Fadlan ururi ama soo geli xog dheeraad ah ka hor tababarka."
        )

    if target not in cleaned_df.columns:
        raise ValueError(f"Tiirka bartilmaameedka ah '{target}' lagama helin dataset-ka.")

    y = cleaned_df[target]
    X_raw = cleaned_df[FEATURE_COLUMNS]

    # One-hot encode categoricals deterministically
    X = pd.get_dummies(X_raw, columns=CATEGORICAL_FEATURES)

    # Convert all to float
    X = X.astype(float)

    # Split dataset
    stratify = y if target == "print_success" and len(y.value_counts()) > 1 and y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )

    feature_names = list(X.columns)

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "feature_names": feature_names,
        "cleaning_report": report,
        "dataset_size": len(cleaned_df),
        "target_name": target
    }

def save_processed_data(df: pd.DataFrame, file_path: str = PROCESSED_FILE_PATH) -> str:
    """
    Kaydi xogta la nadiifiyay si loogu isticmaalo baadhis iyo kormeer.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    return file_path
