# -*- coding: utf-8 -*-
"""服务端回归测试。

纯函数测试不需要引擎；接口测试会在本机服务（127.0.0.1:8731）没启动时自动跳过。
运行：python -m unittest discover -s tests -v
"""
import os
import random
import sys
import unittest
import urllib.request

GUI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gui-web")
sys.path.insert(0, GUI_DIR)
import server  # noqa: E402

API = "http://127.0.0.1:8731"


def api_post(path, payload):
    req = urllib.request.Request(
        API + path,
        data=server.json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return server.json.loads(r.read().decode("utf-8"))


def api_alive():
    try:
        with urllib.request.urlopen(API + "/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


class PureFunctions(unittest.TestCase):
    def test_adapt_mt_openings(self):
        self.assertEqual(server.adapt_mt(1, []), 80)
        self.assertEqual(server.adapt_mt(2, []), 200)
        self.assertEqual(server.adapt_mt(3, []), 600)
        self.assertEqual(server.adapt_mt(4, []), 2000)
        self.assertEqual(server.adapt_mt(5, []), 6000)

    def test_adapt_mt_midgame_multiplier(self):
        self.assertEqual(server.adapt_mt(4, ["m"] * 30), int(2000 * 1.3))
        self.assertEqual(server.adapt_mt(4, ["m"] * 80), int(2000 * 1.6))

    def test_score_to_int(self):
        self.assertEqual(server.score_to_int("cp 35"), 35)
        self.assertEqual(server.score_to_int("cp -20"), -20)
        self.assertEqual(server.score_to_int("mate 3"), 30000)
        self.assertEqual(server.score_to_int("mate -2"), -30000)
        self.assertEqual(server.score_to_int(""), 0)
        self.assertEqual(server.score_to_int("garbage"), 0)

    def test_book_probe_start_position(self):
        node = server.book_probe([])
        self.assertIsNotNone(node)
        self.assertTrue(node)
        for uci, w in node.items():
            self.assertEqual(len(uci), 4)
            self.assertGreater(w, 0)

    def test_book_probe_out_of_book(self):
        self.assertIsNone(server.book_probe(["m"] * 30))

    def test_book_pick_returns_top3_member(self):
        node = {"h2e2": 100, "c3c4": 50, "b2e2": 20, "a0a1": 1}
        rng = random.Random(7)
        for _ in range(20):
            self.assertIn(server.book_pick(node, rng), {"h2e2", "c3c4", "b2e2"})

    def test_cand_list(self):
        lines = [
            {"score": "cp 30", "depth": 18, "pv": "h2e2 h9g7 h0g2"},
            {"score": "cp 20", "depth": 17, "pv": "c3c4 b7c7"},
            {"score": "cp 10", "depth": 16, "pv": "b2e2 b9c7"},
            {"score": "cp 0", "depth": 15, "pv": "a0a1"},
        ]
        out = server.cand_list(lines, k=3)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[0]["uci"], "h2e2")
        self.assertEqual(out[0]["pv"], "h2e2 h9g7 h0g2")
        self.assertEqual(out[1]["uci"], "c3c4")

    def test_cand_list_empty(self):
        self.assertEqual(server.cand_list([]), [])
        self.assertEqual(server.cand_list([{"score": "cp 1", "pv": ""}]), [])


@unittest.skipUnless(api_alive(), "本机服务未启动，跳过接口测试")
class LiveAPI(unittest.TestCase):
    def test_health(self):
        with urllib.request.urlopen(API + "/health", timeout=5) as r:
            data = server.json.loads(r.read().decode("utf-8"))
        self.assertTrue(data["ok"])
        self.assertIn("Pikafish", data["engine"])
        self.assertEqual(data["book"], len(server.BOOK_TREE))

    def test_progress_shape(self):
        with urllib.request.urlopen(API + "/progress", timeout=5) as r:
            data = server.json.loads(r.read().decode("utf-8"))
        self.assertTrue(data["ok"])
        for key in ("active", "depth", "nodes", "nps", "score", "pv", "elapsed"):
            self.assertIn(key, data)

    def test_stop_when_idle(self):
        data = api_post("/stop", {})
        self.assertTrue(data["ok"])

    def test_ai_with_fen(self):
        # 摆谱局面：红车 + 双方将帅，引擎必须按这个 FEN 搜索而不是 startpos
        fen = "3k5/9/9/9/2R6/9/9/9/9/5K3 w - - 0 1"
        data = api_post("/ai", {"moves": [], "level": 2, "nobook": True, "fen": fen})
        self.assertTrue(data["ok"], data)
        self.assertEqual(len(data["best"]), 4, data)
        self.assertNotEqual(data["best"], "(none)")

    def test_ai_after_fen_has_legal_uci(self):
        # 无红炮的摆谱局面：引擎不能凭空走炮
        fen = "3k5/9/9/9/9/9/9/9/9/4K3R w - - 0 1"
        data = api_post("/ai", {"moves": [], "level": 2, "nobook": True, "fen": fen})
        self.assertTrue(data["ok"], data)
        self.assertEqual(len(data["best"]), 4)
        # 红方只有帅（e 列）和车（i 列）：着法起点只可能是这两列
        self.assertIn(data["best"][0], "ei", data["best"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
