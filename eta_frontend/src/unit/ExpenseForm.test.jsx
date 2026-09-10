import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExpenseForm, getLocalDateInputValue } from '../components/ExpenseForm';
import { ExpenseTable } from '../components/ExpenseTable';
import ProfilePage from '../ProfilePage';
import { QuickExpenseEntry } from '../components/QuickExpenseEntry';

const mockClient = { post: vi.fn() };

vi.mock('../hooks/useOfflineSync', () => ({
  useOfflineSync: () => ({ isOnline: true }),
}));

describe('ExpenseForm unit tests', () => {
  const categories = [{ id: 1, name: 'Food' }];
  const subcategories = [{ id: 10, name: 'Groceries', category: 1 }];
  const items = [{ id: 101, category: 1, subcategory: 10, description: 'Rice bag', measurement: 'kg' }];
  const currencies = [{ id: 1, code: 'EUR', symbol: '€' }];

  beforeEach(() => {
    mockClient.post.mockReset();
    mockClient.post.mockResolvedValue({ data: { ok: true } });
  });

  it('shows a reviewable quick expense parse result without saving it', async () => {
    const user = userEvent.setup();
    const client = { post: vi.fn().mockResolvedValue({ data: {
      amount: '35000.00', currency: 'UGX', date: '2026-09-02', description: 'Java House',
      category_name: 'Food', subcategory_name: 'Restaurants', needs_confirmation: true,
    } }) };
    render(<QuickExpenseEntry client={client} onParsed={vi.fn()} />);

    await user.type(screen.getByRole('textbox', { name: /quick expense description/i }), 'I spent 35k at Java House');
    await user.click(screen.getByRole('button', { name: /parse expense/i }));

    expect(await screen.findByText(/review expense/i)).toBeInTheDocument();
    expect(screen.getByText(/Java House/)).toBeInTheDocument();
    expect(client.post).toHaveBeenCalledWith('/expenses/parse-quick-entry/', { text: 'I spent 35k at Java House' });
  });

  it('formats dates using the local browser date instead of UTC', () => {
    const date = new Date(2025, 5, 10, 18, 45, 0);
    const expected = [
      date.getFullYear(),
      String(date.getMonth() + 1).padStart(2, '0'),
      String(date.getDate()).padStart(2, '0'),
    ].join('-');

    expect(getLocalDateInputValue(date)).toBe(expected);
  });

  it('renders the recent-expense table without the converted column and with an edit action', () => {
    const onEdit = vi.fn();

    render(
      <ExpenseTable
        expenses={[{ id: 99, date: '2026-09-02', category_name: 'Food', item_description: 'Rice', measurement: 'kg', amount: '12.50', currency_symbol: '€', supplier: 'Market', country: 'UG', currency_code: 'EUR' }]}
        displayCurrency="EUR"
        onEdit={onEdit}
      />
    );

    expect(screen.queryByText(/converted/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
  });

  it('shows eleven expenses per page', async () => {
    const user = userEvent.setup();
    const expenses = Array.from({ length: 12 }, (_, index) => ({
      id: index + 1,
      date: '2026-09-02',
      category_name: 'Food',
      item_description: `Item ${index + 1}`,
      measurement: 'pc',
      quantity: '1',
      amount: '10.00',
      currency_symbol: '€',
      supplier: 'Market',
      country: 'UG',
    }));

    render(<ExpenseTable expenses={expenses} displayCurrency="EUR" />);

    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 11')).toBeInTheDocument();
    expect(screen.queryByText('Item 12')).not.toBeInTheDocument();
    expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Next' }));

    expect(screen.getByText('Item 12')).toBeInTheDocument();
    expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
    expect(screen.getByText('Page 2 of 2')).toBeInTheDocument();
  });

  it('keeps the server-returned profile image after a successful upload', async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, 'fetch');
    const file = new File(['avatar'], 'avatar.png', { type: 'image/png' });

    URL.createObjectURL = vi.fn(() => 'blob:preview-avatar');

    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          username: 'alice',
          email: 'alice@example.com',
          first_name: 'Alice',
          last_name: 'Demo',
          phone_number: '123',
          profile_picture_url: 'http://localhost:8000/media/avatar.png',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          username: 'alice',
          email: 'alice@example.com',
          first_name: 'Alice',
          last_name: 'Demo',
          phone_number: '123',
          profile_picture_url: 'http://localhost:8000/media/new-avatar.png',
        }),
      });

    render(
      <ProfilePage
        token="demo-token"
        onLogout={vi.fn()}
        theme="light"
        setTheme={vi.fn()}
        onNavigate={vi.fn()}
        username="alice"
        profilePicture=""
        setProfilePicture={vi.fn()}
        setUsername={vi.fn()}
      />
    );

    await waitFor(() => expect(screen.getByRole('img', { name: /profile/i })).toBeInTheDocument());

    const input = screen.getByLabelText(/profile photo/i);
    await user.upload(input, file);
    await user.click(screen.getByRole('button', { name: /save profile/i }));

    await waitFor(() => {
      expect(screen.getByRole('img', { name: /profile/i })).toHaveAttribute('src', 'http://localhost:8000/media/new-avatar.png');
    });

    fetchMock.mockRestore();
  });

  it('renders the expense form and preselects the default currency', () => {
    render(
      <ExpenseForm
        categories={categories}
        subcategories={subcategories}
        items={items}
        currencies={currencies}
        client={mockClient}
        onSuccess={vi.fn()}
        onError={vi.fn()}
      />
    );

    expect(screen.getByText(/add new expense/i)).toBeInTheDocument();
    expect(screen.getByText(/online/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save expense/i })).toBeInTheDocument();
  });

  it('dispatches a refresh event after a successful expense save', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    const onEvent = vi.fn();
    window.addEventListener('expense-saved', onEvent);

    render(
      <ExpenseForm
        categories={categories}
        subcategories={subcategories}
        items={items}
        currencies={currencies}
        client={mockClient}
        onSuccess={onSuccess}
        onError={vi.fn()}
      />
    );

    const selects = document.querySelectorAll('select');
    await user.selectOptions(selects[0], '1');
    await user.selectOptions(selects[1], '10');
    await user.clear(screen.getByLabelText(/expense description/i));
    await user.type(screen.getByLabelText(/expense description/i), 'Rice bag');
    await user.clear(screen.getByLabelText(/amount \(e\.g\. 125\.50\)/i));
    await user.type(screen.getByLabelText(/amount \(e\.g\. 125\.50\)/i), '25.50');
    await user.clear(screen.getByLabelText(/quantity \(e\.g\. 1\)/i));
    await user.type(screen.getByLabelText(/quantity \(e\.g\. 1\)/i), '2');
    await user.click(screen.getByRole('button', { name: /save expense/i }));

    await waitFor(() => {
      expect(onEvent).toHaveBeenCalled();
      expect(onSuccess).toHaveBeenCalledWith('Expense recorded successfully.');
    });

    window.removeEventListener('expense-saved', onEvent);
  });

  it('submits a valid expense payload and calls the success handler', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    const { container } = render(
      <ExpenseForm
        categories={categories}
        subcategories={subcategories}
        items={items}
        currencies={currencies}
        client={mockClient}
        onSuccess={onSuccess}
        onError={vi.fn()}
      />
    );

    const selects = container.querySelectorAll('select');
    await user.selectOptions(selects[0], '1');
    await user.selectOptions(selects[1], '10');

    const descriptionInput = screen.getByLabelText(/expense description/i);
    await user.clear(descriptionInput);
    await user.type(descriptionInput, 'Rice bag');

    const amountInput = screen.getByLabelText(/amount \(e\.g\. 125\.50\)/i);
    const quantityInput = screen.getByLabelText(/quantity \(e\.g\. 1\)/i);

    await user.clear(amountInput);
    await user.type(amountInput, '25.50');
    await user.clear(quantityInput);
    await user.type(quantityInput, '2');

    await user.click(screen.getByRole('button', { name: /save expense/i }));

    await waitFor(() => {
      expect(mockClient.post).toHaveBeenCalledWith(
        '/expenses/',
        expect.objectContaining({
          item_description: 'Rice bag',
          amount: expect.any(String),
          quantity: '2',
          currency: 1,
          category: '1',
          subcategory: '10',
        })
      );
    });

    expect(onSuccess).toHaveBeenCalledWith('Expense recorded successfully.');
  });
});
