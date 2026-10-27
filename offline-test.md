# 离线测试记录 offline-test.md

测试时间：2026-10-25　测试人：本机自动化 Agent
被测对象：`C:\chess-ai\engine\Pikafish-Windows-x86-64-universal.exe` + `C:\chess-ai\gui-web\`（本地界面）

---

## 测试 1：引擎原生搜索（8 线程 / 512MB 哈希）

命令（工作目录 `C:\chess-ai\engine`）：
```
uci
setoption name Threads value 8
setoption name Hash value 512
isready
position startpos moves h2e2 h9g7
go depth 20
```

结果（节选真实输出）：
```
info string NNUE evaluation using pikafish.nnue (64MiB, (62083, 1024, 32, 32, 1))
info depth 19 seldepth 39 multipv 1 score cp 22 nodes 4727342 nps 5872474 hashfull 41 time 805 pv g3g4 h7i7 ...
info depth 20 seldepth 39 multipv 1 score cp 19 nodes 6086862 nps 5835917 hashfull 52 time 1043 pv h0g2 i9h9 ...
bestmove h0g2 ponder i9h9
```
- NNUE 权重加载成功（64MiB 网络，结构 62083→1024→32→32→1）
- 8 线程约 **587 万节点/秒**，1.04 秒算到 **深度 20**
- 落子 `h0g2`（马二进三），评估 +0.19

## 测试 2：界面人机对弈（浏览器实测）

操作：打开 `http://127.0.0.1:8731/` → 「开始新对局」（默认我执红）→ 点红炮 h2 再点 e2（炮八平五）→ 等 AI 应招。

结果：
- 棋盘正确显示 9 列 × 10 行，中文棋子（帅仕相马车炮兵 / 将士象马车炮卒）
- 着法记录：`1. 炮八平五 … 马2进3`（红方我一步 + AI 黑方一步，均合法）
- 引擎评估区显示 `-0.19　深度 21`
- 点「分析局面」返回 3 条主变（MultiPV=3），用时 2.5 秒

结论：人机对弈、AI 应招、局面分析三个核心功能均正常。

## 测试 3：网络连接审计（关键证据）

对弈与分析进行中，检查 `python.exe`（界面服务）与 `Pikafish-Windows-x86-64-universal.exe`（引擎）进程的所有 TCP 连接：

```
OwningProcess  State   LocalAddress  LocalPort  RemoteAddress  RemotePort
33400          Listen  127.0.0.1     8731       0.0.0.0        0
（引擎进程：无任何 socket）
```

- 界面服务只监听 **回环地址 127.0.0.1**，外部机器无法访问
- 引擎进程 **完全没有网络句柄**
- 两个进程 **没有任何外部（非 127.0.0.1）连接**

即：从进程层面已证明该组合的运行路径完全不依赖网络。

## 测试 4：真·拔网复测（需管理员，一步即可）

当前会话无管理员权限，无法用 `Disable-NetAdapter` 真正关闭无线网卡（会触发 UAC）。若要做物理级断网复测，用**管理员** PowerShell 执行：

```powershell
Disable-NetAdapter -Name "WLAN" -Confirm:$false
# 然后双击桌面「中国象棋 Pikafish」下棋 3~5 步、点「分析局面」
Enable-NetAdapter -Name "WLAN" -Confirm:$false
```

预期：与联网时行为完全一致（界面、AI 应招、分析均正常），因为引擎与界面不访问网络。

## 结论

- 引擎 + 权重 + 界面全部本地文件，运行路径无网络依赖（测试 3 已从 socket 层证实）
- 离线可用：是
- 人工确认项：真·断网复测需管理员权限关闭网卡（测试 4 给出命令）
