import logging
from typing import Union, IO, Optional

import hypercorn
from hypercorn.config import Config
class CubeFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = '\x1b[32m'
    reset = "\x1b[0m"
    format = """[%(asctime)s] [%(levelname)s] [%(thread)d-%(threadName)s] [process_ID:%(process)d] "%(message)s" """

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# ==========OVERRIDE HYPERCORN LOGGING SETTING==========
def _create_logger(
        name: str,
        target: Union[logging.Logger, str, None],
        level: Optional[str],
        sys_default: IO,
        *,
        propagate: bool = True,
) -> Optional[logging.Logger]:
    if isinstance(target, logging.Logger):
        return target

    if target:
        logger = logging.getLogger(name)
        logger.handlers = [
            logging.StreamHandler(sys_default) if target == "-" else logging.FileHandler(target)
            # type: ignore # noqa: E501
        ]
        logger.propagate = propagate
        # formatter = logging.Formatter(
        #     "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
        #     "[%Y-%m-%d %H:%M:%S %z]",
        # )

        logger.handlers[0].setFormatter(CubeFormatter())
        if level is not None:
            logger.setLevel(logging.getLevelName(level.upper()))
        return logger
    else:
        return None


hypercorn.logging._create_logger = _create_logger

# ====================================================
log_config = Config()
_logger = hypercorn.logging.Logger(log_config)