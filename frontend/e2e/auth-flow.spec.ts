import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('unauthenticated API requests return 401', async ({ request }) => {
    const response = await request.get('/api/users/');
    expect(response.status()).toBe(401);
  });

  test('unauthenticated users/me returns 401', async ({ request }) => {
    const response = await request.get('/api/users/me/');
    expect(response.status()).toBe(401);
  });

  test('unauthenticated companies returns 401', async ({ request }) => {
    const response = await request.get('/api/companies/');
    expect(response.status()).toBe(401);
  });

  test('unauthenticated roles returns 401', async ({ request }) => {
    const response = await request.get('/api/roles/');
    expect(response.status()).toBe(401);
  });

  test('unauthenticated invitations returns 401', async ({ request }) => {
    const response = await request.get('/api/invitations/');
    expect(response.status()).toBe(401);
  });
});

test.describe('Authenticated API Access', () => {
  // These tests require a valid JWT from AUTHinator.
  // Set E2E_AUTH_TOKEN env var or run after logging in via the UI.
  const token = process.env.E2E_AUTH_TOKEN;

  test.skip(!token, 'E2E_AUTH_TOKEN not set — skipping authenticated tests');

  test('GET /api/users/me/ returns user profile', async ({ request }) => {
    const response = await request.get('/api/users/me/', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('user_id');
    expect(body).toHaveProperty('username');
    expect(body).toHaveProperty('role_name');
    expect(body).toHaveProperty('role_level');
  });

  test('GET /api/users/ returns paginated list', async ({ request }) => {
    const response = await request.get('/api/users/', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('count');
    expect(body).toHaveProperty('results');
    expect(Array.isArray(body.results)).toBeTruthy();
  });

  test('GET /api/roles/ returns role definitions', async ({ request }) => {
    const response = await request.get('/api/roles/', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('results');
    const roleNames = body.results.map((r: { role_name: string }) => r.role_name);
    expect(roleNames).toContain('ADMIN');
    expect(roleNames).toContain('MEMBER');
  });

  test('GET /api/companies/my/ returns user company', async ({ request }) => {
    const response = await request.get('/api/companies/my/', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('name');
  });
});
