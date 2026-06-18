from .base import (
    BaseMessage,
    HumanMessage
)
from wxauto4 import uia
from wxauto4.param import (
    WxParam,
    WxResponse,
    PROJECT_NAME
)
from wxauto4.utils.tools import extract_sender_from_control

from typing import (
    Dict,
    List,
    Any,
    TYPE_CHECKING
)
if TYPE_CHECKING:
    from wxauto4.ui.chatbox import ChatBox

class SystemMessage(BaseMessage):
    attr = 'system'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox",
            additonal_attr: Dict[str, Any]={}
        ):
        super().__init__(control, parent, additonal_attr)
        self.sender = 'system'
        self.sender_remark = 'system'

class FriendMessage(HumanMessage):
    attr = 'friend'

    def __init__(
            self,
            control: uia.Control,
            parent: "ChatBox",
            additonal_attr: Dict[str, Any]={}
        ):
        super().__init__(control, parent, additonal_attr)
        if not hasattr(self, 'sender') or not self.sender:
            self.sender, self.sender_remark = self._resolve_sender()

    def _click(self, x, y, right=False):
        self.roll_into_view()
        if right:
            h = self.control.BoundingRectangle.height()
            self.control.RightClick(
                x=WxParam.DEFAULT_MESSAGE_XBIAS + 50,
                y=int(h * 0.6),
                ratioX=0, ratioY=0,
            )
        else:
            self.control.Click(ratioX=0, ratioY=0)

    @property
    def _bias(self):
        return WxParam.DEFAULT_MESSAGE_XBIAS

    def _resolve_sender(self) -> tuple:
        """解析发送者,返回 (sender, sender_remark)。"""
        try:
            chat_info = self.parent.parent._chat_api.get_info()
        except Exception:
            chat_info = {}
        chat_name = chat_info.get('chat_name', '')
        chat_type = chat_info.get('chat_type', 'friend')
        chat_remark = chat_info.get('chat_remark', '')

        # 群聊:子树查找优先,OCR 由 extract_sender_from_control 根据
        # WxParam.ENABLE_SENDER_OCR 自动决定是否触发
        if chat_type == 'group':
            sender = extract_sender_from_control(self.control, self.content)
            if sender:
                return sender, sender
            # 连续消息通常不重复显示昵称,此时回退到群名作为兜底
            if chat_name:
                return chat_name, chat_name
            return 'friend', 'friend'

        # 单聊:sender 就是对方
        if chat_name:
            return chat_name, chat_remark or chat_name
        return 'friend', 'friend'


class SelfMessage(HumanMessage):
    attr = 'self'

    def __init__(
            self,
            control: uia.Control,
            parent: "ChatBox",
            additonal_attr: Dict[str, Any]={}
        ):
        super().__init__(control, parent, additonal_attr)
        if not hasattr(self, 'sender') or not self.sender:
            self.sender, self.sender_remark = self._resolve_sender()

    def _click(self, x, y, right=False):
        self.roll_into_view()
        if right:
            h = self.control.BoundingRectangle.height()
            self.control.RightClick(
                x=-(WxParam.DEFAULT_MESSAGE_XBIAS + 30),
                y=int(h * 0.6),
                ratioX=1, ratioY=0,
            )
        else:
            self.control.Click(x=x, y=y, ratioX=1, ratioY=0)

    @property
    def _bias(self):
        return -WxParam.DEFAULT_MESSAGE_XBIAS

    def _resolve_sender(self) -> tuple:
        """自己发的消息:sender 取当前登录账号昵称。"""
        try:
            owner = self.parent.parent
            nickname = getattr(owner, 'nickname', None) or getattr(owner, 'who', None)
            if nickname:
                return nickname, nickname
        except Exception:
            from wxauto4.logger import wxlog
            wxlog.debug("SelfMessage 获取 owner nickname 失败", exc_info=True)
        return '我', '我'