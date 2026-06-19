# 🚦 Smart Traffic Intelligence System

> An AI-powered traffic forecasting and decision-support platform that helps authorities **predict congestion** caused by planned and unplanned events, **detect anomalies** before they escalate, and **auto-generate response plans** using Generative AI.

---

## 🧩 Problem Statement

Traffic authorities today react to congestion _after_ it happens — relying on experience-based decisions, manual patrols, and no post-event learning. This system flips that model:

- **Planned events** (rallies, cricket matches, festivals) → predict impact in advance
- **Unplanned events** (breakdowns, accidents, waterlogging) → detect anomalies early
- **Every event** → auto-generate a ready-to-act response plan via GenAI

---

## ✨ Core Features

| Feature                             | Description                                                          |
| ----------------------------------- | -------------------------------------------------------------------- |
| Event-based congestion prediction   | Forecast traffic volume and risk score for any upcoming event        |
| Multilingual incident understanding | Auto-classify Kannada/mixed-language incident reports using NLP      |
| GenAI action planner                | LLM-generated response plans — officers, barricades, diversions      |
| Congestion heatmap                  | Dynamic City Replay map of historical and streaming congestion zones |
| Anomaly detection                   | Detect unexpected traffic surges before they become jams             |
| Interactive dashboard               | Real-time monitoring, alerts, and incident submission                |

---

## 🧠 Machine Learning

### Traffic Prediction

- **Models:** XGBoost (Classifier & Regressor)
- **Predicts:** Priority (High/Low) and estimated resolution time (minutes)
- **Inputs:** Location, corridor frequency, time-of-day, zone, historical junction patterns, incident cause

### Anomaly Detection

- **Models:** Isolation Forest
- **Detects:** Unexpected congestion surges and unplanned disruptions in real time (per zone)
- **Output:** Alert severity score (Normal, Watch, Critical)

---

## 🤖 GenAI Features

### 1. Multilingual NLP — Incident Understanding

Real-world incident descriptions in this dataset are written in Kannada, broken English, and mixed scripts (e.g. _"pipe vehicle off aagide saro"_). A standard rule-based system would discard this as noise.

**What it does:**

- Uses **Groq** to read free-text descriptions in any language (e.g. "ಬಿಎಂಟಿಸಿ ಬಸ್ ಕೆಟ್ಟು ನಿಂತಿದೆ ಸರ್") and automatically map them to the dataset's exact vocabulary (vehicle_breakdown, bmtc_bus, severity 2)., and generates an English summary
- Auto-classifies the event so it feeds cleanly into the ML pipeline

### 2. GenAI Action Planner — Automated Response Generation

Once the ML model predicts priority and expected duration, a Large Language Model takes that output and generates a **complete, human-readable response plan**.

**What it does:**

- Receives: predicted priority, event type, corridor, duration estimate, junction name
- Generates: officers to deploy, barricades, diversion routes, estimated clearance, escalation triggers, and public advisories
- Output is in plain language, streamed in real-time, ready to be acted on immediately

### 3. AI Geocoding & Location Resolution

Instead of relying on rigid, pre-defined coordinates, the system uses Groq AI to dynamically resolve free-text area/zone names into precise latitude and longitude. Whether the user types "Koramangala 5th Block" or simply pastes a Kannada description with a zone name, the agent geocodes it. Ambiguous locations trigger an inline clarification modal so users can select the correct, exact spot. for high-confidence matches, dropping a live pin on the map.

- Handles ambiguity by returning candidate locations and prompting the user to clarify via an interactive modal.

---

## 🏗 System Architecture

```
Raw Incident Data (CSV)
        │
        ▼
┌─────────────────────────┐
│  FastAPI Backend        │
│  (Data & Feature Eng.)  │
└────────────┬────────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
┌──────────┐  ┌──────────────┐
│ XGBoost  │  │ Isolation    │
│ Models   │  │ Forest       │
│(Priority,│  │(Anomaly      │
│ Duration)│  │ Detection)   │
└────┬─────┘  └──────┬───────┘
     │               │
     └──────┬────────┘
            ▼
┌─────────────────────────┐
│          Groq           │  ← NLP Parsing & Action Plans
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│ Next.js Interactive GUI │  ← React + Leaflet + Tailwind
└─────────────────────────┘
```

---

## 🛠 Tech Stack

### Frontend

- **Next.js (React)** — component-based UI
- **TypeScript** — static typing
- **Tailwind CSS** — styling
- **Leaflet.js** — interactive map, heatmap

### Backend

- **FastAPI** — REST API, SSE streaming, prediction endpoints

### Machine Learning

- **Scikit-learn** — preprocessing, Isolation Forest
- **XGBoost** — classification and regression models
- **Pandas / NumPy** — data processing and feature engineering

### GenAI / NLP

- **Groq API** — NLP extraction and action plan generation

---

## 📊 Dashboard Views

| View                | What it shows                                                                                                 |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Map View**        | Full-screen Leaflet map with historical/streaming heatmap, anomaly zone polygons, and real-time alert sidebar |
| **Submit Incident** | Form with structured inputs and free-text NLP processing to simulate/report incidents                         |
| **Analytics**       | Historical charts: hourly volume profile, top 15 high-risk junctions, planned vs unplanned monthly trends     |

_All interactions funnel into a shared **Incident Panel** drawer that displays the prediction, streams the LLM action plan, and collects user feedback._

---

## 🚀 MVP Scope

- [x] Event input form (structured + NLP description)
- [x] Traffic prediction engine (priority + duration)
- [x] Groq API integration for incident parsing & action plans
- [x] AI-powered geocoding for vague location resolution
- [x] Dynamic Congestion heatmap with City Replay
- [x] Real-time anomaly alert feed via Isolation Forest
- [x] Post-plan user feedback collection

---

## 📂 Dataset

Built on real Bengaluru traffic incident data containing:

- Planned and unplanned events, event causes, corridor rankings, resolution times, multilingual descriptions, zone and junction metadata (8,173 records total).

---

## 🎯 Goal

Enable traffic authorities to shift from **reactive** to **proactive** congestion management — using ML to forecast impact, NLP to understand incidents in any language, and GenAI to instantly generate deployment-ready response plans.

---

## 👥 Team

Built for **Smart City Hackathon** — Theme 2: Event-Driven + Anomaly-Based Traffic Congestion Prediction System
