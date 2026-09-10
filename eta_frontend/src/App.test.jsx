import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

describe('App', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.location.hash = '';
  });

  it('shows the login form when no token is stored', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('renders the dashboard when a token is available', () => {
    window.localStorage.setItem('expense-tracker-token', 'demo-token');

    render(<App />);

    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });

  it('switches to the registration form from the login screen', async () => {
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByRole('button', { name: /sign up/i }));

    expect(screen.getByRole('heading', { name: /register/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });
});
