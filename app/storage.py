from logging import getLogger
from pymongo import MongoClient


class LogDatabase(object):
    def __init__(self, host, port, db):
        self.host = host
        self.port = port
        self.db = db

        self.logger = getLogger("default")

    def create(self, entry):
        if entry is None:
            self.logger.info("Tried to insert None-entry.")
            raise ValueError("Cannot insert a None-entry.")

        db = self._openConnection()
        collection = db.entries

        document = {"service": entry.service,
                    "time": entry.time,
                    "path": entry.path,
                    "data": entry.data}

        collection.insert_one(document)

    def _openConnection(self):
        connection = MongoClient(self.host, self.port)

        # NOTE: The following condition may never happen, if MongoDB just
        # creates a new database, if the name is spelled wrong.
        if connection[self.db] is None:
            self.logger.error("Invalid database '{0}'specified.".format(
                self.db))
            raise ValueError("Invalid database specified.")

        return connection[self.db]


class LogEntry(object):
    def __init__(self, service, time, path, data=None):
        self.id = None
        self.service = service
        self.time = time
        self.path = path
        if data is not None:
            self.data = data
        else:
            self.data = {}
