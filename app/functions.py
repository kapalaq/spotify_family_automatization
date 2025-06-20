import os
import yaml
import logging

# Logging Handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ERROR handler
error_handler = logging.FileHandler("logs/error.log", 'a', encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(
    fmt='%(filename)s: %(asctime)s ==> %(message)s',
    datefmt='%Y/%m/%d %I:%M:%S %p'
))

logger.addHandler(error_handler)


# YAML Config Handlers
CONFIG_PATH = os.path.join("settings", "config.yaml")

def load_config() -> dict:
    """
    Load config file
    :return: dict of config
    """
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def save_config(data: dict) -> None:
    """
    Save config file
    :param data: data in dict format
    :return: None
    """
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
