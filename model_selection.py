import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
from typing import Dict, Any, List

def select_regression_model(model_name: str = "random_forest", **kwargs):
    """
    Soo celi regression model ku habboon:
    - 'linear_regression'
    - 'random_forest'
    - 'gradient_boosting'
    """
    model_name_lower = model_name.lower()
    if "linear" in model_name_lower:
        return LinearRegression(**kwargs)
    elif "gradient" in model_name_lower:
        return GradientBoostingRegressor(
            n_estimators=kwargs.get("n_estimators", 100),
            max_depth=kwargs.get("max_depth", 4),
            learning_rate=kwargs.get("learning_rate", 0.1),
            random_state=42
        )
    else: # Default Random Forest Regressor
        return RandomForestRegressor(
            n_estimators=kwargs.get("n_estimators", 100),
            max_depth=kwargs.get("max_depth", 8),
            min_samples_split=kwargs.get("min_samples_split", 2),
            random_state=42
        )

def select_classification_model(model_name: str = "random_forest", **kwargs):
    """
    Soo celi classification model:
    - 'random_forest' (Default)
    - 'logistic_regression'
    """
    if "logistic" in model_name.lower():
        return LogisticRegression(max_iter=1000, random_state=42)
    return RandomForestClassifier(
        n_estimators=kwargs.get("n_estimators", 100),
        max_depth=kwargs.get("max_depth", 6),
        random_state=42
    )

def compare_models(X_train, X_test, y_train, y_test, task_type: str = "regression") -> Dict[str, Any]:
    """
    Isbarbardhig model-lada kala duwan adoo isticmaalaya metrics dhab ah:
    - Regression: MAE, RMSE, R² Score
    - Classification: Accuracy, Precision, Recall, F1 Score
    """
    results = {}

    if task_type == "regression":
        candidate_models = {
            "Linear Regression": LinearRegression(),
            "Random Forest Regressor": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
            "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        }

        for name, model in candidate_models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
            r2 = float(r2_score(y_test, preds))

            results[name] = {
                "algorithm": name,
                "model_instance": model,
                "mae": round(mae, 3),
                "rmse": round(rmse, 3),
                "r2_score": round(r2, 4),
                # Score evaluation (higher R2 and lower MAE is better)
                "selection_score": round(max(r2, 0.0) / (mae + 1.0), 4)
            }

    else: # Classification
        candidate_models = {
            "Random Forest Classifier": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42)
        }

        for name, model in candidate_models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            acc = float(accuracy_score(y_test, preds))
            prec = float(precision_score(y_test, preds, zero_division=0))
            rec = float(recall_score(y_test, preds, zero_division=0))
            f1 = float(f1_score(y_test, preds, zero_division=0))

            results[name] = {
                "algorithm": name,
                "model_instance": model,
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "selection_score": round(f1, 4)
            }

    best_name = get_best_model(results, task_type=task_type)

    return {
        "task_type": task_type,
        "models_evaluated": {k: {m: v for m, v in vals.items() if m != "model_instance"} for k, vals in results.items()},
        "best_model_name": best_name,
        "best_model_instance": results[best_name]["model_instance"],
        "reason": f"Model-ka '{best_name}' ayaa la doortay maxaa yeelay wuxuu keenay metrics-ka ugu fiican (R2/F1 Score ugu sarreeya iyo Khaladka ugu yar)."
    }

def get_best_model(comparison_results: Dict[str, Any], task_type: str = "regression") -> str:
    """
    Dooro magaca model-ka keenay natiijada ugu fiican.
    Ha dooran sabab la'aan: R² ugu sarreeya ee regression, iyo F1/Accuracy ee classification.
    """
    best_name = None
    best_score = -999999.0

    for name, metrics in comparison_results.items():
        if task_type == "regression":
            # Primary: Highest R2 score, Secondary: Lowest MAE
            score = metrics.get("r2_score", -1.0)
        else:
            # Primary: F1 score or Accuracy
            score = metrics.get("f1_score", 0.0)

        if score > best_score:
            best_score = score
            best_name = name

    # Default fallback if all are negative or equal
    if not best_name:
        best_name = "Random Forest Regressor" if task_type == "regression" else "Random Forest Classifier"

    return best_name
