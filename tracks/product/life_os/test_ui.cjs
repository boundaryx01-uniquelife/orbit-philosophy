// Responsive browser smoke check with a temporary database and synthetic account.
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const { mkdtempSync, rmSync, readFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const net = require('node:net');
const assert = require('node:assert/strict');
const { randomBytes } = require('node:crypto');
const root = __dirname;
const question = JSON.parse(readFileSync(join(root,'fixtures','first_flow.synthetic.json'),'utf8'))[0].case.question;
const temp = mkdtempSync(join(tmpdir(), 'life-os-ui-'));
function freePort(){return new Promise(resolve=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port));});});}
async function main(){
  const port=await freePort(), origin=`http://127.0.0.1:${port}`;
  const password=randomBytes(18).toString('base64url');
  const server=spawn('python3',[join(root,'server.py')],{env:{...process.env,LIFE_OS_DB:join(temp,'db.sqlite3'),LIFE_OS_PORT:String(port)},stdio:'ignore'});
  let browser;
  try{
    for(let i=0;i<50;i++){try{const r=await fetch(origin);if(r.ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
    browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
    for(const [label,width] of [['phone',390],['tablet',768],['pc',1280]]){
      const context=await browser.newContext({viewport:{width,height:850}}),page=await context.newPage();
      await page.goto(origin);
      await page.locator('#auth input[name=name]').fill('synthetic-browser');
      await page.locator('#auth input[name=password]').fill(password);
      await page.getByRole('button',{name:label==='phone'?'새 계정 만들기':'로그인'}).click();
      await page.locator('#workspace').waitFor({state:'visible'});
      if(label==='phone'){
        await page.locator('#case-form textarea').fill(question);
        await page.route('**/api/cases',route=>route.request().method()==='POST'?route.abort():route.continue());
        await page.locator('#case-form button').click();
        await page.getByText('서버에 연결할 수 없습니다.',{exact:false}).waitFor();
        assert.equal(await page.locator('#case-form textarea').inputValue(),question);
        await page.unroute('**/api/cases');
        await page.locator('#case-form button').click();
        await page.getByText('저녁 시간이 얼마나 들쭉날쭉했나요?',{exact:false}).waitFor();
        await page.locator('.proposal select[name=reaction]').selectOption('consider');
        await page.getByRole('button',{name:'반응 저장'}).click();
        await page.evaluate(()=>scrollTo(0,0));
        await page.screenshot({path:'/tmp/life-os-phone.png'});
      }
      await page.locator('.proposal').waitFor({state:'visible'});
      assert.equal(await page.locator('.proposal select[name=reaction]').inputValue(),'consider');
      assert.equal(await page.locator('.proposal select[name=did_act]').inputValue(),'unknown');
      const geometry=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
      assert.ok(geometry.scroll<=geometry.viewport,`${label}: horizontal overflow ${JSON.stringify(geometry)}`);
      for(const text of ['새 이야기','조심스러운 제안','이전 이야기'])assert.ok(await page.getByRole('heading',{name:text,exact:true}).isVisible(),`${label}: ${text}`);
      await page.getByRole('link',{name:'이전 이야기'}).click();
      assert.equal(new URL(page.url()).hash,'#stories');
      if(label==='pc'){
        await page.getByRole('button',{name:'지금 정보로 다시 살펴보기'}).click();
        await page.getByText('지난 제안과 반응 1개').click();
        assert.equal(await page.locator('details .proposal select[name=reaction]').inputValue(),'consider');
        await page.evaluate(()=>scrollTo(0,0));
        await page.screenshot({path:'/tmp/life-os-pc.png'});
      }
      console.log(`${label} ${width}px: start, proposal, history visible; no horizontal overflow`);
      await context.close();
    }
  }finally{if(browser)await browser.close();server.kill('SIGTERM');rmSync(temp,{recursive:true,force:true});}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
