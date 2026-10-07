import React from 'react';
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

function CategoryTooltip({ active, payload, symbol }) {
  if (!active || !payload?.length) return null;

  const category = payload[0].payload;
  return (
    <div className="category-chart-tooltip">
      <strong>{category.category}</strong>
      <span>{symbol} {Number(payload[0].value).toFixed(2)}</span>
    </div>
  );
}

function getContrastTextColor(hexColor = '#3B3B3D') {
  const normalized = hexColor.replace('#', '').trim();
  const safeHex = normalized.length === 3 ? normalized.split('').map((char) => char + char).join('') : normalized;
  const value = Number.parseInt(safeHex, 16);
  const red = (value >> 16) & 255;
  const green = (value >> 8) & 255;
  const blue = value & 255;
  const luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;
  return luminance > 0.62 ? '#0F172A' : '#FFFFFF';
}

export function CategorySummary({ categories, year, symbol, expenses = [] }) {
  const [sortOrder, setSortOrder] = React.useState('updated');
  const latestUpdateByCategory = new Map();
  expenses.forEach((expense) => {
    const categoryName = expense.category_name;
    const updatedAt = Date.parse(expense.updated_at || expense.created_at || expense.date || '');
    if (categoryName && Number.isFinite(updatedAt)) {
      latestUpdateByCategory.set(categoryName, Math.max(latestUpdateByCategory.get(categoryName) || 0, updatedAt));
    }
  });
  const chartData = categories.map((category) => ({
    ...category,
    total: Number(category.total || 0),
    textColor: getContrastTextColor(category.color || '#3B3B3D'),
  }));
  const sortedCategories = [...chartData].sort((first, second) => {
    if (sortOrder === 'asc') return first.category.localeCompare(second.category);
    if (sortOrder === 'desc') return second.category.localeCompare(first.category);
    return (latestUpdateByCategory.get(second.category) || 0) - (latestUpdateByCategory.get(first.category) || 0);
  });
  const alphabetizedChartData = [...chartData].sort((first, second) => first.category.localeCompare(second.category));

  return (
    <section className="category-summary-section">
      <div className="section-heading category-summary-heading">
        <div>
          <h2>Category Spending</h2>
          <p className="small-text">Current year: {year}</p>
        </div>
        <label className="category-sort-control">
          Sort categories
          <select aria-label="Sort categories" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
            <option value="updated">Last updated</option>
            <option value="asc">A-Z</option>
            <option value="desc">Z-A</option>
          </select>
        </label>
      </div>

      {chartData.length === 0 ? (
        <div className="card empty-state">No Category Spending Recorded for {year}.</div>
      ) : (
        <>
          <div className="category-buttons">
            {sortedCategories.map((category) => (
              <button
                type="button"
                className="category-total-button"
                key={category.category}
                style={{ '--category-color': category.color, '--category-text-color': category.textColor }}
                title={`${category.category}: ${symbol} ${category.total.toFixed(2)}`}
              >
                <span>{category.category}</span>
                <strong>{symbol} {category.total.toFixed(2)}</strong>
              </button>
            ))}
          </div>

          <div className="card category-bar-card">
            <h2>Category Totals</h2>
            <div className="category-bar-wrapper" style={{ height: Math.max(360, alphabetizedChartData.length * 48) }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={alphabetizedChartData} layout="vertical" margin={{ top: 20, right: 24, left: 24, bottom: 24 }}>
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text)' }} />
                  <YAxis type="category" dataKey="category" width={150} axisLine={false} tickLine={false} tick={{ fontSize: 13, fill: 'var(--text)' }} />
                  <Tooltip content={<CategoryTooltip symbol={symbol} />} cursor={false} />
                  <Bar dataKey="total" barSize={36}>
                    {alphabetizedChartData.map((category) => (
                      <Cell key={category.category} fill={category.color || '#3B3B3D'} />
                    ))}
                  </Bar>
                  
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </section>
  );
}