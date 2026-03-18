import logging
import os
from logging.handlers import TimedRotatingFileHandler

if not os.path.exists("logs"):
    os.makedirs("logs")

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def setup_logging(app):
    # APP LOG
    app_handler = TimedRotatingFileHandler(
        "logs/app.log",
        when="midnight",
        interval=1,
        backupCount=90,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    app.logger.addHandler(app_handler)
    app.logger.setLevel(logging.INFO)

    # COMMAND LOG
    cmd_logger = logging.getLogger("commands")

    if not cmd_logger.handlers:  # evita duplicação
        cmd_handler = TimedRotatingFileHandler(
            "logs/commands.log",
            when="midnight",
            interval=1,
            backupCount=180,
            encoding="utf-8"
        )
        cmd_handler.setFormatter(formatter)
        cmd_logger.addHandler(cmd_handler)

    cmd_logger.setLevel(logging.INFO)
    cmd_logger.propagate = False