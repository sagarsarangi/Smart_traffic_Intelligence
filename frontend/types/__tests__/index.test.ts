import { describe, it, expect } from 'vitest';
import type { IncidentPin } from '../index';

describe('Types sanity checks', () => {
  it('ensures IncidentPin type structure is valid', () => {
    const pin: IncidentPin = {
      id: 'pin-123',
      lat: 12.9352,
      lng: 77.6245,
      zone: 'HSR Layout'
    };
    expect(pin.id).toBe('pin-123');
    expect(typeof pin.lat).toBe('number');
    expect(typeof pin.lng).toBe('number');
  });
});
