import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Header } from '../components/Header';

describe('Header', () => {
  it('shows only the three supported themes as buttons', async () => {
    const user = userEvent.setup();
    const setTheme = vi.fn();

    render(
      <Header
        activePage="dashboard"
        onNavigate={vi.fn()}
        onLogout={vi.fn()}
        theme="light"
        setTheme={setTheme}
      />,
    );

    expect(screen.getAllByRole('button', { name: /theme$/i })).toHaveLength(3);
    expect(screen.getByRole('button', { name: 'Light theme' })).toHaveTextContent('☀');
    expect(screen.getByRole('button', { name: 'Dark theme' })).toHaveTextContent('☾');
    expect(screen.getByRole('button', { name: 'Gold theme' })).toHaveTextContent('✦');
    expect(screen.queryByText('Light')).not.toBeInTheDocument();
    expect(screen.queryByText('Dark')).not.toBeInTheDocument();
    expect(screen.queryByText('Gold')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Light theme' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Dark theme' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: 'Gold theme' })).toHaveAttribute('aria-pressed', 'false');

    await user.click(screen.getByRole('button', { name: 'Dark theme' }));

    expect(setTheme).toHaveBeenCalledWith('dark');
  });

  it('renders an uploaded profile image in the avatar', () => {
    render(
      <Header
        activePage="dashboard"
        onNavigate={vi.fn()}
        onLogout={vi.fn()}
        theme="light"
        setTheme={vi.fn()}
        username="Ada Lovelace"
        profilePicture="/media/profile.png"
      />,
    );

    const profileButton = screen.getByRole('button', { name: 'Open account menu' });
    expect(profileButton).toHaveTextContent('Profile');

    const avatarImage = profileButton.querySelector('img');
    expect(avatarImage).toHaveAttribute('src', '/media/profile.png');
    expect(avatarImage).toHaveAttribute('alt', '');
    expect(avatarImage.parentElement).toHaveClass('profile-picture');
  });
});
