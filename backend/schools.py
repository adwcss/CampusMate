"""Validated school registry. No request can select arbitrary filesystem paths."""
import json
import re
from .settings import ROOT

DEFAULT_SCHOOL = "hnvust"


def load_schools():
    result = {}
    for path in sorted((ROOT / "config/schools").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        identity = value.get("school_id")
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{1,39}", identity) or identity != path.stem:
            raise ValueError("学校配置标识无效")
        if identity in result or not isinstance(value.get("name"), str):
            raise ValueError("学校配置重复或缺少名称")
        domains = value.get("official_domains", [])
        if not isinstance(domains, list) or any(not isinstance(d, str) or not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)+", d) for d in domains):
            raise ValueError("官方域名配置无效")
        if value.get("legacy_content") and identity != DEFAULT_SCHOOL:
            raise ValueError("交接学校资料仅可用于hnvust")
        if type(value.get("legacy_content", False)) is not bool:
            raise ValueError("legacy_content必须为布尔值")
        places = value.get("places", [])
        if not isinstance(places, list) or len(places) > 100:
            raise ValueError("学校地点列表无效")
        seen = set()
        for place in places:
            if not isinstance(place, dict) or any(not isinstance(place.get(k), str) or not place[k].strip() for k in ("id", "name", "category", "question", "note")):
                raise ValueError("地点缺少标识、名称、分类、问题或来源说明")
            if place["id"] in seen or any(type(place.get(k)) not in (int, float) or not 0 <= place[k] <= 100 for k in ("x", "y")):
                raise ValueError("地点标识重复或坐标超出范围")
            seen.add(place["id"])
        for field in ("short_name", "status", "map_notice", "official_home"):
            if not isinstance(value.get(field), str):
                raise ValueError("学校配置缺少显示字段")
        if value["official_home"] and not official_url(value["official_home"], value):
            raise ValueError("学校官网必须位于配置的HTTPS官方域名")
        result[identity] = value
    if DEFAULT_SCHOOL not in result:
        raise ValueError("缺少默认学校配置")
    return result


def select_school(registry, identity):
    if not isinstance(identity, str) or identity not in registry:
        raise ValueError("学校不存在，请选择已配置的学校。")
    return registry[identity]


def official_url(url, school):
    from urllib.parse import urlsplit
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        return (parsed.scheme == "https" and not parsed.username and not parsed.password
                and parsed.port in (None, 443) and any(host == d or host.endswith("." + d) for d in school["official_domains"]))
    except (ValueError, TypeError):
        return False
