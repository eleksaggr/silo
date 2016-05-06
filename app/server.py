import datetime
import json
import logging, logging.config
import os
import socketserver
import sys

from app.storage import LogDatabase, LogEntry


class LogHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def setup(self):
        self.logger = logging.getLogger("default")

        dbConfig = loadConfig("config.json")["database"]
        self.db = LogDatabase(dbConfig["host"], dbConfig["port"],
                              dbConfig["db"])

    def handle(self):
        # Read message length from user.
        try:
            lengthBytes = self.request.recv(4)
            length = int(lengthBytes.decode("utf-8"))
        except ValueError as e:
            self.logger.info(
                "Malformed message length received. Aborting connection.")
            self.logger.exception(e)
            return

        message = self.request.recv(length).decode("utf-8")
        document = self.parse(message)

        self.putEntry(document)

    def parse(self, message):
        document = None
        try:
            document = json.loads(message)
        except json.JSONDecodeError as e:
            self.logger.info(
                "Malformed JSON message received. Aborting parsing.")
        return document

    def putEntry(self, document):
        try:
            entry = LogEntry(document["service"], datetime.datetime.now(),
                             document["path"], document["data"])
        except KeyError:
            self.logger.info(
                "Message missing required information. Aborting parsing.")
            return

        self.db.create(entry)


def initLogging(config, fallbackLevel="INFO"):
    """Initialize the logging system, with the specified configuration.

        Args:
            config (dict): A JSON dictionary containing the configuration.
            fallbackLevel (int): The level of logging to fallback to, if the configuration fails.
    """
    if config is not None and len(config) != 0:
        logging.config.dictConfig(config)
    else:
        # Fallback to basic logging configuration.
        logging.basicConfig(level=fallbackLevel)
        logging.warn("Could not load logging configuration. Fallback enabled.")


def loadConfig(path):
    """Load the configuration file and returns it as a JSON dictionary.

        Args:
            path (str): The path to the configuration file.
    """
    if not os.path.exists(path):
        raise ValueError("Path does not exist.")

    with open(path, "rt") as file:
        config = json.load(file)

    return config


def main():
    config = loadConfig("config.json")
    initLogging(config["logging"])

    server = socketserver.ThreadingTCPServer(
        ("localhost", int(sys.argv[1])), LogHandler)
    server.serve_forever()
