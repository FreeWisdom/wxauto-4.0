"""UIAutomation 兼容层。

历史上 wxauto4 内嵌了 yinkaisheng/Python-UIAutomation-for-Windows 的完整源码
(381KB),无法接收上游 CVE/兼容性补丁。现改为依赖 PyPI 包 ``uiautomation``,
本模块做两件事:

1. 重导出 ``uiautomation`` 包的所有公开符号,让 ``from wxauto4 import uia``
   后能继续用 ``uia.Control``、``uia.ButtonControl``、``uia.WalkControl`` 等。
2. 把项目自己加的辅助函数(``RollIntoView`` / ``IsElementInWindow`` 等,PyPI
   版本没有)从 ``_extras.py`` 注入到本模块命名空间,让 ``uia.IsElementInWindow``
   继续可用。

两种原始用法保持兼容:

- ``from wxauto4 import uia`` → ``uia.Control`` / ``uia.IsElementInWindow``
- ``from wxauto4.uia import uiautomation as uia`` → ``uia.Control``(本模块把
  ``uiautomation`` 作为属性暴露)
"""

import uiautomation
from uiautomation import *  # noqa: F401,F403  重导出 PyPI 包的全部公开符号

# 项目自带的辅助函数(PyPI 版本没有),挂到本模块命名空间
from ._extras import (  # noqa: F401
    CheckElementPosition,
    GetElementPositionDescription,
    IsElementInWindow,
    RollIntoView,
)


# ---------------------------------------------------------------------------
# 兼容补丁: uiautomation PyPI 版本 API 与旧内嵌版本不完全一致。
# 这里注入缺失的方法/属性,确保现有业务代码无需修改。
# ---------------------------------------------------------------------------
import os
import tempfile


def _patch_runtimeid():
    """向 uiautomation.Control 注入 runtimeid property。"""
    if hasattr(uiautomation.Control, 'runtimeid'):
        return

    def _get_runtimeid(self):
        try:
            return ''.join(str(i) for i in self.GetRuntimeId())
        except Exception:
            return ''

    uiautomation.Control.runtimeid = property(_get_runtimeid)


def _patch_screenshot():
    """向 uiautomation.Control 注入 ScreenShot 方法。

    旧内嵌版本: control.ScreenShot() → 返回临时文件路径(str)
    PyPI 版本:   control.CaptureToImage(savePath) → 返回 bool
    """
    if hasattr(uiautomation.Control, 'ScreenShot'):
        return

    def _screenshot(self):
        fd, path = tempfile.mkstemp(suffix='.png', prefix='wxauto4_ss_')
        os.close(fd)
        try:
            ok = self.CaptureToImage(path)
            if ok:
                return path
            return ''
        except Exception:
            try:
                os.remove(path)
            except OSError:
                pass
            return ''

    uiautomation.Control.ScreenShot = _screenshot


_patch_runtimeid()
_patch_screenshot()
