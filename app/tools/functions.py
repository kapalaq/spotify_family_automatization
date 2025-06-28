import os
import yaml
import logging


class ErrorLogger:
    """Class for logging errors.

    A facade class for logger from logging.
    It writes all logged errors into specified file.

    Attributes:
        logger: a logger instance that allows logging effectively
    """

    def __init__(self):
        """Initalizes instance of ErrorLogger

        Log (error.log) file can be found in root/app/settings.

        """
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


class YAMLConfig:
    """YAML Config Handler

    This class allows user to work with YAML config files.
    In details, one can access values from YAML config file
    and update/delete values in it. Then save their changes.

    Attributes:
        CONFIG_PATH: A string containing absolute path to YAML config file
    """

    CONFIG_PATH: str = os.path.join(os.getcwd(), "settings", "config.yaml")

    @staticmethod
    def load_config() -> dict:
        """Load config file.

        Return:
            dict of config
        """
        with open(YAMLConfig.CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def save_config(data: dict) -> None:
        """Save config file.

        Args:
            data (dict): config

        Returns:
             None, saves new config data
        """
        with open(YAMLConfig.CONFIG_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
