import React, { useMemo, useState } from 'react';
import { createClient } from './api';
import { useDashboardData } from './hooks/useDashboardData';
import { ReportExporter } from './components/ReportExporter';

export default function ReportsPage({ token, onLogout, displayCurrency }) {
  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const [status, setStatus] = useState({ type: '', message: '' });

  return (
    <div className="page-content reports-page">
        <div className="page-heading reports-page-heading">
          <h2>Reports</h2>
          <p className="small-text">Export expense reports for a selected period.</p>
        </div>
        {dashboard.error && <div className="alert alert-danger">{dashboard.error}</div>}
        {status.message && <div className={status.type === 'error' ? 'alert alert-danger' : 'alert alert-success'}>{status.message}</div>}
        <ReportExporter
          client={client}
          displayCurrency={displayCurrency}
          onSuccess={(message) => setStatus({ type: 'success', message })}
          onError={(message) => setStatus({ type: 'error', message })}
        />
    </div>
  );
}
