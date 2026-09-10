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

export function CategorySummary({ categories, year, symbol }) {
  const chartData = categories.map((category) => ({
    ...category,
    total: Number(category.total || 0),
  }));
  const alphabetizedChartData = [...chartData].sort((first, second) => first.category.localeCompare(second.category));

  return (
    <section className="category-summary-section">
      <div className="section-heading">
        <div>
          <h2>Category Spending</h2>
          <p className="small-text">Current year: {year}</p>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="card empty-state">No Category Spending Recorded for {year}.</div>
      ) : (
        <>
          <div className="category-buttons">
            {chartData.map((category) => (
              <button
                type="button"
                className="category-total-button"
                key={category.category}
                style={{ '--category-color': category.color }}
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
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--muted)' }} />
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