import React, { useMemo, useState } from 'react';
import { createClient } from './api';
import { useDashboardData } from './hooks/useDashboardData';
import { SpendingChart } from './components/SpendingChart';
import { ExpenseTable } from './components/ExpenseTable';

export default function ExpensesPage({ token, onLogout, onNavigate, displayCurrency }) {
  const client = useMemo(() => createClient(token), [token]);
  const dashboard = useDashboardData(client, displayCurrency, onLogout);
  const [filters, setFilters] = useState({ date: '', category: '', subcategory: '', description: '', amount: '', supplier: '', country: '' });
  const symbol = dashboard.currencies.find((currency) => currency.code === displayCurrency)?.symbol || displayCurrency;
  const filteredExpenses = dashboard.convertedExpenses.filter((expense) => (
    (!filters.date || expense.date === filters.date || expense.date?.endsWith(filters.date.split('-').reverse().join('/')))
    && (!filters.category || String(expense.category) === filters.category)
    && (!filters.subcategory || String(expense.subcategory) === filters.subcategory)
    && (!filters.description || expense.item_description?.toLowerCase().includes(filters.description.toLowerCase()))
    && (!filters.amount || String(expense.amount).includes(filters.amount))
    && (!filters.supplier || expense.supplier?.toLowerCase().includes(filters.supplier.toLowerCase()))
    && (!filters.country || expense.country?.toLowerCase().includes(filters.country.toLowerCase()))
  ));

  return (
    <div className="page-content wide-content">
        <div className="page-heading">
          <h2>Expenses</h2>
          <p className="small-text">Review spending trends and recorded expenses.</p>
        </div>
        {dashboard.error && <div className="alert alert-danger">{dashboard.error}</div>}
        <section className="card expense-filters page-section">
          <h2>Filter Expenses</h2>

          <div className="filter-grid">
            <div className="filter-field filter-search-field">
              <label htmlFor="expense-search">Search Term:</label>
              <input
                id="expense-search"
                aria-label="Search expenses"
                type="text"
                placeholder="Search..."
                value={filters.description}
                onChange={(event) => setFilters((current) => ({ ...current, description: event.target.value }))}
              />
            </div>
            <div className="filter-field">
              <label htmlFor="expense-date">Date:</label>
              <input
                id="expense-date"
                type="date"
                aria-label="Filter by date"
                value={filters.date}
                onChange={(event) => setFilters((current) => ({ ...current, date: event.target.value }))}
              />
            </div>

            <div className="filter-field">
              <label htmlFor="expense-category">Category:</label>
              <select
                id="expense-category"
                aria-label="Filter by category"
                value={filters.category}
                onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value, subcategory: '' }))}
              >
                <option value="">All Categories</option>
                {dashboard.categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="expense-subcategory">Subcategory:</label>
              <select
                id="expense-subcategory"
                aria-label="Filter by subcategory"
                value={filters.subcategory}
                onChange={(event) => setFilters((current) => ({ ...current, subcategory: event.target.value }))}
              >
                <option value="">All Subcategories</option>
                {dashboard.subcategories.filter((item) => !filters.category || String(item.category) === filters.category).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="expense-amount">Amount:</label>
              <input
                id="expense-amount"
                aria-label="Filter by amount"
                type="number"
                placeholder="Amount"
                value={filters.amount}
                onChange={(event) => setFilters((current) => ({ ...current, amount: event.target.value }))}
              />
            </div>

            <div className="filter-field">
              <label htmlFor="expense-supplier">Supplier:</label>
              <input
                id="expense-supplier"
                aria-label="Filter by supplier"
                placeholder="Supplier"
                value={filters.supplier}
                onChange={(event) => setFilters((current) => ({ ...current, supplier: event.target.value }))}
              />
            </div>

            <div className="filter-field">
              <label htmlFor="expense-country">Country:</label>
              <input
                id="expense-country"
                aria-label="Filter by country"
                placeholder="Country"
                value={filters.country}
                onChange={(event) => setFilters((current) => ({ ...current, country: event.target.value }))}
              />
            </div>
          </div>
        </section>
        <div className="page-section">
          <ExpenseTable
            expenses={filteredExpenses}
            displayCurrency={displayCurrency}
            categories={dashboard.categories}
            subcategories={dashboard.subcategories}
            currencies={dashboard.currencies}
            client={client}
            onRefresh={dashboard.refetch}
          />
        </div>
        <div className="page-section">
          <SpendingChart chartData={dashboard.chart} symbol={symbol} transparent />
        </div>
    </div>
  );
}