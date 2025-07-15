import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from colorama import Fore, Style, init as colorama_init
from config import LOGGING_PATH, LOGGING_LIMIT

# Initialize colorama for Windows support
colorama_init(autoreset=True)


os.makedirs(LOGGING_PATH, exist_ok=True)

# Timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = os.path.join(LOGGING_PATH, f"app_log_{timestamp}.log")

# Log Format (plain for file, colored for console)
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
COLOR_FORMATS = {
    "DEBUG": Fore.CYAN + LOG_FORMAT + Style.RESET_ALL,
    "INFO": Fore.WHITE + LOG_FORMAT + Style.RESET_ALL,
    "WARNING": Fore.YELLOW + LOG_FORMAT + Style.RESET_ALL,
    "ERROR": Fore.RED + LOG_FORMAT + Style.RESET_ALL,
    "CRITICAL": Fore.RED + Style.BRIGHT + LOG_FORMAT + Style.RESET_ALL,
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color_fmt = COLOR_FORMATS.get(record.levelname, LOG_FORMAT)
        formatter = logging.Formatter(color_fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def get_logger(name: str = "app", level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Avoid duplicate logs in FastAPI

    if not logger.handlers:
        # Console Handler with colors
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(ColoredFormatter())
        logger.addHandler(ch)

        # File Handler (Rotating)
        fh = RotatingFileHandler(
            LOG_FILENAME, maxBytes=1_000_000, backupCount=LOGGING_LIMIT, encoding='utf-8'
        )
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter(LOG_FORMAT, "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(fh)

    return logger
