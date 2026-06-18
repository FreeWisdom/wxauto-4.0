"""测试 exceptions.py — 异常类层次。"""

import pytest
from wxauto4.exceptions import (
    WxautoError,
    NetWorkError,
    WxautoUINotFoundError,
    WxautoNoteLoadTimeoutError,
)


class TestExceptions:
    def test_wxauto_error_base(self):
        e = WxautoError("base")
        assert str(e) == "base"
        assert isinstance(e, Exception)

    def test_network_error(self):
        e = NetWorkError("no network")
        assert isinstance(e, WxautoError)
        assert isinstance(e, Exception)

    def test_ui_not_found_error(self):
        e = WxautoUINotFoundError("control missing")
        assert isinstance(e, WxautoError)

    def test_note_load_timeout(self):
        e = WxautoNoteLoadTimeoutError("timeout")
        assert isinstance(e, WxautoError)

    def test_catch_by_base(self):
        try:
            raise NetWorkError("test")
        except WxautoError:
            pass

    def test_catch_by_exception(self):
        try:
            raise WxautoUINotFoundError("missing")
        except Exception:
            pass
