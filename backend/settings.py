"""Configuration is offline by default. A key alone never enables paid requests."""
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    allow_remote: bool = False
    api_key: str = field(default="", repr=False)
    model: str = "deepseek-chat"
    data_dir: Path = ROOT / ".runtime"
    allow_search: bool = False
    search_provider: str = "brave"
    search_key: str = field(default="", repr=False)

    @classmethod
    def load(cls):
        # Deliberately do not load the received backend/.env or DEEPSEEK_API_KEY.
        return cls(
            allow_remote=os.environ.get("GUIDE_ALLOW_REMOTE_LLM", "false").lower() == "true",
            api_key=os.environ.get("GUIDE_LLM_API_KEY", "").strip(),
            model=os.environ.get("GUIDE_LLM_MODEL", "deepseek-chat"),
            data_dir=Path(os.environ.get("GUIDE_DATA_DIR", str(ROOT / ".runtime"))),
            allow_search=os.environ.get("CAMPUSMATE_ALLOW_SEARCH", "true").lower() == "true",
            search_provider=os.environ.get("CAMPUSMATE_SEARCH_PROVIDER", "official"),
            search_key=os.environ.get("CAMPUSMATE_SEARCH_API_KEY", "").strip(),
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
