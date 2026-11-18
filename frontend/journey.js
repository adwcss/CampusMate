/* Perspective editorial homepage. All chapter actions lead to existing tools. */
(()=>{
 'use strict';
 const root=document.querySelector('#view-journey');
 root.innerHTML=`
 <div class="journey-space" aria-hidden="true"><svg viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice"><g fill="none" stroke="currentColor" stroke-width=".7"><path d="M0 180L290 300 140 640 540 790 870 590 1170 810 1600 650M290 300L610 130 870 590 1200 190 1600 340M140 640L610 130M540 790L1200 190M0 950L1600 60M0 40L1600 950M0 500H1600M800 0V1000"/><ellipse cx="800" cy="500" rx="710" ry="290"/><ellipse cx="800" cy="500" rx="510" ry="450"/></g><g fill="currentColor">${[[290,300],[140,640],[540,790],[870,590],[1170,810],[610,130],[1200,190]].map(([x,y])=>`<circle cx="${x}" cy="${y}" r="3"/>`).join('')}</g></svg><span class="space-caption">EVERY NEW BEGINNING<br>IS A NEW UNIVERSE.</span></div>
 <header class="journey-nav"><a href="/?view=journey" class="journey-brand">初到<span>HNVUST / FIRST CHAPTER</span></a><nav aria-label="长卷章节"><button data-chapter="begin">序章</button><button data-chapter="prepare">准备</button><button data-chapter="campus">校园</button><button data-chapter="living">生活</button><button data-chapter="future">成长</button></nav><div class="journey-nav-actions"><a href="/?view=chat" class="journey-nav-cta">进入工具台 ↗</a></div></header>
 <aside class="journey-rail" aria-label="探索进度"><span>YOUR FIRST CHAPTER</span><div class="journey-progress"><i id="journey-progress-fill"></i></div><small id="journey-position">01 / 05</small></aside>
 <div class="journey-viewport"><div class="journey-track">
 <section class="journey-chapter chapter-begin" id="journey-begin" data-number="01"><div class="chapter-meta"><span>河南科技职业大学 / 新生指南</span><span>01 — THE BEGINNING</span></div><div class="journey-hero-copy"><p class="journey-kicker">每一次初到，都值得期待。</p><h1>你的大学，<br>从这里<span>展开。</span></h1><p class="journey-lead">从准备第一件行李，到找到属于自己的方向。<br>和我一起，把陌生的校园变成熟悉的日常。</p><button id="journey-start" class="journey-action" data-chapter="prepare">向下，开启新章节 <span>↓</span></button></div><img class="journey-hero-character" src="/assets/school-mascot.png" alt="蓝白色校园向导向你伸出手"><div class="journey-orbits" aria-hidden="true"><i></i><i></i><i></i><b>✦</b></div><div class="journey-hero-bottom"><span>厚德博学 · 求实创新</span><span>SCROLL TO EXPLORE ↓</span></div></section>
 <section class="journey-chapter chapter-prepare" id="journey-prepare" data-number="02"><div class="chapter-meta"><span>出发之前 / BEFORE YOU GO</span><span>02 — GET READY</span></div><div class="chapter-title"><h2>准备好，<br>才更有<span>底气。</span></h2><p>通知怎么核实？行李怎么整理？<br>让未知变成一件件可以完成的小事。</p></div><div class="journey-card-grid"><a class="journey-feature" href="/?view=arrival"><span class="feature-index">01 / REHEARSAL</span><h3>先演练，再出发。</h3><p>在报到之前，体验真实的新生情景。</p><div class="journey-scenario"><span>收到一条“新生缴费通知”</span><strong>先核实来源，<br>还是直接转账？</strong><div><i></i><i></i><i></i></div></div><span class="feature-link">开始情景演练 ↗</span></a><a class="journey-feature" href="/?view=preparation"><span class="feature-index">02 / PACKING</span><h3>把安心，装进行李。</h3><p>证件、用品与个人备忘，都有归处。</p><div class="journey-packing"><div>✓ <span>证件与报到材料</span></div><div>✓ <span>行李与生活用品</span></div><div>＋ <span>留给自己的备忘</span></div><small>你的准备，由你掌握。</small></div><span class="feature-link">打开出发准备台 ↗</span></a></div><div class="journey-inline-links"><a href="/?view=checklist">报到清单 ↗</a><a href="/?view=sources">核对资料来源 ↗</a></div></section>
 <section class="journey-chapter chapter-campus" id="journey-campus" data-number="03"><div class="chapter-meta"><span>第一次遇见 / MEET YOUR CAMPUS</span><span>03 — DISCOVER</span></div><div class="chapter-title"><h2>把校园，<br>走成你的<span>日常。</span></h2><p>从图书馆到餐厅，从教学楼到宿舍。<br>点亮你想认识的第一个地方。</p></div><a class="journey-map-preview" href="/campus3d/" aria-label="进入三维校园"><img src="/assets/maps/hnvust-map-artwork.png" alt="校园地图插画参考" loading="lazy"><div class="map-preview-caption"><span>30 个地点 · 风格化三维场景</span><strong>进入 3D 校园 ↗</strong></div><span class="journey-map-label">HNVUST<br>CAMPUS EXPLORER</span></a><div class="journey-two-columns"><div><h3>一处风景，一个新坐标。</h3><p>旋转、缩放、点击建筑，查看地点信息。地图与模型为参考示意，实际位置以现场为准。</p></div><div><h3>让第一次探索有条理。</h3><p>在二维地图中加入想去的地点，安排探索顺序，记录你已经认识的校园。</p><a class="feature-link" href="/?view=map">规划我的探索行程 ↗</a></div></div></section>
 <section class="journey-chapter chapter-living" id="journey-living" data-number="04"><div class="chapter-meta"><span>安放日常 / MAKE YOURSELF AT HOME</span><span>04 — SETTLE IN</span></div><div class="chapter-title"><h2>让陌生，<br>慢慢变成<span>熟悉。</span></h2><p>一张床、一盏灯、一群新的朋友。<br>属于你的校园生活，正要开始。</p></div><div class="journey-living-grid"><a href="/?view=dorm" class="journey-dorm-card"><img src="/dorm-images/siren-env.jpg" alt="四人间宿舍环境参考" loading="lazy"><div><span>YOUR LITTLE CORNER</span><h3>找到你的生活一角。</h3><p>查看宿舍参考与床位选择信息。实际安排以学校通知为准。</p><strong>了解宿舍生活 ↗</strong></div></a><div class="journey-community"><a href="/?view=club"><span>01 / COMMUNITY</span><h3>遇见同频的人。</h3><p>从兴趣出发，认识校园社团。</p><b>探索社团 ↗</b></a><a href="/?view=union"><span>02 / TOGETHER</span><h3>一起做点有意义的事。</h3><p>了解学生会与校园学生组织。</p><b>认识学生组织 ↗</b></a></div></div></section>
 <section class="journey-chapter chapter-future" id="journey-future" data-number="05"><div class="chapter-meta"><span>下一步 / THE NEXT CHAPTER</span><span>05 — GROW YOUR WAY</span></div><div class="chapter-title"><h2>未来的你，<br>从今天开始<span>生长。</span></h2><p>不必一下子想好全部。<br>先从一件小事开始，慢慢找到自己的节奏。</p></div><div class="journey-growth"><a href="/?view=plan"><span>↗</span><h3>我的成长计划</h3><p>梳理选择，让想法变成行动。</p></a><a href="/?view=contest"><span>✳</span><h3>发现竞赛机会</h3><p>认识赛事类型，寻找适合的挑战。</p></a><a href="/?view=tasks"><span>✓</span><h3>安排今天的小事</h3><p>管理日程与任务，走好眼前这一步。</p></a></div><div class="journey-finale"><span>THE STORY IS YOURS.</span><h3>你的故事，现在开始。</h3><a href="/?view=chat" class="journey-action">有问题，问问校园向导 <span>↗</span></a></div></section>
 </div></div><footer class="journey-footer"><a href="/?view=sources">资料来源与适用范围 ↗</a><span>独立开发作品 · 非学校官方服务</span><button data-chapter="begin">回到序章 ↑</button></footer>`;
 const orbit=document.createElement('div');orbit.className='journey-orbit';orbit.setAttribute('aria-label','校园悬浮画廊');orbit.innerHTML=`<div class="orbit-sphere" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div><a class="orbit-card orbit-one" href="/campus3d/"><img src="/assets/maps/hnvust-map-artwork.png" alt="校园布局参考"><span>01 / 探索校园 ↗</span></a><a class="orbit-card orbit-two" href="/?view=dorm"><img src="/dorm-images/siren-env.jpg" alt="宿舍生活参考"><span>02 / 安放日常 ↗</span></a><a class="orbit-card orbit-three" href="/?view=plan"><img src="/assets/mascot-reading.png" alt="阅读中的校园向导"><span>03 / 让未来生长 ↗</span></a><a class="orbit-card orbit-four" href="/?view=preparation"><img src="/assets/chibi-ready.png" alt="准备出发的校园向导"><span>04 / 准备好出发 ↗</span></a><div class="orbit-caption">A LITTLE CURIOSITY.<br>A WHOLE NEW WORLD.</div>`;root.querySelector('.chapter-begin').append(orbit);
 const cursor=document.createElement('div');cursor.className='journey-cursor';cursor.setAttribute('aria-hidden','true');root.append(cursor);
 const space=root.querySelector('.journey-space');
 space.insertAdjacentHTML('beforeend',`
   <svg class="journey-river" viewBox="0 0 1600 1000" preserveAspectRatio="none" aria-hidden="true">
     <defs>
       <linearGradient id="journey-river-light" x1="0" y1="1000" x2="0" y2="0" gradientUnits="userSpaceOnUse">
         <stop offset="0" stop-color="currentColor" stop-opacity=".12"/>
         <stop offset=".38" stop-color="currentColor" stop-opacity=".95"/>
         <stop offset=".78" stop-color="currentColor" stop-opacity=".44"/>
         <stop offset="1" stop-color="currentColor" stop-opacity="0"/>
       </linearGradient>
       <path id="journey-river-course" d="M34 1040C92 880 181 799 171 660S77 451 115 328 233 158 294 50
         M107 1050C118 889 233 803 208 663S127 449 161 351 234 225 327 75
         M1572 1040C1493 892 1398 803 1424 661S1527 454 1490 330 1371 165 1304 48
         M1504 1050C1468 896 1357 814 1390 667S1474 456 1441 352 1362 220 1275 75"/>
     </defs>
     <use href="#journey-river-course" class="river-bank"/>
     <use href="#journey-river-course" class="river-current"/>
   </svg>`);
 const rail=root.querySelector('.journey-rail');
 rail.querySelector('span').textContent='溯流而上';
 rail.insertAdjacentHTML('afterbegin','<b class="journey-river-arrow" aria-hidden="true">↑</b>');
 root.querySelector('#journey-start').firstChild.textContent='沿长河，开启新章节 ';
 const waveCanvas=document.createElement('canvas');waveCanvas.className='journey-waves';waveCanvas.setAttribute('aria-hidden','true');root.querySelector('.journey-space').append(waveCanvas);const waveContext=waveCanvas.getContext('2d');let waves=[],waveFrame=0,lastWave=0;
 function sizeWaves(){waveCanvas.width=innerWidth;waveCanvas.height=innerHeight;}sizeWaves();addEventListener('resize',sizeWaves);
 function drawWaves(now){waveFrame=0;if(root.hidden||document.hidden){waves=[];waveContext.clearRect(0,0,waveCanvas.width,waveCanvas.height);return;}waveContext.clearRect(0,0,waveCanvas.width,waveCanvas.height);waves=waves.filter(w=>now-w.born<1200);for(const w of waves){const t=(now-w.born)/1200;waveContext.beginPath();waveContext.ellipse(w.x,w.y,15+t*125,8+t*60,-.2,0,Math.PI*2);waveContext.strokeStyle=`rgba(168,209,238,${(1-t)*.2})`;waveContext.lineWidth=.7;waveContext.stroke();}if(waves.length)waveFrame=requestAnimationFrame(drawWaves);}
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'),track=root.querySelector('.journey-track');
 const nav=root.querySelector('.journey-nav');
 const progressFill=root.querySelector('#journey-progress-fill'),positionLabel=root.querySelector('#journey-position');
 const chapterButtons=[...nav.querySelectorAll('[data-chapter]')];
 const paletteKey='freshman-journey-palette';
 const paletteButtons=[];
 for(const host of [nav.querySelector('.journey-nav-actions'),document.querySelector('.topbar > div')]){
   if(!host)continue;
   const palette=document.createElement('div');
   palette.className='journey-palette';
   palette.setAttribute('role','group');
   palette.setAttribute('aria-label','校园配色');
   palette.innerHTML='<button type="button" data-palette="night">深夜</button><button type="button" data-palette="warm">暖阳</button>';
   host.prepend(palette);
   paletteButtons.push(...palette.querySelectorAll('button'));
 }
 function applyPalette(value){
   document.body.dataset.palette=value==='warm'?'warm':'night';
   paletteButtons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.palette===value)));
 }
 let preferredPalette='night';
 try{if(localStorage.getItem(paletteKey)==='warm')preferredPalette='warm';}catch{}
 applyPalette(preferredPalette);
 paletteButtons.forEach(button=>button.addEventListener('click',()=>{
   applyPalette(button.dataset.palette);
   try{localStorage.setItem(paletteKey,button.dataset.palette);}catch{}
 }));
 addEventListener('storage',event=>{
   if(event.key===paletteKey||event.key===null)applyPalette(event.newValue==='warm'?'warm':'night');
 });
 root.classList.add('journey-flat');
 let frame=0,lastTime=0,layout=null,maxScroll=0,activeChapter=-1;
 const light={x:70,y:24,targetX:70,targetY:24},chapters=[...root.querySelectorAll('.journey-chapter')];
 const footer=root.querySelector('.journey-footer');
 chapters.at(-1).append(footer);
 const stops=[
   {id:'prepare',from:'初到',to:'收拾行囊',note:'把期待装进行李'},
   {id:'campus',from:'出发准备',to:'第一次遇见校园',note:'准备就绪，沿着这条路出发'},
   {id:'living',from:'探索校园',to:'安放日常',note:'从认识校园，到熟悉日常'},
   {id:'future',from:'校园生活',to:'找到自己的方向',note:'把今天的相遇带进下一站'},
   {id:'begin',from:'成长',to:'重回序章',note:'带着新的期待，再走一遍'}
 ];
 stops.forEach(({id,from,to,note},index)=>{
   const connector=document.createElement('div');
   connector.className='journey-connector';
   connector.dataset.next=id;
   connector.innerHTML=`
     <div class="journey-stop"><span>0${index+1} / ${from}</span><p>${note}</p></div>
     <svg class="journey-route" viewBox="0 0 320 72" preserveAspectRatio="none" aria-hidden="true">
       <defs><path id="river-lettering-${id}" d="M12 45H54C110 45 114 5 172 5H312"/></defs>
       <path class="journey-route-halo" d="M6 56H54C110 56 114 16 172 16H312"/>
       <path class="journey-route-line" d="M6 56H54C110 56 114 16 172 16H312"/>
       <text class="river-lettering"><textPath href="#river-lettering-${id}" startOffset="18%">HNVUST · CAMPUS JOURNEY</textPath></text>
       <circle cx="6" cy="56" r="4"/><path class="journey-route-arrow" d="m304 9 8 7-8 7"/>
     </svg>
     <button class="journey-next-stop" type="button" data-chapter="${id}">
       <span>${id==='begin'?'回到起点 / 01':`下一站 / 0${index+2}`}</span><strong>${to} <span aria-hidden="true">↘</span></strong>
     </button>`;
   chapters[index].after(connector);
 });
 function measure(){
   const parent=track.offsetParent;
   const top=parent.getBoundingClientRect().top+scrollY+track.offsetTop;
   maxScroll=Math.max(0,document.documentElement.scrollHeight-innerHeight);
   return chapters.map(section=>{
     const sectionTop=top+section.offsetTop;
     return {section,top:sectionTop,height:section.offsetHeight};
   });
 }
 function invalidate(){layout=null;schedule();}
 function setStyle(element,property,value){
   if(element.style.getPropertyValue(property)!==value)element.style.setProperty(property,value);
 }
 function render(now){
   frame=0;
   if(root.hidden||document.hidden){
     lastTime=0;
     return;
   }
   layout??=measure();
   const scroll=scrollY;
   const height=innerHeight;
   const dt=Math.min(lastTime?now-lastTime:16,64);
   lastTime=now;
   const lightBlend=1-Math.exp(-dt/85);
   light.x+=(light.targetX-light.x)*lightBlend;
   light.y+=(light.targetY-light.y)*lightBlend;
   setStyle(root,'--orbit-x',((light.x-50)*.44).toFixed(2)+'px');
   setStyle(root,'--orbit-y',((light.y-40)*.28).toFixed(2)+'px');
   setStyle(root,'--type-shift',((light.x-50)*.024).toFixed(3)+'px');
   setStyle(root,'--orbit-turn',((light.x-50)*.12).toFixed(2)+'deg');
   const progressEnd=maxScroll;
   setStyle(progressFill,'transform',`scaleY(${(progressEnd>0?Math.min(1,scroll/progressEnd):0).toFixed(5)})`);
   let chapter=0;
   layout.forEach(({section,top,height:sectionHeight},index)=>{
     if(top<scroll+height*.55)chapter=index;
     if(top+sectionHeight>scroll&&top<scroll+height){
       setStyle(section,'--light-x',light.x.toFixed(2)+'%');
       setStyle(section,'--light-y',light.y.toFixed(2)+'%');
     }
   });
   if(chapter!==activeChapter){
     activeChapter=chapter;
     positionLabel.textContent=chapters[chapter].dataset.number+' / 05';
     chapterButtons.forEach((button,index)=>button.classList.toggle('active',index===chapter));
   }
   if(Math.abs(light.targetX-light.x)>.1||Math.abs(light.targetY-light.y)>.1)schedule();
   else lastTime=0;
 }
 function schedule(){if(!frame)frame=requestAnimationFrame(render)}
 root.addEventListener('pointermove',e=>{if(reduced.matches||e.pointerType==='touch')return;light.targetX=Math.max(10,Math.min(90,e.clientX/innerWidth*100));light.targetY=Math.max(8,Math.min(80,e.clientY/innerHeight*100));cursor.style.setProperty('--cursor-x',e.clientX+'px');cursor.style.setProperty('--cursor-y',e.clientY+'px');cursor.classList.add('shown');cursor.classList.toggle('over-action',Boolean(e.target.closest('a,button')));const now=performance.now();if(now-lastWave>95){lastWave=now;waves.push({x:e.clientX,y:e.clientY,born:now});if(waves.length>12)waves.shift();if(!waveFrame)waveFrame=requestAnimationFrame(drawWaves);}schedule()},{passive:true});
 root.addEventListener('pointerleave',()=>{light.targetX=70;light.targetY=24;cursor.classList.remove('shown');schedule()});
 if('IntersectionObserver' in window){
   const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
     if(!entry.isIntersecting)return;
     entry.target.classList.add('is-visible');
     observer.unobserve(entry.target);
   }),{rootMargin:'0px 0px 12% 0px',threshold:.05});
   root.querySelectorAll('.journey-chapter,.journey-connector').forEach(element=>observer.observe(element));
   root.classList.add('journey-enhanced');
 }
 root.querySelectorAll('[data-chapter]').forEach(button=>{
   button.onclick=()=>{
     const index=chapters.findIndex(section=>section.id==='journey-'+button.dataset.chapter);
     const target=(layout??=measure())[index];
     const top=index===0?0:target.top-nav.offsetHeight-16;
     window.scrollTo({top:Math.max(0,top),behavior:reduced.matches?'instant':'smooth'});
   };
 });
 const resizeObserver=new ResizeObserver(invalidate);
 chapters.forEach(section=>resizeObserver.observe(section));
 resizeObserver.observe(root);
 new MutationObserver(invalidate).observe(root,{attributes:true,attributeFilter:['hidden']});
 addEventListener('scroll',schedule,{passive:true});
 addEventListener('resize',invalidate);
 document.addEventListener('visibilitychange',schedule);
 reduced.addEventListener('change',invalidate);
 schedule();
})();

/* Shared visual language and cancellable entry motion for all guide tools. */
window.CampusMotion=(()=>{
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const themes={arrival:['#646496','#dbdcf4'],preparation:['#6b719d','#e0e4f5'],chat:['#466b9d','#dbe9f8'],map:['#84665f','#efe1d7'],dorm:['#39796b','#dbede6'],'dorm-bed':['#39796b','#dbede6'],club:['#407b76','#dcefe9'],union:['#407b76','#dcefe9'],plan:['#54729b','#deE8f6'],tasks:['#54729b','#dee8f6'],contest:['#6b719d','#e0e4f5'],checklist:['#6b719d','#e0e4f5'],sources:['#516e91','#e2eaf3']};
 const folios={arrival:'02 · 报到演练',preparation:'02 · 出发准备',chat:'01 · 新生问答',map:'03 · 校园图志',dorm:'04 · 宿舍生活','dorm-bed':'04 · 床位参考',club:'04 · 社团指南',union:'04 · 学生组织',plan:'05 · 成长计划',tasks:'05 · 日程任务',contest:'05 · 竞赛指南',checklist:'02 · 报到清单',sources:'附录 · 资料索引'};
 for(const [view,label] of Object.entries(folios)){
   const title=document.querySelector('#view-'+view+' .page-heading h1');
   if(!title)continue;
   const tag=document.createElement('span');
   tag.className='campus-folio';
   tag.textContent=label;
   title.before(tag);
 }
 let animation=null;
 function enter(view,animate){
   animation?.cancel();
   animation=null;
   const theme=themes[view];
   document.body.classList.toggle('campus-subpage',Boolean(theme));
   document.body.dataset.campusView=view;
   if(!theme)return;
   const [accent,tint]=theme;
   document.body.style.setProperty('--sub-accent',accent);
   document.body.style.setProperty('--sub-tint',tint);
   const panel=document.querySelector('#view-'+view);
   if(panel&&animate&&!reduced.matches){
     animation=panel.animate([{opacity:.75},{opacity:1}],{duration:180,easing:'ease-out'});
   }
 }
 reduced.addEventListener('change',()=>{if(reduced.matches)animation?.cancel()});
 return{enter};
})();
