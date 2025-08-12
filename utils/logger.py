import logging
import os
from logging.handlers import TimedRotatingFileHandler
from colorama import Fore, Style, init as colorama_init
from config import LOGGING_DIR, LOGGING_LIMIT_DAYS

"""
    Create and configure a colorized, rotating logger instance.

    This function returns a `logging.Logger` with:
    - Console output using colorized log levels (via `colorama`)
    - File logging with daily rotation (via `TimedRotatingFileHandler`)
    - Automatic log file directory creation
    - Retention of log files up to `LOGGING_LIMIT_DAYS` days
    - Rotated files renamed from "app.log.YYYY-MM-DD" to "app.YYYY-MM-DD.log"

    Parameters
    ----------
    name : str, optional
        The logger name. Defaults to "app".
    level : int, optional
        Logging level (e.g., `logging.DEBUG`, `logging.INFO`). Defaults to `logging.INFO`.

    Returns
    -------
    logging.Logger
        A configured logger instance.

    Notes
    -----
    - Console log messages are color-coded by severity:
        DEBUG (cyan), INFO (white), WARNING (yellow), ERROR (red), CRITICAL (bright red).
    - File logs are stored in the `LOGGING_DIR` directory from `config.py`.
    - Daily rotation happens at midnight, with filenames in the format:
      `app.YYYY-MM-DD.log`.

    Example
    -------
    >> logger = get_logger()
    >> logger.info("Application started")
    >> logger.error("An error occurred")
"""

# Initialize colorama for Windows support
colorama_init(autoreset=True)

os.makedirs(LOGGING_DIR, exist_ok=True)
LOG_FILENAME = os.path.join(LOGGING_DIR, "app.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
COLOR_FORMATS = {
    "DEBUG":    Fore.CYAN    + LOG_FORMAT + Style.RESET_ALL,
    "INFO":     Fore.WHITE   + LOG_FORMAT + Style.RESET_ALL,
    "WARNING":  Fore.YELLOW  + LOG_FORMAT + Style.RESET_ALL,
    "ERROR":    Fore.RED     + LOG_FORMAT + Style.RESET_ALL,
    "CRITICAL": Fore.RED + Style.BRIGHT + LOG_FORMAT + Style.RESET_ALL,
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        fmt = COLOR_FORMATS.get(record.levelname, LOG_FORMAT)
        return logging.Formatter(fmt, "%Y-%m-%d %H:%M:%S").format(record)

def get_logger(name: str = "app", level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(ColoredFormatter())
        logger.addHandler(ch)

        # File handler with daily rotation, naming backups as app.YYYY-MM-DD.log
        fh = TimedRotatingFileHandler(
            LOG_FILENAME,
            when="midnight",
            interval=1,
            backupCount=LOGGING_LIMIT_DAYS,
            encoding="utf-8",
            utc=False
        )
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter(LOG_FORMAT, "%Y-%m-%d %H:%M:%S"))

        # 1) Use only date for suffix (no time)
        fh.suffix = "%Y-%m-%d"

        # 2) Rename rotated files from "app.log.YYYY-MM-DD" to "app.YYYY-MM-DD.log"
        def namer(default_name: str) -> str:
            # split off the date
            base_with_ext, date = default_name.rsplit(".", 1)
            # base_with_ext is ".../app.log"
            root, ext = os.path.splitext(base_with_ext)  # yields (".../app", ".log")
            return f"{root}.{date}{ext}"

        fh.namer = namer

        logger.addHandler(fh)

    return logger
