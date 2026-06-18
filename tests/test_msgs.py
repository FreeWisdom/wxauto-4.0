"""测试 Message 基类纯逻辑 — 不需要 WeChat 客户端。"""

import pytest
from wxauto4.msgs.base import Message, truncate_string
from wxauto4.param import WxParam


class FakeControl:
    """模拟 UIA 控件,提供 Message 初始化所需的最小属性。"""
    def __init__(self):
        self._runtimeid = (1, 2, 3)

    @property
    def runtimeid(self):
        return "".join(str(i) for i in self._runtimeid)


class FakeChatBox:
    """模拟 ChatBox,提供 Message 所需的最小接口。"""
    def __init__(self):
        self.root = self


class TestTruncateString:
    def test_short_string(self):
        assert truncate_string("hello") == "hello"

    def test_long_string(self):
        s = truncate_string("hello world this is long", 8)
        assert s == "hello wo..."


class TestMessageFields:
    def test_public_fields_empty_by_default(self):
        msg = Message()
        assert len(list(msg)) == 0

    def test_dynamic_fields(self):
        msg = Message()
        msg.content = "hello"
        msg.sender = "张三"
        msg.type = "text"
        msg.attr = "friend"
        assert list(msg) == ["content", "sender", "type", "attr"]

    def test_getitem(self):
        msg = Message()
        msg.content = "hello"
        assert msg["content"] == "hello"

    def test_getitem_missing(self):
        msg = Message()
        with pytest.raises(KeyError):
            _ = msg["nonexistent"]

    def test_get_with_default(self):
        msg = Message()
        assert msg.get("missing", "default") == "default"

    def test_contains(self):
        msg = Message()
        msg.content = "hello"
        assert "content" in msg
        assert "missing" not in msg

    def test_keys_values_items(self):
        msg = Message()
        msg.content = "hello"
        msg.sender = "张三"
        assert msg.keys() == ("content", "sender")
        assert msg.values() == ("hello", "张三")
        assert msg.items() == (("content", "hello"), ("sender", "张三"))

    def test_to_dict(self):
        msg = Message()
        msg.content = "hello"
        msg.type = "text"
        d = msg.to_dict()
        assert d == {"content": "hello", "type": "text"}

    def test_match(self):
        msg = Message()
        msg.content = "hello"
        msg.type = "text"
        msg.sender = "张三"
        assert msg.match(type="text", sender="张三")
        assert not msg.match(type="image")

    def test_match_no_match(self):
        msg = Message()
        msg.type = "text"
        assert not msg.match(type="image")

    def test_str(self):
        msg = Message()
        msg.content = "hello world"
        assert str(msg) == "hello world"

    def test_is_self(self):
        msg = Message()
        msg.attr = "self"
        assert msg.is_self
        assert not msg.is_friend
        assert not msg.is_system

    def test_is_friend(self):
        msg = Message()
        msg.attr = "friend"
        assert msg.is_friend
        assert not msg.is_self
        assert not msg.is_system

    def test_is_system(self):
        msg = Message()
        msg.attr = "system"
        assert msg.is_system
        assert not msg.is_self
        assert not msg.is_friend

    def test_eq_same_id(self):
        m1 = Message()
        m1.id = "abc"
        m2 = Message()
        m2.id = "abc"
        assert m1 == m2

    def test_eq_different_id(self):
        m1 = Message()
        m1.id = "abc"
        m2 = Message()
        m2.id = "def"
        assert m1 != m2

    def test_hash_excludes_private(self):
        msg = Message()
        msg.content = "hello"
        msg._private = "secret"
        assert "content" in msg
        assert "_private" not in msg

    def test_hash_field_controlled_by_param(self):
        msg = Message()
        msg.id = "test_id"
        msg.content = "hello"
        msg.hash = "abc123"

        original = WxParam.MESSAGE_HASH
        try:
            WxParam.MESSAGE_HASH = False
            assert "hash" not in msg
            WxParam.MESSAGE_HASH = True
            assert "hash" in msg
        finally:
            WxParam.MESSAGE_HASH = original
