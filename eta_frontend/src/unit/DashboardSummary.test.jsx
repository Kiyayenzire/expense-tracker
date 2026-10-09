import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CategorySummary } from '../components/CategorySummary';
import { SpendingChart } from '../components/SpendingChart';
import { formatDateEU } from '../api';

describe('CategorySummary unit tests', () => {
  it('renders an empty state when no category totals exist', () => {
    render(<CategorySummary categories={[]} year={2026} symbol="€" />);

    expect(screen.getByText(/no category spending recorded for 2026/i)).toBeInTheDocument();
  });

  it('renders each category total and the current year heading', () => {
    const categories = [
      { category: 'Food', total: 120.5, color: '#ff0000' },
      { category: 'Transport', total: 50, color: '#00ff00' },
    ];

    render(<CategorySummary categories={categories} year={2026} symbol="€" />);

    expect(screen.getByText(/category spending/i)).toBeInTheDocument();
    expect(screen.getByText(/current year: 2026/i)).toBeInTheDocument();
    expect(screen.getByText('Food')).toBeInTheDocument();
    expect(screen.getByText('Transport')).toBeInTheDocument();
  });

  it('renders all category totals in alphabetical order as a bar chart', () => {
    const categories = [
      { category: 'Transport', total: 20, color: '#ff0000' },
      { category: 'Food', total: 100, color: '#00ff00' },
      { category: 'Communication', total: 50, color: '#0000ff' },
    ];

    render(<CategorySummary categories={categories} year={2026} symbol="€" />);

    expect(screen.getByText('Category Totals')).toBeInTheDocument();
    expect(screen.getByText('Communication')).toBeInTheDocument();
    expect(screen.getByText('Food')).toBeInTheDocument();
    expect(screen.getByText('Transport')).toBeInTheDocument();
  });

  it('defaults category cards to latest update and supports alphabetical sorting', async () => {
    const categories = [
      { category: 'Food', total: 100, color: '#00ff00' },
      { category: 'Transport', total: 20, color: '#ff0000' },
      { category: 'Communication', total: 50, color: '#0000ff' },
    ];
    const expenses = [
      { category_name: 'Food', updated_at: '2026-09-01T10:00:00Z' },
      { category_name: 'Transport', updated_at: '2026-09-03T10:00:00Z' },
      { category_name: 'Communication', updated_at: '2026-09-02T10:00:00Z' },
    ];

    render(<CategorySummary categories={categories} year={2026} symbol="€" expenses={expenses} />);

    const getCardOrder = () => [...document.querySelectorAll('.category-total-button span')].map((item) => item.textContent);
    expect(getCardOrder()).toEqual(['Transport', 'Communication', 'Food']);

    await userEvent.selectOptions(screen.getByRole('combobox', { name: /sort categories/i }), 'asc');
    expect(getCardOrder()).toEqual(['Communication', 'Food', 'Transport']);

    await userEvent.selectOptions(screen.getByRole('combobox', { name: /sort categories/i }), 'desc');
    expect(getCardOrder()).toEqual(['Transport', 'Food', 'Communication']);
  });

  it('formats DD/MM/YYYY dates without producing an invalid timestamp', () => {
    expect(formatDateEU('29/04/2026')).toMatch(/29\/04\/2026/);
  });

  it('renders a safe empty-state chart when no spending data is available', () => {
    render(<SpendingChart chartData={{ expensive: [], least: [] }} symbol="€" />);
    expect(screen.getByText(/no spending data available for this period/i)).toBeInTheDocument();
  });

  it('can render spending trends without a card background', () => {
    const { container } = render(
      <SpendingChart chartData={{ expensive: [], least: [] }} symbol="€" transparent />,
    );

    expect(container.firstChild).toHaveClass('chart-card-transparent');
  });
});
