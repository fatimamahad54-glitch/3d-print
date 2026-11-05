from typing import Dict, Any
from ml.prediction import (
    predict_print_time,
    predict_filament_usage,
    predict_failure_risk,
    predict_all
)

class MLPredictionService:
    @staticmethod
    def get_print_time_prediction(data: dict) -> Dict[str, Any]:
        return predict_print_time(data)

    @staticmethod
    def get_filament_prediction(data: dict) -> Dict[str, Any]:
        return predict_filament_usage(data)

    @staticmethod
    def get_failure_prediction(data: dict) -> Dict[str, Any]:
        return predict_failure_risk(data)

    @staticmethod
    def get_all_predictions(data: dict) -> Dict[str, Any]:
        return predict_all(data)
