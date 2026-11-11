/* PixiJS portrait puppet. No bones, Live2D files or external runtime services.
 * Source is a flattened painting: these are independent procedural MASK layers,
 * not recovered original PSD layers. All coordinates below use bottom-left UV.
 * The same source is embedded verbatim in the offline single-file demo. */
(() => {
  'use strict';
  const dialog=document.querySelector('#intro-dialog'),stage=document.querySelector('#cover-stage');
  if(!dialog||!stage)return;
  const art=stage.querySelector('.cover-art'),hint=document.querySelector('#cover-hint-text');
  const motion=matchMedia('(prefers-reduced-motion: reduce)');
  const config=window.COVER_ASSETS||{image:'/assets/cover-portrait-v3.png',alpha:'/assets/cover-portrait-v2.png',library:'/assets/pixi-7.4.3.min.js',csp:'/assets/pixi-csp-7.4.3.min.js'};
  const desired={x:0,y:0},look={x:0,y:0},expression={curious:0,happy:0,puzzled:0};
  const goal={curious:0,happy:0,puzzled:0};
  const captions={idle:'慢慢来，我陪你一起启程。',puzzled:'嗯？让我也看一看。',curious:'发现了什么有趣的事情？',happy:'和你一起，今天也值得期待。'};
  let app,mesh,uniforms,ready=false,loading,active=false,frame=0,last=0,time=0;
  let nextTilt=7+Math.random()*6,tiltStart=-1,tiltSign=1,paused=false,forced=null,name='idle';
  const clamp=(v,a=-1,b=1)=>Math.max(a,Math.min(b,v));
  const ease=(dt,ms)=>1-Math.exp(-dt/ms);
  function setExpression(value){name=value;for(const k of Object.keys(goal))goal[k]=k===value?1:0;
    dialog.dataset.expression=value;const caption=dialog.querySelector('.cover-invitation');if(caption)caption.textContent=captions[value];}
  function reset(){desired.x=desired.y=0;if(!forced)setExpression('idle');}
  // Match the displayed (contain-fitted) artwork, not the window or stage box.
  function bounds(){const r=art.getBoundingClientRect(),s=Math.min(r.width/1536,r.height/1024);return {x:r.x+(r.width-1536*s)/2,y:r.y+(r.height-1024*s)/2,w:1536*s,h:1024*s};}
  function point(e){if(motion.matches||paused||forced)return;const r=bounds(),x=(e.clientX-r.x)/r.w,y=(e.clientY-r.y)/r.h;
    // Broad character rectangle; outside it the gentle resting pose returns.
    if(x<.06||x>.96||y<.01||y>.97){reset();return;}
    desired.x=clamp((x-.515)/.22);desired.y=clamp((y-.42)/.22);
    // Hysteresis prevents jitter at the two expression boundaries.
    const left=name==='puzzled'?.478:.463,right=name==='happy'?.555:.570;
    setExpression(x<left?'puzzled':x>right?'happy':'curious');
    dialog.style.setProperty('--portrait-light-x',(x*100).toFixed(1)+'%');
    dialog.style.setProperty('--portrait-light-y',(y*100).toFixed(1)+'%');
  }
  const vertex=`precision highp float;
    attribute vec2 aVertexPosition; attribute vec2 aTextureCoord;
    uniform mat3 translationMatrix; uniform mat3 projectionMatrix;
    varying vec2 vUv;
    void main(){vUv=aTextureCoord;gl_Position=vec4((projectionMatrix*translationMatrix*vec3(aVertexPosition,1.0)).xy,0.0,1.0);}`;
  const fragment=`precision highp float;
    varying vec2 vUv; uniform sampler2D uImage; uniform sampler2D uAlpha;
    uniform vec2 uLook; uniform vec3 uExpression; uniform float uTime; uniform float uTilt;
    // Separate compact masks act as eye / brow / mouth / cheek / hair layers.
    float patch(vec2 p,vec2 c,vec2 r){return 1.0-smoothstep(.48,1.0,length((p-c)/r));}
    vec4 photo(vec2 p){vec4 c=texture2D(uImage,vec2(p.x,1.0-p.y));return vec4(c.rgb/max(c.a,.001),c.a);}
    void main(){
      vec2 p=vUv,uv=p;float curious=uExpression.x,happy=uExpression.y,puzzled=uExpression.z;
      float breath=sin(uTime*.91); // 6.9 s cycle, independent of frame rate.
      float face=patch(p,vec2(.520,.527),vec2(.139,.157));
      // Sub-pixel breathing / rare tilt only inside the face. Neck and hand are pinned.
      vec2 facePivot=vec2(.520,.47),q=p-facePivot;
      uv-=vec2(-q.y,q.x)*uTilt*face;
      uv.y-=breath*.00065*face;
      vec4 raw=photo(p);
      float blue=smoothstep(.03,.16,raw.b-raw.r)*smoothstep(.0,.09,raw.b-raw.g);
      float side=1.0-smoothstep(.25,.39,p.x)+smoothstep(.71,.85,p.x);
      float hair=blue*side*smoothstep(.26,.40,p.y)*(1.0-smoothstep(.73,.87,p.y));
      // Two frequencies, vertical phase lag and taper: flowing strands, not a translated sprite.
      uv.x+=(sin(uTime*.83+p.y*12.0)*.0014+sin(uTime*1.27+p.y*23.0)*.00045)*hair;
      uv.x+=(uLook.x*.00055+uTilt*.10)*hair;
      uv.y+=sin(uTime*.72+p.x*13.0)*.00065*hair;
      vec2 centers[2];centers[0]=vec2(.448,.563);centers[1]=vec2(.577,.599);
      // Eye / iris layer: gaze, pupil size and expression-specific openness.
      for(int i=0;i<2;i++){
        vec2 c=centers[i],d=(p-c)/vec2(.042,.033);
        float eye=patch(p,c,vec2(.044,.036));
        float iris=patch(p,c+vec2(.001,-.001),vec2(.024,.030));
        uv-=vec2(uLook.x*.005,-uLook.y*.0038)*eye;
        uv-=(p-c)*(.095*curious-.055*puzzled)*iris;
        float openness=.09*curious-.11*happy-.075*puzzled;
        uv.y-=d.y*.033*openness*eye;
      }
      // Brow layer: asymmetric inward tension for puzzled, lift for curious.
      float bl=patch(p,vec2(.432,.636),vec2(.047,.023));
      float br=patch(p,vec2(.559,.674),vec2(.047,.023));
      uv.y-=(curious*.0038+puzzled*.0015+happy*.0008)*bl;
      uv.y-=(curious*.0038-puzzled*.0018+happy*.0008)*br;
      uv.x+=puzzled*.0012*(bl-br);
      // Mouth layer: corners rise in a smile, flatten slightly when puzzled.
      vec2 mouth=(p-vec2(.529,.455))/vec2(.047,.024);
      float mm=patch(p,vec2(.529,.455),vec2(.048,.025));
      uv.y-=(happy*.0050-puzzled*.0028)*mouth.x*mouth.x*mm;
      uv.y-=breath*.0004*mm;
      vec3 color=photo(uv).rgb;
      // Cheek layer: diffused blush, not hard circles. Resting skin remains visible.
      float cheeks=patch(p,vec2(.455,.498),vec2(.044,.028))+patch(p,vec2(.595,.535),vec2(.038,.029));
      color=mix(color,vec3(.96,.44,.49),cheeks*(happy*.10+max(0.0,breath)*.006));
      float alpha=texture2D(uAlpha,vec2(p.x,1.0-p.y)).a;
      gl_FragColor=vec4(color*alpha,alpha); // Pixi's premultiplied alpha blending.
    }`;
  function loadScript(src){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.head.append(s);});}
  async function loadLibrary(){if(!window.PIXI)await loadScript(config.library);if(config.csp)await loadScript(config.csp);}
  async function texture(src){const img=new Image();img.src=src;await img.decode();return PIXI.Texture.from(img);}
  async function prepare(){if(ready||motion.matches)return;if(loading)return loading;
    loading=(async()=>{await loadLibrary();
      const [image,alpha]=await Promise.all([texture(config.image),texture(config.alpha)]);
      app=new PIXI.Application({width:1536,height:1024,backgroundAlpha:0,antialias:true,autoStart:false,resolution:Math.min(devicePixelRatio,1.5),autoDensity:true,powerPreference:'low-power'});
      app.view.className='cover-canvas';app.view.setAttribute('aria-hidden','true');
      const geometry=new PIXI.Geometry().addAttribute('aVertexPosition',[0,0,1536,0,1536,1024,0,1024],2).addAttribute('aTextureCoord',[0,1,1,1,1,0,0,0],2).addIndex([0,1,2,0,2,3]);
      uniforms={uImage:image,uAlpha:alpha,uLook:new Float32Array(2),uExpression:new Float32Array(3),uTime:0,uTilt:0};
      mesh=new PIXI.Mesh(geometry,PIXI.Shader.from(vertex,fragment,uniforms));app.stage.addChild(mesh);art.append(app.view);
      app.view.addEventListener('webglcontextlost',()=>{ready=false;art.classList.remove('cover-ready');dialog.dataset.renderer='fallback';});
      ready=true;resize();app.renderer.render(app.stage);art.classList.add('cover-ready');dialog.dataset.renderer='pixi';
    })().catch(error=>{dialog.dataset.renderer='fallback';art.classList.remove('cover-ready');hint.textContent='当前设备显示静态立绘';console.warn('Portrait fallback:',error.message);app?.destroy(true);ready=false;});return loading;
  }
  function resize(){if(!ready)return;const w=art.clientWidth,h=art.clientHeight;if(!w||!h)return;app.renderer.resize(w,h);const s=Math.min(w/1536,h/1024);mesh.scale.set(s);mesh.position.set((w-1536*s)/2,(h-1024*s)/2);app.renderer.render(app.stage);}
  function tick(now){frame=0;if(!dialog.open||motion.matches||document.hidden)return;frame=requestAnimationFrame(tick);if(now-last<32)return;
    const dt=Math.min(last?now-last:32,80);last=now;
    if(!paused)time+=dt/1000;
    // Rare 3.2s soft tilt; bounded to 0.2 degrees, with no body rotation.
    if(!paused&&time>=nextTilt&&tiltStart<0){tiltStart=time;tiltSign=Math.random()<.5?-1:1;}
    let tilt=0;if(tiltStart>=0){const t=(time-tiltStart)/3.2;if(t>=1){tiltStart=-1;nextTilt=time+8+Math.random()*9;}else tilt=Math.sin(t*Math.PI)**2*.0035*tiltSign;}
    if(!paused){for(const k of ['x','y'])look[k]+=(desired[k]-look[k])*ease(dt,240);for(const k of Object.keys(expression))expression[k]+=(goal[k]-expression[k])*ease(dt,460);}
    stage.dataset.state=name;
    stage.style.setProperty('--look-x',look.x.toFixed(4));stage.style.setProperty('--look-y',look.y.toFixed(4));
    if(ready){uniforms.uLook.set([look.x,look.y]);uniforms.uExpression.set([expression.curious,expression.happy,expression.puzzled]);uniforms.uTime=time;uniforms.uTilt=tilt;app.renderer.render(app.stage);}
  }
  function start(){if(!dialog.open)return;if(!active){active=true;reset();prepare().then(resize);}last=0;if(!motion.matches&&!frame)frame=requestAnimationFrame(tick);}
  function stop(){active=false;cancelAnimationFrame(frame);frame=0;last=0;reset();}
  // Demo controls also provide a keyboard-accessible alternative to pointer regions.
  document.querySelectorAll('[data-portrait-expression]').forEach(b=>b.addEventListener('click',()=>{
    forced=b.dataset.portraitExpression==='auto'?null:b.dataset.portraitExpression;setExpression(forced||'idle');desired.x=forced==='puzzled'?-.65:forced==='happy'?.4:0;desired.y=0;
    document.querySelectorAll('[data-portrait-expression]').forEach(el=>el.setAttribute('aria-pressed',el===b?'true':'false'));
  }));
  document.querySelector('[data-portrait-pause]')?.addEventListener('click',e=>{paused=!paused;e.currentTarget.textContent=paused?'继续动画':'暂停动画';e.currentTarget.setAttribute('aria-pressed',String(paused));});
  dialog.addEventListener('pointermove',point);dialog.addEventListener('pointerleave',reset);dialog.addEventListener('pointercancel',reset);
  stage.addEventListener('blur',reset);stage.addEventListener('keydown',e=>{if(e.key==='Home'){forced=null;reset();}const states={ArrowLeft:'puzzled',ArrowUp:'curious',ArrowRight:'happy',ArrowDown:'idle'};if(states[e.key]){e.preventDefault();setExpression(states[e.key]);desired.x=e.key==='ArrowLeft'?-.7:e.key==='ArrowRight'?.7:0;}});
  new MutationObserver(()=>dialog.open?start():stop()).observe(dialog,{attributes:true,attributeFilter:['open']});
  new ResizeObserver(resize).observe(art);window.addEventListener('resize',resize);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;last=0;}else start();});
  motion.addEventListener('change',()=>{if(motion.matches){stop();art.classList.remove('cover-ready');}else{if(ready)art.classList.add('cover-ready');start();}});
  start();
})();
