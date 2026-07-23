import { useEffect, useState } from 'react';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

const STORAGE_KEY = 'expense-tracker-token';
const THEME_KEY = 'expense-tracker-theme';

function App() {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY));
  const [theme, setTheme] = useState(localStorage.getItem(THEME_KEY) || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  function handleLogin(jwtToken) {
    localStorage.setItem(STORAGE_KEY, jwtToken);
    setToken(jwtToken);
  }

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
  }

  return token ? (
    <Dashboard token={token} onLogout={handleLogout} theme={theme} setTheme={setTheme} />
  ) : (
    <Login onLogin={handleLogin} />
  );
}

export default App;
