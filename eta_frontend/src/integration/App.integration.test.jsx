import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import App from '../App';

vi.mock('axios');

describe('App integration tests', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.location.hash = '';
    vi.clearAllMocks();
  });

  it('logs a user in and shows the dashboard main navigation', async () => {
    const user = userEvent.setup();
    axios.post.mockResolvedValue({ data: { key: 'demo-token' } });

    render(<App />);

    await user.type(screen.getByLabelText(/username or email/i), 'demo-user');
    await user.type(screen.getByLabelText(/password/i), 'strong-password');
    await user.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(window.localStorage.getItem('expense-tracker-token')).toBe('demo-token');
    });

    expect(await screen.findByRole('button', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
  });

  it('shows the delete account modal when the dashboard action is used', async () => {
    window.localStorage.setItem('expense-tracker-token', 'demo-token');

    render(<App />);

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    await userEvent.click(deleteButton);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/delete account\?/i)).toBeInTheDocument();
  });
});
