const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHeatmap() {
    try {
        const response = await fetch(`${API_BASE_URL}/heatmap`);
        if (!response.ok) throw new Error('Failed to fetch heatmap data');
        return await response.json();
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function fetchIncidents(params: { zone?: string, priority?: string, event_type?: string } = {}) {
    try {
        const queryParams = new URLSearchParams();
        if (params.zone) queryParams.append('zone', params.zone);
        if (params.priority) queryParams.append('priority', params.priority);
        if (params.event_type) queryParams.append('event_type', params.event_type);
        
        const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
        const response = await fetch(`${API_BASE_URL}/incidents${queryString}`);
        if (!response.ok) throw new Error('Failed to fetch incidents');
        return await response.json();
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function fetchAnomalyScores() {
    try {
        const response = await fetch(`${API_BASE_URL}/anomaly`);
        if (!response.ok) throw new Error('Failed to fetch anomaly scores');
        return await response.json();
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function fetchAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics`);
        if (!response.ok) throw new Error('Failed to fetch analytics');
        return await response.json();
    } catch (error) {
        console.error("Analytics endpoint might not exist, using local mock data.", error);
        return null;
    }
}

export async function parseNLPDescription(description: string) {
    try {
        const response = await fetch(`${API_BASE_URL}/nlp-parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description })
        });
        if (!response.ok) throw new Error('Failed to parse NLP description');
        return await response.json();
    } catch (error) {
        console.error(error);
        return null;
    }
}

export async function predictIncident(features: any) {
    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(features)
        });
        if (!response.ok) throw new Error('Failed to predict incident');
        return await response.json();
    } catch (error) {
        console.error(error);
        return null;
    }
}

export async function submitFeedback(feedback: { incident_context: any, action_plan: string, rating: 'up' | 'down' }) {
    try {
        const response = await fetch(`${API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedback)
        });
        if (!response.ok) throw new Error('Failed to submit feedback');
        return await response.json();
    } catch (error) {
        console.error(error);
        return null;
    }
}

export function getActionPlanEventSource(queryParams: Record<string, any>) {
    const params = new URLSearchParams();
    for (const key in queryParams) {
        if (queryParams[key] !== undefined && queryParams[key] !== null) {
            params.append(key, queryParams[key].toString());
        }
    }
    return new EventSource(`${API_BASE_URL}/action-plan?${params.toString()}`);
}
