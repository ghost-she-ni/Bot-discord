import logging

class Logger:

    def __init__(self, config:dict):

        print ("logger name ",__name__) 

        self._level = getattr(logging, config["log_level"].upper(), logging.INFO)

        formatter = logging.Formatter(config["log_format"])

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._level)
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(config["log_file"])
        file_handler.setLevel(self._level)
        file_handler.setFormatter(formatter)

        self.log = logging.getLogger(__name__)
        self.log.setLevel(self._level)
        self.log.addHandler(console_handler)
        self.log.addHandler(file_handler)
        # Evite l'ajout répété des handlers si le logger est déjà configuré
        self.log.propagate = False

    def infolog(self, msg: str):
        self.log.info(msg)

    def errorlog(self, msg: str):
        self.log.error(msg)

    def debuglog(self, msg: str):
        self.log.debug(msg)