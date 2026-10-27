# -*- coding: utf-8 -*-
"""一次性构建工具：把 ElephantEye 官方 BOOK.DAT（Zobrist 哈希开局库）翻译成
"moves 前缀 -> 候选着法+权重" 的 JSON 开局树，供 server.py 离线查询。
原理：BFS 从初始局面展开，每个局面计算 Eleeye 的 Zobrist dwLock1，
在 BOOK.DAT 里二分命中后记录该着法并递归；同时尝试左右镜像局面（库查询语义）。
格式与算法均来自 xqbase/eleeye 官方源码（base/rc4prng.h, eleeye/pregen.cpp 等）。
"""
import json, struct, bisect, os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- RC4（base/rc4prng.h, InitZero: key=4字节0） ----------------
class RC4:
    def __init__(self):
        self.s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + self.s[i] + 0) & 255   # key 全 0
            self.s[i], self.s[j] = self.s[j], self.s[i]
        self.x = 0
        self.y = 0
    def next_byte(self):
        self.x = (self.x + 1) & 255
        self.y = (self.y + self.s[self.x]) & 255
        self.s[self.x], self.s[self.y] = self.s[self.y], self.s[self.x]
        return self.s[(self.s[self.x] + self.s[self.y]) & 255]
    def next_long(self):
        b0 = self.next_byte(); b1 = self.next_byte(); b2 = self.next_byte(); b3 = self.next_byte()
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

# ---------------- Zobrist 表（eleeye/pregen.cpp PreGenInit 顺序） ----------------
_rc4 = RC4()
def _z():
    return (_rc4.next_long(), _rc4.next_long(), _rc4.next_long())  # key, lock0, lock1
ZOBR_PLAYER = _z()
ZOBR_TABLE = [[_z() for _ in range(256)] for _ in range(14)]

# ---------------- 坐标映射 ----------------
# Eleeye sq = file + rank*16；file 3..11 对应 a..i；rank 3..12，3=FEN 首行(黑底, UCI 行 '9')
# 我们 board: idx = row*9+col，row 0=红底(UCI '0')，row 9=黑底(UCI '9')
def to_sq(row, col):           # row 0=红底
    return (col + 3) + ((9 - row) + 3) * 16

def from_sq(sq):               # -> (row, col)，row 0=红底
    f = sq & 15
    r = sq >> 4
    return (9 - (r - 3), f - 3)

def mirror_sq(sq):             # 左右镜像：file 3<->11 即 f' = 14 - f，rank 不变
    f = sq & 15
    r = sq >> 4
    return (14 - f) + r * 16

PT_INDEX = {'K': 0, 'A': 1, 'B': 2, 'N': 3, 'R': 4, 'C': 5, 'P': 6}
def pt_index(p):
    return PT_INDEX[p.upper()] + (7 if p.islower() else 0)

def zobrist_lock1(board, red_to_move):
    l1 = 0
    for i, p in enumerate(board):
        if p is None:
            continue
        row, col = divmod(i, 9)
        l1 ^= ZOBR_TABLE[pt_index(p)][to_sq(row, col)][2]
    if not red_to_move:
        l1 ^= ZOBR_PLAYER[2]
    return l1

def mirror_board(board):
    nb = [None] * 90
    for i, p in enumerate(board):
        if p is not None:
            row, col = divmod(i, 9)
            nb[row * 9 + (8 - col)] = p
    return nb

# ---------------- 规则（与前端 index.html 规则一致） ----------------
RED, BLACK = 'r', 'b'
def side_of(p):
    return RED if p.isupper() else BLACK

def in_b(r, c):
    return 0 <= r <= 9 and 0 <= c <= 8

def pseudo_moves(board, i, side):
    """返回目标 idx 列表（不含被将过滤）。"""
    p = board[i]
    if p is None or side_of(p) != side:
        return []
    t = p.upper()
    row, col = divmod(i, 9)
    res = []
    def add(r, c):
        if not in_b(r, c):
            return
        q = board[r * 9 + c]
        if q is None or side_of(q) != side:
            res.append(r * 9 + c)
    if t == 'K':
        r0, r1 = (0, 2) if side == RED else (7, 9)
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr, cc = row + dr, col + dc
            if r0 <= rr <= r1 and 3 <= cc <= 5:
                add(rr, cc)
        # 对脸将
        step = 1 if side == RED else -1
        rr = row + step
        while 0 <= rr <= 9:
            q = board[rr * 9 + col]
            if q is not None:
                if q.upper() == 'K':
                    res.append(rr * 9 + col)
                break
            rr += step
    elif t == 'A':
        r0, r1 = (0, 2) if side == RED else (7, 9)
        for dr, dc in ((1,1),(1,-1),(-1,1),(-1,-1)):
            rr, cc = row + dr, col + dc
            if r0 <= rr <= r1 and 3 <= cc <= 5:
                add(rr, cc)
    elif t == 'B':
        r0, r1 = (0, 4) if side == RED else (5, 9)
        for dr, dc in ((2,2),(2,-2),(-2,2),(-2,-2)):
            rr, cc = row + dr, col + dc
            if r0 <= rr <= r1 and 0 <= cc <= 8 and board[(row + dr//2) * 9 + (col + dc//2)] is None:
                add(rr, cc)
    elif t == 'N':
        for dr, dc, lr, lc in ((2,1,1,0),(2,-1,1,0),(-2,1,-1,0),(-2,-1,-1,0),
                               (1,2,0,1),(1,-2,0,-1),(-1,2,0,1),(-1,-2,0,-1)):
            if in_b(row + dr, col + dc) and in_b(row + lr, col + lc) and \
               board[(row + lr) * 9 + (col + lc)] is None:
                res.append((row + dr) * 9 + (col + dc))
    elif t == 'R':
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr, cc = row + dr, col + dc
            while in_b(rr, cc):
                q = board[rr * 9 + cc]
                if q is None:
                    res.append(rr * 9 + cc)
                else:
                    if side_of(q) != side:
                        res.append(rr * 9 + cc)
                    break
                rr += dr; cc += dc
    elif t == 'C':
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr, cc = row + dr, col + dc
            jumped = False
            while in_b(rr, cc):
                q = board[rr * 9 + cc]
                if not jumped:
                    if q is None:
                        res.append(rr * 9 + cc)
                    else:
                        jumped = True
                else:
                    if q is not None:
                        if side_of(q) != side:
                            res.append(rr * 9 + cc)
                        break
                rr += dr; cc += dc
    elif t == 'P':
        if side == RED:
            add(row + 1, col)
            if row >= 5:
                add(row, col - 1); add(row, col + 1)
        else:
            add(row - 1, col)
            if row <= 4:
                add(row, col - 1); add(row, col + 1)
    return res

def apply_move(board, frm, to):
    nb = list(board)
    nb[to] = nb[frm]
    nb[frm] = None
    return nb

def find_king(board, side):
    target = 'K' if side == RED else 'k'
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1

def king_attacked(board, side):
    k = find_king(board, side)
    if k < 0:
        return True
    opp = BLACK if side == RED else RED
    for i, p in enumerate(board):
        if p is not None and side_of(p) == opp:
            if k in pseudo_moves(board, i, opp):
                return True
    return False

def legal_moves(board, side):
    out = []
    for i, p in enumerate(board):
        if p is not None and side_of(p) == side:
            for to in pseudo_moves(board, i, side):
                if not king_attacked(apply_move(board, i, to), side):
                    out.append((i, to))
    return out

FILES = "abcdefghi"
def uci_of(frm, to):
    fr, fc = divmod(frm, 9)
    tr, tc = divmod(to, 9)
    return "%s%d%s%d" % (FILES[fc], fr, FILES[tc], tr)

# ---------------- BOOK.DAT ----------------
def load_book(path):
    recs = []
    with open(path, 'rb') as f:
        data = f.read()
    for off in range(0, len(data) - 7, 8):
        lock, wmv, wvl = struct.unpack_from('<IHH', data, off)
        recs.append((lock, wmv, wvl))
    recs.sort(key=lambda r: r[0])
    return recs

BOOK = load_book(os.path.join(HERE, 'BOOK.DAT'))
BOOK_KEYS = [r[0] for r in BOOK]
print("BOOK.DAT 记录数:", len(BOOK))

def book_lookup(lock1):
    """返回 [(wmv, wvl)] —— 该 zobrist 的所有候选。"""
    i = bisect.bisect_left(BOOK_KEYS, lock1)
    out = []
    while i < len(BOOK) and BOOK[i][0] == lock1:
        out.append((BOOK[i][1], BOOK[i][2]))
        i += 1
    return out

# ---------------- BFS 翻译 ----------------
START_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"

def parse_start():
    board = [None] * 90
    for ri, row in enumerate(START_FEN.split('/')):
        r = 9 - ri
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                board[r * 9 + c] = ch
                c += 1
    return board

MAX_PLY = 24
book_tree = {}
visited = set()

def bfs(board, moves, red_to_move):
    if len(moves) >= MAX_PLY:
        return
    lock1 = zobrist_lock1(board, red_to_move)
    hits = book_lookup(lock1)
    mirrored = False
    if not hits:
        mb = mirror_board(board)
        lock1m = zobrist_lock1(mb, red_to_move)
        hits = book_lookup(lock1m)
        mirrored = True
    if not hits:
        return
    side = RED if red_to_move else BLACK
    legal = set(uci_of(f, t) for f, t in legal_moves(board, side))
    key = " ".join(moves)
    node = book_tree.setdefault(key, {})
    for wmv, wvl in hits:
        if mirrored:
            src = mirror_sq(wmv & 255)
            dst = mirror_sq((wmv >> 8) & 255)
        else:
            src = wmv & 255
            dst = (wmv >> 8) & 255
        fr, fc = from_sq(src)
        tr, tc = from_sq(dst)
        if not (0 <= fr <= 9 and 0 <= tr <= 9 and 0 <= fc <= 8 and 0 <= tc <= 8):
            continue
        frm, to = fr * 9 + fc, tr * 9 + tc
        uci = uci_of(frm, to)
        if uci not in legal:
            continue
        if wvl > node.get(uci, -1):
            node[uci] = wvl
        # 递归命中分支
        nb = apply_move(board, frm, to)
        state = (tuple(1 if x else 0 for x in nb), red_to_move)  # 粗粒度去重即可
        sig = uci
        bfs(nb, moves + [uci], not red_to_move)

def main():
    bfs(parse_start(), [], True)
    out = os.path.join(HERE, 'book_tree.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(book_tree, f, ensure_ascii=False, separators=(',', ':'))
    print("局面节点数:", len(book_tree))
    print("根节点候选:", book_tree.get("", {}))
    print("已写出:", out, os.path.getsize(out), "bytes")

if __name__ == '__main__':
    main()
