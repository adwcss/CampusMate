import path from 'node:path';import os from 'node:os';import fs from 'node:fs';import assert from 'node:assert/strict';import {spawn} from 'node:child_process';import {pathToFileURL} from 'node:url';
const {chromium}=await import(pathToFileURL(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs')).href);
const out=path.resolve('output/journey');fs.mkdirSync(out,{recursive:true});const server=spawn('python',['-X','utf8','run.py','--port','8772'],{windowsHide:true,stdio:'ignore',env:{...process.env,GUIDE_ALLOW_REMOTE_LLM:'false',GUIDE_DATA_DIR:path.join(out,'test-data')}});
for(let i=0;i<80;i++){try{if((await fetch('http://127.0.0.1:8772/api/health')).ok)break}catch{}await new Promise(r=>setTimeout(r,150))}
const browser=await chromium.launch({executablePath:path.join(process.env['ProgramFiles(x86)'],'Microsoft/Edge/Application/msedge.exe'),headless:true,args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const errors=[],checks=[];try{const p=await browser.newPage({viewport:{width:1440,height:1000}});p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});await p.addInitScript(()=>sessionStorage.setItem('freshman-interactive-cover-v3','1'));await p.goto('http://127.0.0.1:8772/?view=journey');await p.waitForSelector('body.journey-active');await p.waitForFunction(()=>document.querySelector('#school-select').options.length>0);await p.waitForTimeout(600);assert.equal(await p.locator('.journey-track > .journey-chapter').count(),5);await p.screenshot({path:path.join(out,'journey-desktop.png')});
const before=await p.locator('.journey-track').evaluate(e=>getComputedStyle(e).transform);assert.notEqual(before,'none');await p.locator('#journey-perspective').click();await p.waitForFunction(()=>getComputedStyle(document.querySelector('.journey-track')).transform==='none');assert.equal(await p.locator('.journey-track').evaluate(e=>getComputedStyle(e).transform),'none');await p.locator('#journey-perspective').click();await p.waitForTimeout(1100);checks.push('Perspective and flat reading modes transition smoothly');
await p.mouse.move(1100,300);await p.waitForFunction(()=>parseFloat(document.querySelector('#journey-begin').style.getPropertyValue('--light-x'))>74);assert((await p.locator('.journey-chapter').first().evaluate(e=>getComputedStyle(e,':before').backgroundImage)).includes('radial-gradient'));checks.push('Soft pointer lighting and layered chapter gradients');
const connector=p.locator('.journey-connector[data-next=campus]');
await connector.scrollIntoViewIfNeeded();
await p.waitForFunction(()=>document.querySelector('.journey-connector[data-next=campus]').classList.contains('is-visible'));
await p.waitForFunction(()=>parseFloat(document.querySelector('.journey-track').style.getPropertyValue('--drum-tilt'))===9);
const seam=await connector.evaluate(el=>{const prev=el.previousElementSibling,next=el.nextElementSibling;const a=prev.getBoundingClientRect(),b=el.getBoundingClientRect(),c=next.getBoundingClientRect();return Math.max(Math.abs(a.bottom-b.top),Math.abs(b.bottom-c.top),Math.abs(prev.offsetWidth-el.offsetWidth),Math.abs(next.offsetWidth-el.offsetWidth))});
assert(seam<1,'Chapter surfaces should meet the route without gaps or overhangs');
await connector.locator('button').click();await p.waitForTimeout(1300);assert((await p.locator('#journey-position').textContent()).startsWith('03'));await p.screenshot({path:path.join(out,'journey-campus.png')});checks.push('Continuous chapter route, next-stop navigation and reading progress');
await p.locator('.journey-nav [data-chapter=prepare]').click();await p.waitForTimeout(1300);await p.locator('.journey-feature[href="/?view=arrival"]').click();await p.waitForSelector('#view-arrival:not([hidden])');assert(!await p.locator('body').evaluate(e=>e.classList.contains('journey-active')));await p.waitForSelector('.scenario-option');assert(await p.locator('.sidebar').isVisible());await p.locator('.sidebar [data-view=journey]').click();await p.waitForSelector('body.journey-active');checks.push('Existing scenario tool, sidebar and journey return remain functional');
for(const href of ['/journey.js','/journey.css','/assets/maps/hnvust-map-artwork.png','/dorm-images/siren-env.jpg'])assert((await p.request.get('http://127.0.0.1:8772'+href)).ok());assert.equal(await p.locator('.journey-map-preview').getAttribute('href'),'/campus3d/');checks.push('All homepage images and 3D campus entry available');
const wheelStart=await p.evaluate(()=>{
  window.journeyWheelSamples=[];
  addEventListener('scroll',()=>window.journeyWheelSamples.push(scrollY),{passive:true});
  return scrollY;
});
const currentBefore=await p.locator('.journey-river').evaluate(el=>parseFloat(el.style.getPropertyValue('--river-offset')));
await p.mouse.move(720,500);
await p.mouse.wheel(0,420);
await p.waitForFunction(()=>parseFloat(document.querySelector('.journey-track').style.getPropertyValue('--drum-tilt'))>22);
const projection=await p.locator('.journey-track').evaluate(track=>{
  const matrix=new DOMMatrix(getComputedStyle(track).transform);
  const tilt=parseFloat(track.style.getPropertyValue('--drum-tilt'));
  return {tilt,farToNearWidth:1/(1-600*matrix.m24)};
});
assert(projection.tilt<=49&&projection.farToNearWidth<.83);
await p.screenshot({path:path.join(out,'journey-perspective-scroll.png')});
await p.waitForFunction(y=>Math.abs(scrollY-y-420)<=1,wheelStart);
const wheelSamples=await p.evaluate(()=>window.journeyWheelSamples);
assert(new Set(wheelSamples.filter(y=>y>wheelStart&&y<wheelStart+420)).size>=4);
const currentAfter=await p.locator('.journey-river').evaluate(el=>parseFloat(el.style.getPropertyValue('--river-offset')));
const upstreamDistance=((currentBefore-currentAfter)%160+160)%160;
assert(upstreamDistance>98&&upstreamDistance<103);
await p.waitForFunction(()=>parseFloat(document.querySelector('.journey-track').style.getPropertyValue('--drum-tilt'))===9);
checks.push('A wheel step glides in perspective and drives the river highlights upstream');
const startY=await p.evaluate(()=>{
  const track=document.querySelector('.journey-track');
  const preview=document.querySelector('.journey-loop-preview');
  const top=track.offsetParent.getBoundingClientRect().top+scrollY+track.offsetTop;
  scrollTo({top:top+preview.offsetTop+12,behavior:'instant'});
  return top+12;
});
await p.waitForFunction(y=>Math.abs(scrollY-y)<2,startY);
assert((await p.locator('#journey-position').textContent()).startsWith('01'));
assert.equal(await p.locator('.journey-loop-preview').getAttribute('inert'),'');
checks.push('Scrolling across the tail returns to the matching opening position');
const night=await p.locator('.chapter-campus').evaluate(el=>getComputedStyle(el).backgroundImage);
await p.locator('.journey-nav [data-palette=warm]').click();
assert.equal(await p.locator('body').getAttribute('data-palette'),'warm');
assert.notEqual(await p.locator('.chapter-campus').evaluate(el=>getComputedStyle(el).backgroundImage),night);
assert.equal(await p.evaluate(()=>localStorage.getItem('freshman-journey-palette')),'warm');
await p.waitForFunction(()=>getComputedStyle(document.querySelector('.journey-nav [data-palette=warm]')).backgroundColor==='rgb(130, 69, 47)');
await p.screenshot({path:path.join(out,'journey-warm.png')});
await p.locator('.journey-nav-cta').click();
await p.waitForSelector('#view-chat:not([hidden]) .faq-grid button');
assert.equal(await p.locator('.topbar [data-palette=warm]').getAttribute('aria-pressed'),'true');
const faq=p.locator('#view-chat .faq-grid button').first();
const warmFaq=await faq.evaluate(el=>getComputedStyle(el).color);
await p.locator('.topbar [data-palette=night]').click();
await p.waitForFunction(()=>getComputedStyle(document.querySelector('#view-chat .faq-grid button')).color==='rgb(237, 242, 255)');
assert.notEqual(await faq.evaluate(el=>getComputedStyle(el).color),warmFaq);
await p.locator('.sidebar [data-view=journey]').click();
await p.waitForSelector('body.journey-active');
assert.equal(await p.locator('.journey-nav [data-palette=night]').getAttribute('aria-pressed'),'true');
assert.equal(await p.locator('.chapter-campus').evaluate(el=>getComputedStyle(el).backgroundImage),night);
checks.push('Journey and question workspace share and persist the selected palette');
await p.locator('.journey-nav-cta').click();
await p.getByRole('button',{name:'体验：外地新生如何准备报到？'}).click();
const arrivalForm=p.locator('.answer-arrival').last();
await arrivalForm.waitFor();
const guidedMessage=arrivalForm.locator('xpath=ancestor::article');
assert.match(await guidedMessage.locator('.message-body').textContent(),/报到材料[\s\S]*交通与接站[\s\S]*出发前核对/);
await guidedMessage.locator('.citation').nth(1).locator('summary').click();
assert.match(await guidedMessage.locator('.citation[open]').textContent(),/适用参考年份：2024/);
await arrivalForm.getByRole('checkbox',{name:'核对当年入学须知与本人报到安排'}).uncheck();
await arrivalForm.getByRole('button',{name:'加入我的报到清单'}).click();
await arrivalForm.getByRole('status').filter({hasText:/新增 [02] 项，已在清单中 [02] 项/}).waitFor();
await arrivalForm.getByRole('button',{name:'查看报到清单'}).click();
const personalArrival=p.locator('#personal-arrival-list');
await personalArrival.getByText('按本人入学须知整理证件材料').waitFor();
await personalArrival.getByText('核对交通与到校路线并预留时间').waitFor();
assert.equal(await personalArrival.getByText('核对当年入学须知与本人报到安排').count(),0);
await p.reload();
await personalArrival.getByText('按本人入学须知整理证件材料').waitFor();
checks.push('Guided arrival answer exposes evidence and saves selected actions across reloads');
for(const [view,count,search,source] of [
  ['union',14,'综合事务部','大学生学生会与学生组织指南.md'],
  ['club',16,'数学建模协会','大学生社团指南.md']
]){
  await p.locator(`.sidebar [data-view=${view}]`).click();
  await p.waitForSelector(`#view-${view}:not([hidden]) .participation-card`);
  const cards=p.locator(`#${view}-list .participation-card`);
  assert.equal(await cards.count(),count);
  const badges=await cards.locator('.participation-logo').evaluateAll(images=>images.map(image=>image.src));
  assert.equal(new Set(badges).size,count);
  for(const badge of badges){
    const response=await p.request.get(badge);
    assert(response.ok());
    assert(response.headers()['content-type'].includes('image/svg+xml'));
  }
  assert(!/未确认|待核对|交接参考/.test(await p.locator(`#view-${view}`).textContent()));
  assert.equal(await cards.locator('.participation-advice').count(),count);
  await p.locator(`#${view}-search`).fill(search);
  assert.equal(await cards.count(),1);
  await cards.first().getByRole('button',{name:'查看来源'}).click();
  await p.waitForSelector('#view-sources:not([hidden])');
  assert.equal(await p.locator('#source-filter').inputValue(),source);
}
checks.push('Club and student organization guides have unique SVG badges, practical advice and traceable sources');
await p.locator('.sidebar [data-view=contest]').click();
await p.waitForSelector('#contest-levels .contest-level');
await p.locator('.topbar [data-palette=warm]').click();
await p.locator('#appearance-open').click();
await p.locator('input[name="appearance-mode"][value="dark"]').check();
await p.locator('#appearance-close').click();
await p.locator('.contest-grad summary').click();
const contrastRatios=await p.locator('.contest-level :is(strong,p,.level-badge),.contest-grad :is(summary,p)').evaluateAll(nodes=>{
  function luminance(rgb){
    const channels=rgb.match(/[\d.]+/g).slice(0,3).map(channel=>{
      const v=Number(channel)/255;
      return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;
    });
    return channels[0]*.2126+channels[1]*.7152+channels[2]*.0722;
  }
  return nodes.map(node=>{
    const foreground=luminance(getComputedStyle(node).color);
    const surface=node.matches('.level-badge')?node:node.parentElement;
    const background=luminance(getComputedStyle(surface).backgroundColor);
    return (Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05);
  });
});
assert.equal(contrastRatios.length,11);
assert(contrastRatios.every(ratio=>ratio>=4.5),`Contest text contrast: ${contrastRatios.join(', ')}`);
checks.push('Contest levels and expanded advice remain legible with warm palette and dark appearance');
await p.locator('.sidebar [data-view=map]').click();
const mapPlaces=p.locator('#place-list button');
await mapPlaces.first().waitFor();
const placeColors=await mapPlaces.evaluateAll(buttons=>buttons.map(button=>{
  const style=getComputedStyle(button);
  return [style.color,style.backgroundColor];
}));
assert(placeColors.some(([text,bg])=>text==='rgb(65, 46, 41)'&&bg==='rgb(255, 250, 242)'));
await mapPlaces.nth(1).click();
assert(await mapPlaces.nth(1).evaluate(button=>button.classList.contains('active')));
checks.push('Map place buttons remain readable and selectable with warm palette and dark appearance');
await p.locator('.topbar [data-palette=night]').click();
await p.locator('.sidebar [data-view=journey]').click();
await p.waitForSelector('body.journey-active');
await p.locator('.journey-nav [data-chapter=prepare]').click();await p.waitForTimeout(1400);await p.locator('.journey-feature[href="/?view=arrival"]').click();await p.waitForSelector('body.campus-subpage');await p.waitForTimeout(950);await p.screenshot({path:path.join(out,'subpage-arrival.png')});assert(await p.locator('.scenario-option').count());await p.locator('.scenario-option').first().click();assert(await p.locator('.scenario-option input').first().isChecked());checks.push('Subpage entry animation, shared campus styling and scenario interaction');
await p.locator('.sidebar [data-view=preparation]').click();await p.waitForSelector('#view-preparation:not([hidden])');await p.waitForTimeout(1000);await p.screenshot({path:path.join(out,'subpage-preparation.png')});assert.equal(await p.locator('body').getAttribute('data-campus-view'),'preparation');await p.locator('.sidebar [data-view=dorm]').click();await p.waitForSelector('#view-dorm:not([hidden])');await p.waitForTimeout(950);await p.screenshot({path:path.join(out,'subpage-dorm.png')});checks.push('Preparation and dorm tools share the chapter visual language');
await p.goto('http://127.0.0.1:8772/?cover=1');await p.waitForSelector('#intro-dialog[open]');await p.locator('#intro-enter').click();await p.waitForSelector('body.journey-active');checks.push('Cover entry opens the new guide homepage');
const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});mobile.on('pageerror',e=>errors.push(e.message));await mobile.addInitScript(()=>sessionStorage.setItem('freshman-interactive-cover-v3','1'));await mobile.goto('http://127.0.0.1:8772/?view=journey');await mobile.waitForSelector('body.journey-active');await mobile.waitForTimeout(700);assert(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await mobile.screenshot({path:path.join(out,'journey-mobile.png')});await mobile.locator('#journey-start').click();await mobile.waitForTimeout(1300);await mobile.screenshot({path:path.join(out,'journey-mobile-prepare.png')});checks.push('Mobile layout and touch chapter scrolling');
await mobile.goto('http://127.0.0.1:8772/?view=arrival');await mobile.waitForSelector('body.campus-subpage');await mobile.waitForSelector('.scenario-option');await mobile.screenshot({path:path.join(out,'subpage-mobile.png')});const mobileBounds=await mobile.locator('#view-arrival').boundingBox();assert(mobileBounds.x>=0&&mobileBounds.x+mobileBounds.width<=391);await mobile.locator('.scenario-option').first().click();assert(await mobile.locator('.scenario-option input').first().isChecked());checks.push('Mobile subpage layout and scenario selection');
const reduced=await browser.newPage({viewport:{width:1280,height:900},reducedMotion:'reduce'});await reduced.goto('http://127.0.0.1:8772/?view=journey');await reduced.waitForSelector('body.journey-active');assert.equal(await reduced.locator('.journey-track').evaluate(e=>getComputedStyle(e).transform),'none');checks.push('Reduced motion defaults to flat reading');assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({success:true,checks,errors},null,2));console.log('PASS '+checks.join('; '));}finally{await browser.close();server.kill()}


