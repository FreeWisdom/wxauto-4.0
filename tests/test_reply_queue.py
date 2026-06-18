"""测试带标记消息持久化与回复状态机。"""

from wxauto4.param import WxResponse
from wxauto4.reply_queue import (
    HandRaiseReplyWorkflow,
    ReplyTaskStore,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_REPLIED,
)


class FakeMessage:
    def __init__(
        self,
        content="#举手 测试问题",
        *,
        attr="friend",
        sender="张三",
        message_id="message-1",
    ):
        self.content = content
        self.attr = attr
        self.sender = sender
        self.id = message_id
        self.hash = "hash-1"
        self.type = "text"


class FakeChat:
    def __init__(self, name="测试群", chat_type="group"):
        self.who = name
        self._info = {"chat_name": name, "chat_type": chat_type}

    def ChatInfo(self):
        return self._info


class FakeWx:
    def AddListenChat(self, chat_name, callback):
        return chat_name, callback


class FakeQuotedMessage:
    def __init__(self, response=None):
        self.response = response or WxResponse.success("ok")
        self.reply_text = None

    def quote(self, text):
        self.reply_text = text
        return self.response


class FakeLocator:
    def __init__(self, message=None, error=None):
        self.message = message or FakeQuotedMessage()
        self.error = error
        self.tasks = []

    def locate(self, task):
        self.tasks.append(task)
        if self.error:
            raise self.error
        return self.message

    def reply(self, task, reply_text):
        message = self.locate(task)
        return message.quote(reply_text)


def test_store_enqueue_deduplicates_same_message(tmp_path):
    store = ReplyTaskStore(tmp_path / "reply.db")
    first = store.enqueue(
        chat_name="测试群",
        sender="张三",
        content="#举手 问题",
        marker="#举手",
        message_id="same-id",
    )
    second = store.enqueue(
        chat_name="测试群",
        sender="张三",
        content="#举手 问题",
        marker="#举手",
        message_id="same-id",
    )

    assert first.id == second.id
    assert len(store.list()) == 1
    assert first.status == STATUS_PENDING


def test_listener_callback_only_stores_incoming_group_marker(tmp_path):
    workflow = HandRaiseReplyWorkflow(FakeWx(), tmp_path / "reply.db")

    task = workflow.listener_callback(FakeMessage(), FakeChat())
    assert task is not None
    assert task.chat_name == "测试群"

    assert workflow.listener_callback(
        FakeMessage(content="普通消息", message_id="2"),
        FakeChat(),
    ) is None
    assert workflow.listener_callback(
        FakeMessage(attr="self", message_id="3"),
        FakeChat(),
    ) is None
    assert workflow.listener_callback(
        FakeMessage(message_id="4"),
        FakeChat(chat_type="friend"),
    ) is None
    assert len(workflow.store.list()) == 1


def test_listener_callback_respects_allowlist(tmp_path):
    workflow = HandRaiseReplyWorkflow(
        FakeWx(),
        tmp_path / "reply.db",
        allowed_chats=["允许群"],
    )

    assert workflow.listener_callback(FakeMessage(), FakeChat("其他群")) is None
    assert workflow.listener_callback(
        FakeMessage(message_id="2"),
        FakeChat("允许群"),
    ) is not None


def test_successful_reply_marks_task_replied(tmp_path):
    quoted = FakeQuotedMessage()
    locator = FakeLocator(quoted)
    workflow = HandRaiseReplyWorkflow(
        FakeWx(),
        tmp_path / "reply.db",
        locator=locator,
    )
    task = workflow.listener_callback(FakeMessage(), FakeChat())

    response = workflow.reply(task.id, "收到")

    assert response
    assert quoted.reply_text == "收到"
    stored = workflow.store.get(task.id)
    assert stored.status == STATUS_REPLIED
    assert stored.reply_text == "收到"
    assert stored.replied_at is not None


def test_failed_navigation_does_not_mark_replied(tmp_path):
    workflow = HandRaiseReplyWorkflow(
        FakeWx(),
        tmp_path / "reply.db",
        locator=FakeLocator(error=RuntimeError("定位失败")),
    )
    task = workflow.listener_callback(FakeMessage(), FakeChat())

    response = workflow.reply(task.id, "收到")

    assert not response
    stored = workflow.store.get(task.id)
    assert stored.status == STATUS_FAILED
    assert stored.replied_at is None
    assert stored.last_error == "定位失败"


def test_failed_task_can_be_retried(tmp_path):
    workflow = HandRaiseReplyWorkflow(
        FakeWx(),
        tmp_path / "reply.db",
        locator=FakeLocator(error=RuntimeError("第一次失败")),
    )
    task = workflow.listener_callback(FakeMessage(), FakeChat())
    assert not workflow.reply(task.id, "收到")

    quoted = FakeQuotedMessage()
    workflow.locator = FakeLocator(quoted)
    response = workflow.reply(task.id, "第二次收到")

    assert response
    stored = workflow.store.get(task.id)
    assert stored.status == STATUS_REPLIED
    assert stored.attempts == 2


def test_reply_next_claims_oldest_pending_task(tmp_path):
    quoted = FakeQuotedMessage()
    workflow = HandRaiseReplyWorkflow(
        FakeWx(),
        tmp_path / "reply.db",
        locator=FakeLocator(quoted),
    )
    first = workflow.listener_callback(
        FakeMessage(content="#举手 第一个", message_id="1"),
        FakeChat(),
    )
    workflow.listener_callback(
        FakeMessage(content="#举手 第二个", message_id="2"),
        FakeChat(),
    )

    response = workflow.reply_next("先回复第一个")

    assert response
    assert response["data"]["task_id"] == first.id
    assert workflow.store.get(first.id).status == STATUS_REPLIED
