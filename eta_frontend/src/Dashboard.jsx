import React, { useMemo, useState } from 'react';
import { createClient } from './api';
import { useDashboardData } from './hooks/useDashboardData';
import { useOfflineSync } from './hooks/useOfflineSync';

import { Header } from './components/Header';
import { SummaryGrid } from './components/SummaryGrid';
import { CategorySummary } from './components/CategorySummary';

export default function Dashboard({ token, onLogout, theme, setTheme, onNavigate, onDeleteAccount, username, profilePicture }) {
  const [displayCurrency, setDisplayCurrency] = useState('EUR');
  const [summaryOpen, setSummaryOpen] = useState(false);

  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const { queuedCount, isSyncing } = useOfflineSync(client);

  const selectedCurrency = dashboard.currencies.find((currency) => currency.code === displayCurrency);

  return (
    <div className="container">
      <Header activePage="dashboard" onNavigate={onNavigate} onLogout={onLogout} onDeleteAccount={onDeleteAccount} theme={theme} setTheme={setTheme} username={username} profilePicture={profilePicture} queuedCount={queuedCount} isSyncing={isSyncing} />
      {dashboard.error && <div className="alert alert-danger">{dashboard.error}</div>}
      {queuedCount > 0 && (
        <div className="alert alert-warning alert-dismissible fade show" role="alert">
          <strong>⟳ Sync Pending</strong> — {queuedCount} expense(s) saved locally {isSyncing ? 'and now syncing...' : 'and waiting to sync when you reconnect.'}.
        </div>
      )}

      <button type="button" className="summary-menu-button" aria-label="Open summary menu" onClick={() => setSummaryOpen(true)}>☰ <span>Summary</span></button>
      <div className={summaryOpen ? 'dashboard-layout summary-is-open' : 'dashboard-layout'}>
        <aside className="summary-sidebar" aria-label="Summary navigation">
          <div className="card currency-card">
            <h2>Currency</h2>
            <select className="form-control" value={displayCurrency} onChange={(e) => setDisplayCurrency(e.target.value)}>
              {dashboard.currencies.map((c) => (
                <option key={c.code} value={c.code}>{c.symbol} {c.code}</option>
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
        <main className="dashboard-main">
        <CategorySummary
          categories={dashboard.categorySummary.categories}
          year={dashboard.categorySummary.year}
          symbol={selectedCurrency?.symbol || '€'}
        />
        </main>
      </div>
      {summaryOpen && <button type="button" className="sidebar-backdrop" aria-label="Close summary menu" onClick={() => setSummaryOpen(false)} />}
    </div>
  );
}