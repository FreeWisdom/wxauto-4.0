# Message 对象

`Message` 是 wxauto4 中所有消息的基类，定义在 [wxauto4/msgs/base.py](../../wxauto4/msgs/base.py)。每条消息按**发送者属性**（system/friend/self）与**内容类型**（text/quote/voice/image/...）两个维度分类。

## 类层级

```
Message (字典/迭代协议 + 状态判断)
  └─ BaseMessage (字段绑定: id/content/hash/control/...)
       ├─ SystemMessage           (attr='system')
       └─ HumanMessage            (attr='human', 提供 click/forward/quote)
            ├─ FriendMessage      (attr='friend', 自动解析 sender)
            └─ SelfMessage        (attr='self', sender='我')
```

按内容类型在 FriendMessage / SelfMessage 下进一步多继承出 `FriendTextMessage` / `FriendQuoteMessage` / `FriendImageMessage` / ... 与对应的 `Self*Message`。用户拿到的消息实例通常是这些叶子类。

## 字段

### 公开属性（来自 BaseMessage）

| 属性 | 类型 | 说明 |
|---|---|---|
| `id` | int | 控件 runtime id（消息唯一标识） |
| `content` | str | 消息文本（引用消息已展开） |
| `hash` | str | md5 摘要（需开启 `MESSAGE_HASH`，否则为空串） |
| `hash_text` | str | 哈希原文 |
| `direction` | 标识 | UIA 方向，用于像素定位 |
| `distince` | 标识 | 距离信息 |
| `parent` | ChatBox | 所属聊天框 |
| `control` | uia.Control | 底层 UIA 控件 |
| `root` | uia.Control | UIA 控件树根 |

### SystemMessage 字段

| 属性 | 值 |
|---|---|
| `sender` | `'system'` |
| `sender_remark` | `'system'` |

### FriendMessage / SelfMessage 字段

| 属性 | 说明 |
|---|---|
| `sender` | 发送者标识 |
| `sender_remark` | 发送者备注名 |

FriendMessage 群聊中通过递归子树提取发送者昵称，失败时回退到群名；可启用 Windows OCR 兜底（`WxParam.ENABLE_SENDER_OCR = True`）。

SelfMessage 固定 `sender='我'`。

### 引用消息（QuoteMessage）字段

除继承字段外：

| 属性 | 说明 |
|---|---|
| `quote_nickname` | 被引用消息的发送者 |
| `quote_content` | 被引用消息的内容 |

引用消息的 `content` 字段已拼接为 `正文 \n引用 {quote_nickname} 的消息 : {quote_content}`。

## 状态判断

`@property`，无需调用：

```python
msg.is_self      # 自己发的
msg.is_friend    # 对方发的
msg.is_system    # 系统消息
```

## 字典/迭代协议

`Message` 实现了完整的字典语义：

```python
msg = wx.GetLastMessage()

msg['content']                      # 字典式访问
msg.get('sender', default='?')      # 带默认值
dict(msg)                           # 转字典

msg.keys()                          # 所有字段名
msg.values()                        # 所有字段值
msg.items()                         # (key, value) 元组

for k, v in msg:                    # 迭代
    print(k, '=', v)
```

### `to_dict() -> Dict`

转字典，排除 `control`、`parent`、`root` 三个内部字段。

### `match(**conditions) -> bool`

判断当前消息是否同时满足给定的字段条件：

```python
msg.match(sender='张三', type='image')   # 张三发的图片消息
msg.match(attr='self', content='hi')     # 自己发的 hello
```

## 动作方法（仅 HumanMessage）

SystemMessage 不提供以下方法。

### `click()`

左键单击消息。

### `right_click()`

右键单击消息（触发右键菜单）。

### `select_option(option, timeout=2) -> WxResponse`

右键菜单选择指定项。

| 参数 | 说明 |
|---|---|
| `option` | 菜单项文本（如 `'收藏'`、`'转发'`、`'删除'`） |
| `timeout` | 等待菜单出现的超时（秒） |

### `forward(targets, timeout=3, interval=0.1) -> WxResponse`

转发消息。

| 参数 | 类型 | 说明 |
|---|---|---|
| `targets` | str \| List[str] | 转发目标聊天名，单个或多个 |
| `timeout` | int | 单个目标超时（秒） |
| `interval` | float | 多目标之间的间隔（秒） |

```python
msg.forward('文件传输助手')
msg.forward(['群A', '群B', '群C'], interval=0.2)
```

### `quote(text, at=None, timeout=3) -> WxResponse`

引用消息并回复。

| 参数 | 类型 | 说明 |
|---|---|---|
| `text` | str | 回复内容 |
| `at` | str \| List[str] | @ 对象 |
| `timeout` | int | 超时（秒） |

```python
msg.quote('收到，处理中')
msg.quote('已通知张三', at='张三')
```

## 类型字段

| `type` 类属性 | 类 | 解析逻辑 |
|---|---|---|
| `'text'` | TextMessage | 默认字段 |
| `'quote'` | QuoteMessage | 解析 `content`、`quote_nickname`、`quote_content` |
| `'voice'` | VoiceMessage | 语音消息 |
| `'image'` | ImageMessage | 图片消息 |
| `'video'` | VideoMessage | 视频（带 `repattern` 类属性提取时长） |
| `'file'` | FileMessage | 文件（带 `repattern` 提取文件名/大小） |
| `'link'` | LinkMessage | 链接卡片 |
| `'location'` | LocationMessage | 位置 |
| `'personal_card'` | PersonalCardMessage | 名片 |
| `'other'` | OtherMessage | 兜底类型 |

## 内部辅助方法（不保证稳定）

- `roll_into_view()` — 滚动消息至可见
- `exists()` — 判断底层控件是否仍存在

## 示例

```python
# 监听并自动转发
def on_msg(msg, chat):
    if msg.match(attr='friend', type='image'):
        msg.forward('图库群')
    if msg.content == '/ping':
        msg.quote('pong')

wx.AddListenChat('工作群', on_msg)
```

## 下一步

- 监听场景：[消息监听指南](../guide/listener.md)
- WeChat 类方法：[WeChat API](wechat.md)
