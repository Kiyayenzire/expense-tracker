import React from 'react';

export function SummaryGrid({ onNavigate }) {
  const metrics = [
    { label: 'Daily', page: 'daily' },
    { label: 'Weekly', page: 'weekly' },
    { label: 'Monthly', page: 'monthly' },
    { label: 'Quarterly', page: 'quarterly' },
    { label: 'Annual', page: 'annual' },
    { label: 'Spending Trends', page: 'spending-trends' },
  ];

  return (
    <div className="summary-card">
      <div className="summary-grid">
        {metrics.map(({ label, page }) => (
          <button key={page} type="button" className="summary-link" onClick={() => onNavigate(page)}>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}