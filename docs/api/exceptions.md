# 异常

wxauto4 的所有异常都继承自 `WxautoError`，定义在 [wxauto4/exceptions.py](../../wxauto4/exceptions.py)。

## 继承关系

```
Exception
  └─ WxautoError (基类，@dataclass)
       ├─ NetWorkError
       ├─ WxautoUINotFoundError
       └─ WxautoNoteLoadTimeoutError
```

## 异常类

### `WxautoError(message='', detail='', default_message='')`

基础异常类型，所有项目异常的父类。

| 字段 | 说明 |
|---|---|
| `message` | 错误信息（缺省时用 `default_message`） |
| `detail` | 附加上下文（便于日志友好打印） |
| `default_message` | 子类提供的默认信息 |

通过 `e.message` / `e.detail` 访问，`str(e)` 返回 `message`。

### `NetWorkError`

`default_message = '微信无法连接到网络'`

触发场景：网络请求相关异常。

### `WxautoUINotFoundError`

`default_message = '未找到目标 UI 控件'`

触发场景：无法定位到指定 UI 控件（最常见）。常见原因：

- 微信版本不是 4.0.5
- 微信未启动或未登录
- 目标聊天/控件不存在
- 微信界面处于异常状态（如弹窗遮挡）

### `WxautoNoteLoadTimeoutError`

`default_message = '微信笔记加载超时'`

触发场景：微信笔记加载超过 `WxParam.NOTE_LOAD_TIMEOUT`（默认 30 秒）。

## 异常处理

### 按类型区分

```python
from wxauto4 import (
    WeChat,
    WxautoError,
    WxautoUINotFoundError,
    NetWorkError,
)

wx = WeChat()
try:
    wx.ChatWith('不存在的联系人')
    wx.SendMsg('hi')
except WxautoUINotFoundError as e:
    print(f'控件找不到: {e.message}')
    print(f'详情: {e.detail}')
except NetWorkError as e:
    print(f'网络异常: {e}')
except WxautoError as e:
    # 兜底：所有项目异常
    print(f'其他错误: {e.message}')
```

### 用父类捕获所有项目异常

```python
try:
    wx.SendMsg('hi', '张三')
    wx.SendFiles(r'C:\file.txt')
except WxautoError as e:
    print(f'操作失败: {e}')
    # 可以记录 detail 用于调试
    if e.detail:
        print(f'详情: {e.detail}')
```

## 调试技巧

### 启用 debug 日志

```python
wx = WeChat(debug=True)
```

启用后会输出详细的 UIA 控件查找日志，便于定位 `WxautoUINotFoundError` 的根因。

### 配合 try/except 收集

如果做大批量自动化（如群发），建议每条操作独立捕获，避免单条失败中断整体流程：

```python
for name, msg in targets:
    try:
        wx.SendMsg(msg, name)
    except WxautoError as e:
        print(f'跳过 {name}: {e.message}')
        continue
```

## 与 WxResponse 的关系

- **异常**：UIA 控件查找失败、网络异常、加载超时等**底层错误**
- **WxResponse.failure/error**：业务级失败（如目标聊天找不到但已优雅处理）

大部分公开方法（`SendMsg` / `SendFiles` / `Like` / `Comment`）**不会**抛异常，而是返回 `WxResponse`。异常主要出现在 `WeChat()` 初始化、`ChatWith` 切换、监听器内部等更底层场景。

## 下一步

- 响应类型：[WxResponse](response.md)
- WeChat API：[WeChat](wechat.md)
