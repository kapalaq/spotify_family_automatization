import os
import yaml
import logging

# Logging Handler
class ErrorLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # ERROR handler
        path = os.path.join(os.getcwd(), "logs", "error.log")
        error_handler = logging.FileHandler(path, "a", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(
                fmt="%(filename)s: %(asctime)s ==> %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p"
            )
        )

        self.logger.addHandler(error_handler)


# YAML Config Handlers
class YAMLConfig:
    CONFIG_PATH: str = os.path.join("../settings", "config.yaml")

    @staticmethod
    def load_config() -> dict:
        """
        Load config file
        :return: dict of config
        """
        with open(YAMLConfig.CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def save_config(data: dict) -> None:
        """
        Save config file
        :param data: data in dict format
        :return: None
        """
        with open(YAMLConfig.CONFIG_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
