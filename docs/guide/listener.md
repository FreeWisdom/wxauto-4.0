# 消息监听

监听器让你能在后台接收新消息并触发回调，是构建自动回复机器人的核心。

## 工作原理

调用 `AddListenChat(name, callback)` 后：

1. wxauto4 为该聊天**打开独立子窗口**（避免主窗口切换导致控件树变化）
2. 后台线程按 `WxParam.LISTEN_INTERVAL`（默认 1 秒）轮询子窗口新消息
3. 新消息通过线程池（`LISTENER_EXCUTOR_WORKERS` 默认 4 线程）调用回调

回调签名是 `callback(msg, chat)`：

- `msg`：[Message](../api/message.md) 实例
- `chat`：[Chat](../api/wechat.md) 子窗口实例，可直接用 `chat.SendMsg()` 回复

## 最小示例

```python
import time
from wxauto4 import WeChat

def on_message(msg, chat):
    print(f'[{chat.who}] {msg.sender}: {msg.content}')
    if msg.content == 'ping':
        chat.SendMsg('pong')

wx = WeChat()
wx.AddListenChat('好友A', on_message)
wx.AddListenChat('好友B', on_message)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    wx.StopListening()
```

## 多聊天同时监听

```python
targets = ['好友A', '好友B', '群1']
for name in targets:
    wx.AddListenChat(name, on_message)
```

每个监听对象独立子窗口，互不影响。

## 调整轮询参数

```python
from wxauto4 import WxParam

WxParam.LISTEN_INTERVAL = 2              # 轮询间隔（秒）
WxParam.LISTENER_EXCUTOR_WORKERS = 8     # 回调线程池大小
```

| 参数 | 推荐 |
|---|---|
| `LISTEN_INTERVAL = 1` | 默认，延迟低 |
| `LISTEN_INTERVAL = 2–3` | 回调较重时 |
| `LISTEN_INTERVAL = 0.5` | 极低延迟，CPU 占用明显上升 |

## 启用消息哈希去重

```python
WxParam.MESSAGE_HASH = True
```

启用后 `msg.hash` 可用于跨轮次去重，避免 UIAutomation 偶发的重复回调。

## 回调内调用 SendMsg

回调内可以直接用 `chat.SendMsg(...)` 回复：

```python
def on_message(msg, chat):
    if '你好' in msg.content:
        chat.SendMsg('你好！有什么可以帮你？')
```

`SendMsg` 内部由 `@uilock` 串行化，多个回调线程并发回复不会冲突。

但**回调内不要做阻塞 IO**——回调运行在线程池里，若单条回调耗时超过 `LISTEN_INTERVAL`，下一轮新消息会堆积在队列里。长任务请丢到自己的队列异步处理。

## 群聊发送者识别

群聊消息的发送者昵称默认通过递归子树解析得到，失败时启用 Windows OCR 兜底：

```python
WxParam.ENABLE_SENDER_OCR = True       # 默认 True
WxParam.SENDER_OCR_TIMEOUT = 8         # 单次 OCR 超时（秒）
```

如果不需要发送者精度，关闭 OCR 可显著提升性能：

```python
WxParam.ENABLE_SENDER_OCR = False
```

## 维持微信前台

监听长时间运行期间，建议保持微信在前台：

```python
wx.KeepRunning()
```

这会持续检测并激活微信窗口。窗口被最小化或关闭时监听可能停止。

## 移除与停止

```python
# 移除单个监听（默认关闭其独立子窗口）
wx.RemoveListenChat('好友A')

# 停止全部监听
wx.StopListening()

# 停止但保留子窗口
wx.StopListening(remove=False)

# 之后可重启
wx.StartListening()
```

## 优雅退出

```python
import signal

def on_exit(signum, frame):
    wx.StopListening()

signal.signal(signal.SIGINT, on_exit)
signal.signal(signal.SIGTERM, on_exit)

wx.KeepRunning()
```

## 常见问题

### 监听突然停止

- 检查微信窗口是否被手动关闭或最小化
- 启用 `debug=True` 查看日志
- 确认未在监听期间用 `ChatWith` 切换主聊天框

### 回调没触发

- 确认调用过 `AddListenChat`（很多人忘记）
- 确认目标对象名与微信显示一致（含表情符号或空格的昵称要小心）
- 子窗口可能被微信合并到主窗口了，手动拖一个出来再试

### CPU 占用过高

- 提升 `LISTEN_INTERVAL` 到 2 或 3 秒
- 关闭 `ENABLE_SENDER_OCR`
- 关闭 `MESSAGE_HASH`（如果未在用）

## 下一步

- 完整 API：[WeChat 类](../api/wechat.md)
- 消息对象：[Message](../api/message.md)
- 全局参数：[WxParam](../api/param.md)
