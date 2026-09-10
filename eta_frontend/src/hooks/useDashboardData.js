import { useState, useEffect, useCallback } from 'react';

export function useDashboardData(client, displayCurrency, onUnauthorized) {
  const [data, setData] = useState({
    categories: [],
    items: [],
    subcategories: [],
    currencies: [],
    expenses: [],
    summary: {},
    chart: { expensive: [], least: [] },
    categorySummary: { year: new Date().getFullYear(), categories: [] },
    prediction: {},
    insights: { anomalies: [] },
  });
  const [convertedExpenses, setConvertedExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      console.log('useDashboardData: Fetching data with displayCurrency=', displayCurrency);
      const [categories, subcategories, items, currencies, expenses, summary, chart, prediction, insights] = 
        await Promise.all([
          client.get('/categories/'),
          client.get('/subcategories/'),
          client.get('/items/'),
          client.get('/currencies/'),
          client.get('/expenses/'),
          client.get('/expenses/summary/', { params: { target_currency: displayCurrency } }),
          client.get('/expenses/chart/', { params: { target_currency: displayCurrency } }),
          client.get('/expenses/prediction/', { params: { target_currency: displayCurrency } }),
          client.get('/expenses/insights/', { params: { target_currency: displayCurrency } }),
        ]);

      const expenseEntries = expenses.data || [];
      const expenseYears = expenseEntries
        .map((entry) => Number(new Date(entry.date).getFullYear()))
        .filter((year) => Number.isFinite(year));
      const latestExpenseYear = expenseYears.length ? Math.max(...expenseYears) : new Date().getFullYear();

      const categorySummary = await client.get('/expenses/category-summary/', {
        params: { target_currency: displayCurrency, year: latestExpenseYear },
      });

      console.log('useDashboardData: Received chart data:', chart.data);
      setData({
        categories: categories.data || [],
        subcategories: subcategories.data || [],
        items: items.data || [],
        currencies: currencies.data || [],
        expenses: expenseEntries,
        summary: summary.data || {},
        chart: chart.data || { expensive: [], least: [] },
        categorySummary: categorySummary.data || { year: latestExpenseYear, categories: [] },
        prediction: prediction.data || {},
        insights: insights.data || { anomalies: [] },
      });
      setError('');
    } catch (err) {
      if (err.response?.status === 401) {
        onUnauthorized();
        return;
      }
      setError('Unable to load dashboard data.');
    } finally {
      setLoading(false);
    }
  }, [client, displayCurrency, onUnauthorized]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const handleExpenseSaved = () => {
      fetchData();
    };

    window.addEventListener('expense-saved', handleExpenseSaved);
    return () => window.removeEventListener('expense-saved', handleExpenseSaved);
  }, [fetchData]);

  // Handle currency conversion state
  useEffect(() => {
    if (!data.expenses.length || !displayCurrency) return;

    let isMounted = true;
    Promise.all(
      data.expenses.map(async (entry) => {
        if (!entry.amount || entry.currency_code === displayCurrency) {
          return { ...entry, converted_amount: entry.amount };
        }
        try {
          const res = await client.get('/convert-currency/', {
            params: { base: entry.currency_code, target: displayCurrency, amount: entry.amount },
          });
          return { ...entry, converted_amount: res.data.converted || entry.amount };
        } catch {
          return { ...entry, converted_amount: entry.amount };
        }
      })
    ).then((conversions) => {
      if (isMounted) setConvertedExpenses(conversions);
    });

    return () => { isMounted = false; };
  }, [data.expenses, displayCurrency, client]);

  return { ...data, convertedExpenses, loading, error, refetch: fetchData, setError };
}