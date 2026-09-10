import React, { useMemo, useState } from 'react';
import { createClient } from './api';
import { useDashboardData } from './hooks/useDashboardData';
import { useOfflineSync } from './hooks/useOfflineSync';
import { ExpenseForm } from './components/ExpenseForm';
import { QuickExpenseEntry } from './components/QuickExpenseEntry';

export default function AddExpensePage({ token, onLogout, onNavigate }) {
  const client = useMemo(() => createClient(token), [token]);
  const [feedback, setFeedback] = useState('');
  const [quickDraft, setQuickDraft] = useState(null);
  const dashboard = useDashboardData(client, 'EUR', onLogout);
  const { queuedCount, isSyncing } = useOfflineSync(client);

  const handleSuccess = async (message) => {
    setFeedback(message);
    if (dashboard?.refetch) {
      await dashboard.refetch();
    }
    window.setTimeout(() => onNavigate('dashboard'), 700);
  };

  return (
    <div className="page-content">
        <div className="page-heading">
          <h2>Add Expense</h2>
          <p className="small-text">Record a new expense for your account.</p>
        </div>
        {dashboard.error && <div className="alert alert-danger">{dashboard.error}</div>}
        {feedback && <div className="alert alert-success">{feedback}</div>}
        <QuickExpenseEntry client={client} onParsed={setQuickDraft} />
        <ExpenseForm
          categories={dashboard.categories}
          subcategories={dashboard.subcategories}
          items={dashboard.items}
          currencies={dashboard.currencies}
          client={client}
          onSuccess={handleSuccess}
          onError={setFeedback}
          quickDraft={quickDraft}
        />
    </div>
  );
}
