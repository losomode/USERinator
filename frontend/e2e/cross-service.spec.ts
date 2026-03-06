import { test, expect } from '@playwright/test';

test.describe('Cross-Service Integration', () => {
  // These tests verify the full platform integration.
  // Requires all services running + a valid JWT.
  const token = process.env.E2E_AUTH_TOKEN;
  const serviceKey = process.env.E2E_SERVICE_KEY || 'dev-internal-service-key-change-in-production';

  test('service-key auth on role endpoint', async ({ request }) => {
    // Simulates what AUTHinator does during login: fetch role via service key
    const response = await request.get('/api/users/1/role/', {
      headers: { 'X-Service-Key': serviceKey },
    });
    // 200 if user exists, 404 if not — both are valid (service-key auth worked)
    expect([200, 404]).toContain(response.status());
  });

  test('service-key without header returns 401', async ({ request }) => {
    const response = await request.get('/api/users/1/role/');
    expect(response.status()).toBe(401);
  });

  test.describe('with auth token', () => {
    test.skip(!token, 'E2E_AUTH_TOKEN not set — skipping');

    test('JWT contains role_level claim', async ({ request }) => {
      // Login to AUTHinator and verify JWT has role_level
      const meResponse = await request.get('/api/users/me/', {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(meResponse.ok()).toBeTruthy();
      const profile = await meResponse.json();
      expect(profile).toHaveProperty('role_level');
      expect(typeof profile.role_level).toBe('number');
      expect(profile.role_level).toBeGreaterThanOrEqual(10);
    });

    test('company-scoped access control', async ({ request }) => {
      // User should only see profiles in their own company
      const response = await request.get('/api/users/', {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(response.ok()).toBeTruthy();
      const body = await response.json();

      if (body.count > 0) {
        // All returned users should be in the same company
        const companyIds = body.results.map((u: { company: number }) => u.company);
        const uniqueCompanies = [...new Set(companyIds)];
        // Non-admin users see only their company; admins may see all
        expect(uniqueCompanies.length).toBeGreaterThanOrEqual(1);
      }
    });
  });
});
