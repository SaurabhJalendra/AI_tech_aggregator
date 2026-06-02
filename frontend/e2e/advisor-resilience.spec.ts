import { test, expect } from '@playwright/test';

test.describe('Advisor browser resilience', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/chat', async (route) => {
      const body =
        'data: {"type":"meta","session_id":"e2e-session"}\n\n' +
        'data: {"type":"text","content":"Deterministic comparison ready."}\n\n' +
        'data: {"type":"panel_command","command":{"action":"render","panel":"option_cards","source":"planner","data":{"question_id":"budget","question":"What is your budget?","options":[{"id":"low","label":"Low","metadata":{"budget":"low"}}]}}}\n\n' +
        'data: {"type":"done"}\n\n';
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body,
      });
    });
  });

  test('completes stream and unlocks input', async ({ page }) => {
    await page.goto('/advisor');
    const input = page.getByPlaceholder(/ask|message|type/i).first();
    await input.fill('compare vector databases');
    await input.press('Enter');

    await expect(page.getByText(/Deterministic comparison/i)).toBeVisible({ timeout: 15_000 });
    await expect(input).toBeEnabled({ timeout: 5_000 });
  });

  test('negotiation option cards are clickable after stream', async ({ page }) => {
    await page.goto('/advisor');
    const input = page.getByPlaceholder(/ask|message|type/i).first();
    await input.fill('compare vector databases');
    await input.press('Enter');
    await expect(page.getByText(/budget/i).first()).toBeVisible({ timeout: 15_000 });
    const lowOption = page.getByRole('button', { name: /low/i }).first();
    await expect(lowOption).toBeEnabled();
  });

  test('rapid refresh recovers UI', async ({ page }) => {
    await page.goto('/advisor');
    await page.reload();
    const input = page.getByPlaceholder(/ask|message|type/i).first();
    await expect(input).toBeVisible();
    await expect(input).toBeEnabled();
  });
});
