# WxParam 全局参数

`WxParam` 是一组**类属性**，定义在 [wxauto4/param.py](../../wxauto4/param.py)。直接读写即可调整运行时行为，**不需要实例化**。

```python
from wxauto4 import WxParam

WxParam.LISTEN_INTERVAL = 2
WxParam.ENABLE_SENDER_OCR = False
```

## 字段速查

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `LANGUAGE` | Literal | `'cn'` | UI 语言环境：`'cn'` / `'cn_t'` / `'en'` |
| `ENABLE_FILE_LOGGER` | bool | `True` | 是否启用文件日志 |
| `DEFAULT_SAVE_PATH` | str | `./wxauto4文件下载` | 文件/图片默认保存目录 |
| `MESSAGE_HASH` | bool | `False` | 是否启用消息 md5 哈希 |
| `ENABLE_SENDER_OCR` | bool | `True` | 群聊发送者解析失败时启用 Windows OCR 兜底 |
| `SENDER_OCR_TIMEOUT` | int | `8` | 单次 OCR 超时（秒） |
| `DEFAULT_MESSAGE_XBIAS` | int | `51` | 头像到消息的 X 偏移（用于点击定位） |
| `DEFAULT_MESSAGE_YBIAS` | int | `30` | 头像到消息的 Y 偏移 |
| `FORCE_MESSAGE_XBIAS` | bool | `False` | 是否每次启动都强制重新获取 X 偏移 |
| `LISTEN_INTERVAL` | int | `1` | 监听轮询间隔（秒） |
| `LISTENER_EXCUTOR_WORKERS` | int | `4` | 监听回调线程池大小 |
| `SEARCH_CHAT_TIMEOUT` | int | `2` | 搜索聊天对象超时（秒） |
| `NOTE_LOAD_TIMEOUT` | int | `30` | 微信笔记加载超时（秒） |
| `SEND_FILE_TIMEOUT` | int | `10` | 发送文件超时（秒） |

## 字段详解

### `LANGUAGE`

UI 控件名映射语言环境。

- `'cn'` — 简体中文
- `'cn_t'` — 繁体中文
- `'en'` — 英文

如果微信客户端使用其他语言界面，需要把 `LANGUAGE` 调到对应值，否则控件名匹配会失败。

### `DEFAULT_SAVE_PATH`

`Message` 对象调用 `save()` 保存图片/视频/文件时的默认目录。不存在会自动创建。

### `MESSAGE_HASH`

启用后每条消息会计算 md5 哈希并存入 `msg.hash`，可用于跨轮次去重。代价是每次解析多算一次 md5。

```python
WxParam.MESSAGE_HASH = True
# 之后可以
msg = wx.GetMessageByHash(some_hash)
```

### `ENABLE_SENDER_OCR` / `SENDER_OCR_TIMEOUT`

群聊发送者昵称通过递归子树解析，失败时默认启用 Windows OCR 兜底。OCR 需要额外时间（受 `SENDER_OCR_TIMEOUT` 限制）。

不需要发送者精度时关闭 OCR 可显著提升监听吞吐：

```python
WxParam.ENABLE_SENDER_OCR = False
```

### `DEFAULT_MESSAGE_XBIAS` / `DEFAULT_MESSAGE_YBIAS`

群聊消息的「@」、「点击」等操作需要从头像位置偏移定位到消息气泡。默认值在 4.0.5 下实测可用，若你自定义了微信显示缩放，可能需要调整。

`FORCE_MESSAGE_XBIAS = True` 会强制每次启动重新自动测算偏移。

### `LISTEN_INTERVAL`

监听器轮询新消息的间隔（秒）。

- 默认 `1` 秒，延迟与 CPU 占用平衡
- 回调较重时可放宽到 `2` / `3`
- 极低延迟可降到 `0.5`，CPU 占用明显上升

### `LISTENER_EXCUTOR_WORKERS`

监听回调执行的线程池大小。多个聊天同时活跃或回调耗时较长时，可提升到 `8` 或更高。

### `SEARCH_CHAT_TIMEOUT` / `NOTE_LOAD_TIMEOUT` / `SEND_FILE_TIMEOUT`

各类操作的等待超时，按需调整。如果某些操作因机器性能差经常超时，可适度放宽。

## 修改时机

`WxParam` 是全局配置，建议在**程序最开始、`WeChat()` 实例化之前**修改：

```python
from wxauto4 import WxParam, WeChat

WxParam.LISTEN_INTERVAL = 2
WxParam.ENABLE_SENDER_OCR = False

wx = WeChat()  # 之后创建的实例使用上面的配置
```

实例化后再修改部分字段（如 `LISTEN_INTERVAL`）也可能生效，但不保证——具体字段在源码中读取的时机决定。

## 下一步

- 响应类型：[WxResponse](response.md)
- 监听指南：[消息监听](../guide/listener.md)
