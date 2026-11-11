"""Offline acceptance check using an isolated database and a loopback server."""
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from time import perf_counter
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.main import Application, handler_for
from backend.settings import Settings


def verify():
    started = perf_counter()
    session = "jury-synthetic-session"
    with TemporaryDirectory(prefix=".jury-check-", dir=ROOT) as data:
        settings = Settings(data_dir=Path(data), allow_search=True, search_provider="official")
        app = Application(settings)
        with ThreadingHTTPServer(("127.0.0.1", 0), handler_for(app)) as httpd:
            thread = Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{httpd.server_port}"

            def request(path, payload=None):
                req = Request(base + path, data=None if payload is None else json.dumps(payload).encode(),
                              headers={"Content-Type": "application/json"})
                with urlopen(req, timeout=10) as response:
                    return response.read()

            try:
                health = json.loads(request("/api/health"))
                start_time = round(perf_counter() - started, 3)
                assert health["status"] == "ok" and not health["remote_enabled"]
                assert b'id="view-journey"' in request("/")
                ask_started = perf_counter()
                body = request("/api/ask", {"session": session, "question": "新生报到要带什么材料？", "retrieval_mode": "local"}).decode()
                ask_time = round(perf_counter() - ask_started, 3)
                assert "event: done" in body and "event: sources" in body and "录取通知书" in body
                body = request("/api/ask", {"session": session, "question": "我是今年的新生，从外地来报到。需要带哪些材料？接站安排在哪里查？现在可以先准备什么？"}).decode()
                messages = json.loads(request(f"/api/history?session={session}"))["messages"]
                guided = messages[-1]
                assert "event: done" in body and all(f"【{i}】" in guided["content"] for i in (1, 2, 3))
                assert [source["effective_year"] for source in guided["sources"]] == [None, 2024, 2024]
                assert len(guided["arrival_actions"]) == 3 and "19点" not in guided["content"]
                selection = {"session": session, "answer_id": guided["id"], "selected": ["identity", "travel"]}
                saved = json.loads(request("/api/arrival/from-answer", selection))
                assert saved["added"] == 2 and len(saved["arrival_task_ids"]) == 2
                done = {**saved["tasks"][0], "status": "done"}
                request("/api/tasks", {"session": session, "task": done})
                retried = json.loads(request("/api/arrival/from-answer", selection))
                assert retried["added"] == 0 and retried["skipped"] == 2 and retried["tasks"][0] == done
                assert json.loads(request(f"/api/checklist?session={session}"))["arrival_task_ids"] == saved["arrival_task_ids"]
                try:
                    request("/api/arrival/from-answer", {**selection, "session": "jury-another-session"})
                except HTTPError as error:
                    assert error.code == 400
                else:
                    raise AssertionError("Answer actions escaped their session")
                with patch.object(app.answerer.search.notices.opener, "open", side_effect=OSError("synthetic offline")):
                    body = request("/api/ask", {"session": session, "question": "报到要带什么材料？", "retrieval_mode": "enhanced"}).decode()
                assert '"search_status": "unavailable"' in body and '"web_used": false' in body and "event: done" in body
                request("/api/checklist", {"session": session, "task": "admission", "checked": True})
                assert json.loads(request(f"/api/checklist?session={session}"))["checked"]["admission"] is True
                map_info = json.loads(request("/api/map"))
                assert map_info["places"] and request(map_info["image"])
                assert request("/campus3d/places.json") and request("/assets/pixi-7.4.3.min.js")
                assert json.loads(request("/api/health"))["remote_calls"] == 0
            finally:
                httpd.shutdown()
                thread.join()
        reopened = Application(settings)
        assert reopened.store.checklist(session)["admission"] is True
        assert reopened.store.tasks(session)[0] == done
    return {
        "passed": True, "startup_to_health_seconds": start_time, "first_local_answer_seconds": ask_time,
        "elapsed_seconds": round(perf_counter() - started, 3), "remote_model_calls": 0,
        "checks": ["本地首页及健康检查", "首次问答及来源", "模拟官网不可达与本地回退",
                   "复合报到问答分段引用、选项保存、重复保存及会话隔离",
                   "清单写入及重启后读取", "二维地图和三维数据", "封面运行库"],
        "scope": "自动化 HTTP 检查；联网故障使用模拟响应；不含下载安装 Python 与人工浏览器操作时间。",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
