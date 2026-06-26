import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import NeoFooter from '../NeoFooter';

describe('Component Smoke Tests', () => {
  it('renders NeoFooter correctly with brand ticker', () => {
    render(<NeoFooter />);
    expect(screen.getAllByText(/SMART TRAFFIC INTELLIGENCE/i).length).toBeGreaterThan(0);
  });
});
