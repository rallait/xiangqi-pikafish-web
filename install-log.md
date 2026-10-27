# 安装日志 install-log.md

日期：2026-10-25　系统：Windows 11（Build 26200）　语言：中文

## 本机环境
| 项目 | 值 |
|---|---|
| CPU | Intel Core i7-14650HX（16 核 / 24 线程） |
| 内存 | 16 GB |
| 显卡 | 未使用（Pikafish 为 CPU 引擎，不需要 GPU） |
| C 盘可用 | 约 196 GB |
| 当前 Shell 权限 | **非管理员**（全程无需管理员权限，未触发 UAC） |

## 安装结果
| 组件 | 版本 | 位置 |
|---|---|---|
| Pikafish 引擎 | 2026-09-06（官方 universal x86-64，自动选 AVX2/BMI2 指令集） | `C:\chess-ai\engine\Pikafish-Windows-x86-64-universal.exe` |
| NNUE 权重 | 引擎包内自带 `pikafish.nnue`（50,706,378 字节，与引擎同版本编译） | `C:\chess-ai\engine\pikafish.nnue` |
| 图形界面 | 本机自建离线界面（HTML + Python 本地桥接，无外网依赖） | `C:\chess-ai\gui-web\` |
| 备用界面 | BanksiaGUI 0.58（已下载测试，见下文说明，**未采用**） | `C:\chess-ai\gui\BanksiaGui-0.58-win64\` |

## 下载来源与校验（全部官方源）
| 文件 | 下载 URL | 大小 | SHA256 |
|---|---|---|---|
| Pikafish.2026-09-06.7z | https://github.com/official-pikafish/Pikafish/releases/download/Pikafish-2026-09-06/Pikafish.2026-09-06.7z | 53,603,424 | `41952bbfe2520faceb5902c69e6ab4845cc999841d2b49a95cc1be7867a25e5b` |
| pikafish.nnue（Networks 仓库 master-net，备用，未使用） | https://github.com/official-pikafish/Networks/releases/download/master-net/pikafish.nnue | 50,241,100 | `bf3982711150bf2f8b49e99cd93421320f6ca914cfcf131dad5eb7f2402573ac` |
| BanksiaGui-0.58-win64.zip | https://banksiagui.com/dl/BanksiaGui-0.58-win64.zip | 189,225,833 | `6ccbcc79c31229c66bb03b33c3cf1e9853201f0235a99e1570fba997a0cc95e5` |
| BOOK.DAT（职业开局库，ElephantEye 官方，12,081 条记录） | https://github.com/xqbase/eleeye （仓库内 `BOOK/BOOK.DAT`，raw 直连失败，经 gh-proxy.com 镜像下载） | 96,648 | `F95597F41EE6B6BFAB65895B9C8B490CA1E043FE718C59E5CE6B401980E6563E` |

官方项目主页：https://github.com/official-pikafish/Pikafish 、 https://github.com/official-pikafish/Networks 、 https://banksiagui.com/ 、 https://github.com/xqbase/eleeye
引擎 GitHub Release 页附带的 `Copying.txt` 为 GPLv3 许可证，`NNUE-License.md` 为权重许可，均已随引擎解压在 `C:\chess-ai\engine\` 内。
ElephantEye 源码头注明的许可证为 **LGPL 2.1**（仓库根目录附 `LICENSE`），BOOK.DAT 作为该自由软件的组成部分同许可使用。

## 职业开局库转换说明（2026-10-25）
- `BOOK.DAT` 是 ElephantEye（象眼）引擎的二进制开局库：每条记录 8 字节 `{dwZobristLock u32, wmv u16, wvl u16}`，按 Zobrist 哈希排序，wvl 为该着法在职业对局中的统计权重。
- 转换工具 `C:\chess-ai\gui-web\build_book.py`（本机编写）：按 ElephantEye 源码（`base/rc4prng.h`、`eleeye/position.cpp`、`eleeye/book.cpp`）复现其 RC4-Zobrist 哈希与坐标系，从初始局面 BFS 展开 12 回合，逐局面二分查库（含左右镜像），产出 `book_tree.json`（5,036,782 字节，51,101 个局面节点，键为 UCI 着法前缀，值为 {候选着法: 权重}）。
- 运行时由 `server.py` 加载：AI 行棋前 12 回合优先按库权重挑着（前 3 名加权随机，保留变化），套路模式下与套路着法取交集；出库后自动交还 Pikafish 引擎。

## 关于 BanksiaGUI 的结论
BanksiaGUI 0.58 安装并启动成功（进程运行正常、"设置 → 引擎"可添加引擎），但其 **"文件"菜单只有「国际象棋 / Chess960」两种棋类**，界面无法切换到中国象棋（9×10）棋盘，因此**不能用于本项目目标**。已保留在该目录，但不作为使用入口。

## 执行过的关键操作（均为普通用户权限）
1. 创建目录 `C:\chess-ai\{downloads,engine,gui,gui-web}`
2. 用 `curl` 经本地代理（127.0.0.1:7897，仅用于访问 GitHub，安装完成后不需要）下载上述 3 个文件，并用 `Get-FileHash -Algorithm SHA256` 记录哈希（见上表）
3. `tar -xf`（Windows 自带 bsdtar，支持 7z）解压引擎包；`Expand-Archive` 解压 BanksiaGUI
4. 命令行启动 Pikafish 做 UCI 握手与搜索测试，确认 NNUE 已加载：`NNUE evaluation using pikafish.nnue (64MiB, (62083, 1024, 32, 32, 1))`
5. 编写本地界面 `C:\chess-ai\gui-web\server.py` + `index.html`（监听 127.0.0.1:8731，仅本机可访问）
6. 创建启动脚本 `C:\chess-ai\开始下棋.bat`，桌面快捷方式 `中国象棋 Pikafish.lnk`
7. 断网相关验证与测试记录见 `offline-test.md`

## 权限与安全
- **未使用管理员权限**，无 UAC 弹窗，无系统级修改（未改注册表、未改防火墙、未装服务）。
- **未关闭任何安全软件 / 防火墙 / Defender**。
- **未删除任何个人文件**，未格式化磁盘；仅在 `C:\chess-ai` 和桌面新增了文件与一个快捷方式。
- 未安装破解版、未使用来路不明的整合包；三个下载文件均来自官方 GitHub Release / 官方网站。
- 未安装额外运行库：界面用系统自带 Python 3.15（`C:\Users\33809\AppData\Local\Programs\Python\Python315`）。
