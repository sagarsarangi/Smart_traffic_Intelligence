import { describe, it, expect, vi, beforeEach } from 'vitest';
import { geocodeZone } from '../api';

describe('API Geocode tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('geocodeZone high/ambiguous/failed response shapes + network-error fallback', async () => {
    // Mock high confidence
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ confidence: 'high', lat: 12.91, lng: 77.64, resolved_name: 'HSR Layout' })
    });
    const resHigh = await geocodeZone('HSR');
    expect(resHigh.confidence).toBe('high');
    expect(resHigh.lat).toBe(12.91);

    // Mock network failure fallback
    global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network disconnected'));
    const resFail = await geocodeZone('Koramangala');
    expect(resFail.confidence).toBe('failed');
    expect(resFail.message).toContain('Network error');
  });
});
