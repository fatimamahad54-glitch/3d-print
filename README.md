# Nidaamka Maamulka 3D Printing & Machine Learning (Af-Soomaali)

Kani waa nidaam dhamaystiran oo isku dhafan (Full-Stack 3D Printing Management & Machine Learning Subsystem), kaas oo si toos ah ugu dhex shaqaynaya 3D Printing System-ka.

---

## 🏗️ Qaab-dhismeedka Project-ka (Project Structure)

```text
3d print/
├── ml/
│   ├── data_collection.py      # Step 1: Ururinta xogta 3D printing & import
│   ├── data_preprocessing.py   # Step 2: Nadiifinta, validation rules & encoding
│   ├── model_selection.py      # Step 3: Isbarbardhigga moodallada (Linear, RF, GB)
│   ├── train_model.py          # Step 4: Tababarka moodallada & keydinta
│   ├── evaluate_model.py       # Step 5: Qiimaynta (MAE, RMSE, R², Accuracy, Confusion Matrix)
│   ├── prediction.py           # Step 6: Saadaasha tooska ah & uncertainty bounds
│   ├── model_monitoring.py     # Step 7: Kormeerka khaladka, drift detection & retraining
│   ├── model_registry.py       # Diiwaanka moodallada firfircoon
│   ├── requirements.txt        # Maktabadaha Python
│   └── models/                 # Faylasha moodallada la tababaray (.joblib)
├── backend/
│   ├── database.py             # SQLite schema, tables & initial seeds
│   ├── main.py                 # FastAPI server & static file mounting
│   ├── routes/
│   │   ├── ml_routes.py        # Dhammaan API Endpoints-ka Machine Learning
│   │   └── core_routes.py      # Daabacayaasha, Shaqooyinka, Moodallada, Filaments
│   └── services/
│       ├── ml_service.py       # Adeegga 7-da talaabo & xaaladahooda
│       └── ml_prediction_service.py
├── frontend/
│   ├── index.html              # Interface-ka guud oo ku wada qoran Af-Soomaali
│   ├── css/
│   │   └── style.css           # UI-ga casriga ah ee Dashboard-ka
│   └── js/
│       └── app.js              # Xiriiriyaha API-yada, xisaabinta & ficillada dhabta ah
└── tests/
    ├── test_ml_system.py       # Tijaabada 7-da talaabo ee ML
    └── test_api_endpoints.py   # Tijaabada dhammaan Endpoints-ka FastAPI
```

---

## 🔄 7-da Talaabo ee Machine Learning-ka (Fully Implemented)

1. **Ururi Xogta (Collect Data)**:
   - Miiska `MachineLearningDataset` wuxuu kaydiyaa cabbiraadaha: `model_volume`, `model_weight`, `filament_type`, `print_speed`, `layer_height`, `infill_percentage`, `nozzle_temperature`, `bed_temperature`, `support_enabled`, `estimated_print_time`, `actual_print_time`, `filament_used`, `print_status`, `failure_reason`.
   - Shaqo kasta oo 3D print ah oo dhammaata ama fashilanta waxay **si toos ah (automatic)** ugu wareegtaa dataset-ka.
   - Waxaa jira CSV import iyo gelin manual ah. Xogta demo-ga waxaa si cad loogu calaamadeeyay `is_demo = 1`.

2. **Nadiifi Xogta (Prepare & Clean Data)**:
   - Pipeline-ka `ml/data_preprocessing.py` wuxuu hubiyaa sharciyada: Speed > 0, Layer Height > 0, Infill [0-100]%, Temperature macquul ah.
   - Wuxuu tirtiraa duplicates, wuxuu encode gareeyaa tiirarka categorical-ka ah (`filament_type`, `printer_model`).

3. **Dooro Model (Choose a Model)**:
   - `ml/model_selection.py` wuxuu isbarbardhig ku sameeyaa:
     - Regression: *Linear Regression*, *Random Forest Regressor*, *Gradient Boosting Regressor*.
     - Classification: *Random Forest Classifier*, *Logistic Regression*.
   - Wuxuu xushaa model-ka keenay MAE/RMSE ugu yar iyo R²/F1 ugu sarreeya.

4. **Tababar Model (Train the Model)**:
   - `ml/train_model.py` wuxuu tababaraa 3 moodal oo madax-bannaan:
     - Saadaasha Waqtiga Daabacaadda (`print_time_predictor`)
     - Saadaasha Isticmaalka Filament-ka (`filament_usage_predictor`)
     - Saadaasha Khatarta Fashilka (`failure_risk_predictor`)
   - Haddii xogtu ka yar tahay 8 tusaale, wuxuu soo bandhigayaa fariin Af-Soomaali ah: *"Xogtu kuma filna tababarka model-ka dhabta ah..."*

5. **Tijaabi & Qiimee (Test & Evaluate)**:
   - `ml/evaluate_model.py` wuxuu xisaabiyaa:
     - Regression: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), R² Score, MAPE.
     - Classification: Accuracy, Precision, Recall, F1 Score, Confusion Matrix.
   - Natiijooyinka waxaa lagu kaydiyaa miiska `MLEvaluation`.

6. **Ku Xir System-ka (Deploy & Predict)**:
   - API endpoints toos ah:
     - `POST /api/ml/predict-print-time`
     - `POST /api/ml/predict-filament`
     - `POST /api/ml/predict-failure`
     - `POST /api/ml/predict-all`
   - Saadaashu waxay wadataa xadka hubanti-la'aanta (confidence range) iyo digniin cad (*"Saadaashani waa qiyaas (estimate), ma aha dammaanad 100% ah"*).

7. **La Soco & Hagaaji (Monitor & Improve)**:
   - `ml/model_monitoring.py` wuxuu barbar-dhigaa saadaashii la sameeyay iyo qiimaha dhabta ah ee daabacaadda marka ay dhammaato.
   - Wuxuu ogaadaa Data Drift (isbeddelka xogta) iyo waqtiga dib u tababarka loo baahan yahay.

---

## 🚀 Sida Loo Bilaabo (Commands)

### 1. Rakibaadda Dependencies-ka:
```bash
pip install -r ml/requirements.txt
```

### 2. Bilaabidda Server-ka (Backend & Frontend):
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Kaddib fur browser-kaaga:
👉 **http://127.0.0.1:8000/**

### 3. Orodka Tijaabooyinka (Automated Tests):
```bash
pytest tests/ -v
```
Waxay si buuxda u tijaabinaysaa 13 baadhitaan oo covers dhammaan 7-da talaabo iyo API-yada.
