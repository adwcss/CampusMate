// Browser-independent state regression for the real appearance module.
// The DOM below is a small test double; visual acceptance is checked in the browser.
import fs from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../frontend/appearance.js',import.meta.url),'utf8');
function setup({preferences,seen=false,reduced=false,broken=false,slow=false,search=''}={}){
  const nodes=new Map(),timers=new Map(),storage=new Map(),requests=[];let clock=0,id=0;
  if(preferences)storage.set('freshman-appearance-v1',JSON.stringify(preferences));
  if(seen)storage.set('freshman-interactive-cover-v3','1');
  const node=key=>{if(!nodes.has(key)){
    const classes=new Set(),events=new Map();
    nodes.set(key,{isConnected:true,hidden:false,open:false,src:'',dataset:{},style:{setProperty(){}},content:{cloneNode(){return {}; }},classList:{add(...v){v.forEach(x=>classes.add(x));},remove(...v){v.forEach(x=>classes.delete(x));},contains:x=>classes.has(x),toggle(x,v){v?classes.add(x):classes.delete(x);}},setAttribute(){},replaceChildren(){},append(){},prepend(){},showModal(){this.open=true;},close(){this.open=false;},focus(){document.activeElement=this;},addEventListener(k,fn){events.set(k,fn);},fire(k,event={}){return events.get(k)?.(event);},decode(){return broken?Promise.reject(Error('missing')):slow?new Promise(()=>{}):Promise.resolve();}});
  }return nodes.get(key);};
  const document={body:node('body'),documentElement:node('html'),activeElement:null,querySelector:node,querySelectorAll:()=>[],createDocumentFragment:()=>node('fragment'),createElementNS:()=>node('path')};
  document.activeElement=document.body;
  const store={getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v)};
  const context=vm.createContext({document,matchMedia:()=>({matches:reduced,addEventListener(){}}),localStorage:store,sessionStorage:store,indexedDB:{open(){const request={};queueMicrotask(()=>request.onerror());return request;}},setTimeout(fn,ms){const key=++id;timers.set(key,{fn,at:clock+ms});return key;},clearTimeout:key=>timers.delete(key),fetch(url){requests.push(url);throw Error('Unexpected fetch');},Blob,URL,URLSearchParams,location:{search},DOMException,console});
  vm.runInContext(source+'\nthis.appearance=Appearance;',context);
  const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
  const advance=async ms=>{const end=clock+ms;await flush();while(true){const next=[...timers].filter(([,v])=>v.at<=end).sort((a,b)=>a[1].at-b[1].at)[0];if(!next)break;clock=next[1].at;timers.delete(next[0]);next[1].fn();await flush();}clock=end;await flush();};
  return {node,context,storage,requests,advance,flush,timers};
}
test('Old role and disabled-intro choices cannot change the single default opening; photo settings survive',async()=>{
  const app=setup({preferences:{mode:'custom',source:'image',shade:63,blur:7,position:'top',pose:'creative-back',preset:'aurora',intro:false}});await app.flush();
  assert.equal(app.node('#intro-dialog').open,true);assert.equal(app.node('#intro-portrait').src,'/assets/cover-portrait-v3.png');
  assert.deepEqual(JSON.parse(JSON.stringify(app.context.appearance.getSettings())),{mode:'custom',source:'image',shade:63,blur:7,position:'top'});
  assert.deepEqual(app.requests,[]);
});
test('Opening stays until the visitor enters, then records the current tab state',async()=>{
  const app=setup();await app.advance(5000);assert.equal(app.node('#intro-dialog').classList.contains('intro-settled'),true);assert.equal(app.node('#intro-dialog').open,true);app.node('#intro-enter').fire('click');assert.equal(app.node('#intro-dialog').open,false);assert.equal(app.storage.get('freshman-interactive-cover-v3'),'1');
});
test('Same-tab reload skips opening outline fetches',()=>{const app=setup({seen:true});assert.equal(app.node('#intro-dialog').open,false);assert.deepEqual(app.requests,[]);});
test('Explicit cover URL can reopen the cover in a returning tab',()=>{assert.equal(setup({seen:true,search:'?cover=1'}).node('#intro-dialog').open,true);});
test('Reduced motion skips automatic entrance but allows a static replay',async()=>{const app=setup({reduced:true});assert.equal(app.node('#intro-dialog').open,false);app.node('#appearance-preview-intro').fire('click');await app.flush();assert.equal(app.node('#intro-dialog').open,true);assert.equal(app.node('#intro-dialog').classList.contains('intro-static'),true);});
test('Skip during slow loading closes immediately and stale resolution cannot reopen',async()=>{const app=setup({slow:true});app.node('#intro-skip').fire('click');assert.equal(app.node('#intro-dialog').open,false);await app.advance(5000);assert.equal(app.node('#intro-dialog').open,false);assert.equal(app.node('#intro-dialog').classList.contains('intro-playing'),false);});
test('Escape during replay clears the transition and focuses the guide',async()=>{const app=setup({seen:true});app.node('#appearance-preview-intro').focus();app.node('#appearance-preview-intro').fire('click');await app.flush();let cancelled=false;app.node('#intro-dialog').fire('cancel',{preventDefault(){cancelled=true;}});assert.equal(cancelled,true);assert.equal(app.context.document.activeElement,app.node('#journey-start'));await app.advance(5000);assert.equal(app.node('#intro-dialog').open,false);assert.equal(app.node('#intro-dialog').classList.contains('intro-settled'),false);});
test('Unavailable portrait leaves the guide entry usable',async()=>{const app=setup({broken:true});await app.advance(4000);assert.equal(app.node('#intro-dialog').classList.contains('intro-no-portrait'),true);app.node('#intro-enter').fire('click');assert.equal(app.node('#intro-dialog').open,false);});
test('Corrupt settings cannot introduce external images, NaN styling or obsolete pose controls',()=>{const app=setup({seen:true});const clean=JSON.parse(JSON.stringify(app.context.appearance.normalize({mode:'invalid',source:'https://example.invalid',shade:Infinity,blur:-20,position:'bad',pose:'../../outside'})));assert.deepEqual(clean,{mode:'light',source:'preset',shade:55,blur:0,position:'center'});});

test('Page art follows navigation without replaying the opening or accepting arbitrary asset paths',async()=>{
  const app=setup({seen:true});
  app.context.appearance.showView('map');await app.flush();
  assert.equal(app.node('#view-map .campus-heading-figure').src,'/assets/mascot-point.png');
  assert.equal(app.node('#campus-character-watermark').src,'/assets/creative-back-v2.png');
  app.context.appearance.showView('preparation');await app.flush();
  assert.equal(app.node('#view-preparation .campus-heading-figure').classList.contains('is-chibi'),true);
  assert.equal(app.node('#campus-character-watermark').src,'/assets/chibi-ready.png');
  app.context.appearance.showView('../../outside');await app.flush();
  assert.equal(app.node('#campus-character-watermark').src,'/assets/mascot-wave.png');
  assert.equal(app.node('#intro-dialog').open,false);assert.deepEqual(app.requests,[]);
});

test('A late illustration decode cannot reveal the next illustration before it is ready',async()=>{
  const app=setup({seen:true}),watermark=app.node('#campus-character-watermark'),pending=[];
  watermark.decode=()=>new Promise(resolve=>pending.push(resolve));
  app.context.appearance.showView('map');app.context.appearance.showView('plan');
  pending[0]();await app.flush();assert.equal(watermark.hidden,true);
  pending[1]();await app.flush();assert.equal(watermark.hidden,false);
  assert.equal(watermark.src,'/assets/mascot-reading.png');
});
