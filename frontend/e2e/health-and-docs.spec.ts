import { test, expect } from '@playwright/test';

test.describe('Health & Documentation Endpoints', () => {
  test('health check returns healthy status', async ({ request }) => {
    const response = await request.get('/api/users/health/');
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe('healthy');
  });

  test('OpenAPI schema is accessible', async ({ request }) => {
    const response = await request.get('/api/schema/');
    expect(response.ok()).toBeTruthy();
  });

  test('Swagger UI loads', async ({ page }) => {
    await page.goto('/api/docs/');
    await expect(page).toHaveTitle(/Swagger/i);
  });

  test('ReDoc loads', async ({ page }) => {
    await page.goto('/api/redoc/');
    await page.waitForSelector('text=USERinator API');
    await expect(page.locator('text=USERinator API')).toBeVisible();
  });
});
