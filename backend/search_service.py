"""Independent search providers for official campus sources."""
from datetime import datetime, timezone
import hashlib
import html
import json
import re
import threading
import urllib.request
from urllib.parse import urlencode
from .schools import official_url
from .official_notices import OfficialNotices

TOPICS = [(r"军训", "新生 军训 通知"), (r"费用|多少钱|学费|住宿费|收费|缴费", "新生 收费 通知"),
          (r"宿舍|床位", "新生 宿舍 通知"), (r"贷款|资助|助学|绿色通道", "新生 资助 绿色通道"),
          (r"地图|图书馆|餐厅|食堂|校园", "校园地图 开放通知"), (r"专业|院系", "招生 专业"),
          (r"社团|学生会", "学生组织 招新"), (r"竞赛|比赛", "竞赛 通知")]


def search_query(query, school):
    # Send a fixed public topic only: no session, full question or personal history.
    topic = next((topic for pattern, topic in TOPICS if re.search(pattern, query)), "新生 报到 入学须知")
    return "site:" + school["official_domains"][0] + " " + school["name"] + " " + topic


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Search API redirects are disabled")


class SearchService:
    def __init__(self, settings, school):
        self.settings, self.school = settings, school
        self.calls = 0
        self.lock = threading.Lock()
        self.notices = OfficialNotices(school, urllib.request.build_opener(NoRedirect()))

    def enabled(self):
        if self.settings.search_provider == "official":
            return self.settings.allow_search and bool(self.notices.pages)
        return bool(self.settings.allow_search and self.settings.search_provider == "brave"
                    and self.settings.search_key and self.school["official_domains"])

    def search(self, query):
        if not self.enabled():
            return [], "not_configured"
        if self.settings.search_provider == "official":
            with self.lock:
                return self.notices.search(query)
        public_query = search_query(query, self.school)
        url = "https://api.search.brave.com/res/v1/web/search?" + urlencode({"q": public_query, "count": 5, "text_decorations": "false"})
        request = urllib.request.Request(url, headers={"Accept": "application/json", "X-Subscription-Token": self.settings.search_key})
        try:
            with self.lock:
                self.calls += 1
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=8) as response:
                raw = response.read(262145)
            if len(raw) > 262144:
                raise ValueError("oversized response")
            data = json.loads(raw)
            sources, seen = [], set()
            for item in data.get("web", {}).get("results", []):
                url = item.get("url", "")
                if not isinstance(url, str) or not official_url(url, self.school) or url in seen:
                    continue
                title, description = item.get("title"), item.get("description")
                if not isinstance(title, str) or not isinstance(description, str):
                    continue
                seen.add(url)
                clean = lambda value: html.unescape(re.sub(r"<[^>]*>", "", value))
                snippet = clean(description)[:2000]
                if not snippet.strip():
                    continue
                now = datetime.now(timezone.utc).isoformat()
                published = item.get("page_age")
                sources.append({"id": hashlib.sha256(url.encode()).hexdigest()[:16], "school_id": self.school["school_id"],
                                "source": clean(title)[:200], "section": "联网搜索摘要（未核验正文）", "text": snippet,
                                "source_type": "web_snippet", "evidence_origin": "search_api", "verified": False,
                                "official_domain": True, "trust_label": "官方域名搜索摘要，正文待核实", "urls": [url],
                                "effective_year": None, "collected_at": now, "retrieved_at": now,
                                "published_at": published if isinstance(published, str) else None,
                                "caveat": "来自Brave搜索服务的摘要；官方域名不等于已核验内容，发布日期缺失时不推测，不作为办理依据。"})
                if len(sources) == 3:
                    break
            return sources, "ok" if sources else "no_official_results"
        except Exception:
            # Never expose a provider error, request URL or authentication header.
            return [], "unavailable"


def possible_conflicts(local, web):
    result = []
    for left in local:
        for right in web:
            for label, pattern in [("金额", r"\d+(?:\.\d+)?(?=\s*元)"), ("日期", r"20\d{2}[-年]\d{1,2}[-月]\d{1,2}日?")]:
                a, b = set(re.findall(pattern, left["text"])), set(re.findall(pattern, right["text"]))
                if a and b and a != b:
                    result.append({"kind": label, "source_ids": [left["id"], right["id"]],
                                   "message": "本地资料与搜索摘要出现不同" + label + "，可能属于不同年份或项目；请打开原文核对，系统不自动裁定。"})
            if left.get("effective_year") and str(left["effective_year"]) not in right["text"] and re.search(r"20\d{2}", right["text"]):
                result.append({"kind": "适用年份", "source_ids": [left["id"], right["id"]], "message": "本地历史资料与联网摘要可能适用不同年份，请核对当年官方通知。"})
    return result[:6]
