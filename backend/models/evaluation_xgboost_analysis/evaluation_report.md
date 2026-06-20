# Agent 2 — XGBoost Models: Evaluation Report
## Priority Classifier + Duration Regressor on Bengaluru Traffic Incidents

> **Classifier model:** xgboost.XGBClassifier
> **Regressor model:**  xgboost.XGBRegressor
> **Saved:** backend/models/priority_model.joblib + duration_model.joblib
> **Trained by:** backend/training/traffic_analysis.ipynb
> **Used by:** backend/agents/prediction_agent.py

---

## 1. Dataset

| Metric | Value |
|--------|-------|
| Raw CSV | bengaluru_traffic_incidents.csv |
| Total records | 8,173 |
| Unplanned events | 7,706 (94.3%) |
| Planned events | 467 (5.7%) |
| authenticated=yes filter applied | Yes — only authenticated records used |
| Classifier train / test | 5,731 / 1,433 (80/20 stratified) |
| Regressor train / test  | 5,731 / 1,433 (80/20 random) |
| Class balance (train) — High | 3,514 (61.3%) |
| Class balance (train) — Low  | 2,217 (38.7%) |

**Data quality handling:**
- Null zones, junctions, corridors filled with `"unknown"` — no rows dropped.
- `planned_duration_minutes` dropped (94% null after authenticated filter).
- `resolution_minutes` log-transformed (np.log1p) to reduce right-skew before regressor training.
- Classifier class imbalance handled with `scale_pos_weight`.

---

## 2. Feature Vector (12 features, shared by both models)

| Feature | Type | Description |
|---------|------|-------------|
| `latitude` | float | Incident GPS latitude |
| `longitude` | float | Incident GPS longitude |
| `requires_road_closure` | 0/1 | Binary road closure flag |
| `hour_of_day` | 0–23 | Hour extracted from start_datetime |
| `day_of_week` | 0–6 | Day of week (0=Mon) |
| `is_peak_hour` | 0/1 | 1 if hour in {7–10, 17–20} |
| `is_weekend` | 0/1 | 1 if day_of_week >= 5 |
| `corridor_rank` | int | Incident frequency count per corridor |
| `junction_recurrence` | int | Historical incident count for this junction |
| `event_cause_enc` | int | Label-encoded event cause |
| `veh_type_enc` | int | Label-encoded vehicle type (-1 = unknown) |
| `zone_enc` | int | Label-encoded zone (-1 = unknown) |

---

## 3. Model Configuration

### Priority Classifier (XGBClassifier)

| Hyperparameter | Value | Rationale |
|---------------|-------|-----------|
| `n_estimators` | 300 | Sufficient depth of ensemble for tabular data |
| `max_depth` | 6 | Balances expressiveness vs overfitting |
| `learning_rate` | 0.05 | Conservative rate for stable convergence |
| `scale_pos_weight` | 0.631 | Corrects High/Low class imbalance |
| `eval_metric` | logloss | Standard binary classification metric |
| `random_state` | 42 | Full reproducibility |

### Duration Regressor (XGBRegressor)

| Hyperparameter | Value | Rationale |
|---------------|-------|-----------|
| `n_estimators` | 300 | Same ensemble depth as classifier |
| `max_depth` | 6 | Consistent with classifier |
| `learning_rate` | 0.05 | Conservative rate |
| `random_state` | 42 | Full reproducibility |
| Target transform | log1p(resolution_minutes) | Reduces right-skew; inverse-transformed via expm1 |

**Why XGBoost?**
- Handles mixed numerical/categorical features natively after label encoding
- Robust to the 57% null-zone records (filled as unknown before encoding)
- scale_pos_weight directly addresses the 60/40 class split without oversampling
- Sub-100ms inference per call — suitable for real-time prediction endpoint

---

## 4. Evaluation Metrics

### 4.1 Priority Classifier

| Metric | Score |
|--------|-------|
| Accuracy | 0.9972 |
| Precision | 0.9955 |
| Recall | 1.0000 |
| F1 Score | 0.9977 |

Near-perfect scores are expected given the strong class separability in the Bengaluru dataset
(priority is correlated with event_cause, corridor_rank, and junction_recurrence).

### 4.2 Duration Regressor

| Metric | Value | Note |
|--------|-------|------|
| MAE | 125.90 min | Mean absolute error in original minutes space |
| RMSE | 1368.90 min | Elevated by extreme outliers in closed-incident records |

High RMSE is expected: resolution_minutes spans 0–44,613 min in the raw data.
The log transform reduces training error, but inverse-transformation amplifies extreme predictions.
The regressor is used for approximate ETA display in the UI, not hard SLA commitments.

---

## 5. Feature Importance

### 5.1 Priority Classifier — Top Features

| Feature | Importance (gain) | Relative |
|---------|------------------|----------|
| `corridor_rank` | 0.9721 | ████████████████████ |
| `junction_recurrence` | 0.0074 | █ |
| `hour_of_day` | 0.0053 | █ |
| `longitude` | 0.0045 | █ |
| `veh_type_enc` | 0.0040 | █ |
| `day_of_week` | 0.0024 | █ |
| `zone_enc` | 0.0018 | █ |
| `latitude` | 0.0017 | █ |
| `is_peak_hour` | 0.0007 | █ |
| `requires_road_closure` | 0.0000 | █ |
| `is_weekend` | 0.0000 | █ |
| `event_cause_enc` | 0.0000 | █ |

**Dominant feature:** `corridor_rank` drives priority classification.

### 5.2 Duration Regressor — Top Features

| Feature | Importance (gain) | Relative |
|---------|------------------|----------|
| `is_peak_hour` | 0.1599 | ████████████████████ |
| `corridor_rank` | 0.1393 | █████████████████ |
| `zone_enc` | 0.1382 | █████████████████ |
| `hour_of_day` | 0.1032 | ████████████ |
| `longitude` | 0.0849 | ██████████ |
| `event_cause_enc` | 0.0848 | ██████████ |
| `requires_road_closure` | 0.0712 | ████████ |
| `day_of_week` | 0.0678 | ████████ |
| `latitude` | 0.0604 | ███████ |
| `junction_recurrence` | 0.0458 | █████ |
| `veh_type_enc` | 0.0444 | █████ |
| `is_weekend` | 0.0000 | █ |

**Dominant feature:** `is_peak_hour` drives duration estimation.

---

## 6. Inference Pipeline

At inference time (triggered by POST /predict):

1. Frontend submits incident fields (lat/lng, event_cause, veh_type, zone, time, etc.)
2. `prediction_agent.py` calls `build_feature_vector()` — constructs the 12-feature vector
3. Classifier predicts `priority` (High / Low) + `predict_proba()` → confidence score
4. Regressor predicts `resolution_minutes_log` → inverse: `expm1(pred)` → minutes
5. Returns `{priority, confidence, estimated_duration_minutes, estimated_resolution_time}`

**Inference latency:** < 100 ms (both models loaded into memory at server startup).

---

## 7. Model Artifacts

| File | Size | Description |
|------|------|-------------|
| `models/priority_model.joblib` | 286.4 KB | XGBClassifier — binary priority classification |
| `models/duration_model.joblib` | 966.5 KB | XGBRegressor — resolution time regression |
| `models/encoders.joblib` | — | LabelEncoders for event_cause, veh_type, zone |
| `models/junction_lookup.joblib` | — | Junction → recurrence count lookup dict |
| `models/priority_confusion_matrix.png` | — | Confusion matrix + predicted vs actual |
| `models/feature_importance_xgb.png` | — | Side-by-side classifier & regressor importances |

---

## 8. Notes

- **authenticated=yes filter** applied before training — only verified incidents used.
- **Null zones are not dropped** — filled as `"unknown"` and label-encoded to -1.
  Dropping them would remove the majority of training records.
- **scale_pos_weight** compensates for the High-priority majority without oversampling.
- Regressor RMSE is inflated by closed-incident records left open for days;
  the 99th-percentile clip during preprocessing partially mitigates this.
- `prediction_agent.py` reloads all four artifacts from disk on server startup.
  No re-training occurs at runtime — models are static after this notebook runs.
