import fs from 'node:fs';import path from 'node:path';import os from 'node:os';import assert from 'node:assert/strict';import {spawn} from 'node:child_process';import {pathToFileURL} from 'node:url';
const {chromium}=await import(pathToFileURL(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs')).href);
const out=path.resolve('output/portrait-interactive');const browser=await chromium.launch({executablePath:path.join(process.env['ProgramFiles(x86)'],'Microsoft/Edge/Application/msedge.exe'),headless:true,args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const errors=[],checks=[];let server;
try{
 const p=await browser.newPage({viewport:{width:1440,height:1000}});p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 const requests=[];p.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});await p.goto(pathToFileURL(path.join(out,'少女交互动画.html')).href);await p.waitForSelector('[data-renderer=pixi]');
 const position=async(page,x,y=.42)=>page.evaluate(([x,y])=>{const r=document.querySelector('.cover-art').getBoundingClientRect(),s=Math.min(r.width/1536,r.height/1024);return {x:r.x+(r.width-s*1536)/2+s*1536*x,y:r.y+(r.height-s*1024)/2+s*1024*y};},[x,y]);
 for(const [state,x] of [['puzzled',.40],['curious',.52],['happy',.65]]){const pt=await position(p,x);await p.mouse.move(pt.x,pt.y);await p.waitForFunction(s=>document.querySelector('#intro-dialog').dataset.expression===s,state);await p.waitForTimeout(1200);await p.screenshot({path:path.join(out,state+'.png')});}
 await p.mouse.move(1,1);await p.waitForFunction(()=>document.querySelector('#intro-dialog').dataset.expression==='idle');checks.push('Face-relative left / center / right expressions and return to idle');
 assert.equal(await p.locator('[data-portrait-blink]').count(),0);
 await p.locator('[data-portrait-expression=happy]').click();await p.waitForTimeout(700);assert.equal(await p.locator('#intro-dialog').getAttribute('data-expression'),'happy');await p.locator('[data-portrait-pause]').click();const gaze=()=>p.locator('#cover-stage').evaluate(el=>el.style.getPropertyValue('--look-x'));const frozen=await gaze();assert(Number(frozen)>.1);await p.waitForTimeout(400);assert.equal(await gaze(),frozen);checks.push('Accessible expression previews and animation pause');
 assert.equal(requests.length,0);checks.push('file:// offline execution without HTTP requests');
 await p.setViewportSize({width:390,height:844});await p.screenshot({path:path.join(out,'mobile.png')});for(const el of await p.locator('.controls button,[data-portrait-pause]').all()){const r=await el.boundingBox();assert(r.x>=0&&r.y>=0&&r.x+r.width<=390&&r.y+r.height<=844);}
 checks.push('Mobile controls fit viewport');
 server=spawn('python',['-X','utf8','run.py','--port','8775'],{windowsHide:true,stdio:'ignore',env:{...process.env,GUIDE_ALLOW_REMOTE_LLM:'false',GUIDE_DATA_DIR:path.join(out,'test-data')}});
 for(let i=0;i<80;i++){try{if((await fetch('http://127.0.0.1:8775/api/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,150));}
 const cover=await browser.newPage({viewport:{width:1440,height:1000}});cover.on('pageerror',e=>errors.push(e.message));cover.on('console',m=>{if(m.type()==='error')errors.push(m.text());});await cover.goto('http://127.0.0.1:8775/?cover=1');await cover.waitForSelector('#intro-dialog.intro-settled[data-renderer=pixi]');
 for(const [state,x] of [['puzzled',.40],['curious',.52],['happy',.65]]){
   const pt=await position(cover,x);await cover.mouse.move(pt.x,pt.y);
   await cover.waitForFunction(s=>document.querySelector('#intro-dialog').dataset.expression===s,state);
 }
 await cover.mouse.move(1,1);await cover.waitForFunction(()=>document.querySelector('#intro-dialog').dataset.expression==='idle');await cover.screenshot({path:path.join(out,'project-cover.png')});await cover.locator('#intro-enter').click();await cover.waitForSelector('body.journey-active');checks.push('Project cover responds to pointer regions and opens guide');
 const reduced=await browser.newPage({viewport:{width:1280,height:800},reducedMotion:'reduce'});await reduced.goto(pathToFileURL(path.join(out,'少女交互动画.html')).href);await reduced.waitForFunction(()=>document.querySelector('.intro-portrait').naturalWidth>0);assert.equal(await reduced.locator('.cover-canvas').count(),0);checks.push('Reduced-motion static fallback');
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({success:true,checks,errors,requests},null,2));console.log('PASS '+checks.join('; '));
}finally{await browser.close();server?.kill();}
