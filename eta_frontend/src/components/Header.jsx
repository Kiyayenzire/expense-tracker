import React, { useEffect, useRef, useState } from 'react';

export function Header({
  activePage,
  onNavigate,
  onLogout,
  onDeleteAccount,
  theme,
  setTheme,
  username = '',
  profilePicture = '',
  queuedCount = 0,
  isSyncing = false,
}) {
  // ---------------------------------------------------------------------------
  // 1. LOCAL STATE & REFS
  // ---------------------------------------------------------------------------
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // ---------------------------------------------------------------------------
  // 2. HELPER FUNCTIONS & EFFECTS
  // ---------------------------------------------------------------------------
  const getInitials = (name) => {
    return name
      .split(' ')
      .map((word) => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const initials = getInitials(username || 'User');
  const displayPicture = profilePicture || null;

  // Closes the profile dropdown menu when clicking anywhere outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ---------------------------------------------------------------------------
  // 3. MAIN HEADER VIEW
  // ---------------------------------------------------------------------------
  return (
    <header className="header app-header">
      <div className="header-topline">
        <h1>Expense Tracker</h1>
        <p className="small-text">
          Today is {new Intl.DateTimeFormat('en-GB').format(new Date())}
        </p>

        <div className="header-tools">
          {/* Theme Selector */}
          <div className="theme-selector">
            <label htmlFor="theme-select" className="sr-only">
              Select app theme
            </label>
            <select
              id="theme-select"
              aria-label="Select app theme"
              value={theme}
              onChange={(event) => setTheme(event.target.value)}
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="gold">Gold</option>
              <option value="blue">Blue</option>
              <option value="green">Green</option>
              <option value="red">Red</option>
              <option value="purple">Purple</option>
            </select>
          </div>

          {/* User Profile Dropdown Menu */}
          <div className="profile-menu-wrapper" ref={menuRef}>
            <button
              type="button"
              className="user-profile-section profile-button"
              aria-expanded={menuOpen}
              aria-label="Open account menu"
              onClick={() => setMenuOpen((value) => !value)}
            >
              <div className="profile-picture">
                {displayPicture ? (
                  <img src={displayPicture} alt={username || 'User'} title={username || 'User'} />
                ) : (
                  <div className="profile-avatar" title={username || 'User'}>
                    {initials}
                  </div>
                )}
              </div>
              <span className="profile-chevron" aria-hidden="true">
                ▾
              </span>
            </button>

            {menuOpen && (
              <div
                className="profile-dropdown-menu"
                role="menu"
                aria-label="Account menu"
              >
                <div className="profile-dropdown-header">
                  <span className="profile-dropdown-label">Account settings</span>
                  <span className="profile-dropdown-name">{username || 'User'}</span>
                </div>
                <button
                  type="button"
                  className="profile-dropdown-item"
                  onClick={() => {
                    setMenuOpen(false);
                    onNavigate && onNavigate('profile');
                  }}
                >
                  Profile
                </button>
                {onDeleteAccount && (
                  <button
                    type="button"
                    className="profile-dropdown-item danger-item"
                    onClick={() => {
                      setMenuOpen(false);
                      onDeleteAccount();
                    }}
                  >
                    Delete account
                  </button>
                )}
                <button
                  type="button"
                  className="profile-dropdown-item danger-item"
                  onClick={() => {
                    setMenuOpen(false);
                    onLogout && onLogout();
                  }}
                >
                  Log out
                </button>
              </div>
            )}
          </div>

          {/* Sync Status Badges */}
          {queuedCount > 0 && (
            <span
              className="badge bg-warning text-dark"
              title={`${queuedCount} item(s) queued for sync`}
            >
              ⧖ {queuedCount}
            </span>
          )}
          {isSyncing && (
            <span className="badge bg-info text-white" title="Syncing expenses">
              ⟳ Syncing
            </span>
          )}
        </div>
      </div>

      {/* Main Navigation Bar */}
      <nav className="nav-actions" aria-label="Main navigation">
        <button
          type="button"
          className={activePage === 'dashboard' ? 'nav-button active' : 'nav-button'}
          onClick={() => onNavigate('dashboard')}
        >
          Dashboard
        </button>
        <button
          type="button"
          className={activePage === 'add-expense' ? 'nav-button active' : 'nav-button'}
          onClick={() => onNavigate('add-expense')}
        >
          Add Expense
        </button>
        <button
          type="button"
          className={activePage === 'expenses' ? 'nav-button active' : 'nav-button'}
          onClick={() => onNavigate('expenses')}
        >
          Expenses
        </button>
        <button
          type="button"
          className={activePage === 'reports' ? 'nav-button active' : 'nav-button'}
          onClick={() => onNavigate('reports')}
        >
          Reports
        </button>
        <button
          type="button"
          className={activePage === 'insights' ? 'nav-button active' : 'nav-button'}
          onClick={() => onNavigate('insights')}
        >
          Insights
        </button>
      </nav>
    </header>
  );
}