# 消息收发

本指南覆盖消息**发送**与**读取**的全部模式。消息对象本身的字段与方法见 [Message API](../api/message.md)。

## 切换目标聊天

`SendMsg` / `SendFiles` 第二个参数 `who` 会触发搜索切换：

```python
wx.SendMsg('hi', '张三')         # 精确切换到「张三」并发送
wx.SendMsg('hi', '张三', exact=False)  # 模糊匹配
```

如果需要在切换前确认目标存在，显式调用 `ChatWith`：

```python
wx.ChatWith('张三')              # 切换主聊天框
wx.SendMsg('hi')                 # 不带 who，发到当前
```

`ChatWith` 接受额外参数：

```python
wx.ChatWith('张三', exact=True, force=False, force_wait=0.5)
```

| 参数 | 含义 |
|---|---|
| `who` | 目标聊天名 |
| `exact` | 是否精确匹配（默认 True） |
| `force` | 找不到时是否仍尝试点击第一个结果（默认 False） |
| `force_wait` | 点击后等待主聊天框稳定的秒数 |

## 发送文本

### 基础

```python
wx.SendMsg('你好')               # 发到当前聊天
wx.SendMsg('你好', '张三')        # 切换到张三并发送
```

### @ 用户

群聊中通过 `at` 参数 @：

```python
wx.SendMsg('请查收', '工作群', at='张三')
wx.SendMsg('请查收', '工作群', at=['张三', '李四'])
```

`at` 接受单个字符串或字符串列表。列表中每个名字会依次展开为 `@名字 `。

### 保留输入框

调试时可以发送后不清空输入框：

```python
wx.SendMsg('草稿', clear=False)
```

## 发送文件

```python
# 单个文件
wx.SendFiles(r'C:\report.pdf', '张三')

# 多个文件
wx.SendFiles([r'C:\a.pdf', r'C:\b.png'], '张三')

# 发到当前聊天
wx.SendFiles(r'C:\report.pdf')
```

文件支持任意微信可识别的格式（图片、视频、文档、压缩包等），发送通过剪贴板 `CF_HDROP` 实现。

## 读取消息

### 当前聊天全部消息

```python
for msg in wx.GetAllMessage():
    print(msg.type, msg.sender, '|', msg.content)
```

### 自上次以来的新消息

```python
# 第一次调用返回当前可见全部消息并标记基线
new = wx.GetNewMessage()

# 后续调用只返回新增
new = wx.GetNewMessage()
```

`GetNewMessage` 基于消息控件 runtime id 增量识别，跨多轮调用持续有效。

### 最后一条消息

```python
last = wx.GetLastMessage()
if last and last.content == '/help':
    wx.SendMsg('可用命令：…')
```

### 按 id 或 hash 查询

```python
# 按 runtime id
msg = wx.GetMessageById(last.id)

# 按 md5 hash（需开启 WxParam.MESSAGE_HASH = True）
msg = wx.GetMessageByHash(some_hash)
```

## 消息对象常用操作

```python
msg = wx.GetLastMessage()

# 状态判断
msg.is_self / msg.is_friend / msg.is_system

# 字段访问
msg.content / msg.sender / msg.type / msg.attr
msg['sender']  # 字典式
dict(msg)      # 转字典

# 转发
msg.forward('文件传输助手')

# 引用并回复
msg.quote('收到')

# 右键菜单
msg.select_option('收藏')

# 互动
msg.click()
msg.right_click()
```

完整字段与方法见 [Message API](../api/message.md)。

## 子窗口操作

为了避免切换主聊天框影响其他逻辑，可以打开独立子窗口：

```python
chat = wx.GetSubWindow('张三')   # 不存在则新建
chat.SendMsg('hi')
chat.SendFiles(r'C:\file.txt')
for m in chat.GetAllMessage():
    print(m.content)
chat.Close()

# 枚举所有打开的子窗口
for chat in wx.GetAllSubWindow():
    print(chat.who)
```

子窗口的 `Chat` 对象支持主窗口几乎所有的收发与读取方法，区别仅在于不切换主聊天框。

## 错误处理

```python
from wxauto4 import WxautoError, WxautoUINotFoundError

try:
    wx.SendMsg('hi', '不存在的联系人')
except WxautoUINotFoundError:
    print('联系人不存在')
except WxautoError as e:
    print('其他错误：', e)
```

## 下一步

- 监听器场景：[消息监听指南](listener.md)
- 完整消息字段：[Message API](../api/message.md)
