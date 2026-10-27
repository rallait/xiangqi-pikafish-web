# -*- coding: utf-8 -*-
"""
本地中国象棋 AI 桥接服务（Pikafish UCI 引擎 -> 浏览器棋盘）
仅监听 127.0.0.1，不访问外网。
"""
import json
import os
import queue
import subprocess
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ENGINE_DIR = r"C:\chess-ai\engine"
ENGINE_EXE = os.path.join(ENGINE_DIR, "Pikafish-Windows-x86-64-universal.exe")
NNUE_FILE = os.path.join(ENGINE_DIR, "pikafish.nnue")

HOST = "127.0.0.1"
PORT = 8731
THREADS = 8
HASH_MB = 512

# 难度 -> 每步思考时间(毫秒)
LEVELS = {1: 80, 2: 200, 3: 600, 4: 2000, 5: 6000}

import random
RNG = random.Random()

# 职业开局库（ElephantEye BOOK.DAT 翻译而来，5 万局面节点）
BOOK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "book_tree.json")
try:
    with open(BOOK_FILE, "r", encoding="utf-8") as _f:
        BOOK_TREE = json.load(_f)
except OSError:
    BOOK_TREE = {}
BOOK_MAX_PLY = 24   # 库只覆盖前 12 回合


def adapt_mt(level, moves):
    """越下越强：中残局随回合数自动加时（开局 1x → 中局 1.3x → 残局/缠斗 1.6x）。"""
    base = LEVELS.get(level, 600)
    n = len(moves)
    f = 1.0 if n < 20 else (1.3 if n < 60 else 1.6)
    return int(base * f)


def book_probe(moves):
    """当前着法序列在职业开局库里的候选 {uci: wvl}，没有返回 None。"""
    if not BOOK_TREE or len(moves) >= BOOK_MAX_PLY:
        return None
    return BOOK_TREE.get(" ".join(moves))


def book_pick(node, rng):
    """从库候选里按权重挑一手：取权重前 3 名，按权重加权随机（保留变化又偏向主流）。"""
    top = sorted(node.items(), key=lambda kv: -kv[1])[:3]
    total = sum(w for _, w in top)
    r = rng.random() * total
    for uci, w in top:
        r -= w
        if r <= 0:
            return uci
    return top[0][0]


def score_to_int(sc):
    """把 'cp 35' / 'mate -2' 转成整数分值（行棋方视角）。"""
    parts = (sc or "").split()
    if len(parts) < 2:
        return 0
    try:
        n = int(parts[1])
    except ValueError:
        return 0
    if parts[0] == "cp":
        return n
    return 30000 if n > 0 else -30000


def cand_list(lines, k=3):
    """从 MultiPV 结果提取前 k 个候选：首着 uci + 评分 + 完整 PV（行棋方视角）。"""
    out = []
    for l in lines or []:
        pv = (l.get("pv") or "").split()
        if pv:
            out.append({"uci": pv[0], "score": l.get("score", ""),
                       "pv": " ".join(pv), "depth": l.get("depth", 0)})
        if len(out) >= k:
            break
    return out


class Engine:
    def __init__(self):
        self.proc = None
        self.q = queue.Queue()
        self.lock = threading.RLock()
        self.name = ""
        self.nnue = ""
        self.start()

    def start(self):
        self.proc = subprocess.Popen(
            [ENGINE_EXE],
            cwd=ENGINE_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        threading.Thread(target=self._reader, daemon=True).start()
        import time
        time.sleep(0.3)   # 给引擎一点启动时间
        self.send("uci")
        for line in self.read_until(lambda l: l == "uciok", 15):
            if line.startswith("id name"):
                self.name = line[8:].strip()
        self.send("setoption name Threads value %d" % THREADS)
        self.send("setoption name Hash value %d" % HASH_MB)
        self.send("setoption name EvalFile value %s" % NNUE_FILE)
        self.send("isready")
        for line in self.read_until(lambda l: l == "readyok", 20):
            if "NNUE evaluation using" in line:
                self.nnue = line.strip()
        self.send("ucinewgame")
        self.send("isready")
        self.read_until(lambda l: l == "readyok", 20)

    def _reader(self):
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\r\n"))

    def send(self, cmd):
        try:
            self.proc.stdin.write(cmd + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            raise RuntimeError("engine pipe broken")

    def read_until(self, pred, timeout):
        lines = []
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self.q.get(timeout=max(0.01, deadline - time.time()))
            except queue.Empty:
                break
            lines.append(line)
            if pred(line):
                break
        return lines

    def drain(self):
        """清空队列里残留的引擎输出，避免污染下一次 _go。"""
        try:
            while True:
                self.q.get_nowait()
        except queue.Empty:
            pass

    def _go(self, moves, movetime, multipv, searchmoves=None):
        import time
        self.drain()
        if multipv > 1:
            self.send("setoption name MultiPV value %d" % multipv)
            self.send("isready")
            self.read_until(lambda l: l == "readyok", 10)
        pos = "position startpos"
        if moves:
            pos += " moves " + " ".join(moves)
        self.send(pos)
        self.send("isready")
        self.read_until(lambda l: l == "readyok", 10)
        go = "go movetime %d" % movetime
        if searchmoves:
            go += " searchmoves " + " ".join(searchmoves)
        self.send(go)
        lines = self.read_until(lambda l: l.startswith("bestmove"), movetime / 1000.0 + 20)
        # 彻底等待 bestmove 被消费，并清空残留输出
        time.sleep(0.05)
        self.drain()
        if multipv > 1:
            self.send("setoption name MultiPV value 1")
            self.send("isready")
            self.read_until(lambda l: l == "readyok", 10)
            time.sleep(0.05)
            self.drain()

        best, score, depth, pv, elo_lines = "", "", 0, "", {}
        for line in lines:
            if line.startswith("bestmove"):
                best = line.split()[1] if len(line.split()) > 1 else "(none)"
                continue
            if not line.startswith("info"):
                continue
            parts = line.split()
            d = 0
            mpv = 1
            sc = ""
            p = ""
            for i, tok in enumerate(parts):
                if tok == "depth" and i + 1 < len(parts):
                    d = int(parts[i + 1])
                elif tok == "multipv" and i + 1 < len(parts):
                    mpv = int(parts[i + 1])
                elif tok == "score" and i + 2 < len(parts):
                    sc = parts[i + 1] + " " + parts[i + 2]
                elif tok == "pv":
                    p = " ".join(parts[i + 1:])
                    break
            if p:
                depth = max(depth, d)
                if d >= elo_lines.get(mpv, {}).get("depth", 0):
                    elo_lines[mpv] = {"depth": d, "score": sc, "pv": p}
                    if mpv == 1:
                        score = sc
                        pv = p
        out = {"best": best, "score": score, "depth": depth, "pv": pv,
               "engine": self.name, "nnue": self.nnue}
        if multipv > 1:
            out["lines"] = [elo_lines[k] for k in sorted(elo_lines)]
        return out

    def play(self, moves, movetime, searchmoves=None, multipv=1):
        # MultiPV 切换由 _go 内部用 setoption+isready 完成并复位，无需重启引擎
        # （重启每次白白浪费 ~1.1s 启动时间；实测连续 MultiPV 调用管道干净）
        with self.lock:
            return self._go(moves, movetime, multipv, searchmoves)

    def analyze(self, moves, movetime):
        with self.lock:
            return self._go(moves, movetime, 3)

    # 套路内最优着法若已明显亏损（AI 视角低于该值），视为套路不适用，交还引擎自由发挥
    THEME_GIVEUP_CP = -60

    def themed(self, moves, allowed, movetime, exclude=None):
        """一次 MultiPV 搜索，从引擎排序结果里挑第一个属于套路集合的着法。
        只 go 一次，避免连续 go 导致的引擎管道污染；score 是 AI 自己视角。
        若套路内最优也已明显亏损，返回空让前端 fallback 到自由发挥。
        exclude: 额外禁止的着法（如长将违规着），即使它在 allow 里也跳过。
        _go 结束时已把 MultiPV 复位为 1，无需重启引擎（实测连续 MultiPV 调用干净）。"""
        with self.lock:
            n = min(max(len(allowed) + 2, 6), 12)
            try:
                r = self._go(moves, movetime, n)
            except RuntimeError:
                self._restart()
                return {"best": "", "score": "", "depth": 0, "tried": 0, "theme": True}
            lines = r.get("lines") or []
            allow_set = set(allowed)
            excl = set(exclude or [])
            picked = None
            for entry in lines:  # lines 按 multipv 排序 = 引擎认为从好到差
                pv = (entry.get("pv") or "").split()
                first = pv[0] if pv else ""
                if first in allow_set and first not in excl:
                    picked = {"best": first, "score": entry.get("score", ""),
                              "depth": entry.get("depth", 0),
                              "tried": len(lines), "theme": True}
                    break
            if picked and score_to_int(picked["score"]) >= self.THEME_GIVEUP_CP:
                return {**picked, "candidates": cand_list(lines)}
            return {"best": "", "score": "", "depth": 0,
                    "tried": len(lines), "theme": True,
                    "candidates": cand_list(lines)}

    def excluding(self, moves, exclude, movetime):
        """不做套路限制，仅从全部着法里挑第一个不在 exclude 中的（用于规避长将）。
        MultiPV 覆盖数随排除表动态加大，保证排除表较大时也有非禁着可选。"""
        with self.lock:
            n = min(max(len(exclude) + 4, 12), 24)
            try:
                r = self._go(moves, movetime, n)
            except RuntimeError:
                self._restart()
                return {"best": "", "score": "", "depth": 0, "tried": 0}
            lines = r.get("lines") or []
            excl = set(exclude or [])
            picked = None
            for entry in lines:
                pv = (entry.get("pv") or "").split()
                first = pv[0] if pv else ""
                if first and first not in excl:
                    picked = {"best": first, "score": entry.get("score", ""),
                              "depth": entry.get("depth", 0), "tried": len(lines)}
                    break
            return ({**picked, "candidates": cand_list(lines)} if picked
                    else {"best": "", "score": "", "depth": 0, "tried": len(lines),
                          "candidates": cand_list(lines)})

    def _restart(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.kill()
        except Exception:
            pass
        import time
        time.sleep(0.2)
        self.proc = None
        self.q = queue.Queue()
        self.start()

    def stop(self):
        try:
            self.send("quit")
        except Exception:
            pass


ENGINE = None


def get_engine():
    global ENGINE
    if ENGINE is None or ENGINE.proc is None or ENGINE.proc.poll() is not None:
        ENGINE = Engine()
    return ENGINE


def engine_call(fn):
    """引擎调用包装：管道断裂时杀掉重启并重试一次（Pikafish 收到非法输入会退出）。"""
    global ENGINE
    try:
        return fn(get_engine())
    except RuntimeError:
        try:
            if ENGINE and ENGINE.proc:
                ENGINE.proc.kill()
        except Exception:
            pass
        ENGINE = None
        return fn(get_engine())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")   # 页面不缓存，改动刷新即生效
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/health":
            e = get_engine()
            self._json({"ok": True, "engine": e.name, "nnue": e.nnue,
                        "threads": THREADS, "hash": HASH_MB,
                        "book": len(BOOK_TREE)})
        else:
            self._json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        try:
            if self.path == "/ai":
                moves = body.get("moves") or []
                node = book_probe(moves)
                if node:
                    top = sorted(node.items(), key=lambda kv: -kv[1])[:3]
                    self._json({"ok": True, "best": book_pick(node, RNG),
                                "score": "", "depth": 0, "pv": "", "book": True,
                                "candidates": [{"uci": u, "wvl": w} for u, w in top]})
                    return
                mt = adapt_mt(int(body.get("level", 3)), moves)
                sm = [s for s in (body.get("searchmoves") or [])
                      if isinstance(s, str) and len(s) == 4][:64]
                res = engine_call(lambda e: e.play(moves, mt, sm or None, 3))
                lines = res.pop("lines", None) or []
                res["candidates"] = cand_list(lines)
                self._json({"ok": True, **res})
            elif self.path == "/ai_theme":
                moves = body.get("moves") or []
                allow = [m for m in (body.get("allow") or []) if isinstance(m, str) and len(m) >= 4][:10]
                exclude = [m for m in (body.get("exclude") or []) if isinstance(m, str) and len(m) >= 4][:12]
                if not allow:
                    self._json({"ok": False, "error": "empty allow list"}, 400)
                    return
                # 职业开局库优先：套路着法与库候选取交集，按库权重选；无交集再走引擎 MultiPV
                node = book_probe(moves)
                if node:
                    inter = [(u, w) for u, w in node.items()
                             if u in allow and u not in exclude]
                    if inter:
                        best = book_pick(dict(inter), RNG)
                        top3 = sorted(inter, key=lambda kv: -kv[1])[:3]
                        self._json({"ok": True, "best": best, "score": "", "depth": 0,
                                    "tried": len(inter), "theme": True, "book": True,
                                    "candidates": [{"uci": u, "wvl": w} for u, w in top3]})
                        return
                mt = adapt_mt(int(body.get("level", 3)), moves)
                self._json({"ok": True, **engine_call(lambda e: e.themed(moves, allow, mt, exclude))})
            elif self.path == "/ai_exclude":
                moves = body.get("moves") or []
                exclude = [m for m in (body.get("exclude") or []) if isinstance(m, str) and len(m) >= 4][:64]
                mt = adapt_mt(int(body.get("level", 3)), moves)
                self._json({"ok": True, **engine_call(lambda e: e.excluding(moves, exclude, mt))})
            elif self.path == "/analyze":
                moves = body.get("moves") or []
                mt = int(body.get("movetime", 2500))
                self._json({"ok": True, **engine_call(lambda e: e.analyze(moves, mt))})
            else:
                self._json({"ok": False, "error": "not found"}, 404)
        except Exception as ex:
            self._json({"ok": False, "error": str(ex)}, 500)


def main():
    get_engine()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    threading.Timer(1.0, lambda: webbrowser.open("http://%s:%d/" % (HOST, PORT))).start()
    print("中国象棋 AI 已启动: http://%s:%d/  (关闭此窗口即退出)" % (HOST, PORT))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
