import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

vi.mock('../api', async () => {
  const actual = await vi.importActual('../api');
  return {
    ...actual,
    createClient: vi.fn(() => ({
      get: vi.fn((url) => {
        if (url === '/categories/') return Promise.resolve({ data: [{ id: 1, name: 'Food' }] });
        if (url === '/subcategories/') return Promise.resolve({ data: [{ id: 10, name: 'Groceries', category: 1 }] });
        if (url === '/items/') return Promise.resolve({ data: [{ id: 101, category: 1, subcategory: 10, description: 'Rice bag', measurement: 'kg' }] });
        if (url === '/currencies/') return Promise.resolve({ data: [{ id: 1, code: 'EUR', symbol: '€' }] });
        if (url === '/expenses/') return Promise.resolve({ data: [] });
        if (url === '/expenses/summary/') return Promise.resolve({ data: { total: 0 } });
        if (url === '/expenses/chart/') return Promise.resolve({ data: { expensive: [], least: [] } });
        if (url === '/expenses/category-summary/') return Promise.resolve({ data: { year: 2026, categories: [{ category: 'Food', total: 120 }] } });
        if (url === '/expenses/prediction/') return Promise.resolve({ data: { predicted_amount: 3300 } });
        if (url === '/expenses/insights/') return Promise.resolve({ data: { anomalies: [{ description: 'Travel spend is unusually high' }] } });
        return Promise.resolve({ data: {} });
      }),
      post: vi.fn(async (url, payload) => {
        if (url.includes('export-report')) {
          return { data: new Blob(['csv-data'], { type: 'text/csv' }) };
        }
        return { data: { ok: true } };
      }),
    })),
  };
});

describe('Reports and insights integration tests', () => {
  beforeEach(() => {
    window.localStorage.setItem('expense-tracker-token', 'demo-token');
    window.location.hash = '#/insights';
  });

  it('shows the insights headline and forecast text from dashboard data', async () => {
    render(<App />);

    const insightsHeadings = await screen.findAllByRole('heading', { name: /insights/i });
    expect(insightsHeadings.length).toBeGreaterThan(0);
    expect(await screen.findByText(/next month forecast: €3300/i)).toBeInTheDocument();
    expect(await screen.findByText(/travel spend is unusually high/i)).toBeInTheDocument();
  });

  it('navigates from the dashboard to the reports page and renders the export section', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: /reports/i }));

    expect(await screen.findByRole('heading', { name: /reports/i })).toBeInTheDocument();
    expect(await screen.findByText(/export expense reports for a selected period/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /download report/i })).toBeInTheDocument();
  });
});
