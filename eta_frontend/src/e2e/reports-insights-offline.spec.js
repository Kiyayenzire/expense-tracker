import { test, expect } from '@playwright/test';

const mockApiResponses = {
  categories: [{ id: 1, name: 'Food' }],
  subcategories: [{ id: 10, name: 'Groceries', category: 1 }],
  items: [{ id: 101, category: 1, subcategory: 10, description: 'Rice bag', measurement: 'kg' }],
  currencies: [{ id: 1, code: 'EUR', symbol: '€', name: 'Euro' }],
  expenses: [],
  summary: { total: 2400 },
  chart: { expensive: [], least: [] },
  categorySummary: { year: 2026, categories: [{ category: 'Food', total: 120 }] },
  prediction: { predicted_amount: 3300 },
  insights: { anomalies: [{ description: 'Travel spend is unusually high' }] },
};

test.beforeEach(async ({ page }) => {
  await page.route('**/api/**', async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    if (url.includes('/categories/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.categories) });
    }
    if (url.includes('/subcategories/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.subcategories) });
    }
    if (url.includes('/items/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.items) });
    }
    if (url.includes('/currencies/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.currencies) });
    }
    if (url.includes('/expenses/summary/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.summary) });
    }
    if (url.includes('/expenses/chart/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.chart) });
    }
    if (url.includes('/expenses/category-summary/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.categorySummary) });
    }
    if (url.includes('/expenses/prediction/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.prediction) });
    }
    if (url.includes('/expenses/insights/')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.insights) });
    }
    if (url.includes('/expenses/')) {
      if (method === 'POST') {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockApiResponses.expenses) });
    }

    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) });
  });
});

test('reports page loads and renders the export panel', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => {
    window.localStorage.setItem('expense-tracker-token', 'e2e-token');
  });
  await page.reload();

  await page.getByRole('button', { name: /reports/i }).click();

  await expect(page.getByRole('heading', { name: /reports/i })).toBeVisible();
  await expect(page.getByText(/export expense reports for a selected period/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /download report/i })).toBeVisible();
});

test('insights page shows the forecast and anomaly information', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => {
    window.localStorage.setItem('expense-tracker-token', 'e2e-token');
  });
  await page.reload();

  await page.getByRole('button', { name: /insights/i }).click();

  await expect(page.locator('h2').filter({ hasText: 'Insights' }).first()).toBeVisible();
  await expect(page.getByText(/next month forecast/i)).toBeVisible();
  await expect(page.getByText(/travel spend is unusually high/i)).toBeVisible();
});

test('offline sync keeps the app responsive and shows the offline state', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => {
    window.localStorage.setItem('expense-tracker-token', 'e2e-token');
  });
  await page.reload();

  await page.getByRole('button', { name: /add expense/i }).click();
  await page.context().setOffline(true);

  await expect(page.locator('.badge.bg-danger')).toContainText('Offline');
  await expect(page.getByText(/saved locally and sync automatically when you reconnect/i)).toBeVisible();
});
