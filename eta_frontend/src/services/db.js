const DB_NAME = 'ExpenseTrackerDB';
const DB_VERSION = 1;

export const initDB = () =>
  new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains('rates')) {
        db.createObjectStore('rates', { keyPath: 'id' });
      }

      if (!db.objectStoreNames.contains('offline_expenses')) {
        db.createObjectStore('offline_expenses', { keyPath: 'temp_id', autoIncrement: true });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = (event) => reject(event.target.error);
  });

export const saveCachedRates = async (ratesMatrix) => {
  const db = await initDB();
  const tx = db.transaction('rates', 'readwrite');
  tx.objectStore('rates').put({ id: 'active_rates', matrix: ratesMatrix, updatedAt: new Date() });
  return tx.complete;
};

export const getCachedRates = async () => {
  const db = await initDB();
  return new Promise((resolve) => {
    const tx = db.transaction('rates', 'readonly');
    const request = tx.objectStore('rates').get('active_rates');
    request.onsuccess = () => resolve(request.result?.matrix || null);
    request.onerror = () => resolve(null);
  });
};

export const queueOfflineExpense = async (expenseData) => {
  const db = await initDB();
  const tx = db.transaction('offline_expenses', 'readwrite');
  tx.objectStore('offline_expenses').add({
    ...expenseData,
    created_at_offline: new Date().toISOString(),
  });
  return tx.complete;
};

export const getQueuedExpenses = async () => {
  const db = await initDB();
  return new Promise((resolve) => {
    const tx = db.transaction('offline_expenses', 'readonly');
    const request = tx.objectStore('offline_expenses').getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => resolve([]);
  });
};

export const clearQueuedExpense = async (tempId) => {
  const db = await initDB();
  const tx = db.transaction('offline_expenses', 'readwrite');
  tx.objectStore('offline_expenses').delete(tempId);
  return tx.complete;
};
