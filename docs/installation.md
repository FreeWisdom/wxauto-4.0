# 安装

## 前置要求

| 项 | 要求 |
|---|---|
| 操作系统 | Windows 10 或更高 |
| Python | 3.9 – 3.13 |
| 微信客户端 | **仅支持 4.0.5** |

### 微信 4.0.5 下载

下载链接：[wechat4.0-windows-versions/releases](https://github.com/SiverKing/wechat4.0-windows-versions/releases)

> 请勿直接点击 Download URL，找到相应版本后展开 Assets 点击 exe 下载。

## 三种安装方式

### 方式一：pip 安装（推荐）

```bash
pip install wxauto4
```

### 方式二：从 GitHub 安装

```bash
pip install git+https://github.com/cluic/wxauto4.git
```

### 方式三：从源码安装

```bash
git clone https://github.com/cluic/wxauto4.git
cd wxauto4
pip install -e .
```

## 验证

```python
from wxauto4 import WeChat
wx = WeChat()
print(wx.nickname)   # 打印当前登录账号昵称
```

能成功打印昵称即环境就绪。

## 依赖清单

wxauto4 会自动安装以下依赖（来自 `pyproject.toml`）：

| 依赖 | 用途 |
|---|---|
| `tenacity` | 重试装饰器 |
| `pywin32` | Win32 API（窗口、剪贴板等） |
| `pyperclip` | 剪贴板文本 |
| `pillow` | 图像处理 |
| `psutil` | 进程查询 |
| `colorama` | 彩色日志 |
| `comtypes` | UIAutomation COM 接口 |

UIAutomation 核心库（`uiautomation.py`）已内嵌在包内，无需额外安装。

## 卸载

```bash
pip uninstall wxauto4
```

## 常见问题

### 提示「未找到目标 UI 控件」

- 确认微信已启动并登录
- 确认微信版本是 4.0.5（其他版本不兼容）
- 启用 `debug=True` 查看详细日志：

```python
wx = WeChat(debug=True)
```

### 提示「微信无法连接到网络」

- 检查微信是否处于离线/被封禁状态
- 检查代理与防火墙

### Windows Server 上无法运行

wxauto4 依赖桌面会话，不能在无桌面的服务/容器中运行。请使用带桌面环境的 Windows。
