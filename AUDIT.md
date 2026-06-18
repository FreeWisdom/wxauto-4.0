# wxauto4 项目审计清单

> 审计日期: 2026-06-17 | 版本: 40.1.1 | 代码规模: ~7,300 行

## P0 · 致命

- [ ] **补充 `pycryptodome` 依赖或删除 `parse.py` 死代码** — `wxauto4/msgs/parse.py:3` 导入 `Crypto` 但 `pyproject.toml` 未声明依赖，干净环境 import 会崩溃。整个 `parse.py` 模块无调用方，若不需要建议删除（会写明文密钥到 `db_keys.json`，有安全隐患）。
- [ ] **修复 `IsRedPixel` 的 `capture` 引用** — `wxauto4/utils/win32.py:405` 调用了未定义的 `capture(hwnd, bbox)`，运行时 NameError。

## P1 · 高优先级

- [ ] **恢复 `@uilock` 或补充注释** — `wxauto4/ui/chatbox.py:168` 的 `send_file` 和 `wxauto4/ui/sessionbox.py:193` 的 `@uilock` 被注释掉，可能导致 UI 竞态条件。
- [ ] **处理 `except Exception: pass` （8 处）** — 至少改用 `wxlog.exception()` 记录异常：
  - `wxauto4/wx.py:229`
  - `wxauto4/ui/base.py:44`
  - `wxauto4/ui/main.py:71`
  - `wxauto4/moment.py:551`
  - `wxauto4/utils/win32.py:246, 276, 369, 396`
  - `wxauto4/utils/tools.py:516`
  - `wxauto4/msgs/mattr.py:127`
- [ ] **收紧 `except Exception` 为具体异常类型** — `moment.py`（22 处）、`win32.py`（12 处）、`tools.py`（8 处）、`wx.py`（5 处）、`navigationbox.py`（4 处）大量使用裸 `except Exception`，静默吞掉所有错误。
- [ ] **建立自动化测试框架** — 当前零自动化测试，CI 只做 import 检查。优先为 `msgs/` 纯逻辑模块写 pytest 单元测试。
- [ ] **库代码用 `wxlog` 替换 `print()`** — `win32.py`（3 处）、`useful.py`（5 处）、`_extras.py`（1 处）、`main.py:152`（1 处）。

## P2 · 中优先级

- [ ] **修复层边界违规** — `wxauto4/msgs/base.py` 直接导入 UI 组件，消息域不应依赖 UI 域。
- [ ] **补充关键模块类型注解** — `moment.py`、`chatbox.py`、`win32.py`、`parse.py`、`component.py` 中 20+ 函数签名缺少返回类型。
- [ ] **配置代码质量工具** — Ruff（linter）+ mypy/pyright（类型检查）+ Black（格式化）。
- [ ] **清理注释化调试代码** — `msgs/msg.py:138-144`、`tools.py:190`、`win32.py:314-357`。
- [ ] **移动懒加载 import 到模块顶层** — `moment.py:261`、`navigationbox.py:84`。

## P3 · 低优先级

- [ ] **`os.system()` 改为 `subprocess.run()`** — `wxauto4/wx.py:423`。
- [ ] **整理 star re-export** — `msgs/__init__.py`、`utils/__init__.py` API 边界不清晰。
- [ ] **`PasteFile` 防忙等待** — `wxauto4/utils/win32.py:381-399` 的 `while True` 循环在异常情况下可能变成 CPU 忙等。

---

## 模块测试覆盖情况

| 模块 | 状态 |
|------|------|
| `wx.py` (WeChat 核心 API) | 有 E2E 脚本，无自动化 |
| `param.py` (WxResponse) | 有 E2E 脚本 |
| `exceptions.py` | 有手动验证 |
| `utils/lock.py` | 有手动验证 |
| `moment.py` (只读路径) | 有 E2E 脚本 |
| `ui/chatbox.py` | ❌ 无覆盖 |
| `ui/sessionbox.py` | ❌ 无覆盖 |
| `ui/navigationbox.py` | ❌ 无覆盖 |
| `ui/component.py` | ❌ 无覆盖 |
| `ui/base.py` | ❌ 无覆盖 |
| `ui/main.py` | ❌ 无覆盖 |
| `msgs/base.py` | ❌ 无覆盖 |
| `msgs/msg.py` | ❌ 无覆盖 |
| `msgs/mtype.py` | ❌ 无覆盖 |
| `msgs/mattr.py` | ❌ 无覆盖 |
| `msgs/friend.py` | ❌ 无覆盖 |
| `msgs/self.py` | ❌ 无覆盖 |
| `msgs/parse.py` | ❌ 无覆盖 + 死代码 |
| `utils/win32.py` | ❌ 无覆盖 |
| `utils/tools.py` | ❌ 无覆盖（OCR/图像部分） |
| `uia/_extras.py` | ❌ 无覆盖 |
| `logger.py` | ❌ 无覆盖 |
| `languages.py` | ❌ 无覆盖 |
