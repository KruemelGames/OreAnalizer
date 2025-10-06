import logging, os
from logging.handlers import RotatingFileHandler
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "logs")
LOG_PATH = os.path.join(os.path.abspath(LOG_DIR), "app.log")
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    os.makedirs(LOG_DIR, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt_file = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fmt_console = logging.Formatter("[%(levelname)s] %(message)s")
    fh = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt_file)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt_console)
    root.handlers.clear()
    root.addHandler(fh)
    root.addHandler(ch)
    return logging.getLogger(name)
def set_level(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(level)
