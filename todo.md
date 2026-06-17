# Future Enhancements & TODOs

## 1. Real-time Map Updates for New Incidents
- [ ] **Frontend State Management:** Implement a shared state (e.g., React Context, Zustand, or `localStorage`) to store incidents submitted during the current session.
- [ ] **Map Merging:** Modify `MapView.tsx` to read from both the backend API (`fetchIncidents()`) and the local state.
- [ ] **Marker Handling:** 
  - If the submitted incident is at a known location (matching coordinates/junction), update the existing marker's priority and details.
  - If it is a new location, render a new pin with the correct color coding (Red for High priority, Amber for Low priority).
- [ ] **Ephemeral Persistence:** Keep this data in local state so the pins persist as long as the user's session/localStorage is active, until a full backend persistence mechanism is integrated.

## 2. Real-time Anomaly Detection Updates
- [ ] **Frontend Anomaly Trigger:** When a new incident is submitted, immediately trigger a refresh of the anomaly detection loop for that specific zone.
- [ ] **Temporary Data Injection (Backend/Frontend):** Create a mechanism (e.g., a new `POST /anomaly/recalculate` endpoint or an in-memory session cache on the backend) to temporarily include the newly submitted, local-only incident in the Isolation Forest calculations.
- [ ] **Feedback Loop:** Ensure the anomaly zone card immediately reflects the newly calculated score and alert level without waiting for the next 5-second polling cycle.

## 3. Analytics Page Overhaul
- [ ] **Full Modification:** Completely revamp and modify the Analytics page to include more robust, interactive charts and deeper insights. (Specifics to be defined).
