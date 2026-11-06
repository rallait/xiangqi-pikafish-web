# 贡献指南

感谢愿意改进这个项目。这是一个**本地离线**运行的中国象棋程序：纯前端单文件 + Python 标准库服务 + Pikafish 引擎，没有构建步骤，也没有 npm / pip 依赖。

## 开发环境

只需要两样东西：

- **Python 3.8+**（后端与引擎桥，仅使用标准库）
- **Node.js**（只在跑走子规则测试时需要）

```bat
git clone https://github.com/rallait/xiangqi-pikafish-web.git
cd xiangqi-pikafish-web
python gui-web/server.py
```

然后浏览器打开 <http://127.0.0.1:8731/>。首次启动会加载引擎与开局树，约需数秒。

如果页面提示「引擎调用失败：Failed to fetch」，先确认 `8731` 端口有监听、服务窗口没有报错，再确认 `engine/` 下的 Pikafish 可执行文件与 `gui-web/` 下的 NNUE 权重文件都在位。

## 代码结构

| 路径 | 说明 |
|---|---|
| `gui-web/index.html` | 前端全部代码：HTML + CSS + JS 单文件，零依赖、零构建 |
| `gui-web/index-en.html` | 英文界面（棋子汉字与中文记谱保留） |
| `gui-web/server.py` | 本地 HTTP 服务 + UCI 引擎桥，仅用 Python 标准库 |
| `gui-web/book_tree.json` | 开局树（约 5 MB，由 `BOOK.DAT` 生成，勿手工编辑） |
| `gui-web/build_book.py` | 开局库构建脚本 |
| `gui-web/sw.js`、`manifest.json` | PWA 离线缓存与安装信息 |
| `engine/` | Pikafish 引擎二进制与 NNUE 权重（**第三方，GPL-3.0**） |
| `tests/` | 回归测试 |

## 提交前请自测

```bat
node tests/test_rules.js
python -m unittest discover -s tests
```

- `test_rules.js`：走子规则与胜负判定，17 项，不需要引擎
- `test_server.py`：服务端纯函数 + 接口联测，13 项；本机服务没启动时接口部分会自动跳过

在 PR 描述里写明这两条命令的结果。

## 代码约定

- **前端不引入任何第三方库或 CDN**：所有 UI、SVG 绘制、动画都是手写的，离线可用是硬性要求
- **后端只用标准库**：不要新增 `requirements.txt`
- **界面文案用中文**（英文版改动请同步 `index-en.html`）
- 改主题配色时改 `THEMES` 对象，新增主题要同时补上 `THEME_NAMES` 与 `applyTheme` 里的 CSS 变量
- 改动棋盘坐标相关逻辑时注意镜像翻转（`flipped`）：X 轴为 `px(c) = M + (flipped ? 8 - c : c) * CELL`
- 摆谱提交的局面必须先过 `validateSetupBoard()`：皮卡鱼收到非法局面（仕出九宫、相过河、兵站错线、将帅照面）会直接退出进程，导致后续所有引擎调用失败

## 提交信息

用中文简述，前缀与仓库现有风格一致：

```
feat: 新增棋谱导出
fix: 修复悔棋后评估走势残留
docs: 补充摆谱快捷键说明
```

一次提交只做一件事；格式化或重命名请单独提交，方便 review。

## 不要提交的内容

以下路径已在 `.gitignore` 中忽略，请不要强行加入：

- `downloads/`、`gui/`：安装包与第三方 TK GUI
- `__pycache__/`、`*.pyc` 等缓存
- `gui-web/err.txt`、`gui-web/out.txt`：本地服务日志
- `install-log.md`、`offline-test.md`：内部工作日志

另外不要提交大体积的引擎二进制、NNUE 权重或开局库重建产物；如果确有必要更新，请在 issue 里先说明原因。

## 提 Issue / PR

- 提 Bug 前先搜一下是否已有人报告
- Bug 请用 Issue 模板填写：运行方式（release 压缩包 / 克隆源码）、Windows 版本、Python 版本、浏览器、复现步骤，以及浏览器控制台（F12）或服务窗口的报错
- PR 请保持范围聚焦，附带截图或录屏（涉及 UI 的改动），并勾选 PR 模板里的自测项

## 许可

- 自研代码（`gui-web/`、脚本、文档）：**MIT**
- `engine/` 下的 Pikafish 引擎与 NNUE 权重、开局库源数据（Eleeye BOOK.DAT）：**GPL-3.0**

提交代码即表示你同意以 MIT 许可发布你的贡献。涉及 `engine/` 的改动请先确认 GPL-3.0 的要求，详见 [LICENSE](LICENSE)。
