import React, { useMemo, useState } from 'react';
import { createClient } from '../api';
import { useDashboardData } from '../hooks/useDashboardData';
import { Header } from './Header';
import { SummaryGrid } from './SummaryGrid';

export function AppShell({ token, onLogout, theme, setTheme, onNavigate, username, profilePicture, children, displayCurrency, setDisplayCurrency }) {
  const [summaryOpen, setSummaryOpen] = useState(false);
  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const selectedCurrency = dashboard.currencies.find((currency) => currency.code === displayCurrency);

  return (
    <div className="container app-shell">
      <Header activePage="summary" onNavigate={onNavigate} onLogout={onLogout} theme={theme} setTheme={setTheme} username={username} profilePicture={profilePicture} />
      <button type="button" className="summary-menu-button" aria-label="Open summary menu" onClick={() => setSummaryOpen(true)}>☰ <span>Summary</span></button>
      <div className={summaryOpen ? 'dashboard-layout summary-is-open' : 'dashboard-layout'}>
        <aside className="summary-sidebar" aria-label="Summary navigation">
          <div className="card currency-card">
            <h2>Currency</h2>
            <select className="form-control" value={displayCurrency} onChange={(event) => setDisplayCurrency(event.target.value)}>
              {dashboard.currencies.map((currency) => (
                <option key={currency.code} value={currency.code}>{currency.symbol} {currency.code}</option>
              ))}
            </select>
            {selectedCurrency && <p className="small-text currency-note">{selectedCurrency.name} ({selectedCurrency.symbol})</p>}
          </div>
          <div className="sidebar-heading">
            <h2>Summary</h2>
            <button type="button" className="sidebar-close" aria-label="Close summary menu" onClick={() => setSummaryOpen(false)}>×</button>
          </div>
          <SummaryGrid onNavigate={(page) => { setSummaryOpen(false); onNavigate(page); }} />
        </aside>
        <main className="dashboard-main app-page-main">
          {children}
        </main>
      </div>
      {summaryOpen && <button type="button" className="sidebar-backdrop" aria-label="Close summary menu" onClick={() => setSummaryOpen(false)} />}
    </div>
  );
}
