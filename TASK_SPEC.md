# 任务：实现「全局搜索定位消息 + 引用回复」功能

## 背景

wxauto4 是一个基于 Windows UIAutomation 的微信 4.0.5 自动化库。当前库已有消息发送/读取/监听/引用回复等能力，但缺少"通过搜索定位到历史消息"的功能。

## 需求

实现 `search_and_quote(wx, keyword, reply_text)` 函数：
1. 在微信顶部全局搜索框搜索 keyword
2. 点击搜索结果，打开"搜索聊天记录"窗口
3. 在该窗口中点击消息条目右侧浮现的"定位到聊天位置"按钮
4. 关闭搜索窗口后，目标消息出现在聊天视图
5. 右键引用该消息，发送 reply_text

## 已完成的修复（可直接使用）

以下修复已应用在当前代码中：

### 1. `wxauto4/uia/__init__.py` — UIA 兼容补丁
- 注入 `Control.runtimeid` property（PyPI uiautomation 2.0.29 无此属性）
- 注入 `Control.ScreenShot()` 方法（旧 API，新 API 是 `CaptureToImage(path)`）

### 2. `wxauto4/msgs/mattr.py` — 右击坐标修复
- FriendMessage 右击：`x = DEFAULT_MESSAGE_XBIAS + 50, y = height * 0.6, ratioX=0`（点击气泡文字区而非头像）
- SelfMessage 右击：`x = -(DEFAULT_MESSAGE_XBIAS + 30), y = height * 0.6, ratioX=1`

### 3. `wxauto4/utils/tools.py` — delete_update_files 容错
- 添加 PermissionError/OSError 捕获

### 4. 其他清理
- 删除 `wxauto4/msgs/parse.py`（死代码，依赖未声明的 pycryptodome）
- `msgs/base.py` 中的 Menu/SelectContactWnd 改为延迟导入
- `utils/__init__.py` 和 `msgs/__init__.py` 改为显式导出
- `wx.py` 中 `print()` → `wxlog`，`os.system()` → `subprocess.run()`

## UIA 控件路径

### 全局搜索框
```
WeChatMainWnd
  └── ChatMasterView
        └── EditControl: Name="搜索" ClassName="mmui::XValidatorTextEdit"
```
通过 `wx._api._session_api.control.EditControl(Name='搜索', ClassName='mmui::XValidatorTextEdit')` 访问。

### 搜索结果弹窗
```
WindowControl: ClassName="mmui::SearchContentPopover"
  └── ListControl: ClassName="mmui::XTableView"
        └── ListItemControl: 结果条目, 格式为 "群名 消息内容"  (ClassName="mmui::SearchContentCellView")
```

### 搜索聊天记录窗口
点击搜索结果后打开：
```
WindowControl: Name="搜索聊天记录" ClassName="mmui::SearchMsgWindow"
  └── PaneControl
        ├── TextControl: "搜索聊天记录"
        ├── ButtonControl: "清空"
        ├── EditControl: "搜索"
        ├── ListItemControl: "群名 消息内容"  ← 初始折叠状态
        │     └── (点击展开后)
        │     ├── TextControl: "N条与'xxx'的聊天记录"
        │     ├── ButtonControl: "进入聊天"
        │     │     └── ListItemControl: "HH:MM 消息内容"  ← 内部消息条目
        │     └── ListControl: ClassName="mmui::RecyclerListView"
        │           └── ListItemControl: 具体的消息项
        ├── ButtonControl: "最小化"
        ├── ButtonControl: "最大化"
        └── ButtonControl: "关闭"
```

## 已验证的交互流程

```python
# 1. 搜索
sb = session_box.EditControl(Name='搜索', ClassName='mmui::XValidatorTextEdit')
sb.Click()
SetClipboardText(keyword)
sb.SendKeys('{Ctrl}v')
time.sleep(0.8)

# 2. 点击搜索结果
popover = wx._api.control.WindowControl(ClassName='mmui::SearchContentPopover')
for r in popover.ListControl(ClassName='mmui::XTableView').GetChildren():
    if keyword in r.Name:
        r.Click()  # 打开 SearchMsgWindow
        break
time.sleep(2.0)

# 3. 展开 SearchMsgWindow 中的条目
sw = uia.GetRootControl().WindowControl(Name='搜索聊天记录', ClassName='mmui::SearchMsgWindow')
outer = find_ctrl(sw, keyword)  # 递归查找
outer.Click()  # 展开, 显示内部结构
time.sleep(0.5)
```

## 待解决的关键问题

### "定位到聊天位置" 按钮点击

这是整个流程中唯一未稳定跑通的一步。

**现象：**
- 在 SearchMsgWindow 内部消息条目右侧悬浮时，会浮现一个"定位到聊天位置"的按钮/提示
- 该按钮**不是 UIA 控件**（`TextControl "定位到聊天位置"` 未出现在 UIA 树中）
- 已经试过的点击位置（内部消息 ListItemControl 的相对坐标）：
  - `(r.left + r.width * 0.95, r.top + r.height * 0.70)` — 在副屏大窗口下成功过一次
  - 在主屏小窗口下，70%/80% y 均未触发

**已确认的线索：**
1. 点击目标必须是展开后的**内部** `ListItemControl`（如 `"15:10 晚上吃点什么大家"`），不是外层的群名条目
2. x 位置应该在消息条目的右侧（95% 宽度）
3. y 位置需要精确定位到浮现的"定位到聊天位置"文字上
4. 微信窗口需要在主屏（正坐标），副屏负坐标下 XMenu 不可用
5. `ctrl.Click()` 不起作用，必须用 Win32 `mouse_event` 绝对坐标

**建议的解决思路：**
1. **截图+OCR**：悬浮后截取内部消息条目区域，OCR 识别"定位到聊天位置"位置，计算点击坐标
2. **固定偏移**：反复调试 x, y 百分比直到稳定触发
3. **键盘替代**：研究是否可以用 Enter/Tab 等键盘操作替代鼠标点击
4. **图像匹配**：用模板匹配找到"定位到聊天位置"的像素位置

### 引用回复（已可用）

消息出现在聊天视图后：
```python
msgs = wx.GetAllMessage()
target = next((m for m in msgs if keyword in str(m.content)), None)
resp = target.quote(reply_text)  # 右键→菜单选"引用"→输入→发送
```

## 完整参考代码

参见 `test_search_quote.py`。

## 快速开始

```bash
# 安装依赖
pip install -e .

# 确保微信在主屏
python -c "import win32gui,win32con; from wxauto4 import WeChat; w=WeChat(); win32gui.SetWindowPos(w._api.HWND,0,100,30,1260,950,win32con.SWP_NOZORDER)"

# 运行测试
PYTHONIOENCODING=utf-8 python test_search_quote.py
```
