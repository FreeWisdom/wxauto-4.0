"""
@功能专项测试 - 在群聊中 @ 一个真实成员
用法：python test_at.py
"""

from wxauto4 import WeChat, WxResponse
import time

GROUP = "每日饮食打卡🍽️"
AT_TARGET = "杨宝贝"   # 改成群里一个真实群成员的昵称

wx = WeChat()
print(f"已连接: {wx.nickname}")

# 切换到目标群
print(f"\n切换到 {GROUP}...")
wx.ChatWith(GROUP)
time.sleep(0.5)

# 读取当前群信息确认
info = wx.ChatInfo()
print(f"当前聊天: {info.get('chat_name')} (类型: {info.get('chat_type')})")

# 方案A：@指定成员（真正测 @ 逻辑）
msg = f"@测试 {time.strftime('%H:%M:%S')}"
print(f"\n测试 @{AT_TARGET}...")
resp = wx.SendMsg(msg=msg, at=[AT_TARGET], clear=True)
print(f"结果: {resp}")

# 等2秒看结果
time.sleep(2)

# 获取最后一条消息，检查内容
last = wx.GetLastMessage()
if last:
    print(f"\n最后一条消息内容: '{last.content}'")
    print(f"消息类型: {getattr(last, 'type', '?')} / attr: {getattr(last, 'attr', '?')}")

print("\n检查你的微信，消息是否成功 @到了人？")
