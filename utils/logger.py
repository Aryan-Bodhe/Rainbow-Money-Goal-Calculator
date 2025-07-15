import logging
import os
from logging.handlers import TimedRotatingFileHandler
from colorama import Fore, Style, init as colorama_init
from config import LOGGING_PATH, LOGGING_LIMIT_DAYS

# Initialize colorama for Windows support
colorama_init(autoreset=True)

os.makedirs(LOGGING_PATH, exist_ok=True)
LOG_FILENAME = os.path.join(LOGGING_PATH, "app.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
COLOR_FORMATS = {
    "DEBUG":   Fore.CYAN    + LOG_FORMAT + Style.RESET_ALL,
    "INFO":    Fore.WHITE   + LOG_FORMAT + Style.RESET_ALL,
    "WARNING": Fore.YELLOW  + LOG_FORMAT + Style.RESET_ALL,
    "ERROR":   Fore.RED     + LOG_FORMAT + Style.RESET_ALL,
    "CRITICAL":Fore.RED + Style.BRIGHT + LOG_FORMAT + Style.RESET_ALL,
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

        # Timed rotating file handler: rotates at midnight, keeps LOGGING_LIMIT days
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
        logger.addHandler(fh)

    return logger
