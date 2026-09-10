import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

describe('Frontend navigation integration tests', () => {
  beforeEach(() => {
    window.localStorage.setItem('expense-tracker-token', 'demo-token');
    window.location.hash = '#/dashboard';
  });

  it('navigates to the add expense page from the dashboard navigation', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: /add expense/i }));

    expect(screen.getByText(/record a new expense for your account/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /add expense/i })).toBeInTheDocument();
  });

  it('opens the summary menu and navigates to a period summary page', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: /open summary menu/i }));
    await user.click(screen.getByRole('button', { name: /monthly/i }));

    expect(screen.getByText(/monthly summary/i)).toBeInTheDocument();
  });
});
