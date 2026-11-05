from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.database import get_connection
from ml.data_collection import record_completed_job

core_router = APIRouter(prefix="/api", tags=["3D Printing Core"])

class PrinterCreate(BaseModel):
    name: str
    model: str
    nozzle_diameter: float = 0.4
    bed_width: float = 220.0
    bed_depth: float = 220.0
    bed_height: float = 250.0
    ip_address: Optional[str] = "192.168.1.100"

class ModelCreate(BaseModel):
    name: str
    file_name: str
    file_size_kb: float = 1200.0
    volume_cm3: float
    weight_g: float
    dimensions_xyz: str = "50x50x50mm"
    default_infill: float = 20.0
    default_layer_height: float = 0.2

class FilamentCreate(BaseModel):
    brand: str
    material: str
    color: str = "Madow"
    remaining_weight_g: float = 1000.0
    temp_nozzle_min: float = 200.0
    temp_nozzle_max: float = 220.0
    temp_bed: float = 60.0

class JobCreate(BaseModel):
    printer_id: int
    model_id: int
    filament_id: int
    job_name: str
    print_speed: float = 60.0
    layer_height: float = 0.2
    infill_percentage: float = 20.0
    nozzle_temp: float = 205.0
    bed_temp: float = 60.0
    support_enabled: bool = False
    estimated_time_minutes: float = 60.0
    estimated_filament_g: float = 25.0

class JobComplete(BaseModel):
    actual_time_minutes: float
    actual_filament_g: float

class JobFail(BaseModel):
    actual_time_minutes: float
    failure_reason: str

# Printers
@core_router.get("/printers")
def get_printers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM printers")
    printers = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return printers

@core_router.post("/printers")
def create_printer(p: PrinterCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO printers (name, model, nozzle_diameter, bed_width, bed_depth, bed_height, ip_address)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (p.name, p.model, p.nozzle_diameter, p.bed_width, p.bed_depth, p.bed_height, p.ip_address))
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": pid, "message": "Daabacaha si guul leh ayaa loo diiwaangeliyay."}

# Models
@core_router.get("/models")
def get_models():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM print_models")
    models = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return models

@core_router.post("/models")
def create_model(m: ModelCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO print_models (name, file_name, file_size_kb, volume_cm3, weight_g, dimensions_xyz, default_infill, default_layer_height)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (m.name, m.file_name, m.file_size_kb, m.volume_cm3, m.weight_g, m.dimensions_xyz, m.default_infill, m.default_layer_height))
    mid = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": mid, "message": "Moodalka 3D si guul leh ayaa loo keydiyay."}

# Filaments
@core_router.get("/filaments")
def get_filaments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM filaments")
    filaments = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return filaments

@core_router.post("/filaments")
def create_filament(f: FilamentCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO filaments (brand, material, color, remaining_weight_g, temp_nozzle_min, temp_nozzle_max, temp_bed)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (f.brand, f.material, f.color, f.remaining_weight_g, f.temp_nozzle_min, f.temp_nozzle_max, f.temp_bed))
    fid = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": fid, "message": "Filament-ka si guul leh ayaa loo diiwaangeliyay."}

# Print Jobs
@core_router.get("/jobs")
def get_jobs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT j.*, p.name as printer_name, p.model as printer_model, m.name as model_name, f.material as filament_type
    FROM print_jobs j
    LEFT JOIN printers p ON j.printer_id = p.id
    LEFT JOIN print_models m ON j.model_id = m.id
    LEFT JOIN filaments f ON j.filament_id = f.id
    ORDER BY j.id DESC
    ''')
    jobs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jobs

@core_router.post("/jobs")
def create_job(job: JobCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO print_jobs (
        printer_id, model_id, filament_id, job_name, status,
        print_speed, layer_height, infill_percentage, nozzle_temp, bed_temp,
        support_enabled, estimated_time_minutes, estimated_filament_g
    ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job.printer_id, job.model_id, job.filament_id, job.job_name,
        job.print_speed, job.layer_height, job.infill_percentage,
        job.nozzle_temp, job.bed_temp, 1 if job.support_enabled else 0,
        job.estimated_time_minutes, job.estimated_filament_g
    ))
    jid = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": jid, "message": "Shaqada daabacaadda si guul leh ayaa loo bilaabay safka (queued)."}

@core_router.post("/jobs/{job_id}/start")
def start_job(job_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE print_jobs SET status = 'printing' WHERE id = ?", (job_id,))
    cursor.execute("SELECT printer_id FROM print_jobs WHERE id = ?", (job_id,))
    p = cursor.fetchone()
    if p:
        cursor.execute("UPDATE printers SET status = 'printing' WHERE id = ?", (p["printer_id"],))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Shaqada daabacaaddu hadda way socotaa."}

@core_router.post("/jobs/{job_id}/complete")
def complete_job(job_id: int, payload: JobComplete):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
    UPDATE print_jobs
    SET status = 'completed', actual_time_minutes = ?, actual_filament_g = ?, completed_at = ?
    WHERE id = ?
    ''', (payload.actual_time_minutes, payload.actual_filament_g, now, job_id))

    cursor.execute("SELECT printer_id, filament_id FROM print_jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE printers SET status = 'idle' WHERE id = ?", (row["printer_id"],))
        cursor.execute("UPDATE filaments SET remaining_weight_g = MAX(0, remaining_weight_g - ?) WHERE id = ?", (payload.actual_filament_g, row["filament_id"]))

    conn.commit()
    conn.close()

    # Step 1 Automatic Ingestion: Add this completed job to MachineLearningDataset!
    dataset_rec_id = record_completed_job(job_id)

    return {
        "success": True,
        "message": "Shaqadu way dhammaatay! Xogteeda dhabta ah si automatic ah ayaa loogu daray MachineLearningDataset.",
        "dataset_record_id": dataset_rec_id
    }

@core_router.post("/jobs/{job_id}/fail")
def fail_job(job_id: int, payload: JobFail):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
    UPDATE print_jobs
    SET status = 'failed', actual_time_minutes = ?, failure_reason = ?, completed_at = ?
    WHERE id = ?
    ''', (payload.actual_time_minutes, payload.failure_reason, now, job_id))

    cursor.execute("SELECT printer_id FROM print_jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE printers SET status = 'idle' WHERE id = ?", (row["printer_id"],))

    conn.commit()
    conn.close()

    # Step 1 Automatic Ingestion: Add failure record to ML dataset for failure prediction learning
    dataset_rec_id = record_completed_job(job_id)

    return {
        "success": True,
        "message": "Fashilka waa la diiwaangeliyay. Xogta waxaa loo diray Machine Learning dataset si looga barto khatarta.",
        "dataset_record_id": dataset_rec_id
    }
