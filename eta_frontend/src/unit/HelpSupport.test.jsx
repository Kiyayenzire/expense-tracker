import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HelpSupport from '../pages/HelpSupport';
import { SUPPORT_EMAIL } from '../config';

describe('HelpSupport', () => {
  it('shows FAQs and expands the selected answer', async () => {
    const user = userEvent.setup();
    render(<HelpSupport />);

    const question = screen.getByRole('button', { name: /how do i reset my password/i });
    expect(question).toHaveAttribute('aria-expanded', 'false');
    await user.click(question);

    expect(question).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/click 'forgot password' on the login screen/i)).toBeInTheDocument();
  });

  it('creates a support email with the signed-in user context', () => {
    render(<HelpSupport currentUser={{ id: 42, email: 'user@example.com' }} />);

    const emailLink = screen.getByRole('link', { name: SUPPORT_EMAIL });
    const mailto = new URL(emailLink.href);
    const body = decodeURIComponent(mailto.searchParams.get('body'));

    expect(emailLink).toHaveAttribute('href', expect.stringContaining(`mailto:${SUPPORT_EMAIL}`));
    expect(body).toContain('Account Email: user@example.com');
    expect(body).toContain('User ID: 42');
  });

  it('reports clipboard copy success', async () => {
    const user = userEvent.setup();
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
    render(<HelpSupport />);

    await user.click(screen.getByRole('button', { name: /copy email address/i }));

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(SUPPORT_EMAIL);
    expect(screen.getByRole('status')).toHaveTextContent(/copied/i);
  });

  it('shows a selectable-copy fallback when clipboard access is denied', async () => {
    const user = userEvent.setup();
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: vi.fn().mockRejectedValue(new Error('denied')) },
    });
    render(<HelpSupport />);

    await user.click(screen.getByRole('button', { name: /copy email address/i }));

    expect(screen.getByRole('status')).toHaveTextContent(/select the email address below and copy it/i);
    expect(screen.getByText(SUPPORT_EMAIL)).toBeInTheDocument();
  });

  it('falls back to copying through the document when Clipboard API is unavailable', async () => {
    const user = userEvent.setup();
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined });
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, 'execCommand', { configurable: true, value: execCommand });
    render(<HelpSupport />);

    await user.click(screen.getByRole('button', { name: /copy email address/i }));

    expect(execCommand).toHaveBeenCalledWith('copy');
    expect(screen.getByRole('status')).toHaveTextContent(/copied/i);
    delete document.execCommand;
  });
});
