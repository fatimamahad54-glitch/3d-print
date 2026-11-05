import os
import json
from typing import Dict, Any, List

from ml.data_collection import (
    add_dataset_record,
    get_all_dataset,
    get_dataset_statistics,
    import_csv_data,
    seed_sample_demo_data,
    record_completed_job
)
from ml.data_preprocessing import (
    load_data,
    clean_data,
    validate_data,
    prepare_training_data,
    save_processed_data
)
from ml.model_selection import (
    compare_models,
    get_best_model
)
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
from backend.database import get_connection

class MLService:
    @staticmethod
    def get_seven_steps_status() -> Dict[str, Any]:
        """
        Xisaabi xaaladda dhabta ah ee 7-da talaabo ee Machine Learning:
        Statuses:
        - 'Lama bilaabin'
        - 'Socda'
        - 'Dhammaaday'
        - 'Xog ayaa maqan'
        - 'Error'
        """
        stats = get_dataset_statistics()
        total_records = stats["total_records"]
        real_records = stats["real_records"]

        # Step 1: Ururinta Xogta
        if total_records == 0:
            step1_status = "Lama bilaabin"
            step1_desc = "Dataset-ku waa maran yahay. Kudar xog cusub ama soo geli CSV."
        elif total_records < 10:
            step1_status = "Xog ayaa maqan"
            step1_desc = f"Waxaa la hayaa {total_records} record. Ugu yaraan 15 ayaa loo baahan yahay."
        else:
            step1_status = "Dhammaaday"
            step1_desc = f"{total_records} xog ah ayaa diyaar ah ({stats['real_records']} dhab ah, {stats['demo_records']} demo)."

        # Step 2: Nadiifinta Xogta
        cleaned_file_exists = os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml", "data", "processed_dataset.csv"))
        if total_records == 0:
            step2_status = "Lama bilaabin"
            step2_desc = "Xog nadiif ah ma jirto sababtoo ah xog lama helin."
        elif cleaned_file_exists:
            step2_status = "Dhammaaday"
            step2_desc = "Pipeline-ka nadiifinta waa la fuliyay, xogta waa la ansixiyay."
        else:
            step2_status = "Lama bilaabin"
            step2_desc = "Guji 'Nadiifi Xogta' si validation-ka loo maro."

        # Step 3: Xulashada Model-ka
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM MLTrainingRun WHERE training_status = 'Completed'")
        runs_count = cursor.fetchone()[0]

        if runs_count > 0:
            step3_status = "Dhammaaday"
            step3_desc = "Moodallada Linear, Random Forest, iyo Gradient Boosting waa la barbar dhigay."
        elif total_records >= 8:
            step3_status = "Lama bilaabin"
            step3_desc = "Xogtu way ku filan tahay xulashada model-ka."
        else:
            step3_status = "Xog ayaa maqan"
            step3_desc = "Xogtu kuma filna xulashada model-ka."

        # Step 4: Tababarka Model-ka
        models = get_all_registered_models()
        active_models = [m for m in models if m.get("is_active") == 1]
        if len(active_models) >= 3:
            step4_status = "Dhammaaday"
            step4_desc = f"{len(active_models)} moodal oo firfircoon ayaa la tababaray."
        elif len(active_models) > 0:
            step4_status = "Dhammaaday"
            step4_desc = f"{len(active_models)} moodal ayaa la tababaray."
        elif total_records < 8:
            step4_status = "Xog ayaa maqan"
            step4_desc = "Tababarku wuxuu u baahan yahay xog dheeraad ah."
        else:
            step4_status = "Lama bilaabin"
            step4_desc = "Moodallada weli lama tababarin."

        # Step 5: Tijaabinta & Qiimaynta
        cursor.execute("SELECT COUNT(*) FROM MLEvaluation")
        eval_count = cursor.fetchone()[0]
        if eval_count > 0:
            step5_status = "Dhammaaday"
            step5_desc = f"{eval_count} tijaabooyin metrics ah ayaa la fuliyay (MAE, RMSE, R2, F1)."
        elif len(active_models) > 0:
            step5_status = "Lama bilaabin"
            step5_desc = "Model-ku waa tababaran yahay laakiin tijaabo rasmi ah lama gelin."
        else:
            step5_status = "Lama bilaabin"
            step5_desc = "Tababar model-ka marka hore."

        # Step 6: Ku xiridda & Saadaasha (Deployment)
        if len(active_models) >= 1:
            step6_status = "Dhammaaday"
            step6_desc = "API-yada saadaasha (Print Time, Filament, Failure Risk) waa live oo shaqaynaya."
        else:
            step6_status = "Lama bilaabin"
            step6_desc = "Model lama shaqaynayo weli."

        # Step 7: Kormeerka & Hagaajinta (Monitoring)
        cursor.execute("SELECT COUNT(*) FROM MLPrediction")
        pred_count = cursor.fetchone()[0]
        if pred_count > 0:
            step7_status = "Dhammaaday"
            step7_desc = f"{pred_count} saadaal ayaa la socodkooda la diiwaangeliyay."
        else:
            step7_status = "Lama bilaabin"
            step7_desc = "La socodku wuxuu bilaabmayaa marka saadaal la sameeyo."

        conn.close()

        steps = [
            {"step_number": 1, "name": "Ururi Xogta (Collect Data)", "status": step1_status, "description": step1_desc},
            {"step_number": 2, "name": "Nadiifi Xogta (Prepare & Clean)", "status": step2_status, "description": step2_desc},
            {"step_number": 3, "name": "Dooro Model (Choose a Model)", "status": step3_status, "description": step3_desc},
            {"step_number": 4, "name": "Tababar Model (Train the Model)", "status": step4_status, "description": step4_desc},
            {"step_number": 5, "name": "Tijaabi & Qiimee (Test & Evaluate)", "status": step5_status, "description": step5_desc},
            {"step_number": 6, "name": "Ku Xir System-ka (Deploy the Model)", "status": step6_status, "description": step6_desc},
            {"step_number": 7, "name": "La Soco & Hagaaji (Monitor & Improve)", "status": step7_status, "description": step7_desc},
        ]

        completed_count = sum(1 for s in steps if s["status"] == "Dhammaaday")
        progress_percentage = int((completed_count / 7.0) * 100)

        return {
            "progress_percentage": progress_percentage,
            "completed_steps": completed_count,
            "total_steps": 7,
            "steps": steps,
            "active_models_count": len(active_models),
            "total_dataset_records": total_records
        }

    @staticmethod
    def run_clean_pipeline():
        raw_df = load_data(include_demo=True)
        if raw_df.empty:
            return {"success": False, "message": "Dataset-ku waa maran yahay. Xog lagama helin database-ka."}
        cleaned_df, report = clean_data(raw_df)
        save_path = save_processed_data(cleaned_df)
        return {
            "success": True,
            "report": report,
            "cleaned_rows_count": len(cleaned_df),
            "saved_file": save_path,
            "message": f"Nadiifinta waa la dhamaystiray: {report['valid_count']} records ayaa ansax ah. {report['missing_values_dropped'] + report['out_of_bounds_dropped']} ayaa la saaray."
        }
