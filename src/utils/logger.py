"""
logger.py
-------------------------------------------------------------------------------
A tiny helper so every module logs messages the same way instead of using
scattered print() statements. Import get_logger(__name__) at the top of a
module and call logger.info(...) / logger.warning(...) / logger.error(...).
-------------------------------------------------------------------------------
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
