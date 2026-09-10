import { test, expect } from '@playwright/test';

test('login page loads and can switch to registration', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
  await page.getByRole('button', { name: /sign up/i }).click();

  await expect(page.getByRole('heading', { name: /register/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();
});

test('app shows the main expense tracker header on the dashboard state', async ({ page }) => {
  await page.goto('/');

  await page.evaluate(() => {
    window.localStorage.setItem('expense-tracker-token', 'playwright-token');
  });
  await page.reload();

  await expect(page.getByRole('heading', { name: /expense tracker/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /dashboard/i })).toBeVisible();
  await page.getByRole('button', { name: /anders|reprouser|playwright|user/i }).click();
  await expect(page.getByRole('button', { name: /log out/i })).toBeVisible();
});

test('quick expense entry shows a review before saving', async ({ page }) => {
  await page.route('**/api/**', async (route) => {
    const url = route.request().url();
    if (url.includes('/auth/profile/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ username: 'playwright' }) });
    if (url.includes('/currencies/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, code: 'EUR', symbol: '€' }]) });
    if (url.includes('/categories/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, name: 'Food' }]) });
    if (url.includes('/subcategories/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 10, name: 'Restaurants', category: 1 }]) });
    if (url.includes('/items/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    if (url.includes('/parse-quick-entry/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ amount: '35000.00', currency: 'EUR', date: '2026-09-03', description: 'Java House', category: 1, category_name: 'Food', subcategory: 10, subcategory_name: 'Restaurants', needs_confirmation: true }) });
    if (url.includes('/expenses/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
  });
  await page.addInitScript(() => localStorage.setItem('expense-tracker-token', 'playwright-token'));
  await page.goto('/#/add-expense');
  await expect(page.getByRole('heading', { name: /add new expense/i })).toBeVisible();
  await page.getByRole('textbox', { name: /quick expense description/i }).fill('I spent 35k at Java House');
  await page.getByRole('button', { name: /parse expense/i }).click();
  await expect(page.getByText(/review expense/i)).toBeVisible();
  await expect(page.getByText('Java House')).toBeVisible();
});
