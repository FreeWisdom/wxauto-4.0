# 贡献指南

感谢你对 wxauto4 的关注！本文档说明开发环境搭建、提交规范与 Pull Request 流程。

## 开发环境

### 必备条件

- Windows 10 或更高版本（wxauto4 依赖 Windows UIAutomation，无法在 macOS/Linux 上运行真机测试）
- Python 3.9–3.13
- [微信 4.0.5 客户端](https://github.com/SiverKing/wechat4.0-windows-versions/releases)（已登录）
- Poetry ≥ 1.5（推荐）或 pip ≥ 21

### 本地搭建

```bash
git clone https://github.com/cluic/wxauto4.git
cd wxauto4
pip install -e .           # 或 poetry install
```

安装完成后，在已登录微信的机器上跑一遍最小 smoke：

```bash
python -c "from wxauto4 import WeChat; wx = WeChat(); print(wx.nickname)"
```

能打印当前登录账号昵称即环境就绪。

## 项目结构

```
wxauto4/
├── __init__.py        # 对外 API 聚合（__all__）
├── wx.py              # WeChat / Chat / Listener 核心类
├── moment.py          # 朋友圈
├── param.py           # WxParam / WxResponse
├── exceptions.py      # 异常体系
├── ui/                # 微信窗口控件抽象（main/chatbox/sessionbox/navigationbox/component）
├── msgs/              # 消息模型（base/mtype/mattr/friend/self）
└── utils/             # 工具（tools/win32/lock/useful）
```

修改任何 API 时，请同步更新：

- 对应模块的 docstring
- [docs/api/](docs/api/) 下的参考文档
- [README.md](README.md) 中相关章节
- 必要时在 [CHANGELOG.md](CHANGELOG.md) 的 `[Unreleased]` 段添加一行

## 测试

项目提供以下测试脚本（位于仓库根目录）：

| 文件 | 覆盖范围 | 真机要求 |
|---|---|---|
| `test_module1_basic.py` | 初始化、昵称、安装路径、ChatInfo、会话列表 | 需要 |
| `test_module2_messages.py` | 消息发送、文件、读取、按 id/hash 查询 | 需要 |
| `test_module3_listener.py` | 监听器添加/移除/回调触发 | 需要 |
| `test_module4_windows_moments.py` | 子窗口、导航、朋友圈结构 | 需要 |

所有 `test_module*.py` 都需要已登录的微信 4.0.5 真机环境。CI（[`.github/workflows/ci.yml`](.github/workflows/ci.yml)）只跑导入 smoke 与 `test_module1_basic.py` 的 collect-only 验证。

提交 PR 前，请至少在本地手动跑一次与你改动相关的 `test_module*.py`，确保没有回归。

## 提交规范

- 一个 PR 解决一个问题；不要把多个无关变更打包提交
- commit message 推荐使用 [Conventional Commits](https://www.conventionalcommits.org/) 风格：`feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:`
- 涉及行为变更的修复或新功能，在 [CHANGELOG.md](CHANGELOG.md) 的 `[Unreleased]` 段补一行
- **不要**在 PR 中混入调试产物（`debug_*.py` / `probe_*.py` / `probe_output*.txt` 已在 `.gitignore` 中排除）

## Issue 反馈

- Bug 报告请使用 [bug_report.md](.github/ISSUE_TEMPLATE/bug_report.md) 模板，务必附上 wxauto4 版本、微信版本、Python 版本、操作系统、复现代码与 `debug=True` 日志片段
- 功能请求请使用 [feature_request.md](.github/ISSUE_TEMPLATE/feature_request.md) 模板，说明使用场景与期望行为
- 提 Issue 前请先搜索是否已有相同问题

## 代码风格

- 遵循 PEP 8（行宽可放宽到 120）
- 公开方法必须带 docstring（至少一行摘要）
- 新增的对外 API 必须出现在 [wxauto4/__init__.py](wxauto4/__init__.py) 的 `__all__` 中
- 修改 UIA 操作的方法必须考虑并发安全，必要时用 `@uilock` 装饰

## 协议

本项目暂未指定开源协议。提交的代码将按现有项目状态发布。
