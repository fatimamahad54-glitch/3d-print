import os
import io
import csv
import sqlite3
import pandas as pd
from datetime import datetime
from backend.database import get_connection

def add_dataset_record(data: dict) -> int:
    """
    Ku dar record cusub dataset-ka MachineLearningDataset.
    Xog kasta waa la hubiyaa ka hor intaan la gelin DB.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
    INSERT INTO MachineLearningDataset (
        printer_id, model_id, printer_model, model_volume, model_weight,
        filament_type, print_speed, layer_height, infill_percentage,
        nozzle_temperature, bed_temperature, support_enabled,
        estimated_print_time, actual_print_time, filament_used,
        print_status, failure_reason, is_demo, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    now = datetime.now().isoformat()
    cursor.execute(query, (
        data.get("printer_id"),
        data.get("model_id"),
        data.get("printer_model", "Unknown Printer"),
        float(data.get("model_volume", 0.0)),
        float(data.get("model_weight", 0.0)),
        str(data.get("filament_type", "PLA")),
        float(data.get("print_speed", 50.0)),
        float(data.get("layer_height", 0.2)),
        float(data.get("infill_percentage", 20.0)),
        float(data.get("nozzle_temperature", 200.0)),
        float(data.get("bed_temperature", 60.0)),
        1 if data.get("support_enabled") in (True, 1, "1", "true") else 0,
        float(data.get("estimated_print_time", 60.0)),
        float(data.get("actual_print_time")) if data.get("actual_print_time") is not None else None,
        float(data.get("filament_used")) if data.get("filament_used") is not None else None,
        str(data.get("print_status", "completed")),
        data.get("failure_reason"),
        1 if data.get("is_demo") in (True, 1, "1", "true") else 0,
        data.get("created_at", now)
    ))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def record_completed_job(job_id: int) -> int:
    """
    Si toos ah (automatic) ugu wareeji xogta shaqo daabacaad (print job) oo dhammaatay
    ama fashilantay dataset-ka Machine Learning-ka.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT j.*, p.model as printer_model_name, m.volume_cm3, m.weight_g, f.material as filament_material
    FROM print_jobs j
    LEFT JOIN printers p ON j.printer_id = p.id
    LEFT JOIN print_models m ON j.model_id = m.id
    LEFT JOIN filaments f ON j.filament_id = f.id
    WHERE j.id = ?
    ''', (job_id,))
    job = cursor.fetchone()

    if not job:
        conn.close()
        raise ValueError(f"Lama helin shaqada id-keedu yahay: {job_id}")

    record_data = {
        "printer_id": job["printer_id"],
        "model_id": job["model_id"],
        "printer_model": job["printer_model_name"] or "Standard FDM",
        "model_volume": job["volume_cm3"] or 15.0,
        "model_weight": job["weight_g"] or 12.0,
        "filament_type": job["filament_material"] or "PLA",
        "print_speed": job["print_speed"] or 60.0,
        "layer_height": job["layer_height"] or 0.2,
        "infill_percentage": job["infill_percentage"] or 20.0,
        "nozzle_temperature": job["nozzle_temp"] or 205.0,
        "bed_temperature": job["bed_temp"] or 60.0,
        "support_enabled": job["support_enabled"],
        "estimated_print_time": job["estimated_time_minutes"] or 60.0,
        "actual_print_time": job["actual_time_minutes"] or job["estimated_time_minutes"],
        "filament_used": job["actual_filament_g"] or job["estimated_filament_g"],
        "print_status": job["status"],
        "failure_reason": job["failure_reason"],
        "is_demo": 0
    }

    conn.close()
    return add_dataset_record(record_data)

def get_all_dataset(limit: int = 200, offset: int = 0, status_filter: str = None, include_demo: bool = True) -> list:
    """
    Akhri dhammaan xogta MachineLearningDataset oo leh kala soocid iyo filters.
    """
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if not include_demo:
        conditions.append("is_demo = 0")
    if status_filter:
        conditions.append("print_status = ?")
        params.append(status_filter)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM MachineLearningDataset {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_dataset_statistics() -> dict:
    """
    Soo celi xisaabaadka iyo dulmarka guud ee dataset-ka.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM MachineLearningDataset")
    total_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM MachineLearningDataset WHERE is_demo = 1")
    demo_records = cursor.fetchone()[0]

    real_records = total_records - demo_records

    cursor.execute("SELECT COUNT(*) FROM MachineLearningDataset WHERE print_status = 'completed'")
    completed_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM MachineLearningDataset WHERE print_status = 'failed'")
    failed_records = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(actual_print_time), AVG(filament_used), AVG(print_speed) FROM MachineLearningDataset WHERE actual_print_time > 0")
    avg_row = cursor.fetchone()
    avg_print_time = round(avg_row[0], 2) if avg_row and avg_row[0] else 0.0
    avg_filament_used = round(avg_row[1], 2) if avg_row and avg_row[1] else 0.0
    avg_speed = round(avg_row[2], 2) if avg_row and avg_row[2] else 0.0

    # Filament breakdown
    cursor.execute("SELECT filament_type, COUNT(*) as count FROM MachineLearningDataset GROUP BY filament_type")
    filament_counts = {row["filament_type"]: row["count"] for row in cursor.fetchall()}

    # Status distribution
    success_rate = round((completed_records / total_records * 100), 1) if total_records > 0 else 0.0

    conn.close()
    return {
        "total_records": total_records,
        "real_records": real_records,
        "demo_records": demo_records,
        "completed_records": completed_records,
        "failed_records": failed_records,
        "success_rate_percent": success_rate,
        "avg_print_time_minutes": avg_print_time,
        "avg_filament_used_grams": avg_filament_used,
        "avg_print_speed": avg_speed,
        "filament_distribution": filament_counts,
        "data_readiness": "Diyaar" if real_records >= 15 else "Xog Dheeraad ah ayaa loo baahan yahay"
    }

def import_csv_data(csv_text_or_path: str, is_demo: bool = False) -> dict:
    """
    Ka soo rar CSV file xogta oo ku dar database-ka iyadoo la xaqiijinayo badqabka xogta.
    """
    if os.path.exists(csv_text_or_path):
        with open(csv_text_or_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)
    else:
        stream = io.StringIO(csv_text_or_path)
        reader = csv.DictReader(stream)
        records = list(reader)

    imported_count = 0
    rejected_count = 0
    errors = []

    for idx, row in enumerate(records):
        try:
            # Field mapping & validation
            clean_record = {
                "printer_model": row.get("printer_model") or row.get("printer") or "Standard FDM",
                "model_volume": float(row.get("model_volume", 0)),
                "model_weight": float(row.get("model_weight", 0)),
                "filament_type": str(row.get("filament_type", "PLA")).strip(),
                "print_speed": float(row.get("print_speed", 50)),
                "layer_height": float(row.get("layer_height", 0.2)),
                "infill_percentage": float(row.get("infill_percentage", 20)),
                "nozzle_temperature": float(row.get("nozzle_temperature", 200)),
                "bed_temperature": float(row.get("bed_temperature", 60)),
                "support_enabled": 1 if str(row.get("support_enabled", "0")).lower() in ["1", "true", "yes"] else 0,
                "estimated_print_time": float(row.get("estimated_print_time", 60)),
                "actual_print_time": float(row.get("actual_print_time", 0)) if row.get("actual_print_time") else None,
                "filament_used": float(row.get("filament_used", 0)) if row.get("filament_used") else None,
                "print_status": "failed" if str(row.get("print_status", "")).lower() == "failed" else "completed",
                "failure_reason": row.get("failure_reason", ""),
                "is_demo": 1 if is_demo else 0
            }

            # Quick sanity check
            if clean_record["model_volume"] <= 0 or clean_record["print_speed"] <= 0:
                rejected_count += 1
                errors.append(f"Saf {idx+1}: Qiimayaasha Volume ama Speed waa 0 ama ka yar.")
                continue

            add_dataset_record(clean_record)
            imported_count += 1
        except Exception as e:
            rejected_count += 1
            errors.append(f"Saf {idx+1}: Khalad - {str(e)}")

    return {
        "success": True,
        "imported_count": imported_count,
        "rejected_count": rejected_count,
        "errors": errors[:5], # First 5 errors
        "message": f"{imported_count} safaf ah ayaa si guul leh loo soo galiyay. {rejected_count} ayaa la diiday."
    }

def seed_sample_demo_data():
    """
    Haddii dataset-ku maran yahay, soo geli sample xog ah oo si CAD loogu calaamadeeyay:
    is_demo = 1 (TUSAALE / DEMO - MA AHA XOG PRODUCTION AH).
    Tani waxay u saamaxaysaa user-ka inuu tijaabiyo 7-da steps isla markiiba.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM MachineLearningDataset")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        return {"status": "Xog hore ayaa u jirtay", "count": count}

    import random
    # Realistic 3D printing sample experiments with clear demo tag
    materials = ["PLA", "PETG", "ABS", "TPU"]
    printers = ["Ender 3 V2", "Prusa i3 MK3S+", "Bambu X1-Carbon", "Anycubic Kobra 2"]

    samples = []
    random.seed(42)

    for i in range(45):
        mat = random.choice(materials)
        printer = random.choice(printers)
        vol = round(random.uniform(5.0, 150.0), 2)
        density = 1.24 if mat == "PLA" else (1.27 if mat == "PETG" else (1.04 if mat == "ABS" else 1.21))
        infill = random.choice([10.0, 15.0, 20.0, 30.0, 50.0, 80.0])
        speed = random.choice([40.0, 50.0, 60.0, 80.0, 120.0]) if "Bambu" in printer else random.choice([40.0, 50.0, 60.0])
        layer_h = random.choice([0.12, 0.16, 0.20, 0.28])
        support = random.choice([0, 1])

        # Realistic physics based print time & filament consumption
        weight = round(vol * (0.2 + (infill / 100.0) * 0.8) * density, 2)
        speed_factor = 60.0 / speed
        layer_factor = 0.2 / layer_h
        support_factor = 1.25 if support else 1.0

        estimated_time = round((vol * 2.8 * speed_factor * layer_factor * support_factor) + 10, 1)
        # Random noise for actuals
        time_jitter = random.uniform(-0.08, 0.12)
        actual_time = round(estimated_time * (1.0 + time_jitter), 1)
        actual_filament = round(weight * random.uniform(1.01, 1.06), 2)

        # 12% failure rate under extreme conditions
        is_failure = False
        reason = None
        nozzle_t = 205.0 if mat == "PLA" else (235.0 if mat == "PETG" else (250.0 if mat == "ABS" else 220.0))
        bed_t = 60.0 if mat == "PLA" else (80.0 if mat == "PETG" else (100.0 if mat == "ABS" else 50.0))

        if speed > 100 and printer == "Ender 3 V2":
            is_failure = True
            reason = "Layer shifting xawaare sare dartiis"
        elif mat == "ABS" and bed_t < 90:
            is_failure = True
            reason = "Bed adhesion failure (warping)"
        elif i % 8 == 0:
            is_failure = True
            reason = "Filament clogging nozzle"

        status = "failed" if is_failure else "completed"
        if is_failure:
            actual_time = round(actual_time * random.uniform(0.2, 0.6), 1)

        record = {
            "printer_model": printer,
            "model_volume": vol,
            "model_weight": weight,
            "filament_type": mat,
            "print_speed": speed,
            "layer_height": layer_h,
            "infill_percentage": infill,
            "nozzle_temperature": nozzle_t,
            "bed_temperature": bed_t,
            "support_enabled": support,
            "estimated_print_time": estimated_time,
            "actual_print_time": actual_time,
            "filament_used": actual_filament,
            "print_status": status,
            "failure_reason": reason,
            "is_demo": 1 # CLEARLY LABELED DEMO / SAMPLE DATA
        }
        add_dataset_record(record)

    return {"status": "Guul", "count": 45, "message": "45 tusaale oo DEMO ah ayaa lagu daray dataset-ka (si cad ayaa loo calaamadeeyay is_demo=1)"}
