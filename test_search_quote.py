"""搜索定位 + 引用回复 — 参考实现"""
import time, win32api, win32con, win32gui
from wxauto4 import WeChat, uia
from wxauto4.utils.win32 import SetClipboardText


def search_and_quote(wx, keyword, reply_text):
    session_box = wx._api._session_api.control

    # 1. 全局搜索
    sb = session_box.EditControl(Name='搜索', ClassName='mmui::XValidatorTextEdit')
    sb.Click()
    time.sleep(0.3)
    SetClipboardText(keyword)
    sb.SendKeys('{Ctrl}v')
    time.sleep(0.8)

    # 2. 点 SearchContentPopover 结果 → 打开 SearchMsgWindow
    popover = wx._api.control.WindowControl(ClassName='mmui::SearchContentPopover')
    for r in popover.ListControl(ClassName='mmui::XTableView').GetChildren():
        if keyword in r.Name:
            r.Click()
            break
    time.sleep(2.0)

    # 3. SearchMsgWindow: 展开条目 → 点击内部消息右侧浮现的"定位到聊天位置"
    sw = uia.GetRootControl().WindowControl(
        Name='搜索聊天记录', ClassName='mmui::SearchMsgWindow')

    def find(ctrl, kw):
        try:
            if kw in (ctrl.Name or ''): return ctrl
            for ch in ctrl.GetChildren():
                r = find(ch, kw)
                if r: return r
        except: pass
        return None

    outer = find(sw, keyword)
    if outer:
        outer.Click()  # 展开, 显示内部 ListItemControl
        time.sleep(0.5)

    inner = find(sw, keyword)
    if not inner or inner == outer:
        enter_btn = find(sw, '进入聊天')
        if enter_btn:
            inner = find(enter_btn, keyword)

    if inner and inner.ControlTypeName == 'ListItemControl' and inner != outer:
        r = inner.BoundingRectangle
        # TODO: 精确定位"定位到聊天位置"按钮
        # 当前使用 95%宽 70%高 — 在副屏大窗口下成功过, 主屏小窗口下未稳定
        hx = r.left + int(r.width() * 0.95)
        hy = r.top + int(r.height() * 0.70)
        win32api.SetCursorPos((hx, hy))
        time.sleep(1.5)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, hx, hy, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, hx, hy, 0, 0)
        time.sleep(1.0)

    # 关闭搜索窗口
    try: sw.ButtonControl(Name='关闭').Click()
    except: pass
    time.sleep(0.5)

    # 4. 引用回复
    msgs = wx.GetAllMessage()
    target = next((m for m in msgs if keyword in str(m.content)), None)
    if not target:
        print(f'消息不在视图 ({len(msgs)}条)')
        return
    print(f'目标: [{target.sender}] {target.content.strip()}')
    resp = target.quote(reply_text)
    print(f'结果: {resp}')


if __name__ == '__main__':
    wx = WeChat()
    # 确保微信在主屏(正坐标), 副屏负坐标下 XMenu 不可用
    hwnd = wx._api.HWND
    win32gui.SetWindowPos(hwnd, 0, 100, 30, 1260, 950,
        win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
    time.sleep(0.5)

    search_and_quote(wx, '晚上吃点什么大家', '收到，晚上见')
