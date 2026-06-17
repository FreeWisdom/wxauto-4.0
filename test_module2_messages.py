"""
测试模块2：消息收发与获取
验证 SendMsg、SendFiles、GetAllMessage、GetNewMessage、
GetMessageById、GetMessageByHash、GetLastMessage。

用法：
    python test_module2_messages.py

前提：已登录微信 4.0.5 客户端
测试对象：自动使用会话列表中的"文件传输助手"或你提供的好友/群聊
"""

import sys, time, traceback, os

try:
    from wxauto4 import WeChat, WxResponse
except ImportError:
    print("[错误] 未安装 wxauto4，请先执行: pip install wxauto4")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 配置: 修改为你的测试对象
# ---------------------------------------------------------------------------
ALLOWED_TARGETS = ("每日饮食打卡🍽️", "每日饮食打卡", "项目研究")
TEST_TARGET = "每日饮食打卡🍽️"   # 测试用的聊天对象（必须属于 ALLOWED_TARGETS）
SEND_MSG_CONTENT = f"wxauto4 测试消息 - {time.strftime('%H:%M:%S')}"
TEST_FILE_PATH = os.path.abspath("wxauto4_safe_test_file.txt")
# ---------------------------------------------------------------------------


def separator(title=""):
    print()
    print("=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def find_test_target(wx, preferred=TEST_TARGET):
    """在会话列表中查找测试目标，返回纯聊天名"""
    if not is_allowed_target(preferred):
        print(f"  [安全拦截] preferred 不在白名单: {preferred}")
        return None
    print(f"\n--- 查找测试目标 ---")
    sessions = wx.GetSession()
    # 精确匹配 name 属性
    for s in sessions:
        if s.name == preferred:
            print(f"  [通过] 找到测试目标: {s.name}")
            return s.name
    # 模糊匹配：先检查 name 是否以 preferred 开头
    for s in sessions:
        if s.name.startswith(preferred):
            print(f"  [通过] 前缀匹配到测试目标: {preferred}")
            return preferred
    # 再检查 name 中是否包含 preferred
    for s in sessions:
        if preferred in s.name:
            print(f"  [通过] 包含匹配到测试目标: {preferred}")
            return preferred
    print(f"  [失败] 未找到指定的测试目标 '{preferred}'，使用当前聊天窗口")
    return None


def is_allowed_target(name):
    if not name:
        return False
    return any(allowed in name or name in allowed for allowed in ALLOWED_TARGETS)


def current_chat_is_allowed(wx):
    try:
        info = wx.ChatInfo()
        chat_name = info.get("chat_name", "")
        allowed = is_allowed_target(chat_name)
        print(f"  当前聊天: {chat_name or '(未知)'} | 白名单校验: {'通过' if allowed else '失败'}")
        return allowed
    except Exception as e:
        print(f"  [安全拦截] 无法读取当前聊天信息: {e}")
        return False


def ensure_safe_target(wx, target):
    if not is_allowed_target(target):
        print(f"  [安全拦截] 目标不在允许群列表: {target}")
        return False
    try:
        result = wx.ChatWith(target)
        print(f"  [安全校验] 切换结果: {result}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  [安全拦截] 切换到目标失败: {e}")
        return False
    return current_chat_is_allowed(wx)


def test_send_msg(wx, target):
    """测试 1: 发送文本消息"""
    print("\n--- 1. SendMsg: 发送文本消息 ---")
    print(f"  发送对象: {target or '(当前聊天窗口)'}")
    print(f"  消息内容: {SEND_MSG_CONTENT}")
    if not ensure_safe_target(wx, target):
        print("  [跳过] 未确认安全目标，取消发送")
        return None
    try:
        resp = wx.SendMsg(msg=SEND_MSG_CONTENT, who=target, clear=True)
        if isinstance(resp, WxResponse):
            if resp.is_success:
                print(f"  [通过] 消息发送成功")
            else:
                print(f"  [失败] 消息发送失败: {resp.get('message')}")
        else:
            print(f"  [通过] 消息发送成功")
        return resp
    except Exception as e:
        print(f"  [失败] 发送消息异常: {e}")
        traceback.print_exc()
        return None


def test_send_msg_with_at(wx, target):
    """测试 2: 发送带 @ 的消息（仅群聊有效）"""
    print("\n--- 2. SendMsg: 发送带@消息 ---")
    print(f"  发送对象: {target or '(当前聊天窗口)'}")
    if not ensure_safe_target(wx, target):
        print("  [跳过] 未确认安全目标，取消@发送")
        return None
    try:
        print("  [跳过] @测试可能打扰群成员，本轮只验证普通发送；如需专项 @ 测试再手动启用")
        return None
        at_content = f"@测试消息 - {time.strftime('%H:%M:%S')}"
        resp = wx.SendMsg(msg=at_content, who=target, at=["所有人"], clear=True)
        if isinstance(resp, WxResponse):
            if resp.is_success:
                print(f"  [通过] @消息发送成功")
            else:
                print(f"  [提示] @消息发送失败（可能不是群聊）: {resp.get('message')}")
        else:
            print(f"  [通过] @消息发送成功")
        return resp
    except Exception as e:
        print(f"  [提示] 发送@消息异常（可能不支持）: {e}")
        return None


def test_send_msg_no_target(wx):
    """测试 3: 不指定 who 参数发送消息"""
    print("\n--- 3. SendMsg: 不指定发送对象 ---")
    if not current_chat_is_allowed(wx):
        print("  [跳过] 当前窗口不是允许测试群，取消 who=None 发送")
        return None
    try:
        msg = f"无目标测试 - {time.strftime('%H:%M:%S')}"
        resp = wx.SendMsg(msg=msg, clear=True)
        if isinstance(resp, WxResponse):
            if resp.is_success:
                print(f"  [通过] 发送成功（当前聊天窗口）")
            else:
                print(f"  [提示] 发送结果: {resp.get('message')}")
        return resp
    except Exception as e:
        print(f"  [失败] 发送消息异常: {e}")
        return None


def test_send_files(wx, target):
    """测试 4: 发送文件"""
    print("\n--- 4. SendFiles: 发送文件 ---")
    if not os.path.exists(TEST_FILE_PATH):
        with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(f"wxauto4 安全文件发送测试 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"  发送文件: {TEST_FILE_PATH}")
    print(f"  发送对象: {target or '(当前聊天窗口)'}")
    if not ensure_safe_target(wx, target):
        print("  [跳过] 未确认安全目标，取消文件发送")
        return None
    try:
        resp = wx.SendFiles(filepath=TEST_FILE_PATH, who=target)
        if isinstance(resp, WxResponse):
            if resp.is_success:
                print(f"  [通过] 文件发送成功")
            else:
                print(f"  [失败] 文件发送失败: {resp.get('message')}")
        else:
            print(f"  [通过] 文件发送成功")
        return resp
    except Exception as e:
        print(f"  [失败] 发送文件异常: {e}")
        traceback.print_exc()
        return None


def test_get_all_messages(wx, target):
    """测试 5: GetAllMessage 获取当前聊天所有消息"""
    print("\n--- 5. GetAllMessage: 获取当前聊天所有消息 ---")
    if target:
        if not ensure_safe_target(wx, target):
            print("  [跳过] 未确认安全目标，取消读取")
            return []
    try:
        msgs = wx.GetAllMessage()
        print(f"  [通过] 获取到 {len(msgs)} 条消息")
        for msg in msgs[-5:]:  # 只显示最后 5 条
            sender = getattr(msg, 'sender', '系统')
            content = str(msg.content)[:50]
            print(f"      [{sender}] {content}")
        return msgs
    except Exception as e:
        print(f"  [失败] 获取所有消息异常: {e}")
        traceback.print_exc()
        return []


def test_get_new_messages(wx, target):
    """测试 6: GetNewMessage 获取新消息"""
    print("\n--- 6. GetNewMessage: 获取新消息 ---")
    if target:
        if not ensure_safe_target(wx, target):
            print("  [跳过] 未确认安全目标，取消读取")
            return []
    try:
        # 先建立基线
        wx.GetAllMessage()
        time.sleep(0.5)
        # 再获取新消息
        msgs = wx.GetNewMessage()
        print(f"  [通过] 获取到 {len(msgs)} 条新消息（应为 0，因为无新消息）")
        return msgs
    except Exception as e:
        print(f"  [失败] 获取新消息异常: {e}")
        traceback.print_exc()
        return []


def test_get_last_message(wx, target):
    """测试 7: GetLastMessage 获取最后一条消息"""
    print("\n--- 7. GetLastMessage: 获取最后一条消息 ---")
    if target:
        if not ensure_safe_target(wx, target):
            print("  [跳过] 未确认安全目标，取消读取")
            return None
    try:
        msg = wx.GetLastMessage()
        if msg:
            sender = getattr(msg, 'sender', '?')
            content = str(msg.content)[:100]
            print(f"  [通过] 最后一条消息: [{sender}] {content}")
        else:
            print(f"  [通过] 最后一条消息为空（窗口可能无消息）")
        return msg
    except Exception as e:
        print(f"  [失败] 获取最后一条消息异常: {e}")
        traceback.print_exc()
        return None


def test_get_msg_by_id(wx, target):
    """测试 8: GetMessageById 根据 runtime ID 获取消息"""
    print("\n--- 8. GetMessageById: 根据 runtime ID 获取消息 ---")
    if target:
        if not ensure_safe_target(wx, target):
            print("  [跳过] 未确认安全目标，取消读取")
            return
    try:
        msgs = wx.GetAllMessage()
        if msgs:
            test_msg = msgs[-1]
            # 消息 ID 可能存储在不同属性名中
            msg_id = getattr(test_msg, 'id', None) or getattr(test_msg, '_runtimeid', None) or getattr(test_msg, 'runtime_id', None)
            if msg_id:
                found = wx.GetMessageById(msg_id)
                if found:
                    print(f"  [通过] 根据 ID 找到消息: {str(found.content)[:50]}")
                else:
                    print(f"  [失败] 根据 ID 未找到消息")
            else:
                print(f"  [提示] 无法获取消息 ID")
        else:
            print(f"  [跳过] 当前窗口无消息可用")
    except Exception as e:
        print(f"  [失败] GetMessageById 异常: {e}")
        traceback.print_exc()


def test_get_msg_by_hash(wx, target):
    """测试 9: GetMessageByHash 根据哈希值获取消息"""
    print("\n--- 9. GetMessageByHash: 根据哈希值获取消息 ---")
    if target:
        if not ensure_safe_target(wx, target):
            print("  [跳过] 未确认安全目标，取消读取")
            return
    try:
        msgs = wx.GetAllMessage()
        if msgs:
            test_msg = msgs[-1]
            msg_hash = getattr(test_msg, 'hash', None)
            if msg_hash:
                found = wx.GetMessageByHash(msg_hash)
                if found:
                    print(f"  [通过] 根据哈希找到消息: {str(found.content)[:50]}")
                else:
                    print(f"  [提示] 根据哈希未找到消息")
            else:
                # 使用 hash_text 作为备选
                hash_text = getattr(test_msg, 'hash_text', None)
                if hash_text:
                    found = wx.GetMessageByHash(hash_text)
                    if found:
                        print(f"  [通过] 根据哈希文本找到消息: {str(found.content)[:50]}")
                    else:
                        print(f"  [提示] 根据哈希文本未找到消息")
                else:
                    print(f"  [提示] 消息无哈希属性")
        else:
            print(f"  [跳过] 当前窗口无消息可用")
    except Exception as e:
        print(f"  [失败] GetMessageByHash 异常: {e}")
        traceback.print_exc()


def test_subwindow_messages(wx, target):
    """测试 10: 通过子窗口发送和获取消息"""
    print("\n--- 10. 子窗口消息操作 ---")
    if not target:
        print(f"  [跳过] 未指定测试目标")
        return

    try:
        if not is_allowed_target(target):
            print(f"  [安全拦截] 子窗口目标不在允许群列表: {target}")
            return
        sub_win = wx.GetSubWindow(target)
        if sub_win:
            print(f"  [通过] 获取到子窗口: {sub_win.who}")
            msg = f"子窗口消息测试 - {time.strftime('%H:%M:%S')}"
            resp = sub_win.SendMsg(msg=msg)
            if isinstance(resp, WxResponse) and resp.is_success or not isinstance(resp, WxResponse):
                print(f"  [通过] 通过子窗口发送消息成功")
            else:
                print(f"  [提示] 子窗口发送消息结果: {resp}")

            msgs = sub_win.GetAllMessage()
            print(f"  [通过] 子窗口获取到 {len(msgs)} 条消息")
        else:
            print(f"  [提示] 未找到 {target} 的子窗口")
    except Exception as e:
        print(f"  [失败] 子窗口消息操作异常: {e}")
        traceback.print_exc()


def run_all_tests():
    separator("测试模块2：消息收发与获取")

    print(f"\n配置信息:")
    print(f"  测试对象: {TEST_TARGET}")
    print(f"  测试消息: {SEND_MSG_CONTENT}")
    print(f"  测试文件: {TEST_FILE_PATH or '(未配置，将跳过文件测试)'}")

    # 初始化
    print("\n--- 初始化 WeChat ---")
    try:
        wx = WeChat()
        print(f"  [通过] 初始化成功，当前账号: {wx.nickname}")
    except Exception as e:
        print(f"  [失败] 初始化失败: {e}")
        sys.exit(1)

    # 查找测试目标
    target = find_test_target(wx)

    # 切换到测试目标窗口
    if target:
        print(f"\n--- 切换到 {target} ---")
        result = ensure_safe_target(wx, target)
        print(f"  [结果] 安全切换{'成功' if result else '失败'}")

    # 执行测试
    test_send_msg(wx, target)
    test_send_msg_with_at(wx, target)
    test_send_msg_no_target(wx)
    test_send_files(wx, target)
    test_get_all_messages(wx, target)
    test_get_new_messages(wx, target)
    test_get_last_message(wx, target)
    test_get_msg_by_id(wx, target)
    test_get_msg_by_hash(wx, target)
    test_subwindow_messages(wx, target)

    separator("测试模块2 完成")


if __name__ == "__main__":
    run_all_tests()
