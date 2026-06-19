import { SystemData } from '../types';
import { GithubLogo as Github, LinkedinLogo as Linkedin, Code as Code2, InstagramLogo as Instagram, Envelope as Mail, TwitterLogo as Twitter, Calendar, Globe } from '@phosphor-icons/react/ssr';

export const DATA: SystemData = {
  name: "Smart Traffic Intelligence",
  tagline: "Agentic AI for Bengaluru Traffic Management",
  contact: {
    email: "team@smart-traffic.ai",
    portfolio: "https://smart-traffic.ai",
    links: [
      { name: "GitHub", url: "https://github.com/smart-traffic-intelligence", icon: Github },
      { name: "LinkedIn", url: "https://www.linkedin.com/company/smart-traffic", icon: Linkedin },
      { name: "Documentation", url: "#", icon: Code2 },
      { name: "Live Demo", url: "#", icon: Globe },
      { name: "Demo", url: "https://cal.com/sugarytreat/demo", icon: Calendar },
      { name: "Support", url: "mailto:team@smart-traffic.ai", icon: Mail },
    ],
  },
  summary: "Smart Traffic Intelligence is an agentic AI platform that transforms raw Bengaluru traffic incident data into predictive intelligence and actionable deployment plans. Four specialized AI agents work in concert — parsing multilingual incident descriptions, predicting severity and resolution time, detecting zone-level anomalies in real time, and generating field-ready response plans — all orchestrated through a single unified dashboard.",

  systemStats: [
    { label: "Incidents Analyzed", value: "8,173", description: "Real Bengaluru traffic records" },
    { label: "AI Agents", value: "4", description: "Autonomous specialized agents" },
    { label: "Median Resolution", value: "~64 min", description: "Predicted incident clearance" },
    { label: "Training Records", value: "3,205", description: "Validated duration samples" },
  ],

  agents: [
    {
      id: "nlp-parser",
      number: "01",
      name: "NLP Description Parser",
      shortName: "NLP Parser",
      description: "Accepts raw incident descriptions in Kannada, Hindi, mixed-language, or broken English and extracts structured incident metadata using Groq with few-shot prompting.",
      techBadges: ["Groq", "Few-Shot Prompting", "Multilingual NLP"],
      input: "Raw text description (any language — Kannada, Hindi, English, mixed)",
      processing: "Single Groq API call with system instructions + few-shot examples → returns structured JSON extraction",
      output: "{ root_cause, vehicle_type, severity (1-3), action_needed, normalized_summary }",
      details: [
        "Handles Kannada script (e.g. 'ಬಿಎಂಟಿಸಿ ಬಸ್ ಕೆಟ್ಟು ನಿಂತಿದೆ') and transliterated text",
        "Extracts root cause from 10 predefined categories (vehicle_breakdown, accident, etc.)",
        "Falls back gracefully — if parsing fails, structured form fields are used instead",
        "Output displayed in Incident Panel as 'Parsed from description' section"
      ],
      color: "primary"
    },
    {
      id: "prediction-engine",
      number: "02",
      name: "Prediction Engine",
      shortName: "Predictor",
      description: "Two parallel XGBoost models — a binary classifier predicting incident priority (High/Low) and a regressor estimating resolution duration in minutes — operating on a 12-feature vector derived from the incident.",
      techBadges: ["XGBoost Classifier", "XGBoost Regressor", "12-Feature Vector"],
      input: "Feature vector: lat, lng, road_closure, hour, day, peak_hour, weekend, corridor_rank, junction_recurrence, event_cause_enc, veh_type_enc, zone_enc",
      processing: "Dual XGBoost inference — classifier returns priority + confidence probability, regressor returns estimated_duration_minutes",
      output: "{ priority: High/Low, confidence: 0-1, estimated_duration_minutes, estimated_resolution_time }",
      details: [
        "Classifier trained on all authenticated incidents — handles class imbalance with scale_pos_weight",
        "Regressor trained on 3,205 records after dropping outliers >24 hours (raw mean ~6,200 min → median ~64 min)",
        "Sub-100ms inference latency — models loaded into memory at server startup via joblib",
        "12 engineered features including junction_recurrence (historical congestion proxy) and corridor_rank"
      ],
      color: "accent"
    },
    {
      id: "anomaly-detector",
      number: "03",
      name: "Anomaly Detector",
      shortName: "Anomaly AI",
      description: "An Isolation Forest model trained on per-zone traffic baselines that runs continuously, scoring each zone's current state as Normal, Watch, or Critical based on deviation from historical patterns.",
      techBadges: ["Isolation Forest", "Real-time Scoring", "Zone Monitoring"],
      input: "Per-zone aggregates: { incident_count, high_priority_ratio, mean_duration_minutes } grouped by zone × day_type × time_bucket",
      processing: "Isolation Forest scores each zone's current 3D feature vector — anomalous points isolated in fewer splits → lower scores",
      output: "Per zone: { zone, alert_level (Normal/Watch/Critical), incident_count, high_priority_ratio, mean_duration, anomaly_score }",
      details: [
        "Baseline learned from all 8,173 records across zone × day_type × time_bucket combinations",
        "Null zones (57% of records) are grouped by police_station to preserve full dataset coverage",
        "Score thresholds: >0 = Normal, 0 to -0.1 = Watch, <-0.1 = Critical",
        "Zone polygon colors on map update in real-time matching alert levels (green/amber/red)"
      ],
      color: "secondary"
    },
    {
      id: "action-planner",
      number: "04",
      name: "Action Planner",
      shortName: "Planner",
      description: "Generates field-ready deployment plans by combining prediction results with incident context and sending a structured prompt to Groq, streaming the response token-by-token via SSE.",
      techBadges: ["Groq", "SSE Streaming", "Structured Prompting"],
      input: "Full incident context: event_type, cause, address, junction, corridor, zone, predicted priority/confidence/duration, road_closure, NLP summary",
      processing: "Structured Groq prompt → model generates 6-section deployment plan → streamed via SSE to frontend",
      output: "Six labeled sections streamed in real-time: Officers, Barricades, Diversion, Clearance Time, Escalation Trigger, Public Advisory",
      details: [
        "Planned events trigger pre-emptive deployment plans (officers positioned before event start)",
        "Streamed word-by-word with typewriter rendering in the Incident Panel",
        "Distinct prompt strategies for planned vs unplanned incidents",
        "Feedback loop: user rates plan quality (thumbs up/down) → POST /feedback"
      ],
      color: "dark"
    }
  ],

  techStack: [
    { category: "ML & AI", items: ["XGBoost", "Isolation Forest", "Groq API", "scikit-learn", "Pandas", "NumPy"] },
    { category: "Backend", items: ["FastAPI", "Python 3.11", "Uvicorn", "SSE Streaming", "joblib"] },
    { category: "Frontend", items: ["Next.js 16", "React 19", "Leaflet.js", "Recharts", "GSAP", "Tailwind CSS"] },
    { category: "Data", items: ["8,173 Records", "Bengaluru Traffic Dataset", "Real-time Anomaly Feed", "In-memory DataFrame"] },
  ],

  datasetInfo: {
    totalRecords: 8173,
    unplannedRecords: 7706,
    plannedRecords: 467,
    trainableRecords: 3205,
    medianResolution: 64,
    keyColumns: [
      "latitude / longitude", "event_type (planned/unplanned)", "event_cause",
      "requires_road_closure", "start_datetime / end_datetime", "closed_datetime / resolved_datetime",
      "priority (High/Low)", "zone", "junction", "corridor", "police_station",
      "description", "veh_type", "address", "status"
    ],
  },

  derivedFeatures: [
    { name: "resolution_minutes", description: "closed_datetime - start_datetime (capped at 24h, outliers dropped)" },
    { name: "planned_duration_minutes", description: "end_datetime - start_datetime for planned events only" },
    { name: "hour_of_day", description: "Integer 0–23 from start_datetime" },
    { name: "day_of_week", description: "Integer 0–6 from start_datetime" },
    { name: "is_peak_hour", description: "1 if hour ∈ {7,8,9,10,17,18,19,20}" },
    { name: "is_weekend", description: "1 if day_of_week ∈ {5,6}" },
    { name: "corridor_rank", description: "Incident frequency count per corridor" },
    { name: "junction_recurrence", description: "Historical incident count per junction (proxy for congestion)" },
    { name: "time_bucket", description: "morning_peak(6-10) / afternoon(10-16) / evening_peak(16-21) / night(21-6)" },
    { name: "day_type", description: "weekday or weekend — used for anomaly detection grouping" },
  ],

  modelInfo: [
    {
      name: "Priority Classifier",
      type: "Classification",
      algorithm: "XGBoost Binary Classifier",
      target: "priority (High = 1, Low = 0)",
      records: "All authenticated incidents with non-null priority",
      details: "Class imbalance handled with scale_pos_weight. Returns predicted class + probability score."
    },
    {
      name: "Duration Regressor",
      type: "Regression",
      algorithm: "XGBoost Regressor",
      target: "resolution_minutes (positive, ≤1440 min)",
      records: "~3,205 records after dropping outliers >24h",
      details: "Median ~64 minutes. Raw mean ~6,200 min heavily skewed by records left open for days."
    },
    {
      name: "Zone Anomaly Model",
      type: "Anomaly Detection",
      algorithm: "Isolation Forest",
      target: "Per-zone anomaly score (-1 to +1)",
      records: "All 8,173 records aggregated by zone × day_type × time_bucket",
      details: "Points far from cluster isolated quickly → low score. Thresholds: >0 Normal, 0 to -0.1 Watch, <-0.1 Critical."
    }
  ],

  team: [
    { name: "Team Member 1", role: "Lead Developer", focus: "System Architecture & Full-Stack" },
    { name: "Team Member 2", role: "ML Engineer", focus: "XGBoost Models & Feature Engineering" },
    { name: "Team Member 3", role: "AI Agent Developer", focus: "NLP Parsing & Action Planning" },
    { name: "Team Member 4", role: "Frontend Engineer", focus: "Dashboard & Visualization" },
  ],

  capabilities: [
    {
      id: "01",
      title: "Predictive Intelligence",
      description: "Dual XGBoost models classify incident priority and estimate resolution time from a 12-feature vector — giving traffic authorities advance warning before congestion escalates.",
      features: ["Binary Priority Classification", "Duration Regression", "Sub-100ms Inference", "12 Engineered Features"]
    },
    {
      id: "02",
      title: "Real-time Anomaly Detection",
      description: "Isolation Forest monitors every zone continuously, comparing current conditions against historical baselines to flag anomalies before they become crises.",
      features: ["Per-Zone Monitoring", "3D Feature Scoring", "Watch / Critical Alerts", "Map Polygon Integration"]
    },
    {
      id: "03",
      title: "Automated Response Plans",
      description: "Groq generates field-ready deployment plans streamed in real-time — specifying officer counts, barricade positions, diversion routes, and escalation triggers.",
      features: ["SSE Token Streaming", "6-Section Plans", "Planned Event Pre-emption", "Feedback Loop"]
    }
  ],

  achievements: [
    {
      title: "Real Bengaluru Traffic Dataset",
      organization: "8,173 Authenticated Incidents",
      date: "2024-2025",
      points: [
        "Covers both planned (467) and unplanned (7,706) event types across Bengaluru.",
        "Includes vehicle breakdowns, accidents, waterlogging, VIP movements, festivals, and protests."
      ]
    },
    {
      title: "End-to-End Agentic Pipeline",
      organization: "4 Specialized AI Agents",
      date: "2026",
      points: [
        "NLP parsing, priority prediction, anomaly detection, and action plan generation — all autonomous.",
        "From raw Kannada text to deployment-ready field plan in under 2 seconds."
      ]
    }
  ],
};
