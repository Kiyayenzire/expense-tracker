import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function SpendingChart({ chartData = {}, symbol = '€' }) {
  const expensive = Array.isArray(chartData.expensive) ? chartData.expensive : [];
  const least = Array.isArray(chartData.least) ? chartData.least : [];

  if (!expensive.length && !least.length) {
    return (
      <div className="card chart-card">
        <h2>Spending Trends</h2>
        <div className="empty-state">No spending data available for this period.</div>
      </div>
    );
  }

  const formattedChart = expensive.map((item) => ({
    name: item.category__name || item.category,
    total: Number(item.total || 0),
  }));

  return (
    <div className="card chart-card">
      <h2>Spending Trends</h2>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={formattedChart}>
            <XAxis dataKey="name" axisLine={false} tickLine={false} />
            <YAxis axisLine={false} tickLine={false} />
            <Tooltip formatter={(val) => `${symbol} ${Number(val).toFixed(2)}`} />
            <Bar dataKey="total" fill="#3B3B3D" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="insight-box">
        <strong>Least Expensive Categories</strong>
        <ul>
          {least.map((item) => (
            <li key={item.category__name || item.category}>
              {item.category__name || item.category}: {symbol} {(Number(item.total || 0)).toFixed(2)}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}