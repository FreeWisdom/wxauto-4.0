from .param import WxParam

import logging
import colorama
from pathlib import Path
from datetime import datetime


# 初始化 colorama(仅影响 ANSI 颜色码处理,不改宿主 stdout)
colorama.init()


LOG_COLORS = {
    'DEBUG': colorama.Fore.CYAN,
    'INFO': colorama.Fore.GREEN,
    'WARNING': colorama.Fore.YELLOW,
    'ERROR': colorama.Fore.RED,
    'CRITICAL': colorama.Fore.MAGENTA
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        message = super().format(record)
        color = LOG_COLORS.get(levelname, '')
        if color:
            return f"{color}{message}{colorama.Style.RESET_ALL}"
        return message

class WxautoLogger:
    """wxauto4 专用 logger。

    作为库被嵌入时,**不**修改宿主进程的 root logger 与 stdout,
    只操作名为 ``wxauto4`` 的独立 logger(``propagate=False``)。
    """

    name: str = 'wxauto4'

    def __init__(self):
        self.file_handler: logging.FileHandler | None = None
        self.console_handler: logging.StreamHandler | None = None
        self.logger = self._setup_logger()
        self.set_debug(False)

    def _setup_logger(self) -> logging.Logger:
        """配置 wxauto4 命名 logger,与宿主应用隔离。"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        # 关键:不向 root 传播,避免污染宿主日志配置
        logger.propagate = False

        # 抑制部分噪声库的日志(只影响这些命名 logger,不影响 root)
        for noisy in ('asyncio', 'comtypes', 'urllib3', 'requests'):
            logging.getLogger(noisy).setLevel(logging.WARNING)

        # 控制台 handler 只挂一次,避免重复 import 时叠加
        if not self._has_console_handler(logger):
            fmt = '%(asctime)s [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]  %(message)s'
            handler = logging.StreamHandler()
            handler.setFormatter(ColoredFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S"))
            handler.setLevel(logging.INFO)
            logger.addHandler(handler)
            self.console_handler = handler
        else:
            self.console_handler = next(
                h for h in logger.handlers
                if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            )

        return logger

    @staticmethod
    def _has_console_handler(logger: logging.Logger) -> bool:
        return any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )

    def setup_file_logger(self):
        """根据 ``WxParam.ENABLE_FILE_LOGGER`` 决定是否创建文件日志 handler。"""
        if not WxParam.ENABLE_FILE_LOGGER or self.file_handler is not None:
            return

        log_dir = Path(WxParam.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        current_time = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"app_{current_time}.log"

        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self.file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]  %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        self.file_handler.setLevel(logging.DEBUG)

        # 加到 wxauto4 命名 logger,而非 root
        self.logger.addHandler(self.file_handler)

    def set_debug(self, debug=False):
        """动态切换控制台 handler 的日志级别。"""
        if self.console_handler is not None:
            self.console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    def _ensure_file_logger(self):
        if WxParam.ENABLE_FILE_LOGGER and self.file_handler is None:
            self.setup_file_logger()

    def debug(self, msg: str, *args, **kwargs):
        self._ensure_file_logger()
        # stacklevel 默认 2 指向调用方;允许显式覆盖
        kwargs.setdefault('stacklevel', 2)
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._ensure_file_logger()
        kwargs.setdefault('stacklevel', 2)
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._ensure_file_logger()
        kwargs.setdefault('stacklevel', 2)
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._ensure_file_logger()
        kwargs.setdefault('stacklevel', 2)
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self._ensure_file_logger()
        kwargs.setdefault('stacklevel', 2)
        self.logger.critical(msg, *args, **kwargs)


wxlog = WxautoLogger()
