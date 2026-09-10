import React, { useMemo } from 'react';
import { createClient } from './api';
import { useDashboardData } from './hooks/useDashboardData';
import { SpendingChart } from './components/SpendingChart';

export default function SpendingTrendsPage({ token, onLogout, displayCurrency }) {
  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const symbol = dashboard.currencies.find((currency) => currency.code === displayCurrency)?.symbol || displayCurrency;
  return <div className="page-content wide-content"><div className="page-heading"><h2>Spending Trends</h2><p className="small-text">Review spending by category.</p></div><SpendingChart chartData={dashboard.chart} symbol={symbol} /></div>;
}