import React, { useState } from 'react';

export function QuickExpenseEntry({ client, onParsed }) {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const parse = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await client.post('/expenses/parse-quick-entry/', { text });
      setResult(response.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to understand this expense.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card quick-expense-entry">
      <h2>Quick Expense Entry</h2>
      <p className="small-text">Describe the expense, review the interpretation, then edit or confirm it in the normal form.</p>
      <form onSubmit={parse} className="quick-expense-form">
        <input aria-label="Quick expense description" value={text} onChange={(event) => setText(event.target.value)} placeholder="I spent 35k at Java House for lunch yesterday" />
        <button type="submit" disabled={loading || !text.trim()}>{loading ? 'Parsing...' : 'Parse Expense'}</button>
      </form>
      {error && <p className="alert alert-danger">{error}</p>}
      {result && !result.errors?.length && (
        <div className="quick-expense-preview">
          <strong>Review Expense</strong>
          <span>{result.amount} {result.currency} on {result.date}</span>
          <span>{result.description}</span>
          <span>{result.category_name || 'Category needs selection'}{result.subcategory_name ? ` / ${result.subcategory_name}` : ''}</span>
          <button type="button" onClick={() => onParsed(result)}>Use In Expense Form</button>
        </div>
      )}
    </section>
  );
}
