import React from 'react';
import 'fake-indexeddb/auto';
import '@testing-library/jest-dom/vitest';

vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');

  return {
    ...actual,
    ResponsiveContainer: ({ children, width = 800, height = 400 }) =>
      React.createElement('div', { style: { width, height } }, children),
  };
});

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock;

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
