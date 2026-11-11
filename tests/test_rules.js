/* 规则回归测试：从 gui-web/index.html 里抽取纯规则函数，在 Node 中直接跑断言。
   前端是单文件页面，没有模块导出，所以这里按源码标记抽取函数体（不做 DOM 相关调用）。
   运行：node tests/test_rules.js */
"use strict";
const fs = require("fs");
const path = require("path");

const HTML = path.join(__dirname, "..", "gui-web", "index.html");
/* Windows 下 git 可能以 CRLF 签出（autocrlf），统一成 LF 再按源码标记抽取 */
const html = fs.readFileSync(HTML, "utf8").replace(/\r\n/g, "\n");

function block(startMarker, endMarker) {
  const a = html.indexOf(startMarker);
  if (a < 0) throw new Error("找不到起始标记: " + startMarker);
  const b = html.indexOf(endMarker, a);
  if (b < 0) throw new Error("找不到结束标记: " + endMarker);
  return html.slice(a, b);
}

/* 按大括号配平截取一个 function 的完整源码 */
function fn(name) {
  const start = html.indexOf("function " + name + "(");
  if (start < 0) throw new Error("找不到函数: " + name);
  let depth = 0, begun = false;
  for (let i = start; i < html.length; i++) {
    if (html[i] === "{") { depth++; begun = true; }
    else if (html[i] === "}") {
      depth--;
      if (begun && depth === 0) return html.slice(start, i + 1);
    }
  }
  throw new Error("函数大括号不配平: " + name);
}

const consts = block("const FILES = ", "/* ================= 音效（");
const helpers = block("const idx = (c, r)", "\n\n/* ================= 开局套路");
const fns = ["posKey", "parseFEN", "boardToFEN", "pseudoMoves", "findKing",
             "kingAttacked", "applyMove", "legalMovesFrom", "allLegalMoves",
             "fileNum", "numStr", "moveToCN"].map(fn).join("\n");

const API = new Function(
  consts + "\n" + helpers + "\n" + fns +
  "\nreturn {parseFEN, boardToFEN, pseudoMoves, allLegalMoves, legalMovesFrom," +
  " kingAttacked, moveToCN, applyMove, idx, START_FEN, RED, BLK};"
)();

let failed = 0;
function ok(cond, name, extra) {
  if (cond) { console.log("  PASS  " + name); return; }
  failed++;
  console.log("  FAIL  " + name + (extra ? "  →  " + extra : ""));
}

const { RED, BLK, START_FEN, idx } = API;

console.log("FEN 解析 / 生成");
const start = API.parseFEN(START_FEN);
ok(start.filter(Boolean).length === 32, "标准开局 32 个棋子", start.filter(Boolean).length);
ok(API.boardToFEN(start, RED) === START_FEN, "标准开局 FEN 往返一致", API.boardToFEN(start, RED));

const cases = [
  ["空棋盘", "9/9/9/9/9/9/9/9/9/9 w - - 0 1"],
  ["只剩双方将帅", "4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1"],
  ["残局", "3k5/9/9/9/2R6/9/9/9/9/3K5 w - - 0 1"],
  ["满子散落", "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1"],
];
for (const [name, fen] of cases) {
  const b = API.parseFEN(fen);
  const out = API.boardToFEN(b, fen.includes(" b ") ? BLK : RED);
  ok(out === fen, "FEN 往返：" + name, out);
}

console.log("走子合法性");
ok(API.allLegalMoves(start, RED).length === 44, "标准开局红方 44 个合法着法",
   API.allLegalMoves(start, RED).length);
ok(API.allLegalMoves(start, BLK).length === 44, "标准开局黑方 44 个合法着法",
   API.allLegalMoves(start, BLK).length);
const faceKing = API.parseFEN("4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1");
ok(API.kingAttacked(faceKing, RED) === true, "白脸将：红帅被黑将照面");
const kingMoves = API.legalMovesFrom(faceKing, idx(4, 0), RED);
ok(kingMoves.length > 0 && kingMoves.every(m => {
  const c = m.to % 9, r = Math.floor(m.to / 9);
  return c >= 3 && c <= 5 && r <= 2;
}), "帅只能在九宫内活动");
ok(kingMoves.every(m => m.to % 9 !== 4), "帅不能走到与对方将照面的同一列");
ok(API.kingAttacked(faceKing, BLK) === true, "白脸将：黑将同样被照面");
const blockedKing = API.parseFEN("4k4/9/9/9/4P4/9/9/9/9/4K4 w - - 0 1");
ok(API.kingAttacked(blockedKing, RED) === false, "中间有子时白脸将不成立");

console.log("中文记谱");
ok(API.moveToCN(start, idx(7, 2), idx(4, 2)) === "炮二平五", "红炮二平五",
   API.moveToCN(start, idx(7, 2), idx(4, 2)));
ok(API.moveToCN(start, idx(1, 7), idx(4, 7)) === "炮2平5", "黑炮2平5",
   API.moveToCN(start, idx(1, 7), idx(4, 7)));
ok(API.moveToCN(start, idx(4, 3), idx(4, 4)) === "兵五进一", "红兵五进一",
   API.moveToCN(start, idx(4, 3), idx(4, 4)));

console.log("applyMove 不可变");
const before = start.slice();
API.applyMove(start, idx(7, 2), idx(4, 2));
ok(start[idx(7, 2)] === "C" && start[idx(4, 2)] === null, "applyMove 不修改原棋盘");

if (failed) {
  console.log("\n" + failed + " 项失败");
  process.exit(1);
}
console.log("\n规则测试全部通过");
