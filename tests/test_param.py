"""测试 param.py — WxResponse 和 WxParam 纯逻辑。"""

import pytest
from wxauto4.param import WxResponse, WxParam


class TestWxResponse:
    def test_success(self):
        resp = WxResponse.success("完成")
        assert resp.is_success
        assert bool(resp)
        assert resp["status"] == "成功"
        assert resp["message"] == "完成"

    def test_failure(self):
        resp = WxResponse.failure("找不到")
        assert not resp.is_success
        assert not bool(resp)
        assert resp["status"] == "失败"

    def test_error(self):
        resp = WxResponse.error("崩溃")
        assert not resp.is_success
        assert resp["status"] == "错误"

    def test_to_dict(self):
        resp = WxResponse.success("ok", {"key": "val"})
        d = resp.to_dict()
        assert d == {"status": "成功", "message": "ok", "data": {"key": "val"}}

    def test_dict_access(self):
        resp = WxResponse.failure("bad")
        assert resp["status"] == "失败"
        assert resp["message"] == "bad"
        assert resp["data"] is None

    def test_str_repr(self):
        resp = WxResponse.success("hi")
        s = str(resp)
        assert "成功" in s
        assert "hi" in s


class TestWxParam:
    def test_language_default(self):
        assert WxParam.LANGUAGE == "cn"

    def test_message_hash_default(self):
        assert WxParam.MESSAGE_HASH is False

    def test_enable_sender_ocr_default(self):
        assert WxParam.ENABLE_SENDER_OCR is True

    def test_listen_interval_default(self):
        assert WxParam.LISTEN_INTERVAL == 1
