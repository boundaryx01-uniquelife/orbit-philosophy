const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const { mkdtempSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const net = require('node:net');
const assert = require('node:assert/strict');

const temp = mkdtempSync(join(tmpdir(), 'shopping-ui-'));
function freePort(){return new Promise(resolve=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port));});});}
async function main(){
  const port=await freePort(), origin=`http://127.0.0.1:${port}`;
  const server=spawn('python3',[join(__dirname,'server.py')],{env:{...process.env,SHOPPING_DEMO_DB:join(temp,'db.sqlite3'),SHOPPING_DEMO_PORT:String(port)},stdio:'ignore'});
  let browser;
  try{
    for(let i=0;i<60;i++){try{const r=await fetch(origin+'/api/state');if(r.ok)break;}catch{}await new Promise(r=>setTimeout(r,50));}
    browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
    for(const width of [390,768,1280]){
      const context=await browser.newContext({viewport:{width,height:850}}),page=await context.newPage();
      await page.goto(origin);
      await page.getByRole('heading',{name:'두 후보, 무엇이 다른가요?'}).waitFor();
      assert.ok(await page.getByText('케이스형 보호대').isVisible());
      if(width===390){
        await page.getByRole('button',{name:'측면·모서리까지 보호'}).click();
        await page.getByRole('heading',{name:'케이스형 후보를 먼저 확인하세요'}).waitFor();
        await page.getByText('현재 조건 · 이 구매 건').waitFor();
        await page.locator('.feedback-panel summary').click();
        await page.locator('#reaction').selectOption('consider');
        await page.getByRole('button',{name:'반응 저장'}).click();
        await page.getByText('저장되었습니다.').waitFor();
      }else{
        await page.getByRole('heading',{name:'케이스형 후보를 먼저 확인하세요'}).waitFor();
        assert.equal(await page.locator('#reaction').inputValue(),'consider');
        assert.equal(await page.locator('#purchased').inputValue(),'unknown');
      }
      const geometry=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
      assert.ok(geometry.scroll<=geometry.viewport,`${width}px horizontal overflow: ${JSON.stringify(geometry)}`);
      if(width===390 || width===1280)await page.screenshot({path:join('/tmp',`shopping-detail-${width}.png`),fullPage:true});
      if(width===1280){
        const lastUser=page.locator('.turn.user').last();
        await lastUser.getByRole('button',{name:'수정'}).click();
        await lastUser.locator('.edit textarea').fill('이번에는 얇은 착용감을 우선합니다.');
        await lastUser.locator('.edit select').selectOption('film');
        await lastUser.getByRole('button',{name:'수정 저장'}).click();
        await page.getByRole('heading',{name:'필름형 후보를 먼저 확인하세요'}).waitFor();
        page.once('dialog',dialog=>dialog.accept());
        await page.locator('.turn.user').last().getByRole('button',{name:'삭제'}).click();
        await page.getByRole('heading',{name:'원하는 보호 범위를 알려주세요'}).waitFor();
      }
      console.log(`${width}px: detail, conversation source, feedback, no horizontal overflow`);
      await context.close();
    }
  }finally{if(browser)await browser.close();server.kill('SIGTERM');rmSync(temp,{recursive:true,force:true});}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
