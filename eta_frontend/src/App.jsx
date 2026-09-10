import { useEffect, useState } from 'react';
import Login from './components/Login';
import Dashboard from './Dashboard';
import AddExpensePage from './AddExpensePage';
import ExpensesPage from './ExpensesPage';
import ReportsPage from './ReportsPage';
import InsightsPage from './InsightsPage';
import PeriodSummaryPage from './PeriodSummaryPage';
import ProfilePage from './ProfilePage';
import SpendingTrendsPage from './SpendingTrendsPage';
import { AppShell } from './components/AppShell';

const STORAGE_KEY = 'expense-tracker-token';
const THEME_KEY = 'expense-tracker-theme';
const USERNAME_KEY = 'expense-tracker-username';
const PROFILE_PICTURE_KEY = 'expense-tracker-profile-picture';
const getPageFromHash = () => window.location.hash.replace('#/', '') || 'dashboard';

function App() {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY));
  const [username, setUsername] = useState(localStorage.getItem(USERNAME_KEY) || 'User');
  const [profilePicture, setProfilePicture] = useState(localStorage.getItem(PROFILE_PICTURE_KEY) || '');
  const [theme, setTheme] = useState(localStorage.getItem(THEME_KEY) || 'light');
  const [displayCurrency, setDisplayCurrency] = useState('EUR');
  const [page, setPage] = useState(getPageFromHash);
  const [deleteFlow, setDeleteFlow] = useState({ isOpen: false, password: '', error: '' });

  useEffect(() => {
    const syncPage = () => setPage(getPageFromHash());
    window.addEventListener('hashchange', syncPage);
    window.addEventListener('popstate', syncPage);
    return () => {
      window.removeEventListener('hashchange', syncPage);
      window.removeEventListener('popstate', syncPage);
    };
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (!token) return;

    fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/auth/profile/`, {
      headers: {
        Authorization: `Token ${token}`,
      },
    })
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load user profile.');
        return response.json();
      })
      .then((data) => {
        const nextUsername = data.username || localStorage.getItem(USERNAME_KEY) || username || 'User';
        const nextPicture = data.profile_picture_url || data.profile_picture || localStorage.getItem(PROFILE_PICTURE_KEY) || '';
        const safeUsername = String(nextUsername || 'User').trim();

        localStorage.setItem(USERNAME_KEY, safeUsername);
        if (nextPicture) {
          localStorage.setItem(PROFILE_PICTURE_KEY, nextPicture);
        } else {
          localStorage.removeItem(PROFILE_PICTURE_KEY);
        }
        setUsername(safeUsername);
        setProfilePicture(nextPicture);
      })
      .catch(() => {
        // Keep the existing local user info if the profile endpoint is unavailable.
      });
  }, [token]);

  function handleLogin(jwtToken, loggedInUsername = '', profileImage = '') {
    const sourceUsername = loggedInUsername || localStorage.getItem(USERNAME_KEY) || username || 'User';
    const safeUsername = String(sourceUsername).trim() || 'User';
    const safeProfilePicture = profileImage || localStorage.getItem(PROFILE_PICTURE_KEY) || '';

    localStorage.setItem(STORAGE_KEY, jwtToken);
    localStorage.setItem(USERNAME_KEY, safeUsername);
    if (safeProfilePicture) {
      localStorage.setItem(PROFILE_PICTURE_KEY, safeProfilePicture);
    } else {
      localStorage.removeItem(PROFILE_PICTURE_KEY);
    }
    setToken(jwtToken);
    setUsername(safeUsername);
    setProfilePicture(safeProfilePicture);
  }

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(USERNAME_KEY);
    localStorage.removeItem(PROFILE_PICTURE_KEY);
    setToken(null);
    setUsername('User');
    setProfilePicture('');
    setDeleteFlow({ isOpen: false, password: '', error: '' });
  }

  function openDeleteAccountFlow() {
    setDeleteFlow({ isOpen: true, password: '', error: '' });
  }

  function closeDeleteAccountFlow() {
    setDeleteFlow({ isOpen: false, password: '', error: '' });
  }

  async function handleDeleteAccountSubmit(event) {
    event.preventDefault();
    const password = deleteFlow.password.trim();

    if (!password) {
      setDeleteFlow((current) => ({ ...current, error: 'Please enter your current password to continue.' }));
      return;
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/auth/delete-account/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify({ password }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to request account deletion.');
      }

      window.alert(data.detail || 'Account deletion requested.');
      closeDeleteAccountFlow();
      handleLogout();
    } catch (error) {
      setDeleteFlow((current) => ({ ...current, error: error.message || 'Unable to request account deletion.' }));
    }
  }

  function navigate(nextPage) {
    const hash = nextPage === 'dashboard' ? '#/' : `#/${nextPage}`;
    window.history.pushState({}, '', `${window.location.pathname}${window.location.search}${hash}`);
    setPage(nextPage);
  }

  const dashboardView = (
    <>
      {deleteFlow.isOpen && (
        <div className="delete-confirm-overlay" role="dialog" aria-modal="true" aria-labelledby="delete-account-title">
          <div className="delete-confirm-card">
            <h2 id="delete-account-title">Delete Account?</h2>
            <p>
              This action starts a 31-day account deletion process. During that time, your account remains available,
              but your data will be marked for permanent removal. If you log in again before the 31-day period ends,
              the deletion request is cancelled automatically.
            </p>
            <p className="warning-copy">
              Please confirm your current password below to continue.
            </p>
            <form onSubmit={handleDeleteAccountSubmit} className="delete-account-form">
              <label htmlFor="delete-password" className="sr-only">Current password</label>
              <input
                id="delete-password"
                type="password"
                value={deleteFlow.password}
                onChange={(event) => setDeleteFlow((current) => ({ ...current, password: event.target.value, error: '' }))}
                placeholder="Current password"
              />
              {deleteFlow.error && <p className="delete-error">{deleteFlow.error}</p>}
              <div className="delete-actions">
                <button type="button" className="secondary-action-button" onClick={closeDeleteAccountFlow}>Cancel</button>
                <button type="submit" className="danger-action-button">Confirm delete</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {page === 'profile' ? <ProfilePage token={token} onLogout={handleLogout} onNavigate={navigate} username={username} profilePicture={profilePicture} setProfilePicture={setProfilePicture} setUsername={setUsername} />
        : page === 'add-expense' ? <AddExpensePage token={token} onLogout={handleLogout} onNavigate={navigate} />
          : page === 'expenses' ? <ExpensesPage token={token} onLogout={handleLogout} onNavigate={navigate} displayCurrency={displayCurrency} />
            : page === 'reports' ? <ReportsPage token={token} onLogout={handleLogout} displayCurrency={displayCurrency} />
              : page === 'spending-trends' ? <SpendingTrendsPage token={token} onLogout={handleLogout} displayCurrency={displayCurrency} />
              : page === 'insights' ? <InsightsPage token={token} onLogout={handleLogout} displayCurrency={displayCurrency} />
                : ['daily', 'weekly', 'monthly', 'quarterly', 'annual'].includes(page) ? <PeriodSummaryPage period={page} token={token} onLogout={handleLogout} displayCurrency={displayCurrency} />
                : <Dashboard token={token} onLogout={handleLogout} theme={theme} setTheme={setTheme} onNavigate={navigate} onDeleteAccount={openDeleteAccountFlow} username={username} profilePicture={profilePicture} />}
    </>
  );

  return token
    ? page === 'dashboard'
      ? dashboardView
      : <AppShell
          token={token}
          onLogout={handleLogout}
          theme={theme}
          setTheme={setTheme}
          onNavigate={navigate}
          username={username}
          profilePicture={profilePicture}
          displayCurrency={displayCurrency}
          setDisplayCurrency={setDisplayCurrency}
        >
          {dashboardView}
        </AppShell>
    : <Login onLogin={handleLogin} />;
}

export default App;
