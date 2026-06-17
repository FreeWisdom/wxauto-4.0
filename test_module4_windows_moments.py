"""
测试模块4：窗口管理与朋友圈
验证 GetSession、ChatWith、GetSubWindow、GetAllSubWindow、
侧边栏导航切换、朋友圈读取/点赞/评论。

用法：
    python test_module4_windows_moments.py

前提：已登录微信 4.0.5 客户端
"""

import sys, time, traceback

try:
    from wxauto4 import WeChat, WxResponse
except ImportError:
    print("[错误] 未安装 wxauto4，请先执行: pip install wxauto4")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
TEST_TARGET = "每日饮食打卡🍽️"     # 测试用的聊天对象
NAVIGATE_INTERVAL = 0.3           # 导航切换间隔（秒）
# ---------------------------------------------------------------------------


def separator(title=""):
    print()
    print("=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def run_all_tests():
    separator("测试模块4：窗口管理与朋友圈")

    # 初始化
    print("\n--- 初始化 WeChat ---")
    try:
        wx = WeChat()
        print(f"  [通过] 初始化成功，当前账号: {wx.nickname}")
    except Exception as e:
        print(f"  [失败] 初始化失败: {e}")
        sys.exit(1)

    # ======================================================================
    # Part A: 窗口管理
    # ======================================================================
    separator("Part A: 窗口管理")

    # ------------------------------------------------------------------
    # A1: GetSession - 获取会话列表
    # ------------------------------------------------------------------
    print("\n--- A1. GetSession: 获取会话列表 ---")
    try:
        sessions = wx.GetSession()
        print(f"  [通过] 获取到 {len(sessions)} 个会话")
        for i, s in enumerate(sessions[:15]):
            unread = f" 未读:{s.unread_count}" if s.unread_count else ""
            print(f"      {i+1}. {s.name}{unread}")

        # 检查目标是否存在
        target_found = any(TEST_TARGET in s.name for s in sessions)
        if target_found:
            print(f"  [通过] 找到测试目标 '{TEST_TARGET}'")
        else:
            print(f"  [提示] 未在会话列表中找到 '{TEST_TARGET}'")
    except Exception as e:
        print(f"  [失败] 获取会话列表异常: {e}")
        traceback.print_exc()

    # ------------------------------------------------------------------
    # A2: ChatWith - 切换聊天窗口
    # ------------------------------------------------------------------
    print(f"\n--- A2. ChatWith: 切换到 {TEST_TARGET} ---")
    try:
        result = wx.ChatWith(TEST_TARGET)
        if isinstance(result, WxResponse):
            if result.is_success:
                print(f"  [通过] 切换成功")
            else:
                print(f"  [失败] 切换失败: {result.get('message')}")
                print(f"  [提示] 尝试 force=True 切换...")
                result2 = wx.ChatWith(TEST_TARGET, force=True, force_wait=1.0)
                if isinstance(result2, WxResponse) and result2.is_success:
                    print(f"  [通过] 强制切换成功")
        else:
            nickname = result or TEST_TARGET
            print(f"  [通过] 切换到: {nickname}")
    except Exception as e:
        print(f"  [失败] 切换聊天窗口异常: {e}")

    # ------------------------------------------------------------------
    # A3: GetAllSubWindow - 获取所有子窗口
    # ------------------------------------------------------------------
    print("\n--- A3. GetAllSubWindow: 获取所有子窗口 ---")
    try:
        subwins = wx.GetAllSubWindow()
        print(f"  [通过] 获取到 {len(subwins)} 个子窗口")
        for sw in subwins:
            info = {}
            try:
                info = sw.ChatInfo()
            except Exception:
                pass
            chat_type = info.get('chat_type', '?')
            chat_name = info.get('chat_name', sw.who)
            print(f"      [{chat_type}] {chat_name}")
    except Exception as e:
        print(f"  [失败] 获取子窗口异常: {e}")

    # ------------------------------------------------------------------
    # A4: GetSubWindow - 获取特定子窗口
    # ------------------------------------------------------------------
    print(f"\n--- A4. GetSubWindow: 获取 {TEST_TARGET} 子窗口 ---")
    try:
        sub_win = wx.GetSubWindow(TEST_TARGET)
        if sub_win:
            print(f"  [通过] 获取到子窗口: {sub_win.who}")
            info = sub_win.ChatInfo()
            print(f"      聊天类型: {info.get('chat_type', '?')}")
            print(f"      聊天名称: {info.get('chat_name', '?')}")

            # 测试子窗口 Show
            sub_win.Show()
            print(f"  [通过] 子窗口 Show 完成")
        else:
            print(f"  [提示] 未找到 {TEST_TARGET} 的子窗口（可能未以独立窗口打开）")
    except Exception as e:
        print(f"  [失败] 获取子窗口异常: {e}")

    # ======================================================================
    # Part B: 侧边栏导航切换
    # ======================================================================
    separator("Part B: 侧边栏导航切换")

    nav_tests = [
        ("SwitchToChat", "聊天页", wx.SwitchToChat),
        ("SwitchToContact", "联系人页", wx.SwitchToContact),
        ("SwitchToFiles", "聊天文件页", wx.SwitchToFiles),
        ("SwitchToFavorites", "收藏页", wx.SwitchToFavorites),
        ("SwitchToMoments", "朋友圈页", wx.SwitchToMoments),
        ("SwitchToBrowser", "搜一搜页", wx.SwitchToBrowser),
        ("SwitchToVideo", "视频号页", wx.SwitchToVideo),
        ("SwitchToStories", "看一看页", wx.SwitchToStories),
        ("SwitchToMiniProgram", "小程序面板页", wx.SwitchToMiniProgram),
        ("SwitchToPhone", "手机页", wx.SwitchToPhone),
        ("SwitchToSettings", "更多设置页", wx.SwitchToSettings),
    ]

    print("\n  开始依次测试侧边栏导航切换...")
    passed = 0
    failed = 0

    for func_name, page_name, func in nav_tests:
        print(f"\n--- B{pnc+1 if (pnc:=len([passed+failed])//1) else ''}. {func_name}: 切换到{page_name} ---")
        try:
            func()
            time.sleep(NAVIGATE_INTERVAL)
            print(f"  [通过] 切换成功")
            passed += 1
        except AttributeError:
            print(f"  [跳过] 方法不存在")
            continue
        except Exception as e:
            print(f"  [提示] 切换异常: {e}")
            failed += 1

    print(f"\n  导航切换结果: {passed} 通过, {failed} 失败, {len(nav_tests)-passed-failed} 跳过")

    # ======================================================================
    # Part C: 朋友圈
    # ======================================================================
    separator("Part C: 朋友圈功能")

    try:
        from wxauto4 import Moment
    except ImportError:
        Moment = None

    if not Moment:
        print("  [跳过] 无法导入 Moment")
    else:
        # ------------------------------------------------------------------
        # C1: GetMoments - 读取朋友圈
        # ------------------------------------------------------------------
        print("\n--- C1. GetMoments: 读取朋友圈动态 ---")
        try:
            # 先切换到朋友圈
            wx.SwitchToMoments()
            time.sleep(0.5)

            moment = wx.Moment
            items = moment.GetMoments(refresh=True)
            print(f"  [通过] 读取到 {len(items)} 条朋友圈动态")

            for idx, item in enumerate(items[:5], 1):
                print(f"\n     --- 第 {idx} 条 ---")
                print(f"     发布者: {item.publisher}")
                print(f"     时间: {item.timestamp}")
                if item.text:
                    text_preview = item.text[:60].replace('\n', ' ')
                    print(f"     内容: {text_preview}...")
                if item.like_users:
                    print(f"     点赞: {', '.join(item.like_users[:5])}")
                if item.comment_list:
                    for c in item.comment_list[:3]:
                        reply = f" 回复 {c.reply_to}" if c.reply_to else ""
                        print(f"     评论 [{c.author}{reply}]: {c.content[:40]}")
                if item.image_count:
                    print(f"     图片: {item.image_count} 张")
                if item.is_advertisement:
                    print(f"     [广告]")

        except Exception as e:
            print(f"  [失败] 读取朋友圈异常: {e}")
            traceback.print_exc()

        # ------------------------------------------------------------------
        # C2: FindMomentByPublisher - 查找指定发布者的动态
        # ------------------------------------------------------------------
        print("\n--- C2. FindMomentByPublisher: 查找指定发布者 ---")
        try:
            items = wx.Moment.GetMoments(refresh=False)
            if items:
                first_publisher = items[0].publisher
                found = wx.Moment.FindMomentByPublisher(first_publisher)
                if found:
                    print(f"  [通过] 找到了 {first_publisher} 的发布动态")
                else:
                    print(f"  [提示] 未找到 {first_publisher} 的动态")
            else:
                print(f"  [跳过] 没有朋友圈动态可查")
        except Exception as e:
            print(f"  [提示] 查找发布者异常: {e}")

        # ------------------------------------------------------------------
        # C3: Like - 朋友圈点赞 (谨慎：仅打印操作，不实际执行)
        # ------------------------------------------------------------------
        print("\n--- C3. Like: 朋友圈点赞 ---")
        print("  [跳过] 点赞操作会修改真实数据，如需测试请取消下面注释")
        # 如需测试点赞，取消注释以下代码：
        # try:
        #     items = wx.Moment.GetMoments(refresh=False)
        #     if items:
        #         result = wx.Moment.Like(items[0], cancel=False)
        #         print(f"  [结果] 点赞: {result}")
        # except Exception as e:
        #     print(f"  [失败] 点赞异常: {e}")

        # ------------------------------------------------------------------
        # C4: Comment - 朋友圈评论 (谨慎：仅打印操作，不实际执行)
        # ------------------------------------------------------------------
        print("\n--- C4. Comment: 朋友圈评论 ---")
        print("  [跳过] 评论操作会修改真实数据，如需测试请取消下面注释")
        # 如需测试评论，请先修改 TEST_COMMENT 并取消注释：
        # TEST_COMMENT = "测试评论 wxauto4"
        # try:
        #     items = wx.Moment.GetMoments(refresh=False)
        #     if items:
        #         result = wx.Moment.Comment(items[0], TEST_COMMENT)
        #         print(f"  [结果] 评论: {result}")
        # except Exception as e:
        #     print(f"  [失败] 评论异常: {e}")

        # ------------------------------------------------------------------
        # C5: MomentItem 数据结构验证
        # ------------------------------------------------------------------
        print("\n--- C5. MomentItem 数据结构完整性 ---")
        try:
            items = wx.Moment.GetMoments(refresh=False)
            if items:
                item = items[0]
                checks = {
                    "publisher": item.publisher,
                    "timestamp": item.timestamp,
                    "text": item.text,
                    "like_users": item.like_users,
                    "comment_list": item.comment_list,
                    "image_count": item.image_count,
                    "is_advertisement": item.is_advertisement,
                }
                all_ok = True
                for attr, val in checks.items():
                    ok = val is not None
                    if not ok:
                        print(f"  [警告] {attr} 为 None")
                        all_ok = False
                    else:
                        val_str = str(val)[:50]
                        print(f"  [通过] {attr}: {val_str}")
                if all_ok:
                    print(f"  [通过] 所有关键属性均非空")
            else:
                print(f"  [跳过] 没有朋友圈动态可验证")
        except Exception as e:
            print(f"  [失败] 数据结构验证异常: {e}")

    # ------------------------------------------------------------------
    # 收尾：切换回聊天页
    # ------------------------------------------------------------------
    print("\n--- 收尾: 切换回聊天页 ---")
    try:
        wx.SwitchToChat()
        print(f"  [通过] 已切回聊天页")
    except Exception:
        pass

    separator("测试模块4 完成")


if __name__ == "__main__":
    run_all_tests()
