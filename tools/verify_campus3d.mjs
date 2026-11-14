import path from 'node:path';
import os from 'node:os';
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
const {chromium}=await import(pathToFileURL(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs')).href);
const out=path.resolve('output/campus3d');fs.mkdirSync(out,{recursive:true});
const server=spawn('python',['-X','utf8','run.py','--port','8767'],{cwd:process.cwd(),windowsHide:true,stdio:'ignore',env:{...process.env,GUIDE_ALLOW_REMOTE_LLM:'false',GUIDE_DATA_DIR:path.join(out,'test-data')}});
for(let i=0;i<80;i++){try{if((await fetch('http://127.0.0.1:8767/api/health')).ok)break}catch{}await new Promise(r=>setTimeout(r,150));}
const browser=await chromium.launch({executablePath:path.join(process.env['ProgramFiles(x86)'],'Microsoft/Edge/Application/msedge.exe'),headless:true,args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const errors=[];
try{
 const page=await browser.newPage({viewport:{width:1440,height:980}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8767/campus3d/');await page.waitForSelector('#scene canvas');await page.waitForFunction(()=>!document.querySelector('#loading'));await page.waitForTimeout(1500);
 assert.equal(await page.locator('.place-row').count(),30);assert.equal(await page.locator('#detail h2').textContent(),'图书馆');
 await page.screenshot({path:path.join(out,'campus-desktop.png')});
 await page.locator('#search').fill('馨园');assert.equal(await page.locator('.place-row').count(),5);await page.locator('.place-row').first().click();await page.locator('#indoor-open').click();assert(await page.locator('#indoor').evaluate(el=>el.open));
 await page.locator('[data-room=liuren]').click();await page.locator('[data-photo=plan]').click();await page.waitForFunction(()=>document.querySelector('#room-photo').complete&&document.querySelector('#room-photo').naturalWidth>0);assert((await page.locator('#room-photo').getAttribute('src')).includes('liuren-plan'));await page.screenshot({path:path.join(out,'campus-indoor.png')});await page.locator('[data-close=indoor]').click();
 await page.locator('#search').fill('不存在的地点');assert.equal(await page.locator('.place-row').count(),0);await page.locator('#search').fill('');await page.locator('#filters button').filter({hasText:'学习'}).click();assert.equal(await page.locator('.place-row').count(),11);await page.locator('#filters button').filter({hasText:'全部'}).click();
 // Project a building center, then exercise actual 3D ray picking.
 const hit=await page.evaluate(()=>{destination=null;target.set(0,0,8);zoom=1;updateCamera();const p=places.find(p=>p.name==='厚德楼');const v=new THREE.Vector3(p.x-50,p.height/2,(p.z-50)*1.1).project(camera);const r=renderer.domElement.getBoundingClientRect();return {x:r.left+(v.x/2+.5)*r.width,y:r.top+(-v.y/2+.5)*r.height}});await page.mouse.click(hit.x,hit.y);assert.equal(await page.locator('#detail h2').textContent(),'厚德楼');
 await page.locator('#top').click();assert.equal(await page.locator('#top').getAttribute('aria-pressed'),'true');await page.locator('#label-toggle').click();await page.waitForTimeout(100);assert.equal(await page.locator('.map-label:visible').count(),0);await page.locator('#label-toggle').click();await page.locator('#reset').click();
 await page.locator('#sources-open').click();assert(await page.locator('#sources').evaluate(el=>el.open));await page.locator('[data-close=sources]').click();
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});mobile.on('pageerror',e=>errors.push(e.message));await mobile.goto('http://127.0.0.1:8767/campus3d/');await mobile.waitForFunction(()=>!document.querySelector('#loading'));await mobile.waitForTimeout(800);assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await mobile.screenshot({path:path.join(out,'campus-mobile.png')});
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({success:true,places:30,checks:['WebGL render','search and empty state','category filters','building ray picking','photo reference switching','camera controls','source dialog','mobile layout'],errors},null,2));console.log('PASS: 30 locations, WebGL, 3D picking, search, filters, indoor photos, camera controls, dialogs, mobile.');
}finally{await browser.close();server.kill()}
