import React, { useState } from 'react';
import axios from 'axios';
import { useOfflineSync } from '../hooks/useOfflineSync';
import { queueOfflineExpense } from '../services/db';

export const ExpenseFormOffline = () => {
  const { isOnline, rates } = useOfflineSync(axios.create({ baseURL: '/api' }));
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('EUR');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      description,
      expense_date: new Date().toISOString().split('T')[0],
      amount_original: parseFloat(amount),
      currency_original: currency,
    };

    if (isOnline) {
      try {
        await axios.post('/api/expenses/', payload);
        setMessage('Expense saved online successfully!');
      } catch (error) {
        await queueOfflineExpense(payload);
        setMessage('Network error. Saved locally to sync later.');
      }
    } else {
      await queueOfflineExpense(payload);
      setMessage('Offline mode: Saved locally. Will auto-sync when online.');
    }

    setDescription('');
    setAmount('');
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border rounded shadow-sm max-w-md bg-white">
      <div className="mb-2 flex items-center justify-between">
        <span className={`px-2 py-1 text-xs rounded ${isOnline ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
          {isOnline ? '● Online' : '○ Offline Mode'}
        </span>
      </div>

      <div className="mb-3">
        <label className="block text-sm font-medium">Description</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          className="w-full border p-2 rounded"
        />
      </div>

      <div className="mb-3 flex gap-2">
        <div className="flex-1">
          <label className="block text-sm font-medium">Amount</label>
          <input
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            className="w-full border p-2 rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Currency</label>
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="border p-2 rounded bg-white"
          >
            <option value="EUR">EUR (€)</option>
            <option value="USD">USD ($)</option>
            <option value="UGX">UGX (USh)</option>
          </select>
        </div>
      </div>

      <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
        Submit Expense
      </button>

      {rates && <p className="mt-2 text-xs text-gray-500">Rates loaded: {Object.keys(rates).length}</p>}
      {message && <p className="mt-2 text-sm text-gray-600">{message}</p>}
    </form>
  );
};
