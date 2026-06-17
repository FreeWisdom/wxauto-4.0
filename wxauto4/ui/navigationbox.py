from wxauto4 import uia
from wxauto4.param import (
    WxParam,
    WxResponse,
)
from wxauto4.logger import wxlog


class NavigationBox:
    def __init__(self, control, parent):
        self.control: uia.Control = control
        self.root = parent.root
        self.parent = parent
        # init 改为容错:某个按钮折叠在「更多」下时取不到,不应让整个 NavigationBox 不可用。
        # switch_* 方法改为延迟查找,实际点击时再尝试取控件并等待。
        self._icons: dict[str, str] = {}
        self.init()
        # 第一次 init 时记录所有控件名到 _icons,但不强求每个都成功
        self._icons = {
            'chat': self._lang('微信'),
            'contact': self._lang('通讯录'),
            'favorites': self._lang('收藏'),
            'files': self._lang('聊天文件'),
            'moments': self._lang('朋友圈'),
            'browser': self._lang('搜一搜'),
            'video': self._lang('视频号'),
            'stories': self._lang('看一看'),
            'mini_program': self._lang('小程序面板'),
            'phone': self._lang('手机'),
            'settings': self._lang('更多'),
        }

    def init(self):
        """尽力初始化所有侧边栏按钮控件,单个失败不抛异常。"""
        targets = {
            'chat_icon': '微信',
            'contact_icon': '通讯录',
            'favorites_icon': '收藏',
            'files_icon': '聊天文件',
            'moments_icon': '朋友圈',
            'browser_icon': '搜一搜',
            'video_icon': '视频号',
            'stories_icon': '看一看',
            'mini_program_icon': '小程序面板',
            'phone_icon': '手机',
            'settings_icon': '更多',
        }
        for attr, label in targets.items():
            try:
                ctrl = self.control.ButtonControl(Name=self._lang(label))
                setattr(self, attr, ctrl)
            except Exception as e:
                wxlog.debug(f'初始化侧边栏按钮 [{label}] 失败,切换时会重试: {e}')
                setattr(self, attr, None)

    def _lang(self, text):
        return text

    def _switch(self, attr: str, label_cn: str) -> WxResponse:
        """统一的切换逻辑:延迟查找控件,带 Exists 等待,点击后短暂停顿。

        微信 4.x 中部分按钮(聊天文件、看一看)常折叠在「更多」下,
        init 阶段不一定能立即取到。本方法在点击前重新尝试查找并等待控件出现。
        """
        ctrl = getattr(self, attr, None)
        if ctrl is None or not self._safe_exists(ctrl, 0):
            # 重新查找,给微信 UI 一点反应时间
            try:
                ctrl = self.control.ButtonControl(Name=self._lang(label_cn))
                if self._safe_exists(ctrl, WxParam.SEARCH_CHAT_TIMEOUT):
                    setattr(self, attr, ctrl)
                else:
                    msg = f'未找到侧边栏按钮: {label_cn}'
                    wxlog.debug(msg)
                    return WxResponse.failure(msg)
            except Exception as e:
                msg = f'查找侧边栏按钮 [{label_cn}] 异常: {e}'
                wxlog.debug(msg)
                return WxResponse.failure(msg)

        try:
            ctrl.Click()
            # 点击后短暂停顿,等待目标页面渲染
            import time
            time.sleep(0.3)
            return WxResponse.success(f'已切换到 {label_cn}')
        except Exception as e:
            msg = f'点击侧边栏按钮 [{label_cn}] 失败: {e}'
            wxlog.debug(msg)
            return WxResponse.failure(msg)

    @staticmethod
    def _safe_exists(ctrl, wait: float) -> bool:
        try:
            return bool(ctrl.Exists(wait))
        except Exception:
            return False

    def switch_to_chat_page(self):
        return self._switch('chat_icon', '微信')

    def switch_to_contact_page(self):
        return self._switch('contact_icon', '通讯录')

    def switch_to_favorites_page(self):
        return self._switch('favorites_icon', '收藏')

    def switch_to_files_page(self):
        return self._switch('files_icon', '聊天文件')

    def switch_to_browser_page(self):
        return self._switch('browser_icon', '搜一搜')

    def switch_to_moments_page(self):
        return self._switch('moments_icon', '朋友圈')

    def switch_to_video_page(self):
        return self._switch('video_icon', '视频号')

    def switch_to_stories_page(self):
        return self._switch('stories_icon', '看一看')

    def switch_to_mini_program_page(self):
        return self._switch('mini_program_icon', '小程序面板')

    def switch_to_phone_page(self):
        return self._switch('phone_icon', '手机')

    def switch_to_settings_page(self):
        return self._switch('settings_icon', '更多')
