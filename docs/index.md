# wxauto4 文档

wxauto4 是针对**微信 4.0.5 Windows 客户端**的 Python UI 自动化库，基于 Microsoft UIAutomation 协议封装，提供发消息、发文件、消息监听、朋友圈等自动化接口。

| | |
|---|---|
| **版本** | 40.1.1 |
| **Python** | 3.9 – 3.13 |
| **平台** | Windows 10+ |
| **微信** | 仅支持 4.0.5 |

## 章节导航

### 入门

- [安装](installation.md) — 三种安装方式与微信版本要求
- [快速开始](quickstart.md) — 5 个最小可运行示例

### 指南

- [消息收发](guide/messaging.md) — 文本/@/文件/引用/转发，读取全部消息
- [消息监听](guide/listener.md) — 监听器最佳实践与稳定性优化
- [朋友圈](guide/moments.md) — 读取、点赞、评论完整流程

### API 参考

- [WeChat 类](api/wechat.md) — 主入口的 30+ 方法
- [Message 对象](api/message.md) — 消息字段与动作
- [Moment 朋友圈](api/moment.md) — `Moment` 与 `MomentItem`
- [Session 会话](api/session.md) — 会话列表与单会话操作
- [WxParam 全局参数](api/param.md) — 14 个可调字段
- [WxResponse 响应](api/response.md) — 三态返回值
- [异常](api/exceptions.md) — 4 个异常类

## 快速上手

```python
from wxauto4 import WeChat

wx = WeChat()                           # 创建实例
wx.SendMsg('你好，世界！', '好友昵称')   # 发消息
wx.SendFiles(r'C:\file.txt', '好友昵称')  # 发文件

def on_msg(msg, chat):
    print(chat.who, ':', msg.content)

wx.AddListenChat('好友昵称', on_msg)     # 监听消息
```

更多示例见 [快速开始](quickstart.md)。

## 反馈

- Bug 与功能请求：[Issue 模板](https://github.com/cluic/wxauto4/issues/new/choose)
- 贡献代码：[CONTRIBUTING.md](../CONTRIBUTING.md)
- 更新日志：[CHANGELOG.md](../CHANGELOG.md)
