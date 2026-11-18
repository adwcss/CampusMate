"""Package existing art, Pixi and the shared puppet into an offline HTML file.
No image pixels are edited: PNG bytes are embedded verbatim as data URLs.
"""
from pathlib import Path
import base64
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/portrait-interactive'
OUT.mkdir(parents=True, exist_ok=True)

def data(name):
    return 'data:image/png;base64,' + base64.b64encode((ROOT / 'frontend/assets' / name).read_bytes()).decode()

image, alpha = data('cover-portrait-v3.png'), data('cover-portrait-v2.png')
library = (ROOT / 'frontend/assets/pixi-7.4.3.min.js').read_text(encoding='utf-8')
# Do not request a sourcemap or allow an embedded string to close the script tag.
library = library.split('//# sourceMappingURL=')[0].replace('</script', '<\\/script')
license_text = (ROOT / 'frontend/assets/pixi-LICENSE.txt').read_text(encoding='utf-8')
library = f'/*\n{license_text}\n*/\n{library}'
runtime = (ROOT / 'frontend/cover.js').read_text(encoding='utf-8')
html = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>初到 · 少女交互动画</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#edf1f8;color:#364c73;font:14px/1.7 system-ui,"Microsoft YaHei",sans-serif}button,input{font:inherit}button{cursor:pointer;color:inherit}button:focus-visible,input:focus-visible,summary:focus-visible,#cover-stage:focus-visible{outline:2px solid #536db0;outline-offset:5px}
#intro-dialog{position:fixed;inset:0;width:100%;height:100dvh;max-width:none;max-height:none;border:0;margin:0;padding:0;color:inherit;overflow:hidden;background:radial-gradient(ellipse at var(--portrait-light-x,60%) var(--portrait-light-y,30%),#fff 0%,#eef2fa 48%,#dbe4f3 100%)}
.grain{pointer-events:none;position:absolute;inset:0;opacity:.22;background:repeating-linear-gradient(0deg,transparent 0px,transparent 3px,#c7d3e312 4px)}
header{position:absolute;z-index:4;top:28px;left:4vw;right:4vw;display:flex;justify-content:space-between;align-items:center;pointer-events:none}header span{letter-spacing:3px;font-size:11px}header small{font-size:10px;letter-spacing:2px;opacity:.6}
.halo{position:absolute;left:26%;top:8%;width:62%;aspect-ratio:1;border:1px solid #a3b7d32b;border-radius:50%;box-shadow:0 0 0 50px #bfd1ec0b,0 0 0 100px #bfd1ec0b}
#cover-stage{position:absolute;inset:2% 0 16% 10%;overflow:hidden;z-index:2}.cover-art{position:absolute;inset:0;pointer-events:none}.cover-canvas,.intro-portrait{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.cover-ready .intro-portrait{visibility:hidden}
.desk{position:absolute;z-index:3;left:4vw;right:4vw;bottom:4vh;min-height:22vh;border-radius:16px;border:1px solid #fff;border-top:3px solid #c0cde4;background:linear-gradient(110deg,#fbfcfff7,#e9eff9f2);box-shadow:0 -12px 45px #576e8f0c,0 16px 30px #34466b13;padding:24px 32px;display:grid;grid-template-columns:1fr 1.2fr;gap:10px 28px;align-items:center}
h1{font:500 clamp(38px,4.4vw,68px)/1.15 "KaiTi","STKaiti",serif;margin:0;letter-spacing:5px}h1 span{display:block;font:400 18px/1.5 system-ui;margin-top:8px;letter-spacing:2px}.cover-invitation{margin:0;font-size:12px;color:#6a7e9e}.controls{display:flex;flex-wrap:wrap;gap:7px;justify-content:flex-end}button{border:1px solid #becce3;background:#ffffff9e;padding:7px 13px;border-radius:8px;transition:background .3s,box-shadow .3s}button:hover{background:#fff;box-shadow:0 3px 12px #475e8820}button[aria-pressed=true]{color:#fff;background:#4d6597;border-color:#4d6597}.settings{display:flex;gap:20px;align-items:center;justify-content:flex-end;font-size:11px;color:#6a7e9e}.settings label{display:flex;gap:6px;align-items:center}.settings button{font-size:11px;padding:3px 9px}#cover-hint-text{font-size:10px;opacity:.7}.notes{position:absolute;z-index:8;top:63px;left:4vw;max-width:min(400px,90vw);font-size:12px}.notes summary{cursor:pointer;color:#6b80a1}.notes[open]{padding:15px;background:#f9fbffef;border:1px solid #d4deed;border-radius:12px;box-shadow:0 15px 40px #35476920}.notes p{margin:10px 0 0}.badge{position:absolute;z-index:1;left:4%;top:28%;writing-mode:vertical-rl;font-size:12px;letter-spacing:6px;color:#9badc8}.cover-hint{display:none}
@media(max-width:700px){header{top:20px}header small{display:none}#cover-stage{inset:13% -26% 31%;}.desk{left:4%;right:4%;bottom:3%;padding:18px;grid-template-columns:1fr;gap:12px}h1{font-size:32px}h1 span{font-size:13px;display:inline;margin-left:15px}.controls{justify-content:flex-start;gap:5px}.controls button{padding:6px 9px;font-size:12px}.settings{justify-content:flex-start}.cover-invitation{font-size:11px}.badge{display:none}#cover-hint-text{display:none}}
@media(prefers-reduced-motion:reduce){.cover-canvas{display:none}.cover-ready .intro-portrait{visibility:visible}#cover-hint-text{display:none}}
</style></head><body>
<!-- All art and library bytes below are embedded: this file makes no network requests. -->
<dialog id="intro-dialog" open class="intro-settled" aria-label="初到，校园少女交互演示">
 <div class="grain"></div><div class="halo"></div>
 <header><span>河南科技职业大学 · 初到</span><small>PORTRAIT STUDY / 01</small></header>
 <div class="badge" aria-hidden="true">风经过的时候，故事开始了</div>
 <details class="notes"><summary>交互说明与分层思路</summary><p>鼠标移到脸部左侧、中间、右侧，分别触发疑惑、好奇、开心。移出立绘区域会恢复待机。也可点下方按钮，或聚焦人物后按方向键，按 Home 回正。</p><p>眼睛、眉毛、嘴角、脸颊和头发各有独立的区域遮罩，用同一张立绘实现局部形变。分区坐标和动画参数可在源码注释中查看。</p><p>待机时发丝轻轻流动，面部有轻微呼吸和偶发偏头。身体、托腮手和脖子固定。开启系统“减少动态效果”后显示静态原画。</p></details>
 <div id="cover-stage" tabindex="0" role="group" aria-label="角色交互区域，方向键切换神态，Home回正"><div class="cover-art"><img class="intro-portrait" alt="紫蓝长发、红桥与海鸥发饰的托腮少女" width="1536" height="1024"></div><span id="cover-hint-text" hidden></span></div>
 <section class="desk" aria-label="角色动画控制"><h1>初到<span>与你，一起启程。</span></h1>
 <div class="controls" role="group" aria-label="神态预览"><button data-portrait-expression="auto" aria-pressed="true">鼠标跟随</button><button data-portrait-expression="idle" aria-pressed="false">待机</button><button data-portrait-expression="puzzled" aria-pressed="false">疑惑</button><button data-portrait-expression="curious" aria-pressed="false">好奇</button><button data-portrait-expression="happy" aria-pressed="false">开心</button></div>
 <p class="cover-invitation" aria-live="polite">慢慢来，我陪你一起启程。</p>
 <div class="settings"><button data-portrait-pause aria-pressed="false">暂停动画</button><span id="demo-status">独立单文件 · 可离线运行</span></div>
 </section>
</dialog>
<script>/* PixiJS 7.4.3 · MIT license. Bundled locally for offline use. */
__LIBRARY__
</script>
<script>window.COVER_ASSETS=__CONFIG__;const portrait=document.querySelector('.intro-portrait');portrait.src=COVER_ASSETS.image;portrait.style.maskImage='url('+COVER_ASSETS.alpha+')';portrait.style.maskSize='contain';portrait.style.maskPosition='center';portrait.style.maskRepeat='no-repeat';</script>
<script>__RUNTIME__</script>
</body></html>'''
html=html.replace('__LIBRARY__',library).replace('__CONFIG__',json.dumps({'image':image,'alpha':alpha},ensure_ascii=False)).replace('__RUNTIME__',runtime)
dest=OUT/'少女交互动画.html'
dest.write_text(html,encoding='utf-8')
print(f'Built {dest.name} ({dest.stat().st_size/1024/1024:.1f} MB)')
