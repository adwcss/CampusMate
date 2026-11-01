"""Package committed source with actual Git history, hashes and clean-copy checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(output, check_dir, git):
    output, check_dir = output.resolve(), check_dir.resolve()
    stage = output / "CampusMate-2.0"
    if stage.exists() or check_dir.exists():
        raise ValueError("发布目录或验收目录已存在，请指定新目录，避免覆盖。")
    def command(*args):
        return subprocess.check_output([git, *args], cwd=ROOT)
    if command("status", "--porcelain").strip():
        raise ValueError("请先提交所有实际变更后再打包。")
    paths = command("ls-files", "-z").decode("utf-8").split("\0")
    stage.mkdir(parents=True)
    files = []
    for relative in paths:
        if not relative:
            continue
        path = Path(relative)
        if path.name == ".env" or any(part in {".git", ".runtime", "__pycache__", "output"} for part in path.parts):
            raise ValueError("发布清单包含禁止文件")
        original, target = ROOT / path, stage / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        files.append({"file":relative, "sha256":digest(target), "bytes":target.stat().st_size})
    subprocess.run([git, "bundle", "create", str(stage / "history.bundle"), "--all"], cwd=ROOT, check=True, capture_output=True)
    files.append({"file":"history.bundle", "sha256":digest(stage / "history.bundle"), "bytes":(stage / "history.bundle").stat().st_size})
    manifest = {"version":"2.0.0", "created_at":datetime.now(timezone.utc).isoformat(), "commit":command("rev-parse", "HEAD").decode().strip(),
                "note":"Hash list covers all release files except this manifest itself; runtime databases and historical output directory excluded.", "files":files}
    (stage / "release-manifest-campusmate.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    archive = output / "CampusMate-2.0.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(stage.rglob("*")):
            if path.is_file(): bundle.write(path, Path(stage.name) / path.relative_to(stage))
    check_dir.mkdir(parents=True)
    with zipfile.ZipFile(archive) as bundle: bundle.extractall(check_dir)
    clean = check_dir / stage.name
    if any(digest(clean / row["file"]) != row["sha256"] for row in files):
        raise ValueError("解压文件校验失败")
    result = subprocess.run([sys.executable, "-X", "utf8", "-I", "-S", "tools/verify_campusmate.py"], cwd=clean, capture_output=True, encoding="utf-8", errors="replace")
    bundle_check = subprocess.run([git, "bundle", "verify", str(clean / "history.bundle")], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
    report = {"verified_at":datetime.now(timezone.utc).isoformat(), "archive":archive.name, "sha256":digest(archive), "bytes":archive.stat().st_size,
              "commit":manifest["commit"], "file_hashes_verified":len(files), "clean_copy_returncode":result.returncode,
              "clean_copy_output":result.stdout+result.stderr, "history_bundle_verified":bundle_check.returncode == 0}
    (output / "release-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if result.returncode or bundle_check.returncode:
        raise ValueError("独立交付验收失败，请检查release-verification.json")
    print(json.dumps({k:v for k,v in report.items() if k != "clean_copy_output"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-dir", type=Path, required=True)
    parser.add_argument("--git", default="git")
    args = parser.parse_args()
    package(args.output, args.check_dir, args.git)
