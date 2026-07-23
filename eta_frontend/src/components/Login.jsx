import { useState } from 'react';
import axios from 'axios';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.');
      return;
    }

    setError('');

    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
      const response = await axios.post(`${apiBase}/auth/login/`, {
        username: username.trim(),
        password: password.trim(),
      });

      const token = response.data?.key || response.data?.token;
      if (!token) {
        throw new Error('Login did not return an authentication token.');
      }
      onLogin(token);
    } catch (loginError) {
      setError(
        loginError.response?.data?.detail ||
          loginError.response?.data?.non_field_errors?.[0] ||
          'Login failed, please check credentials.'
      );
    }
  };

  return (
    <div className="container">
      <div className="card">
        <div className="header">
          <div>
            <h1>Expense Tracker</h1>
            <p className="small-text">Login to access your dashboard.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Username"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
            />
          </div>

          {error && <p className="small-text" style={{ color: '#dc2626' }}>{error}</p>}

          <button type="submit">Login</button>
        </form>
      </div>
    </div>
  );
}

export default Login;
