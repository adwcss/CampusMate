"""Code-authored SVG illustration, with inherited image coordinates, never a survey."""
from html import escape
from .catalog import PLACES


def render_map(school):
    title = escape(school["name"] + " · 校园插画示意")
    notice = escape(school["map_notice"])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 928 1120" role="img" aria-labelledby="title desc"><title id="title">{title}</title><desc id="desc">{notice}</desc>',
             '<defs><pattern id="lawn" width="24" height="24" patternUnits="userSpaceOnUse"><rect width="24" height="24" fill="#edf5eb"/><circle cx="5" cy="7" r="1" fill="#cbdcc8"/></pattern><pattern id="roof" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M0 4H9" stroke="#fff" stroke-opacity=".5"/></pattern></defs>',
             '<rect x="4" y="4" width="920" height="1112" rx="38" fill="url(#lawn)" stroke="#a8c4b7" stroke-width="4"/>',
             f'<text x="42" y="52" font-family="sans-serif" font-size="24" fill="#244c64">{title}</text>',
             '<text x="42" y="84" font-family="sans-serif" font-size="16" fill="#49615c">非官方地图 · 非实测比例 · 装饰线不代表可通行道路</text>']
    if school.get("legacy_content"):
        parts += ['<path d="M440 130V1000M70 570H850" stroke="#fff" stroke-width="30" fill="none"/>',
                  '<ellipse cx="743" cy="860" rx="95" ry="130" fill="#b8dce6" stroke="#8dbfce" stroke-width="4"/>',
                  '<ellipse cx="745" cy="862" rx="65" ry="100" fill="none" stroke="#ecf6fa" stroke-width="3"/>']
        colors = {"宿舍区": "#e8b89e", "教学与办公区": "#8eb9d5", "餐饮与服务区": "#e8cb7e", "场馆与活动区": "#a4c7a4"}
        for place in PLACES:
            x, y = place["x"] * 9.28, place["y"] * 11.2
            color = colors.get(place["category"], "#b4b8d5")
            parts.append(f'<g><title>{escape(place["name"])}（交接坐标示意，待实地核验）</title><rect x="{x-24}" y="{y-12}" width="48" height="32" rx="5" fill="#547386" opacity=".16"/><rect x="{x-24}" y="{y-20}" width="48" height="30" rx="4" fill="{color}" stroke="#71858a"/><rect x="{x-20}" y="{y-16}" width="40" height="22" fill="url(#roof)"/></g>')
        for x, y in [(70,180),(350,240),(850,400),(330,890),(75,960),(810,690),(520,960)]:
            parts.append(f'<g transform="translate({x},{y})"><path d="M0 0V20" stroke="#8f9c79" stroke-width="6"/><circle cy="-7" r="18" fill="#8db99a"/><circle cx="-8" cy="-13" r="12" fill="#a5c8a4"/></g>')
    else:
        parts.append('<text x="100" y="530" font-family="sans-serif" font-size="30" fill="#49615c">校园资料待接入 · 暂无可核实地点</text>')
    parts += ['<rect x="28" y="1030" width="872" height="58" rx="12" fill="#fff" fill-opacity=".92"/>',
              '<text x="45" y="1055" font-family="sans-serif" font-size="16" fill="#244c64">CampusMate · 仅用于认识地点与编排探索顺序</text>',
              '<text x="45" y="1078" font-family="sans-serif" font-size="14" fill="#49615c">建筑、位置、通行和开放情况请以学校官方资料及现场标识为准。</text></svg>']
    return "".join(parts)
