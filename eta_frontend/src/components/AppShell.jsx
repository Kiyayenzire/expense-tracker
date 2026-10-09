import React, { useEffect, useMemo, useState } from 'react';
import { createClient } from '../api';
import { useDashboardData } from '../hooks/useDashboardData';
import { useOfflineSync } from '../hooks/useOfflineSync';
import { Header } from './Header';
import { SummaryGrid } from './SummaryGrid';

export function AppShell({ token, onLogout, theme, setTheme, onNavigate, onDeleteAccount, activePage, username, profilePicture, currentUser, verificationNotice, children, displayCurrency, setDisplayCurrency }) {
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [verificationMessage, setVerificationMessage] = useState('');
  const [isResendingVerification, setIsResendingVerification] = useState(false);
  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const { queuedCount, isSyncing } = useOfflineSync(client);
  const selectedCurrency = dashboard.currencies.find((currency) => currency.code === displayCurrency);

  const resendVerification = async () => {
    setIsResendingVerification(true);
    setVerificationMessage('');
    try {
      await client.post('/auth/registration/resend-email/', { email: currentUser.email });
      setVerificationMessage('If your email address is still unverified, a verification link has been sent.');
    } catch (error) {
      setVerificationMessage(error.response?.data?.detail || 'We could not send a verification link. Please try again shortly.');
    } finally {
      setIsResendingVerification(false);
    }
  };

  useEffect(() => {
    if (!summaryOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setSummaryOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [summaryOpen]);

  return (
    <div
      className={[
        'container',
        'app-shell',
        activePage === 'dashboard' ? 'dashboard-shell' : '',
        summaryOpen ? 'summary-drawer-open' : '',
      ].filter(Boolean).join(' ')}
    >
      <Header activePage={activePage} onNavigate={onNavigate} onLogout={onLogout} onDeleteAccount={onDeleteAccount} theme={theme} setTheme={setTheme} username={username} profilePicture={profilePicture} queuedCount={queuedCount} isSyncing={isSyncing} />
      {verificationNotice && <p className="verification-result" role="status">{verificationNotice}</p>}
      {currentUser?.email && currentUser.email_verified === false && (
        <section className="warning-banner email-verification-banner" role="status">
          <div>
            <strong>Your email address is not verified.</strong>
            <p>Verify your email to keep full access to your account.</p>
            {verificationMessage && <p className="verification-feedback">{verificationMessage}</p>}
          </div>
          <button
            type="button"
            className="secondary-action-button"
            onClick={resendVerification}
            disabled={isResendingVerification}
          >
            {isResendingVerification ? 'Sending…' : 'Resend verification email'}
          </button>
        </section>
      )}
      <div className="summary-menu-row">
        <button type="button" className="summary-menu-button" aria-label="Open summary navigation" aria-controls="summary-sidebar" aria-expanded={summaryOpen} onClick={() => setSummaryOpen((open) => !open)}>☰ <span>Summary</span></button>
      </div>
      <div className="dashboard-layout">
        <aside id="summary-sidebar" className="summary-sidebar" aria-label="Summary navigation" aria-hidden={!summaryOpen}>
          <div className="card currency-card">
            <h2>Currency</h2>
            <select id="app-currency" className="form-control currency-select" aria-label="Display currency" value={displayCurrency} onChange={(event) => setDisplayCurrency(event.target.value)}>
              {dashboard.currencies.map((currency) => (
                <option key={currency.code} value={currency.code}>{currency.symbol} {currency.code}</option>
              ))}
            </select>
            {selectedCurrency && <p className="small-text currency-note">{selectedCurrency.name} ({selectedCurrency.symbol})</p>}
          </div>
          <div className="sidebar-heading">
            <h2>Summary</h2>
            <button type="button" className="sidebar-close" aria-label="Close summary navigation" onClick={() => setSummaryOpen(false)}>×</button>
          </div>
          <SummaryGrid onNavigate={(page) => { setSummaryOpen(false); onNavigate(page); }} />
        </aside>
        <div className="dashboard-main app-page-main">
          {typeof children === 'function' ? children({ dashboard, queuedCount, isSyncing }) : children}
        </div>
      </div>
    </div>
  );
}
