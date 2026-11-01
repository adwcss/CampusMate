"""Public verification links only. No network, browser launch, scraping or paid API."""
from urllib.parse import urlencode


def verification_links(query, school=None):
    if school is None:
        from .schools import load_schools, DEFAULT_SCHOOL
        school = load_schools()[DEFAULT_SCHOOL]
    if not school["official_domains"]:
        return []
    # Fixed topic vocabulary: never place the full question, history or key in a URL.
    topic = "新生 入学须知"
    for words, value in [(("军训",), "新生 军训"), (("学费", "住宿费", "收费"), "新生 收费通知"),
                         (("社团", "学生会", "招新"), "社团 学生组织 招新"),
                         (("图书馆", "开放", "营业"), "图书馆 开放通知"),
                         (("报到", "接站", "入学"), "新生 报到 入学须知"),
                         (("竞赛", "比赛", "蓝桥", "建模"), "竞赛 通知")]:
        if any(word in query for word in words):
            topic = value
            break
    scoped = "site:" + school["official_domains"][0] + " " + school["name"] + " " + topic
    links = [{"label": "学校官网", "url": school["official_home"]},
             {"label": "搜索学校网站的相关通知", "url": "https://www.baidu.com/s?" + urlencode({"wd": scoped})}]
    if "蓝桥" in query:
        links.append({"label": "蓝桥杯主办方入口", "url": "https://dasai.lanqiao.cn/"})
    if "数学建模" in query:
        links.append({"label": "全国数学建模竞赛组委会", "url": "https://www.mcm.edu.cn/"})
    return links
