import React, { useEffect, useMemo, useState } from 'react';
import { createClient } from './api';

const PERIOD_LABELS = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
  quarterly: 'Quarterly',
  annual: 'Annual',
};

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const CURRENCY_SYMBOLS = { EUR: '€', USD: '$', UGX: 'USh' };

function toInputDate(date) {
  return date.toISOString().slice(0, 10);
}

function formatEuropeanDate(value) {
  if (!value) return '';
  const [year, month, day] = value.split('-');
  return `${day}/${month}/${year}`;
}

function startOfWeek(date) {
  const result = new Date(date);
  const day = result.getDay() || 7;
  result.setDate(result.getDate() - day + 1);
  return result;
}

function endOfMonth(year, month) {
  return new Date(year, month + 1, 0);
}

export default function PeriodSummaryPage({ period, token, onLogout, displayCurrency }) {
  const today = useMemo(() => new Date(), []);
  const client = useMemo(() => createClient(token), [token]);
  const [selectedDate, setSelectedDate] = useState(toInputDate(today));
  const [startDate, setStartDate] = useState(toInputDate(startOfWeek(today)));
  const [endDate, setEndDate] = useState(toInputDate(new Date(startOfWeek(today).getTime() + 6 * 86400000)));
  const [month, setMonth] = useState(today.getMonth());
  const [year, setYear] = useState(today.getFullYear());
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [total, setTotal] = useState(0);
  const [expenses, setExpenses] = useState([]);
  const [rangeError, setRangeError] = useState('');

  const range = useMemo(() => {
    if (period === 'daily') return { start: selectedDate, end: selectedDate };
    if (period === 'weekly') return { start: startDate, end: endDate };
    if (period === 'monthly') return customStartDate && customEndDate
      ? { start: customStartDate, end: customEndDate }
      : { start: toInputDate(new Date(year, month, 1)), end: toInputDate(endOfMonth(year, month)) };
    if (period === 'quarterly') {
      const quarterStart = Math.floor(today.getMonth() / 3) * 3;
      return { start: toInputDate(new Date(year, quarterStart, 1)), end: toInputDate(endOfMonth(year, quarterStart + 2)) };
    }
    return customStartDate && customEndDate
      ? { start: customStartDate, end: customEndDate }
      : { start: toInputDate(new Date(year, 0, 1)), end: toInputDate(new Date(year, 11, 31)) };
  }, [period, selectedDate, startDate, endDate, month, year, customStartDate, customEndDate, today]);

  useEffect(() => {
    if (!range.start || !range.end) return;
    client.get('/expenses/summary-range/', {
      params: { start_date: range.start, end_date: range.end, target_currency: displayCurrency },
    }).then((response) => {
      setTotal(response.data.total || 0);
      setRangeError('');
    }).catch((error) => {
      setRangeError(error.response?.data?.detail || 'Unable to load this summary.');
    });
  }, [client, displayCurrency, range]);

  useEffect(() => {
    client.get('/expenses/').then((response) => {
      const entries = Array.isArray(response.data) ? response.data : response.data.results || [];
      const inRange = entries.filter((entry) => {
        const [day, monthNumber, yearNumber] = String(entry.date || '').split('/').map(Number);
        const entryDate = yearNumber ? `${yearNumber}-${String(monthNumber).padStart(2, '0')}-${String(day).padStart(2, '0')}` : entry.date;
        return entryDate >= range.start && entryDate <= range.end;
      });
      setExpenses(inRange);
    }).catch(() => setExpenses([]));
  }, [client, range]);

  const symbol = CURRENCY_SYMBOLS[displayCurrency] || displayCurrency;
  const years = Array.from({ length: 11 }, (_, index) => today.getFullYear() - index);
  const label = PERIOD_LABELS[period];

  return (
    <div className="page-content">
        <div className="page-heading">
          <h2>{label} Summary</h2>
          <p className="small-text">Choose dates using the calendar or enter them as {formatEuropeanDate(range.start)}.</p>
        </div>

        <section className="card period-controls">
          {period === 'daily' && (
            <div className="form-group">
              <label htmlFor="summary-date">Day</label>
              <input id="summary-date" className="form-control" type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
            </div>
          )}

          {period === 'weekly' && (
            <div className="grid-two gap-small">
              <div className="form-group"><label htmlFor="week-start">Week starts Monday</label><input id="week-start" className="form-control" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></div>
              <div className="form-group"><label htmlFor="week-end">Week ends Sunday</label><input id="week-end" className="form-control" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></div>
            </div>
          )}

          {period === 'monthly' && (
            <div className="grid-two gap-small">
              <div className="form-group"><label htmlFor="summary-month">Month</label><select id="summary-month" className="form-control" value={month} onChange={(event) => setMonth(Number(event.target.value))}>{MONTHS.map((name, index) => <option key={name} value={index}>{name}</option>)}</select></div>
              <div className="form-group"><label htmlFor="summary-month-year">Year</label><select id="summary-month-year" className="form-control" value={year} onChange={(event) => setYear(Number(event.target.value))}>{years.map((item) => <option key={item} value={item}>{item}</option>)}</select></div>
              <div className="form-group"><label htmlFor="month-start">Or start date</label><input id="month-start" className="form-control" type="date" value={customStartDate} onChange={(event) => setCustomStartDate(event.target.value)} /></div>
              <div className="form-group"><label htmlFor="month-end">Or end date</label><input id="month-end" className="form-control" type="date" value={customEndDate} onChange={(event) => setCustomEndDate(event.target.value)} /></div>
            </div>
          )}

          {period === 'annual' && (
            <div className="grid-two gap-small">
              <div className="form-group"><label htmlFor="summary-year">Year</label><select id="summary-year" className="form-control" value={year} onChange={(event) => setYear(Number(event.target.value))}>{years.map((item) => <option key={item} value={item}>{item}</option>)}</select></div>
              <div className="form-group"><label htmlFor="annual-start">Or start date</label><input id="annual-start" className="form-control" type="date" value={customStartDate} onChange={(event) => setCustomStartDate(event.target.value)} /></div>
              <div className="form-group"><label htmlFor="annual-end">Or end date</label><input id="annual-end" className="form-control" type="date" value={customEndDate} onChange={(event) => setCustomEndDate(event.target.value)} /></div>
            </div>
          )}

          {period !== 'daily' && period !== 'quarterly' && (
            <p className="small-text date-range">Date range: {formatEuropeanDate(range.start)} to {formatEuropeanDate(range.end)}</p>
          )}
        </section>

        {rangeError && <div className="alert alert-danger">{rangeError}</div>}
        <section className="card period-summary-card">
          <span className="stat-label">{label}</span>
          <p className="period-total">{symbol} {Number(total).toFixed(2)}</p>
          <p className="small-text">{formatEuropeanDate(range.start)} to {formatEuropeanDate(range.end)}</p>
        </section>
        <section className="card period-expenses-card">
          <h2>Expenses In This Period</h2>
          {expenses.length === 0 ? <p className="small-text">No expenses recorded for this period.</p> : (
            <div className="table-responsive">
              <table className="table table-striped">
                <thead><tr><th>No</th><th>Description</th><th>Category</th><th>Subcategory</th><th>Amount</th><th>Quantity</th><th>Total Amount</th><th>Supplier</th><th>Country</th></tr></thead>
                <tbody>{expenses.map((expense, index) => <tr key={expense.id}><td>{index + 1}</td><td>{expense.item_description || '-'}</td><td>{expense.category_name || '-'}</td><td>{expense.subcategory_name || '-'}</td><td>{expense.currency_symbol || expense.currency_code} {Number(expense.amount || 0).toFixed(2)}</td><td>{Number(expense.quantity || 0).toFixed(2)}</td><td>{expense.currency_symbol || expense.currency_code} {(Number(expense.quantity || 0) * Number(expense.amount || 0)).toFixed(2)}</td><td>{expense.supplier || '-'}</td><td>{expense.country || '-'}</td></tr>)}</tbody>
              </table>
            </div>
          )}
        </section>
    </div>
  );
}
