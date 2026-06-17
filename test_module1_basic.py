"""
测试模块1：窗口和基本信息
验证 WeChat() 初始化、nickname、path、dir、ChatInfo 等基本信息获取。

用法：
    python test_module1_basic.py

前提：已登录微信 4.0.5 客户端
"""

import sys, time, traceback

try:
    from wxauto4 import WeChat
except ImportError:
    print("[错误] 未安装 wxauto4，请先执行: pip install wxauto4")
    sys.exit(1)


def separator(title=""):
    print()
    print("=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def case(desc):
    """装饰器风格的测试 case，用于打印标题和捕获异常"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"\n--- {desc} ---")
            try:
                result = func(*args, **kwargs)
                print(f"  [通过] {desc}")
                return result
            except Exception as e:
                print(f"  [失败] {desc}")
                print(f"  错误: {e}")
                traceback.print_exc()
                return None
        return wrapper
    return decorator


def run_all_tests():
    separator("测试模块1：窗口和基本信息")

    # ------------------------------------------------------------------
    # Case 1: 初始化 WeChat 实例
    # ------------------------------------------------------------------
    print("\n--- 1. 初始化 WeChat 实例 ---")
    try:
        wx = WeChat()
        print(f"  [通过] 初始化成功")
    except Exception as e:
        print(f"  [失败] 初始化 WeChat 实例: {e}")
        traceback.print_exc()
        sys.exit(1)

    # ------------------------------------------------------------------
    # Case 2: 获取当前登录账号昵称
    # ------------------------------------------------------------------
    print("\n--- 2. 获取当前登录账号昵称 ---")
    try:
        nickname = wx.nickname
        if nickname:
            print(f"  [通过] 当前昵称: {nickname}")
        else:
            print(f"  [失败] 昵称为空")
    except Exception as e:
        print(f"  [失败] 获取昵称: {e}")

    # ------------------------------------------------------------------
    # Case 3: 获取微信安装路径
    # ------------------------------------------------------------------
    print("\n--- 3. 获取微信安装路径 ---")
    try:
        path = wx.path
        if path:
            print(f"  [通过] 安装路径: {path}")
        else:
            print(f"  [失败] 安装路径为空")
    except Exception as e:
        print(f"  [失败] 获取安装路径: {e}")

    # ------------------------------------------------------------------
    # Case 4: 获取微信数据目录
    # ------------------------------------------------------------------
    print("\n--- 4. 获取微信数据目录 ---")
    try:
        d = wx.dir
        if d:
            print(f"  [通过] 数据目录: {d}")
        else:
            print(f"  [失败] 数据目录为空")
    except Exception as e:
        print(f"  [失败] 获取数据目录: {e}")

    # ------------------------------------------------------------------
    # Case 5: 获取当前聊天窗口信息 (ChatInfo)
    # ------------------------------------------------------------------
    print("\n--- 5. 获取当前聊天窗口信息 ---")
    try:
        info = wx.ChatInfo()
        print(f"  [通过] 聊天信息:")
        for k, v in info.items():
            print(f"      {k}: {v}")
    except Exception as e:
        print(f"  [失败] 获取聊天窗口信息: {e}")

    # ------------------------------------------------------------------
    # Case 6: 获取会话列表
    # ------------------------------------------------------------------
    print("\n--- 6. 获取会话列表 ---")
    try:
        sessions = wx.GetSession()
        print(f"  [通过] 获取到 {len(sessions)} 个会话")
        for s in sessions[:10]:
            print(f"      {s.name} (未读: {s.unread_count})")
    except Exception as e:
        print(f"  [失败] 获取会话列表: {e}")

    # ------------------------------------------------------------------
    # Case 7: 验证 __repr__ 和 __str__
    # ------------------------------------------------------------------
    print("\n--- 7. 验证对象表示 ---")
    try:
        r = repr(wx)
        s = str(wx)
        print(f"  [通过] repr: {r}")
        print(f"  [通过] str: {s}")
    except Exception as e:
        print(f"  [失败] 对象表示: {e}")

    # ------------------------------------------------------------------
    # Case 8: 获取子窗口列表
    # ------------------------------------------------------------------
    print("\n--- 8. 获取所有子窗口 ---")
    try:
        subwins = wx.GetAllSubWindow()
        print(f"  [通过] 获取到 {len(subwins)} 个子窗口")
        for sw in subwins:
            print(f"      {sw.who}")
    except Exception as e:
        print(f"  [失败] 获取子窗口列表: {e}")

    separator("测试模块1 完成")


if __name__ == "__main__":
    run_all_tests()
