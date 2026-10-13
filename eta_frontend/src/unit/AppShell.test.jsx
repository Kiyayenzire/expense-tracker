import { fireEvent, render, screen } from '@testing-library/react';
import { AppShell } from '../components/AppShell';

const { post } = vi.hoisted(() => ({ post: vi.fn() }));

vi.mock('../api', () => ({
  createClient: () => ({ post }),
}));

vi.mock('../hooks/useDashboardData', () => ({
  useDashboardData: () => ({ currencies: [] }),
}));

vi.mock('../hooks/useOfflineSync', () => ({
  useOfflineSync: () => ({ queuedCount: 0, isSyncing: false }),
}));

vi.mock('../components/Header', () => ({ Header: () => null }));
vi.mock('../components/SummaryGrid', () => ({ SummaryGrid: () => null }));

describe('AppShell email verification notice', () => {
  beforeEach(() => post.mockReset());

  it('shows a warning without displaying the address for an unverified user', () => {
    render(
      <AppShell
        token="token"
        currentUser={{ email: 'private@example.com', email_verified: false }}
        displayCurrency="EUR"
      >
        <div>Page content</div>
      </AppShell>,
    );

    expect(screen.getByText(/your email address is not verified/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument();
    expect(screen.queryByText(/private@example\.com/i)).not.toBeInTheDocument();
  });

  it('shows the email-change deadline for an existing user', () => {
    render(
      <AppShell
        token="token"
        currentUser={{
          email: 'old@example.com',
          email_verified: true,
          email_change_pending: true,
          pending_email: 'new@example.com',
          email_change_days_remaining: 31,
          email_update_required: true,
        }}
        displayCurrency="EUR"
      >
        <div>Page content</div>
      </AppShell>,
    );

    expect(screen.getByText(/verify your new email address/i)).toBeInTheDocument();
    expect(screen.getByText(/new@example\.com within 31 days/i)).toBeInTheDocument();
    expect(screen.getByText(/97 days after deactivation/i)).toBeInTheDocument();
  });

  it('resends verification, confirms it was sent, and hides the resend button', async () => {
    post.mockResolvedValue({ data: {} });
    render(
      <AppShell
        token="token"
        currentUser={{ email: 'private@example.com', email_verified: false }}
        displayCurrency="EUR"
      >
        <div>Page content</div>
      </AppShell>,
    );

    fireEvent.click(screen.getByRole('button', { name: /resend verification email/i }));

    expect(await screen.findByText(/verification email sent\. please check your inbox or spam folder/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /resend verification email/i })).not.toBeInTheDocument();
    expect(post).toHaveBeenCalledWith('/auth/registration/resend-email/', { email: 'private@example.com' });
  });

  it('does not show the notice for a verified user', () => {
    render(
      <AppShell
        token="token"
        currentUser={{ email: 'private@example.com', email_verified: true }}
        displayCurrency="EUR"
      >
        <div>Page content</div>
      </AppShell>,
    );

    expect(screen.queryByText(/your email address is not verified/i)).not.toBeInTheDocument();
  });

  it('shows the result when a verification link is handled', () => {
    render(
      <AppShell
        token="token"
        currentUser={{ email: 'private@example.com', email_verified: true }}
        verificationNotice="Email verified successfully."
        displayCurrency="EUR"
      >
        <div>Page content</div>
      </AppShell>,
    );

    expect(screen.getByRole('status')).toHaveTextContent(/email verified successfully/i);
  });
});
