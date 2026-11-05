import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from ml.data_collection import (
    add_dataset_record,
    get_all_dataset,
    get_dataset_statistics,
    import_csv_data,
    seed_sample_demo_data
)
from ml.data_preprocessing import (
    load_data,
    clean_data,
    prepare_training_data
)
from ml.model_selection import compare_models
from ml.train_model import (
    train_print_time_model,
    train_filament_model,
    train_failure_model,
    train_all_models
)
from ml.evaluate_model import (
    get_latest_evaluations
)
from ml.model_registry import (
    get_all_registered_models,
    get_active_model_info
)
from ml.model_monitoring import (
    generate_monitoring_report,
    check_retraining_conditions,
    monitor_predictions
)
from backend.services.ml_service import MLService
from backend.services.ml_prediction_service import MLPredictionService

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

# Pydantic Schemas
class DataRecordSchema(BaseModel):
    printer_id: Optional[int] = None
    model_id: Optional[int] = None
    printer_model: Optional[str] = "Ender 3 V2"
    model_volume: float = Field(..., gt=0, description="Volume in cm3")
    model_weight: float = Field(..., gt=0, description="Weight in grams")
    filament_type: str = "PLA"
    print_speed: float = Field(..., gt=0, description="Speed mm/s")
    layer_height: float = Field(..., gt=0, description="Layer height mm")
    infill_percentage: float = Field(..., ge=0, le=100, description="Infill %")
    nozzle_temperature: float = Field(..., ge=150, le=320)
    bed_temperature: float = Field(..., ge=0, le=150)
    support_enabled: bool = False
    estimated_print_time: float = Field(..., gt=0)
    actual_print_time: Optional[float] = None
    filament_used: Optional[float] = None
    print_status: str = "completed"
    failure_reason: Optional[str] = None
    is_demo: bool = False

class PredictionInputSchema(BaseModel):
    model_volume: float = Field(15.0, gt=0)
    model_weight: float = Field(12.0, gt=0)
    filament_type: str = "PLA"
    printer_model: str = "Ender 3 V2"
    print_speed: float = Field(60.0, gt=0)
    layer_height: float = Field(0.2, gt=0)
    infill_percentage: float = Field(20.0, ge=0, le=100)
    nozzle_temperature: float = Field(205.0, ge=150, le=320)
    bed_temperature: float = Field(60.0, ge=0, le=150)
    support_enabled: bool = False

class TrainingRequestSchema(BaseModel):
    model_type: str = "all"  # 'time', 'filament', 'failure', 'all'
    include_demo: bool = True

class ActualFeedbackSchema(BaseModel):
    prediction_id: int
    actual_value: float

# 1. Step 1: Collect Data
@router.post("/data")
def create_dataset_record(record: DataRecordSchema):
    try:
        record_id = add_dataset_record(record.model_dump())
        return {
            "success": True,
            "id": record_id,
            "message": "Xogta si guul leh ayaa loogu daray MachineLearningDataset."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data")
def get_dataset(limit: int = 100, offset: int = 0, status: Optional[str] = None, include_demo: bool = True):
    records = get_all_dataset(limit=limit, offset=offset, status_filter=status, include_demo=include_demo)
    return {"count": len(records), "data": records}

@router.get("/data/statistics")
def get_statistics():
    return get_dataset_statistics()

@router.post("/data/import")
async def import_dataset_csv(file: UploadFile = File(...), is_demo: bool = Form(False)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Faylku waa inuu noqdaa CSV (.csv)")
    try:
        content = await file.read()
        text_content = content.decode("utf-8")
        result = import_csv_data(text_content, is_demo=is_demo)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Khalad ayaa dhacay marka CSV la akhriyay: {str(e)}")

@router.post("/data/seed-demo")
def seed_demo_data():
    return seed_sample_demo_data()

# 2. Step 2: Clean Data
@router.post("/clean")
def run_data_cleaning():
    return MLService.run_clean_pipeline()

# 3. Step 3: Choose a Model
@router.post("/select-model")
def select_model(task_type: str = Query("regression"), include_demo: bool = True):
    if task_type not in ["regression", "classification"]:
        raise HTTPException(status_code=400, detail="task_type waa inuu noqdaa 'regression' ama 'classification'")
    try:
        target = "actual_print_time" if task_type == "regression" else "print_success"
        data = prepare_training_data(target=target, include_demo=include_demo)
        comparison = compare_models(data["X_train"], data["X_test"], data["y_train"], data["y_test"], task_type=task_type)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 4. Step 4: Train Model
@router.post("/train")
def train_model_endpoint(req: TrainingRequestSchema):
    if req.model_type == "time":
        res = train_print_time_model(include_demo=req.include_demo)
    elif req.model_type == "filament":
        res = train_filament_model(include_demo=req.include_demo)
    elif req.model_type == "failure":
        res = train_failure_model(include_demo=req.include_demo)
    else:
        res = train_all_models(include_demo=req.include_demo)

    if not res.get("success") and res.get("insufficient_data"):
        return res
    return res

# 5. Step 5: Test & Evaluate
@router.post("/evaluate")
def evaluate_models_endpoint(include_demo: bool = True):
    return {
        "latest_evaluations": get_latest_evaluations(),
        "message": "Natiijooyinka qiimaynta rasmiga ah ee moodallada la tababaray."
    }

@router.get("/model-metrics")
def get_metrics_endpoint():
    return {
        "evaluations": get_latest_evaluations(),
        "models": get_all_registered_models()
    }

# 6. Step 6: Deploy & Predict
@router.get("/model-status")
def get_model_status():
    models = get_all_registered_models()
    return {
        "models_count": len(models),
        "models": models,
        "is_ready": any(m.get("is_active") == 1 for m in models)
    }

@router.post("/predict-print-time")
def predict_print_time_endpoint(req: PredictionInputSchema):
    return MLPredictionService.get_print_time_prediction(req.model_dump())

@router.post("/predict-filament")
def predict_filament_endpoint(req: PredictionInputSchema):
    return MLPredictionService.get_filament_prediction(req.model_dump())

@router.post("/predict-failure")
def predict_failure_endpoint(req: PredictionInputSchema):
    return MLPredictionService.get_failure_prediction(req.model_dump())

@router.post("/predict-all")
def predict_all_endpoint(req: PredictionInputSchema):
    return MLPredictionService.get_all_predictions(req.model_dump())

# 7. Step 7: Monitor & Improve
@router.get("/monitoring-report")
def get_monitoring_report():
    return generate_monitoring_report()

@router.post("/feedback")
def submit_actual_feedback(feedback: ActualFeedbackSchema):
    try:
        res = monitor_predictions(feedback.prediction_id, feedback.actual_value)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 8. Step Status Overview for Dashboard
@router.get("/steps-status")
def get_steps_status():
    return MLService.get_seven_steps_status()
