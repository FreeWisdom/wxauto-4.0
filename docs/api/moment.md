# Moment 朋友圈

朋友圈接口定义在 [wxauto4/moment.py](../../wxauto4/moment.py)。`Moment` 类通过 `wx.Moment` 属性访问。

## Moment 类

### `GetMoments(refresh=False) -> List[MomentItem]`

读取朋友圈动态列表。

| 参数 | 说明 |
|---|---|
| `refresh` | 是否强制刷新缓存 |

> **注意**：`refresh=True` 在微信 4.0.5 部分版本下可能返回 0 条。建议先 `wx.SwitchToMoments()`，等待几秒后再 `GetMoments(refresh=False)`。

### `FindMomentByPublisher(nickname, refresh=False) -> Optional[MomentItem]`

按发布者昵称查找朋友圈动态。找不到返回 `None`。

### `Like(item, cancel=False) -> WxResponse`

对一条朋友圈点赞或取消点赞。

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | MomentItem | 目标动态 |
| `cancel` | bool | True 表示取消点赞 |

### `Comment(item, content, reply_to=None) -> WxResponse`

评论一条朋友圈，或回复已有评论。

| 参数 | 类型 | 说明 |
|---|---|---|
| `item` | MomentItem | 目标动态 |
| `content` | str | 评论内容 |
| `reply_to` | str | 被回复评论的作者昵称（可选） |

## MomentItem

单条朋友圈动态。

### 实例属性

直接访问，不需要方法调用：

| 属性 | 类型 | 说明 |
|---|---|---|
| `nickname` | str | 发布者昵称（原始字段） |
| `content` | str | 正文（原始字段） |
| `time` | str | 时间字符串（原始字段） |
| `location` | str \| None | 位置 |
| `likes` | List[str] | 点赞用户列表（原始字段） |
| `comments` | List[MomentComment] | 评论列表（原始字段） |
| `image_count` | int | 图片数量 |
| `is_advertisement` | bool | 是否为广告 |

### `@property` 别名

| 属性 | 类型 | 说明 |
|---|---|---|
| `publisher` | str | 发布者（同 `nickname`） |
| `text` | str | 正文（同 `content`） |
| `timestamp` | str | 时间（同 `time`） |
| `like_users` | List[str] | 点赞用户（同 `likes`） |
| `comment_list` | List[MomentComment] | 评论（同 `comments`） |

### `find_comment(author) -> Optional[MomentComment]`

按作者查找评论，找不到返回 `None`。

### `get_comment_control(comment) -> Optional[uia.Control]`

根据评论对象定位底层 UIA 控件。

## MomentComment

朋友圈评论的数据类（`@dataclass`）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `author` | str | 评论作者昵称 |
| `content` | str | 评论内容 |
| `reply_to` | str \| None | 被回复者昵称 |
| `raw` | str | 原始评论文本 |

### `MomentComment.from_text(text) -> MomentComment` (classmethod)

从原始评论文本解析构造。

## MomentList

朋友圈列表封装，通常通过 `wx.Moment` 间接使用。

### `get_items(refresh=False) -> List[MomentItem]`

获取全部动态。

### `refresh() -> None`

清空缓存。

### `exists(wait=0) -> bool`

判断列表控件是否存在。

## MomentActionMenu / MomentCommentDialog

点赞评论弹窗的内部封装。一般不直接使用，由 `Moment.Like` / `Moment.Comment` 内部调用。

## 完整示例

```python
from wxauto4 import WeChat
import time

wx = WeChat()
wx.SwitchToMoments()
time.sleep(3)

for item in wx.Moment.GetMoments():
    if item.is_advertisement:
        continue
    print(item.publisher, '@', item.timestamp)
    print('  正文:', item.text[:50])
    for c in item.comment_list:
        print(f'  [{c.author}]: {c.content}')

# 给张三最新一条点赞
target = wx.Moment.FindMomentByPublisher('张三')
if target:
    wx.Moment.Like(target)
    wx.Moment.Comment(target, '点赞支持')
```

## 下一步

- 完整指南：[朋友圈指南](../guide/moments.md)
- 返回值类型：[WxResponse](response.md)
