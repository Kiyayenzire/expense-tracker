import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { renderHook, act } from '@testing-library/react';
import { InsightsSection } from '../components/InsightsSection';
import { ReportExporter } from '../components/ReportExporter';
import { useOfflineSync } from '../hooks/useOfflineSync';
import * as db from '../services/db';

vi.mock('../services/db', () => ({
  clearQueuedExpense: vi.fn(),
  getCachedRates: vi.fn(),
  getQueuedExpenses: vi.fn(),
  saveCachedRates: vi.fn(),
}));

describe('Reports and insights unit tests', () => {
  it('renders the anomaly text when insight data is available', () => {
    render(
      <InsightsSection
        prediction={{ predicted_amount: 3300.5 }}
        insights={{ anomalies: [{ description: 'Travel spend is unusually high' }] }}
        symbol="€"
      />
    );

    expect(screen.queryByText(/next month forecast: €3300.5/i)).not.toBeInTheDocument();
    expect(screen.getByText(/travel spend is unusually high/i)).toBeInTheDocument();
  });

  it('separates insights into the active feature sections only', () => {
    render(
      <InsightsSection
        prediction={{ Food: 100 }}
        insights={{ anomalies: [], budget_recommendations: [], financial_insights: [] }}
        symbol="€"
      />
    );

    expect(screen.getByRole('heading', { name: /natural language entry/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /automatic categorization/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /anomaly detection/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /financial insights/i })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /spending prediction/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /budget recommendations/i })).not.toBeInTheDocument();
  });

  it('submits the export payload with the current report settings', async () => {
    const client = {
      post: vi.fn().mockResolvedValue({ data: new Blob(['csv-data'], { type: 'text/csv' }) }),
    };

    const createObjectURL = vi.fn(() => 'blob:report');
    const revokeObjectURL = vi.fn();
    global.URL.createObjectURL = createObjectURL;
    global.URL.revokeObjectURL = revokeObjectURL;
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    render(
      <ReportExporter
        client={client}
        displayCurrency="USD"
        onSuccess={vi.fn()}
        onError={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /download report/i }));

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith(
        expect.stringContaining('export-report/?format=csv'),
        expect.objectContaining({
          target_currency: 'USD',
          period: 'monthly',
        }),
        expect.objectContaining({ responseType: 'blob' })
      );
    });

    clickSpy.mockRestore();
  });

  it('updates queued offline expenses when the browser goes offline', async () => {
    db.getQueuedExpenses.mockResolvedValue([{ temp_id: 12, amount: 99, created_at_offline: '2026-08-31T00:00:00Z' }]);
    db.getCachedRates.mockResolvedValue({ USD: 1.1 });

    const client = {
      get: vi.fn(),
      post: vi.fn(),
    };

    const { result } = renderHook(() => useOfflineSync(client));

    await waitFor(() => {
      expect(result.current.queuedCount).toBe(1);
    });

    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    await waitFor(() => {
      expect(result.current.isOnline).toBe(false);
    });
  });
});
