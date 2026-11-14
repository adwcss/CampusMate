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
from backend.official_notices import OfficialNotices
from backend.campusmap import render_map
from tools.migrate_legacy_data import migrate
from backend.knowledge import school_chunks
from backend.store import Store
import hashlib


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

    def test_real_second_school_knowledge_maps_and_storage(self):
        documents = self.request("GET", "/api/sources", school="haust")[1]["documents"]
        charter = next(doc for doc in documents if doc["urls"] == ["https://zjc.haust.edu.cn/info/1133/35053.htm"])
        self.assertEqual(charter["effective_year"], 2026)
        self.assertEqual(charter["trust_label"], "依据官方正文整理")
        schools = self.request("GET", "/api/schools", school="haust")[1]["schools"]
        self.assertEqual(next(row for row in schools if row["school_id"] == "haust")["official_map"],
                         "https://www.haust.edu.cn/xxgk/xydt.htm")
        self.assertIn("暂无可核实地点", self.request("GET", "/campus-map.svg", school="haust")[1])
        self.assertEqual(self.request("GET", "/campus3d/places.json", school="haust")[0], 400)
        session = "real-school-isolation-01"
        self.app.store.save(session, "user", "仅在河职大的历史")
        self.assertEqual(self.request("GET", "/api/history?session=" + session, school="haust")[1]["messages"], [])
        status, body = self.request("POST", "/api/ask", {"session": session, "question": "学校地址和校区在哪里？"}, "haust")
        self.assertEqual(status, 200)
        self.assertIn("开元大道263号", body)
        self.assertNotIn("文昌大道", body)
        self.assertEqual(len(self.request("GET", "/api/history?session=" + session)[1]["messages"]), 1)

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

    def test_user_map_has_image_pair_with_correct_school_boundary(self):
        import struct
        for filename in ("hnvust-map-original.png", "hnvust-map-artwork.png"):
            connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
            connection.request("GET", "/assets/maps/" + filename, headers={"X-CampusMate-School":"hnvust"})
            response = connection.getresponse(); raw = response.read(); connection.close()
            self.assertEqual(response.status, 200); self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", raw[16:24]); self.assertGreater(width, 700); self.assertGreater(height, 700)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), hashlib.sha256((ROOT / "frontend/assets/maps" / filename).read_bytes()).hexdigest())
            self.assertEqual(self.request("GET", "/assets/maps/" + filename, school="template-campus")[0], 404)

    def test_user_map_alignment_replaces_previous_geometry(self):
        places = {row["id"]:row for row in self.request("GET", "/api/places")[1]["places"]}
        self.assertEqual(sum(row.get("map_confirmed", True) for row in places.values()), 30)
        self.assertAlmostEqual(places["tushuguan"]["original_position"]["x"], 549/813*100, places=2)
        self.assertFalse(places["wenti"]["map_confirmed"])
        self.assertIn("未清晰确认", places["wenti"]["note"])
        self.assertEqual(places["wangqiu-1"]["name"], "百草园")

    def test_map_metadata_and_compare_controls(self):
        data = self.request("GET", "/api/map")[1]
        self.assertEqual(data["image"], "/assets/maps/hnvust-map-beautified.svg")
        self.assertEqual(data["original_image"], "/assets/maps/hnvust-map-original.png")
        page = self.request("GET", "/")[1]
        self.assertIn('id="map-image-version"', page); self.assertIn('id="map-dialog-title"', page)
        svg = self.request("GET", data["image"])[1]
        ET.fromstring(svg)
        self.assertIn('id="verified-dorm-labels"', svg)
        self.assertIn('>馨园3</text>', svg); self.assertIn('>馨园2</text>', svg)

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
            remote = {**base, "id":"remote", "text":"2026年9月1日 1500元", "effective_year":2026, "evidence_origin":"official_article", "verified":True}
            def local(query): barrier.wait(); return [base]
            def web(query): barrier.wait(); return [remote], "ok"
            with patch.object(app.retriever, "search", side_effect=local), patch.object(app.answerer.search, "search", side_effect=web):
                prepared = app.answerer.prepare("费用", [], "enhanced")
            self.assertTrue(prepared["web_used"]); self.assertEqual(len(prepared["sources"]), 2)
            self.assertTrue(prepared["conflicts"])

    def test_official_search_reads_body_and_preserves_metadata(self):
        service = SearchService(Settings(allow_search=True, search_provider="official"), self.school)
        article = "https://www.hnvust.cn/info/123/456.htm"
        body = """<time>2026年08月20日</time><nav>菜单假正文</nav>
        <div id="vsb_content"><p>2026级新生报到日期和接待点安排请查阅个人通知书，
        新生需要按学院要求核对身份信息及所需材料。</p><script>不应被提取</script></div>"""
        def read(opener, url):
            if url.endswith("robots.txt"):
                return "User-agent: *\nAllow: /"
            if url == article:
                return body
            return f'<a href="{article}">2026级新生报到安排通知</a>'
        with patch("backend.official_notices.read_public", side_effect=read) as reader:
            sources, status = service.search("2026级新生报到日期")
            service.search("2026级新生报到日期")
        self.assertEqual(status, "ok")
        source = sources[0]
        self.assertTrue(source["verified"])
        self.assertEqual(source["effective_year"], 2026)
        self.assertEqual(source["published_at"], "2026-08-20")
        self.assertNotIn("不应被提取", source["text"])
        self.assertNotIn("菜单", source["text"])
        self.assertEqual(sum(call.args[1] == article for call in reader.call_args_list), 1)

    def test_robots_disallow_leaves_link_and_never_reads_article(self):
        url = "https://www.hnvust.cn/info/123/456.htm"
        notices = OfficialNotices(self.school, None)
        source = {"urls": [url], "source": "新生报到", "verified": False}
        with patch("backend.official_notices.read_public", return_value="User-agent: *\nDisallow: /info/") as reader:
            self.assertEqual(notices.verify(source, "报到"), source)
        self.assertEqual(reader.call_args.args[1], "https://www.hnvust.cn/robots.txt")
        reader.assert_called_once()

    def test_enhanced_model_uses_only_verified_citations_and_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(allow_remote=True, api_key="mock-llm", data_dir=Path(directory))
            app = Application(settings, school_id="haust")
            article = {"id": "article", "text": "河南科技大学开元校区和西苑校区均有教学安排。",
                       "source": "校区介绍", "source_type": "official_article", "effective_year": 2026,
                       "verified": True, "caveat": "核对学校官网"}
            snippet = {**article, "id": "snippet", "text": "不得发送的摘要内容", "verified": False,
                       "source_type": "web_snippet"}
            with patch.object(app.answerer.search, "search", return_value=([article, snippet], "ok")):
                prepared = app.answerer.prepare("学校地址和校区在哪里？", [], "enhanced")
            official_index = len(prepared["sources"]) - 1
            candidate = f"学校设有开元校区和西苑校区。【{official_index}】"
            def response(content):
                return io.BytesIO(json.dumps({"choices": [{"message": {"content": content}}]}).encode())
            with patch("urllib.request.OpenerDirector.open", return_value=response(candidate)) as remote:
                answer, mode = app.answerer.generate("", prepared)
                request = json.loads(remote.call_args.args[0].data)
            self.assertEqual(mode, "remote_llm")
            self.assertIn(candidate, answer)
            self.assertIn("开元大道263号", request["messages"][-1]["content"])
            self.assertNotIn(snippet["text"], request["messages"][-1]["content"])
            with patch("urllib.request.OpenerDirector.open", return_value=response(f"宿舍费88888元。【{official_index}】")):
                answer, mode = app.answerer.generate("", prepared)
            self.assertEqual(mode, "local_evidence")
            self.assertNotIn("88888", answer)

    def test_explicit_cohort_does_not_use_admissions_charter_as_arrival_notice(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Application(Settings(data_dir=Path(directory)))
            prepared = app.answerer.prepare("2026级报到时间是几号？", [], "enhanced")
            answer, mode = app.answerer.generate("", prepared)
        self.assertEqual(mode, "local_evidence")
        self.assertNotIn("2024", answer)
        self.assertIn("官网", answer)

    def test_arrival_cohort_filters_old_material_and_keeps_school_citations(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Application(Settings(data_dir=Path(directory)))
            prepared = app.answerer.prepare("2026级新生报到需要带哪些材料？接站时间在哪？", [])
            answer, _ = app.answerer.generate("", prepared)
            self.assertIsNone(prepared["guided_arrival"])
            self.assertIn("待核实", answer)
            self.assertNotIn("2024", answer)
            self.assertNotIn("9月13日至14日", answer)
            fee = app.answerer.prepare("2026年新生收费标准怎么查？", [])
            fee_answer, _ = app.answerer.generate("", fee)
            self.assertEqual(fee["sources"][0]["urls"], ["https://caiwuchu.hnvust.cn/info/1065/1428.htm"])
            self.assertIn("17000", fee_answer)

            haust = app.for_school("haust").answerer
            prepared = haust.prepare("2026级新生报到和接站怎么安排？", [])
            answer, _ = haust.generate("", prepared)
            self.assertIn("开元、西苑", answer)
            self.assertTrue(any("wbnewsid=344251" in url for source in prepared["sources"] for url in source["urls"]))
            self.assertTrue(all(source["school_id"] == "haust" for source in prepared["sources"]))
            self.assertNotIn("文昌大道", answer)

    def test_official_domain_validation_rejects_userinfo_suffix_and_ports(self):
        for url in ("http://hnvust.cn/a", "https://hnvust.cn.evil/a", "https://evilhnvust.cn/a", "https://hnvust.cn:444/a", "https://user@hnvust.cn/a"):
            self.assertFalse(official_url(url, self.school))
        self.assertTrue(official_url("https://zhaoshengchu.hnvust.cn/a", self.school))


class KnowledgeAndMigrationTests(unittest.TestCase):
    def test_verified_source_checksum_school_boundary_and_pending_skip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); folder = root / "knowledge/example-campus"; folder.mkdir(parents=True)
            raw = "## 入学参考\n报到材料以本人通知为准。".encode()
            (folder / "official.txt").write_bytes(raw)
            school = {"school_id":"example-campus", "official_domains":["school.example"], "legacy_content":False}
            source = {"title":"测试官方资料", "url":"https://school.example/a", "status":"verified_download", "file":"official.txt", "sha256":hashlib.sha256(raw).hexdigest(), "downloaded_at":"2026-11-01T00:00:00Z"}
            manifest = folder / "sources.json"
            manifest.write_text(json.dumps({"school_id":"example-campus", "sources":[source]}), encoding="utf-8")
            with patch("backend.knowledge.ROOT", root):
                chunks = school_chunks(school)
                self.assertEqual(chunks[0]["school_id"], "example-campus"); self.assertTrue(chunks[0]["verified"])
                (folder / "official.txt").write_text("tampered", encoding="utf-8")
                with self.assertRaises(ValueError): school_chunks(school)
                source["status"] = "pending_verification"
                manifest.write_text(json.dumps({"school_id":"example-campus", "sources":[source]}), encoding="utf-8")
                self.assertEqual(school_chunks(school), [])
                manifest.write_text(json.dumps({"school_id":"wrong-campus", "sources":[]}), encoding="utf-8")
                with self.assertRaises(ValueError): school_chunks(school)

    def test_knowledge_path_cannot_escape_school_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); folder = root / "knowledge/example-campus"; folder.mkdir(parents=True)
            source = {"status":"verified_download", "file":"../../private.txt", "url":"https://school.example/a"}
            (folder / "sources.json").write_text(json.dumps({"school_id":"example-campus", "sources":[source]}), encoding="utf-8")
            with patch("backend.knowledge.ROOT", root), self.assertRaises(ValueError):
                school_chunks({"school_id":"example-campus", "official_domains":["school.example"]})

    def test_legacy_migration_keeps_source_session_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); old = Store(root / "old")
            old.save("old-session-00001", "user", "旧资料")
            before = hashlib.sha256(old.path.read_bytes()).hexdigest()
            target = migrate(old.path, root / "new")
            self.assertTrue(target.is_file())
            restored = Store(root / "new/schools/hnvust")
            self.assertEqual(restored.history("old-session-00001")[0]["content"], "旧资料")
            self.assertEqual(hashlib.sha256(old.path.read_bytes()).hexdigest(), before)
            with self.assertRaises(ValueError): migrate(old.path, root / "new")

    def test_configuration_rejects_cross_school_legacy_and_malformed_places(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); folder = root / "config/schools"; folder.mkdir(parents=True)
            school = {**load_schools()["hnvust"], "school_id":"wrong-campus"}
            (folder / "wrong-campus.json").write_text(json.dumps(school), encoding="utf-8")
            with patch("backend.schools.ROOT", root), self.assertRaises(ValueError): load_schools()

    def test_settings_repr_does_not_disclose_keys(self):
        value = repr(Settings(api_key="synthetic-llm-secret", search_key="synthetic-search-secret"))
        self.assertNotIn("synthetic-llm-secret", value); self.assertNotIn("synthetic-search-secret", value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
