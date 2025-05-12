#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/custom_logging.py

Description:
    Short description of what this (custom_logging.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     06 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import logging
import sys
import os
from pathlib import Path

# Third-party imports

# Local application imports

__all__ = ["setup_logging"]

# climb back up from .../src/config/custom_logging.py to your project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# now build a `data/logs` folder under that
LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# and point your log file there
LOG_FILENAME = LOG_DIR / "region_designer.log"


# --- define a custom SUCCESS level --- #
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


# Monkey-patch Logger to have .success()
logging.Logger.success = success


class SuccessErrorFilter(logging.Filter):
    """Only pass through records that are exactly SUCCESS or >= ERROR."""
    def filter(self, record):
        return (record.levelno == SUCCESS_LEVEL) or (record.levelno >= logging.ERROR)


def setup_logging(console_level: str = "INFO") -> None:

    root = logging.getLogger()

    # Clear previous logging handlers as they live outside namespace; avoiding %reset
    for h in root.handlers[:]:
        root.removeHandler(h)
        try:
            h.close()
        except:
            pass

    root.setLevel(logging.DEBUG)   # capture everything—handlers will filter.

    fmt     = "%(asctime)s %(name)s %(levelname)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # 1) Console handler: show INFO+ on stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(ch)

    # 2) File handler: only SUCCESS and ERROR+ (overwrite on each run)
    fh = logging.FileHandler(LOG_FILENAME, mode="w")
    # set low enough so that SUCCESS records reach it
    fh.setLevel(SUCCESS_LEVEL)
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    fh.addFilter(SuccessErrorFilter())
    root.addHandler(fh)
