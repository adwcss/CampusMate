"""Build the stylized scene's place inventory from the retained map notes."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
text = (root / '校园地图.md').read_text(encoding='utf-8')
places = []
for title, body in re.findall(r'## (.*?)\n\n(.*?)(?=\n## |\Z)', text, re.S):
    xy = re.search(r'(?:坐标：|坐标)([\d.]+)%[、，]([\d.]+)%', body)
    if not xy:
        continue
    category = '生活' if '园' in title and re.search(r'\d', title) else '餐饮' if '餐厅' in title else '运动' if any(s in title for s in ['体育场', '篮球', '游泳']) else '景观' if any(s in title for s in ['湖', '广场', '百草', '光明', '停车']) else '学习'
    desc = re.split(r'图上百分比|图上坐标', body.strip())[0].strip()
    places.append(dict(id=f'p{len(places)}', name=title, x=float(xy[1]), z=float(xy[2]), category=category, description=desc, interior='photos' if category == '生活' else None))
(root / 'frontend/campus3d/places.json').write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Built {len(places)} map locations')
