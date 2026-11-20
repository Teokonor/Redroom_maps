import os
import sys
from pathlib import Path

from loguru import logger

from .constants import PROJECT_DIR


_configured = False
_LOG_FORMAT = (
    '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | '
    '{name}:{function}:{line} - {message}'
)
_VALID_LEVELS = {
    'TRACE',
    'DEBUG',
    'INFO',
    'SUCCESS',
    'WARNING',
    'ERROR',
    'CRITICAL',
}


def setup_logging() -> None:
    """Configure stderr and rotating file logging once per process."""
    global _configured

    if _configured:
        return

    _configured = True

    level = os.environ.get('REDROOM_LOG_LEVEL', 'INFO').upper()
    if level not in _VALID_LEVELS:
        level = 'INFO'

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=_LOG_FORMAT,
        backtrace=True,
        diagnose=False,
    )

    log_dir_value = os.environ.get('REDROOM_LOG_DIR')
    log_dir = (
        Path(log_dir_value).resolve()
        if log_dir_value
        else PROJECT_DIR / 'logs'
    )

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / 'app.log',
            level=level,
            format=_LOG_FORMAT,
            rotation='10 MB',
            retention='14 days',
            compression='zip',
            encoding='utf-8',
            backtrace=True,
            diagnose=False,
        )
    except OSError as error:
        logger.warning('Cannot set up file logging in {}: {}', log_dir, error)

    logger.debug('Logging configured: level={}, file={}', level, log_dir)
