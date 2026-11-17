"""Configuration is offline by default. A key alone never enables paid requests."""
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEEPSEEK_CONFIG = ROOT / "config" / "deepseek.local.env"
DEEPSEEK_OPTIONS = {"GUIDE_ALLOW_REMOTE_LLM", "GUIDE_LLM_API_KEY", "GUIDE_LLM_MODEL"}


def local_deepseek_config():
    try:
        lines = LOCAL_DEEPSEEK_CONFIG.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return {}
    options = {}
    for line in lines:
        name, separator, value = line.partition("=")
        name = name.strip()
        if separator and name in DEEPSEEK_OPTIONS:
            options[name] = value.strip()
    return options


@dataclass(frozen=True)
class Settings:
    allow_remote: bool = False
    api_key: str = field(default="", repr=False)
    model: str = "deepseek-chat"
    data_dir: Path = ROOT / ".runtime"
    allow_search: bool = False
    search_provider: str = "brave"
    search_key: str = field(default="", repr=False)
    public_host: str = ""

    @classmethod
    def load(cls):
        public_host = os.environ.get("CAMPUSMATE_PUBLIC_HOST", "").strip().lower()
        if public_host and not re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z0-9-]+", public_host):
            raise ValueError("CAMPUSMATE_PUBLIC_HOST 只填写域名，不含协议、端口或路径。")
        # A specific deployment can override the project's DeepSeek settings.
        local = local_deepseek_config()
        return cls(
            allow_remote=os.environ.get("GUIDE_ALLOW_REMOTE_LLM", local.get("GUIDE_ALLOW_REMOTE_LLM", "false")).lower() == "true",
            api_key=os.environ.get("GUIDE_LLM_API_KEY", local.get("GUIDE_LLM_API_KEY", "")).strip(),
            model=os.environ.get("GUIDE_LLM_MODEL", local.get("GUIDE_LLM_MODEL", "deepseek-chat")),
            data_dir=Path(os.environ.get("GUIDE_DATA_DIR", str(ROOT / ".runtime"))),
            allow_search=os.environ.get("CAMPUSMATE_ALLOW_SEARCH", "true").lower() == "true",
            search_provider=os.environ.get("CAMPUSMATE_SEARCH_PROVIDER", "official"),
            search_key=os.environ.get("CAMPUSMATE_SEARCH_API_KEY", "").strip(),
            public_host=public_host,
        )

    def remote_enabled(self):
        if not self.allow_remote or not self.api_key:
            return False
        blocked = json.loads((ROOT / "config/blocked_key_fingerprints.json").read_text(encoding="utf-8"))
        return hashlib.sha256(self.api_key.encode()).hexdigest() not in blocked

    def key_blocked(self):
        if not self.api_key:
            return False
        blocked = json.loads((ROOT / "config/blocked_key_fingerprints.json").read_text(encoding="utf-8"))
        return hashlib.sha256(self.api_key.encode()).hexdigest() in blocked
