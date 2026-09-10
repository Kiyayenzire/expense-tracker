import React, { useMemo } from 'react';
import { createClient } from './api';
import { useDashboardData } from './hooks/useDashboardData';
import { InsightsSection } from './components/InsightsSection';

const CURRENCY_SYMBOLS = { EUR: '€', USD: '$', UGX: 'USh' };

export default function InsightsPage({ token, onLogout, displayCurrency = 'EUR' }) {
  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const symbol = CURRENCY_SYMBOLS[displayCurrency] || displayCurrency;

  return (
    <div className="page-content">
        <div className="page-heading">
          <h2>Insights</h2>
          <p className="small-text">Review forecasts and unusual spending activity.</p>
        </div>
        {dashboard.error && <div className="alert alert-danger">{dashboard.error}</div>}
        <InsightsSection prediction={dashboard.prediction} insights={dashboard.insights} symbol={symbol} />
    </div>
  );
}
