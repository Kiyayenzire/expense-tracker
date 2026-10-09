import { useState, useEffect } from 'react';
import axios from 'axios';

// 1. Email Regex & Helper outside the component
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const formatFieldError = (error) => {
  if (!error) return null;
  return Array.isArray(error) ? error.join(' ') : error;
};

const getApiErrorMessage = (data, fallback) => {
  if (data?.detail) return formatFieldError(data.detail);
  const firstMessage = Object.values(data || {}).flat().find((value) => typeof value === 'string');
  return firstMessage || fallback;
};

function Login({ onLogin, onNavigate }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [isResettingPassword, setIsResettingPassword] = useState(false);
  const [resetStep, setResetStep] = useState('request'); // 'request' or 'confirm'
  const [identifier, setIdentifier] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [resetEmail, setResetEmail] = useState('');
  const [resetUid, setResetUid] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [resetPassword, setResetPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [pendingVerificationEmail, setPendingVerificationEmail] = useState('');
  const [verificationStatus, setVerificationStatus] = useState('idle');
  const [resendingVerification, setResendingVerification] = useState(false);
  const [authOptions, setAuthOptions] = useState({
    providers: { google: { configured: false, url: '' }, apple: { configured: false, url: '' } },
    support: { email: '', phone: '' },
  });
  const [authOptionsStatus, setAuthOptionsStatus] = useState('loading');
  
  // Field-specific errors object and general fallback error
  const [fieldErrors, setFieldErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [success, setSuccess] = useState('');

  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api';

  const clearErrors = () => {
    setFieldErrors({});
    setGeneralError('');
    setSuccess('');
  };

  useEffect(() => {
    axios.get(`${apiBase}/auth/options/`)
      .then((response) => {
        setAuthOptions((current) => ({ ...current, ...response.data }));
        setAuthOptionsStatus('ready');
      })
      .catch(() => setAuthOptionsStatus('error'));
  }, [apiBase]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    clearErrors();

    const normalizedIdentifier = identifier.trim().toLowerCase();
    const normalizedEmail = email.trim().toLowerCase();

  // REGISTRATION FLOW
  if (isRegistering) {
    const newErrors = {};

    if (!normalizedIdentifier) {
      newErrors.username = 'Username is required.';
    }

    if (!normalizedEmail || !EMAIL_REGEX.test(normalizedEmail)) {
      newErrors.email = 'Please enter a valid email address (e.g., user@example.com).';
    }

    if (!password) {
      newErrors.password1 = 'Password is required.';
    } else if (password !== confirmPassword) {
      newErrors.password2 = 'Passwords do not match.';
    }

    if (Object.keys(newErrors).length > 0) {
      setFieldErrors(newErrors);
      return;
    }

    try {
      await axios.post(`${apiBase}/auth/registration/`, {
        username: normalizedIdentifier,
        email: normalizedEmail,
        password1: password.trim(),
        password2: confirmPassword.trim(),
      });

      setPendingVerificationEmail(normalizedEmail);
      setIsRegistering(false);
      setPassword('');
      setConfirmPassword('');
      setSuccess('');
    } catch (signupError) {
      const data = signupError.response?.data || {};
      if (data.verification_pending) {
        setPendingVerificationEmail(data.email || normalizedEmail);
        setIsRegistering(false);
        setGeneralError(getApiErrorMessage(data, 'Your account is pending email verification.'));
        return;
      }
      if (typeof data === 'object' && !Array.isArray(data)) {
        setFieldErrors(data);
        const emailError = formatFieldError(data.email);
        if (emailError && /already|registered|exists/i.test(emailError)) {
          setGeneralError('This email address is already registered. Sign in or use Forgot password.');
        } else {
          setGeneralError(getApiErrorMessage(data, 'Registration could not be completed. Check the highlighted fields and try again.'));
        }
      } else {
        setGeneralError('Registration could not be completed. Please check your details and try again.');
      }
    }

    return;
  }

  // LOGIN FLOW
  if (!normalizedIdentifier || !password.trim()) {
    setGeneralError('Please enter both username/email and password.');
    return;
  }

  try {
    const response = await axios.post(`${apiBase}/auth/login/`, {
      username: normalizedIdentifier,
      password: password.trim(),
    });

    const token = response.data?.key || response.data?.token;
    if (!token) {
      throw new Error('Login did not return an authentication token.');
    }

    const backendUsername = response.data?.user?.username || response.data?.username || normalizedIdentifier;
    const backendProfilePicture = response.data?.user?.profile_picture_url || response.data?.user?.profile_picture || '';
    onLogin(token, backendUsername, backendProfilePicture, response.data?.user);
  } catch (loginError) {
    const data = loginError.response?.data;
    setGeneralError(
      data?.detail ||
      data?.non_field_errors?.[0] ||
      'We could not sign you in. Check your username or email and password.'
    );
  }
};

  const handleResendVerification = async () => {
    if (!pendingVerificationEmail) return;
    setResendingVerification(true);
    clearErrors();
    try {
      await axios.post(`${apiBase}/auth/registration/resend-email/`, { email: pendingVerificationEmail });
      setSuccess('A new verification email has been sent. Check your inbox and spam folder.');
    } catch (error) {
      setGeneralError(getApiErrorMessage(error.response?.data, 'We could not resend the verification email. Try again shortly.'));
    } finally {
      setResendingVerification(false);
    }
  };

  const handleSocialLogin = (provider) => {
    if (authOptionsStatus === 'loading') {
      setGeneralError('Checking social sign-in configuration. Please try again shortly.');
      return;
    }
    if (authOptionsStatus === 'error') {
      setGeneralError('Could not check social sign-in configuration. Please try again shortly.');
      return;
    }

    const providerConfig = authOptions.providers?.[provider];
    if (!providerConfig?.configured || !providerConfig.url) {
      setGeneralError(`${provider === 'google' ? 'Google' : 'Apple'} sign-in is not configured yet. Contact support for help.`);
      return;
    }
    window.location.assign(providerConfig.url);
  };

  const handlePasswordReset = async (event) => {
    event.preventDefault();
    clearErrors();

    const normalizedEmail = resetEmail.trim().toLowerCase();

    if (!normalizedEmail || !EMAIL_REGEX.test(normalizedEmail)) {
      setFieldErrors({ resetEmail: 'Please enter a valid email address.' });
      return;
    }

    try {
      await axios.post(`${apiBase}/auth/password/reset/`, {
        email: normalizedEmail,
      });
      setSuccess('Password reset link sent to your email. Check your inbox.');
      setResetStep('confirm');
      setResetEmail('');
    } catch (error) {
      const data = error.response?.data;
      setGeneralError(getApiErrorMessage(data, 'We could not send a reset email. Check the address and try again.'));
    }
  };

  const handlePasswordResetConfirm = async (event) => {
    event.preventDefault();
    clearErrors();

    if (!resetPassword || !resetConfirmPassword) {
      setFieldErrors({
        resetPassword: 'Password is required.',
        resetConfirmPassword: 'Confirm password is required.',
      });
      return;
    }

    if (resetPassword !== resetConfirmPassword) {
      setFieldErrors({
        resetConfirmPassword: 'Passwords do not match.',
      });
      return;
    }

    if (resetPassword.length < 8) {
      setFieldErrors({
        resetPassword: 'Password must be at least 8 characters long.',
      });
      return;
    }

    try {
      await axios.post(`${apiBase}/auth/password/reset/confirm/`, {
        uid: resetUid,
        token: resetToken,
        new_password: resetPassword.trim(),
      });
      setSuccess('Password reset successfully. You can now log in.');
      setIsResettingPassword(false);
      setResetStep('request');
      setResetPassword('');
      setResetConfirmPassword('');
      setResetUid('');
      setResetToken('');
    } catch (error) {
      const data = error.response?.data;
      setGeneralError(getApiErrorMessage(data, 'We could not reset your password. Check the link and try again.'));
    }
  };

  // If we have URL params for reset, populate the state
  useEffect(() => {
    const hash = window.location.hash;
    const verificationMatch = hash.match(/\/verify-email\/([^/?#]+)/);
    if (verificationMatch) {
      const key = decodeURIComponent(verificationMatch[1]);
      setVerificationStatus('checking');
      axios.post(`${apiBase}/auth/registration/verify-email/`, { key })
        .then(() => {
          setVerificationStatus('verified');
          window.history.replaceState({}, '', `${window.location.pathname}${window.location.search}#/`);
        })
        .catch((error) => {
          setVerificationStatus('failed');
          setGeneralError(getApiErrorMessage(error.response?.data, 'This verification link is invalid or expired.'));
        });
      return;
    }

    if (hash.includes('reset-password/')) {
      const parts = hash.split('reset-password/');
      if (parts[1]) {
        const [uid, token] = parts[1].split('/');
        if (uid && token) {
          setIsResettingPassword(true);
          setResetStep('confirm');
          setResetUid(uid);
          setResetToken(token);
        }
      }
    }
  }, [apiBase]);

  return (
    <div className="auth-container">
      <div className="card auth-card">
        {verificationStatus !== 'idle' ? (
          <section className="auth-status-panel" aria-live="polite">
            <h2>{verificationStatus === 'checking' ? 'Verifying your email' : verificationStatus === 'verified' ? 'Email verified' : 'Verification link issue'}</h2>
            {verificationStatus === 'checking' ? (
              <p>Please wait while we confirm your email address.</p>
            ) : verificationStatus === 'verified' ? (
              <>
                <p>Your email is verified and your account is ready. Sign in to continue.</p>
                <button type="button" className="auth-action-button" onClick={() => setVerificationStatus('idle')}>Back to sign in</button>
              </>
            ) : (
              <>
                <p className="auth-error-message">{generalError}</p>
                <button type="button" className="auth-action-button" onClick={() => { setVerificationStatus('idle'); clearErrors(); }}>Back to sign in</button>
              </>
            )}
          </section>
        ) : pendingVerificationEmail ? (
          <section className="auth-status-panel" aria-live="polite">
            <h2>Check your email</h2>
            <p>We sent a verification link to <strong>{pendingVerificationEmail}</strong>. Your account is not ready to sign in until you verify this address.</p>
            {generalError && <p className="auth-error-message">{generalError}</p>}
            {success && <p className="auth-success-message">{success}</p>}
            <div className="auth-inline-row">
              <button type="button" className="auth-action-button" onClick={handleResendVerification} disabled={resendingVerification}>
                {resendingVerification ? 'Sending…' : 'Resend verification email'}
              </button>
              <button type="button" className="auth-action-button" onClick={() => { setPendingVerificationEmail(''); clearErrors(); }}>Back to sign in</button>
            </div>
          </section>
        ) : isResettingPassword ? (
          <>
            <div className="header">
              <div>
                <h1>Expense Tracker</h1>
                <h2>{resetStep === 'request' ? 'Reset Password' : 'Set New Password'}</h2>
                <p className="subtitle-text">
                  {resetStep === 'request'
                    ? 'Enter your email to receive a password reset link.'
                    : 'Enter your new password to complete the reset.'}
                </p>
              </div>
            </div>

            <form className="auth-form" onSubmit={resetStep === 'request' ? handlePasswordReset : handlePasswordResetConfirm}>
              {resetStep === 'request' ? (
                <>
                  <div className="form-group">
                    <label htmlFor="resetEmail">Email</label>
                    <input
                      id="resetEmail"
                      type="email"
                      value={resetEmail}
                      onChange={(event) => setResetEmail(event.target.value)}
                      placeholder="Your email address"
                      className={fieldErrors.resetEmail ? 'input-error' : ''}
                    />
                    {fieldErrors.resetEmail && (
                      <span className="small-text" style={{ color: '#dc2626', display: 'block', marginTop: '0.25rem' }}>
                        {formatFieldError(fieldErrors.resetEmail)}
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="form-group">
                    <label htmlFor="resetPassword">New Password</label>
                    <input
                      id="resetPassword"
                      type="password"
                      value={resetPassword}
                      onChange={(event) => setResetPassword(event.target.value)}
                      placeholder="New password"
                      className={fieldErrors.resetPassword ? 'input-error' : ''}
                    />
                    {fieldErrors.resetPassword && (
                      <span className="small-text" style={{ color: '#dc2626', display: 'block', marginTop: '0.25rem' }}>
                        {formatFieldError(fieldErrors.resetPassword)}
                      </span>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="resetConfirmPassword">Confirm Password</label>
                    <input
                      id="resetConfirmPassword"
                      type="password"
                      value={resetConfirmPassword}
                      onChange={(event) => setResetConfirmPassword(event.target.value)}
                      placeholder="Confirm password"
                      className={fieldErrors.resetConfirmPassword ? 'input-error' : ''}
                    />
                    {fieldErrors.resetConfirmPassword && (
                      <span className="small-text" style={{ color: '#dc2626', display: 'block', marginTop: '0.25rem' }}>
                        {formatFieldError(fieldErrors.resetConfirmPassword)}
                      </span>
                    )}
                  </div>
                </>
              )}

              {generalError && <p className="auth-error-message" role="alert">{generalError}</p>}
              {success && <p className="auth-success-message" role="status">{success}</p>}

              <button className="auth-submit" type="submit">
                {resetStep === 'request' ? 'Send Reset Link' : 'Reset Password'}
              </button>
            </form>

            <div className="footer">
              <p className="small-text">
                <button
                  type="button"
                  className="auth-action-button"
                  onClick={() => {
                    setIsResettingPassword(false);
                    setResetStep('request');
                    clearErrors();
                  }}
                >
                  Back to Login
                </button>
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="header">
              <div>
                <h1>Expense Tracker</h1>
                <h2>{isRegistering ? 'Register' : 'Sign in'}</h2>
                <p className="subtitle-text">
                  {isRegistering
                    ? 'Use a username for registration and provide a valid email for verification.'
                    : 'Enter your username or verified email and password to continue.'}
                </p>
              </div>
            </div>

            <form id="login-form" className="auth-form" noValidate onSubmit={handleSubmit}>
              {/* USERNAME / IDENTIFIER FIELD */}
              <div className="form-group">
                <label htmlFor="identifier">
                  {isRegistering ? 'Username' : 'Username or email'}
                </label>
                <input
                  id="identifier"
                  type="text"
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                  placeholder={isRegistering ? 'Username' : 'Username or email'}
                  className={fieldErrors.username ? 'input-error' : ''}
                />
                {fieldErrors.username && (
                  <span className="small-text" style={{ color: '#dc2626', display: 'block', marginTop: '0.25rem' }}>
                    {formatFieldError(fieldErrors.username)}
                  </span>
                )}
              </div>

              {/* EMAIL FIELD (REGISTERING ONLY) */}
              {isRegistering && (
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="Email address"
                    className={fieldErrors.email ? 'input-error' : ''}
                  />
                  {fieldErrors.email && (
                    <span className="small-text" style={{ color: '#dc2626', display: 'block', marginTop: '0.25rem' }}>
                      {formatFieldError(fieldErrors.email)}
                    </span>
                  )}
                </div>
              )}

              {/* PASSWORD FIELD */}
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Password"
                  className={fieldErrors.password1 || fieldErrors.password ? 'input-error' : ''}
                />
                {(fieldErrors.password1 || fieldErrors.password) && (
                  <span className="small-text" style={{ color: '#dc2626', display: 'block', marginTop: '0.25rem' }}>
                    {formatFieldError(fieldErrors.password1 || fieldErrors.password)}
                  </span>
                )}
              </div>

              {/* CONFIRM PASSWORD FIELD (REGISTERING ONLY) */}
              {isRegistering && (
                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirm Password</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    placeholder="Confirm password"
                    className={fieldErrors.password2 ? 'input-error' : ''}
                  />
                  {fieldErrors.password2 && (
                    <span className="small-text" style={{ color: '#dc2626', display: 'block', marginTop: '0.25rem' }}>
                      {formatFieldError(fieldErrors.password2)}
                    </span>
                  )}
                </div>
              )}

              {/* GENERAL MESSAGES */}
              {generalError && <p className="small-text" style={{ color: '#dc2626' }}>{generalError}</p>}
              {success && <p className="small-text" style={{ color: '#16a34a' }}>{success}</p>}

              {isRegistering ? (
                <button className="auth-submit" type="submit">Create Account</button>
              ) : (
                <button className="auth-submit" type="submit">Login</button>
              )}
            </form>

            <div className="footer auth-actions">
              {isRegistering ? (
                <p className="small-text">
                  Already have an account?{' '}
                  <button
                    type="button"
                    className="auth-action-button"
                    onClick={() => {
                      setIsRegistering(false);
                      clearErrors();
                    }}
                  >
                    Login
                  </button>
                </p>
              ) : (
                <div className="auth-link-stack">
                  <div className="auth-inline-row">
                    <button
                      type="button"
                      className="auth-action-button"
                      onClick={() => {
                        setIsRegistering(true);
                        clearErrors();
                      }}
                    >
                      Sign up
                    </button>

                    <button
                      type="button"
                      className="auth-action-button"
                      onClick={() => {
                        setIsResettingPassword(true);
                        clearErrors();
                      }}
                    >
                      Forgot password?
                    </button>
                  </div>
                </div>
              )}
              <div className="social-auth-actions">
                <p>Or continue with</p>
                <div className="social-auth-row">
                  <button
                    type="button"
                    className="auth-action-button social-auth-button"
                    aria-label="Continue with Google"
                    title="Continue with Google"
                    onClick={() => handleSocialLogin('google')}
                  >
                    <i className="fa-brands fa-google" aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    className="auth-action-button social-auth-button"
                    aria-label="Continue with Apple"
                    title="Continue with Apple"
                    onClick={() => handleSocialLogin('apple')}
                  >
                    <i className="fa-brands fa-apple" aria-hidden="true" />
                  </button>
                </div>
                {(!authOptions.providers?.google?.configured || !authOptions.providers?.apple?.configured) && (
                  authOptionsStatus === 'ready' && (
                    <small>Google and Apple authentication require provider credentials to be configured.</small>
                  )
                )}
                {authOptionsStatus === 'error' && (
                  <small role="status">Social sign-in availability could not be checked.</small>
                )}
              </div>
            </div>

            {onNavigate && (
              <button type="button" className="auth-support-link" onClick={() => onNavigate('support')}>
                Need help? Help &amp; Support
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Login;