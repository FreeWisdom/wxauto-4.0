# WxResponse 统一响应

`WxResponse` 继承 `dict`，定义在 [wxauto4/param.py](../../wxauto4/param.py)。`SendMsg` / `SendFiles` / `Like` / `Comment` 等动作类方法返回此类型，三态描述调用结果。

## 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | str | `'成功'` / `'失败'` / `'错误'` |
| `message` | str | 人类可读的结果描述 |
| `data` | dict | 附加上下文（如失败原因、相关 ID 等） |

## 判断结果

`__bool__` 重写为 `is_success`，可直接用 `if resp:`：

```python
resp = wx.SendMsg('hi', '张三')
if resp:
    print('发送成功')
else:
    print(f"失败: {resp['status']} - {resp['message']}")
```

也可显式调用 `is_success` property：

```python
if resp.is_success:
    ...
```

## 工厂方法（classmethod）

`WxResponse` 提供三个工厂方法，主要用于库内部或自定义回调中构造响应：

### `WxResponse.success(message=None, data=None)`

构造成功响应。

### `WxResponse.failure(message, data=None)`

构造失败响应（业务失败，如未找到目标聊天）。

### `WxResponse.error(message, data=None)`

构造错误响应（异常情况，如网络异常）。

```python
from wxauto4 import WxResponse

ok = WxResponse.success('已发送')
bad = WxResponse.failure('未找到目标聊天')
err = WxResponse.error('网络异常')

print(ok, ok.is_success)      # {'status': '成功', ...} True
print(bad, bool(bad))         # {'status': '失败', ...} False
print(err, bool(err))         # {'status': '错误', ...} False
```

## 字典访问

`WxResponse` 继承 `dict`，所有字典操作都支持：

```python
resp = wx.SendMsg('hi', '张三')
resp['status']
resp.get('message', '')
resp.keys()
dict(resp)
```

### `to_dict()`

转普通字典。

## 状态语义

| `status` | 含义 | 是否成功 |
|---|---|---|
| `'成功'` | 操作完成 | True |
| `'失败'` | 业务失败（可恢复，如目标不存在） | False |
| `'错误'` | 异常情况（不应出现） | False |

调用方通常只需区分「成功」与「未成功」：

```python
resp = wx.Moment.Like(item)
if not resp:
    print(f"操作失败: {resp['message']}")
```

## 示例

```python
from wxauto4 import WeChat

wx = WeChat()

# 发消息
resp = wx.SendMsg('hi', '不存在的联系人')
if not resp:
    print('发送失败:', resp['message'])

# 发文件
files = [r'C:\a.txt', r'C:\b.png']
resp = wx.SendFiles(files, '工作群')
if resp:
    print(f'已发送 {len(files)} 个文件')

# 点赞
wx.SwitchToMoments()
import time; time.sleep(2)
for item in wx.Moment.GetMoments():
    if item.publisher == '张三':
        r = wx.Moment.Like(item)
        print(r['status'], r.get('message', ''))
        break
```

## 下一步

- 异常处理：[Exceptions](exceptions.md)
- 完整 API：[WeChat](wechat.md)
