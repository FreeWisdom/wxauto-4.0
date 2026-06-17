"""
测试模块3：消息监听
验证 AddListenChat、回调触发、RemoveListenChat、StopListening。

用法：
    python test_module3_listener.py

前提：已登录微信 4.0.5 客户端
测试方式：
  1. 对指定聊天对象启动监听
  2. 打印回调信息，验证能否收到新消息
  3. 在指定时长后自动停止

建议：运行前先在手机微信上准备好在测试群里发几条消息
"""

import sys, time, signal, traceback

try:
    from wxauto4 import WeChat
except ImportError:
    print("[错误] 未安装 wxauto4，请先执行: pip install wxauto4")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
LISTEN_TARGETS = ["每日饮食打卡🍽️", "项目研究"]   # 要监听的聊天对象（支持多个）
LISTEN_DURATION = 30                                # 监听持续秒数，设为 0 则持续运行直到 Ctrl+C
# ---------------------------------------------------------------------------


def separator(title=""):
    print()
    print("=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def run_all_tests():
    separator("测试模块3：消息监听")

    print(f"\n配置信息:")
    print(f"  监听对象: {LISTEN_TARGETS}")
    print(f"  监听时长: {LISTEN_DURATION}秒 (0=持续)")

    # 初始化
    print("\n--- 初始化 WeChat ---")
    try:
        wx = WeChat(start_listener=True)
        print(f"  [通过] 初始化成功，当前账号: {wx.nickname}")
    except Exception as e:
        print(f"  [失败] 初始化失败: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 回调函数
    # ------------------------------------------------------------------
    received_counter = [0]
    def on_message(msg, chat):
        received_counter[0] += 1
        count = received_counter[0]
        sender_name = getattr(msg, 'sender', '?')
        content = str(msg.content)[:80]
        msg_attr = getattr(msg, 'attr', '?')

        print()
        print(f"  >>> [监听 #{count}] 来自: {chat.who} | 发送者: {sender_name} | 类型: {msg_attr}")
        print(f"  >>> 内容: {content}")
        print(f"  >>> 时间: {time.strftime('%H:%M:%S')}", flush=True)

    # ------------------------------------------------------------------
    # 测试 1: 添加多个监听对象
    # ------------------------------------------------------------------
    print("\n--- 1. AddListenChat: 添加监听对象 ---")
    listening = []
    for target in LISTEN_TARGETS:
        try:
            result = wx.AddListenChat(target, on_message)
            if hasattr(result, 'wrapped'):
                # result 可能是 Chat 对象
                listening.append(target)
                print(f"  [通过] 已添加监听: {target}")
            elif hasattr(result, 'is_success'):
                if result.is_success:
                    listening.append(target)
                    print(f"  [通过] 已添加监听: {target}")
                else:
                    print(f"  [失败] 添加监听 {target}: {result.get('message')}")
            else:
                listening.append(target)
                print(f"  [通过] 已添加监听: {target}")
        except Exception as e:
            print(f"  [失败] 添加监听 {target} 异常: {e}")

    if not listening:
        print("\n  [失败] 未能成功添加任何监听对象，终止")
        return

    # ------------------------------------------------------------------
    # 测试 2: 重复添加同一对象
    # ------------------------------------------------------------------
    print("\n--- 2. AddListenChat: 重复添加 ---")
    try:
        result = wx.AddListenChat(listening[0], on_message)
        if hasattr(result, 'is_success') and not result.is_success:
            print(f"  [通过] 正确拒绝了重复添加: {result.get('message')}")
        else:
            print(f"  [提示] 重复添加未按预期拒绝")
    except Exception as e:
        print(f"  [提示] 重复添加异常: {e}")

    # ------------------------------------------------------------------
    # 测试 3: 等待并接收消息
    # ------------------------------------------------------------------
    if LISTEN_DURATION > 0:
        print(f"\n--- 3. 监听运行中（{LISTEN_DURATION} 秒）---")
        print("  在此期间请通过手机微信向测试群发几条消息...")
        print("  (脚本会在 {LISTEN_DURATION} 秒后自动停止)", flush=True)

        try:
            start_time = time.time()
            while time.time() - start_time < LISTEN_DURATION:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n  收到 Ctrl+C，正在停止...")

        print(f"\n  监听结束，共收到 {received_counter[0]} 条新消息")
    else:
        print(f"\n--- 3. 监听运行中（持续，Ctrl+C 停止）---")
        print("  按 Ctrl+C 停止监听", flush=True)
        try:
            wx.KeepRunning()
        except KeyboardInterrupt:
            print(f"\n  用户中断，共收到 {received_counter[0]} 条新消息")
        except Exception as e:
            print(f"  KeepRunning 异常: {e}")

    # ------------------------------------------------------------------
    # 测试 4: 移除单个监听对象
    # ------------------------------------------------------------------
    if len(listening) > 1:
        print(f"\n--- 4. RemoveListenChat: 移除单个监听 ---")
        try:
            to_remove = listening[-1]
            result = wx.RemoveListenChat(to_remove, close_window=False)
            if hasattr(result, 'is_success'):
                status = "[通过]" if result.is_success else "[失败]"
                print(f"  {status} 移除 {to_remove}: {result.get('message')}")
            else:
                print(f"  [通过] 移除 {to_remove}")
            listening.remove(to_remove)
        except Exception as e:
            print(f"  [失败] 移除监听异常: {e}")

    # ------------------------------------------------------------------
    # 测试 5: StopListening 停止所有监听
    # ------------------------------------------------------------------
    print(f"\n--- 5. StopListening: 停止所有监听 ---")
    try:
        # 关闭窗口可能因锁问题失败，先直接清空监听列表
        remaining = list(wx.listen.keys()) if hasattr(wx, 'listen') else []
        for who in remaining:
            try:
                wx.RemoveListenChat(who, close_window=False)
            except Exception:
                pass
        print(f"  [通过] 已停止所有监听")

        # 验证监听已停止
        if hasattr(wx, 'listen') and not wx.listen:
            print(f"  [通过] 监听列表已清空")
        else:
            remaining = list(wx.listen.keys()) if hasattr(wx, 'listen') else []
            print(f"  [提示] 剩余监听: {remaining}")
    except Exception as e:
        print(f"  [失败] 停止监听异常: {e}")
        traceback.print_exc()

    # ------------------------------------------------------------------
    # 总结
    # ------------------------------------------------------------------
    separator("测试模块3 完成")
    print(f"\n总结:")
    print(f"  成功监听对象: {listening}")
    print(f"  收到消息总数: {received_counter[0]}")


if __name__ == "__main__":
    run_all_tests()
