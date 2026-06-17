# Session 会话

会话列表与单会话操作定义在 [wxauto4/ui/sessionbox.py](../../wxauto4/ui/sessionbox.py)。

## SessionBox 类

`wx.SessionBox` 属性返回此实例。

### `get_session() -> List[SessionElement]`

返回当前可见的会话列表。

### `search(keywords, force=False, force_wait=0.5)`

在搜索框输入关键字并返回搜索结果元素列表。

### `switch_chat(keywords, exact=True, force=False, force_wait=0.5)`

根据搜索结果点击切换聊天。参数与 `WeChat.ChatWith` 一致。

### `open_separate_window(name)`

把指定会话打开为独立窗口。

### 滚动

| 方法 | 说明 |
|---|---|
| `roll_up(n=5)` | 向上滚动 n 次 |
| `roll_down(n=5)` | 向下滚动 n 次 |
| `go_top()` | 回到列表顶部 |
| `go_bottom()` | 跳到列表底部 |

## SessionElement 类

`wx.GetSession()` 与 `SessionBox.get_session()` 返回的列表元素。

### `@property`

| 属性 | 类型 | 说明 |
|---|---|---|
| `name` | str | 会话名称 |
| `texts` | List[str] | 会话控件中的文本行（含预览） |
| `unread_count` | int | 未读消息数 |

### 鼠标交互

| 方法 | 说明 |
|---|---|
| `click()` | 单击 |
| `double_click()` | 双击 |
| `right_click()` | 右键单击 |
| `roll_into_view()` | 滚动到可见 |

### 右键菜单

#### `select_option(option, wait=0.3)`

右键菜单选择指定项。

#### `select_menu_option(option_key, wait=0.3)`

按语言配置 key 选择菜单项（用于多语言场景）。

### 快捷动作（封装右键菜单）

| 方法 | 说明 |
|---|---|
| `pin()` | 置顶聊天 |
| `unpin()` | 取消置顶 |
| `mark_unread()` | 标记为未读 |
| `toggle_mute()` | 切换消息免打扰 |
| `open_in_separate_window()` | 在独立窗口中打开 |
| `hide()` | 不显示聊天 |
| `delete()` | 删除聊天 |

> **注意**：`hide` / `delete` 是破坏性操作，请确认后使用。

## SearchResultElement 类

搜索结果元素，由 `SessionBox.search()` 返回。

### `@property` / 方法

| 成员 | 说明 |
|---|---|
| `type` | 结果类型标识 |
| `get_all_text()` | 拆分后的文本行列表 |
| `click()` | 滚动至可见并单击 |
| `close()` | 发送 Esc 关闭搜索结果 |

## 完整示例

```python
wx = WeChat()

# 列出所有会话与未读数
for s in wx.GetSession():
    print(f'{s.name} ({s.unread_count} 未读)')

# 找到张三并标记未读
for s in wx.GetSession():
    if s.name == '张三':
        s.mark_unread()
        s.pin()

# 关闭一些会话独立窗口
wx.SessionBox.go_top()
```

## 下一步

- WeChat 主类：[WeChat API](wechat.md)
- 指南：[消息收发](../guide/messaging.md)
