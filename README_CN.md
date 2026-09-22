# grokbot-cdp

用 Python 驱动 Grok Bot（xAI 的 computer-use agent）背后那台云主机，走 Chrome DevTools Protocol，因为它根本没有 API 可调。

[![Python](https://img.shields.io/badge/Python-3.11%2B-orange?style=flat)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![依赖](https://img.shields.io/badge/%E4%BE%9D%E8%B5%96-2-green?style=flat)](pyproject.toml)
[![语言](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-EN%20%2F%20CN-blue?style=flat)](#语言)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.1.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## ⭐ 先读这里, 设计理念

有三条承诺贯穿全仓，它们比 API 本身更值得先看。

**只写测出来的，绝不推断。** 这个仓库里的每一个数字、每一条错误信息、每一个古怪之处，都来自
对一台真实 Bot 的实际运行。没有一条是从文档上读来的，也没有一条是按「各部件理应如此」推演出来
的。凡是只有一次观测支撑的结论，正文会明说，而不是把它四舍五入成一条规律。

**会撒谎的通道，要让它失败而不是让它含糊。** 屏幕是这个库唯一的通道，而它有一种失效形态：它
继续作答，但不再为真。窗口隐藏时，画布停在最后画过的那一帧，与此同时输入照常送达、会话照常报
告 `Connected`。这种情况下在文档里写一句提醒是撑不住的，因为错的答案和对的答案长得一模一样。
所以这个库选择拒绝：它宁可抛异常，也不交出一帧自己无法担保的画面。同样的取向也贯穿输入模型和
凭据处理。

**凭据要窄。** 远端那台机器是账号下每个 Bot 共享的，连文件和浏览器会话都共享。所以放上去的东
西应当是能完成任务的最小那一个，进去的路上绝不能被画在屏幕上，而且必须能被单独吊销。

## 它是什么（不是什么）

它是一个小的 Python 库：挂到 Grok Bot 桌面端的 Chrome DevTools 端口上，找到承载那台机器 noVNC
会话的 `<webview>`，然后读屏、发送点击与按键、执行 shell 命令、以及在不回显的前提下放置一份凭
据。运行时依赖只有两个，`requests` 和 `websocket-client`。

它**不是** Claude Code 的 skill 或 plugin，也不带 `SKILL.md`：它是一个你 import 的库。它**不
是**浏览器自动化框架，也没有包装任何一个，因为大家最先想到的那个框架根本看不见这个 target。它
**不受** xAI 支持，是对一个从未被当作接口发布的东西做自动化，所以应用内部一变，它随时可能失效
且不会有任何通知。

最要紧的是，它**不是一条能带回 stdout 的通道**。输出是以像素形式回来的。这里没有任何东西读取命
令的退出码或文本，所以凡是结果重要的命令，都得让它把结果写到一个你能用别的途径拿到的地方。

## 安装

Python 3.11 或更新，Windows、macOS、Linux 均可。

```bash
git clone --recursive https://github.com/DaizeDong/grokbot-cdp
cd grokbot-cdp
pip install -e .                       # 或者：pip install -r requirements.txt
git config core.hooksPath .githooks    # 装载闸门；这是本地配置，无法被提交
```

`--recursive` 很要紧。闸门放在 submodule 里，不带这个参数克隆会留下存在但为空的目录，而
`.githooks/pre-commit` 对这种情况是拒绝，不是默默放行。如果已经克隆过了，补跑
`git submodule update --init --recursive`。

应用必须是已登录状态。这个库不处理登录，也不该处理：那恰恰是唯一值得你自己动手的一步。

## 快速开始

```python
from grokbot_cdp import launch, VmSession

launch()
with VmSession() as vm:
    print(vm.status())          # Connected (encrypted) to grok-bot-vm-<id>:2
    vm.run("uname -sr; python3 -V")
    vm.screenshot("screen.jpg")
```

```bash
python examples/probe_host.py          # 这台机器能做什么
python examples/run_command.py "ls -la /workspace"
```

## 细节在哪里

每条规则只有一个家，而且不是这个文件。当你手上的问题正好是某一条回答的那个，再去点它。

| 读这份 | 当你在问 |
| --- | --- |
| [reference/cdp-transport.md](reference/cdp-transport.md) | 本机的进程究竟怎么够到那块屏，以及什么在网络边界的哪一侧 |
| [reference/input-model.md](reference/input-model.md) | 为什么一次点击或一次按键没到，或者到了两次 |
| [reference/screen-capture.md](reference/screen-capture.md) | 你手上这一帧是不是此刻那台机器的样子 |
| [reference/machine-model.md](reference/machine-model.md) | 另一端是什么形态的主机，它消失时什么会留下 |
| [reference/secrets.md](reference/secrets.md) | 怎么把凭据放上去，以及放上去到底暴露了什么 |
| [reference/no-api.md](reference/no-api.md) | 为什么要有这个库而不是调一个接口，以及你接下来会试的那条弯路 |

## API 一览

| 路径 | 是什么 |
| --- | --- |
| `grokbot_cdp/app.py` | 找到已安装的应用；带调试端口启动它；等它就绪。 |
| `grokbot_cdp/cdp.py` | 裸 CDP 客户端与 target 选取。 |
| `grokbot_cdp/vm.py` | 读屏、点击、输入、执行命令、重连。 |
| `grokbot_cdp/secrets.py` | 在不显示内容的前提下把凭据放到机器上。 |
| `examples/` | 一个能力探针和一个单命令执行器。 |
| `tests/` | 离线检查：target 选取、输入形状、shell 引用、屏幕活性、打包、仓库卫生。 |
| `CONTRIBUTING.md` | 怎么连同闸门一起克隆，以及哪些东西必须实测而不能假定。 |

## 局限

没有 stdout，如上：结果要么以像素回来，要么根本回不来。没有支持，xAI 不管，别人也不管。一次只
有一个会话，因为客户端假定只有一个应用、一个机器视图。也没有对明天的保证：它驱动的是一个从未
作为接口发布过的东西。

## 语言

English (`README.md`) · 中文 (`README_CN.md`)

## Roadmap · 贡献 · 许可

见 [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [LICENSE](LICENSE)（MIT）。

与本家仓库规范之间的偏离，以及每一条的理由，记在
[docs/2026-09-22-spec-adaptation.md](docs/2026-09-22-spec-adaptation.md)。
