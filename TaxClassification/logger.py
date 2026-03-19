import logging
import asyncio
import traceback
from datetime import datetime
from pathlib import Path

from emailing import errormail

class logger:
    def __init__(self, mail = False, subject: str | None = None, path: str | None = None):
        self.mail = mail
        self.subject = subject
        self.path = path
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.filepath = createlogfilepath()
        
        if not self.logger.handlers:
            formatter = logging.Formatter(
                "[%(levelname)s] %(asctime)s : %(message)s",
                datefmt="%m/%d/%Y %I:%M:%S %p"
            )

            # for writing in file
            file_handler = logging.FileHandler(filename=self.filepath, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            # for console printing
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
        
    def log(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
        
    def warn(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
        
    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
        if self.mail:
            details = msg
            if kwargs.get("exc_info"):
                # Include full traceback in the email body.
                details = f"{msg}\n\n{traceback.format_exc()}"
            # errormail is async; run it safely from sync logging.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(errormail(details, subject=(f"[MDM Quality Error] {self.subject}" if self.subject else "Error alert in MDM Quality check"), logger=self))
            else:
                loop.create_task(errormail(details, subject=(f"[MDM Quality Error] {self.subject}" if self.subject else "Error alert in MDM Quality check"), logger=self))

def createlogfilepath():
    """Return a timestamped log file path under the local `logs` directory."""
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d_%H-%M_LOG")
    return logs_dir / f"{today}.log"

def _log_helpers(logger):
    """
    Return standard logging functions (_log, _warn, _error) for use in other modules.
    """
    def _debug(msg):
        if logger:
            logger.debug(msg)
        else:
            print(f"[ debug ] {msg}")
    
    def _log(msg):
        if logger:
            logger.log(msg)
        else:
            print(f"[ info ] {msg}")

    def _warn(msg):
        if logger:
            logger.warn(msg)
        else:
            print(f"[ warning ] {msg}")

    def _error(msg, exc_info=False):
        if logger:
            logger.error(msg, exc_info=exc_info)
        else:
            print(f"[ error ] {msg}")
            if exc_info:
                traceback.print_exc()

    return _debug, _log, _warn, _error

def log_helpers(logger):
    return _log_helpers(logger)

