# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，版本号与 `pyproject.toml` 中的 `version` 字段一致。

## [Unreleased]

### 已知问题
- `SwitchToFiles()` / `SwitchToStories()` 在微信 4.0.5 部分版本下点击后侧边栏不切换
- `GetMoments(refresh=True)` 强制刷新后可能返回 0 条
- `GetMessageById(msg_id)` 对最后一条文件消息可能返回 `None`

## [40.1.1] - 2026-06-15

### 修复
- 修复 wxauto4 消息与路径处理（`45161d0`）
  - 消息解析路径异常
  - 微信安装路径/版本目录解析问题

## [40.1.0] - 2025-09-19

7 个 PR 集中合并，补全 README 中提到但尚未实现的功能。

### 新增
- **导航切换助手**（`804da4a`）：`WeChat` 类增加 11 个 `SwitchTo*` 方法（Chat/Contact/Favorites/Files/Moments/Browser/Video/Stories/MiniProgram/Phone/Settings）
- **聊天消息读取助手**（`91dea62`，PR#2）：`Chat` 类（子窗口）增加 `GetAllMessage` / `GetNewMessage` / `GetMessageById` / `GetMessageByHash` / `GetLastMessage`
- **消息映射工具**（`8d88f5b`，PR#3）：`Message` 基类支持字典/迭代协议（`keys` / `values` / `items` / `get` / `to_dict` / `match`），增加 `is_self` / `is_friend` / `is_system` 属性
- **会话操作完善**（`26a42b0`，PR#4）：`SessionBox` 与 `SessionElement`，会话置顶/免打扰/标记未读/隐藏/删除/独立窗口等 15 个动作
- **朋友圈基础支持**（`f09f5c7`，PR#5）：`Moment` 类、`MomentItem` / `MomentComment` / `MomentList` / `MomentActionMenu` / `MomentCommentDialog`
- **异常与锁实现**（`5d82551`，PR#6）：`WxautoError` / `NetWorkError` / `WxautoUINotFoundError` / `WxautoNoteLoadTimeoutError`；`LockManager` 与 `uilock` 装饰器
- **完整 demo 脚本**（`941f78d`，PR#8）：`demo.py` 覆盖全部公开 API 的命令行演示
- **工具与朋友圈修复**（`476f1b1`，PR#7）：`utils/tools.py` 与 `moment.py` 的稳定性修复

## [0.1.0] - 2025-09-04

### 新增
- 项目初始化（`b99719b`）
- README 描述（`f2039ee`）
- 自动删除微信新版本文件，避免自动更新导致版本漂移（`4307976`）

[Unreleased]: https://github.com/cluic/wxauto4/compare/v40.1.1...HEAD
[40.1.1]: https://github.com/cluic/wxauto4/compare/v40.1.0...v40.1.1
[40.1.0]: https://github.com/cluic/wxauto4/compare/v0.1.0...v40.1.0
[0.1.0]: https://github.com/cluic/wxauto4/releases/tag/v0.1.0
