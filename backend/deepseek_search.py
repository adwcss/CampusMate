"""Retrieve public evidence for questions the local knowledge base cannot answer."""
from datetime import datetime, timezone
import hashlib
import json
import re
import urllib.request
from urllib.parse import urldefrag, urlsplit

from .schools import official_url
from .search_service import NoRedirect

CONTEST = r"竞赛|比赛|大赛|赛道|初赛|复赛|决赛|蓝桥杯|挑战杯|建模|华为\s*ICT"
SCOPE_QUESTION = r"考哪|考什么|考些|考核内容|考查什么|考察什么|考查范围|考试|大纲|知识点|题型|考点|考.*知识"
SCOPE_EVIDENCE = r"考试内容|考试范围|考(?:查|察|核)(?:内容|范围|知识点)|考(?:查|察)[^。；\n]{2,70}(?:方向|知识|能力)|(?:竞赛|大赛|赛道)内容.{0,12}(?:包括|涵盖|有)|考试大纲|考点|题型"
SCHOOL_CONTEXT = r"本校|校内|我们学校|河职大|河南科技职业大学"
SCHOOL_ARRANGEMENT = r"入学|报[到道]|接站|军训|缴费|学费|住宿费|宿舍|校门|校园卡|一卡通|学籍|调宿"
ICT_CONTEST = r"华为\s*ict|\bict\s*(?:大赛|竞赛|网络赛道)"
NETWORK_TOPICS = r"数据通信|数通|Datacom|网络安全|防火墙|Security|WLAN|无线局域网|路由|交换"
PRIVATE_QUERY = r"(?i)https?://|\bsk-[\w-]+|(?:[0-9][ -]?){7,}|[\w.+-]+@[\w.-]+|身份证号|密码|密钥|准考证号|学号[:：]"


def asks_contest_scope(query):
    return bool(re.search(CONTEST, query, re.I) and re.search(SCOPE_QUESTION, query))


def has_contest_scope(source, query):
    if re.search(ICT_CONTEST, query, re.I) and re.search(r"网络(?:赛道|方向)", query):
        return bool(re.search(r"网络赛道|赛道[一1]：\s*网络|Network Track", source, re.I)
                    and re.search(NETWORK_TOPICS, source, re.I))
    return bool(re.search(SCOPE_EVIDENCE, source))


class DeepSeekSearch:
    def __init__(self, settings, school):
        self.settings = settings
        self.school = school

    def enabled(self):
        return self.settings.allow_search and self.settings.remote_enabled()

    def search(self, query):
        if not self.enabled():
            return [], "not_configured"
        if re.search(PRIVATE_QUERY, query):
            return [], "not_requested"
        contest_scope = asks_contest_scope(query)
        school_only = bool(re.search(SCHOOL_CONTEXT, query) or (
            not re.search(CONTEST, query, re.I) and re.search(SCHOOL_ARRANGEMENT, query)
        ))
        national_math = bool(re.search(r"全国大学生数学竞赛|^(?:请问)?(?:大学生)?数学竞赛", query))
        huawei_ict = bool(re.search(ICT_CONTEST, query, re.I))
        edition = None
        domains = self.school["official_domains"] if school_only else []
        if not school_only and contest_scope and national_math:
            domains = ["cmathc.org.cn", "cms.org.cn"]
            edition = re.search(r"20\d{2}年|第[一二三四五六七八九十\d]+届", query)
            focus = next((word for word in ("决赛", "初赛") if word in query), "初赛")
            public_query = f"{edition[0] if edition else ''} 全国大学生数学竞赛 {focus} 考试内容 数学专业类 非数学专业类 " + " OR ".join(
                "site:" + domain for domain in domains
            )
        elif not school_only and contest_scope and huawei_ict:
            domains = ["huawei.com"]
            edition = re.search(r"20\d{2}\s*[-—–至]\s*20\d{2}", query)
            topic = re.sub(ICT_CONTEST, "", query, count=1, flags=re.I).strip()
            public_query = f"华为 ICT 大赛 实践赛 {topic[:75]} 考察内容 site:huawei.com"
        elif domains:
            restriction = " site:" + domains[0]
            public_query = f"{self.school['name']} {query}"[:128 - len(restriction)] + restriction
        else:
            if school_only:
                return [], "no_official_results"
            public_query = f"{query[:95]} 主办方 官方 竞赛大纲" if contest_scope else query[:128]

        sources, status = self._search(public_query.strip(), query, domains, edition)
        if sources or status != "no_official_results":
            return sources, status
        if huawei_ict and not school_only and "网络赛道" in query:
            term = f"{edition[0]} " if edition else ""
            retry = f"{term}华为 ICT 大赛 网络赛道 考核内容 赛道说明 site:huawei.com"
        elif not school_only and not domains and contest_scope:
            retry = query[:128]
        else:
            return sources, status
        return self._search(retry.strip(), query, domains, edition)

    def _search(self, public_query, query, domains, edition):
        edition_token = re.sub(r"[\s—–至-]", "", edition[0]) if edition else ""
        body = {"query": public_query, "count": 5}
        request = urllib.request.Request(
            "https://api.deepseek.com/v1/tools/search",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.settings.api_key},
            method="POST",
        )
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=12) as response:
                raw = response.read(262145)
            if len(raw) > 262144:
                raise ValueError("oversized response")
            results = json.loads(raw)["results"]
            if "cmathc.org.cn" in domains:
                results.sort(key=lambda item: not bool(re.match(r"关于举办第.+届全国大学生数学竞赛的通知", item["title"])))
            sources, seen = [], set()
            now = datetime.now(timezone.utc).isoformat()
            for item in results:
                url = urldefrag(item["url"]).url
                parsed = urlsplit(url)
                host = parsed.hostname or ""
                title = item["title"].strip()
                snippet = (item["summary"] or item["snippet"]).strip()
                if parsed.scheme not in {"http", "https"} or "." not in host or parsed.username is not None:
                    continue
                if domains:
                    relevant = any(host == domain or host.endswith("." + domain) for domain in domains)
                else:
                    relevant = item.get("authority", 0) >= 2 and item.get("rerank_score", 0) >= 1.5
                if domains == self.school["official_domains"]:
                    relevant = official_url(url, self.school) and item.get("rerank_score", 0) >= 1.5
                if not relevant or url in seen or not title or not snippet:
                    continue
                if edition_token and edition_token not in re.sub(r"[\s—–至-]", "", title + snippet):
                    continue
                if asks_contest_scope(query) and not has_contest_scope(snippet, query):
                    continue
                seen.add(url)
                published = item.get("date") or ""
                sources.append({
                    "id": hashlib.sha256(url.encode()).hexdigest()[:16], "school_id": self.school["school_id"],
                    "source": title[:200], "section": "DeepSeek 联网摘要", "text": snippet[:1800],
                    "source_type": "deepseek_web", "evidence_origin": "deepseek_search", "verified": False,
                    "trust_label": "联网来源摘要", "urls": [url], "effective_year": None,
                    "published_at": published[:10] if re.match(r"\d{4}-\d{2}-\d{2}", published) else None,
                    "collected_at": now, "retrieved_at": now,
                    "caveat": "适用年份和细节请对照来源原文。",
                })
                if len(sources) == 3:
                    break
            return sources, "ok" if sources else "no_official_results"
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return [], "unavailable"
