---
name: Bug 报告
about: 报告 wxauto4 的 bug 或异常行为
title: "[Bug] "
labels: bug
---

## 环境信息

- wxauto4 版本：`pip show wxauto4` 的 Version（或 git commit）
- 微信版本：（例如 4.0.5.x，从微信「关于」对话框查看）
- Python 版本：`python --version`
- 操作系统：（例如 Windows 11 23H2）

## 复现步骤

```python
# 最小可复现代码
from wxauto4 import WeChat
wx = WeChat()
...
```

## 预期行为

<!-- 你期望发生什么 -->

## 实际行为

<!-- 实际发生了什么 -->

## debug=True 日志片段

请使用 `WeChat(debug=True)` 重新运行，把相关日志片段贴在这里（可裁剪到关键部分）：

```
（在此粘贴日志）
```

## 补充信息

<!-- 截图、堆栈、相关 Issue 链接等 -->
