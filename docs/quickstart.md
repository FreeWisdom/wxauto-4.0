# 快速开始

本页提供 5 个最小可运行示例，覆盖 90% 的日常用法。完整 API 见 [API 参考](api/wechat.md)。

## 示例 1：初始化与发消息

```python
from wxauto4 import WeChat

wx = WeChat()                       # 绑定已登录的微信主窗口
print(wx.nickname)                  # 当前账号昵称

wx.SendMsg('你好，世界！', '好友昵称')
```

`SendMsg` 第二个参数是目标聊天对象名（昵称或备注）。不指定则发送到当前聊天。

## 示例 2：发文件

```python
# 单个文件
wx.SendFiles(r'C:\path\to\file.txt', '好友昵称')

# 多个文件
files = [
    r'C:\path\to\a.txt',
    r'C:\path\to\b.jpg',
    r'C:\path\to\c.pdf',
]
wx.SendFiles(files, '好友昵称')

# 向当前聊天窗口发送（不切换）
wx.SendFiles(r'C:\path\to\file.txt')
```

## 示例 3：读取消息

```python
# 当前聊天的所有消息
for msg in wx.GetAllMessage():
    print(msg.sender, '|', msg.content)

# 最近一条消息
last = wx.GetLastMessage()
print(last.content)

# 自上次调用以来的新消息
new_msgs = wx.GetNewMessage()
```

## 示例 4：消息监听

```python
def on_message(msg, chat):
    """每收到一条新消息时被调用"""
    print(f'[{chat.who}] {msg.sender}: {msg.content}')
    if msg.content == 'hello':
        chat.SendMsg('Hello! 我是 xxx')

# 为多个聊天注册监听
wx.AddListenChat('好友A', on_message)
wx.AddListenChat('好友B', on_message)

# 程序退出前停止
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    wx.StopListening()
```

## 示例 5：@ 用户

```python
# 在群聊中 @ 单个用户
wx.SendMsg('请查看', '群名', at='张三')

# @ 多个用户
wx.SendMsg('请查看', '群名', at=['张三', '李四'])
```

## 完整命令行演示

仓库根目录的 [demo.py](../demo.py) 提供了覆盖全部公开 API 的命令行演示，可以作为运行示例的「索引」：

```bash
python demo.py --target "好友昵称" --message "你好"
python demo.py --listen "好友昵称" --listen-duration 60
python demo.py --moments --like
python demo.py --navigate moments
```

`python demo.py --help` 查看全部子命令。

## 下一步

- 完整 API：[WeChat 类](api/wechat.md)
- 深入消息对象：[Message](api/message.md)
- 监听器最佳实践：[消息监听指南](guide/listener.md)
