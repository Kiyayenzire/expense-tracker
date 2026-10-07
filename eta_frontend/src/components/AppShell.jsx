import React, { useEffect, useMemo, useState } from 'react';
import { createClient } from '../api';
import { useDashboardData } from '../hooks/useDashboardData';
import { Header } from './Header';
import { SummaryGrid } from './SummaryGrid';

export function AppShell({ token, onLogout, theme, setTheme, onNavigate, username, profilePicture, children, displayCurrency, setDisplayCurrency }) {
  const [summaryOpen, setSummaryOpen] = useState(false);
  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const selectedCurrency = dashboard.currencies.find((currency) => currency.code === displayCurrency);

  useEffect(() => {
    if (!summaryOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setSummaryOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [summaryOpen]);

  return (
    <div className={summaryOpen ? 'container app-shell summary-drawer-open' : 'container app-shell'}>
      <Header activePage="summary" onNavigate={onNavigate} onLogout={onLogout} theme={theme} setTheme={setTheme} username={username} profilePicture={profilePicture} />
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
        <main className="dashboard-main app-page-main">
          {children}
        </main>
      </div>
      {summaryOpen && <button type="button" className="sidebar-backdrop" aria-label="Close summary navigation" onClick={() => setSummaryOpen(false)} />}
    </div>
  );
}
