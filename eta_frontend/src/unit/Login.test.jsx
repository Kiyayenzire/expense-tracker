import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import Login from '../components/Login';

afterEach(() => vi.restoreAllMocks());

describe('Login unit tests', () => {
  it('renders the login form by default', () => {
    render(<Login onLogin={() => {}} onNavigate={() => {}} />);

    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username or email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.queryByText(/irislee\.8154@gmail\.com/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /need help\? help & support/i })).toBeInTheDocument();
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

  it('shows Google and Apple options with icons on sign-in and registration', async () => {
    const user = userEvent.setup();
    render(<Login onLogin={() => {}} />);

    const googleButton = screen.getByRole('button', { name: 'Continue with Google' });
    const appleButton = screen.getByRole('button', { name: 'Continue with Apple' });
    expect(googleButton).toBeInTheDocument();
    expect(appleButton).toBeInTheDocument();
    expect(document.querySelector('.fa-google')).toBeInTheDocument();
    expect(document.querySelector('.fa-apple')).toBeInTheDocument();
    expect(googleButton).not.toHaveTextContent('Google');
    expect(appleButton).not.toHaveTextContent('Apple');

    await user.click(screen.getByRole('button', { name: /sign up/i }));

    expect(screen.getByRole('button', { name: 'Continue with Google' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Continue with Apple' })).toBeInTheDocument();
  });

  it('does not report providers as unconfigured when the status request fails', async () => {
    const user = userEvent.setup();
    vi.spyOn(axios, 'get').mockRejectedValue(new Error('offline'));

    render(<Login onLogin={() => {}} />);

    expect(await screen.findByRole('status')).toHaveTextContent(/availability could not be checked/i);
    await user.click(screen.getByRole('button', { name: 'Continue with Google' }));

    expect(screen.getByText(/could not check social sign-in configuration/i)).toBeInTheDocument();
  });

  it('reports a provider as unconfigured when the backend confirms it is missing', async () => {
    const user = userEvent.setup();
    vi.spyOn(axios, 'get').mockResolvedValue({
      data: {
        providers: {
          google: { configured: false, url: '' },
          apple: { configured: false, url: '' },
        },
        support: {},
      },
    });

    render(<Login onLogin={() => {}} />);
    await user.click(screen.getByRole('button', { name: 'Continue with Google' }));

    expect(screen.getByText(/google sign-in is not configured yet/i)).toBeInTheDocument();
  });

  it('keeps registration pending until the user verifies their email', async () => {
    const user = userEvent.setup();
    vi.spyOn(axios, 'get').mockResolvedValue({ data: { providers: {}, support: {} } });
    const post = vi.spyOn(axios, 'post').mockResolvedValue({ data: {} });

    render(<Login onLogin={() => {}} />);

    await user.click(screen.getByRole('button', { name: /sign up/i }));
    await user.type(screen.getByLabelText(/username/i), 'pending-user');
    await user.type(screen.getByLabelText(/^email$/i), 'pending@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'StrongPassword1!');
    await user.type(screen.getByLabelText(/confirm password/i), 'StrongPassword1!');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByRole('heading', { name: /check your email/i })).toBeInTheDocument();
    expect(screen.getByText(/account is not ready to sign in until you verify/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith('/api/auth/registration/', expect.objectContaining({ email: 'pending@example.com' }));
  });

  it('displays the expected error for an invalid registration email', async () => {
    const user = userEvent.setup();
    vi.spyOn(axios, 'get').mockResolvedValue({ data: { providers: {}, support: {} } });
    const post = vi.spyOn(axios, 'post');
    render(<Login onLogin={() => {}} />);

    await user.click(screen.getByRole('button', { name: /sign up/i }));
    await user.type(screen.getByLabelText(/username/i), 'invalid-email-user');
    await user.type(screen.getByLabelText(/^email$/i), 'not-an-email');
    await user.type(screen.getByLabelText(/^password$/i), 'StrongPassword1!');
    await user.type(screen.getByLabelText(/confirm password/i), 'StrongPassword1!');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText(/please enter a valid email address/i)).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });

  it('shows a clear message when registration uses an existing email', async () => {
    const user = userEvent.setup();
    vi.spyOn(axios, 'get').mockResolvedValue({ data: { providers: {}, support: {} } });
    vi.spyOn(axios, 'post').mockRejectedValue({
      response: { data: { email: ['A user is already registered with this email address.'] } },
    });
    render(<Login onLogin={() => {}} />);

    await user.click(screen.getByRole('button', { name: /sign up/i }));
    await user.type(screen.getByLabelText(/username/i), 'existing-user');
    await user.type(screen.getByLabelText(/^email$/i), 'existing@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'StrongPassword1!');
    await user.type(screen.getByLabelText(/confirm password/i), 'StrongPassword1!');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText(/this email address is already registered/i)).toBeInTheDocument();
  });

  it('shows the server message for a wrong password', async () => {
    const user = userEvent.setup();
    vi.spyOn(axios, 'get').mockResolvedValue({ data: { providers: {}, support: {} } });
    vi.spyOn(axios, 'post').mockRejectedValue({
      response: { data: { detail: 'Incorrect password.' } },
    });
    render(<Login onLogin={() => {}} />);

    await user.type(screen.getByLabelText(/username or email/i), 'user@example.com');
    await user.type(screen.getByLabelText(/password/i), 'WrongPassword1!');
    await user.click(screen.getByRole('button', { name: /^login$/i }));

    expect(await screen.findByText(/incorrect password/i)).toBeInTheDocument();
  });
});
