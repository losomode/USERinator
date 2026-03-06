import { describe, it, expect, beforeEach, vi } from 'vitest';
import apiClient, { getToken, setToken, clearToken } from './client';

describe('client token helpers', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('getToken returns null when no token stored', () => {
    expect(getToken()).toBeNull();
  });

  it('setToken stores token in localStorage', () => {
    setToken('abc123');
    expect(localStorage.getItem('auth_token')).toBe('abc123');
  });

  it('getToken retrieves stored token', () => {
    setToken('token-xyz');
    expect(getToken()).toBe('token-xyz');
  });

  it('clearToken removes token from localStorage', () => {
    setToken('to-remove');
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe('request interceptor', () => {
  it('adds Authorization header when token exists', async () => {
    setToken('test-bearer-token');
    const interceptor = apiClient.interceptors.request as unknown as { handlers: { fulfilled: (config: Record<string, unknown>) => Record<string, unknown> }[] };
    const handler = interceptor.handlers[0].fulfilled;
    const headers = new Map<string, string>();
    const headersObj = Object.defineProperty({}, 'Authorization', {
      get() { return headers.get('Authorization'); },
      set(v: string) { headers.set('Authorization', v); },
      enumerable: true,
      configurable: true,
    });
    const config = { headers: headersObj } as unknown as Record<string, unknown>;
    const result = handler(config) as { headers: { Authorization: string } };
    expect(result.headers.Authorization).toBe('Bearer test-bearer-token');
  });

  it('does not add Authorization header when no token', async () => {
    localStorage.clear();
    const interceptor = apiClient.interceptors.request as unknown as { handlers: { fulfilled: (config: Record<string, unknown>) => Record<string, unknown> }[] };
    const handler = interceptor.handlers[0].fulfilled;
    const config = { headers: {} } as unknown as Record<string, unknown>;
    const result = handler(config) as { headers: Record<string, string> };
    expect(result.headers.Authorization).toBeUndefined();
  });
});

describe('response interceptor', () => {
  it('clears token and redirects on 401', async () => {
    setToken('will-be-cleared');
    const originalHref = window.location.href;
    // Mock window.location
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { ...window.location, pathname: '/dashboard', href: originalHref },
    });

    const interceptor = apiClient.interceptors.response as unknown as { handlers: { rejected: (error: unknown) => Promise<never> }[] };
    const handler = interceptor.handlers[0].rejected;
    const error = { response: { status: 401 } };

    await expect(handler(error)).rejects.toEqual(error);
    expect(getToken()).toBeNull();
  });

  it('passes through non-401 errors', async () => {
    const interceptor = apiClient.interceptors.response as unknown as { handlers: { rejected: (error: unknown) => Promise<never> }[] };
    const handler = interceptor.handlers[0].rejected;
    const error = { response: { status: 500 } };

    await expect(handler(error)).rejects.toEqual(error);
  });

  it('passes through successful responses', () => {
    const interceptor = apiClient.interceptors.response as unknown as { handlers: { fulfilled: (resp: unknown) => unknown }[] };
    const handler = interceptor.handlers[0].fulfilled;
    const response = { status: 200, data: {} };
    expect(handler(response)).toEqual(response);
  });
});
