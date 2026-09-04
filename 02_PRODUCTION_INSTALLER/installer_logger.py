import logging, re
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Patterns for values that must never reach disk in plaintext, per spec section 9
# ("Secret বা credential log করা যাবে না"). Matches key=value / key: value / JSON
# "key": "value" shapes for common secret-bearing field names, case-insensitive.
_SECRET_KEY_NAMES = r"(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|authorization|auth|credential|signature|bearer)"
_SECRET_PATTERNS = [
    re.compile(rf'("{_SECRET_KEY_NAMES}"\s*:\s*")([^"]+)(")', re.IGNORECASE),
    re.compile(rf"({_SECRET_KEY_NAMES}\s*[:=]\s*)(\S+)", re.IGNORECASE),
]

def redact(message: str) -> str:
    for pattern in _SECRET_PATTERNS:
        if pattern.groups == 3:
            message = pattern.sub(r"\1***REDACTED***\3", message)
        else:
            message = pattern.sub(r"\1***REDACTED***", message)
    return message

class _RedactingFilter(logging.Filter):
    def filter(self, record):
        try:
            record.msg = redact(record.getMessage())
            record.args = ()
        except Exception:
            pass
        return True

def get_logger(log_dir):
    Path(log_dir).mkdir(parents=True,exist_ok=True); logger=logging.getLogger("lmacw.installer")
    if not logger.handlers:
        h=RotatingFileHandler(Path(log_dir)/"installer.log",encoding="utf-8",maxBytes=5*1024*1024,backupCount=5)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addFilter(_RedactingFilter())
        logger.addHandler(h); logger.setLevel(logging.INFO)
    return logger
