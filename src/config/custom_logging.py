#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/config/custom_logging.py

Description:
    Logging control file to be imported at the top-level builder.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     06 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import logging
import sys
from pathlib import Path

# Third-party imports

# Local application imports

__all__ = ["setup_logging"]

# climb back up from PATH to PROJECT_ROOT 'src'
SRC_DIR = Path(__file__).resolve().parents[2]
# output directory for log files is <project_root>/data/logs
LOG_DIR = SRC_DIR / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILENAME = LOG_DIR / "ubermag_interface.log"


# --- Custom toggles and file-logging levels --- #
## --- configurable toggles for file‐logging levels --- ##
# Should INFO messages go to the log file?
ENABLE_INFO_IN_FILE = False
# Should SUCCESS messages go to the log file?
ENABLE_SUCCESS_IN_FILE = True

## --- I find it useful to distinguish SUCCESS cases from general INFO --- ##
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def success(self, message, *args, **kwargs) -> None:
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


# Monkey-patch Logger to have .success()
logging.Logger.success = success


class FileLevelFilter(logging.Filter):
    """
     Allow DEBUG and ERROR+ always.
     Allow INFO only if ENABLE_INFO_IN_FILE.
     Allow SUCCESS only if ENABLE_SUCCESS_IN_FILE.
     """
    def filter(self, record):
        lvl = record.levelno
        if lvl == logging.INFO:
            return True
        if lvl == logging.DEBUG:
            return True
        if lvl >= logging.ERROR:
            return True
        if lvl == SUCCESS_LEVEL and ENABLE_SUCCESS_IN_FILE:
            return True
        if lvl == logging.INFO and ENABLE_INFO_IN_FILE:
            return True
        return False


def setup_logging(console_level: str = "INFO", file_level: str = "DEBUG") -> None:

    root = logging.getLogger()

    # Clear previous logging handlers as they live outside namespace; avoiding %reset
    for h in root.handlers[:]:
        root.removeHandler(h)
        try:
            h.close()
        except:
            # TODO. Create proper error handling
            pass

    root.setLevel(logging.DEBUG)   # capture everything—handlers will filter.

    fmt = "%(asctime)s %(levelname)s %(name)s : %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # 1) Console handler: show INFO+ on stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(ch)

    # 2) File handler: only SUCCESS and ERROR+ (overwrite on each run)
    fh = logging.FileHandler(LOG_FILENAME, mode="w")
    # capture everything; the filter will let through only the desired levels
    ch.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    fh.addFilter(FileLevelFilter())
    root.addHandler(fh)
