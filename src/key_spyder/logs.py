import logging

from key_spyder.defaults import DEFAULT_PATH, NOW


class Logger:
    def __init__(self, name, verbose=False):
        fh_path = f"{DEFAULT_PATH}/logs/{name}_{NOW}.log"
        file_handler = logging.FileHandler(fh_path, "w", encoding="utf-8")
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(message)s",
            level=logging.INFO,
            encoding="utf-8"
        )
        self.logger = logging.getLogger(name)
        self.logger.addHandler(file_handler)
        if verbose:
            self.logger.setLevel(10)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def critical(self, message):
        self.logger.critical(message)

    def debug(self, message):
        self.logger.debug(message)

    def exception(self, message):
        self.logger.exception(message)

    def log(self, level, message):
        self.logger.log(level, message)

    def set_level(self, level):
        self.logger.setLevel(level)
