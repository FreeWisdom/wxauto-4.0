# wxauto4 - WeChat自动化工具

<p align="center">
  <img src="https://img.shields.io/badge/Version-40.1.1-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows10+-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/WeChat-4.0.5-green.svg" alt="WeChat">
</p>

wxauto4 是一个适用于微信4.0客户端的 Python 自动化库，提供微信自动化操作接口，包括消息发送、文件传输等功能。

## 重要声明

<font color='red'>**目前仅适用于微信 4.0.5 版本客户端**</font>

下载链接：[点击跳转](https://github.com/SiverKing/wechat4.0-windows-versions/releases)

> [!Warning]
> 请勿直接点击Download URL，找到相应版本，展开Assets点击exe下载


## 安装方式

### 使用 pip 安装（推荐）

```bash
pip install wxauto4
```
或者通过Github

```bash
pip install git+https://github.com/cluic/wxauto4.git
```

### 从源码安装

```bash
git clone https://github.com/cluic/wxauto4.git
cd wxauto4
pip install -e .
```

## 🚀 快速开始

```python
from wxauto4 import WeChat

# 创建微信实例
wx = WeChat()

# 发送消息
wx.SendMsg('你好，世界！', '好友昵称')

# 发送文件
wx.SendFiles(r'C:\path\to\file.txt', '好友昵称')

# 获取消息
messages = wx.GetAllMessage()
for msg in messages:
    print(msg.content)
```


## 文档

### 1. 获取微信实例

```python
from wxauto4 import WeChat

# 创建微信主窗口实例
wx = WeChat()
```

### 2. 发送消息 - SendMsg

```python
# 基础消息发送
wx.SendMsg('Hello!', '目标用户')
```

**参数说明：**
- `msg` (str): 消息内容
- `who` (str, optional): 发送对象，不指定则发送给当前聊天对象
- `clear` (bool, optional): 发送后是否清空编辑框，默认 True
- `at` (Union[str, List[str]], optional): @对象，支持字符串或列表
- `exact` (bool, optional): 是否精确匹配用户名，默认 False

### 3. 发送文件 - SendFiles

```python
# 发送单个文件
wx.SendFiles(r'C:\path\to\file.txt', '目标用户')

# 发送多个文件
files = [
    r'C:\path\to\file1.txt',
    r'C:\path\to\file2.jpg',
    r'C:\path\to\file3.pdf'
]
wx.SendFiles(files, '目标用户')

# 向当前聊天窗口发送文件
wx.SendFiles(r'C:\path\to\file.txt')
```

**参数说明：**
- `filepath` (str|list): 文件的绝对路径，支持单个文件或文件列表
- `who` (str, optional): 发送对象，不指定则发送给当前聊天对象
- `exact` (bool, optional): 是否精确匹配用户名，默认 False

### 4. 获取消息 - GetAllMessage

```python
# 获取当前聊天窗口的所有消息
all_messages = wx.GetAllMessage()
```

**返回值：**
- `List[Message]`: 消息列表，每个消息对象包含发送者、内容、时间、类型等信息

### 5. 监听消息 - AddListenChat

```python
def on_message(msg, chat):
    """消息回调函数"""
    print(f'收到来自 {chat} 的消息: {msg.content}', flush=True)
    
    # 自动回复
    if msg.content == 'hello':
        chat.SendMsg('Hello! 我是xxx')

# 添加消息监听
wx.AddListenChat('好友昵称', on_message)
```

**参数说明：**
- `who` (str|List[str]): 监听对象，支持单个或多个
- `callback` (Callable): 回调函数，接收 `(msg, chat)` 两个参数

### 6. 移除监听 - RemoveListenChat

```python
# 移除特定对象的监听
wx.RemoveListenChat('好友昵称')

# 停止所有监听
wx.StopListening()
```

### 7. 切换聊天窗口 - ChatWith

```python
# 切换到指定聊天窗口
wx.ChatWith('好友昵称')
```

**参数说明：**
- `who` (str): 要切换到的聊天对象
- `exact` (bool, optional): 是否精确匹配名称

### 8. 获取子窗口实例 - GetSubWindow

```python
# 获取指定聊天的子窗口
chat_window = wx.GetSubWindow('好友昵称')

# 通过子窗口发送消息（不会切换主窗口）
chat_window.SendMsg('这是通过子窗口发送的消息')

# 获取子窗口信息
info = chat_window.ChatInfo()
print(f'聊天对象: {info["chat_name"]}')

# 关闭子窗口
chat_window.Close()
```

### 9. 获取所有子窗口实例 - GetAllSubWindow

```python
# 获取所有打开的子窗口
all_windows = wx.GetAllSubWindow()

for window in all_windows:
    print(f'窗口: {window.who}')
    # 可以对每个窗口进行操作
    window.SendMsg('批量消息发送')
    
# 关闭所有子窗口
for window in all_windows:
    window.Close()
```

### 10. 停止监听 - StopListening

```python
# 停止所有消息监听
wx.StopListening()

# 程序结束前建议停止监听
try:
    wx.SendMsg('程序即将结束', '管理员')
finally:
    wx.StopListening()
```

## 监听稳定性优化建议

微信 4.x 客户端的消息读取依赖 UIAutomation 控件树，控件可见性、窗口状态和微信版本都会影响监听稳定性。以下实践可显著提升监听长时间运行的稳定性。

### 使用独立子窗口而非主窗口

`AddListenChat` 会为每个被监听对象打开一个独立的聊天子窗口，避免主窗口切换会话导致控件树变化。**不要**在监听期间用 `ChatWith` 切换主窗口到其他会话——会打断当前主聊天框的控件绑定。

### 调整 `LISTEN_INTERVAL`

默认每秒轮询一次（`WxParam.LISTEN_INTERVAL = 1`）。如果回调处理较重或 CPU 占用敏感，可放宽到 2–3 秒；如果需要更低延迟，可降到 0.5 秒但会显著增加 CPU 占用。

```python
from wxauto4 import WxParam

WxParam.LISTEN_INTERVAL = 2          # 轮询间隔（秒）
WxParam.LISTENER_EXCUTOR_WORKERS = 8 # 回调线程池大小
```

### 回调函数要快、要幂等

监听线程把新消息丢到线程池执行回调，但单条消息的回调若超过 `LISTEN_INTERVAL`，下一轮就会堆积。回调里**不要**做阻塞 IO；要做长任务请把消息丢到自己的队列里异步处理。回调内调用 `chat.SendMsg` 是允许的，但需注意 `@uilock` 会自动串行化。

### 启用消息哈希去重

```python
WxParam.MESSAGE_HASH = True
```

启用后每条消息会计算 md5 哈希存入 `msg.hash`，可用于跨轮次去重。代价是每次解析多算一次 md5，对一般负载可忽略。

### 群聊发送者识别

群聊消息的发送者昵称通过递归子树解析得到，失败时默认启用 Windows OCR 兜底（`ENABLE_SENDER_OCR = True`）。如果不需要发送者精度，可关闭 OCR 以提升性能：

```python
WxParam.ENABLE_SENDER_OCR = False
```

### 优雅关闭

```python
import signal

def on_exit(signum, frame):
    wx.StopListening()
    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)

wx.KeepRunning()  # 维持微信前台运行
```

---

## 消息对象

`GetAllMessage` / `GetNewMessage` / `GetLastMessage` 返回 `Message` 实例。每条消息按 **属性**（发送者身份）和 **类型**（内容形态）两个维度归类。

### 字段访问

消息对象支持字典协议，可直接按字段名取值：

```python
msg = wx.GetLastMessage()
print(msg.content)              # 属性访问
print(msg['content'])           # 字典式访问
print(msg.get('sender', '?'))   # 带默认值
print(dict(msg))                # 转字典
```

### 公开字段

| 字段 | 说明 |
|---|---|
| `id` | 控件 runtime id（消息唯一标识） |
| `content` | 消息文本内容（引用消息已展开为「正文 + 引用」拼接） |
| `hash` | md5 摘要（需开启 `WxParam.MESSAGE_HASH`） |
| `sender` | 发送者标识，系统消息为 `'system'`，自己为 `'我'` |
| `sender_remark` | 发送者备注名 |
| `type` | 内容类型：`text`/`quote`/`voice`/`image`/`video`/`file`/`link`/`location`/`personal_card`/`other` |
| `attr` | 发送者属性：`system`/`friend`/`self` |
| `direction` | UIA 方向标识 |
| `parent` | 所属聊天框 |
| `control` | 底层 UIA 控件 |

### 状态判断

```python
msg.is_self      # 自己发的
msg.is_friend    # 对方发的
msg.is_system    # 系统消息
```

### 消息动作（仅 HumanMessage）

```python
# 转发到单个或多个对象
msg.forward('文件传输助手')
msg.forward(['群A', '群B'], interval=0.2)

# 引用并回复
msg.quote('收到', at='@张三')

# 右键菜单选择项
msg.select_option('收藏')

# 鼠标交互
msg.click()
msg.right_click()
```

### 条件匹配

```python
# 找出张三在 10 分钟内发的所有图片消息
for m in wx.GetAllMessage():
    if m.match(sender='张三', type='image'):
        ...
```

完整字段与方法列表详见 [docs/api/message.md](docs/api/message.md)。

---

## 朋友圈

`WeChat` 实例的 `Moment` 属性提供朋友圈接口。

```python
wx.SwitchToMoments()  # 进入朋友圈界面

# 读取朋友圈
moments = wx.Moment.GetMoments()
for item in moments:
    print(item.publisher, item.text[:30], item.timestamp)
    print('点赞:', item.like_users)
    print('评论:', [c.content for c in item.comment_list])

# 按发布者过滤
target = wx.Moment.FindMomentByPublisher('张三')

# 点赞 / 取消点赞
wx.Moment.Like(target)
wx.Moment.Like(target, cancel=True)

# 评论 / 回复评论
wx.Moment.Comment(target, '写得真好')
wx.Moment.Comment(target, '同感', reply_to='李四')
```

### MomentItem 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `publisher` | str | 发布者昵称 |
| `text` | str | 正文内容 |
| `timestamp` | str | 时间字符串 |
| `location` | str \| None | 位置信息 |
| `like_users` | List[str] | 点赞用户列表 |
| `comment_list` | List[MomentComment] | 评论列表 |
| `image_count` | int | 图片数量 |
| `is_advertisement` | bool | 是否为广告 |

完整接口详见 [docs/api/moment.md](docs/api/moment.md)。

---

## 会话列表

```python
for session in wx.GetSession():
    print(session.name, '未读:', session.unread_count)
    # session.pin()              # 置顶
    # session.unpin()            # 取消置顶
    # session.mark_unread()      # 标记未读
    # session.toggle_mute()      # 切换免打扰
    # session.open_in_separate_window()  # 独立窗口
    # session.hide()             # 隐藏会话
    # session.delete()           # 删除会话
```

---

## 侧边栏导航

`WeChat` 提供 11 个 `SwitchTo*` 方法切换侧边栏视图：

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

---

## 全局参数 WxParam

`WxParam` 是一组类属性，可直接修改以调整运行时行为。

```python
from wxauto4 import WxParam

WxParam.LANGUAGE = 'cn'                  # UI 语言：'cn'/'cn_t'/'en'
WxParam.DEFAULT_SAVE_PATH = r'D:\WeChat Files'  # 文件/图片保存目录
WxParam.LISTEN_INTERVAL = 1              # 监听轮询间隔（秒）
WxParam.SEARCH_CHAT_TIMEOUT = 2          # 搜索聊天对象超时（秒）
WxParam.ENABLE_SENDER_OCR = True         # 群聊发送者解析失败时启用 OCR 兜底
WxParam.MESSAGE_HASH = False             # 启用消息 md5 哈希
```

完整字段表详见 [docs/api/param.md](docs/api/param.md)。

---

## 统一响应 WxResponse

`SendMsg`、`SendFiles`、`Like`、`Comment` 等动作类方法返回 `WxResponse` 实例，三态描述调用结果。

```python
resp = wx.SendMsg('hi', '张三')
if resp:                       # __bool__ 等价于 is_success
    print('发送成功')
else:
    print(resp['status'], resp['message'])

# 主动构造（库内部或自定义回调中使用）
from wxauto4 import WxResponse
ok = WxResponse.success('已发送')
bad = WxResponse.failure('未找到目标聊天')
err = WxResponse.error('网络异常')
```

| 字段 | 说明 |
|---|---|
| `status` | `'成功'` / `'失败'` / `'错误'` |
| `message` | 人类可读信息 |
| `data` | 附加上下文（dict） |

详见 [docs/api/response.md](docs/api/response.md)。

---

## 异常处理

`wxauto4` 提供四个异常类，全部继承自 `WxautoError`。

| 异常 | 触发场景 |
|---|---|
| `WxautoError` | 基类，所有项目异常的父类 |
| `NetWorkError` | 微信无法连接到网络 |
| `WxautoUINotFoundError` | 未找到目标 UI 控件 |
| `WxautoNoteLoadTimeoutError` | 微信笔记加载超时 |

```python
from wxauto4 import WxautoUINotFoundError, WxautoError

try:
    wx.ChatWith('不存在的用户')
except WxautoUINotFoundError as e:
    print('控件找不到:', e)
except WxautoError as e:
    print('其他错误:', e, e.detail)
```

---

## 已知问题

- **`SwitchToFiles()` / `SwitchToStories()` 在微信 4.0.5 部分版本下点击后侧边栏不会切换**（详见 [test_report_20260617.md](test_report_20260617.md)）
- **`GetMoments(refresh=True)` 强制刷新后可能返回 0 条**：受朋友圈列表控件重渲染时机影响，建议改为先 `SwitchToMoments()` 等待几秒再 `GetMoments(refresh=False)`
- **`GetMessageById(msg_id)` 对最后一条文件消息可能返回 `None`**：UIAutomation 偶发无法定位到最后一条消息控件
- 监听器在窗口被手动最小化/关闭时停止响应，建议配合 `wx.KeepRunning()` 维持前台

如遇上述或新问题，请按 [Issue 模板](.github/ISSUE_TEMPLATE/bug_report.md) 提交反馈。

---

## 贡献

欢迎提交 Issue 与 Pull Request。提交前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发环境、提交规范与测试要求。

---

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)。当前版本 **40.1.1**。

---

## 致谢

- [uiautomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)：yinkaisheng 的 Windows UIAutomation 封装
- [wxauto](https://github.com/cluic/wxauto)：本项目的前身（微信 3.x 客户端版本）
