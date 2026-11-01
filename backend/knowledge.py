"""Manifest-controlled evidence. New files never become trusted by filename alone."""
import hashlib
import json
from .settings import ROOT
from .schools import official_url
from .retriever.splitter import split_all


def school_chunks(school):
    identity = school["school_id"]
    chunks = split_all(ROOT) if school.get("legacy_content") else []
    for chunk in chunks:
        # Preserve inherited assertions as history, not fresh verification.
        chunk.update(school_id=identity, evidence_origin="inherited", verified=False)
        if chunk["source_type"] == "official_verified":
            chunk["source_type"] = "inherited_reference"
            chunk["caveat"] = "交接文件声称曾核对官方入口；本次未逐项复核文件内所有事实。"
    directory = ROOT / "knowledge" / identity
    manifest = directory / "sources.json"
    if not manifest.exists():
        return chunks
    for source in json.loads(manifest.read_text(encoding="utf-8")).get("sources", []):
        if source.get("status") != "verified_download":
            continue
        path = (directory / source["file"]).resolve()
        if not path.is_relative_to(directory.resolve()) or not official_url(source["url"], school):
            raise ValueError("知识来源超出学校范围")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError("知识文件校验失败")
        if path.suffix != ".txt":
            continue  # Raw HTML/PDF preserved for inspection, not naively indexed.
        for index, part in enumerate(raw.decode("utf-8").split("\n\n")):
            if not part.strip():
                continue
            chunks.append({"id": hashlib.sha256((identity + source["file"] + str(index) + part).encode()).hexdigest()[:16],
                           "school_id": identity, "source": source["title"], "section": part.splitlines()[0][:100],
                           "text": part, "source_header": source["title"], "urls": [source["url"]],
                           "source_type": "official_verified", "evidence_origin": "official_download",
                           "effective_year": source.get("effective_year"), "collected_at": source["downloaded_at"],
                           "published_at": source.get("published_at"), "verified": True,
                           "caveat": source.get("caveat", "官方公开文件；适用范围以原文为准。")})
    return chunks
