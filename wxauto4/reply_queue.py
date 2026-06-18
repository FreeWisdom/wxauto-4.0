"""带标记消息的持久化与搜索引用回复工作流。"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import sqlite3
import subprocess
import time
import win32api
import win32con
import win32gui
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Set, TYPE_CHECKING

from PIL import Image

from wxauto4 import uia
from wxauto4.logger import wxlog
from wxauto4.param import WxParam, WxResponse
from wxauto4.utils.lock import uilock
from wxauto4.utils.win32 import SetClipboardText, preserve_clipboard_text

if TYPE_CHECKING:
    from wxauto4.msgs.base import Message
    from wxauto4.wx import Chat, WeChat


STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_REPLIED = "replied"
STATUS_FAILED = "failed"


_WINDOWS_OCR_LINES_SCRIPT = r"""& {
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$path = $env:WXAUTO4_OCR_IMAGE
if (-not $path) { exit 3 }
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStreamWithContentType, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
function Await($op, [Type]$type) {
    $asTask = $asTaskGeneric.MakeGenericMethod($type)
    $task = $asTask.Invoke($null, @($op))
    $task.Wait()
    $task.Result
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('zh-Hans'))
if ($null -eq $engine) { exit 2 }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$output = @()
foreach ($line in $result.Lines) {
    $words = @($line.Words)
    if ($words.Count -eq 0) { continue }
    $left = ($words | ForEach-Object { $_.BoundingRect.X } | Measure-Object -Minimum).Minimum
    $top = ($words | ForEach-Object { $_.BoundingRect.Y } | Measure-Object -Minimum).Minimum
    $right = ($words | ForEach-Object { $_.BoundingRect.X + $_.BoundingRect.Width } | Measure-Object -Maximum).Maximum
    $bottom = ($words | ForEach-Object { $_.BoundingRect.Y + $_.BoundingRect.Height } | Measure-Object -Maximum).Maximum
    $output += [PSCustomObject]@{
        text = $line.Text
        x = [double]$left
        y = [double]$top
        width = [double]($right - $left)
        height = [double]($bottom - $top)
    }
}
$output | ConvertTo-Json -Compress
}"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").split())


@dataclass(frozen=True)
class ReplyTask:
    id: int
    dedupe_key: str
    chat_name: str
    sender: str
    content: str
    marker: str
    message_id: Optional[str]
    message_hash: Optional[str]
    message_type: Optional[str]
    status: str
    attempts: int
    reply_text: Optional[str]
    last_error: Optional[str]
    received_at: str
    replied_at: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ReplyTask":
        return cls(**dict(row))


class ReplyTaskStore:
    """SQLite 待回复任务存储。

    每个方法独立创建连接，便于监听线程和回复线程并发使用。
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reply_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dedupe_key TEXT NOT NULL UNIQUE,
                    chat_name TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    marker TEXT NOT NULL,
                    message_id TEXT,
                    message_hash TEXT,
                    message_type TEXT,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    reply_text TEXT,
                    last_error TEXT,
                    received_at TEXT NOT NULL,
                    replied_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reply_tasks_status_id "
                "ON reply_tasks(status, id)"
            )

    @staticmethod
    def build_dedupe_key(
        chat_name: str,
        sender: str,
        content: str,
        message_id: Optional[str] = None,
        message_hash: Optional[str] = None,
    ) -> str:
        identity = message_id or message_hash or f"{sender}\0{content}"
        raw = f"{chat_name}\0{identity}".encode("utf-8", errors="replace")
        return hashlib.sha256(raw).hexdigest()

    def enqueue(
        self,
        *,
        chat_name: str,
        sender: str,
        content: str,
        marker: str,
        message_id: Optional[str] = None,
        message_hash: Optional[str] = None,
        message_type: Optional[str] = None,
        received_at: Optional[str] = None,
    ) -> ReplyTask:
        now = _utcnow()
        dedupe_key = self.build_dedupe_key(
            chat_name,
            sender,
            content,
            message_id,
            message_hash,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO reply_tasks (
                    dedupe_key, chat_name, sender, content, marker,
                    message_id, message_hash, message_type, status,
                    received_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dedupe_key,
                    chat_name,
                    sender,
                    content,
                    marker,
                    message_id,
                    message_hash,
                    message_type,
                    STATUS_PENDING,
                    received_at or now,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM reply_tasks WHERE dedupe_key = ?",
                (dedupe_key,),
            ).fetchone()
        return ReplyTask.from_row(row)

    def get(self, task_id: int) -> Optional[ReplyTask]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM reply_tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return ReplyTask.from_row(row) if row else None

    def list(
        self,
        statuses: Optional[Sequence[str]] = None,
        limit: int = 100,
    ) -> List[ReplyTask]:
        params: List[object] = []
        where = ""
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            where = f"WHERE status IN ({placeholders})"
            params.extend(statuses)
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM reply_tasks {where} ORDER BY id ASC LIMIT ?",
                params,
            ).fetchall()
        return [ReplyTask.from_row(row) for row in rows]

    def claim(self, task_id: Optional[int] = None) -> Optional[ReplyTask]:
        """原子领取一个待回复任务。

        指定 task_id 时允许手动重试 failed 任务；自动领取只取 pending。
        """

        now = _utcnow()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if task_id is None:
                row = connection.execute(
                    "SELECT id FROM reply_tasks WHERE status = ? ORDER BY id ASC LIMIT 1",
                    (STATUS_PENDING,),
                ).fetchone()
                allowed_statuses = (STATUS_PENDING,)
            else:
                row = connection.execute(
                    "SELECT id FROM reply_tasks "
                    "WHERE id = ? AND status IN (?, ?)",
                    (task_id, STATUS_PENDING, STATUS_FAILED),
                ).fetchone()
                allowed_statuses = (STATUS_PENDING, STATUS_FAILED)
            if row is None:
                connection.rollback()
                return None

            placeholders = ",".join("?" for _ in allowed_statuses)
            cursor = connection.execute(
                f"""
                UPDATE reply_tasks
                SET status = ?, attempts = attempts + 1,
                    last_error = NULL, updated_at = ?
                WHERE id = ? AND status IN ({placeholders})
                """,
                (STATUS_PROCESSING, now, row["id"], *allowed_statuses),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                return None
            claimed = connection.execute(
                "SELECT * FROM reply_tasks WHERE id = ?",
                (row["id"],),
            ).fetchone()
            connection.commit()
        return ReplyTask.from_row(claimed)

    def mark_replied(self, task_id: int, reply_text: str) -> ReplyTask:
        now = _utcnow()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE reply_tasks
                SET status = ?, reply_text = ?, replied_at = ?,
                    last_error = NULL, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    STATUS_REPLIED,
                    reply_text,
                    now,
                    now,
                    task_id,
                    STATUS_PROCESSING,
                ),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"任务 {task_id} 不是 processing 状态")
            row = connection.execute(
                "SELECT * FROM reply_tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return ReplyTask.from_row(row)

    def mark_failed(self, task_id: int, error: str) -> ReplyTask:
        now = _utcnow()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE reply_tasks
                SET status = ?, last_error = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (STATUS_FAILED, error, now, task_id, STATUS_PROCESSING),
            )
            row = connection.execute(
                "SELECT * FROM reply_tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return ReplyTask.from_row(row)

    def retry(self, task_id: int) -> Optional[ReplyTask]:
        now = _utcnow()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE reply_tasks
                SET status = ?, last_error = NULL, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (STATUS_PENDING, now, task_id, STATUS_FAILED),
            )
            row = connection.execute(
                "SELECT * FROM reply_tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return ReplyTask.from_row(row) if row else None


class SearchMessageLocator:
    """通过微信全局搜索定位到原消息并返回消息对象。"""

    SEARCH_WINDOW_CLASS = "mmui::SearchMsgWindow"
    SEARCH_POPOVER_CLASS = "mmui::SearchContentPopover"
    SEARCH_EDIT_CLASS = "mmui::XValidatorTextEdit"
    MESSAGE_LIST_CLASS = "mmui::RecyclerListView"
    MESSAGE_ITEM_CLASS = "mmui::ChatTextItemView"

    def __init__(
        self,
        wx: "WeChat",
        *,
        timeout: float = 6.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.wx = wx
        self.timeout = timeout
        self.sleep = sleep

    def _wait_for(self, factory: Callable[[], object], timeout: Optional[float] = None):
        deadline = time.time() + (timeout or self.timeout)
        last = None
        while time.time() < deadline:
            try:
                last = factory()
                if last is not None and (
                    not hasattr(last, "Exists") or last.Exists(0)
                ):
                    return last
            except Exception:
                last = None
            self.sleep(0.1)
        return None

    @staticmethod
    def _children(control) -> list:
        try:
            return list(control.GetChildren())
        except Exception:
            return []

    def _walk(self, control, max_depth: int = 8) -> Iterable[object]:
        stack = [(control, 0)]
        while stack:
            current, depth = stack.pop()
            yield current
            if depth >= max_depth:
                continue
            children = self._children(current)
            stack.extend((child, depth + 1) for child in reversed(children))

    def _find(
        self,
        control,
        *,
        control_type: Optional[str] = None,
        class_name: Optional[str] = None,
        automation_id: Optional[str] = None,
        name: Optional[str] = None,
        max_depth: int = 8,
    ):
        for candidate in self._walk(control, max_depth=max_depth):
            try:
                if control_type and candidate.ControlTypeName != control_type:
                    continue
                if class_name and candidate.ClassName != class_name:
                    continue
                if automation_id and candidate.AutomationId != automation_id:
                    continue
                if name and candidate.Name != name:
                    continue
                return candidate
            except Exception:
                continue
        return None

    def _set_search_text(self, edit, text: str) -> None:
        edit.Click()
        edit.SendKeys("{Ctrl}a")
        edit.SendKeys("{BACK}")
        with preserve_clipboard_text():
            SetClipboardText(text)
            edit.SendKeys("{Ctrl}v")

    def _resolve_search_edit(self):
        session_control = self.wx._api._session_api.control
        search_edit = session_control.EditControl(
            Name="搜索",
            ClassName=self.SEARCH_EDIT_CLASS,
        )
        try:
            if search_edit.Exists(0):
                return search_edit
        except Exception:
            pass

        # WeChat 4.x 在窗口跨 DPI 屏幕移动后，UIA 主树有时只暴露一个
        # MMUIRenderSubWindowHW Pane。此时搜索框仍可交互，但无法按树检索。
        # 使用主窗口内已验证的相对位置聚焦，并用焦点控件类型反向校验。
        main_window = uia.ControlFromHandle(self.wx._api.HWND)
        rect = main_window.BoundingRectangle
        main_window.Click(
            x=int(rect.width() * 0.21),
            y=int(rect.height() * 0.073),
            ratioX=0,
            ratioY=0,
            waitTime=0.3,
        )
        focused = uia.GetFocusedControl()
        if (
            getattr(focused, "ControlTypeName", None) != "EditControl"
            or getattr(focused, "ClassName", None) != self.SEARCH_EDIT_CLASS
        ):
            raise RuntimeError("无法聚焦微信顶部搜索框")
        return focused

    def _select_global_result(self, popover, task: ReplyTask):
        query = _normalize_text(task.content)
        chat_name = _normalize_text(task.chat_name)
        candidates = []
        for candidate in self._walk(popover, max_depth=8):
            try:
                if candidate.ControlTypeName != "ListItemControl":
                    continue
                name = _normalize_text(candidate.Name)
                if not name:
                    continue
                score = 0
                if query and query in name:
                    score += 10
                if chat_name and chat_name in name:
                    score += 5
                if candidate.ClassName == "mmui::SearchContentCellView":
                    score += 2
                if score:
                    candidates.append((score, candidate))
            except Exception:
                continue
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _select_chat_in_search_window(self, search_window, task: ReplyTask) -> None:
        search_list = self._find(
            search_window,
            control_type="ListControl",
            automation_id="search_list",
            max_depth=8,
        )
        if search_list is None:
            return
        chat_name = _normalize_text(task.chat_name)
        rows = self._children(search_list)
        matches = [
            row
            for row in rows
            if chat_name and chat_name in _normalize_text(getattr(row, "Name", ""))
        ]
        if matches:
            matches[0].Click()
            self.sleep(0.3)

    def _find_message_item(self, message_list, content: str):
        query = _normalize_text(content)
        for candidate in self._children(message_list):
            try:
                if candidate.ControlTypeName != "ListItemControl":
                    continue
                name = _normalize_text(candidate.Name)
                if query and query in name:
                    return candidate
            except Exception:
                continue
        return None

    def _scroll_to_message(self, message_list, content: str):
        unchanged_rounds = 0
        previous_names = None
        for _ in range(20):
            item = self._find_message_item(message_list, content)
            if item is not None:
                return item
            names = tuple(
                _normalize_text(getattr(child, "Name", ""))
                for child in self._children(message_list)
            )
            if names == previous_names:
                unchanged_rounds += 1
            else:
                unchanged_rounds = 0
            if unchanged_rounds >= 3:
                break
            previous_names = names
            message_list.WheelDown(wheelTimes=5, waitTime=0.2)
        return None

    def _close_search_window(self, search_window) -> None:
        """关闭聊天记录搜索窗口。

        UIA 的关闭按钮在负坐标副屏和混合 DPI 下偶发不生效，因此保留
        Win32 ``WM_CLOSE`` 兜底，避免搜索窗口遮挡后续消息右键操作。
        """

        close_button = self._find(
            search_window,
            control_type="ButtonControl",
            name="关闭",
            max_depth=8,
        )
        if close_button is not None:
            try:
                close_button.Click()
            except Exception:
                pass

        handles = []

        def collect(hwnd, _):
            try:
                if win32gui.GetWindowText(hwnd) == "搜索聊天记录":
                    handles.append(hwnd)
            except Exception:
                pass

        win32gui.EnumWindows(collect, None)
        for hwnd in handles:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass
        if handles:
            self.sleep(0.3)

    def _find_visible_message(self, task: ReplyTask) -> Optional["Message"]:
        query = _normalize_text(task.content)
        sender = _normalize_text(task.sender)
        try:
            messages = self.wx.GetAllMessage()
        except Exception:
            return None
        content_matches = [
            message
            for message in reversed(messages)
            if _normalize_text(getattr(message, "content", "")) == query
        ]
        if sender:
            for message in content_matches:
                if _normalize_text(getattr(message, "sender", "")) == sender:
                    return message
        return content_matches[0] if content_matches else None

    @staticmethod
    def _native_click(x: int, y: int, *, right: bool = False) -> None:
        win32api.SetCursorPos((x, y))
        if right:
            down = win32con.MOUSEEVENTF_RIGHTDOWN
            up = win32con.MOUSEEVENTF_RIGHTUP
        else:
            down = win32con.MOUSEEVENTF_LEFTDOWN
            up = win32con.MOUSEEVENTF_LEFTUP
        win32api.mouse_event(down, 0, 0, 0, 0)
        win32api.mouse_event(up, 0, 0, 0, 0)

    def _ocr_lines(self, image_path: Path) -> list:
        env = os.environ.copy()
        env["WXAUTO4_OCR_IMAGE"] = str(image_path)
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                _WINDOWS_OCR_LINES_SCRIPT,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=WxParam.SENDER_OCR_TIMEOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            env=env,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else [data]

    def _find_text_point(self, content: str) -> Optional[tuple]:
        main_window = uia.ControlFromHandle(self.wx._api.HWND)
        screenshot = Path(main_window.ScreenShot())
        try:
            with Image.open(screenshot) as image:
                image_width, image_height = image.size
            lines = self._ocr_lines(screenshot)
        finally:
            screenshot.unlink(missing_ok=True)

        query = _normalize_text(content)
        compact_query = "".join(query.split())
        best = None
        for line in lines:
            text = _normalize_text(line.get("text", ""))
            compact_text = "".join(text.split())
            if not compact_text:
                continue
            if compact_query in compact_text or compact_text in compact_query:
                score = 1.0
            else:
                score = difflib.SequenceMatcher(
                    None,
                    compact_query,
                    compact_text,
                ).ratio()
            if score >= 0.62 and (best is None or score > best[0]):
                best = (score, line)
        if best is None:
            return None

        rect = main_window.BoundingRectangle
        line = best[1]
        scale_x = rect.width() / max(image_width, 1)
        scale_y = rect.height() / max(image_height, 1)
        x = rect.left + int((float(line["x"]) + float(line["width"]) / 2) * scale_x)
        y = rect.top + int((float(line["y"]) + float(line["height"]) / 2) * scale_y)
        return x, y

    def _find_quote_menu_item(self, timeout: float = 3.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            handles = []

            def collect(hwnd, _):
                try:
                    if (
                        win32gui.IsWindowVisible(hwnd)
                        and win32gui.GetWindowText(hwnd) == "Weixin"
                        and "ToolSaveBits" in win32gui.GetClassName(hwnd)
                    ):
                        handles.append(hwnd)
                except Exception:
                    pass

            win32gui.EnumWindows(collect, None)
            for hwnd in handles:
                try:
                    menu = uia.ControlFromHandle(hwnd)
                    if menu.ClassName != "mmui::XMenu":
                        continue
                    item = menu.MenuItemControl(Name="引用", searchDepth=2)
                    if item.Exists(0):
                        return item
                except Exception:
                    continue
            self.sleep(0.1)
        return None

    def _focus_chat_input(self):
        main_window = uia.ControlFromHandle(self.wx._api.HWND)
        rect = main_window.BoundingRectangle
        x = rect.left + int(rect.width() * 0.66)
        y = rect.top + int(rect.height() * 0.68)
        self._native_click(x, y)
        self.sleep(0.2)
        focused = uia.GetFocusedControl()
        if (
            getattr(focused, "ControlTypeName", None) != "EditControl"
            or getattr(focused, "ClassName", None) != "mmui::ChatInputField"
        ):
            raise RuntimeError("无法聚焦微信聊天输入框")
        return focused

    def _screen_quote_reply(self, task: ReplyTask, reply_text: str) -> WxResponse:
        point = self._find_text_point(task.content)
        if point is None:
            return WxResponse.failure("OCR 未找到目标消息文字")

        self._native_click(point[0], point[1], right=True)
        quote_item = self._find_quote_menu_item()
        if quote_item is None:
            return WxResponse.failure("右键菜单中未找到“引用”")
        rect = quote_item.BoundingRectangle
        self._native_click(
            (rect.left + rect.right) // 2,
            (rect.top + rect.bottom) // 2,
        )
        self.sleep(0.4)

        edit = self._focus_chat_input()
        edit.SendKeys("{Ctrl}a")
        edit.SendKeys("{BACK}")
        with preserve_clipboard_text():
            SetClipboardText(reply_text)
            edit.SendKeys("{Ctrl}v")
        if edit.GetValuePattern().Value != reply_text:
            return WxResponse.failure("回复内容未正确写入输入框")
        edit.SendKeys("{ENTER}", waitTime=0.8)
        if edit.GetValuePattern().Value:
            return WxResponse.failure("发送后输入框未清空")
        return WxResponse.success("引用回复成功")

    def reply(self, task: ReplyTask, reply_text: str) -> WxResponse:
        """定位并引用回复；UIA 消息边界失效时自动切换到 OCR 屏幕定位。"""

        message = self.locate(task)
        if message is None:
            return WxResponse.failure("已执行搜索定位，但主聊天中未找到原消息")
        response = message.quote(reply_text)
        if response:
            return response
        return self._screen_quote_reply(task, reply_text)

    @uilock
    def locate(self, task: ReplyTask) -> Optional["Message"]:
        """定位任务对应的原消息，不发送任何内容。"""

        query = task.content.strip()
        if not query:
            return None

        search_edit = self._resolve_search_edit()
        self._set_search_text(search_edit, query)

        root = uia.GetRootControl()
        popover = self._wait_for(
            lambda: root.WindowControl(ClassName=self.SEARCH_POPOVER_CLASS)
        )
        if popover is None:
            raise RuntimeError("未找到全局搜索结果窗口")

        result = self._wait_for(lambda: self._select_global_result(popover, task))
        if result is None:
            raise RuntimeError("全局搜索没有找到目标消息")
        result.Click()

        search_window = self._wait_for(
            lambda: root.WindowControl(
                Name="搜索聊天记录",
                ClassName=self.SEARCH_WINDOW_CLASS,
            )
        )
        if search_window is None:
            raise RuntimeError("未打开“搜索聊天记录”窗口")

        try:
            self._select_chat_in_search_window(search_window, task)
            message_list = self._wait_for(
                lambda: self._find(
                    search_window,
                    control_type="ListControl",
                    class_name=self.MESSAGE_LIST_CLASS,
                    max_depth=10,
                )
            )
            if message_list is None:
                raise RuntimeError("未找到聊天记录消息列表")

            message_item = self._scroll_to_message(message_list, task.content)
            if message_item is None:
                raise RuntimeError("聊天记录列表中未找到目标消息")

            # 实测 4.x 客户端悬浮后按钮固定在消息项右下区域。
            # 使用 UIA 相对坐标，避免 DPI 缩放和副屏负坐标导致 Win32 点击偏移。
            message_item.MoveCursorToInnerPos(x=-75, y=-25)
            self.sleep(0.6)
            message_item.Click(x=-75, y=-25)
            self.sleep(0.8)
        finally:
            self._close_search_window(search_window)

        return self._wait_for(lambda: self._find_visible_message(task), timeout=4.0)


class HandRaiseReplyWorkflow:
    """监听 ``#举手`` 消息、持久化，并按任务搜索引用回复。"""

    def __init__(
        self,
        wx: "WeChat",
        db_path: str | Path,
        *,
        marker: str = "#举手",
        groups_only: bool = True,
        allowed_chats: Optional[Sequence[str]] = None,
        locator: Optional[SearchMessageLocator] = None,
    ):
        self.wx = wx
        self.marker = marker
        self.groups_only = groups_only
        self.allowed_chats: Optional[Set[str]] = (
            set(allowed_chats) if allowed_chats is not None else None
        )
        self.store = ReplyTaskStore(db_path)
        self.locator = locator or SearchMessageLocator(wx)

    @staticmethod
    def _chat_info(chat: "Chat") -> dict:
        try:
            return chat.ChatInfo() or {}
        except Exception:
            return {}

    def listener_callback(
        self,
        message: "Message",
        chat: "Chat",
    ) -> Optional[ReplyTask]:
        """可直接传给 ``wx.AddListenChat`` 的轻量回调。"""

        content = str(getattr(message, "content", "") or "").strip()
        if self.marker not in content:
            return None
        if getattr(message, "attr", None) != "friend":
            return None

        info = self._chat_info(chat)
        if self.groups_only and info.get("chat_type") != "group":
            return None
        chat_name = (
            info.get("chat_name")
            or getattr(chat, "who", None)
            or getattr(chat, "nickname", None)
        )
        if not chat_name:
            wxlog.warning("收到带标记消息，但无法确定聊天名称")
            return None
        if self.allowed_chats is not None and chat_name not in self.allowed_chats:
            wxlog.warning("忽略不在允许列表中的聊天消息：%s", chat_name)
            return None

        task = self.store.enqueue(
            chat_name=chat_name,
            sender=str(getattr(message, "sender", "") or ""),
            content=content,
            marker=self.marker,
            message_id=str(getattr(message, "id", "") or "") or None,
            message_hash=str(getattr(message, "hash", "") or "") or None,
            message_type=str(getattr(message, "type", "") or "") or None,
        )
        wxlog.info("待回复消息已入库：task=%s chat=%s", task.id, chat_name)
        return task

    def add_listen_chats(self, chat_names: Sequence[str]) -> dict:
        """为指定群聊注册监听，并返回每个群的注册结果。"""

        return {
            chat_name: self.wx.AddListenChat(chat_name, self.listener_callback)
            for chat_name in chat_names
        }

    def list_pending(self, limit: int = 100) -> List[ReplyTask]:
        return self.store.list((STATUS_PENDING, STATUS_FAILED), limit=limit)

    def _reply_claimed(self, task: ReplyTask, reply_text: str) -> WxResponse:
        if self.allowed_chats is not None and task.chat_name not in self.allowed_chats:
            error = f"聊天不在允许列表中：{task.chat_name}"
            self.store.mark_failed(task.id, error)
            return WxResponse.failure(error)
        if not reply_text.strip():
            error = "回复内容不能为空"
            self.store.mark_failed(task.id, error)
            return WxResponse.failure(error)

        try:
            if hasattr(self.locator, "reply"):
                response = self.locator.reply(task, reply_text)
            else:
                message = self.locator.locate(task)
                if message is None:
                    raise RuntimeError("已执行搜索定位，但主聊天中未找到原消息")
                response = message.quote(reply_text)
            if not response:
                raise RuntimeError(response.get("message") or "引用回复失败")
        except Exception as exc:
            error = str(exc)
            self.store.mark_failed(task.id, error)
            wxlog.error("任务 %s 回复失败：%s", task.id, error)
            return WxResponse.failure(error, data={"task_id": task.id})

        replied = self.store.mark_replied(task.id, reply_text)
        return WxResponse.success(
            "引用回复成功",
            data={"task_id": replied.id, "status": replied.status},
        )

    def reply(self, task_id: int, reply_text: str) -> WxResponse:
        task = self.store.claim(task_id)
        if task is None:
            return WxResponse.failure("任务不存在、已回复或正在处理中")
        return self._reply_claimed(task, reply_text)

    def reply_next(self, reply_text: str) -> WxResponse:
        task = self.store.claim()
        if task is None:
            return WxResponse.failure("没有待回复任务")
        return self._reply_claimed(task, reply_text)


__all__ = [
    "HandRaiseReplyWorkflow",
    "ReplyTask",
    "ReplyTaskStore",
    "SearchMessageLocator",
    "STATUS_FAILED",
    "STATUS_PENDING",
    "STATUS_PROCESSING",
    "STATUS_REPLIED",
]
