import { useEffect, useMemo, useState } from 'react';
import { createClient, formatDateEU } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';

const defaultExpense = {
  date: new Date().toISOString().slice(0, 10),
  category: '',
  item: '',
  quantity: '1',
  supplier: '',
  country: '',
  amount: '0.00',
  currency: '',
  notes: '',
};

const currencySymbols = {
  EUR: '€',
  USD: '$',
  UGX: 'USh',
};

function Dashboard({ token, onLogout, theme, setTheme }) {
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState({});
  const [chart, setChart] = useState({ expensive: [], least: [] });
  const [prediction, setPrediction] = useState({});
  const [insights, setInsights] = useState({ anomalies: [] });
  const [displayCurrency, setDisplayCurrency] = useState('EUR');
  const [convertedExpenses, setConvertedExpenses] = useState([]);
  const [expenseForm, setExpenseForm] = useState(defaultExpense);
  const [reportType, setReportType] = useState('monthly');
  const [reportYear, setReportYear] = useState(new Date().getFullYear());
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);
  const [reportStartYear, setReportStartYear] = useState(new Date().getFullYear() - 1);
  const [reportEndYear, setReportEndYear] = useState(new Date().getFullYear());
  const [reportFormat, setReportFormat] = useState('csv');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const client = useMemo(() => createClient(token), [token]);

  useEffect(() => {
    fetchData();
  }, [displayCurrency]);

  useEffect(() => {
    if (expenses.length && displayCurrency) {
      convertExpenses();
    }
  }, [expenses, displayCurrency]);

  useEffect(() => {
    if (currencies.length && !expenseForm.currency) {
      const eurCurrency = currencies.find((currency) => currency.code === 'EUR');
      setExpenseForm((current) => ({
        ...current,
        currency: eurCurrency ? eurCurrency.id : currencies[0].id,
      }));
    }
  }, [currencies, expenseForm.currency]);

  async function fetchData() {
    try {
      const [categoryRes, itemRes, currencyRes, expenseRes, summaryRes, chartRes, predictionRes, insightsRes] = await Promise.all([
        client.get('/categories/'),
        client.get('/items/'),
        client.get('/currencies/'),
        client.get('/expenses/'),
        client.get('/expenses/summary/', { params: { target_currency: displayCurrency } }),
        client.get('/expenses/chart/'),
        client.get('/expenses/prediction/'),
        client.get('/expenses/insights/'),
      ]);

      setCategories(categoryRes.data || []);
      setItems(itemRes.data || []);
      setCurrencies(currencyRes.data || []);
      setExpenses(expenseRes.data || []);
      setSummary(summaryRes.data || {});
      setChart(chartRes.data || { expensive: [], least: [] });
      setPrediction(predictionRes.data || {});
      setInsights(insightsRes.data || { anomalies: [] });
    } catch (err) {
      setError('Unable to load dashboard data.');
    }
  }

  function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  async function handleExport(format) {
    setError('');
    setSuccess('');
    try {
      const endpoint = `/export-report/?format=${format}`;
      const payload = {
        period: reportType,
        year: reportYear,
        month: reportMonth,
        start_year: reportStartYear,
        end_year: reportEndYear,
        target_currency: displayCurrency,
      };
      const response = await client.post(endpoint, payload, {
        responseType: 'blob',
      });

      const contentType = response.headers['content-type'];
      const extension = format === 'pdf' ? 'pdf' : 'csv';
      const filename = `expense_report_${reportType}_${reportYear}${reportType === 'monthly' ? `_${reportMonth.toString().padStart(2, '0')}` : ''}.${extension}`;
      downloadFile(new Blob([response.data], { type: contentType }), filename);
      setSuccess(`Report exported as ${filename}`);
    } catch (err) {
      setError('Unable to export report. Please try again.');
    }
  }

  async function convertExpenses() {
    const conversions = await Promise.all(
      expenses.map(async (entry) => {
        if (!entry.amount || entry.currency_code === displayCurrency) {
          return { ...entry, converted_amount: entry.amount };
        }
        try {
          const response = await client.get('/convert-currency/', {
            params: {
              base: entry.currency_code,
              target: displayCurrency,
              amount: entry.amount,
            },
          });
          return { ...entry, converted_amount: response.data.converted || entry.amount };
        } catch (err) {
          return { ...entry, converted_amount: entry.amount };
        }
      })
    );

    setConvertedExpenses(conversions);
  }

  async function handleFormChange(field, value) {
    setExpenseForm((current) => ({ ...current, [field]: value }));
  }

  async function handleAddExpense(event) {
    event.preventDefault();
    setError('');
    setSuccess('');

    const payload = {
      ...expenseForm,
      user_local_time: new Date().toISOString(),
      user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    };

    try {
      const response = await client.post('/expenses/', payload);
      setSuccess('Expense recorded successfully.');
      setExpenseForm({ ...defaultExpense, currency: expenseForm.currency, category: expenseForm.category, item: expenseForm.item });
      setExpenses((current) => [response.data, ...current]);
      setSummary((current) => ({ ...current }));
      fetchData();
    } catch (err) {
      setError('Unable to save expense. Please check the form and try again.');
    }
  }

  const displaySymbol = currencySymbols[displayCurrency] || displayCurrency;

  return (
    <div className="container">
      <div className="header">
        <div>
          <h1>Expense Tracker Dashboard</h1>
          <p className="small-text">Today is {formatDateEU(new Date().toISOString())}.</p>
        </div>
        <div className="theme-toggle">
          <button type="button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
            Switch to {theme === 'light' ? 'dark' : 'light'} mode
          </button>
          <button type="button" onClick={onLogout} className="logout-button">
            Logout
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="grid-two">
        <div className="card summary-card">
          <h2>Monthly summary</h2>
          <div className="summary-grid">
            <div>
              <strong>Daily</strong>
              <p>{displaySymbol} {(summary.daily || 0).toFixed(2)}</p>
            </div>
            <div>
              <strong>Weekly</strong>
              <p>{displaySymbol} {(summary.weekly || 0).toFixed(2)}</p>
            </div>
            <div>
              <strong>Monthly</strong>
              <p>{displaySymbol} {(summary.monthly || 0).toFixed(2)}</p>
            </div>
            <div>
              <strong>Quarterly</strong>
              <p>{displaySymbol} {(summary.quarterly || 0).toFixed(2)}</p>
            </div>
            <div>
              <strong>Annual</strong>
              <p>{displaySymbol} {(summary.annual || 0).toFixed(2)}</p>
            </div>
          </div>
        </div>

        <div className="card currency-card">
          <h2>Display currency</h2>
          <select
            className="form-control"
            value={displayCurrency}
            onChange={(e) => setDisplayCurrency(e.target.value)}
          >
            {currencies.map((currency) => (
              <option key={currency.code} value={currency.code}>
                {currency.code} - {currency.name}
              </option>
            ))}
          </select>
          <div className="insight-box">
            <p>Current report currency: {displayCurrency}</p>
            <p>{Object.entries(prediction).length > 0 ? 'Predicted next month spend available.' : 'Predictions loading...'}</p>
          </div>
        </div>
      </div>

      <div className="grid-two">
        <div className="card">
          <h2>Add new expense</h2>
          <form onSubmit={handleAddExpense}>
            <div className="form-group">
              <label>Date</label>
              <input
                type="date"
                className="form-control"
                value={expenseForm.date}
                onChange={(e) => handleFormChange('date', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Category</label>
              <select
                className="form-control"
                value={expenseForm.category}
                onChange={(e) => handleFormChange('category', e.target.value)}
                required
              >
                <option value="">Select category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Item</label>
              <select
                className="form-control"
                value={expenseForm.item}
                onChange={(e) => handleFormChange('item', e.target.value)}
                required
              >
                <option value="">Select item</option>
                {items.map((item) => (
                  <option key={item.id} value={item.id}>{item.description}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Amount</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                value={expenseForm.amount}
                onChange={(e) => handleFormChange('amount', e.target.value)}
                required
              />
            </div>
            <div className="grid-two gap-small">
              <div className="form-group">
                <label>Quantity</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  value={expenseForm.quantity}
                  onChange={(e) => handleFormChange('quantity', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Currency</label>
                <select
                  className="form-control"
                  value={expenseForm.currency}
                  onChange={(e) => handleFormChange('currency', e.target.value)}
                >
                  {currencies.map((currency) => (
                    <option key={currency.code} value={currency.id}>{currency.code}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Supplier / Provider</label>
              <input
                className="form-control"
                value={expenseForm.supplier}
                onChange={(e) => handleFormChange('supplier', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Country</label>
              <input
                className="form-control"
                value={expenseForm.country}
                onChange={(e) => handleFormChange('country', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Notes</label>
              <textarea
                className="form-control"
                value={expenseForm.notes}
                onChange={(e) => handleFormChange('notes', e.target.value)}
              />
            </div>
            <button className="btn btn-primary w-100" type="submit">Save expense</button>
          </form>
        </div>

        <div className="card chart-card">
          <h2>Spending trends</h2>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={chart.expensive.map((item) => ({ name: item.category__name || item.category, total: item.total }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => `${displaySymbol} ${value}`} />
                <Bar dataKey="total" fill="#2563EB" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="insight-box">
            <strong>Least expensive sections</strong>
            <ul>
              {chart.least.map((item) => (
                <li key={item.category__name || item.category}>{item.category__name || item.category}: {displaySymbol} {(item.total || 0).toFixed(2)}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="grid-two">
        <div className="card">
          <h2>Export report</h2>
          <div className="form-group">
            <label>Report type</label>
            <select className="form-control" value={reportType} onChange={(e) => setReportType(e.target.value)}>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
          <div className="grid-two gap-small">
            <div className="form-group">
              <label>Year</label>
              <input
                type="number"
                className="form-control"
                value={reportYear}
                onChange={(e) => setReportYear(Number(e.target.value))}
                min="2000"
                max="2100"
                disabled={reportType === 'range'}
              />
            </div>
            {reportType === 'monthly' && (
              <div className="form-group">
                <label>Month</label>
                <input
                  type="number"
                  className="form-control"
                  value={reportMonth}
                  onChange={(e) => setReportMonth(Number(e.target.value))}
                  min="1"
                  max="12"
                />
              </div>
            )}
            {reportType === 'range' && (
              <>
                <div className="form-group">
                  <label>Start Year</label>
                  <input
                    type="number"
                    className="form-control"
                    value={reportStartYear}
                    onChange={(e) => setReportStartYear(Number(e.target.value))}
                    min="2000"
                    max="2100"
                  />
                </div>
                <div className="form-group">
                  <label>End Year</label>
                  <input
                    type="number"
                    className="form-control"
                    value={reportEndYear}
                    onChange={(e) => setReportEndYear(Number(e.target.value))}
                    min="2000"
                    max="2100"
                  />
                </div>
              </>
            )}
          </div>
          <div className="form-group">
            <label>Format</label>
            <select className="form-control" value={reportFormat} onChange={(e) => setReportFormat(e.target.value)}>
              <option value="csv">CSV</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
          <button className="btn btn-secondary w-100" type="button" onClick={() => handleExport(reportFormat)}>
            Export report
          </button>
          <p className="small-text">Exports can be generated by month or year in the selected display currency.</p>
        </div>

        <div className="card">
        <div className="card">
          <h2>Prediction for next month</h2>
          {Object.keys(prediction).length ? (
            <ul className="prediction-list">
              {Object.entries(prediction).map(([category, amount]) => (
                <li key={category}>{category}: {displaySymbol} {amount.toFixed ? amount.toFixed(2) : amount}</li>
              ))}
            </ul>
          ) : (
            <p>No prediction data available yet.</p>
          )}
        </div>
        <div className="card">
          <h2>Anomaly insights</h2>
          {insights.anomalies.length ? (
            <ul className="prediction-list">
              {insights.anomalies.slice(0, 5).map((anomaly, index) => (
                <li key={index}>{anomaly.category__name || 'Expense'} - {displaySymbol} {(anomaly.amount || 0).toFixed(2)} on {formatDateEU(anomaly.date)}</li>
              ))}
            </ul>
          ) : (
            <p>No anomalies detected.</p>
          )}
        </div>
      </div>

      <div className="card">
        <div className="header">
          <div>
            <h2>Recent expenses</h2>
            <p className="small-text">Showing most recent entries with selected display currency.</p>
          </div>
        </div>
        <div className="table-responsive">
          <table className="table table-striped">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Item</th>
                <th>Amount</th>
                <th>Converted</th>
                <th>Supplier</th>
                <th>Country</th>
              </tr>
            </thead>
            <tbody>
              {convertedExpenses.map((expense) => (
                <tr key={expense.id}>
                  <td>{formatDateEU(expense.date)}</td>
                  <td>{expense.category_name}</td>
                  <td>{expense.item_description}</td>
                  <td>{expense.currency_code} {Number(expense.amount).toFixed(2)}</td>
                  <td>{displayCurrency} {Number(expense.converted_amount || expense.amount).toFixed(2)}</td>
                  <td>{expense.supplier}</td>
                  <td>{expense.country}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
