import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App theme persistence', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.location.hash = '';
    window.localStorage.setItem('expense-tracker-token', 'demo-token');
  });

  it('removes an unsupported stored theme and starts with light', () => {
    window.localStorage.setItem('expense-tracker-theme', 'purple');

    render(<App />);

    expect(screen.getByRole('button', { name: 'Light theme' })).toHaveAttribute('aria-pressed', 'true');
    expect(document.documentElement).toHaveAttribute('data-theme', 'light');
    expect(window.localStorage.getItem('expense-tracker-theme')).toBe('light');
  });
});
