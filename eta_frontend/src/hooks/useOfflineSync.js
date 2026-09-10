import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

import { clearQueuedExpense, getCachedRates, getQueuedExpenses, saveCachedRates } from '../services/db';

export const useOfflineSync = (client = axios) => {
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [rates, setRates] = useState(null);
  const [queuedCount, setQueuedCount] = useState(0);

  const updateQueuedCount = useCallback(async () => {
    const items = await getQueuedExpenses();
    setQueuedCount(items.length);
  }, []);

  const refreshRates = useCallback(async () => {
    if (typeof navigator !== 'undefined' && navigator.onLine) {
      try {
        const response = await client.get('/rates/current/');
        const data = response.data;
        setRates(data);
        await saveCachedRates(data);
      } catch (error) {
        console.warn('Failed to fetch live rates. Using local cache.', error);
        const cached = await getCachedRates();
        setRates(cached);
      }
    } else {
      const cached = await getCachedRates();
      setRates(cached);
    }
  }, [client]);

  const syncOfflineQueue = useCallback(async () => {
    const queuedItems = await getQueuedExpenses();
    if (!queuedItems.length) return;

    setIsSyncing(true);

    for (const item of queuedItems) {
      try {
        const { temp_id, created_at_offline, ...payload } = item;
        await client.post('/expenses/', payload);
        await clearQueuedExpense(temp_id);
      } catch (error) {
        console.error(`Failed to sync item ${item.temp_id}:`, error);
        break;
      }
    }

    setIsSyncing(false);
    await updateQueuedCount();
  }, [client, updateQueuedCount]);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      refreshRates();
      syncOfflineQueue();
    };

    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    refreshRates();
    updateQueuedCount();
    if (typeof navigator !== 'undefined' && navigator.onLine) {
      syncOfflineQueue();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [refreshRates, syncOfflineQueue, updateQueuedCount]);

  return { isOnline, isSyncing, rates, queuedCount, refreshRates, syncOfflineQueue, updateQueuedCount };
};
