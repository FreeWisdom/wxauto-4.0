# 朋友圈

wxauto4 提供朋友圈的**读取、点赞、评论**接口。完整 API 见 [Moment](../api/moment.md)。

## 切换到朋友圈

```python
wx.SwitchToMoments()
```

朋友圈操作要求当前在朋友圈页面。首次调用建议先 `SwitchToMoments()` 等几秒，再 `GetMoments(refresh=False)`。

## 读取朋友圈

```python
wx.SwitchToMoments()

import time
time.sleep(2)

moments = wx.Moment.GetMoments()
for item in moments:
    print('---')
    print('发布者:', item.publisher)
    print('时间:', item.timestamp)
    print('正文:', item.text[:50])
    print('位置:', item.location)
    print('图片数:', item.image_count)
    print('点赞:', item.like_users)
    for c in item.comment_list:
        print(f'  评论 - {c.author}: {c.content}')
    print('广告:', item.is_advertisement)
```

### 强制刷新

```python
moments = wx.Moment.GetMoments(refresh=True)
```

> **注意**：`refresh=True` 会清空缓存强制重新解析，但微信 4.0.5 部分版本下重渲染时机问题可能返回 0 条。**建议改为**先 `SwitchToMoments()`、等待几秒、再用 `refresh=False` 读取。

## 按发布者查找

```python
item = wx.Moment.FindMomentByPublisher('张三')
if item:
    print('找到:', item.text[:30])
```

`FindMomentByPublisher` 内部遍历当前缓存，找不到返回 `None`。可强制刷新：

```python
item = wx.Moment.FindMomentByPublisher('张三', refresh=True)
```

## 点赞与取消

```python
target = wx.Moment.FindMomentByPublisher('张三')
if target:
    wx.Moment.Like(target)                       # 点赞
    wx.Moment.Like(target, cancel=True)          # 取消点赞
```

`Like` 返回 [`WxResponse`](../api/response.md)，可用 `if resp:` 判断成功。

## 评论与回复

```python
target = wx.Moment.FindMomentByPublisher('张三')
if target:
    # 直接评论
    wx.Moment.Comment(target, '写得真好')

    # 回复某条评论
    wx.Moment.Comment(target, '同感', reply_to='李四')
```

`reply_to` 是被回复评论的作者名。若该作者在此条朋友圈有多条评论，回复第一条匹配项。

## MomentItem 字段速查

| 属性 | 类型 | 说明 |
|---|---|---|
| `publisher` | str | 发布者昵称 |
| `text` | str | 正文 |
| `timestamp` | str | 时间字符串 |
| `location` | str \| None | 位置 |
| `like_users` | List[str] | 点赞用户列表 |
| `comment_list` | List[MomentComment] | 评论列表 |
| `image_count` | int | 图片数量 |
| `is_advertisement` | bool | 是否为广告 |

`MomentComment` 字段：

| 字段 | 说明 |
|---|---|
| `author` | 评论作者昵称 |
| `content` | 评论内容 |
| `reply_to` | 被回复者昵称（可选） |
| `raw` | 原始评论文本 |

## 已知限制

- 朋友圈列表采用启发式定位，深度滚动后可能解析不准；建议在已加载的状态下读取，避免边滚边读
- `refresh=True` 偶发返回 0 条（详见 [已知问题](../../README.md#已知问题)）
- 广告类型朋友圈的 `is_advertisement` 标记依赖微信内部样式，跨小版本可能漂移

## 完整示例

```python
from wxauto4 import WeChat
import time

wx = WeChat()
wx.SwitchToMoments()
time.sleep(3)

# 找出张三今天发的所有朋友圈并点赞 + 评论
for item in wx.Moment.GetMoments():
    if item.publisher == '张三' and not item.is_advertisement:
        wx.Moment.Like(item)
        wx.Moment.Comment(item, '👍')
        print(f'已点赞评论: {item.text[:30]}')
```

## 下一步

- 完整 API：[Moment](../api/moment.md)
- 响应对象：[WxResponse](../api/response.md)
