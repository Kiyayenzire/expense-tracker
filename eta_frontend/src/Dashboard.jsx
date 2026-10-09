import React from 'react';
import { CategorySummary } from './components/CategorySummary';

export default function Dashboard({ dashboard, queuedCount, isSyncing, symbol }) {
  return (
    <>
      {dashboard.error && <p className="dashboard-error-message" role="alert"><strong>{dashboard.error}</strong></p>}
      {queuedCount > 0 && (
        <div className="alert alert-warning alert-dismissible fade show" role="alert">
          <strong>⟳ Sync Pending</strong> — {queuedCount} expense(s) saved locally {isSyncing ? 'and now syncing...' : 'and waiting to sync when you reconnect.'}.
        </div>
      )}
      <section className="dashboard-main-content">
        <CategorySummary
          categories={dashboard.categorySummary.categories}
          year={dashboard.categorySummary.year}
          symbol={symbol}
          expenses={dashboard.expenses}
        />
      </section>
    </>
  );
}