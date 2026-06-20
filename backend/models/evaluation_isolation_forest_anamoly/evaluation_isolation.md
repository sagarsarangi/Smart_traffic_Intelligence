# Agent 3 Anomaly Detector: Evaluation Report
## Isolation Forest on Bengaluru Traffic Incidents

> **Model:** sklearn.ensemble.IsolationForest
> **Saved:** backend/models/anomaly_detector.joblib
> **Trained by:** backend/training/isolation_forest.ipynb
> **Source logic:** backend/agents/anomaly_detector.py TrafficAnomalyDetector.fit()

---

## 1. Dataset

| Metric | Value |
|--------|-------|
| Raw CSV | bengaluru_traffic_incidents.csv |
| Total records | 8,173 |
| Unplanned events | 7,706 (94.3%) |
| Planned events | 467 (5.7%) |
| Records with valid zone | 3444 (42.1%) |
| Records using police_station fallback | 4729 (57.9%) |
| Valid duration records (0-1440 min) | 2,523 |
| overall_mean_duration (fallback) | 98.51 min |

**Data quality handling:** Null zones (57.9% of records) are grouped by `police_station`
instead of being dropped, preserving the full dataset. Dropping null-zone records would
discard more than half the training data.

---

## 2. Feature Engineering

The Isolation Forest is **not** trained on raw incident features.
It learns the distribution of **aggregate zone behaviour** across time.

For every unique `(zone_or_station, day_type, time_bucket)` combination:

| Feature | Description | Range |
|---------|-------------|-------|
| `mean_incident_count` | Average incidents per active day in this bucket | >= 0 |
| `high_priority_ratio` | Fraction of High-priority incidents | 0.0 to 1.0 |
| `mean_duration_minutes` | Avg resolution time in min (outliers >1440 excluded) | > 0 |

**Baseline rows:** 450 unique (zone, day_type, time_bucket) combinations  
**Unique zones/stations:** 64

### Feature Statistics

| Feature | Min | Mean | Median | P95 | Max |
|---------|-----|------|--------|-----|-----|
| mean_incident_count | 1.00 | 1.48 | 1.30 | 2.70 | 6.67 |
| high_priority_ratio | 0.000 | 0.560 | 0.638 | 1.000 | 1.000 |
| mean_duration_minutes | 1.6 | 109.6 | 81.1 | 381.3 | 1228.1 |

---

## 3. Model Configuration

| Hyperparameter | Value | Rationale |
|---------------|-------|-----------|
| `n_estimators` | 100 | Standard for reliable score stability |
| `contamination` | 0.05 | ~5% of zone-time buckets expected anomalous |
| `random_state` | 42 | Full reproducibility |
| `max_samples` | auto | Default (min(256, n_samples)) |
| `offset_` | -0.5859 | Fitted from contamination fraction |

**Why Isolation Forest?**
- No labelled anomaly data exists -- unsupervised detection
- 3D feature space has a dense normal core with genuine outlier spikes
- Isolates rare points in O(log n) random splits vs brute-force distance methods
- Returns continuous anomaly scores enabling the 3-tier alert system

---

## 4. Alert Threshold Logic

| Score Range | Alert Level | UI Colour | Meaning |
|-------------|-------------|-----------|---------|
| > 0.0 | Normal | Green | Zone behaves within historical norms |
| 0.0 to -0.1 | Watch | Amber | Elevated activity, monitor closely |
| < -0.1 | Critical | Red | Significant anomaly, trigger action plan |

Thresholds defined in `anomaly_detector.py:323-329` and documented in AGENTS.md.

---

## 5. Alert Level Distribution (Training Baseline)

| Alert Level | Count | Fraction |
|-------------|-------|----------|
| Normal   | 427 | 94.9% |
| Watch    | 16 | 3.6% |
| Critical | 7 | 1.6% |

The anomaly fraction (~5.1%) is close to the configured `contamination=0.05`, confirming the model fitted correctly.

---

## 6. Top Critical Zones

(zone/station, day_type, time_bucket) combinations with the lowest anomaly scores in training data:

| Zone / Station | Day Type | Time Bucket | Incidents/Day | High Priority % | Mean Duration (min) | Score |
|---------------|----------|-------------|---------------|-----------------|---------------------|-------|
| HAL Old Airport | weekend | morning_peak | 6.67 | 95.0% | 35.9 | -0.1476 |
| Basavanagudi | weekday | afternoon | 3.00 | 0.0% | 744.4 | -0.1304 |
| South Zone 2 | weekend | night | 6.38 | 78.4% | 49.0 | -0.1221 |
| Jayanagara | weekend | evening_peak | 6.00 | 0.0% | 98.5 | -0.1213 |
| Basavanagudi | weekday | morning_peak | 1.60 | 0.0% | 846.8 | -0.1122 |

---

## 7. Feature Sensitivity (Proxy Importance)

Estimated by perturbing each feature +1 std and measuring avg absolute score change.

| Feature | Delta Score (avg) | Relative Influence |
|---------|------------------|-------------------|
| `mean_duration_minutes` | 0.059638 | ████████████████████ (100%) |
| `mean_incident_count` | 0.043537 | ██████████████ (73%) |
| `high_priority_ratio` | 0.019227 | ██████ (32%) |

**Dominant feature:** `mean_duration_minutes` -- primary driver of anomaly detection.

---

## 8. Inference Pipeline

At inference time (every 13 seconds in backend, polled by frontend every 5 seconds):

1. Collect active incidents within 24h sliding window per zone
2. Compute three features: count, priority ratio, mean duration
3. Call `model.decision_function([[count, ratio, duration]])` -> anomaly score
4. Apply thresholds -> alert level
5. Return `{zone, alert_level, incident_count, high_priority_ratio, mean_duration, anomaly_score}`

**Duration fallback chain** (avoids erratic scores from elapsed-time variance):
1. `resolution_minutes` from closed/resolved timestamps (historical)
2. `estimated_duration_minutes` from prediction agent (live submissions)
3. Baseline stats lookup for this (zone, day_type, time_bucket)
4. `overall_mean_duration = 98.51 min` (final fallback)

---

## 9. Model Artifacts

| File | Description |
|------|-------------|
| `models/anomaly_detector.joblib` | Serialised state: model + baseline_stats + overall_mean_duration |
| `models/anomaly_feature_distributions.png` | Feature histograms |
| `models/anomaly_score_analysis.png` | Score distribution + feature scatter |
| `models/anomaly_zone_heatmap.png` | Per-zone alert level heatmap across time buckets |

---

## 10. Notes

- **No authenticated filter applied** -- anomaly detector uses ALL 8,173 records.
  All incidents contribute to zone-level baseline regardless of data quality flags.
- The Isolation Forest is **unsupervised** -- no labelled anomalies exist in the dataset.
  The 5% contamination is a prior expectation, not a measured quantity.
- `anomaly_detector.py` retrains on server startup; this notebook produces an identical
  `.joblib` for offline inspection and validation.
- **Do not drop null-zone records** -- removes 57.9% of training data and leaves many
  police stations without baseline coverage.
