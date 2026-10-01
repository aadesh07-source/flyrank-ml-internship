import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Hero from '../sections/Hero';
import Limitations from '../sections/Limitations';

describe('Frontend Component Tests', () => {
  it('renders Hero section with working title', () => {
    render(<Hero />);
    expect(screen.getByText(/CTR & Engagement Opportunity Scoring/i)).toBeInTheDocument();
  });

  it('renders Limitations section with honest framing callout', () => {
    render(<Limitations id="limitations" />);
    expect(screen.getByText(/What this research does NOT claim/i)).toBeInTheDocument();
  });
});
