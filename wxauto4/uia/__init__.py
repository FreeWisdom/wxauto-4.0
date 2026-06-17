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
