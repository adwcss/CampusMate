"""Focused, source-linked preparation answers for the legacy campus."""
import re
from .retriever.retriever import TRUST_LABELS

ARRIVAL_CONTEXT = r"报[到道]|入学|新生|接站|迎新|开学"


def arrival_answer(question, retriever, school):
    if not school.get("legacy_content") or not re.search(ARRIVAL_CONTEXT, question):
        return None
    if re.search(r"彩票|股票|天气|食谱|量子|密码|管理员|系统提示|忽略.*指令", question):
        return None
    if re.search(r"学费|缴费|宿舍|军训|社团|竞赛|资助|户口|校园卡|党团", question):
        return None
    topics = [
        (r"材料|证件|带什么|要带|带啥|准备啥|录取通知书|身份证|证件照|复印件", "报到材料", "入学准备清单.md", "一、必备材料",
         "可以先把录取通知书原件和身份证放进随身文件袋，再对照本届入学须知核对复印件、证件照和档案要求。", "identity"),
        (r"接站|车站|高铁|外地|接驳|迎新车|接送|火车|坐车过去|下车.*怎么去", "交通与接站", "入学指南补充.md", "三、交通与接站",
         "从学校官网或随通知书发放的入学须知找本届接站安排，核对站点、服务时段和集合位置。下方 2024 级资料可用来了解往年流程。", "travel"),
        (r"先准备|提前准备|报[到道]时间|什么时候报[到道]|几号报[到道]|报[到道]日期|提前.{0,6}做什么|哪天.{0,4}(?:到校|报[到道])|啥时候.{0,4}(?:到校|报[到道])|何时.{0,4}(?:到校|报[到道])|订票.{0,8}(?:之前|前)|出发前.{0,8}(?:查|核对|确认)", "出发前核对", "入学指南补充.md", "一、报到时间",
         "先查本届入学须知里的报到日期和入口，再安排车票。也可以现在就把入学须知和随身证件放到一起。下方日期适用于 2024 级。", "notice"),
    ]
    matched = [topic for topic in topics if re.search(topic[0], question)]
    if len(matched) < 2:
        return None
    chunks = {(c["source"], c["section"]): c for c in retriever.chunks}
    sources, paragraphs, templates = [], [], []
    for _, title, filename, section, advice, template in matched:
        source = chunks.get((filename, section))
        if not source:
            return None
        sources.append({**source, "trust_label": TRUST_LABELS[source["source_type"]]})
        paragraphs.append(f"{len(sources)}. {title}\n{advice}【{len(sources)}】")
        templates.append(template)
    return "\n\n".join(paragraphs), sources, templates
