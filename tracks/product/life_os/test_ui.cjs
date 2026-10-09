// Synthetic, login-free chat preview at phone, tablet, and desktop widths.
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const net = require('node:net');
const assert = require('node:assert/strict');
const { join } = require('node:path');

const root = __dirname;
function freePort() {
  return new Promise(resolve => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });
}

async function main() {
  const port = await freePort();
  const origin = `http://127.0.0.1:${port}`;
  const server = spawn('python3', [join(root, 'server.py')], {
    env: {...process.env, LIFE_OS_PORT: String(port)}, stdio: 'ignore',
  });
  let browser;
  try {
    for (let i = 0; i < 50; i++) {
      try { if ((await fetch(origin)).ok) break; } catch {}
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    browser = await chromium.launch({headless: true, executablePath: '/usr/bin/chromium', args: ['--no-sandbox']});
    for (const [label, width] of [['phone', 390], ['tablet', 768], ['pc', 1280]]) {
      const context = await browser.newContext({viewport: {width, height: 850}});
      const page = await context.newPage();
      await Promise.all([page.waitForResponse('**/fixtures/first_flow.synthetic.json'), page.goto(origin)]);
      assert.equal(await page.locator('input[type=password]').count(), 0);
      await page.getByRole('heading', {name: '지금 무엇이 궁금하세요?'}).waitFor();

      await page.getByRole('button', {name: '자료 없이 질문하기'}).click();
      await page.getByText('최근 며칠 저녁 시간이 얼마나 들쭉날쭉했나요?', {exact: false}).waitFor();
      if (label === 'phone') {
        await page.locator('#thread').evaluate(node => { node.scrollTop = 0; });
        await page.screenshot({path: '/tmp/life-os-chat-first-phone.png'});
      }
      await page.getByRole('button', {name: '고려해 볼게'}).click();
      await page.getByText('실행: 아직 모름 · 체감: 아직 모름', {exact: false}).waitFor();

      await page.getByRole('button', {name: '두 시점 자료 살펴보기'}).click();
      await page.getByText('수치 차이의 원인', {exact: false}).waitFor();
      await page.getByText('두 번의 측정이 같은 기기와 비슷한 조건에서 이루어졌는지', {exact: false}).waitFor();

      if (width <= 720) await page.locator('#history-drawer summary').click();
      await page.getByRole('button', {name: '새 대화'}).click();
      await page.locator('#message').fill('퇴근하면 저녁을 챙길 여유가 없어요. 무엇부터 살펴볼까요?');
      await page.getByRole('button', {name: '보내기'}).click();
      await page.getByText('최근 며칠 저녁 시간이 얼마나 들쭉날쭉했나요?', {exact: false}).waitFor();
      await page.getByRole('button', {name: '지금은 맞지 않아'}).click();
      await page.locator('#message').fill('시간이 계속 바뀌어요.');
      await page.getByRole('button', {name: '보내기'}).click();
      await page.getByText('앞의 제안이 지금 맞지 않았던 이유를', {exact: false}).waitFor();

      const geometry = await page.evaluate(() => ({scroll: document.documentElement.scrollWidth, viewport: innerWidth}));
      assert.ok(geometry.scroll <= geometry.viewport, `${label}: horizontal overflow ${JSON.stringify(geometry)}`);
      if (label === 'phone') await page.screenshot({path: '/tmp/life-os-chat-phone.png'});
      if (label === 'pc') await page.screenshot({path: '/tmp/life-os-chat-pc.png'});
      await page.reload();
      await page.getByRole('heading', {name: '지금 무엇이 궁금하세요?'}).waitFor();
      assert.match(await page.locator('#case-list').textContent(), /아직 대화가 없습니다/);
      console.log(`${label} ${width}px: chat, evidence, feedback, follow-up; no login or overflow`);
      await context.close();
    }
  } finally {
    if (browser) await browser.close();
    server.kill('SIGTERM');
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
