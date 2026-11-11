"""Read public school announcement titles and links, without copying articles."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import re
from time import monotonic
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request
from urllib.robotparser import RobotFileParser

from .schools import official_url

PUBLIC_PAGES = {
    "hnvust": (
        "https://www.hnvust.cn/xwdt/tzgg.htm",
        "https://zhaoshengchu.hnvust.cn/",
    ),
}
AGENT = "CampusMateNotices"
TOPIC_WORDS = (
    (r"报到|入学|迎新", ("报到", "入学", "迎新", "新生")),
    (r"招生|录取|专业", ("招生", "录取", "专业")),
    (r"费用|收费|学费|缴费", ("收费", "学费", "缴费")),
)


class NoticeLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = {}
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            fields = dict(attrs)
            self.anchor = (fields.get("href") or "", fields.get("title") or "", [])

    def handle_data(self, data):
        if self.anchor:
            self.anchor[2].append(data)

    def handle_endtag(self, tag):
        if tag != "a" or not self.anchor:
            return
        href, title, words = self.anchor
        self.anchor = None
        title = " ".join((title or "".join(words)).split())
        if len(title) >= 8:
            self.items[href] = title[:180]


def read_public(opener, url):
    request = Request(url, headers={"User-Agent": AGENT})
    with opener.open(request, timeout=3) as response:
        raw = response.read(524289)
        if len(raw) > 524288:
            raise ValueError("oversized public page")
        return raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")


class OfficialNotices:
    def __init__(self, school, opener):
        self.school = school
        self.opener = opener
        self.pages = PUBLIC_PAGES.get(school["school_id"], ())
        self.cache = {}

    def index(self, page):
        cached = self.cache.get(page)
        if cached and monotonic() < cached[0]:
            return cached[1:]
        try:
            robot_url = urljoin(page, "/robots.txt")
            parser = RobotFileParser(robot_url)
            try:
                parser.parse(read_public(self.opener, robot_url).splitlines())
            except HTTPError as error:
                if error.code not in (404, 410):
                    raise
                parser.parse([])
            if not parser.can_fetch(AGENT, page):
                raise ValueError("public index restricted")
            links = NoticeLinks()
            links.feed(read_public(self.opener, page))
            items = {}
            for href, title in links.items.items():
                url = urljoin(page, href)
                if official_url(url, self.school) and re.fullmatch(r"/info/\d+/\d+\.htm", urlsplit(url).path):
                    items[url] = title
            row = (items, datetime.now(timezone.utc).isoformat())
            ttl = 1800
        except (OSError, ValueError):
            row, ttl = ({}, None), 300
        self.cache[page] = (monotonic() + ttl, *row)
        return row

    def search(self, query):
        words = {word for word in ("军训", "宿舍", "资助", "竞赛", "比赛", "图书馆") if word in query}
        for pattern, synonyms in TOPIC_WORDS:
            if re.search(pattern, query):
                words.update(synonyms)
        if not words:
            return [], "no_official_results"
        ranked = {}
        available = False
        for page in self.pages:
            if not official_url(page, self.school):
                continue
            items, fetched_at = self.index(page)
            available |= bool(fetched_at)
            for url, title in items.items():
                score = sum(word in title for word in words)
                if score:
                    ranked[url] = (score, title, fetched_at)
        sources = []
        for url, (_, title, fetched_at) in sorted(ranked.items(), key=lambda row: -row[1][0])[:3]:
            sources.append({
                "id": hashlib.sha256(url.encode()).hexdigest()[:16], "school_id": self.school["school_id"],
                "source": title, "section": "学校官网公告索引", "text": title,
                "source_type": "official_notice_link", "evidence_origin": "official_index",
                "verified": False, "official_domain": True, "urls": [url],
                "effective_year": None, "published_at": None, "collected_at": fetched_at, "retrieved_at": fetched_at,
                "caveat": "此条仅提供学校官网公告标题和原文入口。具体时间、资格与办理要求请打开原文。",
            })
        return sources, "ok" if sources else "no_official_results" if available else "unavailable"
