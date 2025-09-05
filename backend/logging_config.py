# backend/logging_config.py
import os, logging, logging.config, datetime

def ensure_logs_dir(base_dir: str) -> str:
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

def make_log_path(base_dir: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(ensure_logs_dir(base_dir), f"backend_{ts}.log")

def setup_logging(base_dir: str = None, level: str = "DEBUG") -> str:
    """
    Configure logging for the entire app BEFORE anything else logs.
    Returns the log file path used.
    """
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    log_path = make_log_path(base_dir)

    # Avoid re-configuring if already configured
    root = logging.getLogger()
    if getattr(root, "_configured_by_app", False):
        return log_path

    fmt = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    config = {
        "version": 1,
        "disable_existing_loggers": False,  # keep third-party loggers active
        "formatters": {
            "standard": {"format": fmt, "datefmt": datefmt},
            "access":   {"format": '%(asctime)s %(levelname)s - %(message)s', "datefmt": datefmt},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": log_path,
                "encoding": "utf-8",
                "mode": "w",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console", "file"],
        },
        # Make sure these loggers propagate to root (so they hit our handlers)
        "loggers": {
            # Uvicorn loggers
            "uvicorn":         {"level": level, "propagate": True},
            "uvicorn.error":   {"level": level, "propagate": True},
            "uvicorn.access":  {"level": level, "propagate": True, "handlers": []},
            # Our app loggers (add others as needed)
            "analyzer":        {"level": level, "propagate": True},
            "analyzer_api":    {"level": level, "propagate": True},
            "colab_compat":    {"level": level, "propagate": True},
            "error_handler":   {"level": level, "propagate": True},
        },
    }

    logging.config.dictConfig(config)
    # Mark to prevent duplicate setup
    root._configured_by_app = True

    logging.getLogger(__name__).info("Logging configured. File: %s", log_path)
    return log_path

