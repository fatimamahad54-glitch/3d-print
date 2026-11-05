import os
import json
import joblib
from datetime import datetime
from typing import Dict, Any, Optional
from backend.database import get_connection

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def register_model(
    model_name: str,
    model_type: str,
    target_variable: str,
    model_version: str,
    algorithm: str,
    file_path: str,
    dataset_size: int
) -> int:
    """
    Diiwaangeli ama cusboonaysii model-ka miiska MLModel.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Deactivate older versions of the same model_name
    cursor.execute("UPDATE MLModel SET is_active = 0 WHERE model_name = ?", (model_name,))

    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO MLModel (
        model_name, model_type, target_variable, model_version,
        algorithm, file_path, is_active, dataset_size, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
    ''', (
        model_name, model_type, target_variable, model_version,
        algorithm, file_path, dataset_size, now, now
    ))
    model_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return model_id

def get_active_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Soo celi xogta model-ka firfircoon (active model) ee loo isticmaalo saadaasha.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MLModel WHERE model_name = ? AND is_active = 1 ORDER BY id DESC LIMIT 1", (model_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_registered_models() -> list:
    """
    Liiska dhammaan moodallada la tababaray ee diiwaangashan.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MLModel ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
