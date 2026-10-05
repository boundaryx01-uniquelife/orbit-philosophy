// Responsive browser smoke check with a temporary database and synthetic account.
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const { mkdtempSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const net = require('node:net');
const assert = require('node:assert/strict');
const root = __dirname;
const temp = mkdtempSync(join(tmpdir(), 'life-os-ui-'));
function freePort(){return new Promise(resolve=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port));});});}
async function main(){
  const port=await freePort(), origin=`http://127.0.0.1:${port}`;
  const server=spawn('python3',[join(root,'server.py')],{env:{...process.env,LIFE_OS_DB:join(temp,'db.sqlite3'),LIFE_OS_PORT:String(port)},stdio:'ignore'});
  let browser;
  try{
    for(let i=0;i<50;i++){try{const r=await fetch(origin);if(r.ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
    browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
    for(const [label,width] of [['phone',390],['tablet',768],['pc',1280]]){
      const context=await browser.newContext({viewport:{width,height:850}}),page=await context.newPage();
      await page.goto(origin);
      await page.locator('#workspace').waitFor({state:'visible'});
      assert.equal(await page.locator('#auth').isVisible(),false);
      assert.ok(await page.getByText('합성 사례 체험',{exact:false}).isVisible());
      assert.ok(await page.locator('#case-list').getByText('오후에 자주 지치는데',{exact:false}).isVisible());
      assert.ok(await page.locator('#case-list').getByText('두 번의 신체 구성 기록',{exact:false}).isVisible());
      if(label==='phone'){
        await page.locator('#case-form textarea').fill('오후에 지칠 때 무엇을 살펴볼까요?');
        await page.locator('#case-form button').click();
        await page.getByText('자료가 없어도 괜찮습니다.',{exact:false}).last().waitFor();
        await page.locator('.proposal select[name=reaction]').selectOption('consider');
        await page.getByRole('button',{name:'반응 저장'}).click();
      }
      await page.locator('.proposal').waitFor({state:'visible'});
      assert.equal(await page.locator('.proposal select[name=reaction]').inputValue(),'consider');
      assert.equal(await page.locator('.proposal select[name=did_act]').inputValue(),'unknown');
      const geometry=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
      assert.ok(geometry.scroll<=geometry.viewport,`${label}: horizontal overflow ${JSON.stringify(geometry)}`);
      for(const text of ['새 이야기','조심스러운 제안','이전 이야기'])assert.ok(await page.getByRole('heading',{name:text,exact:true}).isVisible(),`${label}: ${text}`);
      if(label==='pc'){
        await page.getByRole('button',{name:'지금 정보로 다시 살펴보기'}).click();
        await page.getByText('지난 제안과 반응 1개').click();
        assert.equal(await page.locator('details .proposal select[name=reaction]').inputValue(),'consider');
      }
      console.log(`${label} ${width}px: start, proposal, history visible; no horizontal overflow`);
      await context.close();
    }
  }finally{if(browser)await browser.close();server.kill('SIGTERM');rmSync(temp,{recursive:true,force:true});}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
