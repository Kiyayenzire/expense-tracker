import React, { useEffect, useState } from 'react';
import { formatDateEU } from '../api';

const PAGE_SIZE = 11;

export function ExpenseTable({ expenses, displayCurrency, categories = [], currencies = [], client, onRefresh }) {
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const pageCount = Math.max(1, Math.ceil(expenses.length / PAGE_SIZE));
  const visibleExpenses = expenses.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  useEffect(() => {
    setCurrentPage((page) => Math.min(page, pageCount));
  }, [pageCount]);

  const startEdit = (exp) => {
    setEditingId(exp.id);
    setDraft({
      date: exp.date || '',
      category: exp.category ?? '',
      item_description: exp.item_description || '',
      measurement: exp.measurement || 'pc',
      quantity: String(exp.quantity ?? '1'),
      amount: String(exp.amount ?? '0'),
      currency: exp.currency ?? '',
      supplier: exp.supplier || '',
      country: exp.country || '',
      notes: exp.notes || '',
    });
  };

  const handleSave = async () => {
    if (!editingId || !client) return;

    const payload = {
      date: draft.date,
      category: Number(draft.category),
      item_description: draft.item_description,
      measurement: draft.measurement,
      quantity: Number(draft.quantity),
      amount: Number(draft.amount),
      currency: Number(draft.currency),
      supplier: draft.supplier,
      country: draft.country,
      notes: draft.notes,
    };

    try {
      await client.patch(`/expenses/${editingId}/`, payload);
      setEditingId(null);
      setDraft({});
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Unable to update expense:', error);
      window.alert('Unable to update this expense. Please try again.');
    }
  };

  return (
    <div className="card">
      <div className="header">
        <div>
          <h2>Recent Expenses</h2>
          <p className="small-text">Showing entries in {displayCurrency}.</p>
        </div>
      </div>
      <div className="table-responsive">
        <table className="table table-striped">
          <thead>
            <tr>
              <th>Date</th>
              <th>Category</th>
              <th>Subcategory</th>
              <th>Item</th>
              <th>Measure</th>
              <th>Quantity</th>
              <th>Amount</th>
              <th>Total Amount</th>
              <th>Supplier</th>
              <th>Country</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {visibleExpenses.map((exp) => {
              if (exp.date && typeof exp.date !== 'string') {
                console.warn('Non-string date value:', exp.id, exp.date, typeof exp.date);
              }

              try {
                return (
                  <tr key={exp.id}>
                    <td>{formatDateEU(exp.date)}</td>
                    <td>{exp.category_name || '-'}</td>
                    <td>{exp.subcategory_name || '-'}</td>
                    <td>{exp.item_description || '-'}</td>
                    <td>{exp.measurement || '-'}</td>
                    <td>{Number(exp.quantity || 0).toFixed(2)}</td>
                    <td>{exp.currency_symbol || exp.currency_code || '?'} {Number(exp.amount || 0).toFixed(2)}</td>
                    <td>{exp.currency_symbol || exp.currency_code || '?'} {(Number(exp.quantity || 0) * Number(exp.amount || 0)).toFixed(2)}</td>
                    <td>{exp.supplier || '-'}</td>
                    <td>{exp.country || '-'}</td>
                    <td>
                      <button type="button" className="btn btn-sm btn-outline-primary" onClick={() => startEdit(exp)}>Edit</button>
                    </td>
                  </tr>
                );
              } catch (error) {
                console.error('Error rendering expense row:', exp, error);
                return (
                  <tr key={exp.id}>
                    <td colSpan="11" style={{ color: 'red', textAlign: 'center' }}>Error rendering this expense</td>
                  </tr>
                );
              }
            })}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="pagination-controls" aria-label="Recent expenses pagination">
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setCurrentPage((page) => Math.max(1, page - 1))} disabled={currentPage === 1}>Previous</button>
          <span>Page {currentPage} of {pageCount}</span>
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setCurrentPage((page) => Math.min(pageCount, page + 1))} disabled={currentPage === pageCount}>Next</button>
        </div>
      )}

      {editingId !== null && (
        <div className="modal d-block" style={{ background: 'rgba(0,0,0,0.45)' }} role="dialog" aria-modal="true">
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Edit Expense</h5>
                <button type="button" className="btn-close" aria-label="Close" onClick={() => setEditingId(null)} />
              </div>
              <div className="modal-body">
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label">Date</label>
                    <input type="date" className="form-control" value={draft.date || ''} onChange={(event) => setDraft((current) => ({ ...current, date: event.target.value }))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Category</label>
                    <select className="form-control" value={draft.category ?? ''} onChange={(event) => setDraft((current) => ({ ...current, category: event.target.value }))}>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>{category.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Item</label>
                    <input type="text" className="form-control" value={draft.item_description || ''} onChange={(event) => setDraft((current) => ({ ...current, item_description: event.target.value }))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Measurement</label>
                    <select className="form-control" value={draft.measurement || 'pc'} onChange={(event) => setDraft((current) => ({ ...current, measurement: event.target.value }))}>
                      <option value="pc">Piece (pc)</option>
                      <option value="tn">Tin (tn)</option>
                      <option value="bt">Bottle (bt)</option>
                      <option value="kg">Kilogram (kg)</option>
                      <option value="ltr">Litre (ltr)</option>
                      <option value="un">Unit (un)</option>
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="edit-expense-quantity">Quantity</label>
                    <input id="edit-expense-quantity" type="number" step="0.01" min="0" className="form-control" value={draft.quantity || '0'} onChange={(event) => setDraft((current) => ({ ...current, quantity: event.target.value }))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Amount</label>
                    <input type="number" step="0.01" min="0" className="form-control" value={draft.amount || '0'} onChange={(event) => setDraft((current) => ({ ...current, amount: event.target.value }))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Currency</label>
                    <select className="form-control" value={draft.currency ?? ''} onChange={(event) => setDraft((current) => ({ ...current, currency: event.target.value }))}>
                      {currencies.map((currency) => (
                        <option key={currency.id} value={currency.id}>{currency.symbol} {currency.code}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Supplier</label>
                    <input type="text" className="form-control" value={draft.supplier || ''} onChange={(event) => setDraft((current) => ({ ...current, supplier: event.target.value }))} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Country</label>
                    <input type="text" className="form-control" value={draft.country || ''} onChange={(event) => setDraft((current) => ({ ...current, country: event.target.value }))} />
                  </div>
                  <div className="col-12">
                    <label className="form-label">Notes</label>
                    <textarea className="form-control" rows="3" value={draft.notes || ''} onChange={(event) => setDraft((current) => ({ ...current, notes: event.target.value }))} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline-secondary" onClick={() => setEditingId(null)}>Cancel</button>
                <button type="button" className="btn btn-primary" onClick={handleSave}>Save changes</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}