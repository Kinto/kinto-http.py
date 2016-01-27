from __future__ import absolute_import
import logging

COMMAND_LOG_LEVEL = 25

logging.addLevelName(COMMAND_LOG_LEVEL, 'COMMAND')
logging.basicConfig(level=COMMAND_LOG_LEVEL, format="%(message)s")

global_logger = logging.getLogger(__file__)


def command_log(logger, *args, **kwargs):
    logger.log(COMMAND_LOG_LEVEL, *args, **kwargs)
