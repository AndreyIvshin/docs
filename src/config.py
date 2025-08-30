from impl.llm import OpenAIClient
from impl.screenshot_maker import Mhtml2Png
from impl.mhtml_manipulator import MhtmlManipulator
import os, logging, colorlog

def llm():
    return OpenAIClient(
        api_key=os.getenv("OPEN_AI_API_KEY"),
        api_url=os.getenv("OPEN_AI_API_URL")
    )

def creenshot_maker():
    return Mhtml2Png("tmp")

def mhtml_manipulator():
    return MhtmlManipulator("tmp")

def logger_factory():
    return lambda name: __logger(name)

def __logger(name):
    formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        secondary_log_colors={},
        style="%",
    )

    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    return logger
