import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';
import { SUPPORT_EMAIL } from '../config';

describe('Help & Support navigation', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.location.hash = '';
  });

  it('opens the public support page from login and returns to sign in', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: /help & support/i }));
    expect(screen.getByRole('heading', { name: /frequently asked questions/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: SUPPORT_EMAIL })).toHaveAttribute('href', expect.stringContaining('mailto:'));

    await user.click(screen.getByRole('button', { name: /back to app/i }));
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
  });
});
