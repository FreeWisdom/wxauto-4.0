"""Safe listener trigger test.

Only sends to the allowlisted chat "项目研究". The Chinese chat name is built
from Unicode escapes to avoid PowerShell stdin encoding issues.
"""

import time
import traceback

from wxauto4 import WeChat


TARGET = "\u9879\u76ee\u7814\u7a76"


def main():
    print("init listener", flush=True)
    wx = WeChat(start_listener=True)
    print(f"nickname={wx.nickname}", flush=True)
    events = []

    def callback(msg, chat):
        text = str(getattr(msg, "content", ""))
        print(
            "callback who=%s attr=%s text=%s"
            % (chat.who, getattr(msg, "attr", "?"), text[:120]),
            flush=True,
        )
        events.append(text)

    try:
        result = wx.AddListenChat(TARGET, callback)
        print(f"AddListenChat={result}", flush=True)
        time.sleep(2)

        content = "wxauto4 listener callback test - " + time.strftime("%H:%M:%S")
        print(f"SendMsg target={TARGET} content={content}", flush=True)
        response = wx.SendMsg(content, TARGET, clear=True)
        print(f"SendMsg response={response}", flush=True)

        deadline = time.time() + 15
        while time.time() < deadline and not events:
            time.sleep(0.5)
        print(f"events_count={len(events)}", flush=True)
    except Exception as exc:
        print(f"error={exc!r}", flush=True)
        traceback.print_exc()
    finally:
        try:
            remove_response = wx.RemoveListenChat(TARGET, close_window=False)
            print(f"RemoveListenChat={remove_response}", flush=True)
        except Exception as exc:
            print(f"RemoveListenChat error={exc!r}", flush=True)
        try:
            wx.StopListening(remove=False)
            print("StopListening=ok", flush=True)
        except Exception as exc:
            print(f"StopListening error={exc!r}", flush=True)


if __name__ == "__main__":
    main()
