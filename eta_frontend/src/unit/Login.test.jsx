import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from '../components/Login';

describe('Login unit tests', () => {
  it('renders the login form by default', () => {
    render(<Login onLogin={() => {}} />);

    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username or email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('switches to the registration fields when sign up is pressed', async () => {
    const user = userEvent.setup();
    render(<Login onLogin={() => {}} />);

    await user.click(screen.getByRole('button', { name: /sign up/i }));

    expect(screen.getByRole('heading', { name: /register/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('shows required validation when the user submits empty login details', async () => {
    const user = userEvent.setup();
    render(<Login onLogin={() => {}} />);

    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(screen.getByText(/please enter both username\/email and password/i)).toBeInTheDocument();
  });
});
