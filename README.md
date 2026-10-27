# 中国象棋 AI（Pikafish + Web GUI）

本地离线运行的中国象棋对弈程序：Pikafish 引擎（NNUE）+ 自研 Web 界面 + 5.1 万节点职业开局库。

## 功能

- **强引擎**：Pikafish 2026-09-06，8 线程 / 512MB 哈希，五档难度（默认高级 2s/步，随对局深入自动加时，越下越强）
- **职业开局库**：由 Eleeye BOOK.DAT 翻译的 51,101 节点开局树，按职业比赛统计权重选着，零延迟
- **AI 候选着法**：每步给出前 3 候选（中文记谱 + 我方视角分差 + 续着），**点击候选即可让 AI 改走该手**
- **局势评估卡**：白话结论（我方略优 / 对方大优…）+ 红方视角形势条 + 中文主变
- **规则完备**：长将/长捉违规判定、三次重复局面、六十回合和棋
- **美术**：4 套主题随时切换（赛博霓虹/经典木纹/青瓷/水墨），落子滑行动画、吃子碎裂特效、将军/绝杀全屏横幅、走子路径箭头、战损陈列区、落子音效
- **套路模式**：AI 按指定开局套路（中炮、飞相、仙人指路等）见招拆招

## 快速开始（Windows）

```bat
开始下棋.bat
```

或手动：

```bat
cd gui-web
python server.py
```

然后浏览器打开 <http://127.0.0.1:8731>。需要 Python 3.8+，无需安装任何第三方包。

## 目录结构

```
engine/          Pikafish 引擎（Windows/Linux/macOS/Android 二进制 + NNUE 权重 + 官方许可）
gui-web/         Web 界面与服务端
  index.html     单文件前端（棋盘 SVG、规则引擎、动画特效、主题系统）
  server.py      HTTP 服务 + UCI 引擎桥接（开局库、MultiPV 候选、长将排除）
  book_tree.json 职业开局库（51,101 节点，由 BOOK.DAT 生成）
  build_book.py  BOOK.DAT → book_tree.json 转换脚本
开始下棋.bat     一键启动
usage.md         使用说明
install-log.md   安装与来源校验记录（URL / SHA256）
offline-test.md  离线验证记录
```

## 许可

- Pikafish 引擎与 NNUE 权重：GPL-3.0（见 `engine/Copying.txt`、`engine/NNUE-License.md`）
- 开局库源数据 BOOK.DAT 来自 Eleeye（GPL）
- 本仓库自研代码（gui-web、脚本、文档）：MIT
