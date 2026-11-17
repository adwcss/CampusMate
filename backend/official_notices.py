"""Discover official announcements and extract bounded article evidence."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import hashlib
from html.parser import HTMLParser
import re
from threading import Lock
from time import monotonic
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request
from urllib.robotparser import RobotFileParser

from .schools import official_url

AGENT = "CampusMateNotices"
ARTICLE_PATH = r"(?:/[^/?#]+)*/(?:info/\d+/\d+\.htm|c\d+a\d+/page\.htm)"
TOPIC_WORDS = (
    (r"报到|入学|迎新", ("报到", "入学", "迎新", "新生")),
    (r"招生|录取|专业", ("招生", "录取", "专业")),
    (r"费用|收费|学费|缴费", ("收费", "学费", "缴费")),
    (r"绿色通道|缓缴|资助", ("绿色通道", "缓缴", "资助")),
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
        if len(title) >= 5:
            self.items[href] = title[:180]


def read_public(opener, url):
    request = Request(url, headers={"User-Agent": AGENT})
    with opener.open(request, timeout=3) as response:
        if response.headers.get_content_type() not in {"text/html", "application/xhtml+xml", "text/plain"}:
            raise ValueError("unsupported public page")
        raw = response.read(524289)
        if len(raw) > 524288:
            raise ValueError("oversized public page")
        return raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")


class NoticeArticle(HTMLParser):
    """Extract recognized article containers without menus or executable content."""
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.containers = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template", "noscript"}:
            self.hidden += 1
        if self.hidden:
            return
        fields = dict(attrs)
        classes = set((fields.get("class") or "").lower().split())
        article = tag == "article" or fields.get("id") == "vsb_content" or bool(
            classes & {"v_news_content", "wp_articlecontent", "article-content"}
        )
        if tag in {"div", "article"}:
            self.containers.append(article or self.active)
        if self.active and tag in {"p", "br", "li", "tr", "h2", "h3"}:
            self.blocks.append("\n")

    @property
    def active(self):
        return bool(self.containers and self.containers[-1])

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template", "noscript"} and self.hidden:
            self.hidden -= 1
            return
        if self.hidden:
            return
        if self.active and tag in {"p", "div", "li", "tr", "h2", "h3"}:
            self.blocks.append("\n")
        if tag in {"div", "article"} and self.containers:
            self.containers.pop()

    def handle_data(self, data):
        if self.active and not self.hidden:
            self.blocks.append(data)


def published_date(markup):
    for value in re.findall(r'(?:发布时间|发布日期|<time[^>]*>)\s*[:：]?\s*(20\d{2}[-年]\d{1,2}[-月]\d{1,2})', markup):
        try:
            return date(*(int(part) for part in re.findall(r"\d+", value))).isoformat()
        except ValueError:
            continue
    return None


class OfficialNotices:
    def __init__(self, school, opener):
        self.school = school
        self.opener = opener
        self.pages = school.get("notice_pages", ())
        self.articles = school.get("notice_articles", {})
        self.cache = {}
        self.robots = {}
        self.cache_lock = Lock()

    def map_asset(self):
        url = self.school.get("official_map_asset")
        if not url or not self.allowed(url):
            return None
        request = Request(url, headers={"User-Agent": AGENT, "Referer": self.school["official_map"]})
        with self.opener.open(request, timeout=6) as response:
            raw = response.read(12_000_001)
        if len(raw) > 12_000_000:
            return None
        for signature, mime in ((b"%PDF-", "application/pdf"), (b"\xff\xd8\xff", "image/jpeg"),
                                (b"\x89PNG\r\n\x1a\n", "image/png")):
            if raw.startswith(signature):
                return raw, mime
        return None

    def allowed(self, url):
        if not official_url(url, self.school):
            return False
        robot_url = urljoin(url, "/robots.txt")
        cached = self.robots.get(robot_url)
        if not cached or monotonic() >= cached[0]:
            parser = RobotFileParser(robot_url)
            try:
                parser.parse(read_public(self.opener, robot_url).splitlines())
            except HTTPError as error:
                if error.code not in (404, 410):
                    raise
                parser.parse([])
            self.robots[robot_url] = cached = (monotonic() + 1800, parser)
        return cached[1].can_fetch(AGENT, url)

    def verify(self, source, query):
        url = source["urls"][0]
        if not official_url(url, self.school) or (url not in self.articles and not re.fullmatch(ARTICLE_PATH, urlsplit(url).path)):
            return source
        key = ("article", url)
        cached = self.cache.get(key)
        if not cached or monotonic() >= cached[0]:
            lines, published = [], None
            try:
                if self.allowed(url):
                    markup = read_public(self.opener, url)
                    article = NoticeArticle()
                    article.feed(markup)
                    lines = [" ".join(line.split()) for line in "".join(article.blocks).splitlines() if line.strip()]
                    published = published_date(markup)
            except (OSError, ValueError, LookupError):
                pass
            cached = (monotonic() + (1800 if lines else 300), lines, published, datetime.now(timezone.utc).isoformat())
            with self.cache_lock:
                if len(self.cache) >= 256:
                    self.cache.pop(next(iter(self.cache)))
                self.cache[key] = cached
        _, lines, published, collected = cached
        title = source["source"]
        if len("".join(lines)) < 40:
            return source
        from .retriever.retriever import terms
        words = set(terms(query))
        scored = [(len(words.intersection(terms(line))), index) for index, line in enumerate(lines)]
        ranked = sorted(((-score, index) for score, index in scored if score), key=lambda row: row)
        if not ranked:
            return source
        indexes = sorted(index for _, index in ranked[:4])
        excerpt = "\n".join(lines[index][:400] for index in indexes)
        years = set(re.findall(r"(20\d{2})(?:年|级)", title))
        now = datetime.now(timezone.utc).isoformat()
        return {**source, "text": excerpt, "section": "学校官网正文节选",
                "source_type": "official_article", "evidence_origin": "official_article",
                "verified": True, "trust_label": "学校官网正文已读取",
                "published_at": published, "collected_at": collected, "retrieved_at": now,
                "effective_year": int(next(iter(years))) if len(years) == 1 else None,
                "caveat": "学校官网公开正文节选；办理要求、适用对象及更新以原文为准。"}

    def index(self, page):
        cached = self.cache.get(page)
        if cached and monotonic() < cached[0]:
            return cached[1:]
        try:
            if not self.allowed(page):
                raise ValueError("public index restricted")
            links = NoticeLinks()
            links.feed(read_public(self.opener, page))
            items = {}
            for href, title in links.items.items():
                url = urljoin(page, href)
                if official_url(url, self.school) and re.fullmatch(ARTICLE_PATH, urlsplit(url).path):
                    items[url] = title
            row = (items, datetime.now(timezone.utc).isoformat())
            ttl = 1800
        except (OSError, ValueError, LookupError):
            row, ttl = ({}, None), 300
        with self.cache_lock:
            self.cache[page] = (monotonic() + ttl, *row)
        return row

    def search(self, query):
        words = {word for word in ("军训", "宿舍", "资助", "竞赛", "比赛", "图书馆") if word in query}
        for pattern, synonyms in TOPIC_WORDS:
            if re.search(pattern, query):
                words.update(synonyms)
        if re.search(r"学校代码|国标代码|地址|章程|校区|招生办", query):
            words.update(("招生章程", "招生", "校区", "地址"))
        if not words:
            return [], "no_official_results"
        ranked = {}
        available = bool(self.articles)
        years = set(re.findall(r"20\d{2}", query))
        for url, title in self.articles.items():
            score = sum(word in title for word in words)
            if score:
                ranked[url] = (score + 5 * any(year in title for year in years) + 1, title, None)
        pages = [page for page in self.pages if official_url(page, self.school)]
        with ThreadPoolExecutor(max_workers=5) as pool:
            indexes = list(pool.map(self.index, pages))
        for items, fetched_at in indexes:
            available |= bool(fetched_at)
            for url, title in items.items():
                score = sum(word in title for word in words)
                if score:
                    ranked[url] = (score + 5 * any(year in title for year in years), title, fetched_at)
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
        with ThreadPoolExecutor(max_workers=3) as pool:
            sources = list(pool.map(lambda source: self.verify(source, query), sources))
        return sources, "ok" if sources else "no_official_results" if available else "unavailable"
