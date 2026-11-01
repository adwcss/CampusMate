"""Multi-school boundaries, real HTTP flows, mocked search protocol; no paid calls."""
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.main import Application, handler_for
from backend.settings import Settings
from backend.schools import load_schools, official_url
from backend.search_service import SearchService, possible_conflicts, search_query, NoRedirect
from backend.arrival import arrival_tasks
from backend.campusmap import render_map


class MultiHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.app = Application(Settings(data_dir=Path(cls.temp.name)))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(cls.app))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.temp.cleanup()

    def request(self, method, path, payload=None, school="hnvust", extra=None):
        headers = {"Content-Type": "application/json", "X-CampusMate-School": school, **(extra or {})}
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        connection.request(method, path, json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None, headers)
        response = connection.getresponse(); body = response.read().decode(); status = response.status
        connection.close()
        return status, json.loads(body) if body.startswith("{") else body

    def test_same_session_school_tasks_and_export_isolated(self):
        session = "same-session-school-0001"
        self.assertEqual(self.request("POST", "/api/tasks", {"session": session, "task": {"title": "仅河职大任务"}})[0], 200)
        self.assertEqual(self.request("GET", "/api/tasks?session=" + session, school="template-campus")[1]["tasks"], [])
        other = self.request("GET", "/api/export?session=" + session, school="template-campus")[1]
        self.assertEqual(other["school_id"], "template-campus"); self.assertEqual(other["messages"], [])
        self.assertNotIn("仅河职大任务", json.dumps(other, ensure_ascii=False))

    def test_same_session_history_feedback_and_delete_isolated(self):
        session = "same-history-school-0001"
        self.app.store.save(session, "user", "河职大私人问题")
        identity = self.app.store.save(session, "assistant", "回答")
        self.assertEqual(self.request("POST", "/api/feedback", {"session": session, "answer": identity, "value": "helpful"}, "template-campus")[0], 400)
        self.request("DELETE", "/api/history", {"session": session}, "template-campus")
        self.assertEqual(len(self.request("GET", "/api/history?session=" + session)[1]["messages"]), 2)

    def test_unknown_traversal_and_conflicting_school_rejected(self):
        for school in ("../hnvust", "missing", "", "HNVUST"):
            self.assertEqual(self.request("GET", "/api/catalog", school=school)[0], 400)
        self.assertEqual(self.request("GET", "/api/catalog?school_id=template-campus")[0], 400)
        self.assertEqual(self.request("POST", "/api/tasks", {"school_id": "template-campus", "session": "school-conflict-0001", "task": {"title": "bad"}})[0], 400)

    def test_cross_school_and_unscoped_backup_rejected(self):
        session = "cross-backup-0000001"
        exported = self.request("GET", "/api/tasks/backup?session=" + session)[1]
        self.assertEqual(exported["school_id"], "hnvust")
        for value in (exported, {k:v for k,v in exported.items() if k != "school_id"}):
            self.assertEqual(self.request("POST", "/api/tasks/import", {"session": session, "backup": value}, "template-campus")[0], 400)
        self.assertEqual(self.request("POST", "/api/tasks/import", {"session": session, "backup": exported})[0], 200)

    def test_knowledge_and_school_specific_modules_do_not_leak(self):
        self.assertEqual(self.request("GET", "/api/sources", school="template-campus")[1]["documents"], [])
        for path in ("/api/dorm", "/api/explore", "/api/club", "/api/preparation?session=template-session-001", "/school-map.jpg"):
            self.assertEqual(self.request("GET", path, school="template-campus")[0], 400)
        for field in ("places", "tasks", "route"):
            self.assertEqual(self.request("GET", "/api/catalog", school="template-campus")[1][field], [])

    def test_arrival_preview_generation_idempotency_progress_and_school_isolation(self):
        session = "arrival-multi-000001"
        payload = {"session": session, "profile": {"arrival_date": "2026-11-03", "live_on_campus": True, "need_aid": True}}
        status, preview = self.request("POST", "/api/arrival/preview", payload)
        self.assertEqual(status, 200); self.assertEqual(len(preview["tasks"]), 4)
        self.assertEqual(self.request("GET", "/api/tasks?session=" + session)[1]["tasks"], [])
        first = self.request("POST", "/api/arrival/generate", payload)[1]
        task = {**first["tasks"][0], "status": "done", "due": "2026-11-05"}
        self.assertEqual(self.request("POST", "/api/tasks", {"session": session, "task": task})[0], 200)
        again = self.request("POST", "/api/arrival/generate", payload)[1]
        self.assertEqual(again["added"], 0); self.assertEqual(again["tasks"][0]["status"], "done")
        self.assertEqual(again["tasks"][0]["due"], "2026-11-05")
        self.assertEqual(self.request("POST", "/api/arrival/generate", payload, "template-campus")[1]["added"], 4)

    def test_invalid_arrival_inputs_and_atomic_capacity(self):
        for profile in (None, {"need_aid": "yes"}, {"arrival_date": "2026-02-30"}, {"school_id": "hnvust"}):
            self.assertEqual(self.request("POST", "/api/arrival/generate", {"session": "arrival-bad-000001", "profile": profile})[0], 400)
        session = "arrival-capacity-001"
        self.app.store.merge_tasks(session, [arrival_tasks({}, self.app.school)[0] | {"title": str(i)} for i in range(99)])
        self.assertEqual(self.request("POST", "/api/arrival/generate", {"session": session, "profile": {}})[0], 400)
        self.assertEqual(len(self.app.store.tasks(session)), 99)

    def test_svg_metadata_and_template_has_no_inherited_names(self):
        status, svg = self.request("GET", "/campus-map.svg")
        self.assertEqual(status, 200); ET.fromstring(svg); self.assertIn("非官方地图", svg)
        svg = self.request("GET", "/campus-map.svg", school="template-campus")[1]
        self.assertNotIn("沁园", svg); self.assertIn("暂无可核实地点", svg)

    def test_enhanced_without_key_sse_fallback_and_default_no_calls(self):
        status, text = self.request("POST", "/api/ask", {"session": "search-fallback-001", "question": "报到时间？", "retrieval_mode": "enhanced"})
        self.assertEqual(status, 200); self.assertIn('"search_status": "not_configured"', text)
        self.assertIn('"web_used": false', text); self.assertEqual(self.app.answerer.search.calls, 0)
        self.assertEqual(self.app.answerer.remote_calls, 0)

    def test_template_answer_has_no_hnvust_phone_or_documents(self):
        status, text = self.request("POST", "/api/ask", {"session": "template-answer-001", "question": "学费多少？"}, "template-campus")
        self.assertEqual(status, 200); self.assertNotIn("0394", text); self.assertIn('"sources": []', text)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.school = load_schools()["hnvust"]
        self.service = SearchService(Settings(allow_search=True, search_key="synthetic-search-secret"), self.school)

    def mock_open(self, results):
        return patch("urllib.request.OpenerDirector.open", return_value=io.BytesIO(json.dumps({"web":{"results":results}}).encode()))

    def test_provider_protocol_and_official_host_boundary(self):
        results = [{"title":"官方", "url":"https://www.hnvust.cn/info/example.htm", "description":"<b>新生</b>通知 2026年9月1日 1500元"},
                   {"title":"冒充", "url":"https://hnvust.cn.attacker.example/a", "description":"wrong"},
                   {"title":"其他高校", "url":"https://haust.edu.cn/a", "description":"wrong"},
                   {"title":"凭据", "url":"https://name:secret@hnvust.cn/a", "description":"wrong"}]
        with self.mock_open(results) as remote:
            sources, status = self.service.search("身份证私密12345 学费多少")
        self.assertEqual(status, "ok"); self.assertEqual(len(sources), 1)
        source = sources[0]; self.assertFalse(source["verified"]); self.assertIsNone(source["published_at"])
        self.assertNotIn("<b>", source["text"]); self.assertEqual(source["school_id"], "hnvust")
        request = remote.call_args.args[0]
        self.assertTrue(request.full_url.startswith("https://api.search.brave.com/res/v1/web/search?"))
        self.assertNotIn("12345", request.full_url); self.assertNotIn("synthetic-search-secret", request.full_url)
        self.assertEqual(request.get_header("X-subscription-token"), "synthetic-search-secret")
        self.assertTrue(source["retrieved_at"])

    def test_search_separate_from_llm_and_fail_closed(self):
        service = SearchService(Settings(allow_remote=True, api_key="synthetic-llm-key"), self.school)
        with patch("urllib.request.OpenerDirector.open") as remote:
            self.assertEqual(service.search("报到")[1], "not_configured"); remote.assert_not_called()
        with patch("urllib.request.OpenerDirector.open", side_effect=RuntimeError("secret upstream error")):
            self.assertEqual(self.service.search("报到"), ([], "unavailable"))

    def test_malformed_payload_or_no_official_results(self):
        with self.mock_open([{"url":"https://www.hnvust.cn/a", "title":[], "description":"wrong"}]):
            self.assertEqual(self.service.search("入学")[1], "no_official_results")
        with patch("urllib.request.OpenerDirector.open", return_value=io.BytesIO(b"x" * 262145)):
            self.assertEqual(self.service.search("入学")[1], "unavailable")

    def test_redirect_never_forwards_search_key(self):
        with self.assertRaises(ValueError): NoRedirect().redirect_request(None, None, 302, "", {}, "https://attacker.example")

    def test_parallel_local_and_search_and_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Application(Settings(data_dir=Path(directory)))
            barrier = threading.Barrier(2, timeout=3)
            base = {"id":"local", "text":"2024年9月1日 1000元", "caveat":"历史资料", "verified":False, "source":"历史", "effective_year":2024}
            remote = {**base, "id":"remote", "text":"2026年9月1日 1500元", "effective_year":None, "evidence_origin":"search_api"}
            def local(query): barrier.wait(); return [base]
            def web(query): barrier.wait(); return [remote], "ok"
            with patch.object(app.retriever, "search", side_effect=local), patch.object(app.answerer.search, "search", side_effect=web):
                prepared = app.answerer.prepare("费用", [], "enhanced")
            self.assertTrue(prepared["web_used"]); self.assertEqual(len(prepared["sources"]), 2)
            self.assertTrue(prepared["conflicts"])

    def test_official_domain_validation_rejects_userinfo_suffix_and_ports(self):
        for url in ("http://hnvust.cn/a", "https://hnvust.cn.evil/a", "https://evilhnvust.cn/a", "https://hnvust.cn:444/a", "https://user@hnvust.cn/a"):
            self.assertFalse(official_url(url, self.school))
        self.assertTrue(official_url("https://zhaoshengchu.hnvust.cn/a", self.school))


if __name__ == "__main__":
    unittest.main(verbosity=2)
