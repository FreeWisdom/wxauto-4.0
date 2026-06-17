# WeChat 类

`WeChat` 是 wxauto4 的主入口，定义在 [wxauto4/wx.py](../../wxauto4/wx.py)。它继承 `Chat` 与 `Listener`，聚合了导航、会话、聊天框、朋友圈四大子模块。

## 构造

```python
from wxauto4 import WeChat

wx = WeChat()
wx = WeChat(nickname='张三')          # 指定多开账号昵称
wx = WeChat(debug=True)                # 启用调试日志
wx = WeChat(start_listener=True)       # 构造即启动监听线程
```

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `nickname` | str | None | 绑定指定账号（多开场景） |
| `start_listener` | bool | False | 构造即启动监听线程 |
| `debug` | bool | False | 启用调试日志 |
| `**kwargs` | | | 透传给底层窗口初始化 |

## 实例属性

| 属性 | 类型 | 说明 |
|---|---|---|
| `wx.nickname` | str | 当前登录账号昵称 |
| `wx.path` | str | 微信安装路径（`@property`） |
| `wx.dir` | str | 微信版本号目录（`@property`） |
| `wx.NavigationBox` | NavigationBox | 侧边栏导航 API |
| `wx.SessionBox` | SessionBox | 会话列表 API |
| `wx.ChatBox` | ChatBox | 当前聊天框 API |
| `wx.Moment` | Moment | 朋友圈 API |
| `wx.listen` | dict | 监听字典 `{nickname: (chat, callback)}` |

## 发送

### `SendMsg(msg, who=None, clear=True, at=None, exact=False) -> WxResponse`

发送消息。

| 参数 | 类型 | 说明 |
|---|---|---|
| `msg` | str | 消息内容 |
| `who` | str | 发送对象，不指定则发到当前聊天 |
| `clear` | bool | 发送后是否清空编辑框，默认 True |
| `at` | str \| List[str] | @ 对象，支持字符串或列表 |
| `exact` | bool | 是否精确匹配用户名，默认 False |

### `SendFiles(filepath, who=None, exact=False) -> WxResponse`

发送文件。

| 参数 | 类型 | 说明 |
|---|---|---|
| `filepath` | str \| List[str] | 文件路径，单个或列表 |
| `who` | str | 发送对象，不指定则发到当前聊天 |
| `exact` | bool | 是否精确匹配 |

## 读取消息

| 方法 | 签名 | 返回 |
|---|---|---|
| `GetAllMessage()` | 获取当前聊天全部消息 | `List[Message]` |
| `GetNewMessage()` | 自上次调用以来的新消息 | `List[Message]` |
| `GetLastMessage()` | 最后一条消息 | `Optional[Message]` |
| `GetMessageById(msg_id)` | 按 runtime id 查询 | `Optional[Message]` |
| `GetMessageByHash(msg_hash)` | 按 md5 hash 查询（需开启 `MESSAGE_HASH`） | `Optional[Message]` |

返回的消息对象见 [Message](message.md)。

## 会话与聊天切换

### `ChatWith(who, exact=True, force=False, force_wait=0.5)`

切换主聊天框。

| 参数 | 类型 | 说明 |
|---|---|---|
| `who` | str | 目标聊天名 |
| `exact` | bool | 精确匹配（默认 True） |
| `force` | bool | 找不到时是否仍尝试点击首个结果 |
| `force_wait` | float | 切换后等待稳定的秒数 |

### `GetSession() -> List[SessionElement]`

返回当前会话列表，元素类型见 [Session](session.md)。

### `GetSubWindow(nickname) -> Chat`

获取指定聊天的独立子窗口（不存在则新建）。返回的 `Chat` 对象支持与主窗口相同的收发与读取方法。

### `GetAllSubWindow() -> List[Chat]`

返回所有已打开的子窗口实例。

## 监听器

### `AddListenChat(nickname, callback) -> WxResponse`

为指定聊天添加监听。内部会打开独立子窗口。

| 参数 | 类型 | 说明 |
|---|---|---|
| `nickname` | str | 监听对象名 |
| `callback` | Callable[[Message, Chat], None] | 收到新消息时的回调 |

### `RemoveListenChat(nickname, close_window=True) -> WxResponse`

移除监听。

### `StartListening() -> None`

启动监听线程（构造时 `start_listener=True` 会自动调用）。

### `StopListening(remove=True) -> None`

停止监听。`remove=False` 保留已打开的子窗口。

### `KeepRunning()`

维持微信前台运行（用于长时间监听场景）。

## 侧边栏导航

11 个 `SwitchTo*` 方法切换侧边栏视图：

| 方法 | 目标 |
|---|---|
| `SwitchToChat()` | 聊天 |
| `SwitchToContact()` | 通讯录 |
| `SwitchToFavorites()` | 收藏 |
| `SwitchToFiles()` | 聊天文件 |
| `SwitchToMoments()` | 朋友圈 |
| `SwitchToBrowser()` | 搜一搜 |
| `SwitchToVideo()` | 视频号 |
| `SwitchToStories()` | 看一看 |
| `SwitchToMiniProgram()` | 小程序面板 |
| `SwitchToPhone()` | 设备 |
| `SwitchToSettings()` | 设置 |

> **已知问题**：`SwitchToFiles` / `SwitchToStories` 在 4.0.5 部分版本下不生效，详见 [CHANGELOG](../../CHANGELOG.md#unreleased)。

## 生命周期

### `ShutDown()`

强制结束微信进程（`taskkill`）。

## Chat 类（子窗口）

`GetSubWindow` 与 `GetAllSubWindow` 返回的 `Chat` 实例提供以下方法，签名与 `WeChat` 中的同名方法一致，但作用于独立子窗口：

| 方法 | 签名 |
|---|---|
| `Show()` | 显示窗口 |
| `ChatInfo() -> Dict[str, str]` | 获取聊天窗口信息（`chat_name`、`chat_type` 等） |
| `SendMsg(msg, who=None, clear=True, at=None, exact=False)` | 发消息 |
| `SendFiles(filepath, who=None, exact=False)` | 发文件 |
| `GetAllMessage()` | 当前聊天全部消息 |
| `GetNewMessage()` | 新消息 |
| `GetLastMessage()` | 最后一条消息 |
| `GetMessageById(msg_id)` | 按 id 查询 |
| `GetMessageByHash(msg_hash)` | 按 hash 查询 |
| `Close()` | 关闭子窗口 |

实例属性：

| 属性 | 说明 |
|---|---|
| `chat.who` | 聊天对象名 |
| `chat.nickname` | 当前账号昵称 |

## 示例

```python
from wxauto4 import WeChat

wx = WeChat(debug=True)
print('登录账号:', wx.nickname)
print('安装路径:', wx.path)

wx.ChatWith('文件传输助手')
wx.SendMsg('hello')
wx.SendFiles(r'C:\Users\me\test.txt')

last = wx.GetLastMessage()
print('最后一条:', last.content)
```
