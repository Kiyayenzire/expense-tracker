import React, { useState, useEffect } from 'react';
import { useOfflineSync } from '../hooks/useOfflineSync';
import { queueOfflineExpense } from '../services/db';

export function getLocalDateInputValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

const initialForm = {
  date: getLocalDateInputValue(),
  category: '',
  subcategory: '',
  itemDescription: '',
  measurement: 'pc',
  quantity: '1',
  supplier: '',
  country: '',
  amount: '0.00',
  currency: '',
  notes: '',
};

export function ExpenseForm({ categories, subcategories, items, currencies, client, onSuccess, onError, quickDraft }) {
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const { isOnline } = useOfflineSync(client);

  useEffect(() => {
    if (currencies.length && !form.currency) {
      const defaultEur = currencies.find((c) => c.code === 'EUR');
      setForm((prev) => ({ ...prev, currency: defaultEur ? defaultEur.id : currencies[0].id }));
    }
  }, [currencies, form.currency]);

  useEffect(() => {
    if (!quickDraft) return;
    const currency = currencies.find((item) => item.code === quickDraft.currency);
    setForm((previous) => ({
      ...previous,
      date: quickDraft.date || previous.date,
      category: quickDraft.category ? String(quickDraft.category) : previous.category,
      subcategory: quickDraft.subcategory ? String(quickDraft.subcategory) : previous.subcategory,
      itemDescription: quickDraft.description || previous.itemDescription,
      amount: quickDraft.amount || previous.amount,
      currency: currency ? String(currency.id) : previous.currency,
    }));
  }, [quickDraft, currencies]);

  const handleChange = (field, val) => setForm((prev) => ({ ...prev, [field]: val }));

  const categoryItems = items.filter((item) => String(item.category) === String(form.category));
  const categorySubcategories = subcategories
    .filter((subcategory) => String(subcategory.category) === String(form.category))
    .sort((first, second) => {
      if (first.name.toLowerCase() === 'other') return 1;
      if (second.name.toLowerCase() === 'other') return -1;
      return first.name.localeCompare(second.name);
    });
  const filteredItems = categoryItems.filter((item) => !form.subcategory || String(item.subcategory) === String(form.subcategory));
  const suggestedDescription = filteredItems[0]?.description || '';
  const suggestedMeasurement = filteredItems[0]?.measurement || 'pc';

  const handleCategoryChange = (value) => {
    setForm((prev) => ({ ...prev, category: value, subcategory: '', itemDescription: '' }));
  };

  const handleSubcategoryChange = (value) => {
    const matchingItem = categoryItems.find((item) => String(item.subcategory) === String(value));
    setForm((prev) => ({ ...prev, subcategory: value, itemDescription: '', measurement: matchingItem?.measurement || 'pc' }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    const { itemDescription, ...formData } = form;
    const payload = {
      ...formData,
      item_description: itemDescription.trim(),
      user_local_time: new Date().toISOString(),
      user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    };

    try {
      await client.post('/expenses/', payload);
      window.dispatchEvent(new CustomEvent('expense-saved'));
      onSuccess('Expense recorded successfully.');
      setForm((prev) => ({ ...initialForm, currency: prev.currency, category: prev.category }));
    } catch (error) {
      const isNetworkFailure = !isOnline || !error?.response || error.code === 'ERR_NETWORK' || error.message === 'Network Error';

      if (isNetworkFailure) {
        await queueOfflineExpense(payload);
        onSuccess('Connection issue detected. Expense saved locally and will sync automatically when you reconnect.');
        setForm((prev) => ({ ...initialForm, currency: prev.currency, category: prev.category }));
        return;
      }

      onError('Unable to save expense. Please verify form details.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">Add New Expense</h2>
        <span className={`badge ${isOnline ? 'bg-success' : 'bg-danger'}`}>
          {isOnline ? '● Online' : '⚠ Offline'}
        </span>
      </div>
      {!isOnline && <p className="small-text text-warning mb-2">You're offline. Expenses will be saved locally and sync automatically when you reconnect.</p>}
      <form onSubmit={handleSubmit} className="expense-form">
        <div className="form-group expense-field expense-field-date">
          <label>Date (DD/MM/YYYY)</label>
          <input type="date" className="form-control" title="Choose a date; it is displayed as DD/MM/YYYY" value={form.date} onChange={(e) => handleChange('date', e.target.value)} required />
        </div>

        <div className="form-group expense-field expense-field-category">
          <label htmlFor="expense-category">Category</label>
          <select id="expense-category" className="form-control" value={form.category} onChange={(e) => handleCategoryChange(e.target.value)} required>
            <option value="">Select Category</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="form-group expense-field expense-field-subcategory">
          <label htmlFor="expense-subcategory">Subcategory</label>
          <select id="expense-subcategory" className="form-control" value={form.subcategory} onChange={(e) => handleSubcategoryChange(e.target.value)} disabled={!form.category} required>
            <option value="">{form.category ? 'Select Subcategory' : 'Select Category first'}</option>
            {categorySubcategories.map((subcategory) => <option key={subcategory.id} value={subcategory.id}>{subcategory.name}</option>)}
          </select>
        </div>
        <div className="form-group expense-field expense-field-description">
          <label htmlFor="expense-description">Expense Description</label>
          <input id="expense-description" className="form-control" value={form.itemDescription} onChange={(e) => handleChange('itemDescription', e.target.value)} placeholder={form.subcategory ? `e.g. ${suggestedDescription}` : 'Select Subcategory first'} disabled={!form.subcategory} required />
          <span className="small-text field-hint">Example only: {suggestedDescription || 'enter your own final description'}. Type your complete description here.</span>
        </div>

        <div className="form-group expense-field expense-field-measurement">
          <label htmlFor="measurement">Measurement</label>
          <select id="measurement" className="form-control" value={form.measurement} onChange={(e) => handleChange('measurement', e.target.value)}>
            <option value="pc">Piece (pc)</option>
            <option value="tn">Tin (tn)</option>
            <option value="bt">Bottle (bt)</option>
            <option value="kg">Kilogram (kg)</option>
            <option value="ltr">Litre (ltr)</option>
            <option value="un">Unit (un)</option>
          </select>
          <span className="small-text field-hint">Suggested measurement: {suggestedMeasurement}. You can change it.</span>
        </div>

        <div className="form-group expense-field expense-field-amount">
          <label htmlFor="expense-amount">Amount (e.g. 125.50)</label>
          <input id="expense-amount" type="number" step="0.01" min="0" placeholder="Enter amount" className="form-control" value={form.amount} onChange={(e) => handleChange('amount', e.target.value)} required />
        </div>
        <div className="form-group expense-field expense-field-currency">
          <label htmlFor="expense-currency">Currency</label>
          <select id="expense-currency" className="form-control" value={form.currency} onChange={(e) => handleChange('currency', e.target.value)}>
            {currencies.map((c) => <option key={c.id} value={c.id}>{c.symbol} {c.code}</option>)}
          </select>
        </div>

        <div className="form-group expense-field expense-field-quantity">
          <label htmlFor="expense-quantity">Quantity (e.g. 1)</label>
          <input id="expense-quantity" type="number" step="0.01" min="0" placeholder="Enter quantity" className="form-control" value={form.quantity} onChange={(e) => handleChange('quantity', e.target.value)} required />
        </div>
        <div className="form-group expense-field expense-field-supplier">
          <label htmlFor="expense-supplier">Supplier / Provider (optional)</label>
          <input id="expense-supplier" className="form-control" placeholder="e.g. Local market" value={form.supplier} onChange={(e) => handleChange('supplier', e.target.value)} />
        </div>

        <div className="form-group expense-field expense-field-country">
          <label htmlFor="expense-country">Country (optional)</label>
          <input id="expense-country" className="form-control" placeholder="e.g. Uganda" value={form.country} onChange={(e) => handleChange('country', e.target.value)} />
        </div>

        <div className="form-group expense-field expense-field-notes">
          <label>Notes (optional)</label>
          <textarea className="form-control" placeholder="Add useful details" value={form.notes} onChange={(e) => handleChange('notes', e.target.value)} rows={2} />
        </div>

        <button className="btn btn-primary w-100" type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : 'Save Expense'}
        </button>
      </form>
    </div>
  );
}