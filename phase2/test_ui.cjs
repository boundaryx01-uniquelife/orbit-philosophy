// Browser check with a synthetic model endpoint. No real product or API key is used.
const { chromium } = require('playwright');
const { createServer } = require('node:http');
const { spawn } = require('node:child_process');
const { mkdtempSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const net = require('node:net');
const assert = require('node:assert/strict');

const root=join(__dirname,'..'),temp=mkdtempSync(join(tmpdir(),'phase2-ui-'));
function freePort(){return new Promise(resolve=>{const socket=net.createServer();socket.listen(0,'127.0.0.1',()=>{const port=socket.address().port;socket.close(()=>resolve(port))})})}
async function main(){
  const appPort=await freePort(),modelPort=await freePort(),origin=`http://127.0.0.1:${appPort}`;
  let calls=0;
  const model=createServer((req,res)=>{
    let raw='';req.on('data',chunk=>raw+=chunk);req.on('end',()=>{
      const request=JSON.parse(raw),last=request.messages.at(-1).content;calls++;
      const first=last.includes('전자 기기');
      const answer=first?{reply:'지금은 링크의 가격을 확인할 수 없습니다. 측면 보호가 우선인가요?',memory_candidates:[{text:'이번 기기에서 측면 보호를 우선함',scope:'thread'}],referenced_evidence_ids:[]}:
        {reply:'앞서 확인된 공통 조건을 살펴보고 의자 사용 시간을 물어보겠습니다.',memory_candidates:[],referenced_evidence_ids:[]};
      res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({choices:[{message:{content:JSON.stringify(answer)}}]}));
    });
  });
  await new Promise(resolve=>model.listen(modelPort,'127.0.0.1',resolve));
  const server=spawn('python3',['-m','phase2.app.server'],{cwd:root,env:{...process.env,PHASE2_DB:join(temp,'db.sqlite3'),PHASE2_PORT:String(appPort),PHASE2_MODEL_API_KEY:'synthetic-test-only',PHASE2_MODEL_NAME:'synthetic-test',PHASE2_MODEL_API_URL:`http://127.0.0.1:${modelPort}/chat/completions`},stdio:'ignore'});
  let browser;
  try{
    for(let i=0;i<70;i++){try{if((await fetch(origin+'/api/bootstrap')).ok)break}catch{}await new Promise(resolve=>setTimeout(resolve,50))}
    browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
    const context=await browser.newContext({viewport:{width:390,height:850}}),page=await context.newPage();
    await page.goto(origin);
    await page.getByRole('heading',{name:'무엇을 고르고 계세요?'}).waitFor();
    await page.locator('#message').fill('전자 기기 케이스를 고르고 싶어요.');
    await page.getByRole('button',{name:'보내기'}).click();
    await page.getByText('측면 보호가 우선인가요?',{exact:false}).waitFor();
    await page.getByText('다음 판단에도 이 내용을 참고할까요?').waitFor();
    assert.equal(calls,1);
    await page.screenshot({path:'/tmp/phase2-phone.png',fullPage:true});
    await page.getByRole('button',{name:'기억하기'}).click();
    await page.getByText('다음 판단에도 이 내용을 참고할까요?').waitFor({state:'hidden'});

    for(const width of [390,820,1280]){
      await page.setViewportSize({width,height:850});
      const widthCheck=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
      assert.ok(widthCheck.scroll<=widthCheck.viewport,`${width}px overflow ${JSON.stringify(widthCheck)}`);
      if(width===820)await page.screenshot({path:'/tmp/phase2-tablet.png',fullPage:true});
      console.log(`${width}px: chat, evidence context and composer fit`);
    }
    await context.close();
  }finally{if(browser)await browser.close();server.kill('SIGTERM');await new Promise(resolve=>model.close(resolve));rmSync(temp,{recursive:true,force:true})}
}
main().catch(error=>{console.error(error);process.exitCode=1});
