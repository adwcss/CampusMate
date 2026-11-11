"""Export a reviewable working-tree snapshot, separate from Git release history."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.retriever.splitter import DOC_FILES

RUNTIME_DIRS = ("backend", "frontend", "config", "knowledge")
SUFFIXES = {".py", ".html", ".js", ".css", ".json", ".txt", ".md", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".woff2"}
TEXT_SUFFIXES = {".py", ".html", ".js", ".css", ".json", ".txt", ".md", ".svg", ".example", ".cmd"}
ROOT_FILES = ["run.py", "README.md", ".env.example", "启动新生指南.cmd", "校园地图.png", "学校地图.jpg",
              "四人间卫生间.jpg", "四人间洗手台.jpg", "六人间浴室洗手台.jpg", "四人间六人间洗衣房.jpg",
              "六人间床位.jpg", "六人宿舍俯视图.jpg", "四人间床位.jpg", "四人宿舍俯视图.jpg"]
SUPPORT = ["tools/jury_check.py", "tools/migrate_legacy_data.py", "docs/评委十分钟复现.md", "docs/当前版技术说明.md",
           "docs/参赛证据索引.md", "docs/迎新资料覆盖表.md", "docs/地图美化与接入.md"]
SECRET = re.compile(rb"(?i)\bsk-[0-9a-f]{32}\b|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")


def package():
    output = ROOT / "output/jury"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "CampusMate-评审运行快照.zip"
    names = {Path(name) for name in ROOT_FILES + DOC_FILES + SUPPORT}
    for folder in RUNTIME_DIRS:
        for path in (ROOT / folder).rglob("*"):
            relative = path.relative_to(ROOT)
            if path.is_file() and not path.is_symlink() and not any(part.startswith(".") for part in relative.parts):
                if path.suffix.lower() in SUFFIXES or path.name.startswith("LICENSE"):
                    names.add(relative)
    manifest = {"kind": "working_tree_snapshot", "commit": None,
                "note": "此快照用于功能验收。文件哈希用于校验，提交链另由真实仓库提供。", "files": {}}
    with TemporaryDirectory(prefix=".jury-package-", dir=output) as temp:
        tmp = Path(temp)
        archive = tmp / "snapshot.zip"
        with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
            for name in sorted(names):
                data = (ROOT / name).read_bytes()
                if name.suffix.lower() in TEXT_SUFFIXES and SECRET.search(data):
                    raise ValueError(f"需先检查凭据：{name}")
                manifest["files"][name.as_posix()] = hashlib.sha256(data).hexdigest()
                bundle.writestr(f"CampusMate/{name.as_posix()}", data)
            bundle.writestr("CampusMate/SNAPSHOT.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        with ZipFile(archive) as bundle:
            bundle.extractall(tmp / "clean")
        clean = tmp / "clean/CampusMate"
        assert all(hashlib.sha256((clean / name).read_bytes()).hexdigest() == digest
                   for name, digest in manifest["files"].items())
        result = subprocess.check_output([sys.executable, "-X", "utf8", "-S", "tools/jury_check.py"], cwd=clean)
        report = json.loads(result.decode("utf8"))
        report.update({"archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                       "files_verified": len(manifest["files"]), "clean_extract_verified": True})
        archive.replace(target)
        (output / "独立解压验收.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    package()
