"""真实微信搜索、入库与引用回复测试。

该脚本只使用 wxauto4 项目功能和 Windows 系统 OCR，不调用任何大模型、
多模态模型或外部视觉识别服务。

默认模式不会发送消息，只验证：

1. SQLite 待回复任务入库；
2. 相同消息重复入库时去重；
3. 微信全局搜索和“定位到聊天位置”；
4. 定位后的聊天名称和消息内容。

只有显式传入 ``--send`` 时，才会执行右键引用和发送，并在成功后检查
数据库状态是否变为 ``replied``。
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import tempfile
import time
import traceback
from pathlib import Path

from wxauto4 import HandRaiseReplyWorkflow, SearchMessageLocator, WeChat
from wxauto4.reply_queue import STATUS_PENDING, STATUS_REPLIED


DEFAULT_CHAT = "每日饮食打卡🍽️"
DEFAULT_KEYWORD = "晚上吃点什么大家"
DEFAULT_REPLY = "收到，晚上见【wxauto4脚本测试】"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "使用 wxauto4 + Windows 系统 OCR 测试消息入库、搜索定位和引用回复；"
            "默认不发送消息。"
        )
    )
    parser.add_argument("--chat", default=DEFAULT_CHAT, help="目标聊天名称")
    parser.add_argument("--keyword", default=DEFAULT_KEYWORD, help="要搜索的消息原文")
    parser.add_argument(
        "--reply-text",
        default=DEFAULT_REPLY,
        help="启用 --send 时发送的回复内容",
    )
    parser.add_argument(
        "--db",
        type=Path,
        help="测试数据库路径；不指定时使用系统临时目录中的独立数据库",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="真实执行引用回复；未指定时只定位和验证，不发送",
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="测试结束后保留自动创建的临时数据库",
    )
    return parser


def print_event(event: str, **data) -> None:
    payload = {"event": event, **data}
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def create_db_path(requested: Path | None) -> tuple[Path, bool]:
    if requested is not None:
        return requested.expanduser().resolve(), False
    filename = f"wxauto4_reply_workflow_test_{time.time_ns()}.db"
    return Path(tempfile.gettempdir()) / filename, True


def remove_sqlite_files(db_path: Path) -> None:
    gc.collect()
    paths = (
        db_path,
        Path(f"{db_path}-wal"),
        Path(f"{db_path}-shm"),
    )
    for _ in range(5):
        remaining = []
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                remaining.append(path)
        if not remaining:
            return
        gc.collect()
        time.sleep(0.1)


def run(args: argparse.Namespace) -> int:
    db_path, _ = create_db_path(args.db)
    print_event(
        "test_start",
        vision_backend="Windows.Media.Ocr",
        ai_vision=False,
        send_enabled=args.send,
        chat=args.chat,
        keyword=args.keyword,
        db=str(db_path),
    )

    wx = WeChat()
    workflow = HandRaiseReplyWorkflow(
        wx,
        db_path=db_path,
        allowed_chats=[args.chat],
    )

    # 测试任务使用唯一消息 ID，避免复用旧数据库时误领取历史任务。
    test_message_id = f"integration-test:{time.time_ns()}"
    task = workflow.store.enqueue(
        chat_name=args.chat,
        sender="",
        content=args.keyword,
        marker="#举手",
        message_id=test_message_id,
        message_type="text",
    )
    duplicate = workflow.store.enqueue(
        chat_name=args.chat,
        sender="",
        content=args.keyword,
        marker="#举手",
        message_id=test_message_id,
        message_type="text",
    )
    if duplicate.id != task.id:
        raise RuntimeError("SQLite 去重失败：相同消息生成了两个任务")
    if task.status != STATUS_PENDING:
        raise RuntimeError(f"新任务状态错误：{task.status}")
    print_event(
        "database_ok",
        task_id=task.id,
        deduplicated=True,
        status=task.status,
    )

    locator = SearchMessageLocator(wx, timeout=8)
    message = locator.locate(task)
    if message is None:
        raise RuntimeError("未能通过微信全局搜索定位目标消息")

    chat_info = wx.ChatInfo()
    actual_chat = chat_info.get("chat_name")
    actual_content = str(getattr(message, "content", "")).strip()
    if actual_chat != args.chat:
        raise RuntimeError(
            f"定位到错误聊天：期望 {args.chat!r}，实际 {actual_chat!r}"
        )
    if args.keyword not in actual_content:
        raise RuntimeError(
            f"定位到错误消息：期望包含 {args.keyword!r}，实际 {actual_content!r}"
        )
    print_event(
        "locate_ok",
        chat=actual_chat,
        chat_type=chat_info.get("chat_type"),
        sender=getattr(message, "sender", None),
        attr=getattr(message, "attr", None),
        content=actual_content,
    )

    if not args.send:
        print_event(
            "dry_run_complete",
            sent=False,
            task_status=workflow.store.get(task.id).status,
        )
        return 0

    response = workflow.reply(task.id, args.reply_text)
    stored = workflow.store.get(task.id)
    if not response:
        raise RuntimeError(response.get("message") or "引用回复失败")
    if stored is None or stored.status != STATUS_REPLIED:
        raise RuntimeError(
            f"消息发送成功后数据库状态错误：{getattr(stored, 'status', None)!r}"
        )
    print_event(
        "reply_ok",
        sent=True,
        task_id=task.id,
        status=stored.status,
        reply_text=stored.reply_text,
        replied_at=stored.replied_at,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")

    args = build_parser().parse_args(argv)
    db_path, temporary_db = create_db_path(args.db)
    # run() 需要使用同一个自动生成路径，避免清理另一个临时文件。
    args.db = db_path
    try:
        return run(args)
    except Exception as exc:
        print_event("test_failed", error=repr(exc))
        traceback.print_exc()
        return 1
    finally:
        if temporary_db and not args.keep_db:
            remove_sqlite_files(db_path)
        elif temporary_db:
            print_event("database_kept", db=str(db_path))


if __name__ == "__main__":
    sys.exit(main())
